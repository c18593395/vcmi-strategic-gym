#!/usr/bin/env python3
"""
P8-C 阶段3-B: 城镇决策链探针 (A Warm and Familiar Place 图)
红方自带城镇 + 主英雄贴脸 → 完整决策环:
  1. SRV-DIAG 拿 hero/town OI
  2. 我方回合: BuildStructure(town, DWELL_LVL_1=30) 建一级兵营
  3. 解析 SetAvailableCreatures(112) 广播拿可招生物
  4. RecruitCreatures(187) 招到英雄身上
  5. MoveHero + EndTurn
验收: server 日志出现 BuildStructure/RecruitCreatures "successfully applied" 且无 fishy。
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected, MoveHero, EndTurn, BuildStructure, RecruitCreatures

HOST='127.0.0.1'; PORT=3030; BIN=r'D:\vcmi-fork-build\bin'
MY_COLOR = 0
MAP = r'Maps/A Warm and Familiar Place.h3m'
SRV_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8c2_srv.log'

LOBBY_TIDS={216:'LobbyClientConnected',217:'LobbyClientDisconnected',218:'LobbyChatMessage',
            221:'LobbyLoadProgress',223:'LobbyPrepareStartGame',224:'LobbyStartGame',
            226:'LobbyUpdateState',229:'LobbySetMap',225:'LobbyChangeHost',227:'LobbyShowMessage'}
GAME_TIDS={88:'PlayerStartsTurn',116:'NewTurn',132:'BattleStart',135:'BattleResult',
           84:'PackageApplied',85:'SystemMessage',109:'TryMoveHero',115:'GiveHero',
           121:'NewObject',102:'PlayerEndsTurn',86:'SetResources',95:'SetObjectProperty',
           106:'SetHeroes',111:'SetAvailableHero',112:'SetAvailableCreatures',
           117:'SetObjects',118:'SetSetters',125:'SetPlayerInfo',251:'PackageReceived'}

def tid_name(t):
    return LOBBY_TIDS.get(t) or GAME_TIDS.get(t) or f'?{t}'

def kill_all():
    for exe in ('VCMI_server.exe','VCMI_client.exe'):
        subprocess.run(['taskkill','/F','/IM',exe],capture_output=True)
    time.sleep(1)

class Probe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self._us = 0
        self.client2_seen = False
        self.game_started = False
        self.running = True
        self.heroes = {}
        self.towns = {}       # oi -> owner
        self.my_hero = None
        self.my_town = None
        self.available = {}   # town_oi -> [(amount, [creature_ids])]  from 112
        self.townavail = {}   # town_oi -> [jsonKey,...] from SRV-DIAG TOWNAVAIL
        self.turns = 0
        self.build_result = None
        self.recruit_result = None
        self.recruit_attempted = False
        self._req = 0
        self.end_turn_sent = False
        self.applied = {}     # (type_id) -> last ok

    def next_req(self):
        self._req += 1
        return self._req

    def send_pack(self, pack):
        self.conn.send_frame(pack.to_bytes())

    def poll_diag(self):
        try:
            if not os.path.exists(SRV_LOG): return
            with open(SRV_LOG, 'r', errors='replace') as f:
                for line in f:
                    m = re.search(r'\[SRV-DIAG\] HERO OI=(\d+) owner=(-?\d+) pos=\((-?\d+) (-?\d+) (-?\d+)\)', line)
                    if m:
                        self.heroes[int(m.group(1))] = (int(m.group(2)), (int(m.group(3)),int(m.group(4)),int(m.group(5))))
                    m = re.search(r'\[SRV-DIAG\] TOWN OI=(\d+) owner=(-?\d+) pos=\((-?\d+) (-?\d+) (-?\d+)\) creatures=(.*)', line)
                    if m:
                        self.towns[int(m.group(1))] = int(m.group(2))
                    m = re.search(r'\[SRV-DIAG\] TOWNAVAIL OI=(\d+) creatures=(.*)', line)
                    if m:
                        oi = int(m.group(1))
                        keys = [k for k in m.group(2).strip().split(',') if k]
                        self.townavail[oi] = keys
                        print(f'[DIAG] TOWNAVAIL town={oi} creatures={keys}')
        except Exception as e:
            print(f'[DIAG] {e}')

    def resolve(self):
        for oi,(owner,pos) in self.heroes.items():
            if owner == MY_COLOR:
                self.my_hero = oi
        for oi,owner in self.towns.items():
            if owner == MY_COLOR:
                self.my_town = oi

    def act_turn(self):
        self.poll_diag(); self.resolve()
        if self.my_town and self.build_result is None:
            bs = BuildStructure(tid=self.my_town, bid=30, player=MY_COLOR, request_id=self.next_req())  # 30=DWELL_LVL_1
            print(f'[ACT] BuildStructure town={self.my_town} bid=30(DWELL_LVL_1)')
            self.send_pack(bs)
            time.sleep(0.8)
        if self.my_town and self.my_hero and self.my_town in self.available and not self.recruit_attempted:
            diag_keys = self.townavail.get(self.my_town, [])
            for amount, crids in self.available[self.my_town]:
                # 优先 SRV-DIAG TOWNAVAIL 的真实 jsonKey; 否则只用字面 jsonKey (跨包去重 ref 本地还原不了)
                crid = diag_keys[0] if diag_keys else next((c for c in crids if c and c[0].isalpha()), None)
                if amount > 0 and crid:
                    rc = RecruitCreatures(tid=self.my_town, dst=self.my_hero, crid=crid,
                                          amount=amount, level=0, player=MY_COLOR, request_id=self.next_req())
                    print(f'[ACT] RecruitCreatures town={self.my_town} -> hero={self.my_hero} crid={crid} x{amount}')
                    self.send_pack(rc)
                    self.recruit_attempted = True
                    time.sleep(0.8)
                    break
        print('[ACT] EndTurn')
        self.send_pack(EndTurn(player=MY_COLOR, request_id=self.next_req()))

    def recv_loop(self):
        while self.running:
          try:
            data = self.conn.recv_frame()
            if data is None:
                if not self.conn.connected:
                    print('[RECV] 断开'); break
                continue
            if len(data)==0: continue
            d = BinaryDeserializer(data)
            if d.read_bool(): continue
            d.read_int()
            tid = d.read_int()
            if tid in (100,117,118,125,86,106,111,95,109):
                continue
            print(f'[RECV] {len(data):6d}B tid={tid} {tid_name(tid)}')
            if tid==226:
                self._us += 1
                if self._us >= 2: self.client2_seen = True
            elif tid==224:
                self.game_started = True
            elif tid==112:
                # SetAvailableCreatures: tid(OI) + vector<pair<ui32 amount, vector<CreatureID string>>>
                # CreatureID = EntityIdentifier → wire string (jsonKey)。11B 帧 = 空容器 (无建筑)
                town_oi = d.read_int()
                n = d.read_int()
                lst = []
                for _ in range(max(n,0)):
                    amount = d.read_int()
                    cn = d.read_int()
                    crids = []
                    for _ in range(max(cn,0)):
                        ln = d.read_int()
                        if ln < 0:
                            crids.append(f'<ref{-ln}>')  # 去重引用 (跨包表, 本地无法解析)
                        elif ln == 0:
                            crids.append('')
                        else:
                            crids.append(d.read_raw(ln).decode('utf-8','replace'))
                    lst.append((amount, crids))
                self.available[town_oi] = lst
                print(f'[112] town={town_oi} available={lst}')
            elif tid==88:
                qid = d.read_int(); player = d.read_int()
                if player == MY_COLOR and not self.end_turn_sent:
                    self.turns += 1
                    print(f'--- MY TURN #{self.turns} ---')
                    self.act_turn()
                    self.end_turn_sent = True
            elif tid==102:
                self.end_turn_sent = False
            elif tid==84:
                p=d.read_int(); req=d.read_int(); pt=d.read_int(); ok=d.read_bool()
                self.applied[pt] = ok
                if pt in (185,187):
                    print(f'[APPLIED] tid={pt} ({tid_name(pt)}) result={ok}')
                    if pt==185: self.build_result = ok
                    if pt==187: self.recruit_result = ok
          except Exception as e:
            print(f'[RECV-ERR] {e}')  # 单包解析失败不杀线程
            continue

def main():
    print('=== P8-C stage3-B: town decision chain (Build -> Available -> Recruit) ===')
    kill_all()
    srv_log = open(SRV_LOG,'w')
    srv = subprocess.Popen([BIN+r'\VCMI_server.exe','--port=3030'],cwd=BIN,stdout=srv_log,stderr=subprocess.STDOUT)
    time.sleep(9)

    p = Probe()
    if not p.conn.connect():
        print('[FAIL] connect'); return 1
    threading.Thread(target=p.recv_loop,daemon=True).start()
    p.conn.send_frame(LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['PyHost'], mode=0).to_bytes())
    print('[1] joined lobby'); time.sleep(1)

    cli_log = open(r'C:\Users\Administrator\AppData\Local\Temp\p8c2_cli.log','w')
    env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI']='1'
    cli = subprocess.Popen([BIN+r'\VCMI_client.exe','--testmap',MAP,
                            '--donotstartserver','--serverport','3030','--headless'],
                           cwd=BIN,stdout=cli_log,stderr=subprocess.STDOUT,env=env)
    print(f'[2] client1 pid={cli.pid}')
    t0=time.time()
    while time.time()-t0 < 15 and not p.client2_seen: time.sleep(0.2)
    print(f'[3] client2_seen={p.client2_seen}')
    p.conn.send_frame(bytes([0,0,0xe1,0x01,0x02]))
    print('[4] ChangeHost')
    t0=time.time()
    while time.time()-t0 < 40 and not p.game_started: time.sleep(0.5)
    print(f'[5] game_started={p.game_started}')
    if not p.game_started:
        p.running=False; return 2

    t0=time.time()
    while time.time()-t0 < 10:
        p.poll_diag(); p.resolve()
        if p.my_hero and p.my_town: break
        time.sleep(0.5)
    print(f'[6] my_hero={p.my_hero} my_town={p.my_town}')

    t0=time.time()
    while time.time()-t0 < 180 and p.turns < 4:
        time.sleep(0.5); p.poll_diag()

    p.running=False
    try: p.conn.disconnect()
    except: pass
    time.sleep(0.5); kill_all()

    print('\n=== RESULT ===')
    print(f'build_applied={p.build_result} recruit_applied={p.recruit_result}')
    print(f'available_seen={p.available}')
    print(f'VERDICT: {"PASS" if p.build_result else "CHECK"} (build=协议+游戏双验收)')
    return 0 if p.build_result else 3

if __name__=='__main__':
    sys.exit(main())
