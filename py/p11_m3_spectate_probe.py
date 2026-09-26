#!/usr/bin/env python3
"""
T13.11 M3 探针 v1 — 第 3 连接（观战位）存活验证
=================================================
拓扑 (单机, 3030):
  [VCMI_server]
    +-- Python   (cid=1, host->让位, 红方模型位, EndTurn 占位)
    +-- client1  (cid=2, guest, onlyai, --testmap 装图, 蓝方 = Nullkiller2)
    +-- client3  (cid=3, headless onlyai, 无 --testmap, 纯 join lobby = 观战位模拟)

背景: P8-E (09-15) 实测 3 客户端 join Twins 后 14LobbyStartGame → server NEW_GAME 崩
("Picking random factions")。09-16 server robustness (#205) 修过包处理 → 本探针复验
现状 server 对 3 连接 2 slot 是否仍崩。

判定:
  1. server 存活 + 对局开始 (14LobbyStartGame)
  2. 红蓝交替照常 (>=4 轮) + 蓝方 NK2 动作包 > 0
  3. client3 进程存活 (join lobby 后不被 server 掐死)
  4. server log 无 "Disaster happened"/"Crash info"
  5. client3 log 无 LoadLibrary 失败/异常退出
若 PASS → 第 3 连接存活 → GUI 非 headless 观战画面可走同路径 (人工 join)。
若 FAIL (server 崩) → 治本路线: fork server 3 连接修复 (重编 server)。
"""
import sys, os, time, uuid as uuidlib, subprocess, threading, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.packs import LobbyClientConnected

HOST = '127.0.0.1'
PORT = 3030
BIN = r'D:\vcmi-fork-build\bin'
MAP = r'Maps/Twins.h3m'
TMP = r'C:\Users\Administrator\AppData\Local\Temp'

MY_COLOR = 0
MY_NAME = 'P11M3Host'

RECV_CC = re.compile(r'Received CPack of type 20LobbyClientConnected')
RECV_LEAD = re.compile(r'Player (\w+) will be lead by (\S+)')
AI_ACT_TIDS = {86, 95, 100, 106, 109, 111, 115, 117, 118, 121, 125, 132, 135}


def kill_all():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


def count_pattern(path, pattern):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for line in f if pattern.search(line))
    except FileNotFoundError:
        return 0


def grep_log(path, flag):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return any(flag in line for line in f)
    except FileNotFoundError:
        return False


def find_lead_by(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                m = RECV_LEAD.search(line)
                if m:
                    return m.group(1), m.group(2)
    except FileNotFoundError:
        pass
    return None, None


class P11M3:
    def __init__(self):
        self.srv = self.blue_cli = self.obs_cli = None
        self.conn = VCMITCPConnection(HOST, PORT)
        self.running = True
        self.turn_seq = []
        self.blue_act_count = 0
        self._in_blue_turn = False
        self.endturn_acked = 0

    def start_server(self):
        log = open(f'{TMP}\\p11m3_srv.log', 'w')
        self.srv = subprocess.Popen([os.path.join(BIN, 'VCMI_server.exe'), f'--port={PORT}'],
                                    cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(9)
        return self.srv.poll() is None

    def start_client(self, logname, role):
        """role: 'blue'=装图蓝方 | 'obs'=第3连接观战位。
        obs 加 --spectate (fork 原生参数, L171 'enable spectator interface for AI-only games')
        → testmap '摘自己'(L904 setPlayer) 后以 spectate 身份存活, 不走 0x98 崩的默认非 slot 路径。"""
        log = open(f'{TMP}\\{logname}', 'w')
        env = dict(os.environ)
        env['VCMI_TESTMAP_ONLYAI'] = '1'
        cmd = [os.path.join(BIN, 'VCMI_client.exe'), '--testmap', MAP,
               '--donotstartserver', '--serverport', str(PORT)]
        if role == 'obs':
            cmd += ['--spectate']   # 观战位: headless 由 spectate 自含, 不加 --headless
        else:
            cmd += ['--headless']
        return subprocess.Popen(cmd, cwd=BIN, stdout=log, stderr=subprocess.STDOUT, env=env)

    def host_join(self):
        if not self.conn.connect():
            return False
        threading.Thread(target=self.recv_loop, daemon=True).start()
        lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=[MY_NAME], mode=0)
        self.conn.send_frame(lcc.to_bytes())
        print('[H] python(host,红) 已连入')
        return True

    def recv_loop(self):
        from vcmi_protocol.serialization import BinaryDeserializer
        while self.running:
            data = self.conn.recv_frame()
            if data is None:
                if not self.conn.connected:
                    print('[RECV] 断开')
                    break
                continue
            if len(data) == 0:
                continue
            d = BinaryDeserializer(data)
            if d.read_bool():
                continue
            d.read_int()
            tid = d.read_int()
            if tid == 88:
                qid = d.read_int()
                player = d.read_int()
                print(f'[RECV] PlayerStartsTurn p{player}')
                self._in_blue_turn = (player == 1)
                self.turn_seq.append(f'p{player}')
                if player == MY_COLOR:
                    self.send_end_turn()
            elif tid == 84:
                self.endturn_acked += 1
                print(f'[RECV] PackageApplied (#ack={self.endturn_acked})')
            elif self._in_blue_turn and tid in AI_ACT_TIDS:
                self.blue_act_count += 1

    def send_end_turn(self):
        from vcmi_protocol.serialization import BinarySerializer
        self._n = getattr(self, '_n', 0) + 1
        s = BinarySerializer()
        s.write_bool(False); s.write_int(0); s.write_int(180)
        s.write_int(MY_COLOR); s.write_int(self._n)
        self.conn.send_frame(s.get_bytes())
        print(f'[SEND] EndTurn (player={MY_COLOR})')

    def send_change_host(self, cid):
        self.conn.send_frame(bytes([0, 0, 0xe1, 0x01, cid]))
        print(f'[SEND] ChangeHost({cid})')

    def srv_alive(self):
        if self.srv.poll() is not None:
            return False
        try:
            with open(f'{TMP}\\p11m3_srv.log', 'r', encoding='utf-8', errors='replace') as f:
                tail = f.readlines()[-30:]
            return not any('Disaster happened' in l or 'Crash info will be put' in l for l in tail)
        except Exception:
            return True

    def wait_until(self, pred, timeout, what):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if pred():
                print(f'  [OK] {what}')
                return True
            time.sleep(0.5)
        print(f'  [FAIL] {what} ({timeout}s 超时)')
        return False

    def count_alt_turns(self):
        alt = sum(1 for a, b in zip(self.turn_seq, self.turn_seq[1:]) if a != b)
        return alt + 1 if self.turn_seq else 0

    def run(self):
        print('=== T13.11 M3 v1: 第 3 连接(观战位)存活验证 ===')
        kill_all()

        results = {}
        results['server_alive'] = self.start_server()
        print(f'[1] server = {results["server_alive"]}')
        if not results['server_alive']:
            return 2

        results['host_joined'] = self.host_join()
        print(f'[2] python(红) 连入 = {results["host_joined"]}')
        if not results['host_joined']:
            self.cleanup()
            return 2
        time.sleep(1)

        # client1 (蓝 NK2)
        self.blue_cli = self.start_client('p11m3_blue.log', role='blue')
        results['blue_joined'] = self.wait_until(
            lambda: count_pattern(f'{TMP}\\p11m3_srv.log', RECV_CC) >= 2, 25,
            'client1(蓝) 连入')
        print(f'[3] client1(蓝) = {results["blue_joined"]}')

        # 观战位 client3 (同 testmap 形态 join lobby) — 3 连接全在 SetMap 前 = P8-E 崩溃时序复验
        self.obs_cli = self.start_client('p11m3_obs.log', role='obs')
        results['obs_joined'] = self.wait_until(
            lambda: count_pattern(f'{TMP}\\p11m3_srv.log', RECV_CC) >= 3, 40,
            'client3(观战位) 连入 (第 3 个 ClientConnected)')
        print(f'[4] client3(观战位) = {results["obs_joined"]}')

        # 三 CC 齐后再 ChangeHost (client1 连入至今 < 10s 窗口内)
        self.send_change_host(2)

        results['game_started'] = self.wait_until(
            lambda: grep_log(f'{TMP}\\p11m3_srv.log', 'Received CPack of type 14LobbyStartGame'), 50,
            '对局开始')
        print(f'[5] 对局开始 = {results["game_started"]}')

        lead_color, lead_ai = None, None
        self.wait_until(lambda: find_lead_by(f'{TMP}\\p11m3_blue.log')[0] is not None, 30,
                        '蓝方 AI 身份')
        lead_color, lead_ai = find_lead_by(f'{TMP}\\p11m3_blue.log')
        results['blue_ai'] = lead_ai
        print(f'[6] 蓝方 AI = {lead_ai}')

        t0 = time.time()
        while time.time() - t0 < 150:
            if self.count_alt_turns() >= 5 and self.blue_act_count > 0:
                break
            time.sleep(1)
        results['alt_turns'] = self.count_alt_turns()
        results['blue_actions'] = self.blue_act_count
        results['endturn_acked'] = self.endturn_acked
        results['server_no_crash'] = self.srv_alive()
        results['procs'] = {'server': self.srv.poll() is None,
                            'blue': self.blue_cli.poll() is None,
                            'observer': self.obs_cli.poll() is None}
        results['observer_log_clean'] = not grep_log(f'{TMP}\\p11m3_obs.log', 'LoadLibraryW failed')
        # 蓝方身份以 server 侧受控为准 (蓝方 client 摘 slot 后自身 log 可能无 lead by)
        results['blue_ai_server'] = grep_log(f'{TMP}\\p11m3_srv.log', 'Player color 1 will be controlled from connection 2')
        print(f'[7] 交替={results["alt_turns"]} NK2动作={results["blue_actions"]} '
              f'ack={results["endturn_acked"]} 无崩={results["server_no_crash"]} '
              f'进程={results["procs"]} obs日志净={results["observer_log_clean"]} '
              f'server蓝方=cid2:{results["blue_ai_server"]}')

        self.running = False
        self.conn.disconnect()
        self.cleanup()

        # 核心判据 = 观战位(client3)存活 + 对局照常 (M3 目标: 人类观战 client 不崩)
        verdict = (results['server_alive'] and results['game_started']
                   and results['alt_turns'] >= 4 and results['blue_actions'] > 0
                   and results['server_no_crash']
                   and results['procs']['server'] and results['procs']['blue']
                   and results['procs']['observer'])
        import json
        rpt = {'ts': time.strftime('%Y-%m-%d %H:%M:%S'), 'results': results,
               'verdict': 'PASS' if verdict else 'FAIL'}
        rp = f'{TMP}\\p11m3_report.json'
        Path(rp).write_text(json.dumps(rpt, ensure_ascii=False, indent=2))
        print(f"\n=== T13.11 M3 v1 结果: {rpt['verdict']} ===")
        print(f"报告: {rp}")
        return 0 if verdict else 3

    def cleanup(self):
        for p in (self.obs_cli, self.blue_cli, self.srv):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        kill_all()


if __name__ == '__main__':
    sys.exit(P11M3().run())
