#!/usr/bin/env python3
"""
T13.9 — 端到端验证测试
覆盖 T13.3-T13.8 全部子系统的集成测试

测试分类:
  A. 序列化往返 (T13.1-13.2 已有, 此处扩展)
  B. 战略包发送 (T13.4)
  C. 客户端包解析 (T13.5)
  D. Query 回复 (T13.6)
  E. 战斗包 (T13.7)
  F. 模型接入层 (T13.8)
  G. TCP 帧格式 (T13.3)
"""
import sys
import os
import struct
import time

# 添加包路径
import pathlib
sys.path.insert(0, 'D:/Bigdata/hero3_fresh/py')

from vcmi_protocol.serialization import BinarySerializer, BinaryDeserializer, encode_lvarint, decode_lvarint
from vcmi_protocol.types import (
    PlayerColor, ObjectInstanceID, QueryID, BattleID,
    BattleSide, EActionType, EPathfindingLayer,
    int3, BattleHex, DestinationInfo,
)
from vcmi_protocol.packs import (
    EndTurn, MoveHero, QueryReply, RecruitCreatures,
    BuildStructure, MakeAction, BattleAction,
    DismissHero, UpgradeCreature, SetFormation,
    CastAdvSpell, GamePause, HireHero,
    NewTurn, PackageApplied, TryMoveHero,
    PlayerStartsTurn, PlayerEndsTurn,
    SystemMessage, NewObject, GiveHero,
    ChangeObjPos, SetAvailableHero, SetAvailableCreatures,
    BattleStart, BattleResult, BattleLogMessage,
    HeroLevelUp, BlockingDialog, GarrisonDialog,
    SERVER_PACKS, CLIENT_PACKS,
)
from vcmi_protocol.protocol import (
    VCMIProtocolClient, QueryManager,
    parse_client_pack, parse_server_pack,
)
from vcmi_protocol.connection import VCMITCPConnection
from vcmi_protocol.model_bridge import ModelBridge, ModelState


PASS = 0
FAIL = 0
TOTAL = 0


def check(name, condition, detail=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def test_lvarint_roundtrip():
    """A1: LVarInt 往返"""
    values = [0, 1, 63, 64, 127, 128, 255, 1000, 65535, 2147483647,
              -1, -64, -65, -127, -128, -1000, -2147483648]
    for v in values:
        encoded = encode_lvarint(v)
        decoded, pos = decode_lvarint(encoded, 0)
        check(f"LVarInt({v})", decoded == v and pos == len(encoded),
              f"got {decoded}, pos {pos}, expected {v}, len {len(encoded)}")


def test_basic_types():
    """A2: 基本类型往返"""
    # Bool
    s = BinarySerializer()
    s.write_bool(True)
    s.write_bool(False)
    d = BinaryDeserializer(s.get_bytes())
    check("Bool True", d.read_bool() == True)
    check("Bool False", d.read_bool() == False)

    # Int
    s = BinarySerializer()
    for v in [0, 1, -1, 100, -100, 65535, -65535]:
        s.write_int(v)
    d = BinaryDeserializer(s.get_bytes())
    for v in [0, 1, -1, 100, -100, 65535, -65535]:
        check(f"Int({v})", d.read_int() == v)

    # Float
    s = BinarySerializer()
    s.write_float(3.14159)
    s.write_float(-2.718)
    d = BinaryDeserializer(s.get_bytes())
    check("Float 3.14159", abs(d.read_float() - 3.14159) < 0.001)
    check("Float -2.718", abs(d.read_float() - (-2.718)) < 0.001)

    # String
    s = BinarySerializer()
    s.write_string("")
    s.write_string("hello")
    s.write_string("hello")  # dedup
    d = BinaryDeserializer(s.get_bytes())
    check("String empty", d.read_string() == "")
    check("String hello", d.read_string() == "hello")
    check("String dedup", d.read_string() == "hello")


def test_int3():
    """A3: int3 坐标往返"""
    coords = [(0, 0, 0), (1, 2, 3), (-5, -10, 0), (1000, -1000, 500)]
    for x, y, z in coords:
        s = BinarySerializer()
        s.write_int3(x, y, z)
        d = BinaryDeserializer(s.get_bytes())
        result = d.read_int3()
        check(f"int3({x},{y},{z})", result == (x, y, z))


def test_server_packs():
    """B: 战略包序列化往返 (T13.4)"""
    packs = [
        ("EndTurn", EndTurn(player=1, request_id=1)),
        ("MoveHero", MoveHero(path=[(0,0,0),(1,0,0),(2,0,0)], hid=42, layer=0, player=1, request_id=2)),
        ("QueryReply", QueryReply(qid=7, reply=0, player=1, request_id=3)),
        ("QueryReply(None)", QueryReply(qid=8, reply=None, player=1, request_id=4)),
        ("RecruitCreatures", RecruitCreatures(tid=10, dst=42, crid="core:footman", amount=5, level=1, player=1, request_id=5)),
        ("BuildStructure", BuildStructure(tid=10, bid="core:tavern", player=1, request_id=6)),
        ("DismissHero", DismissHero(tid=10, hid=5, player=1, request_id=7)),
        ("UpgradeCreature", UpgradeCreature(tid=10, src="core:footman", dst="core:swordsman", amount=3, player=1, request_id=8)),
        ("SetFormation", SetFormation(tid=10, formation=1, player=1, request_id=9)),
        ("CastAdvSpell", CastAdvSpell(target=15, spell="core:Fireball", hero_id=42, player=1, request_id=10)),
        ("GamePause", GamePause(paused=True, player=1, request_id=11)),
        ("HireHero", HireHero(tid=10, cost=300, bid="core:tavern", player=1, request_id=12)),
    ]

    for name, pack in packs:
        s = BinarySerializer()
        pack.serialize_full(s)
        data = s.get_bytes()

        # Parse back — 实机指针帧: isNull(1B) + pid(LVarInt) + tid(LVarInt) + data
        result = parse_server_pack(data)
        type_id = result["type_id"] if result else -1

        expected_tid = pack.type_id
        check(f"{name} typeID", type_id == expected_tid, f"got {type_id}, expected {expected_tid}")

        # Check deserializer can read at least the base
        if pack.__class__ in [EndTurn, BuildStructure]:
            try:
                d = BinaryDeserializer(data)
                d.read_bool()   # isNull
                d.read_int()    # pid
                d.read_int()    # tid
                player = d.read_int()
                req_id = d.read_int()
                check(f"{name} base", player == pack.player and req_id == pack.request_id,
                      f"player={player}, req={req_id}")
            except Exception as e:
                check(f"{name} base", False, str(e))

        # Verify no remaining data for simple packs
        if pack.__class__ == EndTurn:
            d = BinaryDeserializer(data)
            d.read_bool(); d.read_int(); d.read_int(); d.read_int(); d.read_int()
            check(f"{name} no extra", d.get_remaining() == 0, f"remaining={d.get_remaining()}")


def test_movehero_detailed():
    """B2: MoveHero 详细验证"""
    # Empty path
    pack = MoveHero(path=[], hid=1, layer=0, player=1, request_id=1)
    s = BinarySerializer()
    pack.serialize_full(s)
    d = BinaryDeserializer(s.get_bytes())
    d.read_bool()    # isNull
    d.read_int()     # pid
    d.read_int()     # tid
    d.read_int()     # player
    d.read_int()     # request_id
    path_len = d.read_int()
    check("MoveHero empty path", path_len == 0)

    # 10 point path
    path = [(i, 0, 0) for i in range(10)]
    pack = MoveHero(path=path, hid=5, layer=1, player=2, request_id=2)
    s = BinarySerializer()
    pack.serialize_full(s)
    d = BinaryDeserializer(s.get_bytes())
    d.read_bool()
    d.read_int()
    d.read_int()
    d.read_int()
    d.read_int()
    path_len = d.read_int()
    check("MoveHero 10 points", path_len == 10)
    for i, expected in enumerate(path):
        x, y, z = d.read_int(), d.read_int(), d.read_int()
        check(f"MoveHero path[{i}]", (x, y, z) == expected)

    layer = d.read_int()
    hid = d.read_int()
    transit = d.read_bool()
    check("MoveHero layer", layer == 1)
    check("MoveHero hid", hid == 5)
    check("MoveHero transit", transit == False)


def test_battle_action():
    """E: 战斗包 (T13.7)"""
    # Move action
    action = BattleAction(
        side=BattleSide.LEFT,
        stack_number=3,
        action_type=EActionType.MOVE,
        spell="",
        target=[(0, 5, 8)]  # unit_value, hex_x, hex_y
    )

    s = BinarySerializer()
    s.write_uint16(MakeAction.type_id)
    s.write_int(PlayerColor.BLUE)
    s.write_int(1)  # request_id
    action.serialize(s)
    s.write_int(42)  # battle_id

    d = BinaryDeserializer(s.get_bytes())
    d.read_uint16()  # typeID
    d.read_int()     # player
    d.read_int()     # request_id

    # Read BattleAction
    side = d.read_int()
    stack_num = d.read_int()
    action_type = d.read_int()
    spell = d.read_string()
    target_len = d.read_int()

    check("BattleAction side", side == BattleSide.LEFT)
    check("BattleAction stack", stack_num == 3)
    check("BattleAction type", action_type == EActionType.MOVE)
    check("BattleAction spell", spell == "")
    check("BattleAction target_len", target_len == 1)

    # Target
    unit_val = d.read_int()
    hex_x = d.read_int()
    hex_y = d.read_int()
    check("BattleAction target", (unit_val, hex_x, hex_y) == (0, 5, 8))

    bid = d.read_int()
    check("MakeAction bid", bid == 42)


def test_client_packs():
    """C: 客户端包解析 (T13.5)"""
    # NewTurn
    pack = NewTurn(turn=5)
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    check("NewTurn parse", result is not None)
    if result:
        check("NewTurn class", result["class_name"] == "NewTurn")
        check("NewTurn turn", result.get("turn") == 5)

    # SystemMessage
    pack = SystemMessage(message="Hello world!")
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("SystemMessage parse", result["class_name"] == "SystemMessage")
        check("SystemMessage msg", result.get("message") == "Hello world!")

    # PlayerStartsTurn
    pack = PlayerStartsTurn(time_limit=60)
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("PlayerStartsTurn parse", result["class_name"] == "PlayerStartsTurn")
        check("PlayerStartsTurn time_limit", result.get("time_limit") == 60)

    # BattleStart
    pack = BattleStart(bid=7)
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("BattleStart parse", result["class_name"] == "BattleStart")
        check("BattleStart bid", result.get("bid") == 7)

    # BattleResult
    pack = BattleResult(bid=7, winner=0)
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("BattleResult parse", result["class_name"] == "BattleResult")
        check("BattleResult winner", result.get("winner") == 0)

    # HeroLevelUp
    pack = HeroLevelUp(hid=3, level_ups=[5, 8])
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("HeroLevelUp parse", result["class_name"] == "HeroLevelUp")
        check("HeroLevelUp hid", result.get("hid") == 3)
        check("HeroLevelUp ups", result.get("level_ups") == [5, 8])

    # ChangeObjPos
    pack = ChangeObjPos(obj_id=10, old_pos=int3(1, 2, 0), new_pos=int3(5, 6, 0))
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("ChangeObjPos parse", result["class_name"] == "ChangeObjPos")
        check("ChangeObjPos obj_id", result.get("obj_id") == 10)

    # PackageApplied
    pack = PackageApplied(request_id=3, is_successful=True)
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("PackageApplied parse", result["class_name"] == "PackageApplied")
        check("PackageApplied req", result.get("request_id") == 3)
        check("PackageApplied success", result.get("is_successful") == True)

    # TryMoveHero
    pack = TryMoveHero(source=10, destination=11, reason="Blocked by enemy")
    s = BinarySerializer()
    pack.serialize_full(s)
    data = s.get_bytes()
    result = parse_client_pack(data)
    if result:
        check("TryMoveHero parse", result["class_name"] == "TryMoveHero")
        check("TryMoveHero reason", result.get("reason") == "Blocked by enemy")

    # Unknown pack type — 实机指针帧: isNull + pid + tid(9999)
    s = BinarySerializer()
    s.write_bool(False)
    s.write_int(0)
    s.write_int(9999)
    s.write_int(0)
    data = s.get_bytes()
    result = parse_client_pack(data)
    check("Unknown pack", result is not None and result["class_name"] == "UNKNOWN")


def test_query_manager():
    """D: Query 管理器 (T13.6)"""
    sent = []
    sent_fn = lambda pack: sent.append(pack)

    mgr = QueryManager(player=1, auto_reply=True)

    # PlayerStartsTurn
    result = {"type_id": 88, "class_name": "PlayerStartsTurn", "data": {}}
    reply = mgr.handle_query(result, sent_fn)
    check("Query auto-reply PlayerStartsTurn", reply is not None)
    check("Query reply type", isinstance(reply, QueryReply))
    check("Query reply value", reply.reply == 0)
    check("Query sent", len(sent) == 1)

    # Custom handler
    mgr.register_handler(154, lambda data: 3)  # HeroLevelUp → choose skill 3
    result = {"type_id": 154, "class_name": "HeroLevelUp", "data": {"hid": 1}}
    reply = mgr.handle_query(result, sent_fn)
    check("Query custom handler", reply.reply == 3)

    # Stats
    stats = mgr.get_stats()
    check("Query stats total", stats["total_queries"] == 2)
    check("Query stats handlers", 154 in stats["handlers"])


def test_tcp_frame():
    """G: TCP 帧格式 (T13.3)"""
    # Frame construction
    payload = b'\x00\x01\x02\x03'
    frame = struct.pack('<I', len(payload)) + payload
    check("Frame length", struct.unpack('<I', frame[:4])[0] == 4)
    check("Frame payload", frame[4:] == payload)

    # Heartbeat (empty)
    hb = struct.pack('<I', 0)
    check("Heartbeat frame", len(hb) == 4)

    # Connection object (no actual connection)
    conn = VCMITCPConnection("127.0.0.1", 5555)
    check("Connection init", not conn.connected)
    check("Connection host", conn.host == "127.0.0.1")
    check("Connection port", conn.port == 5555)


def test_protocol_client_init():
    """F: 协议客户端初始化 (T13.8)"""
    client = VCMIProtocolClient("127.0.0.1", 5555, player=1)
    check("Client init", client.player == 1)
    check("Client query_mgr", isinstance(client.query_mgr, QueryManager))
    check("Client not connected", not client.conn.connected)

    # Request counter
    r1 = client._next_request_id()
    r2 = client._next_request_id()
    check("Request counter", r1 == 1 and r2 == 2)

    # Stats
    stats = client.get_stats()
    check("Stats connected", stats["connected"] == False)
    check("Stats sent", stats["packets_sent"] == 0)


def test_model_bridge():
    """F2: 模型接入层 (T13.8)"""
    client = VCMIProtocolClient("127.0.0.1", 5555, player=1)
    bridge = ModelBridge(client, model=None)

    check("Bridge obs_dim", bridge.OBS_DIM == 3464)
    check("Bridge n_actions", bridge.N_ACTIONS == 25)
    check("Bridge action_map", len(bridge.ACTION_MAP) == 25)

    # Action names
    names = [bridge.ACTION_MAP[i][0] for i in range(25)]
    check("Bridge action 0", names[0] == "move_north")
    check("Bridge action 10", names[10] == "end_turn")
    check("Bridge action 24", names[24] == "wait")

    # Step (no model → default end_turn)
    result = bridge.step()
    check("Bridge step has obs", "observation" in result)
    check("Bridge step obs dim", len(result["observation"]) == 3464)
    check("Bridge step action", result["action"] == 10)  # default end_turn
    check("Bridge step done", result["done"] == True)

    # Stats
    stats = bridge.get_stats()
    check("Bridge stats turn", "turn" in stats)
    check("Bridge stats client", "client_stats" in stats)


def test_all_pack_registries():
    """H: 包注册表完整性"""
    # Server packs
    check("SERVER_PACKS count", len(SERVER_PACKS) >= 12, f"got {len(SERVER_PACKS)}")
    check("SERVER_PACKS has EndTurn", 180 in SERVER_PACKS)
    check("SERVER_PACKS has MoveHero", 182 in SERVER_PACKS)
    check("SERVER_PACKS has QueryReply", 197 in SERVER_PACKS)
    check("SERVER_PACKS has MakeAction", 198 in SERVER_PACKS)

    # Client packs
    check("CLIENT_PACKS count", len(CLIENT_PACKS) >= 16, f"got {len(CLIENT_PACKS)}")
    check("CLIENT_PACKS has NewTurn", 116 in CLIENT_PACKS)
    check("CLIENT_PACKS has PlayerStartsTurn", 88 in CLIENT_PACKS)
    check("CLIENT_PACKS has BattleStart", 132 in CLIENT_PACKS)
    check("CLIENT_PACKS has HeroLevelUp", 154 in CLIENT_PACKS)


def test_packet_size():
    """I: 包大小分析"""
    packs = [
        ("EndTurn", EndTurn(player=1, request_id=0)),
        ("MoveHero(1pt)", MoveHero(path=[(1,2,0)], hid=42, layer=0, player=1, request_id=0)),
        ("MoveHero(10pt)", MoveHero(path=[(i,0,0) for i in range(10)], hid=42, layer=0, player=1, request_id=0)),
        ("QueryReply(0)", QueryReply(qid=7, reply=0, player=1, request_id=0)),
        ("RecruitCreatures", RecruitCreatures(tid=10, dst=42, crid="core:footman", amount=5, level=1, player=1, request_id=0)),
        ("BuildStructure", BuildStructure(tid=10, bid="core:tavern", player=1, request_id=0)),
        ("MakeAction(move)", MakeAction(
            action=BattleAction(side=0, stack_number=3, action_type=1, spell="", target=[(0,5,8)]),
            bid=42, player=1, request_id=0)),
        ("GamePause", GamePause(paused=True, player=1, request_id=0)),
        ("CastAdvSpell", CastAdvSpell(target=15, spell="core:Fireball", hero_id=42, player=1, request_id=0)),
    ]

    print("  --- 包大小 ---")
    for name, pack in packs:
        data = pack.to_bytes()
        print(f"    {name}: {len(data)} bytes")
        check(f"{name} < 64MB", len(data) < 65536, f"too large: {len(data)}")


def main():
    global PASS, FAIL, TOTAL
    print("=" * 60)
    print("T13.9 — VCMI 协议客户端端到端验证")
    print("=" * 60)

    tests = [
        ("A1: LVarInt 往返", test_lvarint_roundtrip),
        ("A2: 基本类型", test_basic_types),
        ("A3: int3 坐标", test_int3),
        ("B: 战略包序列化", test_server_packs),
        ("B2: MoveHero 详细", test_movehero_detailed),
        ("E: 战斗包", test_battle_action),
        ("C: 客户端包解析", test_client_packs),
        ("D: Query 管理器", test_query_manager),
        ("G: TCP 帧格式", test_tcp_frame),
        ("F: 协议客户端", test_protocol_client_init),
        ("F2: 模型接入层", test_model_bridge),
        ("H: 包注册表", test_all_pack_registries),
        ("I: 包大小分析", test_packet_size),
    ]

    for name, fn in tests:
        print(f"\n--- {name} ---")
        try:
            fn()
        except Exception as e:
            FAIL += 1
            TOTAL += 1
            print(f"  ❌ {name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"结果: {PASS} passed, {FAIL} failed / {TOTAL} total")
    print(f"{'=' * 60}")

    if FAIL == 0:
        print("\n✅ 全部通过! T13.3-T13.8 验证完成。")
    return FAIL == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
