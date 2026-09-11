#!/usr/bin/env python3
"""
P8-B 第一步 — Python 连真实 VCMI server, 完成 lobby 握手
实验目的: 验证 LobbyClientConnected 帧格式是否被 server 接受

用法:
  1. 启动 server:  VCMI_server.exe --port=3030  (不要 --run-by-client)
  2. 跑本脚本:     python py/p8b_lobby_probe.py

预期: server 日志出现 "Connection with client 1 established"
"""
import sys
import os
import time
import uuid as uuidlib

sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')

from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected, LobbyQueryState

HOST = '127.0.0.1'
PORT = 3030


def hexdump(data: bytes, limit: int = 128) -> str:
    h = data[:limit].hex()
    return ' '.join(h[i:i+2] for i in range(0, len(h), 2))


def try_parse_lobby(data: bytes):
    """尝试按指针帧解析 lobby 包"""
    deser = BinaryDeserializer(data)
    try:
        is_null = deser.read_bool()
        if is_null:
            return {"frame": "null-ptr"}
        deser.read_int()  # pid
        tid = deser.read_int()
        return {"frame": "ptr", "tid": tid, "consumed": deser.pos}
    except Exception as e:
        return {"frame": "parse-error", "error": str(e)}


LOBBY_TIDS = {
    216: "LobbyClientConnected",
    217: "LobbyClientDisconnected",
    218: "LobbyChatMessage",
    224: "LobbyStartGame",
    226: "LobbyUpdateState",
    229: "LobbySetMap",
    265: "LobbyQueryState",
    266: "LobbyModsCheck",
}


def main():
    # 实机语义 (0911 P8-B 首次实锤): version 会被 server 取 min(pack.version, CURRENT)
    # 并 setSerializationVersion — 发 0 会把 server 端 deserializer 版本清零 → 解析崩溃
    # 官方客户端默认 = ESerializationVersion::CURRENT = CONTROL_LOSS_TRACKING = 905
    ESERIALIZATION_VERSION_CURRENT = 905

    print(f"=== P8-B lobby probe: {HOST}:{PORT} ===")

    conn = VCMITCPConnection(HOST, PORT)
    if not conn.connect():
        print("[FAIL] 连不上 server — 先启动 VCMI_server.exe --port=3030")
        return 1

    print("[OK] TCP 已连接, 等待 server 首包 (3s)...")
    time.sleep(3)

    # server 通常不主动发首包, 客户端先发 LobbyClientConnected
    my_uuid = str(uuidlib.uuid4())
    lcc = LobbyClientConnected(
        uuid=my_uuid,
        names=["PyProbe"],
        mode=0,  # EStartMode::NEW_GAME
        # version 默认 905 (raw int32), clientId/hostClientId 默认 -1 — 与官方 client 字节一致
    )
    payload = lcc.to_bytes()
    print(f"[SEND] LobbyClientConnected ({len(payload)}B): {hexdump(payload)}")

    # 预期帧: isNull(00) + pid(00) + tid(216=d801) + uuid字符串 + names + mode
    ok = conn.send_frame(payload)
    print(f"[SEND] result={ok}")

    # 收包循环 10s
    print("[RECV] 监听 10s ...")
    deadline = time.time() + 10
    got_any = False
    while time.time() < deadline:
        data = conn.recv_frame()
        if data is None:
            continue
        if len(data) == 0:
            print("[RECV] heartbeat")
            continue
        got_any = True
        info = try_parse_lobby(data)
        tid = info.get("tid")
        name = LOBBY_TIDS.get(tid, "?")
        print(f"[RECV] {len(data)}B tid={tid}({name}) frame={info}")
        print(f"       hex: {hexdump(data)}")

    if not got_any:
        print("[WARN] 10s 无任何包 — 可能 server 拒绝了握手 (看 server_log.txt)")

    conn.disconnect()
    return 0


if __name__ == '__main__':
    sys.exit(main())
