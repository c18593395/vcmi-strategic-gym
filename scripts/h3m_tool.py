#!/usr/bin/env python3
"""H3M 解析 + 修改工具 (2026-08-23)
逆向 VCMI MapFormatH3M.cpp readHeader 系列 + 对象表 (readObjectTemplates/readObjects)。
用法:
  python h3m_tool.py scan <file.h3m>          # 解析结构, 输出 terrain 偏移等信息
  python h3m_tool.py terrain <in.h3m> <out.h3m> <edits.json>  # 改 terrain 字节
  python h3m_tool.py objects <file.h3m>       # 解析对象表 (位置/类型/owner)
edits.json: {"water": [[x1,y1],[x2,y2],...], "rock": [...], "grass": [...], "rect_water": [x0,y0,x1,y1], ...}
terrain 字节: 0=dirt 1=sand 2=grass 3=snow 4=swamp 5=rough 6=subterra 7=lava 8=water 9=rock
"""
import gzip, struct, sys, json

ROE, AB, SOD, CHR, WOG, HOTA = 0x0e, 0x15, 0x1c, 0x1d, 0x33, 0x20

TERRAIN_NAMES = {0:"dirt",1:"sand",2:"grass",3:"snow",4:"swamp",5:"rough",6:"subterra",7:"lava",8:"water",9:"rock"}

class R:
    """字节读取器 (gzip 解压后的 raw)"""
    def __init__(self, raw):
        self.raw = raw
        self.pos = 0
        self.log = []
        self.safe = False  # True 时越界返回 0 (容错解析用)
    def _b(self, n):
        if self.pos + n <= len(self.raw):
            v = self.raw[self.pos:self.pos+n]
            self.pos += n
            return v
        if self.safe:
            self.pos = len(self.raw)
            return b'\x00' * n
        raise IndexError(f"读取越界 @{self.pos} (需要 {n}B)")
    def u8(self):
        if self.pos < len(self.raw):
            v = self.raw[self.pos]; self.pos += 1; return v
        if self.safe:
            self.pos = len(self.raw)
            return 0
        raise IndexError(f"读取越界 @{self.pos}")
    def i8(self):
        v = self.u8()
        return v - 256 if v >= 128 else v
    def u16(self):
        return struct.unpack_from('<H', self._b(2), 0)[0]
    def u32(self):
        return struct.unpack_from('<I', self._b(4), 0)[0]
    def i32(self):
        return struct.unpack_from('<i', self._b(4), 0)[0]
    def skip(self, n):
        if self.pos + n <= len(self.raw):
            self.pos += n
        elif self.safe:
            self.pos = len(self.raw)
        else:
            raise IndexError(f"跳过越界 @{self.pos} (+{n})")
    def sstr(self):
        """readBaseString: u32 len + bytes"""
        l = self.u32()
        if self.pos + l <= len(self.raw):
            s = self.raw[self.pos:self.pos+l]; self.pos += l
            return s
        if self.safe:
            self.pos = len(self.raw)
            return b''
        raise IndexError(f"字符串越界 @{self.pos} (len={l})")
    def lstr(self):
        return self.sstr()
    def int3(self):
        x = self.u8(); y = self.u8(); z = self.u8()
        return (x, y, z)

def parse_header(path):
    with open(path, 'rb') as f:
        raw = gzip.decompress(f.read())
    r = R(raw)
    n = len(raw)
    info = {'path': path, 'size': n}

    ver = r.u32()
    info['version'] = ver
    levelAB = ver in (AB, SOD, CHR, WOG, HOTA)
    levelSOD = ver in (SOD, CHR, WOG, HOTA)

    if ver == HOTA:
        hota_version = r.u32()
        info['hota_version'] = hota_version
        if hota_version >= 8:
            r.u32(); r.u32(); r.u32()
        if hota_version >= 1:
            r.u8(); r.u8()
        if hota_version >= 2:
            r.u32()
        if hota_version >= 5:
            r.u32(); r.u8()
        if hota_version >= 7:
            r.u8()
        if hota_version >= 8:
            r.u8()
        if hota_version >= 9:
            r.i32()

    info['are_any_players'] = r.u8()
    info['size'] = r.u32()  # width=height
    w = info['size']
    info['has_underground'] = r.u8()
    info['name'] = r.lstr().decode('utf-8', 'replace')
    info['description'] = r.lstr().decode('utf-8', 'replace')
    info['difficulty'] = r.u8()
    if levelAB:
        info['level_limit'] = r.u8()

    # players
    inactive_skip = 6 + (6 if levelAB else 0) + (1 if levelSOD else 0)
    factions_bytes = 1 if ver == ROE else (4 if ver == HOTA else 2)
    players = []
    for i in range(8):
        can_h = r.u8(); can_c = r.u8()
        if not (can_h or can_c):
            r.skip(inactive_skip)
            continue
        p = {'idx': i, 'human': bool(can_h), 'ai': bool(can_c)}
        r.u8()  # aiTactic
        if levelSOD:
            r.skip(1)
        r.skip(factions_bytes)
        r.u8()  # isFactionRandom
        has_main_town = r.u8()
        if has_main_town:
            if levelAB:
                r.u8(); r.skip(1)
            p['main_town'] = r.int3()
        has_random_hero = r.u8()
        main_hero = r.u8()  # readHero 1B
        if main_hero != 0xff:
            r.u8()  # portrait
            r.lstr()  # name
        if levelAB:
            r.skip(1)
            hero_count = r.u32()
            for _ in range(hero_count):
                r.u8()  # heroId
                r.lstr()  # heroName
        players.append(p)
    info['players'] = players

    # victory conditions (EVictoryConditionType: WINSTANDARD=-1, ARTIFACT=0, GATHERTROOP=1, ...)
    vic = r.i8()
    info['victory'] = vic
    if vic != -1:
        r.u8()  # allowNormalVictory
        r.u8()  # appliesToAI
        if vic == 0:      # ARTIFACT (readArtifact: ROE=u8, AB+=u16)
            r.skip(1 if ver == ROE else 2)
        elif vic == 1:    # GATHERTROOP (readCreature: ROE=u8, AB+=u16)
            r.skip(1 if ver == ROE else 2); r.i32()
        elif vic == 2:    # GATHERRESOURCE
            r.u8(); r.i32()
        elif vic == 3:    # BUILDCITY
            r.int3(); r.u8(); r.u8()
        elif vic == 4:    # BUILDGRAIL
            r.int3()
        elif vic == 5:    # BEATHERO
            r.int3()
        elif vic == 6:    # CAPTURECITY
            r.int3()
        elif vic == 7:    # BEATMONSTER
            r.int3()
        elif vic == 8:    # TAKEDWELLINGS
            pass
        elif vic == 9:    # TAKEMINES
            pass
        elif vic == 10:   # TRANSPORTITEM (readArtifact8 固定 u8)
            r.u8(); r.int3()
        elif vic == 11:   # HOTA_ELIMINATE_ALL_MONSTERS
            pass
        elif vic == 12:   # HOTA_SURVIVE_FOR_DAYS
            r.u32()
        else:
            raise ValueError(f"未知 victory 条件 {vic} @{r.pos}")

    # loss conditions (ELossConditionType: LOSSSTANDARD=-1, LOSSCASTLE=0, LOSSHERO=1, TIMEEXPIRES=2)
    loss = r.i8()
    info['loss'] = loss
    if loss != -1:
        if loss == 0:    # LOSSCASTLE
            r.int3()
        elif loss == 1:  # LOSSHERO
            r.int3()
        elif loss == 2:  # TIMEEXPIRES
            r.u16()
        else:
            raise ValueError(f"未知 loss 条件 {loss} @{r.pos}")

    # team info
    teams = r.u8()
    info['teams'] = teams
    if teams > 0:
        r.skip(8)

    # allowed heroes (ROE=16, AB/SOD=20 字节 bitmask)
    if ver == HOTA:
        pass  # sized variant — 暂不支持, HOTA 模板不用
    else:
        r.skip(16 if ver == ROE else 20)
    if levelAB:
        placeholders = r.u32()
        r.skip(placeholders)  # readHero 1B each

    # disposed heroes (SOD)
    if levelSOD:
        disp = r.u8()
        for _ in range(disp):
            r.u8()       # heroId
            r.u8()       # portrait
            r.lstr()     # name
            r.skip(1)    # players bitmask

    # map options: skipZero(31)
    r.skip(31)
    if ver == HOTA:
        raise ValueError("HOTA map options 暂不支持")

    # allowed artifacts: ROE 不读 (if(levelAB) 才读), AB=17, SOD=18 字节
    if ver == ROE:
        pass
    elif levelAB and not levelSOD:
        r.skip(17)
    elif levelSOD:
        r.skip(18)
    # allowed spells (SOD: spellsBytes=9) + skills (skillsBytes=4)
    if levelSOD:
        r.skip(9)
        r.skip(4)

    # rumors
    rumors = r.u32()
    for _ in range(rumors):
        r.lstr()  # name
        r.lstr()  # text

    # predefined heroes (SOD: heroesCount=156)
    if levelSOD:
        for hero_id in range(156):
            custom = r.u8()
            if not custom:
                continue
            raise ValueError(f"自定义英雄 {hero_id} @{r.pos} 暂不支持")

    info['terrain_offset'] = r.pos
    info['terrain_bytes'] = w * w * 7 * (2 if info['has_underground'] else 1)
    info['terrain_end'] = r.pos + info['terrain_bytes']
    return info

# ── 对象表 (readObjectTemplates + readObjects) ────────────────────────────────
# 逆向 vcmi/lib/mapping/MapFormatH3M.cpp (2026-08-23)
# 对象类型数字 = VCMI Obj 枚举 (H3M 原始 id == remapped id, gdb 实测校准)
# 实测 Twins(AB)+For Sale(SOD): RANDOM_HERO=70 TOWN=77 MINE=53 RESOURCE=79
# RANDOM_RESOURCE=76 TREASURE_CHEST=101 ARTIFACT=5 EVENT=26 CAMPFIRE=12 ...
# 参考 MapObjectBaseID::Type 完整枚举 (gdb ptype libvcmi.so)

OBJ_NAMES = {
    5: 'ARTIFACT', 6: 'PANDORAS_BOX', 7: 'BLACK_MARKET',
    9: 'BORDERGUARD', 12: 'CAMPFIRE',
    16: 'CREATURE_BANK', 17: 'CREATURE_GENERATOR1', 18: 'CREATURE_GENERATOR2',
    19: 'CREATURE_GENERATOR3', 20: 'CREATURE_GENERATOR4',
    24: 'DERELICT_SHIP', 25: 'DRAGON_UTOPIA', 26: 'EVENT', 29: 'FLOTSAM',
    33: 'GARRISON', 36: 'GRAIL', 39: 'LEAN_TO',
    53: 'MINE', 54: 'RANDOM_MONSTER', 58: 'OCEAN_BOTTLE', 61: 'PRISON',
    62: 'HERO',
    65: 'RANDOM_ART', 66: 'RANDOM_TREASURE_ART', 67: 'RANDOM_MINOR_ART',
    68: 'RANDOM_MAJOR_ART', 69: 'RANDOM_RELIC_ART', 70: 'RANDOM_HERO',
    72: 'RANDOM_MONSTER_L1', 73: 'RANDOM_MONSTER_L2',
    74: 'RANDOM_MONSTER_L3', 75: 'RANDOM_MONSTER_L4', 76: 'RANDOM_RESOURCE',
    77: 'RANDOM_TOWN', 79: 'RESOURCE', 81: 'SCHOLAR', 82: 'SEA_CHEST',
    83: 'SEER_HUT', 84: 'CRYPT', 85: 'SHIPWRECK', 86: 'SHIPWRECK_SURVIVOR',
    87: 'SHIPYARD', 88: 'SHRINE_OF_MAGIC_INCANTATION',
    89: 'SHRINE_OF_MAGIC_GESTURE', 90: 'SHRINE_OF_MAGIC_THOUGHT',
    91: 'SIGN', 93: 'SPELL_SCROLL', 98: 'TOWN', 101: 'TREASURE_CHEST',
    102: 'TREE_OF_KNOWLEDGE', 104: 'UNIVERSITY', 105: 'WAGON',
    108: 'WARRIORS_TOMB', 113: 'WITCH_HUT',
    162: 'RANDOM_MONSTER_L6', 163: 'RANDOM_MONSTER_L7',
    212: 'BORDER_GATE', 214: 'HERO_PLACEHOLDER', 215: 'QUEST_GUARD',
    216: 'RANDOM_DWELLING', 217: 'RANDOM_DWELLING_LVL',
    218: 'RANDOM_DWELLING_FACTION', 219: 'GARRISON2',
}

def _features(ver, hota_version=0):
    """MapFormatFeaturesH3M 关键值 (MapFeaturesH3M.cpp)"""
    f = dict(
        levelAB=ver in (AB, SOD, CHR, WOG, HOTA), levelSOD=ver in (SOD, CHR, WOG, HOTA),
        levelHOTA3=hota_version > 2, levelHOTA5=hota_version > 4,
        levelHOTA6=hota_version > 5, levelHOTA7=hota_version > 6,
        levelHOTA9=hota_version > 8,
        factionsBytes=1 if ver == ROE else (4 if ver == HOTA else 2),
        heroesBytes=16 if ver == ROE else 20,
        artifactsBytes=16 if ver == ROE else (17 if (ver in (AB,)) else 18),
        spellsBytes=9, skillsBytes=4, buildingsBytes=6, resourcesBytes=4,
        artifactSlotsCount=18 if ver in (ROE, AB) else 19,
    )
    return f

def _bool(r):
    return r.u8() & 1

def _read_artifact(r, f):
    return r.u16() if f['levelAB'] else r.u8()

def _read_creature(r, f):
    return r.u16() if f['levelAB'] else r.u8()

def _read_creature_set(r, f):
    """readCreatureSet: 7 × (creature + u16 count)"""
    out = []
    for _ in range(7):
        cid = _read_creature(r, f)
        cnt = r.u16()
        if cid != 0 and cid != 0xffff:
            out.append((cid, cnt))
    return out

def _read_message_and_guards(r, f):
    """readMessageAndGuards: bool msg + [lstr + bool guards + creatureSet + skip4]"""
    if _bool(r):
        r.lstr()
        if _bool(r):
            _read_creature_set(r, f)
        r.skip(4)

def _read_bitmask(r, f, key):
    """readBitmask: N 字节 bitmask"""
    n = {'spells': 9, 'skills': 4, 'buildings': 6, 'factions': f['factionsBytes'],
         'heroes': f['heroesBytes'], 'resources': 4, 'players': 1}[key]
    r.skip(n)

def _read_quest(r, f):
    """readQuest (AB+): i8 mission + 载荷 + i32 lastDay + 3×lstr"""
    mission = r.i8()
    if mission == 0:
        return mission
    if mission == 1:      # PRIMARY_SKILL
        r.skip(4)
    elif mission == 2:    # LEVEL
        r.u32()
    elif mission in (3, 4):  # KILL_HERO / KILL_CREATURE
        r.u32()
    elif mission == 5:    # ARTIFACT
        n = r.u8()
        for _ in range(n):
            _read_artifact(r, f)
            if f['levelHOTA5']:
                r.i16()
    elif mission == 6:    # ARMY
        n = r.u8()
        for _ in range(n):
            _read_creature(r, f)
            r.u16()
    elif mission == 7:    # RESOURCES
        r.skip(28)
    elif mission == 8:    # HERO
        r.u8()
    elif mission == 9:    # PLAYER
        r.u8()
    elif mission == 10:   # HOTA_MULTI
        sub = r.u32()
        if sub == 0:
            n = r.u32(); r.skip((n + 7) // 8)
        elif sub == 1:
            r.u32()
        elif sub == 2:
            r.u32()
        elif sub == 3:
            r.u32(); _bool(r)
    r.i32()               # lastDay
    r.lstr(); r.lstr(); r.lstr()  # 3×文本
    return mission

def _read_box_content(r, f):
    """readBoxContent (Pandora/Event 共用): readMessageAndGuards + 经验/资源/技能/宝物/生物 + skip8"""
    _read_message_and_guards(r, f)
    r.u32()               # heroExperience
    r.i32()               # manaDiff
    r.i8()                # morale (checked)
    r.i8()                # luck
    r.skip(28)            # 7×i32 resources
    r.skip(4)             # 4×u8 primary
    n = r.u8(); r.skip(n * 2)      # gained abilities (u8 skill + i8 val)
    n = r.u8()                     # gained artifacts
    for _ in range(n):
        _read_artifact(r, f)
        if f['levelHOTA5']:
            r.i16()
    n = r.u8(); r.skip(n)          # gained spells (u8 each)
    n = r.u8()                     # gained creatures
    for _ in range(n):
        _read_creature(r, f)
        r.u16()
    r.skip(8)

def _read_box_hota(r, f):
    """readBoxHotaContent"""
    if f['levelHOTA5']:
        r.i32(); r.i32()
    if f['levelHOTA6']:
        r.i32()
    if f['levelHOTA9']:
        if _bool(r):
            r.i32(); _bool(r)

def _read_seer_quest(r, f):
    """readSeerHutQuest (AB+): readQuest + reward"""
    mission = _read_quest(r, f) if f['levelAB'] else 0
    if not f['levelAB']:
        art = _read_artifact(r, f)
        mission = 5 if art != 0 and art != 0xffff else 0
    if mission != 0:
        rw = r.i8()
        if rw == 0: pass
        elif rw == 1: r.u32()          # EXP
        elif rw == 2: r.u32()          # MANA
        elif rw in (3, 4): r.i8()      # MORALE / LUCK
        elif rw == 5: r.i8(); r.u32()  # RESOURCES
        elif rw == 6: r.u8(); r.u8()   # PRIMARY
        elif rw == 7: r.u8(); r.i8()   # SECONDARY
        elif rw == 8:                  # ARTIFACT
            _read_artifact(r, f)
            if f['levelHOTA5']:
                r.i16()
        elif rw == 9: r.u8()           # SPELL
        elif rw == 10:                 # CREATURE
            _read_creature(r, f); r.u16()

def _read_hero(r, f, pos):
    """readHero 对象 (HERO/RANDOM_HERO/PRISON) — 返回 owner/heroType 摘要"""
    if f['levelAB']:
        r.u32()               # identifier
    owner = r.u8()
    hero_type = r.u8()
    name = None
    if _bool(r):
        name = r.lstr().decode('utf-8', 'replace')
    if f['levelSOD']:
        if _bool(r):
            r.u32()           # exp
    else:
        r.u32()               # exp (ROE/AB 无条件)
    if _bool(r):
        r.u8()                # portrait
    if _bool(r):
        n = r.u32()
        r.skip(n * 2)         # sec skills (u8 + i8)
    if _bool(r):
        _read_creature_set(r, f)
    r.i8()                    # formation
    if _bool(r):              # loadArtifactsOfHero
        for _ in range(f['artifactSlotsCount']):
            _read_artifact(r, f)
            if f['levelHOTA5']:
                r.i16()
        n = r.u16()
        for _ in range(n):
            _read_artifact(r, f)
            if f['levelHOTA5']:
                r.i16()
    r.u8()                    # patrolRadius
    if f['levelAB']:
        if _bool(r):
            r.lstr()          # biography
        r.i8()                # gender
    if f['levelSOD']:
        if _bool(r):
            _read_bitmask(r, f, 'spells')
        if _bool(r):
            r.skip(4)         # prim skills
    else:
        r.u8()                # AB: 1 spell
    r.skip(16)
    if f['levelHOTA5']:
        _bool(r); _bool(r); r.i32()
    return {'owner': owner, 'hero_type': hero_type, 'name': name}

def _read_town(r, f, pos, oid, subid):
    """readTown 对象 — 返回 owner/faction 摘要"""
    if f['levelAB']:
        r.u32()               # identifier
    owner = r.u8()
    faction = subid if oid == 13 else None
    if _bool(r):
        r.lstr()              # name
    if _bool(r):
        _read_creature_set(r, f)
    r.i8()                    # formation
    if _bool(r):              # hasCustomBuildings
        _read_bitmask(r, f, 'buildings')
        _read_bitmask(r, f, 'buildings')
    else:
        _bool(r)              # hasFort
    if f['levelAB']:
        _read_bitmask(r, f, 'spells')   # obligatory
    _read_bitmask(r, f, 'spells')       # possible
    n = r.u32()               # castle events
    for _ in range(n):
        r.lstr(); r.lstr()    # event name + message
        r.skip(28)            # resources
        _read_bitmask(r, f, 'players')
        if f['levelSOD']:
            _bool(r)
        _bool(r)              # computerAffected
        r.u16(); r.u16()      # first/next occurrence
        r.skip(16)
        if f['levelHOTA7']:
            r.i32()
        if f['levelHOTA9']:
            if _bool(r):
                r.i32(); _bool(r)
        if f['levelHOTA5']:
            r.i32(); r.i32(); r.i32(); r.i16()
        _read_bitmask(r, f, 'buildings')
        r.skip(14)            # 7×u16 creatures
        r.skip(4)
    if f['levelSOD']:
        r.u8()                # alignment
    r.skip(3)
    return {'owner': owner, 'faction': faction}

def _valid_obj_head(r, p, w, def_count):
    """检查 p 处是否为有效对象头 (位置界内[允许 ±8 越界] + def 合法 + skip 全 0)"""
    if p + 12 > len(r.raw):
        return False
    x, y, z = r.raw[p], r.raw[p+1], r.raw[p+2]
    di = struct.unpack_from('<I', r.raw, p+3)[0]
    return x < w + 8 and y < w + 8 and z < 2 and di < def_count and r.raw[p+7:p+12] == b'\x00'*5

def parse_objects(path, tolerant=True):
    """解析对象段: 返回 {'templates','objects','obj_count','skipped_bytes'}
    tolerant=True: 每对象后校验下一对象头, 错位时向后搜索有效头恢复 (脏数据图如 Twins hero 需要)"""
    with open(path, 'rb') as fh:
        raw = gzip.decompress(fh.read())
    r = R(raw)
    ver = r.u32()
    hota_version = 0
    if ver == HOTA:
        hota_version = r.u32()
    f = _features(ver, hota_version)
    if ver == HOTA:
        raise ValueError("HOTA 对象表暂不支持")
    info = parse_header(path)
    off = info['terrain_offset']
    w = info['size']
    r.pos = off + w * w * 7 * (2 if info['has_underground'] else 1)
    r.safe = True  # 容错: 越界返回 0 而非抛异常

    def_count = r.u32()
    templates = []
    for _ in range(def_count):
        anim = r.lstr().decode('utf-8', 'replace')
        r.skip(12)            # blockMask 6 + visitMask 6
        r.u16()
        r.u16()
        oid = r.u32()
        subid = r.u32()
        r.u8()
        r.u8()
        r.skip(16)
        templates.append({'anim': anim, 'id': oid, 'subid': subid})

    obj_count = r.u32()
    objects = []
    skipped_bytes = 0
    for i in range(obj_count):
        # 头校验: 若当前位置不是有效对象头 (仅容错模式), 搜索恢复
        if tolerant and r.pos + 12 <= len(r.raw):
            x0, y0, z0 = r.raw[r.pos], r.raw[r.pos+1], r.raw[r.pos+2]
            di0 = struct.unpack_from('<I', r.raw, r.pos+3)[0]
            skip0 = r.raw[r.pos+7:r.pos+12]
            if x0 >= w + 8 or y0 >= w + 8 or z0 >= 2 or di0 >= def_count or skip0 != b'\x00'*5:
                found = None
                for q in range(r.pos + 1, min(r.pos + 500, len(r.raw) - 12)):
                    x, y, z = r.raw[q], r.raw[q+1], r.raw[q+2]
                    di = struct.unpack_from('<I', r.raw, q+3)[0]
                    if x < w and y < w and z < 2 and di < def_count and r.raw[q+7:q+12] == b'\x00'*5:
                        found = q
                        break
                if found is not None:
                    skipped_bytes += max(0, found - r.pos)
                    r.pos = found
        x, y, z = r.int3()
        def_idx = r.u32()
        r.skip(5)
        if def_idx >= def_count:
            raise ValueError(f"def_idx {def_idx} 越界 @{r.pos-12} (tolerant 未恢复)")
        t = templates[def_idx]
        oid, subid = t['id'], t['subid']
        name = OBJ_NAMES.get(oid, f'OBJ_{oid}')
        rec = {'idx': i, 'x': x, 'y': y, 'z': z, 'type': name, 'subid': subid,
               'owner': None}
        # 按类型分派 (MapFormatH3M.cpp readObject)
        if oid == 26:                       # EVENT
            _read_box_content(r, f)
            _read_bitmask(r, f, 'players')
            _bool(r); _bool(r)
            r.skip(4)
            if f['levelHOTA3']:
                _bool(r)
            _read_box_hota(r, f)
        elif oid in (62, 70):               # HERO / RANDOM_HERO (Obj:: 实测: HERO=62, RANDOM_HERO=70)
            before = r.pos
            h = _read_hero(r, f, (x, y, z))
            rec.update(h)
            if r.pos - before > 300:        # 脏数据 hero (如 Twins: bag 读爆)
                # 回溯到 hero 头附近搜索真实对象流
                found = None
                for q in range(before + 20, min(before + 300, len(r.raw) - 24)):
                    if _valid_obj_head(r, q, w, def_count) and _valid_obj_head(r, q + 12, w, def_count):
                        found = q
                        break
                if found is not None:
                    skipped_bytes += max(0, found - r.pos)
                    r.pos = found
        elif oid in (54, 72, 73, 74, 75, 162, 163):  # MONSTER 系列 (RANDOM_MONSTER=54 实测; L5=161 实测 generic)
            if f['levelAB']:
                r.u32()
            r.u16()
            r.i8()
            if _bool(r):
                r.lstr()
                r.skip(28)
                _read_artifact(r, f)
            _bool(r)
            _bool(r)
            r.skip(2)
            if f['levelHOTA3']:
                r.i32(); _bool(r); r.i32(); r.i32(); r.i32()
            if f['levelHOTA5']:
                _bool(r); r.i32()
        elif oid == 91:                     # SIGN (Obj:: 实测; OCEAN_BOTTLE 值未实测, 58 实测为 generic)
            r.lstr()
            r.skip(4)
        elif oid == 83:                     # SEER_HUT
            qn = 1
            if f['levelHOTA3']:
                qn = r.u32()
            for _ in range(qn):
                _read_seer_quest(r, f)
            if f['levelHOTA3']:
                rn = r.u32()
                for _ in range(rn):
                    _read_seer_quest(r, f)
            r.skip(2)
        elif oid == 113:                    # WITCH_HUT
            if f['levelAB']:
                _read_bitmask(r, f, 'skills')
        elif oid == 81:                     # SCHOLAR
            r.i8(); r.u8()
            r.skip(6)
        elif oid in (33, 219):              # GARRISON / GARRISON2
            rec['owner'] = r.u32()
            _read_creature_set(r, f)
            if f['levelAB']:
                _bool(r)
            r.skip(8)
        elif oid in (5, 65, 66, 67, 68, 69):  # ARTIFACT 系列
            _read_message_and_guards(r, f)
            if f['levelHOTA5']:
                r.u32(); r.u8()
        elif oid == 93:                     # SPELL_SCROLL
            _read_message_and_guards(r, f)
            r.i32()
        elif oid in (79, 76):               # RESOURCE / RANDOM_RESOURCE
            _read_message_and_guards(r, f)
            r.u32()
            r.skip(4)
        elif oid in (98, 77):               # TOWN / RANDOM_TOWN
            t2 = _read_town(r, f, (x, y, z), oid, subid)
            rec.update(t2)
        elif oid == 53:                     # MINE / ABANDONED_MINE (subid<7 = 矿, >=7 = abandoned)
            if subid < 7:
                rec['owner'] = r.u32()
            else:
                _read_bitmask(r, f, 'resources')
                if f['levelHOTA5']:
                    if _bool(r):
                        r.u32(); r.i32(); r.i32()
                    else:
                        r.skip(12)
        elif oid in (17, 18, 19, 20):       # CREATURE_GENERATOR
            rec['owner'] = r.u32()
        elif oid in (88, 89, 90):           # SHRINE
            r.i32()
        elif oid == 6:                      # PANDORAS_BOX
            _read_box_content(r, f)
            if f['levelHOTA5']:
                r.skip(1)
            _read_box_hota(r, f)
        elif oid == 36:                     # GRAIL
            r.i32()
        elif oid in (216, 217, 218):        # RANDOM_DWELLING
            rec['owner'] = r.u32()
            has_faction = oid in (25, 26)
            has_level = oid in (25, 27)
            if has_faction:
                ident = r.u32()
                if ident == 0:
                    _read_bitmask(r, f, 'factions')
            if has_level:
                r.u8(); r.u8()
        elif oid == 215:                    # QUEST_GUARD
            _read_quest(r, f)
        elif oid == 87:                     # SHIPYARD
            rec['owner'] = r.u32()
        elif oid == 214:                    # HERO_PLACEHOLDER
            rec['owner'] = r.u8()
            ht = r.u8()
            if ht == 0xff:
                r.u8()
            if f['levelHOTA5']:
                _bool(r)
                r.skip(28)
                n = r.i32()
                for _ in range(n):
                    r.i32()
        
            rec['owner'] = r.u32()
        elif oid in (16, 24, 25, 84, 85):   # CREATURE_BANK 系列
            if f['levelHOTA3']:
                r.i32(); r.i8()
                n = r.u32()
                r.skip(n * 4)
        elif oid == 62:                     # PYRAMID
            if f['levelHOTA5']:
                c = r.i32()
                if c == 0:
                    r.i32()
                else:
                    r.skip(4)
        elif oid == 101:                    # TREASURE_CHEST
            if f['levelHOTA5']:
                c = r.i32()
                if c != -1 and c == 3:
                    r.i32()
                else:
                    r.skip(4)
        elif oid in (108, 82, 86):          # WARRIORS_TOMB / SEA_CHEST / SHIPWRECK_SURVIVOR
            if f['levelHOTA5']:
                c = r.i32()
                if c != -1:
                    if c == 1:
                        r.i32()
                    else:
                        r.skip(4)
                else:
                    r.skip(4)
        elif oid in (29, 102):              # FLOTSAM / TREE_OF_KNOWLEDGE
            if f['levelHOTA5']:
                c = r.i32()
                if c != -1:
                    r.skip(4)
                else:
                    r.skip(4)
        elif oid == 12:                     # CAMPFIRE
            if f['levelHOTA5']:
                c = r.i32()
                if c != -1:
                    r.skip(4); r.i32(); r.i8(); r.i32(); r.i8()
                else:
                    r.skip(14)
        elif oid == 105:                    # WAGON
            if f['levelHOTA5']:
                c = r.i32()
                if c == 0:
                    r.i32(); r.i32(); r.i8(); r.skip(5)
                else:
                    r.skip(14)
        elif oid == 39:                     # LEAN_TO
            if f['levelHOTA5']:
                c = r.i32()
                if c != -1:
                    r.skip(4); r.i32(); r.i8(); r.skip(5)
                else:
                    r.skip(14)
        elif oid == 7:                      # BLACK_MARKET
            if f['levelHOTA5']:
                r.skip(28)
        elif oid == 104:                    # UNIVERSITY
            if f['levelHOTA5']:
                r.i32()
                _read_bitmask(r, f, 'skills')
        elif oid == 212:                    # BORDER_GATE (默认 generic)
            pass
        else:                               # readGeneric: 0 字节
            pass
        objects.append(rec)
    return {'templates': templates, 'objects': objects, 'obj_count': obj_count,
            'skipped_bytes': skipped_bytes}

def modify_terrain(in_path, out_path, edits):
    """edits: {'water': [[x,y],...], 'rock': [...], 'grass': [...], 'rect': [x0,y0,x1,y1,code], 'river': [...]}"""
    info = parse_header(in_path)
    w = info['size']
    off = info['terrain_offset']
    has_ug = info['has_underground']
    levels = 2 if has_ug else 1

    with open(in_path, 'rb') as f:
        raw = bytearray(gzip.decompress(f.read()))

    code_map = {'dirt':0,'sand':1,'grass':2,'snow':3,'swamp':4,'rough':5,'subterra':6,'lava':7,'water':8,'rock':9}
    changes = 0
    for key, cells in edits.items():
        if key == 'rect':
            x0, y0, x1, y1, code = cells
            if isinstance(code, str): code = code_map[code]
            for y in range(y0, y1+1):
                for x in range(x0, x1+1):
                    pos = off + (y * w + x) * 7  # surface only
                    raw[pos] = code
                    changes += 1
            continue
        code = code_map[key]
        for (x, y) in cells:
            pos = off + (y * w + x) * 7
            raw[pos] = code
            changes += 1

    with open(out_path, 'wb') as f:
        f.write(gzip.compress(raw))
    print(f"修改 {changes} 格 terrain, 输出 {out_path}")
    return changes

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'scan':
        info = parse_header(sys.argv[2])
        print(json.dumps({k: v for k, v in info.items() if k != 'players'}, indent=1, default=str))
        print("players:", json.dumps(info['players']))
    elif cmd == 'terrain':
        modify_terrain(sys.argv[2], sys.argv[3], json.load(open(sys.argv[4])))
    elif cmd == 'objects':
        res = parse_objects(sys.argv[2])
        for o in res['objects']:
            line = f"#{o['idx']:3d} {o['type']:22s} sub={o['subid']:3d} pos=({o['x']:3d},{o['y']:3d},{o['z']})"
            if o['owner'] is not None:
                line += f" owner={o['owner']}"
            if o.get('hero_type') is not None:
                line += f" hero={o['hero_type']}"
            if o.get('name'):
                line += f" name={o['name']}"
            if o.get('faction') is not None:
                line += f" faction={o['faction']}"
            print(line)
        print(f"templates={len(res['templates'])} objects={res['obj_count']} skipped={res['skipped_bytes']}")
    else:
        print(__doc__)
