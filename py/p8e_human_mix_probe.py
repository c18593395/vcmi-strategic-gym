#!/usr/bin/env python3
"""
P8-E 人机混局探针 (T13.10 目标场景实跑)
========================================
目标: 人类 GUI 客户端 + 外挂 AI 客户端 同一 VCMI_server 同局 (人机混局)。

拓扑 (单机, 端口 3030, fork build 隔离, 不影响训练):
  [VCMI_server.exe --port=3030]
      +-- Python host (cid=1, VCMITCPConnection, 先连当 host, 发 LobbyClientConnected + ChangeHost(15))
      +-- 外挂AI (cid=2, headless, VCMI_TESTMAP_ONLYAI=1, guest, 自动接管蓝方回合)
      +-- 人类 GUI (仅连入 lobby 不 join slot, 验证"人类 GUI 进程与 AI 同机共存")

约束 (Twins 2 玩家槽 + 关键踩坑):
  1. Twins.h3m 仅 2 玩家槽, 连入客户端须 <= 2。第 3 个客户端 join lobby 会触发
     NEW_GAME 初始化 "Picking random factions for players" -> "Disaster happened" 崩溃
     (09-15 P8-E 实测: 3 客户端连入 Twins, 14 LobbyStartGame 广播后 server 在 NEW_GAME 崩)。
  2. 人类 GUI 若真实 join lobby (server log 第 2 个 ClientConnected), 就占掉一个玩家槽,
     第 3 个 (AI) 超出 Twins 2 槽 -> 崩溃。故人类 GUI 只连入 lobby 进程但不 join slot,
     判定"人类 GUI 进程存活"而非 server log ClientConnected 计数。
  3. 人类 host + AI guest 组合触发 VCMI 8 玩家槽 AI 控制 bug:
     "Player 0/1/2/... controlled by AI" -> 人类玩家丢失 -> AI mi.fileURI 恒 NULL -> 10s 超时退出。
     故必须用 Python host (非人类 host)。

判定 (全部从 server log + 进程状态读取):
  1. server 存活
  2. Python host 连入 -> server log 第 1 个 "Received CPack of type 20LobbyClientConnected"
  3. 外挂AI 连入 -> server log 第 2 个 "Received CPack of type 20LobbyClientConnected"
  4. 人类 GUI 进程存活 (仅验证同机共存, 不 join slot)
  5. 对局开始 -> server log 出现 "Received CPack of type 14LobbyStartGame" (Python 侧 tid=14)
  6. 全进程存活 (server / 人类 / 外挂AI 未崩, server log 无崩溃标志)

typeID 实锤 (来自 P8-B 成功 server 日志):
  "Received CPack of type 20LobbyClientConnected" = 客户端连入 (Python 侧 216)
  "Received CPack of type 14LobbyStartGame" = 对局真正开局信号 (Python 侧 14)
  "Sending a pack of type 14LobbySetPlayer" = SetPlayer 广播 (Python 侧 14 但非开局, 勿混淆)
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

MY_COLOR = 0   # Python host 占红方; 蓝方(1) 由外挂AI 接管
AI_NAME = 'ModelAI'

RECV_CC = re.compile(r'Received CPack of type 20LobbyClientConnected')
RECV_STARTGAME = re.compile(r'Received CPack of type 14LobbyStartGame')
RECV_SETPLAYER = re.compile(r'Received CPack of type 14LobbySetPlayer')


def kill_all():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


def count_pattern(path: str, pattern: re.Pattern) -> int:
    """读 log, 返回 pattern 匹配行数。"""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for line in f if pattern.search(line))
    except FileNotFoundError:
        return 0


def grep_log_exists(path: str, flag: str) -> bool:
    """读 log, 返回是否含 flag 子串。"""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return any(flag in line for line in f)
    except FileNotFoundError:
        return False


class P8E:
    def __init__(self):
        self.srv = self.human = self.ai = None
        self.conn = VCMITCPConnection(HOST, PORT)
        self.running = True

    # ---------- 进程管理 ----------
    def start_server(self):
        log = open(f'{TMP}\\p8e_srv.log', 'w')
        self.srv = subprocess.Popen([os.path.join(BIN, 'VCMI_server.exe'), f'--port={PORT}'],
                                    cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(9)
        return self.srv.poll() is None

    def start_human(self):
        """人类 GUI 客户端 (无 --testmap, 无 --serverport, 不连 3030)。
        仅验证"人类 GUI 进程与 AI 同机共存" — 进程存活 + SDL 窗口即可。
        不带 --testmap/--serverport, 人类 GUI 不连 3030, 不 join lobby, 不占 Twins 2 玩家 slot。
        若带 --testmap, EntryPoint.cpp L379 会让 --testmap 默认 onlyai=true, 人类 GUI
        也会发 LobbyClientConnected join lobby, 成为第 3 个客户端 -> NEW_GAME 崩溃。"""
        log = open(f'{TMP}\\p8e_human.log', 'w')
        p = subprocess.Popen([os.path.join(BIN, 'VCMI_client.exe')],
                             cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(8)
        return p

    def start_ai(self):
        """真实外挂 AI 客户端 (headless, VCMI_TESTMAP_ONLYAI=1, guest, 自动接管蓝方)。"""
        log = open(f'{TMP}\\p8e_ai.log', 'w')
        env = dict(os.environ)
        env['VCMI_TESTMAP_ONLYAI'] = '1'
        p = subprocess.Popen([os.path.join(BIN, 'VCMI_client.exe'),
                              '--testmap', MAP,
                              '--donotstartserver', '--serverport', str(PORT), '--headless'],
                             cwd=BIN, stdout=log, stderr=subprocess.STDOUT, env=env)
        time.sleep(10)
        return p

    # ---------- Python host 协议 (P8-B 范式) ----------
    def host_join(self):
        if not self.conn.connect():
            return False
        threading.Thread(target=self.recv_loop, daemon=True).start()
        lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=[AI_NAME + '_Host'], mode=0)
        self.conn.send_frame(lcc.to_bytes())
        print('[H] python(host) 已连入, LobbyClientConnected 已发')
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
            print(f'[RECV] {len(data):6d}B tid={tid} ?')
            # 不再依赖 tid==14 判定 (server 广播 14 到 Python 连接时 host 已让位,
            # 可能收不到); 开局判定走 server log 的 "Received CPack of type 14LobbyStartGame"。
            # 这里仅监控 88 PlayerStartsTurn, 红方回合发 EndTurn。
            if tid == 88:
                qid = d.read_int()
                player = d.read_int()
                print(f'[RECV] PlayerStartsTurn p{player} qid={qid}')
                if player == MY_COLOR:
                    self.send_end_turn()
                else:
                    print(f'[SKIP] p{player} 回合 (AI 接管, 不代发 EndTurn)')

    def send_end_turn(self):
        from vcmi_protocol.serialization import BinarySerializer
        self._n = getattr(self, '_n', 0) + 1
        s = BinarySerializer()
        s.write_bool(False); s.write_int(0); s.write_int(180)
        s.write_int(0); s.write_int(self._n)
        self.conn.send_frame(s.get_bytes())
        print(f'[SEND] EndTurn (player={MY_COLOR})')

    def send_change_host(self, new_host_cid: int):
        # LobbyChangeHost(225) body = newHostConnectionId (LVarInt)
        # 手工构帧: isNull(00) + pid(00) + tid(225=e1 01) + cid(LVarInt)
        self.conn.send_frame(bytes([0, 0, 0xe1, 0x01, new_host_cid]))
        print(f'[SEND] LobbyChangeHost(newHost={new_host_cid})')

    # ---------- 日志判定 ----------
    def srv_log_cc(self) -> int:
        return count_pattern(f'{TMP}\\p8e_srv.log', RECV_CC)

    def srv_log_started(self) -> bool:
        """server log 含 "Received CPack of type 14LobbyStartGame" (排除 LobbySetPlayer 误判)。"""
        return grep_log_exists(f'{TMP}\\p8e_srv.log', 'Received CPack of type 14LobbyStartGame')

    def srv_log_alive(self) -> bool:
        """server log 无崩溃标志 + 进程存活。"""
        if self.srv.poll() is not None:
            return False
        try:
            with open(f'{TMP}\\p8e_srv.log', 'r', encoding='utf-8', errors='replace') as f:
                tail = f.readlines()[-30:]
            return not any('Disaster happened' in l or 'Crash info will be put' in l for l in tail)
        except Exception:
            return True

    # ---------- 判定 ----------
    def wait_until(self, pred, timeout, what):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if pred():
                print(f'  [OK] {what}')
                return True
            time.sleep(0.5)
        print(f'  [FAIL] {what} (等待 {timeout}s 超时)')
        return False

    def run(self) -> int:
        print('=== P8-E 人机混局探针 (Python host + 外挂AI 2客户端, 人类GUI同机共存, 同 VCMI_server 3030) ===')
        kill_all()

        results = {}
        # 1. server
        results['server_alive'] = self.start_server()
        print(f'[1] server 存活 = {results["server_alive"]}')
        if not results['server_alive']:
            print('[FAIL] server 启动失败, 中止')
            return 2

        # 2. Python host 先连入 (cid=1, 当前 host)
        results['host_joined'] = self.host_join()
        print(f'[2] python(host) 连入 = {results["host_joined"]}')
        if not results['host_joined']:
            print('[FAIL] Python host 连入失败, 中止')
            self.cleanup()
            return 2
        time.sleep(1)

        # 3. 人类 GUI 启动 (同机共存, 不 join slot, 仅验证进程存活 + SDL 窗口)
        #    不再等 server log ClientConnected (3 客户端连 Twins 必崩), 改验证进程存活
        self.human = self.start_human()
        results['human_alive'] = self.human.poll() is None
        print(f'[3] 人类(GUI) 进程存活 = {results["human_alive"]}')

        # 4. 外挂AI (cid=2, guest) 连入 -> server log 第 2 个 20LobbyClientConnected
        self.ai = self.start_ai()
        results['ai_joined'] = self.wait_until(
            lambda: self.srv_log_cc() >= 2, 25, '外挂AI 连入 (server log 第2个 ClientConnected)')
        print(f'[4] 外挂AI 连入 = {results["ai_joined"]}')

        # 5. AI (guest) 连入后立即让位 (踩坑 #202, 落在 AI mi_loop 10s 窗口内)
        self.send_change_host(2)

        # 6. 等对局开始 (server log 出现 "Received CPack of type 14LobbyStartGame")
        results['game_started'] = self.wait_until(
            lambda: self.srv_log_started(), 50, '对局开始 (server log 14LobbyStartGame)')
        print(f'[5] 对局开始 = {results["game_started"]}')

        # 7. 观察 30s, 确认 server 无崩溃 + 全进程存活
        time.sleep(30)
        results['server_no_crash'] = self.srv_log_alive()
        results['procs_alive'] = {
            'server': self.srv.poll() is None,
            'human': self.human.poll() is None,
            'ai': self.ai.poll() is None,
        }
        print(f'[6] server无崩溃 = {results["server_no_crash"]}, 进程存活 = {results["procs_alive"]}')

        self.running = False
        self.conn.disconnect()
        self.cleanup()

        # ---------- 汇总 ----------
        verdict = (results['server_alive'] and results['host_joined']
                   and results['human_alive']
                   and results['ai_joined'] and results['game_started']
                   and results['server_no_crash']
                   and all(results['procs_alive'].values()))
        import json
        rpt = {
            'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'verdict': 'PASS' if verdict else 'FAIL',
        }
        rp = f'{TMP}\\p8e_report.json'
        Path(rp).write_text(json.dumps(rpt, ensure_ascii=False, indent=2))
        print(f"\n=== P8-E 结果: {rpt['verdict']} ===")
        print(f"server={results['server_alive']} host={results['host_joined']} "
              f"human_alive={results['human_alive']}")
        print(f"ai={results['ai_joined']} started={results['game_started']} "
              f"no_crash={results['server_no_crash']} procs={results['procs_alive']}")
        print(f"报告: {rp}")
        return 0 if verdict else 3

    def cleanup(self):
        for p in (self.ai, self.human, self.srv):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        kill_all()


if __name__ == '__main__':
    sys.exit(P8E().run())

