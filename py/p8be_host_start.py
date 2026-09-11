
#!/usr/bin/env python3
"""
P8-B 阶段2 方案E — Python 先连当 host (常驻), client1 guest 装地图, Python 发 StartGame
"""
import sys, os, time, uuid as uuidlib, subprocess, threading

sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected

HOST='127.0.0.1'; PORT=3030; BIN=r'D:\vcmi-fork-build\bin'
MY_COLOR = 0   # Python 占红方 (player color 0)；蓝方 = ModelAI 客户端自己管回合

LOBBY_TIDS={216:'LobbyClientConnected',217:'LobbyClientDisconnected',218:'LobbyChatMessage',
            221:'LobbyLoadProgress',223:'LobbyPrepareStartGame',224:'LobbyStartGame',
            226:'LobbyUpdateState',229:'LobbySetMap',227:'LobbyShowMessage'}
GAME_TIDS={88:'PlayerStartsTurn',116:'NewTurn',132:'BattleStart',135:'BattleResult',
           84:'PackageApplied',85:'SystemMessage',109:'TryMoveHero',115:'GiveHero',
           121:'NewObject',102:'PlayerEndsTurn',86:'SetResources',95:'SetObjectProperty',
           100:'SetAvailableCreatures',106:'SetHeroes',111:'SetAvailableHero',
           117:'SetObjects',118:'SetSetters',125:'SetPlayerInfo'}

def tid_name(t):
    return LOBBY_TIDS.get(t) or GAME_TIDS.get(t) or f'?{t}'

def kill_all():
    for exe in ('VCMI_server.exe','VCMI_client.exe'):
        subprocess.run(['taskkill','/F','/IM',exe],capture_output=True)
    time.sleep(1)

class Probe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self.lobby_state = None
        self.map_set = False
        self.client2_seen = False
        self._us_count = 0
        self.game_started = False
        self.turn_events = []
        self.running = True

    def send_pack(self, type_id, body=b''):
        s = BinarySerializer()
        s.write_bool(False)   # isNull
        s.write_int(0)        # pid
        s.write_int(type_id)  # tid
        s.write_raw(body)
        return self.conn.send_frame(s.get_bytes())

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
            print(f'[RECV] {len(data):6d}B tid={tid} {name}')
            if tid==226:
                self.map_set = True   # UpdateState 广播
                self._us_count += 1
                if self._us_count >= 2:
                    self.client2_seen = True
            elif tid==224:
                self.game_started = True
            elif tid==88:
                # PlayerStartsTurn body = queryID(LVarInt) + player(LVarInt)
                qid = d.read_int()
                player = d.read_int()
                self.turn_events.append(f'turn_start p{player}')
                # 只在红方(0)回合发 EndTurn；蓝方(1)回合由 ModelAI 客户端自己管
                if player == MY_COLOR:
                    self.send_end_turn()
                else:
                    print(f'[SKIP] 非我回合 (p{player}), 不发 EndTurn')
            elif tid==116:
                self.turn_events.append('new_turn')

    def send_end_turn(self):
        s = BinarySerializer()
        s.write_bool(False); s.write_int(0); s.write_int(180)
        s.write_int(0)  # player = 0 (red)
        s.write_int(self._req())
        self.conn.send_frame(s.get_bytes())
        print('[SEND] EndTurn (player=0)')

    def _req(self):
        self._n = getattr(self,'_n',0)+1
        return self._n

def main():
    print('=== P8-B phase2 PLAN E: python host + client1 guest map-setter ===')
    kill_all()
    srv_log = open(r'C:\Users\Administrator\AppData\Local\Temp\p8be_srv.log','w')
    srv = subprocess.Popen([BIN+r'\VCMI_server.exe','--port=3030'],cwd=BIN,stdout=srv_log,stderr=subprocess.STDOUT)
    time.sleep(9)

    p = Probe()
    if not p.conn.connect():
        print('[FAIL] python(host) connect'); return 1
    threading.Thread(target=p.recv_loop,daemon=True).start()
    lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['PyHost'], mode=0)
    p.conn.send_frame(lcc.to_bytes())
    print('[1] python(host) joined lobby')
    time.sleep(1)

    cli_log = open(r'C:\Users\Administrator\AppData\Local\Temp\p8be_cli.log','w')
    env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI']='1'
    cli = subprocess.Popen([BIN+r'\VCMI_client.exe','--testmap','Maps/Twins.h3m',
                            '--donotstartserver','--serverport','3030','--headless'],
                           cwd=BIN,stdout=cli_log,stderr=subprocess.STDOUT,env=env)
    print(f'[2] client1(guest map-setter) pid={cli.pid}')

    # 等 client1 加入 (第2个 UpdateState = client1 连接广播)
    t0=time.time()
    while time.time()-t0 < 10:
        if p.client2_seen: break
        time.sleep(0.2)
    print(f'[3] client2_seen={p.client2_seen}')

    # 方案 F (0911 实锤): SetMap 是 host-only (visitForLobby 默认 isClientHost), guest 的 SetMap
    # 全被静默拒绝 → mi 恒 NULL → client1 mi_loop 10s 超时。解法 = python(host) 用 LobbyChangeHost(225)
    # 把 host 让给 client1(cid=2), client1 后续 SetMap 被接受 → 正常装图+开局。
    # body = newHostConnectionId (GameConnectionID, LVarInt) = 2
    import struct as _s
    # 手工构帧: isNull(00)+pid(00)+tid(225=e1 01)+cid(02)
    frame = bytes([0, 0, 0xe1, 0x01, 0x02])
    p.conn.send_frame(frame)
    print('[4] host sent LobbyChangeHost(newHost=2)')

    # 等 client1 装图开局
    t0=time.time()
    while time.time()-t0 < 30:
        if p.game_started: break
        time.sleep(0.5)
    print(f'[5] game_started={p.game_started} (waited {time.time()-t0:.1f}s)')

    # 观察游戏流 30s
    t0=time.time()
    while time.time()-t0 < 30:
        if p.turn_events:
            break
        time.sleep(0.5)
    print(f'[6] turn_events={p.turn_events[:5]}')
    p.running=False
    p.conn.disconnect()
    print(f"RESULT: game_started={p.game_started} turns={len(p.turn_events)}")
    return 0 if p.game_started else 2

if __name__=='__main__':
    sys.exit(main())
