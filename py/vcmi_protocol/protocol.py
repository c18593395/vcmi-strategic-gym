"""
T13.5 — 客户端包解析器 + T13.4 — 战略包发送器 + T13.6 — Query 回复管理器
完整协议客户端: 接收/解析服务器包, 发送战略包, 自动回复 Query
"""
import threading
import time
from typing import Optional, Callable
from .connection import VCMITCPConnection
from .serialization import BinaryDeserializer, BinarySerializer
from .packs import (
    CPackForServer, CPackForClient,
    EndTurn, MoveHero, QueryReply, RecruitCreatures,
    MakeAction, BattleAction,
    SERVER_PACKS, CLIENT_PACKS,
    PlayerStartsTurn, NewTurn, PackageApplied,
    PlayerEndsTurn, SystemMessage,
    BattleStart, BattleResult,
    HeroLevelUp, BlockingDialog, GarrisonDialog,
    ChangeObjPos, TryMoveHero,
)


# ============================================================
# 包解析器 — typeID → deserialize
# ============================================================

def parse_client_pack(data: bytes) -> Optional[dict]:
    """
    解析服务器→客户端包
    返回 {type_id, class_name, data} 或 None
    """
    deser = BinaryDeserializer(data)
    try:
        type_id = deser.read_uint16()
    except (IndexError, struct.error):
        return None

    pack_class = CLIENT_PACKS.get(type_id)
    if pack_class is None:
        return {"type_id": type_id, "class_name": "UNKNOWN", "data": {}, "raw": data}

    try:
        result = pack_class.deserialize(deser)
        result["type_id"] = type_id
        result["class_name"] = pack_class.__name__
        result["raw"] = data
        return result
    except Exception as e:
        return {"type_id": type_id, "class_name": pack_class.__name__,
                "data": {"error": str(e)}, "raw": data}


def parse_server_pack(data: bytes) -> Optional[dict]:
    """
    解析客户端→服务器包 (测试/调试用)
    """
    deser = BinaryDeserializer(data)
    try:
        type_id = deser.read_uint16()
    except (IndexError, struct.error):
        return None

    pack_class = SERVER_PACKS.get(type_id)
    if pack_class is None:
        return {"type_id": type_id, "class_name": "UNKNOWN", "data": {}}

    try:
        result = pack_class.deserialize(deser)
        result["type_id"] = type_id
        result["class_name"] = pack_class.__name__
        return result
    except Exception as e:
        return {"type_id": type_id, "class_name": pack_class.__name__,
                "data": {"error": str(e)}}


# ============================================================
# Query 管理器 (T13.6)
# ============================================================

class QueryManager:
    """
    Query 回复管理器
    
    VCMI 的 Query 机制:
    - 服务器发送 Query 包 (PlayerStartsTurn, HeroLevelUp, BlockingDialog, etc.)
    - 客户端必须回复 QueryReply, 否则服务器超时
    
    自动回复策略:
    - PlayerStartsTurn → reply=0 (接受开始回合)
    - HeroLevelUp → reply=0 (接受升级)
    - BlockingDialog → reply=0 (确认)
    - GarrisonDialog → reply=0 (确认)
    - 其他 Query → reply=0 (默认接受)
    """

    # Query 包 typeID
    QUERY_TYPES = {
        88: "PlayerStartsTurn",
        154: "HeroLevelUp",
        156: "BlockingDialog",
        157: "GarrisonDialog",
        158: "ExchangeDialog",
        159: "TeleportDialog",
        160: "MapObjectSelectDialog",
    }

    def __init__(self, player: int = 1, auto_reply: bool = True):
        self.player = player
        self.auto_reply = auto_reply
        self.query_handlers = {}  # type_id -> callback(query_data) -> reply_value
        self.last_query_id = 0
        self.query_history = []

        # 默认回复: 接受所有 Query
        self._default_handler = lambda qid, data: 0

    def register_handler(self, query_type_id: int, handler: Callable):
        """注册 Query 处理器"""
        self.query_handlers[query_type_id] = handler

    def should_auto_reply(self, type_id: int) -> bool:
        """判断是否应该自动回复"""
        return self.auto_reply and type_id in self.QUERY_TYPES

    def handle_query(self, query_data: dict, send_fn: Callable) -> Optional[QueryReply]:
        """
        处理 Query, 返回 QueryReply 包
        send_fn: 发送函数 (pack) -> bool
        """
        type_id = query_data.get("type_id", 0)
        query_name = query_data.get("class_name", "Unknown")

        # 从 Query 包中提取 qid
        # 大部分 Query 包的 qid 在 base 中或通过特定字段
        # PlayerStartsTurn: 无 qid 字段, 用 type_id 代替
        # 但实际 VCMI 中 qid 是 QueryID, 在 QueryReply 中需要正确引用

        # 从 raw data 提取 QueryID
        # Query 包结构: [typeID: uint16] [base data] [specific fields]
        # 对于需要回复的 Query, VCMI 会分配 QueryID

        # 简化: 用 type_id 作为 qid (实际中 QueryID 由服务器分配)
        qid = type_id

        # 检查是否有自定义处理器
        if type_id in self.query_handlers:
            reply_value = self.query_handlers[type_id](query_data)
        else:
            reply_value = self._default_handler(qid, query_data)

        # 构建 QueryReply
        reply = QueryReply(
            qid=qid,
            reply=reply_value,
            player=self.player,
            request_id=0,
        )

        # 发送
        send_fn(reply)
        print(f"[QUERY] 自动回复 {query_name}: qid={qid}, reply={reply_value}")

        self.query_history.append({
            "type_id": type_id,
            "name": query_name,
            "reply": reply_value,
            "time": time.time(),
        })

        return reply

    def get_stats(self) -> dict:
        return {
            "auto_reply": self.auto_reply,
            "total_queries": len(self.query_history),
            "handlers": list(self.query_handlers.keys()),
        }


# ============================================================
# 协议客户端 (T13.4 + T13.5 整合)
# ============================================================

class VCMIProtocolClient:
    """
    VCMI 协议客户端 — 完整的外挂 AI 客户端
    
    功能:
    1. TCP 连接管理 (T13.3)
    2. 包序列化/反序列化 (T13.1-13.2)
    3. 战略包发送 (T13.4)
    4. 客户端包解析 (T13.5)
    5. Query 自动回复 (T13.6)
    6. 战斗包对接 (T13.7)
    
    架构:
    - 后台线程持续接收服务器包
    - 解析后分发给回调
    - Query 包自动回复
    - AI 决策通过 send_* 方法发送
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555,
                 player: int = 1, auto_reply: bool = True):
        self.conn = VCMITCPConnection(host, port)
        self.player = player
        self.query_mgr = QueryManager(player, auto_reply)
        
        # 回调
        self.on_turn_start: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
        self.on_battle_start: Optional[Callable] = None
        self.on_battle_result: Optional[Callable] = None
        self.on_system_message: Optional[Callable] = None
        self.on_new_turn: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # 状态
        self._running = False
        self._recv_thread = None
        self._heartbeat_thread = None
        self.current_turn = 0
        self.request_counter = 0
        self.in_battle = False
        self.turn_started = False

        # 包统计
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_by_type = {}

    def connect(self) -> bool:
        """连接并开始接收循环"""
        if not self.conn.connect():
            return False

        self._running = True
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        print(f"[CLIENT] 协议客户端已启动 (player={self.player})")
        return True

    def disconnect(self):
        """停止接收循环并断开"""
        self._running = False
        self.conn.disconnect()
        if self._recv_thread:
            self._recv_thread.join(timeout=3)
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=3)
        print(f"[CLIENT] 已断开 (发送 {self.packets_sent}, 接收 {self.packets_received})")

    def _next_request_id(self) -> int:
        self.request_counter += 1
        return self.request_counter

    # ============================================================
    # 战略包发送 (T13.4)
    # ============================================================

    def send_end_turn(self) -> bool:
        """结束回合"""
        pack = EndTurn(player=self.player, request_id=self._next_request_id())
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
            print(f"[SEND] EndTurn (req={pack.request_id})")
        return ok

    def send_move_hero(self, path: list, hid: int, layer: int = 0) -> bool:
        """移动英雄"""
        pack = MoveHero(path=path, hid=hid, layer=layer,
                        player=self.player, request_id=self._next_request_id())
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
            print(f"[SEND] MoveHero (req={pack.request_id}, path={len(path)} points)")
        return ok

    def send_recruit(self, tid: int, dst: int, creature_id: str,
                     amount: int = 1, level: int = 0) -> bool:
        """招募生物"""
        pack = RecruitCreatures(tid=tid, dst=dst, crid=creature_id,
                                amount=amount, level=level,
                                player=self.player, request_id=self._next_request_id())
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
            print(f"[SEND] RecruitCreatures (req={pack.request_id})")
        return ok

    def send_build(self, tid: int, building_id: str) -> bool:
        """建设"""
        from .packs import BuildStructure
        pack = BuildStructure(tid=tid, bid=building_id,
                              player=self.player, request_id=self._next_request_id())
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
            print(f"[SEND] BuildStructure (req={pack.request_id})")
        return ok

    def send_battle_action(self, action: BattleAction, battle_id: int) -> bool:
        """战斗动作"""
        pack = MakeAction(action=action, bid=battle_id,
                          player=self.player, request_id=self._next_request_id())
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
            print(f"[SEND] MakeAction (req={pack.request_id}, bid={battle_id})")
        return ok

    def send_query_reply(self, qid: int, reply: int) -> bool:
        """回复查询"""
        pack = QueryReply(qid=qid, reply=reply,
                          player=self.player, request_id=self._next_request_id())
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
            print(f"[SEND] QueryReply (req={pack.request_id}, qid={qid})")
        return ok

    def send_raw(self, pack) -> bool:
        """发送任意包"""
        ok = self.conn.send_pack(pack)
        if ok:
            self.packets_sent += 1
        return ok

    # ============================================================
    # 包接收循环 (T13.5)
    # ============================================================

    def _recv_loop(self):
        """后台接收循环"""
        while self._running:
            data = self.conn.recv_frame()
            if data is None:
                if not self.conn.connected:
                    print("[RECV] 连接断开")
                    break
                continue

            if len(data) == 0:
                # heartbeat
                continue

            self.packets_received += 1
            self._handle_packet(data)

    def _handle_packet(self, data: bytes):
        """处理接收到的包"""
        result = parse_client_pack(data)
        if result is None:
            print(f"[RECV] 无法解析: {data[:20].hex()}")
            return

        type_id = result["type_id"]
        class_name = result["class_name"]

        self.packets_by_type[class_name] = self.packets_by_type.get(class_name, 0) + 1

        # Query 自动回复
        if self.query_mgr.should_auto_reply(type_id):
            self.query_mgr.handle_query(result, self.send_raw)
            return

        # 分发到回调
        self._dispatch(result)

    def _dispatch(self, result: dict):
        """分发包到回调"""
        class_name = result["class_name"]
        data = result.get("data", {})

        if class_name == "PlayerStartsTurn":
            self.turn_started = True
            print(f"[RECV] PlayerStartsTurn (player {data.get('player', '?')})")
            if self.on_turn_start:
                self.on_turn_start(data)

        elif class_name == "PlayerEndsTurn":
            self.turn_started = False
            print(f"[RECV] PlayerEndsTurn")
            if self.on_turn_end:
                self.on_turn_end(data)

        elif class_name == "NewTurn":
            self.current_turn = data.get("turn", self.current_turn + 1)
            print(f"[RECV] NewTurn (turn {self.current_turn})")
            if self.on_new_turn:
                self.on_new_turn(data)

        elif class_name == "SystemMessage":
            msg = data.get("message", "")
            print(f"[RECV] SystemMessage: {msg}")
            if self.on_system_message:
                self.on_system_message(data)

        elif class_name == "BattleStart":
            self.in_battle = True
            bid = data.get("bid", 0)
            print(f"[RECV] BattleStart (bid={bid})")
            if self.on_battle_start:
                self.on_battle_start(data)

        elif class_name == "BattleResult":
            self.in_battle = False
            winner = data.get("winner", -1)
            print(f"[RECV] BattleResult (winner={winner})")
            if self.on_battle_result:
                self.on_battle_result(data)

        elif class_name == "PackageApplied":
            req_id = data.get("request_id", 0)
            ok = data.get("is_successful", True)
            status = "OK" if ok else "FAIL"
            print(f"[RECV] PackageApplied (req={req_id}, {status})")

        elif class_name == "TryMoveHero":
            print(f"[RECV] TryMoveHero (reason={data.get('reason', '?')})")

        else:
            print(f"[RECV] {class_name} (type={result['type_id']})")

    # ============================================================
    # 心跳循环
    # ============================================================

    def _heartbeat_loop(self):
        """定时发送心跳"""
        from .connection import HEARTBEAT_INTERVAL
        while self._running:
            time.sleep(HEARTBEAT_INTERVAL)
            if self._running and self.conn.connected:
                self.conn.send_heartbeat()

    # ============================================================
    # 状态查询
    # ============================================================

    def get_stats(self) -> dict:
        return {
            "connected": self.conn.connected,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packets_by_type": dict(self.packets_by_type),
            "current_turn": self.current_turn,
            "in_battle": self.in_battle,
            "turn_started": self.turn_started,
            "query_stats": self.query_mgr.get_stats(),
        }
