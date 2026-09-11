"""
P8-D 跨机器部署 — 部署管理器
职责:
  1. VCMI 实例管理 (启动/停止/健康检查)
  2. 部署配置 (多节点拓扑)
  3. 远程节点执行 (SSH 或本地)
  4. 健康监控 (心跳 + 状态文件)
  5. 密钥分发 (HSK 生成/分发/轮转)
"""
from __future__ import annotations
import subprocess
import os
import sys
import time
import json
import socket
import threading
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


# ---------------------------------------------------------------------------
# 部署配置
# ---------------------------------------------------------------------------

@dataclass
class NodeConfig:
    """单个部署节点"""
    node_id: str = "node-1"
    host: str = "127.0.0.1"
    port: int = 3030
    vcmi_exe: str = ""  # VCMI_server.exe / VCMI_client.exe 路径
    headless: bool = True
    test_map: str = ""   # .h3m 地图路径 (local 模式)
    vcmi_data_dir: str = ""  # VCMI 数据目录
    is_server: bool = False  # 该节点是否运行 server
    is_client: bool = False  # 该节点是否运行 client
    client_count: int = 0


@dataclass
class DeploymentConfig:
    """多节点部署拓扑"""
    name: str = "p8d-default"
    nodes: List[NodeConfig] = field(default_factory=list)
    hsk_file: str = ""           # 共享密钥文件路径
    status_dir: str = "./vcmi_status"  # 节点状态文件目录
    log_dir: str = "./vcmi_logs"
    timeout: int = 30
    heartbeat_interval: float = 15.0

    @property
    def server_nodes(self) -> List[NodeConfig]:
        return [n for n in self.nodes if n.is_server]

    @property
    def client_nodes(self) -> List[NodeConfig]:
        return [n for n in self.nodes if n.is_client]

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'hsk_file': self.hsk_file,
            'status_dir': self.status_dir,
            'log_dir': self.log_dir,
            'nodes': [
                {
                    'node_id': n.node_id,
                    'host': n.host,
                    'port': n.port,
                    'is_server': n.is_server,
                    'is_client': n.is_client,
                    'headless': n.headless,
                    'test_map': n.test_map,
                    'vcmi_exe': n.vcmi_exe,
                }
                for n in self.nodes
            ],
        }


# ---------------------------------------------------------------------------
# 进程管理 (本地 + SSH 远端)
# ---------------------------------------------------------------------------

class ProcessManager:
    """管理 VCMI 进程"""

    def __init__(self, config: DeploymentConfig):
        self.cfg = config
        self._procs: dict[str, subprocess.Popen] = {}

    def start_node(self, node: NodeConfig) -> dict:
        """启动一个节点 (server + N×client)"""
        results = []
        vc = node.vcmi_exe

        if node.is_server:
            cmd = self._build_server_cmd(node)
            if vc:
                try:
                    proc = subprocess.Popen(cmd, shell=True,
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)
                    self._procs[f"{node.node_id}-server"] = proc
                    results.append({
                        'role': 'server',
                        'pid': proc.pid,
                        'cmd': cmd,
                        'status': 'started',
                    })
                except Exception as e:
                    results.append({'role': 'server', 'status': f'error: {e}'})
            else:
                results.append({'role': 'server', 'status': 'skipped (no vcmi_exe)'})

        if node.is_client and node.client_count > 0:
            for i in range(node.client_count):
                cmd = self._build_client_cmd(node, i)
                if vc:
                    try:
                        proc = subprocess.Popen(cmd, shell=True,
                                                stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL)
                        self._procs[f"{node.node_id}-client{i}"] = proc
                        results.append({
                            'role': f'client{i}',
                            'pid': proc.pid,
                            'cmd': cmd,
                            'status': 'started',
                        })
                    except Exception as e:
                        results.append({'role': f'client{i}', 'status': f'error: {e}'})
                else:
                    results.append({'role': f'client{i}', 'status': 'skipped (no vcmi_exe)'})

        return {'node_id': node.node_id, 'results': results}

    def _build_server_cmd(self, node: NodeConfig) -> str:
        flags = f" --port={node.port}"
        if node.headless:
            flags += " --headless"
        return f"{node.vcmi_exe}{flags}"

    def _build_client_cmd(self, node: NodeConfig, idx: int) -> str:
        flags = " --donotstartserver --serverport " + str(node.port)
        if node.headless:
            flags += " --headless"
        if node.test_map:
            flags += f" --testmap {node.test_map}"
        return f"{node.vcmi_exe}{flags}"

    def stop_node(self, node_id: str) -> dict:
        """停止该节点所有进程"""
        stopped = []
        for key, proc in list(self._procs.items()):
            if key.startswith(node_id):
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    stopped.append(key)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                del self._procs[key]
        return {'node_id': node_id, 'stopped': stopped}

    def stop_all(self):
        for key in list(self._procs.keys()):
            try:
                self._procs[key].terminate()
                self._procs[key].wait(timeout=5)
            except Exception:
                try:
                    self._procs[key].kill()
                except Exception:
                    pass
        self._procs.clear()

    def health_check(self, node: NodeConfig) -> dict:
        """TCP 探活节点端口"""
        try:
            s = socket.create_connection((node.host, node.port), timeout=3)
            s.close()
            return {'node_id': node.node_id, 'port': node.port, 'alive': True}
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            return {'node_id': node.node_id, 'port': node.port, 'alive': False, 'error': str(e)}

    def get_status(self) -> dict:
        return {
            'name': self.cfg.name,
            'processes': {
                k: {'pid': p.pid, 'running': p.poll() is None}
                for k, p in self._procs.items()
            },
        }


# ---------------------------------------------------------------------------
# 状态文件 (节点健康心跳)
# ---------------------------------------------------------------------------

class StatusFileWriter:
    """每 heartbeat_interval 写一次 status JSON 到 status_dir"""

    def __init__(self, node_id: str, status_dir: str, port: int):
        self.node_id = node_id
        self.status_dir = Path(status_dir)
        self.status_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.status_dir / f"{node_id}.json"
        self._stop = threading.Event()
        self._port = port

    def _write(self, alive: bool, error: str = ""):
        data = {
            'node_id': self.node_id,
            'port': self._port,
            'alive': alive,
            'error': error,
            'ts': int(time.time()),
        }
        # 直接写目标文件 (Windows 不支持 atomic rename over existing)
        with open(self._path, 'w') as f:
            json.dump(data, f)

    def start(self, check_fn, interval: float = 15.0):
        """check_fn: callable → (bool, str)"""
        def loop():
            while not self._stop.is_set():
                try:
                    alive, err = check_fn()
                    self._write(alive, err)
                except Exception as e:
                    self._write(False, str(e))
                self._stop.wait(interval)

        t = threading.Thread(target=loop, daemon=True, name=f"status-{self.node_id}")
        t.start()
        return t

    def stop(self):
        self._stop.set()

    @classmethod
    def read(cls, status_dir: str, node_id: str) -> Optional[dict]:
        p = Path(status_dir) / f"{node_id}.json"
        if not p.exists():
            return None
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            return None


# ---------------------------------------------------------------------------
# 密钥分发
# ---------------------------------------------------------------------------

class KeyDistributor:
    """HSK 生成/分发/轮转"""

    def __init__(self, hsk_file: str = ""):
        self.hsk_file = hsk_file or "./vcmi_hsk.key"

    def generate_and_save(self) -> bytes:
        from .auth import SharedKeyManager
        key = SharedKeyManager.generate()
        SharedKeyManager.save_to_file(key, self.hsk_file)
        return key

    def load(self) -> Optional[bytes]:
        from .auth import SharedKeyManager
        p = Path(self.hsk_file)
        if not p.exists():
            return None
        return SharedKeyManager.load_from_file(self.hsk_file)

    def rotate(self) -> bytes:
        """轮转密钥 (生成新 key, 旧 key 立即作废)"""
        new_key = self.generate_and_save()
        # 生产环境: 通知所有已连接客户端切换
        return new_key


# ---------------------------------------------------------------------------
# 部署编排器
# ---------------------------------------------------------------------------

class DeploymentManager:
    """
    P8-D 部署编排:
      deploy_all()  → 生成密钥 → 启动 server 节点 → 启动 client 节点 → 健康检查
      status()      → 全节点健康快照
      teardown()    → 停止所有节点
    """

    def __init__(self, config: DeploymentConfig):
        self.cfg = config
        self.pm = ProcessManager(config)
        Path(config.status_dir).mkdir(parents=True, exist_ok=True)
        Path(config.log_dir).mkdir(parents=True, exist_ok=True)

    def deploy_all(self) -> dict:
        results = {}
        for node in self.cfg.nodes:
            results[node.node_id] = self.pm.start_node(node)
        # 等待 server 端口就绪
        time.sleep(1.0)
        for node in self.cfg.server_nodes:
            results[f"{node.node_id}-health"] = self.pm.health_check(node)
        return results

    def status(self) -> dict:
        out = self.pm.get_status()
        out['nodes'] = {}
        for node in self.cfg.nodes:
            out['nodes'][node.node_id] = {
                'health': self.pm.health_check(node),
                'status_file': StatusFileWriter.read(self.cfg.status_dir, node.node_id),
            }
        return out

    def teardown(self):
        self.pm.stop_all()


# ---------------------------------------------------------------------------
# 离线验证入口
# ---------------------------------------------------------------------------

def _offline_verify():
    """
    离线验证 — 无需 VCMI 实机:
      1. 密钥生成/签发/验证 闭环
      2. 部署配置序列化
      3. 状态文件读写
      4. 进程管理命令构造
      5. 节点拓扑查询
    """
    import tempfile
    from .auth import SharedKeyManager, TokenIssuer, TokenVerifier, AuthToken

    passed = 0
    total = 0

    def ok(name, cond, detail=""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} — {detail}")

    # --- 1. 密钥闭环 ---
    print("\n--- 1. 密钥生成/签发/验证 ---")
    with tempfile.TemporaryDirectory() as tmpd:
        key = SharedKeyManager.generate()
        ok("HSK 生成 32B", len(key) == 32, f"got {len(key)}")
        ok("HSK 校验", SharedKeyManager.validate(key))

        issuer = TokenIssuer(key, "client-001")
        verifier = TokenVerifier(key)
        tok = issuer.issue()
        ok("Token 签发", tok.client_id == "client-001")
        ok("Token 有 nonce", len(tok.nonce) == 16)

        good, reason = verifier.verify(tok)
        ok(f"Token 验证 (fresh): {good}", good, reason)

        # 重放
        good2, reason2 = verifier.verify(tok)
        ok(f"Token 重放拒绝: {not good2}", not good2, reason2)

        # 过期
        old_tok = AuthToken(client_id="client-001",
                            timestamp=int(time.time()) - 9999,
                            nonce="oldnonce",
                            signature="fake")
        good3, reason3 = verifier.verify(old_tok)
        ok(f"Token 过期拒绝: {not good3}", not good3, reason3)

        # 篡改
        tampered = AuthToken(client_id="client-001",
                             timestamp=int(time.time()),
                             nonce=tok.nonce,
                             signature=tok.signature + "X")
        good4, _ = verifier.verify(tampered)
        ok(f"Token 篡改拒绝: {not good4}", not good4)

    # --- 2. 部署配置 ---
    print("\n--- 2. 部署配置序列化 ---")
    cfg = DeploymentConfig(
        name="test-topology",
        nodes=[
            NodeConfig(node_id="srv-1", host="10.0.0.1", port=3030,
                       is_server=True, vcmi_exe="/opt/vcmi/VCMI_server.exe"),
            NodeConfig(node_id="cli-1", host="10.0.0.2", port=3030,
                       is_client=True, client_count=2, vcmi_exe="/opt/vcmi/VCMI_client.exe"),
        ],
    )
    d = cfg.to_dict()
    ok("节点数", len(d["nodes"]) == 2)
    ok("server 数", len(cfg.server_nodes) == 1)
    ok("client 数", len(cfg.client_nodes) == 1)
    ok("client_count", cfg.client_nodes[0].client_count == 2)

    # --- 3. 状态文件 ---
    print("\n--- 3. 状态文件读写 ---")
    with tempfile.TemporaryDirectory() as tmpd:
        sw = StatusFileWriter("test-node", tmpd, 3030)
        sw._write(True)
        r = StatusFileWriter.read(tmpd, "test-node")
        ok("状态文件写入", r is not None and r["alive"] == True)

        sw._write(False, "port busy")
        r2 = StatusFileWriter.read(tmpd, "test-node")
        ok("状态文件更新", r2["alive"] == False and r2["error"] == "port busy")

    # --- 4. 进程管理命令构造 ---
    print("\n--- 4. 进程管理命令构造 ---")
    pm = ProcessManager(cfg)
    srv_cmd = pm._build_server_cmd(cfg.server_nodes[0])
    ok("server 命令含 port", "--port=3030" in srv_cmd, srv_cmd)
    ok("server 命令 headless", "--headless" in srv_cmd, srv_cmd)

    cli_cmd = pm._build_client_cmd(cfg.client_nodes[0], 0)
    ok("client 命令含 donotstartserver", "--donotstartserver" in cli_cmd, cli_cmd)
    ok("client 命令含 serverport", "3030" in cli_cmd, cli_cmd)

    # --- 5. 密钥分发 ---
    print("\n--- 5. 密钥分发 ---")
    with tempfile.TemporaryDirectory() as tmpd:
        kd = KeyDistributor(os.path.join(tmpd, "hsk.key"))
        key = kd.generate_and_save()
        loaded = kd.load()
        ok("密钥落盘+读取", loaded == key)
        new_key = kd.rotate()
        ok("密钥轮转", new_key != key)

    print(f"\n{'=' * 50}")
    print(f"P8-D 离线验证: {passed} passed, {total - passed} failed / {total} total")
    print(f"{'=' * 50}")
    return total - passed


if __name__ == "__main__":
    # 直接运行 `python deployment.py` 时, 相对导入失效, 需手动注入包路径
    import os
    _pkg_dir = os.path.dirname(os.path.abspath(__file__))
    if _pkg_dir not in sys.path:
        sys.path.insert(0, _pkg_dir)
    if "vcmi_protocol" not in sys.modules:
        import types
        _pkg = types.ModuleType("vcmi_protocol")
        _pkg.__path__ = [_pkg_dir]
        sys.modules["vcmi_protocol"] = _pkg
    # 重新以包内模块身份导入自身
    import importlib
    _self = importlib.import_module("vcmi_protocol.deployment")
    sys.exit(0 if _self._offline_verify() == 0 else 1)
