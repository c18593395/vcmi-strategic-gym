"""
P8-D 跨机器部署 — 脚手架设计 + 骨架
========================================
职责:
  1. 网络拓扑设计 (文档级)
  2. 认证方案落地 (auth.py + remote_connection.py)
  3. 部署编排 (deployment.py)
  4. 离线自测 (无需 VCMI 实机即可跑)
  5. 实机验证入口 (需要真实 VCMI 时才跑)

运行:
  python py/p8/p8d_scaffold_design.py --offline     # 离线验证 (默认)
  python py/p8/p8d_scaffold_design.py --deploy      # 实机部署 (需 VCMI)
"""
from __future__ import annotations
import sys
import os
import time
import argparse
import json
from pathlib import Path

# 添加包路径 (py/p8 -> 上一级 py/, vcmi_protocol 包所在)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vcmi_protocol.auth import (
    SharedKeyManager, TokenIssuer, TokenVerifier, AuthToken,
)
from vcmi_protocol.remote_connection import (
    RemoteVCMITCPConnection, RemoteConnConfig, RemoteConnectionError,
    AuthFailedError,
)
from vcmi_protocol.deployment import (
    DeploymentConfig, NodeConfig, DeploymentManager,
    KeyDistributor, StatusFileWriter, ProcessManager,
)


# ---------------------------------------------------------------------------
# 网络拓扑设计 (文档级, 输出到 stdout)
# ---------------------------------------------------------------------------

TOPOLOGY_DOC = """
================================================================
P8-D 跨机器部署 — 网络拓扑设计
================================================================

拓扑模式 A: 本地开发 (单机, 训练 + 实机验证并行)
----------------------------------------------------------------
  [训练 v5 systemd]  12核  ────  (不碰 T13)
  [P8-D 本地探针]    1核   ────  ┐
                                  │
        localhost:3030           │
        VCMI_server.exe ◄────────┘  本地回环
        VCMI_client.exe (human)    2× 本地
        ai_client.py    (AI 座位)   2× 本地

  特点: 单进程 server, 多客户端本地回环, 与训练并行无冲突

拓扑模式 B: 双机 (跨机器, P8-D 核心验证目标)
----------------------------------------------------------------
  Machine A (server)                     Machine B (AI)
  ┌──────────────────────┐               ┌──────────────────┐
  │ VCMI_server.exe       │   TCP 3030    │ ai_client.py     │
  │   (10.0.0.1:3030)    │◄─────────────►│   (10.0.0.2)     │
  │                        │  HSK 认证     │  ModelBridge     │
  │ VCMI_client.exe ×1    │               │  (obs 3464)     │
  │   (human 座位)        │               │  N_ACTIONS=25    │
  └──────────────────────┘               └──────────────────┘
  特点: 真实网络, HSK 预交换, 延迟 ~1-5ms (局域网)

拓扑模式 C: 三机 (生产扩展)
----------------------------------------------------------------
  [Server 节点]      [Human 节点]      [AI 节点]
  10.0.0.1:3030   10.0.0.2        10.0.0.3
       │                 │                 │
       └─────────────────┴─────────────────┘
                          TCP (HSK 认证)

  特点: 各节点独立, AI 节点跑 ModelBridge (obs 3464 + PPO 模型)

认证方案:
----------------------------------------------------------------
  密钥交换: 部署前一次性预交换 HSK (32B, 文件 / keymanager)
  连接认证: 每次 TCP 连接后先发 1 帧 AuthToken (JSON)
            [4B len][{client_id, ts, nonce, sig}]
  签名算法: HMAC-SHA256(HSK, client_id | timestamp | nonce)
  时间窗:   ±300s
  重放防护: nonce 去重 (server 端内存 / 生产 Redis)
  ACK:      server 回 1 字节 0x01=OK / 0x00=FAIL
  传输层:   内网 plaintext; 公网可选 TLS (预留接口, 不实现)

部署脚本 (Windows 侧):
----------------------------------------------------------------
  deploy.ps1:
    1. 生成/加载 HSK → C:\\vcmi\\hsk.key
    2. 启动 VCMI_server.exe --port=3030
    3. 启动 VCMI_client.exe --donotstartserver --serverport 3030 --headless
    4. 启动 ai_client.py --host 10.0.0.1 --port 3030
    5. 写状态文件 vcmi_status/{node}.json
    6. 定时健康检查 (每 15s)
    7. Ctrl+C / 信号 → 优雅停止 (先 client 后 server)

Python 侧 (AI 节点):
    ai_client.py:
      1. 加载 HSK (路径或环境变量 VCMI_HSK)
      2. RemoteVCMITCPConnection.connect() → TCP + 认证
      3. 进入 ModelBridge 决策循环
      4. 断连 → 指数退避重试 (backoff 2.0, 3 次)

  ========================================================================
"""


# ---------------------------------------------------------------------------
# 离线自测
# ---------------------------------------------------------------------------

def run_offline() -> int:
    """离线验证全部组件 (无需 VCMI 实机)"""
    print(TOPOLOGY_DOC)
    return 0  # 详细测试由 deployment.py 的 _offline_verify 提供


def run_offline_deep() -> int:
    """调用 deployment.py 内部深度测试"""
    from vcmi_protocol.deployment import _offline_verify
    return _offline_verify()


# ---------------------------------------------------------------------------
# 实机部署入口 (需真实 VCMI)
# ---------------------------------------------------------------------------

def run_deploy(args) -> int:
    """
    实机部署流程 (Windows 侧 PowerShell 调起):
      python py/p8/p8d_scaffold_design.py --deploy --config p8d_config.json
    """
    cfg_path = args.config
    if not os.path.exists(cfg_path):
        print(f"部署配置文件不存在: {cfg_path}")
        return 1

    with open(cfg_path) as f:
        raw = json.load(f)

    # 构建 DeploymentConfig
    nodes = [
        NodeConfig(
            node_id=n["node_id"],
            host=n.get("host", "127.0.0.1"),
            port=n.get("port", 3030),
            vcmi_exe=n.get("vcmi_exe", ""),
            headless=n.get("headless", True),
            test_map=n.get("test_map", ""),
            is_server=n.get("is_server", True),
            is_client=n.get("is_client", False),
            client_count=n.get("client_count", 0),
        )
        for n in raw.get("nodes", [])
    ]
    cfg = DeploymentConfig(
        name=raw.get("name", "p8d"),
        nodes=nodes,
        hsk_file=raw.get("hsk_file", "./vcmi_hsk.key"),
        status_dir=raw.get("status_dir", "./vcmi_status"),
        log_dir=raw.get("log_dir", "./vcmi_logs"),
        timeout=raw.get("timeout", 30),
    )

    print(f"\n=== P8-D 实机部署: {cfg.name} ===")
    print(f"节点: {len(nodes)} 个")
    for n in nodes:
        print(f"  [{n.node_id}] {n.host}:{n.port} "
              f"(server={n.is_server}, client={n.is_client}×{n.client_count})")

    mgr = DeploymentManager(cfg)

    # 1. 密钥
    kd = KeyDistributor(cfg.hsk_file)
    if kd.load() is None:
        print("\n[密钥] 未找到 HSK, 生成新的...")
        kd.generate_and_save()
        print(f"  已保存到 {cfg.hsk_file}")
    else:
        print("\n[密钥] 已加载 HSK")

    # 2. 启动节点
    print("\n[部署] 启动节点...")
    results = mgr.deploy_all()
    for k, v in results.items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)}")

    # 3. 健康检查
    print("\n[健康] 全节点健康快照:")
    status = mgr.status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 4. 保持运行 (Ctrl+C 停止)
    print("\n[运行中] 按 Ctrl+C 停止...")
    try:
        while True:
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n[停止] 优雅关闭...")
        mgr.teardown()
        print("[完成]")
    return 0


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="P8-D 跨机器部署脚手架")
    ap.add_argument("--offline", action="store_true", default=True,
                    help="离线验证 (默认)")
    ap.add_argument("--offline-deep", action="store_true",
                    help="深度离线测试 (密钥+部署+状态)")
    ap.add_argument("--deploy", action="store_true",
                    help="实机部署")
    ap.add_argument("--config", type=str, default="p8d_config.json",
                    help="部署配置 JSON")
    args = ap.parse_args()

    if args.deploy:
        sys.exit(run_deploy(args))
    elif args.offline_deep:
        sys.exit(run_offline_deep())
    else:
        sys.exit(run_offline())


if __name__ == "__main__":
    main()
