#!/usr/bin/env python3
"""
P8-B 混人长局浸泡探针 (30min)
=============================
在 P8-B 方案 F (Python host + 真实 guest client + ChangeHost 让位) 基础上,
跑 30 分钟真实对局, 监控 server 崩溃 / client 断线 / 回合流转中断。

设计:
- fork server (VCMI_server.exe --port=3030)
- 真实 VCMI client (VCMI_TESTMAP_ONLYAI=1, 蓝方 ModelAI)
- Python 当 host (红方), 发 LobbyChangeHost 让位 + EndTurn 管红方回合
- 每 5min checkpoint: turn_count, 包统计, server/client 存活
- 30min 后汇总: 无崩溃/无断线/回合正常 → PASS

跑法:
  python py/p8/p8b_soak_30min.py
预计 30-35min, 退出码 0=PASS / 1=FAIL。
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, json, signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected, EndTurn

HOST = '127.0.0.1'; PORT = 3030; BIN = r'D:\vcmi-fork-build\bin'
MY_COLOR = 0   # Python 红方
MAP = r'Maps/Twins.h3m'
SRV_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8b_soak_srv.log'
CLI_LOG = r'C:\Users\Administrator\AppData\Local\Temp\p8b_soak_cli.log'
REPORT = r'C:\Users\Administrator\AppData\Local\Temp\p8b_soak_report.json'
DURATION = 1800   # 30min
CHECKPOINT = 300   # 每 5min

LOBBY_TIDS = {216:'LobbyClientConnected',217:'LobbyClientDisconnected',218:'LobbyChatMessage',
              221:'LobbyLoadProgress',223:'LobbyPrepareStartGame',224:'LobbyStartGame',
              226:'LobbyUpdateState',229:'LobbySetMap',225:'LobbyChangeHost',227:'LobbyShowMessage'}
GAME_TIDS = {88:'PlayerStartsTurn',116:'NewTurn',132:'BattleStart',135:'BattleResult',
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


class SoakProbe:
    def __init__(self):
        self.conn = VCMITCPConnection(HOST, PORT)
        self.srv_proc = None
        self.cli_proc = None
        self._us_count = 0
        self.client2_seen = False
        self.game_started = False
        self.running = True
        self.turn_count = 0
        self.end_turn_sent = False
        self._req = 0
        # 统计
        self.packets = {}      # tid → count
        self.disconnects = 0
        self.reconnects = 0
        self.checkpoints = []  # [{ts, turn, packets_total, srv_alive, cli_alive}]
        self.server_crash = False
        self.client_crash = False

    def next_req(self):
        self._req += 1
        return self._req

    def send_end_turn(self):
        s = BinarySerializer()
        s.write_bool(False); s.write_int(0); s.write_int(180)
        s.write_int(MY_COLOR)
        s.write_int(self.next_req())
        self.conn.send_frame(s.get_bytes())

    def recv_loop(self):
        while self.running:
            try:
                data = self.conn.recv_frame()
            except Exception as e:
                print(f'[RECV-ERR] {e}')
                time.sleep(0.5)
                continue
            if data is None:
                if not self.conn.connected:
                    self.disconnects += 1
                    print(f'[RECV] 断开 #{self.disconnects}, 尝试重连...')
                    time.sleep(2)
                    try:
                        self.conn.connect()
                        self.reconnects += 1
                        print(f'[RECV] 重连成功 #{self.reconnects}')
                    except Exception:
                        print('[RECV] 重连失败, 终止')
                        self.running = False
                        break
                continue
            if len(data) == 0:
                continue
            d = BinaryDeserializer(data)
            if d.read_bool():
                continue
            d.read_int()
            tid = d.read_int()
            self.packets[tid] = self.packets.get(tid, 0) + 1
            name = tid_name(tid)

            if tid == 226:
                self._us_count += 1
                if self._us_count >= 2:
                    self.client2_seen = True
            elif tid == 224:
                self.game_started = True
                print(f'[KEY] game_started=True')
            elif tid == 88:
                qid = d.read_int()
                player = d.read_int()
                if player == MY_COLOR and not self.end_turn_sent:
                    self.turn_count += 1
                    self.send_end_turn()
                    self.end_turn_sent = True
                    if self.turn_count % 20 == 0:
                        print(f'[TURN] 第 {self.turn_count} 回合')
                elif player != MY_COLOR:
                    pass
            elif tid == 102:
                self.end_turn_sent = False

    def checkpoint(self, ts_offset):
        srv_alive = self.srv_proc.poll() is None if self.srv_proc else False
        cli_alive = self.cli_proc.poll() is None if self.cli_proc else False
        total_pkts = sum(self.packets.values())
        cp = {'ts': time.strftime('%H:%M:%S'), 't_offset': ts_offset,
              'turn': self.turn_count, 'packets_total': total_pkts,
              'srv_alive': srv_alive, 'cli_alive': cli_alive,
              'disconnects': self.disconnects, 'reconnects': self.reconnects}
        self.checkpoints.append(cp)
        print(f'[CP] {cp["ts"]} turn={cp["turn"]} pkts={total_pkts} '
              f'srv={srv_alive} cli={cli_alive} disc={cp["disconnects"]}')
        if not srv_alive:
            self.server_crash = True
        if not cli_alive:
            self.client_crash = True

    def tail_server_log(self):
        """检查 server 日志是否有崩溃关键字"""
        try:
            if not os.path.exists(SRV_LOG):
                return
            bad_kws = ('fishy','not-allowed','CRASH','crash','TIMEOUT','abort',
                       'Assertion','terminate','signal 11','segfault')
            with open(SRV_LOG, 'r', errors='replace') as f:
                for line in f:
                    for kw in bad_kws:
                        if kw in line:
                            print(f'[SRV-WARN] [{kw}] {line.strip()[:120]}')
                            return
        except Exception:
            pass

    def run(self):
        print(f'=== P8-B 混人长局浸泡 ({DURATION}s) ===')
        kill_all()
        srv_log = open(SRV_LOG, 'w')
        self.srv_proc = subprocess.Popen([BIN + r'\VCMI_server.exe', f'--port={PORT}'],
                                          cwd=BIN, stdout=srv_log, stderr=subprocess.STDOUT)
        time.sleep(9)
        if self.srv_proc.poll() is not None:
            print('[FAIL] server 启动失败'); return 2

        if not self.conn.connect():
            print('[FAIL] connect'); return 1
        threading.Thread(target=self.recv_loop, daemon=True).start()
        lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=['SoakHost'], mode=0)
        self.conn.send_frame(lcc.to_bytes())
        print(f'[1] python(host) joined lobby')
        time.sleep(1)

        cli_log = open(CLI_LOG, 'w')
        env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI'] = '1'
        self.cli_proc = subprocess.Popen(
            [BIN + r'\VCMI_client.exe', '--testmap', MAP,
             '--donotstartserver', '--serverport', str(PORT), '--headless'],
            cwd=BIN, stdout=cli_log, stderr=subprocess.STDOUT, env=env)
        print(f'[2] client1 pid={self.cli_proc.pid}')

        # 等 client 连入
        t0 = time.time()
        while time.time() - t0 < 15 and not self.client2_seen:
            time.sleep(0.2)
        print(f'[3] client2_seen={self.client2_seen}')

        # ChangeHost 让位
        self.conn.send_frame(bytes([0, 0, 0xe1, 0x01, 0x02]))
        print('[4] ChangeHost sent')

        # 等游戏开始
        t0 = time.time()
        while time.time() - t0 < 40 and not self.game_started:
            time.sleep(0.5)
        print(f'[5] game_started={self.game_started}')
        if not self.game_started:
            self.running = False
            kill_all()
            return 2

        # 跑 DURATION 秒, 每 CHECKPOINT 记录
        t0 = time.time()
        next_cp = CHECKPOINT
        while time.time() - t0 < DURATION:
            time.sleep(1)
            elapsed = time.time() - t0
            if elapsed >= next_cp:
                self.checkpoint(int(elapsed))
                next_cp += CHECKPOINT
            # 定期 tail server log
            if int(elapsed) % 60 == 0:
                self.tail_server_log()
            # 检测崩溃
            if self.srv_proc and self.srv_proc.poll() is not None:
                print(f'[CRASH] server 在 t={int(elapsed)}s 崩溃, exit={self.srv_proc.returncode}')
                self.server_crash = True
                break
            if self.cli_proc and self.cli_proc.poll() is not None:
                print(f'[CRASH] client 在 t={int(elapsed)}s 崩溃, exit={self.cli_proc.returncode}')
                self.client_crash = True
                break

        # 收尾
        self.running = False
        time.sleep(1)
        if self.srv_proc and self.srv_proc.poll() is None:
            self.srv_proc.terminate()
            try: self.srv_proc.wait(timeout=5)
            except: self.srv_proc.kill()
        if self.cli_proc and self.cli_proc.poll() is None:
            self.cli_proc.terminate()
            try: self.cli_proc.wait(timeout=5)
            except: self.cli_proc.kill()
        kill_all()

        # 汇总
        total_pkts = sum(self.packets.values())
        report = {
            'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': DURATION,
            'turns': self.turn_count,
            'packets_total': total_pkts,
            'packets_breakdown': {str(k): v for k, v in sorted(self.packets.items())},
            'disconnects': self.disconnects,
            'reconnects': self.reconnects,
            'checkpoints': self.checkpoints,
            'server_crash': self.server_crash,
            'client_crash': self.client_crash,
            'verdict': None,
        }
        # 判定
        if not self.server_crash and not self.client_crash and self.turn_count >= 5:
            report['verdict'] = 'PASS'
            print(f'\n[VERDICT] PASS: 30min 无崩溃, {self.turn_count} 回合, '
                  f'{total_pkts} 包, {self.disconnects} 断线')
        else:
            report['verdict'] = 'FAIL'
            print(f'\n[VERDICT] FAIL: srv_crash={self.server_crash} '
                  f'cli_crash={self.client_crash} turns={self.turn_count}')

        with open(REPORT, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f'[REPORT] -> {REPORT}')
        return 0 if report['verdict'] == 'PASS' else 3


if __name__ == '__main__':
    sys.exit(SoakProbe().run())
