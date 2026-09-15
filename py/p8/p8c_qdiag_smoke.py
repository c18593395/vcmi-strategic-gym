#!/usr/bin/env python3
"""
opsx add-query-reply-live-verification — Task 1.2 QUERY-DIAG 冒烟 (最终版)
==========================================================================
前置修复:
- fork 补丁: CServerHandler onConnectionFailed/onTimer 加 ENGINE 空指针防护 (headless 不再崩)
- 配置: ~/.config/vcmi/settings.json server.localPort=3030 (实测 client 真正读的端口)
- server 必须先监听 (client 连不上会重试, 有 server 在即连上)
流程: vcmiserver(diag=1) -> client1 --testmap guest -> ChangeHost -> 开局 -> 抓 QUERY-DIAG
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re, socket

sys.path.insert(0, '/mnt/d/Bigdata/hero3_fresh/py')
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected

HOST = '127.0.0.1'; PORT = 3030
BIN = '/home/administrator/vcmi-native/rel/bin'
MAP = 'Maps/A Warm and Familiar Place.h3m'
MY_COLOR = 0
SRV_LOG = '/tmp/qdiag_srv.log'
CLI_LOG = '/tmp/qdiag_cli.log'
DUR = 120

LOBBY_TIDS = {216:'LobbyClientConnected',218:'LobbyChatMessage',223:'LobbyPrepareStartGame',224:'LobbyStartGame',
              226:'LobbyUpdateState',229:'LobbySetMap',225:'LobbyChangeHost'}

def tid_name(t):
    return LOBBY_TIDS.get(t) or f'?{t}'

def kill_all():
    subprocess.run(['pkill', '-f', 'vcmiserver'], capture_output=True)
    subprocess.run(['pkill', '-f', 'vcmiclient'], capture_output=True)
    time.sleep(1)

class Probe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self.client2_seen = False
        self.game_started = False
        self.running = True
        self.turn_events = []
        self._us_count = 0
        self._n = 0

    def _req(self):
        self._n += 1
        return self._n

    def recv_loop(self):
        while self.running:
            data = self.conn.recv_frame()
            if data is None:
                if not self.conn.connected:
                    print('[RECV] 断开', flush=True); break
                continue
            if len(data) == 0:
                continue
            d = BinaryDeserializer(data)
            if d.read_bool():
                continue
            d.read_int()
            tid = d.read_int()
            print(f'[RECV] {len(data):6d}B tid={tid} {tid_name(tid)}', flush=True)
            if tid == 226:
                self._us_count += 1
                if self._us_count >= 2:
                    self.client2_seen = True
            elif tid == 224:
                self.game_started = True
            elif tid == 88:
                qid = d.read_int()
                player = d.read_int()
                self.turn_events.append(f'turn_start p{player}')
                if player == MY_COLOR:
                    self.send_end_turn()

    def send_end_turn(self):
        s = BinarySerializer()
        s.write_bool(False); s.write_int(0); s.write_int(180)
        s.write_int(0)
        s.write_int(self._req())
        self.conn.send_frame(s.get_bytes())
        print('[SEND] EndTurn (player=0)', flush=True)

def main():
    print('=== Task 1.2: QUERY-DIAG 冒烟 (ENGINE 防护补丁版) ===', flush=True)
    kill_all()
    env = dict(os.environ); env['VCMI_QUERY_DIAG'] = '1'
    srv_log = open(SRV_LOG, 'w')
    srv = subprocess.Popen([BIN + '/vcmiserver', f'--port={PORT}'],
                           cwd=BIN, stdout=srv_log, stderr=subprocess.STDOUT, env=env)
    # 注意: 不可做 "连了再断" 的探活 — fork 语义: 首个连接断开 = host 离开 -> server SHUTDOWN。
    # 直接让 python 真连接当第一个客户端, 重试直到 server 就绪。
    p = Probe()
    for attempt in range(20):
        if p.conn.connect():
            print(f'[0] python connected as first client after {attempt} retries', flush=True)
            break
        time.sleep(1)
    else:
        print('[FAIL] python(host) connect (20 attempts)'); return 1
    threading.Thread(target=p.recv_loop, daemon=True).start()
    lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['PyHost'], mode=0)
    p.conn.send_frame(lcc.to_bytes())
    print('[1] python(host) joined lobby', flush=True)
    time.sleep(1)

    cli_log = open(CLI_LOG, 'w')
    cenv = dict(os.environ); cenv['VCMI_TESTMAP_ONLYAI'] = '1'
    cli = subprocess.Popen([BIN + '/vcmiclient', '--testmap', MAP,
                            '--donotstartserver', '--headless'],
                           cwd=BIN, stdout=cli_log, stderr=subprocess.STDOUT, env=cenv)
    print(f'[2] client1 pid={cli.pid}', flush=True)

    t0 = time.time()
    while time.time() - t0 < 40 and not p.client2_seen:
        time.sleep(0.2)
    print(f'[3] client2_seen={p.client2_seen}', flush=True)

    p.conn.send_frame(bytes([0, 0, 0xe1, 0x01, 0x02]))   # LobbyChangeHost -> cid2
    print('[4] ChangeHost sent', flush=True)

    t0 = time.time()
    while time.time() - t0 < 90 and not p.game_started:
        time.sleep(0.5)
    print(f'[5] game_started={p.game_started} turns={len(p.turn_events)}', flush=True)

    t0 = time.time()
    while time.time() - t0 < DUR:
        time.sleep(1)

    p.running = False
    p.conn.disconnect()
    time.sleep(1)
    srv.terminate(); cli.terminate()
    time.sleep(1)
    srv.kill(); cli.kill()

    diag_lines, bad = [], []
    if os.path.exists(SRV_LOG):
        with open(SRV_LOG, errors='replace') as f:
            for line in f:
                m = re.search(r'\[QUERY-DIAG\] qid=(-?\d+) player=(\S+) type=(.*)', line)
                if m:
                    diag_lines.append(m.groups())
                low = line.lower()
                for kw in ('fishy', 'not allowed', 'not-allowed'):
                    if kw in low:
                        bad.append(line.strip()[:100])
    print('\n=== RESULT ===', flush=True)
    print(f'turn events: {p.turn_events[:12]}')
    print(f'QUERY-DIAG lines: {len(diag_lines)}')
    for q in diag_lines[:10]:
        print(f'  qid={q[0]} player={q[1]} type={q[2][:70]}')
    print(f'bad keywords: {len(bad)}')
    for b in bad[:5]:
        print(f'  {b}')
    ok = len(diag_lines) > 0 and len(bad) == 0
    print('VERDICT:', 'PASS' if ok else 'CHECK')
    return 0 if ok else 2

if __name__ == '__main__':
    sys.exit(main())
