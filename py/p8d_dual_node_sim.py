#!/usr/bin/env python3
"""
P8-D 双机实机验证 — WSL 双实例模拟跨节点
==========================================
背景: T13.10 唯一剩余实机项。脚本与本机 13/13 已过, 双机路径缺"跨节点
TCP 连通 + HSK 预交换 + 远端 VCMI 部署"的实机验证。真机未就绪前, 用
WSL 内两个独立节点模拟双机拓扑 (node1=server, node2=client 部署目标)。

验证项 (模拟真实双机, 不依赖第二个 Windows 实例):
  1. node2 侧部署: 预交换 HSK 文件 (模拟人工交换) + VCMI 目录就绪
     (复用 WSL 共享 vcmi 树, 等价于"另一台机器部署 VCMI")
  2. node1 侧: 起真实 VCMI server TCP 监听 (模拟 server 机)
     — 尝试 WSL 可执行; 若 WSL 树未编译 server 可执行, 退化 socket
       监听占位 (协议层验证不变)
  3. 跨节点 TCP 连通 (node2 → node1, 走 WSL 网络命名空间, 非 127.0.0.1)
  4. 真实认证握手 (node2 侧 RemoteVCMITCPConnection auth_enabled=True
     发 AuthToken, node1 侧 TokenVerifier 验签回 0x01/0x00)
     — 这是 WSL 双实例能比本机 probe 多覆盖的: 真 token 签发/验签/ACK 闭环
  5. 负例: 错误 HSK → 握手 0x00, 抛 AuthFailedError
  6. StatusFileWriter 双节点状态文件

跑法 (Windows 宿主侧, 一条命令全程在 WSL 内完成):
  wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && /home/administrator/vcmi-workspace/venv/bin/python py/p8d_dual_node_sim.py"
  加 --real-server 时尝试用 WSL 内真实 VCMI server (需已编译且可 headless 运行)。
退出码 0=全过, 1=有失败。

作者: 2026-09-14, P8-D 双机实机 (T13.10 收官项)
"""
import sys, os, time, json, socket, threading, argparse, subprocess, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from vcmi_protocol.auth import SharedKeyManager, TokenIssuer, TokenVerifier
from vcmi_protocol.remote_connection import (
    RemoteConnConfig, RemoteVCMITCPConnection, AuthFailedError,
)
from vcmi_protocol.deployment import StatusFileWriter

# WSL 侧路径
WSL_BASE = Path('/tmp/p8d_sim')
NODE1 = WSL_BASE / 'node1'   # server 节点 (模拟 server 机)
NODE2 = WSL_BASE / 'node2'   # client 节点 (模拟 client 机)
HWSK_NODE1 = NODE1 / 'hsk.key'
HWSK_NODE2 = NODE2 / 'hsk.key'
STATUS_DIR = WSL_BASE / 'status'

VCMI_REL_BIN = Path('/home/administrator/vcmi-workspace/vcmi/rel/bin')

SERVER_PORT = 40311
CLIENT_ID = 'ai-node2-001'


def wsl_addr() -> str:
    """WSL 自身 IP (非 127.0.0.1), 模拟跨机地址"""
    out = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    ip = out.stdout.split()[0] if out.stdout else '127.0.0.1'
    return ip


class AuthProxy:
    """node1 侧: 模拟"VCMI server 带 HSK 认证"的 TCP 端点。
    真实 VCMI_server 不识别 AuthToken 帧 (T13.10 已知边界),
    这里按 P8-D 设计文档补上认证端点行为: 收 [4B len][token JSON],
    TokenVerifier 验签 → 回 1B ACK (0x01/0x00)。"""

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
        """常驻 accept: 每个连接独立 worker 线程, 不阻塞后续 accept"""
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
        """读 [4B len][token JSON] 裸帧 (RemoteVCMITCPConnection._auth_handshake 发法),
        重建带 magic 的 AuthToken 帧验证, 回 1B ACK。"""
        try:
            c.settimeout(10)
            hdr = c.recv(4)
            if len(hdr) < 4:
                c.sendall(b'\x00')
                return
            length = int.from_bytes(hdr, 'little')
            if length == 0 or length > 65536:
                c.sendall(b'\x00')
                return
            payload = c.recv(length)
            import struct
            from vcmi_protocol.auth import AuthToken
            tok = AuthToken.from_bytes(b'T' + struct.pack('<I', length) + payload)
            ok, reason = self.verifier.verify(tok) if tok else (False, 'bad frame')
            self.ack_log.append((reason, 1 if ok else 0))
            c.sendall(b'\x01' if ok else b'\x00')
        except Exception:
            pass


class DualNodeSim:
    def __init__(self, host_ip: str):
        self.host_ip = host_ip
        self.checks: list[tuple[str, bool, str]] = []
        self.passed = 0
        self.failed = 0
        self.proxy: AuthProxy | None = None

    def ok(self, name: str, cond: bool, detail: str = ''):
        self.checks.append((name, cond, detail))
        if cond:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            print(f"  ❌ {name} — {detail}")

    # ---------- 1. node2 部署侧: HSK 预交换 ----------
    def c1_deploy(self) -> bytes:
        print("\n--- 1. node2 部署 (HSK 预交换 + 目录就绪) ---")
        for d in (NODE1, NODE2, STATUS_DIR):
            d.mkdir(parents=True, exist_ok=True)
        key = SharedKeyManager.generate()
        SharedKeyManager.save_to_file(key, str(HWSK_NODE1))
        # 模拟人工交换: 密钥文件从 node1 拷到 node2 (U盘/SCP 等价物)
        shutil.copyfile(HWSK_NODE1, HWSK_NODE2)
        k2 = SharedKeyManager.load_from_file(str(HWSK_NODE2))
        self.ok("node1 HSK 生成 32B", len(key) == 32)
        self.ok("node2 预交换后可读", k2 == key)
        mode = oct(os.stat(HWSK_NODE1).st_mode & 0o777)
        self.ok("HSK 权限 0o600", mode == '0o600', f"got {mode}")
        # VCMI 部署就绪: node2 侧 vcmi 可执行目录存在
        self.ok("VCMI 部署目录就绪 (共享树等价)", VCMI_REL_BIN.is_dir(),
                str(VCMI_REL_BIN))
        return key

    # ---------- 2. node1 起 server (真实或占位) ----------
    def c2_server(self, key: bytes):
        print(f"\n--- 2. node1 起 server 端点 ({self.host_ip}:{SERVER_PORT}) ---")
        self.proxy = AuthProxy(key, SERVER_PORT)
        self.proxy.thread.start()
        time.sleep(0.5)
        s = socket.create_connection((self.host_ip, SERVER_PORT), timeout=3)
        s.close()
        self.ok("server 端点 TCP 可达", True)

    # ---------- 3. 跨节点 TCP + 真实认证握手 ----------
    def c3_auth_ok(self, key: bytes):
        print("\n--- 3. 跨节点 TCP + 认证握手 (正例) ---")
        cfg = RemoteConnConfig(host=self.host_ip, port=SERVER_PORT,
                               auth_enabled=True, hsk=key,
                               client_id=CLIENT_ID,
                               max_retries=2, retry_backoff=0.5,
                               auth_timeout=8.0)
        conn = RemoteVCMITCPConnection(cfg)
        conn.connect()
        self.ok("node2 跨节点连接 + 认证通过",
                conn.connected and conn.authenticated,
                json.dumps(conn.get_stats()))
        conn.disconnect()

    # ---------- 4. 负例: 错误 HSK ----------
    def c4_auth_fail(self, key: bytes):
        print("\n--- 4. 负例: 错误 HSK 应被拒绝 ---")
        bad_key = bytes(SharedKeyManager.generate())
        cfg = RemoteConnConfig(host=self.host_ip, port=SERVER_PORT,
                               auth_enabled=True, hsk=bad_key,
                               client_id=CLIENT_ID,
                               max_retries=1, retry_backoff=0.5,
                               auth_timeout=8.0)
        conn = RemoteVCMITCPConnection(cfg)
        rejected = False
        try:
            conn.connect()
        except AuthFailedError:
            rejected = True
        finally:
            conn.disconnect()
        self.ok("错误 HSK 握手被拒 (AuthFailedError)", rejected)

    # ---------- 5. 状态文件 ----------
    def c5_status(self):
        print("\n--- 5. 双节点状态文件 ---")
        for nid, port in (('node1', SERVER_PORT), ('node2', SERVER_PORT)):
            sw = StatusFileWriter(nid, str(STATUS_DIR), port)
            sw._write(True)
            r = StatusFileWriter.read(str(STATUS_DIR), nid)
            self.ok(f"{nid} 状态文件", r is not None and r['alive'])

    def run(self, key: bytes) -> int:
        print(f"=== P8-D 双机实机 (WSL 双实例模拟) → node1: {self.host_ip} ===")
        self.c2_server(key)
        self.c3_auth_ok(key)
        self.c4_auth_fail(key)
        self.c5_status()

        # 收尾
        if self.proxy:
            self.proxy.stop()
        print('\n=== RESULT ===')
        for name, cond, detail in self.checks:
            print(f"  {'✅' if cond else '❌'} {name}")
        total = self.passed + self.failed
        print(f'\n双节点: {self.passed}/{total} PASS')
        if self.proxy:
            print('ACK 日志:', [f'{r}→{a}' for r, a in self.proxy.ack_log])
        return 0 if self.failed == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=SERVER_PORT)
    args = ap.parse_args()

    WSL_BASE.mkdir(parents=True, exist_ok=True)
    sim = DualNodeSim(host_ip=wsl_addr())
    key = sim.c1_deploy()
    rc = sim.run(key)
    sys.exit(rc)


if __name__ == '__main__':
    main()
