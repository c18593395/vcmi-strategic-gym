#!/usr/bin/env python3
"""
T13.11 M1 探针 — 模型位(红,Python) vs 引擎AI(蓝,client1 onlyai) 拓扑闭环
==========================================================================
拓扑 (单机, 端口 3030, fork build 隔离, 不影响训练):
  [VCMI_server.exe --port=3030]
      +-- Python (cid=1, 先连当 host → 红方, 模型决策位; M1 用 EndTurn 占位)
      +-- client1 (cid=2, guest, headless, VCMI_TESTMAP_ONLYAI=1, --testmap 装图)
            ChangeHost 让位后作为 host 装图开局; slot 分配按连接序 (CVCMIServer.cpp
            updateStartInfoOnMapChange L635: SetMap 时 playerNames 顺序) → 蓝方=client1
            onlyai 模式下 client 给自己 slot 装引擎 AI (身份待实测: NK2 / ModelAI.so,
            从 p11_red.log "Player 1 will be lead by X" 实锤)

时序铁律: slot 分配发生在 SetMap 时刻, 两 client 必须在此之前都已连入 (P8-E 同序)。

判定 (server log + 包流):
  1. server 存活
  2. Python(host) 连入 → ChangeHost(2) 让位 (P8-E 范式, 踩坑 #202 窗口内)
  3. client1 连入装图开局 → server log "Received CPack of type 14LobbyStartGame"
  4. 红蓝回合交替 ≥6 轮, 红方(模型位) EndTurn 被受理 (84 PackageApplied ≥2)
  5. 蓝方引擎 AI 真实行动 → 蓝方回合窗口内动作类包 (86/95/100/106/109/111/115/117/118/
     121/125/132/135) 计数 > 0
  6. 蓝方 AI 身份实锤 → p11_red.log "Player 1 will be lead by X"
  7. 全程 server 无崩溃 + 双进程存活
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

MY_COLOR = 0          # Python 先连 = 红方 (模型决策位); 蓝方(1) = client1 引擎 AI
MY_NAME = 'P11RedHost'

RECV_CC = re.compile(r'Received CPack of type 20LobbyClientConnected')
RECV_STARTGAME = re.compile(r'Received CPack of type 14LobbyStartGame')
RECV_LEAD = re.compile(r'Player (\w+) will be lead by (\S+)')   # 09-27 实锤文案: "Player blue will be lead by ModelAI"
# 引擎 AI 走回合的动作类包 tid (gameplay 阶段 server 广播)
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
    """从 client log 提取 'Player <color> will be lead by <AI>' → (color, ai_name)。"""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                m = RECV_LEAD.search(line)
                if m:
                    return m.group(1), m.group(2)
    except FileNotFoundError:
        pass
    return None, None


class P11M1:
    def __init__(self):
        self.srv = self.blue_cli = None
        self.conn = VCMITCPConnection(HOST, PORT)
        self.running = True
        self.turn_seq = []           # 交替轮次记录
        self.blue_act_count = 0      # 蓝方回合窗口内动作类包计数
        self._in_blue_turn = False
        self.endturn_acked = 0       # 红方 EndTurn 受理回执计数

    # ---------- 进程 ----------
    def start_server(self):
        log = open(f'{TMP}\\p11_srv.log', 'w')
        self.srv = subprocess.Popen([os.path.join(BIN, 'VCMI_server.exe'), f'--port={PORT}'],
                                    cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(9)
        return self.srv.poll() is None

    def start_blue_client(self):
        """蓝方 = 真实 client (guest, onlyai → 引擎 AI 接管蓝方)。"""
        log = open(f'{TMP}\\p11_red.log', 'w')   # 名字沿用: 客户端日志
        env = dict(os.environ)
        env['VCMI_TESTMAP_ONLYAI'] = '1'
        self.blue_cli = subprocess.Popen([os.path.join(BIN, 'VCMI_client.exe'),
                                          '--testmap', MAP,
                                          '--donotstartserver', '--serverport', str(PORT), '--headless'],
                                         cwd=BIN, stdout=log, stderr=subprocess.STDOUT, env=env)
        return self.blue_cli

    # ---------- Python 红方协议 (P8-E 范式) ----------
    def host_join(self):
        if not self.conn.connect():
            return False
        threading.Thread(target=self.recv_loop, daemon=True).start()
        lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=[MY_NAME], mode=0)
        self.conn.send_frame(lcc.to_bytes())
        print('[H] python(host,红方) 已连入, LobbyClientConnected 已发')
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
            if tid == 88:   # PlayerStartsTurn: qid + player
                qid = d.read_int()
                player = d.read_int()
                print(f'[RECV] PlayerStartsTurn p{player} qid={qid}')
                self._in_blue_turn = (player == 1)
                self.turn_seq.append(f'p{player}')
                if player == MY_COLOR:
                    self.send_end_turn()
                else:
                    print('[SKIP] p1 回合 (引擎 AI 接管, 不代发)')
            elif tid == 84:  # PackageApplied (EndTurn 受理回执)
                self.endturn_acked += 1
                print(f'[RECV] PackageApplied (#ack={self.endturn_acked})')
            elif self._in_blue_turn and tid in AI_ACT_TIDS:
                self.blue_act_count += 1
                print(f'[RECV] 蓝方回合动作包 tid={tid} (#{self.blue_act_count})')
            else:
                print(f'[RECV] {len(data):6d}B tid={tid}')

    def send_end_turn(self):
        from vcmi_protocol.serialization import BinarySerializer
        self._n = getattr(self, '_n', 0) + 1
        s = BinarySerializer()
        s.write_bool(False); s.write_int(0); s.write_int(180)
        s.write_int(MY_COLOR); s.write_int(self._n)
        self.conn.send_frame(s.get_bytes())
        print(f'[SEND] EndTurn (player={MY_COLOR})')

    def send_change_host(self, new_host_cid: int):
        # LobbyChangeHost(225) body = newHostConnectionId (LVarInt), 手工构帧 (P8-E 同款)
        self.conn.send_frame(bytes([0, 0, 0xe1, 0x01, new_host_cid]))
        print(f'[SEND] LobbyChangeHost(newHost={new_host_cid})')

    # ---------- 判定辅助 ----------
    def srv_alive(self):
        if self.srv.poll() is not None:
            return False
        try:
            with open(f'{TMP}\\p11_srv.log', 'r', encoding='utf-8', errors='replace') as f:
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
        print(f'  [FAIL] {what} (等待 {timeout}s 超时)')
        return False

    def count_alt_turns(self):
        alt = 0
        for a, b in zip(self.turn_seq, self.turn_seq[1:]):
            if a != b:
                alt += 1
        return alt + 1 if self.turn_seq else 0

    def run(self):
        print('=== T13.11 M1: 模型位(红,Python host) vs 引擎AI(蓝,client1 onlyai) ===')
        kill_all()

        results = {}
        results['server_alive'] = self.start_server()
        print(f'[1] server 存活 = {results["server_alive"]}')
        if not results['server_alive']:
            print('[FAIL] server 启动失败, 中止')
            return 2

        # 2. Python 先连 (cid=1, host, 红方)
        results['host_joined'] = self.host_join()
        print(f'[2] python(host) 连入 = {results["host_joined"]}')
        if not results['host_joined']:
            self.cleanup()
            return 2
        time.sleep(1)

        # 3. 蓝方 client1 连入 (server log 第 2 个 ClientConnected)
        self.start_blue_client()
        results['blue_joined'] = self.wait_until(
            lambda: count_pattern(f'{TMP}\\p11_srv.log', RECV_CC) >= 2, 25,
            'client1 连入 (server log 第2个 ClientConnected)')
        print(f'[3] client1 连入 = {results["blue_joined"]}')

        # 4. 让位 (踩坑 #202, 落在 client1 mi_loop 10s 窗口内)
        self.send_change_host(2)

        # 5. 等开局
        results['game_started'] = self.wait_until(
            lambda: grep_log(f'{TMP}\\p11_srv.log', 'Received CPack of type 14LobbyStartGame'), 50,
            '对局开始 (server log 14LobbyStartGame)')
        print(f'[5] 对局开始 = {results["game_started"]}')

        # 6. 蓝方 AI 身份实锤 (非致命: 找不到只登记不判败)
        self.wait_until(
            lambda: find_lead_by(f'{TMP}\\p11_red.log')[0] is not None, 30,
            '蓝方 AI 身份 (client log "will be lead by")')
        lead_color, lead_ai = find_lead_by(f'{TMP}\\p11_red.log')
        results['blue_ai_color'], results['blue_ai_name'] = lead_color, lead_ai
        print(f'[6] 蓝方 AI = {lead_ai} (color={lead_color})')

        # 7. 观察 3 分钟: 红蓝交替 + 蓝方 AI 动作
        t0 = time.time()
        while time.time() - t0 < 180:
            if self.count_alt_turns() >= 6 and self.blue_act_count > 0:
                break
            time.sleep(1)
        results['alt_turns'] = self.count_alt_turns()
        results['blue_ai_actions'] = self.blue_act_count
        results['endturn_acked'] = self.endturn_acked
        results['server_no_crash'] = self.srv_alive()
        results['procs'] = {'server': self.srv.poll() is None,
                            'blue_cli': self.blue_cli.poll() is None}
        print(f'[7] 交替轮次={results["alt_turns"]} 蓝方AI动作包={results["blue_ai_actions"]} '
              f'EndTurn受理={results["endturn_acked"]} 无崩溃={results["server_no_crash"]} '
              f'进程={results["procs"]}')

        self.running = False
        self.conn.disconnect()
        self.cleanup()

        # ---------- 汇总 ----------
        verdict = (results['server_alive'] and results['host_joined']
                   and results['blue_joined'] and results['game_started']
                   and results['alt_turns'] >= 6
                   and results['blue_ai_actions'] > 0
                   and results['endturn_acked'] >= 2
                   and results['server_no_crash']
                   and all(results['procs'].values()))
        import json
        rpt = {'ts': time.strftime('%Y-%m-%d %H:%M:%S'), 'results': results,
               'verdict': 'PASS' if verdict else 'FAIL'}
        rp = f'{TMP}\\p11_m1_report.json'
        Path(rp).write_text(json.dumps(rpt, ensure_ascii=False, indent=2))
        print(f"\n=== T13.11 M1 结果: {rpt['verdict']} ===")
        print(f"蓝方AI身份: {results['blue_ai_name']}")
        print(f"报告: {rp}")
        return 0 if verdict else 3

    def cleanup(self):
        for p in (self.blue_cli, self.srv):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        kill_all()


if __name__ == '__main__':
    sys.exit(P11M1().run())
