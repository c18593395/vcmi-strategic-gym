"""
strategic_reader.py — Python ctypes 直读 libmlclient.so 中的 StrategicState 全局指针
用法:
    from strategic_reader import StrategicReader
    reader = StrategicReader()
    state = reader.read()   # 返回 dict，每次调用读最新状态
"""
import ctypes
import os
from typing import Dict, List, Optional

MAX_HEROES = 8
MAX_TOWNS = 8
MAX_PLAYERS = 8
MAX_MINES = 64   # A+B: 矿场最大数量 (与 C 头 strategic_state.h 一致)

# OBS schema v3 常量（与 C 头 strategic_state.h 一致）
LOCAL_WIN = 15     # local_tiles 窗口边长
LOCAL_CH = 3       # v3: 通道数 (0=可通行性 1=对象类型 2=守卫战力)
GLOBAL_GRID = 32   # global_explored 网格边长
MAX_LEVELS = 2     # 地图层数 (地上/地下)
NAV_SIZE = 32
TARGET_LIST = 8    # 目标槽数
TARGET_DIM = 8     # 每目标维度
ENEMY_THREAT = 7
BATTLE_PRED = 4
EVENTS_SIZE = 4
RESERVED_SIZE = 134
GRID_SIZE = 21
GRID_CHANNELS = 4
GRID_TOTAL = GRID_SIZE * GRID_SIZE * GRID_CHANNELS  # 1764

class StrategicHero(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int32),
        ("owner", ctypes.c_int32),
        ("pos_x", ctypes.c_int32), ("pos_y", ctypes.c_int32), ("pos_z", ctypes.c_int32),
        ("movement", ctypes.c_int32), ("max_movement", ctypes.c_int32),
        ("level", ctypes.c_int32),
        ("attack", ctypes.c_int32), ("defense", ctypes.c_int32),
        ("power", ctypes.c_int32), ("knowledge", ctypes.c_int32),
        ("mana", ctypes.c_int32), ("max_mana", ctypes.c_int32),
        ("exp", ctypes.c_int32),
        ("army_count", ctypes.c_int32 * 7), ("army_type", ctypes.c_int32 * 7),
        ("in_battle", ctypes.c_int32),
        ("name", ctypes.c_char * 32),
        # --- v3 扩展 ---
        ("total_power", ctypes.c_int32),   # 该英雄总战力 (army × AIValue)
        ("is_garrisoned", ctypes.c_int32), # 0=野外 1=驻守
        ("has_commander", ctypes.c_int32), # 0=无 1=有指挥官
    ]

class StrategicTown(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int32), ("owner", ctypes.c_int32),
        ("pos_x", ctypes.c_int32), ("pos_y", ctypes.c_int32), ("pos_z", ctypes.c_int32),
        ("buildings", ctypes.c_int32),
        ("garrison", ctypes.c_int32 * 7),
        ("gold_income", ctypes.c_int32),
        ("name", ctypes.c_char * 32),
        # --- v3 扩展 ---
        ("recruit_mask_lo", ctypes.c_int32),  # 可招募兵种 bitmask 低16位
        ("recruit_mask_hi", ctypes.c_int32),  # 可招募兵种 bitmask 高16位
        ("build_mask_lo", ctypes.c_int32),    # 可建建筑 bitmask 低16位
        ("build_mask_hi", ctypes.c_int32),    # 可建建筑 bitmask 高16位
    ]

class StrategicPlayer(ctypes.Structure):
    _fields_ = [
        ("color", ctypes.c_int32), ("human", ctypes.c_int32),
        ("gold", ctypes.c_int32),
        ("wood", ctypes.c_int32), ("mercury", ctypes.c_int32),
        ("ore", ctypes.c_int32), ("sulfur", ctypes.c_int32),
        ("crystal", ctypes.c_int32), ("gems", ctypes.c_int32),
        ("hero_count", ctypes.c_int32), ("town_count", ctypes.c_int32),
        ("alive", ctypes.c_int32),
        # --- v3 扩展 ---
        ("total_power", ctypes.c_int32),   # 该玩家总战力
        ("weekly_income", ctypes.c_int32), # 金币周收入
        ("relation_to_me", ctypes.c_int32) # 0=中立 1=敌对 2=结盟
    ]

class StrategicMine(ctypes.Structure):
    """A+B: 矿场 (与 C 头 strategic_state.h 的 StrategicMine 一致)"""
    _fields_ = [
        ("id", ctypes.c_int32),
        ("type", ctypes.c_int32),
        ("owner", ctypes.c_int32),
        ("pos_x", ctypes.c_int32), ("pos_y", ctypes.c_int32), ("pos_z", ctypes.c_int32),
    ]

class StrategicState(ctypes.Structure):
    _fields_ = [
        ("day", ctypes.c_int32), ("week", ctypes.c_int32), ("month", ctypes.c_int32),
        ("current_player", ctypes.c_int32),
        ("map_width", ctypes.c_int32), ("map_height", ctypes.c_int32),
        ("has_underground", ctypes.c_int32),
        ("player_count", ctypes.c_int32),
        ("players", StrategicPlayer * MAX_PLAYERS),
        ("heroes", StrategicHero * MAX_HEROES),
        ("towns", StrategicTown * MAX_TOWNS),
        ("game_over", ctypes.c_int32),
        ("action", ctypes.c_int32),
        ("_version", ctypes.c_int32),
        ("passable", ctypes.c_int32 * 8),
        # --- OBS schema v3: 态势感知 + H 扩展 (与 C 头完全一致) ---
        # ctypes 左结合: 最右乘数=最外层, 与 C 声明 [ch][y][x] / [z][gy][gx] 对齐
        ("active_hero", ctypes.c_int32),
        ("local_tiles", ctypes.c_int8 * LOCAL_WIN * LOCAL_WIN * LOCAL_CH),
        ("global_explored", ctypes.c_int8 * GLOBAL_GRID * GLOBAL_GRID * MAX_LEVELS),
        # --- A+B: 事件奖励扩展 (StrategicState 末尾追加, 与 C 头一致) ---
        # 注意: 以下字段只用于奖励计算, 不进 obs
        ("mine_count", ctypes.c_int32),
        ("mines", StrategicMine * MAX_MINES),
        ("battle_result", ctypes.c_int32),   # 0=无 1=red赢 2=red输 3=平局
        # --- H 扩展 (v3): obs 3456 ---
        ("nav", ctypes.c_int32 * NAV_SIZE),
        ("target_list", ctypes.c_int32 * TARGET_LIST * TARGET_DIM),
        ("enemy_threat", ctypes.c_int32 * ENEMY_THREAT),
        ("battle_pred", ctypes.c_int32 * BATTLE_PRED),
        ("events", ctypes.c_int32 * EVENTS_SIZE),
        ("reserved", ctypes.c_int32 * RESERVED_SIZE),
        ("terrain_grid", ctypes.c_uint8 * GRID_TOTAL),
    ]

class StrategicReader:
    def __init__(self, lib_path: str = None):
        if lib_path is None:
            lib_path = os.path.join(
                os.path.dirname(__file__),
                "vcmi/rel/bin/libmlclient.so"
            )
        self.lib = ctypes.CDLL(lib_path)
        # g_strategic_state 是 extern "C" 全局变量
        self._ptr = ctypes.c_void_p.in_dll(self.lib, "g_strategic_state")

    def read(self) -> Optional[Dict]:
        """读取当前游戏状态，返回 dict 或 None"""
        addr = self._ptr.value
        if not addr:
            return None
        state = StrategicState.from_address(addr)

        # hero_count 需要从 heroes 数组统计
        hero_list = []
        for i in range(MAX_HEROES):
            h = state.heroes[i]
            if h.id == -1 or h.id == 0:
                break
            hero_list.append({
                "id": h.id, "owner": h.owner,
                "pos": (h.pos_x, h.pos_y, h.pos_z),
                "movement": h.movement, "max_movement": h.max_movement,
                "level": h.level,
                "attack": h.attack, "defense": h.defense,
                "power": h.power, "knowledge": h.knowledge,
                "mana": h.mana,
                "army": list(h.army_count),
                "name": h.name.decode().rstrip("\x00"),
                "in_battle": bool(h.in_battle),
            })

        town_list = []
        for i in range(MAX_TOWNS):
            t = state.towns[i]
            if t.id == 0:
                break
            town_list.append({
                "id": t.id, "owner": t.owner,
                "pos": (t.pos_x, t.pos_y, t.pos_z),
                "buildings": t.buildings,
                "garrison": list(t.garrison),
                "gold_income": t.gold_income,
                "name": t.name.decode().rstrip("\x00"),
            })

        player_list = []
        for i in range(state.player_count):
            p = state.players[i]
            player_list.append({
                "color": p.color, "human": bool(p.human), "alive": bool(p.alive),
                "gold": p.gold, "wood": p.wood, "mercury": p.mercury,
                "ore": p.ore, "sulfur": p.sulfur, "crystal": p.crystal, "gems": p.gems,
                "heroes": [h for h in hero_list if h["owner"] == p.color],
                "towns": [t for t in town_list if t["owner"] == p.color],
            })

        # A+B: 矿场列表 (只用于奖励/调试, 不进 obs)
        mine_list = []
        for i in range(state.mine_count):
            m = state.mines[i]
            mine_list.append({
                "id": m.id, "type": m.type, "owner": m.owner,
                "pos": (m.pos_x, m.pos_y, m.pos_z),
            })

        return {
            "day": state.day, "week": state.week, "month": state.month,
            "current_player": state.current_player,
            "map": (state.map_width, state.map_height, state.has_underground),
            "players": player_list,
            "heroes": hero_list,
            "towns": town_list,
            "mines": mine_list,
            "battle_result": state.battle_result,
            "game_over": state.game_over,
            "active_hero": state.active_hero,
        }
