#!/usr/bin/env python3
"""
P8-B 阶段2 实验 — 方案 B: 真实 client 当 host 装地图, Python 后连当 guest AI
  1. 起 server (3030)
  2. 起 client1: --testmap Twins.h3m --donotstartserver (VCMI_TESTMAP_ONLYAI=1, host)
  3. 2s 后 Python 连入 → guest AI 槽
  4. 观察: LobbySetMap / LobbyUpdateState / LobbyStartGame / 游戏包流
"""
import sys
import os
import time
import uuid as uuidlib
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.serialization import BinaryDeserializer
from vcmi_protocol.packs import LobbyClientConnected

HOST = '127.0.0.1'
PORT = 3030
BIN = r'D:\vcmi-fork-build\bin'

LOBBY_TIDS = {216: 'LobbyClientConnected', 217: 'LobbyClientDisconnected',
              218: 'LobbyChatMessage', 224: 'LobbyStartGame', 226: 'LobbyUpdateState',
              229: 'LobbySetMap', 265: 'LobbyQueryState', 266: 'LobbyModsCheck',
              227: 'LobbyShowMessage'}

# 游戏客户端包 (GAMEPLAY 状态) 关键类型
GAME_TIDS = {88: 'PlayerStartsTurn', 116: 'NewTurn', 132: 'BattleStart',
             135: 'BattleResult', 84: 'PackageApplied', 85: 'SystemMessage',
             109: 'TryMoveHero', 115: 'GiveHero', 121: 'NewObject',
             154: 'HeroLevelUp', 156: 'BlockingDialog', 157: 'GarrisonDialog',
             102: 'PlayerEndsTurn'}


def kill_all():
    subprocess.run(['taskkill', '/F', '/IM', 'VCMI_server.exe'], capture_output=True)
    subprocess.run(['taskkill', '/F', '/IM', 'VCMI_client.exe'], capture_output=True)
    time.sleep(1)


def start_server():
    logf = open(r'C:\Users\Administrator\AppData\Local\Temp\p8b2_srv.log', 'w')
    proc = subprocess.Popen([BIN + r'\VCMI_server.exe', '--port=3030'],
                            cwd=BIN, stdout=logf, stderr=subprocess.STDOUT)
    time.sleep(9)
    return proc


def start_client1():
    env = dict(os.environ)
    env['VCMI_TESTMAP_ONLYAI'] = '1'
    logf = open(r'C:\Users\Administrator\AppData\Local\Temp\p8b2_cli.log', 'w')
    proc = subprocess.Popen([BIN + r'\VCMI_client.exe', '--testmap', 'Maps/Twins.h3m',
                             '--donotstartserver', '--serverport', '3030', '--headless'],
                            cwd=BIN, stdout=logf, stderr=subprocess.STDOUT, env=env)
    return proc


def ptr_header(d):
    isnull = d.read_bool()
    if isnull:
        return False, None, None
    pid = d.read_int()
    tid = d.read_int()
    return True, pid, tid


def main():
    print("=== P8-B phase2: real client host + python guest ===")
    kill_all()
    srv = start_server()
    print(f"[1] server pid={srv.pid}")
    cli = start_client1()
    print(f"[2] client1 (host/map-setter) pid={cli.pid}")
    # 时序实锤 (0911 首测): client1 ~1s 完成连接进 mi-loop, mi 回显后立即 setPlayer+StartGame。
    # Python 必须在 client1 发 StartGame 前连入 (LOBBY 态), 否则 GAMEPLAY 态新连接被拒 (10054)。
    time.sleep(0.8)

    conn = VCMITCPConnection(HOST, PORT)
    if not conn.connect():
        print("[FAIL] python connect")
        return 1
    print("[3] python connected, sending LobbyClientConnected")

    lcc = LobbyClientConnected(uuid=str(uuidlib.uuid4()), names=["PyAI"], mode=0)
    conn.send_frame(lcc.to_bytes())

    # 收包 30s, 记录包类型流
    seen_types = {}
    start_game_seen = False
    deadline = time.time() + 30
    while time.time() < deadline:
        data = conn.recv_frame()
        if data is None:
            if not conn.connected:
                print("[RECV] 连接断开")
                break
            continue
        if len(data) == 0:
            continue
        d = BinaryDeserializer(data)
        isnull = d.read_bool()
        if isnull:
            continue
        d.read_int()
        tid = d.read_int()
        name = LOBBY_TIDS.get(tid) or GAME_TIDS.get(tid) or f'?{tid}'
        seen_types[name] = seen_types.get(name, 0) + 1
        print(f"[RECV] {len(data):5d}B tid={tid} {name}")

        if tid == 224:  # LobbyStartGame
            start_game_seen = True
            print("[KEY] LobbyStartGame 收到! 进入 GAMEPLAY 流")

        if tid == 88:  # PlayerStartsTurn
            print("[KEY] PlayerStartsTurn — 游戏回合流转中!")

    print("\n=== 包统计 ===")
    for k, v in sorted(seen_types.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    conn.disconnect()
    print(f"\nRESULT: start_game={'YES' if start_game_seen else 'NO'}")
    return 0 if start_game_seen else 2


if __name__ == '__main__':
    sys.exit(main())
