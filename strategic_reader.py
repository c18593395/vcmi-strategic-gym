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
    ]

class StrategicTown(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int32), ("owner", ctypes.c_int32),
        ("pos_x", ctypes.c_int32), ("pos_y", ctypes.c_int32), ("pos_z", ctypes.c_int32),
        ("buildings", ctypes.c_int32),
        ("garrison", ctypes.c_int32 * 7),
        ("gold_income", ctypes.c_int32),
        ("name", ctypes.c_char * 32),
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
        ("_version", ctypes.c_int32),
        ("passable", ctypes.c_int32 * 8),
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

        return {
            "day": state.day, "week": state.week, "month": state.month,
            "current_player": state.current_player,
            "map": (state.map_width, state.map_height, state.has_underground),
            "players": player_list,
            "heroes": hero_list,
            "towns": town_list,
            "game_over": state.game_over,
        }
