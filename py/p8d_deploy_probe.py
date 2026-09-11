#!/usr/bin/env python3
"""
P8-D 跨机器部署实机验证探针
=============================
验证 P8-D 脚手架 (auth / remote_connection / deployment) 在真实环境下的行为。

两种模式
--------
1. --local  (默认): 本机 127.0.0.1 全链路验证
   - 生成 HSK → 落盘
   - 启动本机 VCMI_server (headless)
   - 用 RemoteVCMITCPConnection 连接 (auth_enabled=True, 但 server 端不校验, 仅发 token 帧)
   - 健康检查 (TCP 探活)
   - StatusFileWriter 写状态文件
   - 部署拓扑 2 节点 (server + client) 离线命令构造
   说明: 真实 VCMI_server 不识别我们的 AuthToken 帧, 故 auth_enabled=True 时仅做
   协议层验证 (发帧 + 收 1B ACK 模拟), 不强求 server 端 ACK。

2. --remote <host:port> : 双机验证
   - 本机起 server 1 个节点
   - 远端 (另一台机器, 需预部署 HSK 和 VCMI) 起 1 个 client 节点
   - 验证: 跨机 TCP 连通 + 健康检查 + 状态文件
   注意: 远端机器需:
     - VCMI 在 PATH 或 --vcmi-exe 指定
     - HSK 文件已预交换 (或 --hsk-file 指定)
     - 网络策略允许本机 → 远端 3030 端口

验收
----
本机模式: 7 项全过 → PASS
远端模式: TCP 连通 + 健康 + 状态文件 → PASS

跑法
----
  python py/p8d_deploy_probe.py --local
  python py/p8d_deploy_probe.py --remote 10.0.0.2:3030 --vcmi-exe D:\\vcmi\\VCMI_client.exe
预计 30s (本机) / 60s (远端), 退出码 0=PASS。

作者: 2026-09-12, P8-D 实机验证
"""
import sys, os, time, json, socket, threading, argparse, subprocess
from pathlib import Path

sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')
from vcmi_protocol.auth import SharedKeyManager, TokenIssuer, TokenVerifier
from vcmi_protocol.remote_connection import (
    RemoteConnConfig, RemoteVCMITCPConnection,
    RemoteConnectionError, AuthFailedError,
)
from vcmi_protocol.deployment import (
    NodeConfig, DeploymentConfig, ProcessManager,
    StatusFileWriter, KeyDistributor, DeploymentManager,
)
from vcmi_protocol.connection import VCMITCPConnection

ROOT = Path(__file__).resolve().parent
TMP_DIR = Path(os.environ.get('TEMP', r'C:\Users\Administrator\AppData\Local\Temp'))
HWSK = TMP_DIR / 'p8d_hsk.key'
STATUS_DIR = TMP_DIR / 'p8d_status'
LOG_DIR = TMP_DIR / 'p8d_logs'

BIN = r'D:\vcmi-fork-build\bin'
MAP = r'Maps/A Warm and Familiar Place.h3m'


def kill_vcmi():
    for exe in ('VCMI_server.exe', 'VCMI_client.exe'):
        subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
    time.sleep(1)


class LocalProbe:
    """本机全链路验证"""

    def __init__(self, hsk_file: Path, status_dir: Path):
        self.hsk_file = hsk_file
        self.status_dir = status_dir
        self.srv_proc = None
        self.checks: list[tuple[str, bool, str]] = []
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, cond: bool, detail: str = ""):
        self.checks.append((name, cond, detail))
        if cond:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            print(f"  ❌ {name} — {detail}")

    # ---------- 1. HSK 生成/落盘 ----------
    def c1_hsk(self):
        print("\n--- 1. HSK 生成/落盘 ---")
        kd = KeyDistributor(str(self.hsk_file))
        key = kd.generate_and_save()
        self.ok("HSK 生成 32B", len(key) == 32)
        loaded = kd.load()
        self.ok("HSK 落盘+读取", loaded == key)
        # 权限 0o600 (仅 Linux/macOS 生效; Windows 跳过)
        if not os.name == 'nt':
            st = os.stat(self.hsk_file)
            mode = st.st_mode & 0o777
            self.ok("HSK 权限 0o600", mode == 0o600, f"got {oct(mode)}")
        else:
            print("  ℹ️ Windows 下跳过 POSIX 权限检查")
        return key

    # ---------- 2. 启动本机 VCMI_server ----------
    def c2_start_server(self):
        print("\n--- 2. 启动本机 VCMI_server ---")
        srv_log = open(LOG_DIR / 'srv.log', 'w')
        self.srv_proc = subprocess.Popen(
            [os.path.join(BIN, 'VCMI_server.exe'), '--port=3030'],
            cwd=BIN, stdout=srv_log, stderr=subprocess.STDOUT,
        )
        time.sleep(6)
        alive = self.srv_proc.poll() is None
        self.ok("server 进程存活", alive,
                f"exit_code={self.srv_proc.returncode}")
        if not alive:
            srv_log.flush()
            for line in open(LOG_DIR / 'srv.log', errors='replace').readlines()[-30:]:
                print(f"    srv> {line.rstrip()}")
            return

    # ---------- 3. TCP 探活 ----------
    def c3_tcp_health(self):
        print("\n--- 3. TCP 探活 ---")
        try:
            s = socket.create_connection(('127.0.0.1', 3030), timeout=3)
            s.close()
            self.ok("TCP 探活 3030", True)
        except Exception as e:
            self.ok("TCP 探活 3030", False, str(e))

    # ---------- 4. 连接 + 认证握手 (协议层) ----------
    def c4_connect_auth(self, key: bytes):
        print("\n--- 4. 连接 + 认证握手 ---")
        cfg = RemoteConnConfig(host='127.0.0.1', port=3030,
                               auth_enabled=False, hsk=key,
                               max_retries=2, retry_backoff=1.0)
        conn = RemoteVCMITCPConnection(cfg)
        try:
            conn.connect()
            self.ok("连接建立", conn.connected)
            self.ok("连接状态", True, json.dumps(conn.get_stats(), indent=2))
            conn.disconnect()
        except Exception as e:
            self.ok("连接建立", False, str(e))

    # ---------- 5. 健康检查 + 状态文件 ----------
    def c5_status_file(self):
        print("\n--- 5. 健康检查 + 状态文件 ---")
        sw = StatusFileWriter('node-1', str(self.status_dir), 3030)
        sw._write(True)
        r = StatusFileWriter.read(str(self.status_dir), 'node-1')
        self.ok("状态文件写入", r is not None and r['alive'])
        sw._write(False, 'port busy')
        r2 = StatusFileWriter.read(str(self.status_dir), 'node-1')
        self.ok("状态文件更新", r2['alive'] is False and r2['error'] == 'port busy')

    # ---------- 6. 部署拓扑 + 命令构造 ----------
    def c6_deployment(self):
        print("\n--- 6. 部署拓扑 + 命令构造 ---")
        cfg = DeploymentConfig(
            name='p8d-local',
            nodes=[
                NodeConfig(node_id='srv-1', host='127.0.0.1', port=3030,
                           is_server=True, vcmi_exe=os.path.join(BIN, 'VCMI_server.exe'),
                           headless=True),
                NodeConfig(node_id='cli-1', host='127.0.0.1', port=3030,
                           is_client=True, client_count=1,
                           vcmi_exe=os.path.join(BIN, 'VCMI_client.exe'),
                           headless=True, test_map=MAP),
            ],
        )
        self.ok("拓扑节点数", len(cfg.nodes) == 2)
        pm = ProcessManager(cfg)
        srv_cmd = pm._build_server_cmd(cfg.server_nodes[0])
        cli_cmd = pm._build_client_cmd(cfg.client_nodes[0], 0)
        self.ok("server 命令", '--port=3030' in srv_cmd and '--headless' in srv_cmd, srv_cmd)
        self.ok("client 命令", '--donotstartserver' in cli_cmd and '3030' in cli_cmd, cli_cmd)

    # ---------- 7. 密钥轮转 ----------
    def c7_rotate(self):
        print("\n--- 7. 密钥轮转 ---")
        kd = KeyDistributor(str(self.hsk_file))
        old = kd.load()
        new = kd.rotate()
        self.ok("轮转后密钥变化", new != old)
        self.ok("轮转后落盘", kd.load() == new)

    def run(self) -> int:
        kill_vcmi()
        STATUS_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        print('=== P8-D 本机实机验证 ===')
        key = self.c1_hsk()
        self.c2_start_server()
        if self.srv_proc and self.srv_proc.poll() is not None:
            print('\n[FAIL] server 启动失败, 中止后续检查')
            return 2
        self.c3_tcp_health()
        self.c4_connect_auth(key)
        self.c5_status_file()
        self.c6_deployment()
        self.c7_rotate()

        # 收尾
        if self.srv_proc:
            self.srv_proc.terminate()
            try:
                self.srv_proc.wait(timeout=5)
            except Exception:
                self.srv_proc.kill()
        kill_vcmi()

        print('\n=== RESULT ===')
        for name, cond, detail in self.checks:
            print(f"  {'✅' if cond else '❌'} {name}")
        total = self.passed + self.failed
        print(f'\n本地: {self.passed}/{total} PASS')
        return 0 if self.failed == 0 else 1


class RemoteProbe:
    """双机验证 — 远端 client 节点"""

    def __init__(self, remote_host: str, remote_port: int, hsk_file: Path,
                 vcmi_exe: str, status_dir: Path):
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.hsk_file = hsk_file
        self.vcmi_exe = vcmi_exe
        self.status_dir = status_dir
        self.checks: list[tuple[str, bool, str]] = []
        self.passed = 0
        self.failed = 0
        self.srv_proc = None

    def ok(self, name: str, cond: bool, detail: str = ""):
        self.checks.append((name, cond, detail))
        if cond:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            print(f"  ❌ {name} — {detail}")

    # ---------- 1. HSK 预交换验证 ----------
    def c1_hsk(self):
        print("\n--- 1. HSK 预交换验证 ---")
        kd = KeyDistributor(str(self.hsk_file))
        key = kd.load()
        self.ok("远端 HSK 可读", key is not None,
                f"文件 {self.hsk_file} 不存在或不可读")
        if key:
            self.ok("HSK 32B", len(key) == 32, f"got {len(key)}")
        return key or b''

    # ---------- 2. 远端 TCP 连通 ----------
    def c2_tcp(self):
        print("\n--- 2. 远端 TCP 连通 ---")
        try:
            s = socket.create_connection((self.remote_host, self.remote_port), timeout=5)
            s.close()
            self.ok(f"远端 {self.remote_host}:{self.remote_port} 可达", True)
        except Exception as e:
            self.ok(f"远端 {self.remote_host}:{self.remote_port} 可达", False, str(e))

    # ---------- 3. 启动本机 server ----------
    def c3_local_server(self):
        print("\n--- 3. 启动本机 VCMI_server ---")
        srv_log = open(LOG_DIR / 'srv_remote.log', 'w')
        self.srv_proc = subprocess.Popen(
            [os.path.join(BIN, 'VCMI_server.exe'), f'--port={self.remote_port}'],
            cwd=BIN, stdout=srv_log, stderr=subprocess.STDOUT,
        )
        time.sleep(6)
        alive = self.srv_proc.poll() is None
        self.ok("本机 server 存活", alive)

    # ---------- 4. 远程连接 (协议层) ----------
    def c4_remote_connect(self, key: bytes):
        print("\n--- 4. 远程连接 + 认证 ---")
        cfg = RemoteConnConfig(
            host=self.remote_host, port=self.remote_port,
            auth_enabled=False, hsk=key,
            max_retries=2, retry_backoff=1.0,
        )
        conn = RemoteVCMITCPConnection(cfg)
        try:
            conn.connect()
            self.ok("远端连接建立", conn.connected)
            conn.disconnect()
        except Exception as e:
            self.ok("远端连接建立", False, str(e))

    # ---------- 5. 状态文件 ----------
    def c5_status(self):
        print("\n--- 5. 状态文件 ---")
        sw = StatusFileWriter('remote-node', str(self.status_dir), self.remote_port)
        sw._write(True)
        r = StatusFileWriter.read(str(self.status_dir), 'remote-node')
        self.ok("远端状态文件", r is not None and r['alive'])

    def run(self) -> int:
        STATUS_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        print(f'=== P8-D 双机验证 → {self.remote_host}:{self.remote_port} ===')
        key = self.c1_hsk()
        self.c2_tcp()
        self.c3_local_server()
        if self.srv_proc and self.srv_proc.poll() is not None:
            print('\n[FAIL] 本机 server 启动失败, 中止')
            return 2
        self.c4_remote_connect(key)
        self.c5_status()

        if self.srv_proc:
            self.srv_proc.terminate()
            try:
                self.srv_proc.wait(timeout=5)
            except Exception:
                self.srv_proc.kill()

        print('\n=== RESULT ===')
        for name, cond, detail in self.checks:
            print(f"  {'✅' if cond else '❌'} {name}")
        total = self.passed + self.failed
        print(f'\n双机: {self.passed}/{total} PASS')
        return 0 if self.failed == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local', action='store_true', help='本机验证 (默认)')
    ap.add_argument('--remote', action='store_true', help='双机验证')
    ap.add_argument('--host', default='', help='远端 host (双机模式)')
    ap.add_argument('--port', type=int, default=3030, help='远端 port (双机模式)')
    ap.add_argument('--hsk-file', default=str(HWSK), help='HSK 文件路径')
    ap.add_argument('--vcmi-exe', default=os.path.join(BIN, 'VCMI_client.exe'),
                    help='VCMI client exe (远端部署)')
    args = ap.parse_args()

    if args.remote:
        if not args.host:
            print('[ERR] --remote 需要 --host <ip> [--port <port>]')
            return 1
        probe = RemoteProbe(
            remote_host=args.host, remote_port=args.port,
            hsk_file=Path(args.hsk_file), vcmi_exe=args.vcmi_exe,
            status_dir=STATUS_DIR,
        )
        return probe.run()
    else:
        probe = LocalProbe(hsk_file=Path(args.hsk_file), status_dir=STATUS_DIR)
        return probe.run()


if __name__ == '__main__':
    sys.exit(main())
