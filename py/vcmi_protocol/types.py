"""
T13 — VCMI 类型定义 (对应 C++ 源码中的枚举/标识符类型)
"""

# ============================================================
# PlayerColor — 玩家颜色 (StaticIdentifier)
# ============================================================
class PlayerColor:
    NEUTRAL = 0
    BLUE = 1
    GREEN = 2
    RED = 3
    TEAL = 4
    ORANGE = 5
    PURPLE = 6
    PINK = 7
    GRAY = 8


# ============================================================
# ObjectInstanceID — 物体实例 ID (StaticIdentifier)
# ============================================================
class ObjectInstanceID:
    NONE = 0
    INVALID = -1


# ============================================================
# QueryID — 查询 ID (StaticIdentifier)
# ============================================================
class QueryID:
    INVALID = -1


# ============================================================
# BattleID — 战斗 ID (StaticIdentifier)
# ============================================================
class BattleID:
    INVALID = -1


# ============================================================
# EPathfindingLayer — 寻路层 (enum)
# ============================================================
class EPathfindingLayer:
    LayerMain = 0
    LayerFort = 1


# ============================================================
# BattleSide — 战斗阵营 (enum)
# ============================================================
class BattleSide:
    LEFT = 0
    RIGHT = 1


# ============================================================
# EActionType — 战斗动作类型 (enum)
# ============================================================
class EActionType:
    WAIT = 0
    MOVE = 1
    SPELLCAST = 2
    UNIT_SPELLCAST = 3
    MELEE_ATTACK = 4
    SHOT_ATTACK = 5
    HEAL = 6
    DEFEND = 7
    WALK_AND_CAST = 8
    END_OF_TACTICS = 9
    RETREAT = 10
    SURRENDER = 11


# ============================================================
# BattleHex — 战斗格子 (int x, y)
# ============================================================
class BattleHex:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

    def serialize(self, ser):
        ser.write_int(self.x)
        ser.write_int(self.y)

    @staticmethod
    def deserialize(deser):
        x = deser.read_int()
        y = deser.read_int()
        return BattleHex(x, y)


# ============================================================
# int3 — 地图坐标 (三个 int32)
# ============================================================
class int3:
    def __init__(self, x: int = 0, y: int = 0, z: int = 0):
        self.x = x
        self.y = y
        self.z = z

    def serialize(self, ser):
        ser.write_int(self.x)
        ser.write_int(self.y)
        ser.write_int(self.z)

    @staticmethod
    def deserialize(deser):
        x = deser.read_int()
        y = deser.read_int()
        z = deser.read_int()
        return int3(x, y, z)

    def __eq__(self, other):
        if isinstance(other, int3):
            return self.x == other.x and self.y == other.y and self.z == other.z
        if isinstance(other, tuple) and len(other) == 3:
            return self.x == other[0] and self.y == other[1] and self.z == other[2]
        return False

    def __repr__(self):
        return f"int3({self.x}, {self.y}, {self.z})"


# ============================================================
# DestinationInfo — 战斗目标信息
# ============================================================
class DestinationInfo:
    def __init__(self, unit_value: int = -1, hex_value=None):
        self.unit_value = unit_value
        self.hex_value = hex_value  # BattleHex or None

    def serialize(self, ser):
        ser.write_int(self.unit_value)
        if self.hex_value:
            self.hex_value.serialize(ser)
        else:
            ser.write_int(0)
            ser.write_int(0)

    @staticmethod
    def deserialize(deser):
        unit_value = deser.read_int()
        hex_x = deser.read_int()
        hex_y = deser.read_int()
        return DestinationInfo(unit_value, BattleHex(hex_x, hex_y))
