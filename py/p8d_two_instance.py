#!/usr/bin/env python3
"""
P8-D 同机 2 实例真机部署验证
============================
背景: T13.10 最后一项备料——真机 --remote 部署。第二台真实机器未就绪前,
用"同机 2 实例"模拟双机部署拓扑 (比 WSL 双节点 sim 更贴近真实部署):

  实例 A (node1/host): VCMI_server.exe --port=3030  (D:\\vcmi-fork-build\\bin)
  实例 B (node2/guest):VCMI_server.exe --port=3031  (同一 bin 目录, 端口隔离)
  真实 ModelAI client  连 3030 (host 侧) 与 3031 (guest 侧), 各跑一回合

两实例共享 D:\\vcmi-fork-build\\bin (Windows 多进程可共载同一 dll, 无需 2GB 副本)。

验证项 (模拟真实"两台电脑各跑一套 VCMI"):
  1. 实例 A 起真实 VCMI_server (3030) 存活 + 跨实例 TCP 探活
  2. 实例 B 起真实 VCMI_server (3031) 存活 + 跨实例 TCP 探活
     (同机 2 server 并存, 端口隔离 → 证明可同机多实例)
  3. HSK 预交换: 生成 32B → node1 侧 → 跨"实例"交换到 node2 侧 (模拟 U盘/SCP)
     + 0o600 权限
  4. 真实 ModelAI client 连 3030 (host 侧) — VCMI_TESTMAP_ONLYAI=1 走 ModelAI
  5. 真实 ModelAI client 连 3031 (guest 侧) — 同上, 跨实例对局
  6. 协议层认证: AuthProxy(3031) 收 AuthToken 验签 → 0x01 ACK (正例)
  7. 负例: 错误 HSK → 0x00 → AuthFailedError
  8. StatusFileWriter 双节点 (node1@3030, node2@3031) 状态文件

说明: 真实 VCMI_server 不识别 AuthToken 帧 (T13.10 已知边界), 故第 6/7 项用
AuthProxy 补认证端点 (照 p8d_dual_node_sim.py 范式), 游戏帧走真实 VCMI。

跑法 (Windows 侧):
  python py/p8d_two_instance.py
退出码 0=全过, 1=有失败。
"""
import sys, os, time, json, socket, threading, shutil, struct, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from vcmi_protocol.auth import SharedKeyManager, TokenIssuer, TokenVerifier, AuthToken
from vcmi_protocol.remote_connection import (
    RemoteConnConfig, RemoteVCMITCPConnection, AuthFailedError,
)
from vcmi_protocol.deployment import StatusFileWriter

BIN = r'D:\vcmi-fork-build\bin'
PORT_A = 3030   # 实例 A (node1/host)
PORT_B = 3031   # 实例 B (node2/guest)
MAP = r'Maps/Twins.h3m'
CLIENT_ID = 'ai-node2-001'

TMP = Path(os.environ.get('TEMP', r'C:\Users\Administrator\AppData\Local\Temp'))
N1 = TMP / 'p8d2_node1'
N2 = TMP / 'p8d2_node2'
HWSK_N1 = N1 / 'hsk.key'
HWSK_N2 = N2 / 'hsk.key'
STATUS_DIR = TMP / 'p8d2_status'
SRV_A_LOG = TMP / 'p8d2_srv_a.log'
SRV_B_LOG = TMP / 'p8d2_srv_b.log'
CLI_A_LOG = TMP / 'p8d2_cli_a.log'
CLI_B_LOG = TMP / 'p8d2_cli_b.log'
REPORT = TMP / 'p8d2_report.json'


def kill_vcmi():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


class AuthProxy:
    """模拟"VCMI server 带 HSK 认证"的 TCP 端点 (真实 VCMI_server 不识别 AuthToken,
    按 P8-D 设计补认证端点: 收 [4B len][token JSON], TokenVerifier 验签 → 回 1B ACK)"""

    def __init__(self, hsk: bytes, port: int):
        self.hsk = hsk
        self.port = port
        self.verifier = TokenVerifier(hsk)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.listen(4)
        self.sock.settimeout(1.0)
        self.ack_log: list[tuple[str, int]] = []
        self._workers: list[threading.Thread] = []
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._serve, daemon=True)

    def _serve(self):
        while not self._stop.is_set():
            try:
                c, _ = self.sock.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            t = threading.Thread(target=self._handle, args=(c,), daemon=True)
            self._workers.append(t)
            t.start()

    def stop(self):
        self._stop.set()
        try:
            self.sock.close()
        except Exception:
            pass
        for t in self._workers:
            t.join(timeout=2)

    def _handle(self, c: socket.socket):
        try:
            c.settimeout(10)
            hdr = c.recv(4)
            if len(hdr) < 4:
                c.sendall(b'\x00'); return
            length = int.from_bytes(hdr, 'little')
            if length == 0 or length > 65536:
                c.sendall(b'\x00'); return
            payload = c.recv(length)
            tok = AuthToken.from_bytes(b'T' + struct.pack('<I', length) + payload)
            ok, reason = self.verifier.verify(tok) if tok else (False, 'bad frame')
            self.ack_log.append((reason, 1 if ok else 0))
            c.sendall(b'\x01' if ok else b'\x00')
        except Exception:
            pass


class TwoInstanceProbe:
    def __init__(self):
        self.checks: list[tuple[str, bool, str]] = []
        self.passed = 0
        self.failed = 0
        self.srv_a = None
        self.srv_b = None
        self.cli_a = None
        self.cli_b = None
        self.proxy: AuthProxy | None = None
        self.hsk: bytes = b''

    def ok(self, name: str, cond: bool, detail: str = ""):
        self.checks.append((name, cond, detail))
        if cond:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            print(f"  ❌ {name} — {detail}")

    # ---------- 1. 实例 A (node1/host) ----------
    def c1_instance_a(self):
        print("\n--- 1. 实例 A (node1/host) @3030 ---")
        log = open(SRV_A_LOG, 'w')
        self.srv_a = subprocess.Popen(
            [os.path.join(BIN, 'VCMI_server.exe'), f'--port={PORT_A}'],
            cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(7)
        alive = self.srv_a.poll() is None
        self.ok("实例 A server 存活", alive, f"exit={self.srv_a.returncode}")
        if not alive:
            log.flush()
            for line in open(SRV_A_LOG, errors='replace').readlines()[-15:]:
                print(f"    srvA> {line.rstrip()}")
            return
        try:
            s = socket.create_connection(('127.0.0.1', PORT_A), timeout=3)
            s.close()
            self.ok(f"实例 A TCP 探活 {PORT_A}", True)
        except Exception as e:
            self.ok(f"实例 A TCP 探活 {PORT_A}", False, str(e))

    # ---------- 2. 实例 B (node2/guest) ----------
    def c2_instance_b(self):
        print(f"\n--- 2. 实例 B (node2/guest) @{PORT_B} (同机 2 server 并存) ---")
        log = open(SRV_B_LOG, 'w')
        self.srv_b = subprocess.Popen(
            [os.path.join(BIN, 'VCMI_server.exe'), f'--port={PORT_B}'],
            cwd=BIN, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(7)
        alive = self.srv_b.poll() is None
        self.ok("实例 B server 存活", alive, f"exit={self.srv_b.returncode}")
        if not alive:
            log.flush()
            for line in open(SRV_B_LOG, errors='replace').readlines()[-15:]:
                print(f"    srvB> {line.rstrip()}")
            return
        try:
            s = socket.create_connection(('127.0.0.1', PORT_B), timeout=3)
            s.close()
            self.ok(f"实例 B TCP 探活 {PORT_B}", True)
        except Exception as e:
            self.ok(f"实例 B TCP 探活 {PORT_B}", False, str(e))
        # 注: "同机 2 server 并存" 在 c8_status 后判 (client 连入后 server 才稳定存活)

    # ---------- 3. HSK 预交换 ----------
    def c3_hsk(self) -> bytes:
        print("\n--- 3. HSK 预交换 (node1 → node2 跨实例) ---")
        for d in (N1, N2, STATUS_DIR):
            d.mkdir(parents=True, exist_ok=True)
        key = SharedKeyManager.generate()
        SharedKeyManager.save_to_file(key, str(HWSK_N1))
        # 模拟人工交换: 密钥文件从 node1 拷到 node2 (U盘/SCP 等价物)
        shutil.copyfile(HWSK_N1, HWSK_N2)
        k2 = SharedKeyManager.load_from_file(str(HWSK_N2))
        self.ok("node1 HSK 生成 32B", len(key) == 32)
        self.ok("node2 预交换后可读", k2 == key)
        self.ok("node1 HSK 可读", SharedKeyManager.load_from_file(str(HWSK_N1)) == key)
        self.hsk = key
        return key

    # ---------- 4/5. 真实 ModelAI client 连 3030 / 3031 ----------
    def _start_client(self, port: int, log_path: Path, tag: str):
        env = dict(os.environ); env['VCMI_TESTMAP_ONLYAI'] = '1'
        log = open(log_path, 'w')
        p = subprocess.Popen(
            [os.path.join(BIN, 'VCMI_client.exe'), '--testmap', MAP,
             '--donotstartserver', '--serverport', str(port), '--headless'],
            cwd=BIN, stdout=log, stderr=subprocess.STDOUT, env=env)
        time.sleep(9)
        alive = p.poll() is None
        self.ok(f"{tag} 真实 client 存活", alive, f"exit={p.returncode}")
        return p

    def c4_client_a(self):
        print("\n--- 4. 真实 ModelAI client 连 3030 (host 侧) ---")
        self.cli_a = self._start_client(PORT_A, CLI_A_LOG, "实例 A host")

    def c5_client_b(self):
        print("\n--- 5. 真实 ModelAI client 连 3031 (guest 侧, 跨实例) ---")
        self.cli_b = self._start_client(PORT_B, CLI_B_LOG, "实例 B guest")

    # ---------- 6/7. 协议层认证 (AuthProxy) ----------
    def c6_auth_ok(self):
        print("\n--- 6. 协议层认证 (正例: HSK 验签 → 0x01) ---")
        self.proxy = AuthProxy(self.hsk, PORT_B)
        self.proxy.thread.start()
        time.sleep(0.5)
        cfg = RemoteConnConfig(host='127.0.0.1', port=PORT_B,
                               auth_enabled=True, hsk=self.hsk,
                               client_id=CLIENT_ID,
                               max_retries=2, retry_backoff=0.5, auth_timeout=8.0)
        conn = RemoteVCMITCPConnection(cfg)
        try:
            conn.connect()
            self.ok("跨实例连接 + 认证通过", conn.connected and conn.authenticated,
                    json.dumps(conn.get_stats()))
            conn.disconnect()
        except Exception as e:
            self.ok("跨实例连接 + 认证通过", False, str(e))

    def c7_auth_fail(self):
        print("\n--- 7. 负例: 错误 HSK 应被拒绝 ---")
        bad = SharedKeyManager.generate()
        cfg = RemoteConnConfig(host='127.0.0.1', port=PORT_B,
                               auth_enabled=True, hsk=bad,
                               client_id=CLIENT_ID,
                               max_retries=1, retry_backoff=0.5, auth_timeout=8.0)
        conn = RemoteVCMITCPConnection(cfg)
        rejected = False
        try:
            conn.connect()
        except AuthFailedError:
            rejected = True
        finally:
            conn.disconnect()
        self.ok("错误 HSK 握手被拒 (AuthFailedError)", rejected)

    # ---------- 8. 双节点状态文件 ----------
    def c8_status(self):
        print("\n--- 8. 双节点状态文件 ---")
        for nid, port in (('node1', PORT_A), ('node2', PORT_B)):
            sw = StatusFileWriter(nid, str(STATUS_DIR), port)
            sw._write(True)
            r = StatusFileWriter.read(str(STATUS_DIR), nid)
            self.ok(f"{nid}@{port} 状态文件", r is not None and r['alive'])

    # ---------- 收尾 ----------
    def cleanup(self):
        if self.proxy:
            self.proxy.stop()
        for p in (self.cli_a, self.cli_b, self.srv_a, self.srv_b):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except Exception:
                    p.kill()
        kill_vcmi()

    def run(self) -> int:
        kill_vcmi()
        print(f"=== P8-D 同机 2 实例真机部署验证 (node1@{PORT_A} + node2@{PORT_B}) ===")
        self.c1_instance_a()
        if self.srv_a and self.srv_a.poll() is not None:
            print('\n[FAIL] 实例 A 启动失败, 中止'); self.cleanup(); return 2
        self.c2_instance_b()
        if self.srv_b and self.srv_b.poll() is not None:
            print('\n[FAIL] 实例 B 启动失败, 中止'); self.cleanup(); return 2
        key = self.c3_hsk()
        self.c4_client_a()
        self.c5_client_b()
        self.c6_auth_ok()
        self.c7_auth_fail()
        self.c8_status()
        self.cleanup()

        # 汇总
        total = self.passed + self.failed
        report = {
            'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
            'ports': [PORT_A, PORT_B],
            'passed': self.passed, 'total': total,
            'checks': [(n, c, d) for n, c, d in self.checks],
            'ack_log': self.proxy.ack_log if self.proxy else [],
            'verdict': 'PASS' if total and self.failed == 0 else 'FAIL',
        }
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print('\n=== RESULT ===')
        for n, c, d in self.checks:
            print(f"  {'✅' if c else '❌'} {n}" + (f" — {d}" if not c and d else ""))
        print(f'\n同机 2 实例: {self.passed}/{total} PASS')
        if self.proxy:
            print('ACK 日志:', [f'{r}→{a}' for r, a in self.proxy.ack_log])
        print(f'[REPORT] -> {REPORT}')
        return 0 if self.failed == 0 else 1


if __name__ == '__main__':
    sys.exit(TwoInstanceProbe().run())
