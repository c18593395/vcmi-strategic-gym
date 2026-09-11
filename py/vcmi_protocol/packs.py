"""
T13.4/T13.5 — VCMI 网络包定义
CPackForServer (客户端→服务器) 和 CPackForClient (服务器→客户端)
"""
from .serialization import BinarySerializer, BinaryDeserializer
from .types import (
    PlayerColor, ObjectInstanceID, QueryID, BattleID,
    BattleSide, EActionType, EPathfindingLayer,
    int3, BattleHex, DestinationInfo,
)


# ============================================================
# CPackForServer 基类
# ============================================================
class CPackForServer:
    """CPackForServer 基类 — 所有客户端→服务器包的基类"""

    type_id = 179  # CPackForServer 基类 ID

    def __init__(self, player: int = PlayerColor.BLUE, request_id: int = 0):
        self.player = player
        self.request_id = request_id

    def serialize(self, ser: BinarySerializer):
        """
        CPackForServer 序列化:
        [player: LVarInt] [requestID: LVarInt] + 子类字段
        """
        ser.write_int(self.player)
        ser.write_int(self.request_id)

    @staticmethod
    def deserialize_base(deser: BinaryDeserializer) -> dict:
        player = deser.read_int()
        request_id = deser.read_int()
        return {"player": player, "request_id": request_id}

    # 实机帧格式 (BinaryDeserializer::loadRawPointer, 0911 P8-B 实锤):
    # 顶层包 = 指针序列化: isNull(1B) + pid(LVarInt) + tid(LVarInt) + 包数据
    # 旧实现 write_uint16(type_id) 是错的 — server 端 deserializer 按 isNull+pid+tid 读
    def serialize_full(self, ser: BinarySerializer):
        """完整序列化: [isNull:1B=0] [pid:LVarInt] [tid:LVarInt] + 包数据"""
        ser.write_bool(False)      # isNull = false
        ser.write_int(0)           # pid = 0 (首指针)
        ser.write_int(self.type_id)  # tid = LVarInt
        self.serialize(ser)

    def to_bytes(self) -> bytes:
        """序列化为 bytes"""
        ser = BinarySerializer()
        self.serialize_full(ser)
        return ser.get_bytes()


# ============================================================
# 战略包 — CPackForServer 子类
# ============================================================

class EndTurn(CPackForServer):
    """结束回合 — typeID 180, 无额外字段"""
    type_id = 180

    def serialize(self, ser):
        super().serialize(ser)
        # 无额外字段

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return CPackForServer.deserialize_base(deser)


class MoveHero(CPackForServer):
    """
    移动英雄 — typeID 182
    字段: path (vector<int3>), layer (EPathfindingLayer), hid (ObjectInstanceID), transit (bool)
    """
    type_id = 182

    def __init__(self, path: list, layer: int = 0, hid: int = 0,
                 transit: bool = False, player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.path = path      # list of int3 or (x, y, z) tuples
        self.layer = layer    # EPathfindingLayer
        self.hid = hid        # ObjectInstanceID (hero)
        self.transit = transit

    def serialize(self, ser):
        super().serialize(ser)
        # path: vector<int3>
        ser.write_int(len(self.path))
        for p in self.path:
            if isinstance(p, int3):
                p.serialize(ser)
            else:
                ser.write_int(p[0])
                ser.write_int(p[1])
                ser.write_int(p[2])
        # layer
        ser.write_int(self.layer)
        # hid
        ser.write_int(self.hid)
        # transit
        ser.write_bool(self.transit)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        # path
        length = deser.read_int()
        path = []
        for _ in range(length):
            path.append(int3.deserialize(deser))
        # layer
        layer = deser.read_int()
        # hid
        hid = deser.read_int()
        # transit
        transit = deser.read_bool()

        base["path"] = path
        base["layer"] = layer
        base["hid"] = hid
        base["transit"] = transit
        return base


class QueryReply(CPackForServer):
    """
    回复查询 — typeID 197
    字段: qid (QueryID), reply (optional<int32>)
    """
    type_id = 197

    def __init__(self, qid: int, reply: int = None,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.qid = qid
        self.reply = reply  # optional<int32>

    def serialize(self, ser):
        super().serialize(ser)
        # qid
        ser.write_int(self.qid)
        # reply: optional<int32>
        if self.reply is not None:
            ser.write_uint8(1)
            ser.write_int(self.reply)
        else:
            ser.write_uint8(0)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        # qid
        qid = deser.read_int()
        # reply
        present = deser.read_uint8()
        reply = deser.read_int() if present else None

        base["qid"] = qid
        base["reply"] = reply
        return base


class RecruitCreatures(CPackForServer):
    """
    招募生物 — typeID 187
    字段: tid (ObjectInstanceID), dst (ObjectInstanceID), crid (CreatureID string), amount (ui32), level (si32)
    """
    type_id = 187

    def __init__(self, tid: int, dst: int, crid: str, amount: int, level: int = 0,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.tid = tid
        self.dst = dst
        self.crid = crid
        self.amount = amount
        self.level = level

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)       # ObjectInstanceID
        ser.write_int(self.dst)       # ObjectInstanceID
        ser.write_string(self.crid)   # CreatureID → string
        ser.write_int(self.amount)    # ui32
        ser.write_int(self.level)     # si32

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        tid = deser.read_int()
        dst = deser.read_int()
        crid = deser.read_string()
        amount = deser.read_int()
        level = deser.read_int()

        base["tid"] = tid
        base["dst"] = dst
        base["crid"] = crid
        base["amount"] = amount
        base["level"] = level
        return base


class BuildStructure(CPackForServer):
    """
    建设 — typeID 185
    字段: tid (ObjectInstanceID), bid (BuildingID string)
    """
    type_id = 185

    def __init__(self, tid: int, bid: str,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.tid = tid
        self.bid = bid

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)       # ObjectInstanceID
        ser.write_string(self.bid)    # BuildingID → string

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        tid = deser.read_int()
        bid = deser.read_string()
        base["tid"] = tid
        base["bid"] = bid
        return base


class HireHero(CPackForServer):
    """
    雇佣英雄 — typeID 195
    字段: tid (ObjectInstanceID), cost (si32), bid (BuildingID string)
    """
    type_id = 195

    def __init__(self, tid: int, cost: int = -1, bid: str = "",
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.tid = tid
        self.cost = cost
        self.bid = bid

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_int(self.cost)
        ser.write_string(self.bid)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        tid = deser.read_int()
        cost = deser.read_int()
        bid = deser.read_string()
        base["tid"] = tid
        base["cost"] = cost
        base["bid"] = bid
        return base


class DismissHero(CPackForServer):
    """解散英雄 — typeID 181"""
    type_id = 181

    def __init__(self, tid: int, hid: int,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.tid = tid  # town ID
        self.hid = hid  # hero ID

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_int(self.hid)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        base["tid"] = deser.read_int()
        base["hid"] = deser.read_int()
        return base


class UpgradeCreature(CPackForServer):
    """升级生物 — typeID 188"""
    type_id = 188

    def __init__(self, tid: int, src: str, dst: str, amount: int = 1,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.tid = tid      # town ID
        self.src = src      # source creature ID (string)
        self.dst = dst      # destination creature ID (string)
        self.amount = amount

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_string(self.src)
        ser.write_string(self.dst)
        ser.write_int(self.amount)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        base["tid"] = deser.read_int()
        base["src"] = deser.read_string()
        base["dst"] = deser.read_string()
        base["amount"] = deser.read_int()
        return base


class SetFormation(CPackForServer):
    """设置阵型 — typeID 194"""
    type_id = 194

    def __init__(self, tid: int, formation: int,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.tid = tid
        self.formation = formation  # EArmyFormation enum

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_int(self.formation)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        base["tid"] = deser.read_int()
        base["formation"] = deser.read_int()
        return base


class CastAdvSpell(CPackForServer):
    """冒险地图施法 — typeID 200"""
    type_id = 200

    def __init__(self, target: int, spell: str, hero_id: int = 0,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.target = target  # ObjectInstanceID
        self.spell = spell    # SpellID (string)
        self.hero_id = hero_id

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.target)
        ser.write_string(self.spell)
        ser.write_int(self.hero_id)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        base["target"] = deser.read_int()
        base["spell"] = deser.read_string()
        base["hero_id"] = deser.read_int()
        return base


class GamePause(CPackForServer):
    """暂停游戏 — typeID 212"""
    type_id = 212

    def __init__(self, paused: bool = True,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.paused = paused

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_bool(self.paused)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        base["paused"] = deser.read_bool()
        return base


# ============================================================
# 战斗包 — BattleAction + MakeAction
# ============================================================

class BattleAction:
    """
    战斗动作 — 对应 C++ BattleAction
    字段: side (BattleSide), stackNumber (ui32), actionType (EActionType),
          spell (SpellID string), target (vector<DestinationInfo>)
    """
    def __init__(self, side: int = 0, stack_number: int = 0,
                 action_type: int = 0, spell: str = "", target: list = None):
        self.side = side                    # BattleSide
        self.stack_number = stack_number    # ui32
        self.action_type = action_type      # EActionType
        self.spell = spell                  # SpellID (string)
        self.target = target or []          # vector<DestinationInfo>

    def serialize(self, ser: BinarySerializer):
        ser.write_int(self.side)
        ser.write_int(self.stack_number)
        ser.write_int(self.action_type)
        ser.write_string(self.spell)
        # target: vector<DestinationInfo>
        ser.write_int(len(self.target))
        for t in self.target:
            if isinstance(t, DestinationInfo):
                t.serialize(ser)
            else:
                # (unit_value, hex_x, hex_y)
                ser.write_int(t[0])
                ser.write_int(t[1])
                ser.write_int(t[2])

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        side = deser.read_int()
        stack_number = deser.read_int()
        action_type = deser.read_int()
        spell = deser.read_string()
        # target
        target_len = deser.read_int()
        target = []
        for _ in range(target_len):
            target.append(DestinationInfo.deserialize(deser))

        return {
            "side": side,
            "stack_number": stack_number,
            "action_type": action_type,
            "spell": spell,
            "target": target,
        }


class MakeAction(CPackForServer):
    """
    战斗动作包 — typeID 198
    字段: action (BattleAction), bid (BattleID)
    """
    type_id = 198

    def __init__(self, action: BattleAction, bid: int,
                 player: int = PlayerColor.BLUE, request_id: int = 0):
        super().__init__(player, request_id)
        self.action = action
        self.bid = bid

    def serialize(self, ser):
        super().serialize(ser)
        self.action.serialize(ser)
        ser.write_int(self.bid)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForServer.deserialize_base(deser)
        base["action"] = BattleAction.deserialize(deser)
        base["bid"] = deser.read_int()
        return base


# ============================================================
# CPackForClient — 服务器→客户端包
# ============================================================
class CPackForClient:
    """CPackForClient 基类 — 所有服务器→客户端包"""

    type_id = 82

    def __init__(self, player: int = PlayerColor.BLUE):
        self.player = player

    def serialize(self, ser: BinarySerializer):
        ser.write_int(self.player)

    @staticmethod
    def deserialize_base(deser: BinaryDeserializer) -> dict:
        player = deser.read_int()
        return {"player": player}

    # 实机帧格式同 CPackForServer: isNull(1B) + pid(LVarInt) + tid(LVarInt) + 数据
    def serialize_full(self, ser: BinarySerializer):
        ser.write_bool(False)      # isNull = false
        ser.write_int(0)           # pid = 0
        ser.write_int(self.type_id)  # tid = LVarInt
        self.serialize(ser)

    def to_bytes(self) -> bytes:
        ser = BinarySerializer()
        self.serialize_full(ser)
        return ser.get_bytes()


class NewTurn(CPackForClient):
    """新回合 — typeID 116"""
    type_id = 116

    def __init__(self, turn: int = 0):
        super().__init__()
        self.turn = turn

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.turn)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["turn"] = deser.read_int()
        return base


class PackageApplied(CPackForClient):
    """包已应用 — typeID 84"""
    type_id = 84

    def __init__(self, request_id: int = 0, is_successful: bool = True):
        super().__init__()
        self.request_id = request_id
        self.is_successful = is_successful

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.request_id)
        ser.write_bool(self.is_successful)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["request_id"] = deser.read_int()
        base["is_successful"] = deser.read_bool()
        return base


class TryMoveHero(CPackForClient):
    """尝试移动英雄 — typeID 109"""
    type_id = 109

    def __init__(self, source: int = 0, destination: int = 0, reason: str = ""):
        super().__init__()
        self.source = source
        self.destination = destination
        self.reason = reason

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.source)
        ser.write_int(self.destination)
        ser.write_string(self.reason)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["source"] = deser.read_int()
        base["destination"] = deser.read_int()
        base["reason"] = deser.read_string()
        return base


class PlayerStartsTurn(CPackForClient):
    """
    玩家开始回合 (Query) — typeID 88
    C++ 结构 (PacksForClient.h): Query{queryID} + PlayerColor player
      serialize: h & queryID; h & player;
      queryID=-1 (INVALID) 表示无 timer query, 不应回复 QueryReply
      (fork 无回合计时器时 server 发 -1, 实测 6B 帧 = 顶层3B + qid(1B) + player(1B) + 1B? 以实机为准)
    """
    type_id = 88

    def __init__(self, player: int = 0, query_id: int = -1):
        super().__init__()
        self.player = player
        self.query_id = query_id

    def serialize(self, ser):
        ser.write_int(self.query_id)
        ser.write_int(self.player)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        # 覆写基类: 字段序 = queryID + player (非基类的 player 先行)
        query_id = deser.read_int()
        player = deser.read_int()
        return {"query_id": query_id, "player": player}


class PlayerEndsTurn(CPackForClient):
    """玩家结束回合 — typeID 102"""
    type_id = 102

    def serialize(self, ser):
        super().serialize(ser)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return CPackForClient.deserialize_base(deser)


class SystemMessage(CPackForClient):
    """系统消息 — typeID 85"""
    type_id = 85

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_string(self.message)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["message"] = deser.read_string()
        return base


class NewObject(CPackForClient):
    """新物体 — typeID 121"""
    type_id = 121

    def __init__(self, obj_id: int = 0):
        super().__init__()
        self.obj_id = obj_id

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.obj_id)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["obj_id"] = deser.read_int()
        return base


class GiveHero(CPackForClient):
    """给予英雄 — typeID 115"""
    type_id = 115

    def __init__(self, hero_id: int = 0):
        super().__init__()
        self.hero_id = hero_id

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.hero_id)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["hero_id"] = deser.read_int()
        return base


class ChangeObjPos(CPackForClient):
    """改变物体位置 — typeID 101"""
    type_id = 101

    def __init__(self, obj_id: int = 0, old_pos=None, new_pos=None):
        super().__init__()
        self.obj_id = obj_id
        self.old_pos = old_pos or int3(0, 0, 0)
        self.new_pos = new_pos or int3(0, 0, 0)

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.obj_id)
        self.old_pos.serialize(ser)
        self.new_pos.serialize(ser)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["obj_id"] = deser.read_int()
        base["old_pos"] = int3.deserialize(deser)
        base["new_pos"] = int3.deserialize(deser)
        return base


class SetAvailableHero(CPackForClient):
    """设置可用英雄 — typeID 99"""
    type_id = 99

    def __init__(self, tid: int = 0, heroes: list = None):
        super().__init__()
        self.tid = tid  # town ID
        self.heroes = heroes or []  # list of (hero_id, cost)

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_int(len(self.heroes))
        for h in self.heroes:
            ser.write_int(h[0])  # hero_id
            ser.write_int(h[1])  # cost

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["tid"] = deser.read_int()
        hero_count = deser.read_int()
        heroes = []
        for _ in range(hero_count):
            heroes.append((deser.read_int(), deser.read_int()))
        base["heroes"] = heroes
        return base


class SetAvailableCreatures(CPackForClient):
    """设置可用生物 — typeID 112"""
    type_id = 112

    def __init__(self, tid: int = 0, creatures: list = None):
        super().__init__()
        self.tid = tid  # town ID
        self.creatures = creatures or []  # list of (creature_id, amount, cost)

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_int(len(self.creatures))
        for c in self.creatures:
            ser.write_string(c[0])  # creature_id
            ser.write_int(c[1])     # amount
            ser.write_int(c[2])     # cost

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["tid"] = deser.read_int()
        count = deser.read_int()
        creatures = []
        for _ in range(count):
            creatures.append((deser.read_string(), deser.read_int(), deser.read_int()))
        base["creatures"] = creatures
        return base


# ============================================================
# 战斗客户端包
# ============================================================

class BattleStart(CPackForClient):
    """战斗开始 — typeID 132"""
    type_id = 132

    def __init__(self, bid: int = 0):
        super().__init__()
        self.bid = bid  # BattleID

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.bid)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["bid"] = deser.read_int()
        return base


class BattleResult(CPackForClient):
    """战斗结果 — typeID 135"""
    type_id = 135

    def __init__(self, bid: int = 0, winner: int = -1):
        super().__init__()
        self.bid = bid
        self.winner = winner  # BattleSide or -1 (no winner)

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.bid)
        ser.write_int(self.winner)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["bid"] = deser.read_int()
        base["winner"] = deser.read_int()
        return base


class BattleResultAccepted(CPackForClient):
    """战斗结果接受 — typeID 136"""
    type_id = 136

    def serialize(self, ser):
        super().serialize(ser)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return CPackForClient.deserialize_base(deser)


class BattleLogMessage(CPackForClient):
    """战斗日志 — typeID 138"""
    type_id = 138

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_string(self.message)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["message"] = deser.read_string()
        return base


# ============================================================
# 对话框包 (Query) — 客户端必须回复 QueryReply
# ============================================================

class HeroLevelUp(CPackForClient):
    """英雄升级 (Query) — typeID 154"""
    type_id = 154

    def __init__(self, hid: int = 0, level_ups: list = None):
        super().__init__()
        self.hid = hid
        self.level_ups = level_ups or []  # list of skill/spell IDs

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.hid)
        ser.write_int(len(self.level_ups))
        for l in self.level_ups:
            ser.write_int(l)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["hid"] = deser.read_int()
        count = deser.read_int()
        ups = []
        for _ in range(count):
            ups.append(deser.read_int())
        base["level_ups"] = ups
        return base


class BlockingDialog(CPackForClient):
    """阻塞对话框 (Query) — typeID 156"""
    type_id = 156

    def __init__(self, message: str = ""):
        super().__init__()
        self.message = message

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_string(self.message)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["message"] = deser.read_string()
        return base


class GarrisonDialog(CPackForClient):
    """城防对话框 (Query) — typeID 157"""
    type_id = 157

    def __init__(self, tid: int = 0, stacks: list = None):
        super().__init__()
        self.tid = tid
        self.stacks = stacks or []

    def serialize(self, ser):
        super().serialize(ser)
        ser.write_int(self.tid)
        ser.write_int(len(self.stacks))
        for s in self.stacks:
            ser.write_string(s[0])
            ser.write_int(s[1])

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        base = CPackForClient.deserialize_base(deser)
        base["tid"] = deser.read_int()
        count = deser.read_int()
        stacks = []
        for _ in range(count):
            stacks.append((deser.read_string(), deser.read_int()))
        base["stacks"] = stacks
        return base


# ============================================================
# 包注册表 — typeID → (class, is_server_pack)
# ============================================================

SERVER_PACKS = {
    180: EndTurn,
    181: DismissHero,
    182: MoveHero,
    185: BuildStructure,
    187: RecruitCreatures,
    188: UpgradeCreature,
    194: SetFormation,
    195: HireHero,
    197: QueryReply,
    198: MakeAction,
    200: CastAdvSpell,
    212: GamePause,
}

CLIENT_PACKS = {
    84: PackageApplied,
    85: SystemMessage,
    88: PlayerStartsTurn,
    101: ChangeObjPos,
    102: PlayerEndsTurn,
    109: TryMoveHero,
    112: SetAvailableCreatures,
    115: GiveHero,
    116: NewTurn,
    121: NewObject,
    132: BattleStart,
    135: BattleResult,
    136: BattleResultAccepted,
    138: BattleLogMessage,
    154: HeroLevelUp,
    156: BlockingDialog,
    157: GarrisonDialog,
    99: SetAvailableHero,
}


# ============================================================
# Lobby 包 — P8/T13.10 前置
# 来源: vcmi/lib/networkPacks/PacksForLobby.h + serializer/RegisterTypes.h
# ============================================================

class CPackForLobby:
    """CPackForLobby 基类 — 无额外字段"""
    type_id = 213

    def serialize(self, ser):
        pass

    # 实机帧格式同上: isNull(1B) + pid(LVarInt) + tid(LVarInt) + 数据
    def serialize_full(self, ser: BinarySerializer):
        ser.write_bool(False)      # isNull = false
        ser.write_int(0)           # pid = 0
        ser.write_int(self.type_id)  # tid = LVarInt
        self.serialize(ser)

    def to_bytes(self) -> bytes:
        ser = BinarySerializer()
        self.serialize_full(ser)
        return ser.get_bytes()


class LobbyClientConnected(CPackForLobby):
    """
    客户端连接通知 — typeID 216
    字段: uuid, names, mode, clientId, hostClientId, version
    """
    type_id = 216

    def __init__(self, uuid: str = "", names=None, mode: int = 0,
                 client_id: int = -1, host_client_id: int = -1, version: int = 905):
        self.uuid = uuid
        self.names = names or ["Hermes AI"]
        self.mode = mode          # EStartMode: NEW_GAME=0
        self.client_id = client_id      # GameConnectionID::INVALID=-1 (server 回填)
        self.host_client_id = host_client_id  # 同上
        self.version = version    # ESerializationVersion::CURRENT = CONTROL_LOSS_TRACKING = 905

    def serialize(self, ser):
        ser.write_string(self.uuid)
        ser.write_int(len(self.names))
        for n in self.names:
            ser.write_string(n)
        ser.write_int(self.mode)
        ser.write_int(self.client_id)
        ser.write_int(self.host_client_id)
        # version = ESerializationVersion 枚举 — C++ save(Version) 是 raw int32 (非 LVarInt)
        # 0911 实机对拍: 官方 client 发 89 03 00 00 = raw int32 905 (CONTROL_LOSS_TRACKING)
        ser.write_int32_raw(self.version)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        out = {}
        out["uuid"] = deser.read_string()
        count = deser.read_int()
        out["names"] = [deser.read_string() for _ in range(count)]
        out["mode"] = deser.read_int()
        out["client_id"] = deser.read_int()
        out["host_client_id"] = deser.read_int()
        out["version"] = deser.read_int32_raw()  # raw int32, 非 LVarInt
        return out


class LobbyQueryState(CPackForLobby):
    """查询大厅状态 — typeID 265, 无字段"""
    type_id = 265

    def serialize(self, ser):
        pass

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return {}


class _CModVersion:
    @staticmethod
    def read(deser):
        return {"major": deser.read_int(), "minor": deser.read_int(), "patch": deser.read_int()}

    @staticmethod
    def write(ser, v):
        ser.write_int(v.get("major", -1))
        ser.write_int(v.get("minor", -1))
        ser.write_int(v.get("patch", -1))


class _ModVerificationInfo:
    @staticmethod
    def read(deser):
        return {
            "name": deser.read_string(),
            "version": _CModVersion.read(deser),
            "checksum": deser.read_int(),
            "parent": deser.read_string(),
            "impactsGameplay": deser.read_bool(),
        }


class LobbyModsCheck(CPackForLobby):
    """大厅兼容检查响应 — typeID 266"""
    type_id = 266

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        out = {"vcmiVersion": deser.read_string()}
        mod_count = deser.read_int()
        mods = {}
        for _ in range(mod_count):
            info = _ModVerificationInfo.read(deser)
            mods[info["name"]] = info
        out["mods"] = mods
        out["hostAccountDisplayName"] = deser.read_string()
        part_count = deser.read_int()
        out["participantNames"] = [deser.read_string() for _ in range(part_count)]
        return out


class _PlayerSettings:
    @staticmethod
    def read(deser):
        return {
            "castle": deser.read_string(),
            "hero": deser.read_string(),
            "heroPortrait": deser.read_string(),
            "heroNameTextId": deser.read_string(),
            "bonus": deser.read_int(),
            "color": deser.read_int(),
            "handicap": {
                "startBonus": [deser.read_int() for _ in range(7)],
                "percentIncome": deser.read_int(),
                "percentGrowth": deser.read_int(),
            },
            "name": deser.read_string(),
            "connectedPlayerIDs": deser.read_set(lambda: deser.read_int()),
            "compOnly": deser.read_bool(),
        }


class _StartInfo:
    # fork StartInfo::serialize 实际字段序 (StartInfo.h):
    # mode, difficulty, playerInfos(map), startTime, fileURI, simturnsInfo, turnTimerInfo,
    # extraOptionsInfo, mapname, mapGenOptions(ptr), campState(ptr), ML mlconfig
    # 0911 实机对拍 LobbyUpdateState 字节流校准
    @staticmethod
    def read(deser):
        si = {}
        si["mode"] = deser.read_int()
        si["difficulty"] = deser.read_uint8()
        player_count = deser.read_int()
        player_infos = {}
        for _ in range(player_count):
            color = deser.read_int()
            player_infos[color] = _PlayerSettings.read(deser)
        si["playerInfos"] = player_infos
        si["startTime"] = deser.read_int()
        si["fileURI"] = deser.read_string()
        si["simturnsInfo"] = {
            "requiredTurns": deser.read_int(),
            "optionalTurns": deser.read_int(),
            "allowHumanWithAI": deser.read_bool(),
            "ignoreAlliedContacts": deser.read_bool(),
        }
        si["turnTimerInfo"] = {
            "minTurnTime": deser.read_int(),
            "maxTurnTime": deser.read_int(),
            "startWithMaxTurnTime": deser.read_bool(),
        }
        si["extraOptionsInfo"] = {}  # TODO: 实机抓包校准
        si["mapname"] = deser.read_string()
        has_mgo = deser.read_bool()
        si["hasMapGenOptions"] = has_mgo
        if has_mgo:
            deser.read_int()
            deser.read_uint16()
        has_camp = deser.read_bool()
        si["hasCampState"] = has_camp
        if has_camp:
            deser.read_int()
            deser.read_uint16()
        return si


class _LobbyState:
    @staticmethod
    def read(deser):
        si = deser.read_pointer(lambda: _StartInfo.read(deser))
        mi_present = deser.read_pointer_present()
        mi = None
        if mi_present:
            deser.read_int()
            deser.read_uint16()
            mi = {"_unknown": "CMapInfo"}
        player_count = deser.read_int()
        player_names = {}
        for _ in range(player_count):
            pid = deser.read_int()
            player_names[pid] = {"connection": deser.read_int(), "name": deser.read_string()}
        return {
            "si": si,
            "mi": mi,
            "playerNames": player_names,
            "hostClientId": deser.read_int(),
            "campaignMap": deser.read_int(),   # CampaignScenarioID enum → LVarInt (非 string)
            "campaignBonus": deser.read_int(),
        }


class LobbyUpdateState(CPackForLobby):
    """大厅状态更新 — typeID 226"""
    type_id = 226

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return {
            "state": _LobbyState.read(deser),
            "refreshList": deser.read_bool(),
        }


class LobbyClientDisconnected(CPackForLobby):
    type_id = 217

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return {"client_id": deser.read_int(), "shutdownServer": deser.read_bool()}


class LobbyChatMessage(CPackForLobby):
    type_id = 218

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return {"playerName": deser.read_string(), "message": deser.read_string()}


class LobbySetMap(CPackForLobby):
    type_id = 229

    def __init__(self, map_name: str = ""):
        self.map_name = map_name

    def serialize(self, ser):
        # 最简占位: mapInfo=null, mapGenOptions=null
        ser.write_bool(False)
        ser.write_bool(False)

    @staticmethod
    def deserialize(deser: BinaryDeserializer) -> dict:
        return {"hasMapInfo": deser.read_pointer_present(), "hasMapGenOptions": deser.read_pointer_present()}


LOBBY_PACKS = {
    216: LobbyClientConnected,
    217: LobbyClientDisconnected,
    218: LobbyChatMessage,
    226: LobbyUpdateState,
    265: LobbyQueryState,
    266: LobbyModsCheck,
    229: LobbySetMap,
}
