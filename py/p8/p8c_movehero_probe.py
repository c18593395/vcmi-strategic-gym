#!/usr/bin/env python3
"""
P8-C 阶段3 决策接入探针 — 在 P8-B 阶段2 (方案F) 基础上把"盲发 EndTurn"
换成真实战略决策第一步: MoveHero(182) 真实移动我方英雄, 再 EndTurn(180)。

数据源: 不解析 171KB StartGame blob, 而是读 server 日志中新增的
[SRV-DIAG] HERO OI=.. owner=.. pos=(x y z) 行 (CGameHandler::start 注入)。

验收: server 日志出现 MoveHero "successfully applied" 且无 fishy/not-allowed;
客户端收到 TryMoveHero(109) result=SUCCESS。
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected, MoveHero, EndTurn

HOST='127.0.0.1'; PORT=3030; BIN=r'D:\vcmi-fork-build\bin'
MY_COLOR = 0          # python = red
SRV_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8c_move_srv.log'
MOVES_PER_TURN = 3    # 每回合走 3 步

LOBBY_TIDS={216:'LobbyClientConnected',217:'LobbyClientDisconnected',218:'LobbyChatMessage',
            221:'LobbyLoadProgress',223:'LobbyPrepareStartGame',224:'LobbyStartGame',
            226:'LobbyUpdateState',229:'LobbySetMap',225:'LobbyChangeHost',227:'LobbyShowMessage'}
GAME_TIDS={88:'PlayerStartsTurn',116:'NewTurn',132:'BattleStart',135:'BattleResult',
           84:'PackageApplied',85:'SystemMessage',109:'TryMoveHero',115:'GiveHero',
           121:'NewObject',102:'PlayerEndsTurn',86:'SetResources',95:'SetObjectProperty',
           100:'SetAvailableCreatures',106:'SetHeroes',111:'SetAvailableHero',
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
        self._us_count = 0
        self.client2_seen = False
        self.game_started = False
        self.running = True
        self.heroes = {}        # oi -> dict(owner,pos)  从 SRV-DIAG 行解析
        self.my_hero_oi = None
        self.my_hero_pos = None
        self.turn_count = 0
        self.move_accepted = 0
        self.move_failed = 0
        self.try_move_results = []
        self._req = 0
        self.end_turn_sent = False

    def next_req(self):
        self._req += 1
        return self._req

    def send_pack(self, pack):
        self.conn.send_frame(pack.to_bytes())

    # ---------- server log tail: 提取英雄 OI ----------
    def poll_srv_diag(self):
        try:
            if not os.path.exists(SRV_LOG):
                return
            with open(SRV_LOG, 'r', errors='replace') as f:
                for line in f:
                    m = re.search(r'\[SRV-DIAG\] HERO OI=(\d+) owner=(-?\d+) pos=\((-?\d+) (-?\d+) (-?\d+)\)', line)
                    if m:
                        oi = int(m.group(1)); owner = int(m.group(2))
                        pos = (int(m.group(3)), int(m.group(4)), int(m.group(5)))
                        self.heroes[oi] = dict(owner=owner, pos=pos)
        except Exception as e:
            print(f'[DIAG] read err {e}')

    def resolve_my_hero(self):
        for oi, info in self.heroes.items():
            if info['owner'] == MY_COLOR:
                self.my_hero_oi = oi
                self.my_hero_pos = info['pos']
                return True
        return False

    # ---------- 决策: 朝敌方英雄方向走一步 (锚点坐标, 8邻域) ----------
    def decide_step(self):
        assert self.my_hero_pos is not None
        blue = next((i for i,v in self.heroes.items() if v['owner'] != MY_COLOR), None)
        target = self.heroes[blue]['pos'] if blue else (8, 8, 0)
        dx = (target[0] > self.my_hero_pos[0]) - (target[0] < self.my_hero_pos[0])
        dy = (target[1] > self.my_hero_pos[1]) - (target[1] < self.my_hero_pos[1])
        # 简单走位: 优先对角, 遇阻退化单轴 (server 会拒绝非法步, 我们记录失败数)
        return (self.my_hero_pos[0] + dx, self.my_hero_pos[1] + dy, self.my_hero_pos[2])

    def act_turn(self):
        """我方回合: 走 MOVES_PER_TURN 步 (逐步发, 每步等 TryMoveHero), 然后 EndTurn"""
        self.poll_srv_diag()
        if not self.resolve_my_hero():
            print('[ACT] 未解析到我方英雄 OI, 直接 EndTurn')
            self.send_pack(EndTurn(player=MY_COLOR, request_id=self.next_req()))
            return
        for i in range(MOVES_PER_TURN):
            step = self.decide_step()
            mh = MoveHero(path=[step], layer=0, hid=self.my_hero_oi,
                          transit=False, player=MY_COLOR, request_id=self.next_req())
            print(f'[ACT] MoveHero hid={self.my_hero_oi} {self.my_hero_pos} -> {step}')
            self.send_pack(mh)
            time.sleep(0.7)   # 等 server apply + TryMoveHero 广播回流
            self.poll_srv_diag()
        print('[ACT] EndTurn')
        self.send_pack(EndTurn(player=MY_COLOR, request_id=self.next_req()))

    # ---------- 收包循环 ----------
    def recv_loop(self):
        while self.running:
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
            name = tid_name(tid)
            if tid not in (100, 117, 118, 125, 86):
                print(f'[RECV] {len(data):6d}B tid={tid} {name}')
            if tid==226:
                self._us_count += 1
                if self._us_count >= 2:
                    self.client2_seen = True
            elif tid==224:
                self.game_started = True
            elif tid==109:
                # TryMoveHero wire: id + result + start(int3) + end(int3) + movePoints + fowRevealed(vector) + attackedFrom
                oid = d.read_int()
                result = d.read_int()      # 0=FAILED 1=SUCCESS 2=TELEPORT 3=BLOCKING_VISIT 4=EMBARK 5=DISEMBARK
                sx=d.read_int(); sy=d.read_int(); sz=d.read_int()
                ex=d.read_int(); ey=d.read_int(); ez=d.read_int()
                mp = d.read_int()
                fow_n = d.read_int()
                for _ in range(max(fow_n,0)):
                    d.read_int()
                self.try_move_results.append((oid, result))
                if oid == self.my_hero_oi:
                    if result >= 1:
                        self.move_accepted += 1
                        self.my_hero_pos = (ex,ey,ez)
                    else:
                        self.move_failed += 1
                        print(f'[TRY] OI={oid} FAILED ({sx},{sy},{sz})->({ex},{ey},{ez})')
            elif tid==88:
                qid = d.read_int(); player = d.read_int()
                if player == MY_COLOR and not self.end_turn_sent:
                    self.turn_count += 1
                    print(f'--- MY TURN #{self.turn_count} (qid={qid}) ---')
                    self.act_turn()
                    self.end_turn_sent = True
            elif tid==102:
                self.end_turn_sent = False
            elif tid==84:
                # PackageApplied: player + requestID + packType + result
                p=d.read_int(); req=d.read_int(); pt=d.read_int(); ok=d.read_bool()
                if pt==182:
                    print(f'[APPLIED] MoveHero req={req} result={ok}')

def main():
    print('=== P8-C probe: MoveHero real action on my turn ===')
    kill_all()
    srv_log = open(SRV_LOG,'w')
    srv = subprocess.Popen([BIN+r'\VCMI_server.exe','--port=3030'],cwd=BIN,stdout=srv_log,stderr=subprocess.STDOUT)
    time.sleep(9)

    p = Probe()
    if not p.conn.connect():
        print('[FAIL] connect'); return 1
    threading.Thread(target=p.recv_loop,daemon=True).start()
    lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['PyHost'], mode=0)
    p.conn.send_frame(lcc.to_bytes())
    print('[1] python(host) joined lobby')
    time.sleep(1)

    cli_log = open(r'C:\Users\Administrator\AppData\Local\Temp\p8c_move_cli.log','w')
    env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI']='1'
    cli = subprocess.Popen([BIN+r'\VCMI_client.exe','--testmap','Maps/Twins.h3m',
                            '--donotstartserver','--serverport','3030','--headless'],
                           cwd=BIN,stdout=cli_log,stderr=subprocess.STDOUT,env=env)
    print(f'[2] client1 pid={cli.pid}')

    t0=time.time()
    while time.time()-t0 < 15 and not p.client2_seen:
        time.sleep(0.2)
    print(f'[3] client2_seen={p.client2_seen}')

    p.conn.send_frame(bytes([0, 0, 0xe1, 0x01, 0x02]))   # LobbyChangeHost -> cid2
    print('[4] ChangeHost sent')

    t0=time.time()
    while time.time()-t0 < 40 and not p.game_started:
        time.sleep(0.5)
    print(f'[5] game_started={p.game_started}')
    if not p.game_started:
        p.running=False; return 2

    # 等 SRV-DIAG 英雄行出现
    t0=time.time()
    while time.time()-t0 < 10:
        p.poll_srv_diag()
        if p.resolve_my_hero(): break
        time.sleep(0.5)
    print(f'[6] heroes={p.heroes} my_hero_oi={p.my_hero_oi}')

    # 跑 3 个我方回合
    t0=time.time()
    while time.time()-t0 < 150 and p.turn_count < 3:
        time.sleep(0.5)
        p.poll_srv_diag()

    p.running=False
    p.conn.disconnect()
    time.sleep(0.5)
    kill_all()

    print('\n=== RESULT ===')
    print(f'turns_act={p.turn_count} move_accepted={p.move_accepted} move_failed={p.move_failed}')
    print(f'try_move_results={p.try_move_results}')
    ok = p.move_accepted > 0
    print(f'VERDICT: {"PASS" if ok else "FAIL"}')
    return 0 if ok else 3

if __name__=='__main__':
    sys.exit(main())
