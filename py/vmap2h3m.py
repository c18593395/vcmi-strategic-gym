#!/usr/bin/env python3
"""vmap2h3m: VCMI .vmap (zip json) → HoMM3 .h3m (SOD 格式) 转换器 (P10 旁路工具, 2026-09-01)

引擎无 H3M 写出器 (只有 vmap saveMap), 本脚本按 h3m_tool.py reader 的字节镜像自建写回。
范围 = 训练图特征集: hero / town / mine / resource / monster 五类对象 + 全地形, 单层或双层。

对象模板 (def) 来源 = donor 官方图: 按 (id, subid) 匹配后**原样复制 raw 条目**,
文件内对象 id 一致性天然成立, 绕开 H3M 原始编号考证。
donor 缺 (id,subid) 时: 同 id 任意条目 patch subid 字节 (外观可能错位, 引擎可读)。

映射数据源 = 引擎 config (creatures/heroes json 的 index 字段), 不硬编码大表。

用法:
  python3 vmap2h3m.py <in.vmap> <out.h3m> [--engine-root DIR] [--donor H3M ...]
                      [--name NAME] [--desc DESC] [--report REPORT.json]

验证:
  python3 h3m_tool.py objects <out.h3m>   # 读回对账 (类型/坐标/owner/兵力)
  python3 h3m_tool.py scan <out.h3m>      # header 对账
"""
import argparse
import glob
import gzip
import json
import os
import re
import struct
import sys
import zipfile

# ── 常量 ──────────────────────────────────────────────────────────────────────
ROE, AB, SOD, CHR, WOG, HOTA = 0x0e, 0x15, 0x1c, 0x1d, 0x33, 0x20
VERSION_OUT = SOD

TERRAIN_CODE = {'dt': 0, 'sa': 1, 'gr': 2, 'sn': 3, 'sw': 4, 'rg': 5,
                'sb': 6, 'lv': 7, 'wt': 8, 'rc': 9}
FLIP_MAP = {'r': 0, 'd': 1, 'l': 2, 'u': 3}  # flipCodes[flags%4] 逆映射 (近似, 仅图形)

FACTION_CODE = {'castle': 0, 'rampart': 1, 'tower': 2, 'inferno': 3,
                'necropolis': 4, 'dungeon': 5, 'stronghold': 6, 'fortress': 7,
                'conflux': 8}
RESOURCE_CODE = {'wood': 0, 'mercury': 1, 'ore': 2, 'sulfur': 3,
                 'crystal': 4, 'gems': 5, 'gold': 6}
MINE_CODE = {'sawmill': 0, 'alchemistLab': 1,
             'oreMine': 2, 'orePit': 2,
             'sulfurMine': 3, 'sulfurDune': 3,
             'crystalMine': 4, 'crystalCavern': 4,
             'gemPond': 5, 'goldMine': 6,
             'abandoned': -1}  # -1 = 跳过 (donor 无独立 abandoned 模板, 走 report.missing)
# mine subid 与资源同序 (0 sawmill .. 6 gold), 7+ = abandoned

OWNER_CODE = {'red': 0, 'blue': 1, 'tan': 2, 'green': 3, 'orange': 4,
              'purple': 5, 'teal': 6, 'pink': 7, 'neutral': 255}

# donor 匹配候选: vmap type → (候选 H3M 对象 id 集, subid 求值函数)
CANDIDATE_IDS = {
    'town': (98, 77),          # fork 枚举 TOWN=98; h3m_tool 实测 77; donor 实际为准
    'hero': (62, 34),          # 同上 (h3m_tool 实测 62 / fork 34)
    'monster': (54,),          # MONSTER
    'resource': (79,),
    'mine': (53,),
}


def strip_json_comments(path):
    txt = open(path, encoding='utf-8').read()
    txt = re.sub(r'//[^\n]*', '', txt)
    txt = re.sub(r'/\*.*?\*/', '', txt, flags=re.S)
    return json.loads(txt)


# ── 引擎 index 表 ─────────────────────────────────────────────────────────────
def load_engine_indexes(engine_root):
    """shortIdentifier → index (creatures / heroes), 来自引擎 config json"""
    creatures, heroes = {}, {}
    pat = [
        ('Mods/vcmi/Content/config/creatures/*.json', creatures),
        ('config/creatures/*.json', creatures),
        ('Mods/vcmi/Content/config/heroes/*.json', heroes),
        ('config/heroes/*.json', heroes),
    ]
    for rel, dst in pat:
        for f in sorted(glob.glob(os.path.join(engine_root, rel))):
            try:
                d = strip_json_comments(f)
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] config 解析失败 {f}: {e}", file=sys.stderr)
                continue
            for k, v in d.items():
                if isinstance(v, dict) and 'index' in v:
                    dst.setdefault(k, v['index'])
    return creatures, heroes


# ── donor 模板库 ──────────────────────────────────────────────────────────────
class TemplateLib:
    """donor h3m 模板 raw 条目库: (id, subid) → raw bytes (可 patch subid)"""

    def __init__(self):
        self.by_key = {}     # (id, subid) → raw
        self.by_id = {}      # id → [raw, ...]
        self.sources = []

    def add_h3m(self, path):
        with open(path, 'rb') as fh:
            raw = gzip.decompress(fh.read())
        ver = struct.unpack_from('<I', raw, 0)[0]
        if ver not in (ROE, AB, SOD, CHR, WOG):
            return 0
        # 复用 h3m_tool 的 header 解析定位 terrain 之后
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
        import h3m_tool  # noqa: PLC0415
        info = h3m_tool.parse_header(path)
        pos = info['terrain_end']
        n = struct.unpack_from('<I', raw, pos)[0]
        pos += 4
        added = 0
        for _ in range(n):
            start = pos
            ln = struct.unpack_from('<I', raw, pos)[0]
            anim = raw[pos + 4:pos + 4 + ln].decode('latin1')
            pos += 4 + ln + 12            # anim + block6+visit6
            _u16a, _u16b = struct.unpack_from('<HH', raw, pos)
            pos += 4
            oid, subid = struct.unpack_from('<II', raw, pos)
            pos += 8 + 1 + 1 + 16
            entry = raw[start:pos]
            key = (oid, subid)
            if key not in self.by_key:
                self.by_key[key] = entry
                self.by_id.setdefault(oid, []).append(entry)
                added += 1
        self.sources.append((os.path.basename(path), added))
        return added

    def fetch(self, oid_candidates, subid):
        """按候选 id + subid 精确命中; 否则同 id 任意条目 patch subid; 都缺则 None"""
        for oid in oid_candidates:
            if (oid, subid) in self.by_key:
                return self.by_key[(oid, subid)], oid, 'exact'
        for oid in oid_candidates:
            lst = self.by_id.get(oid)
            if lst:
                entry = bytearray(lst[0])
                # raw: [u32 len][anim][12B][u16][u16][u32 id][u32 subid][u8][u8][16B]
                off = 4 + struct.unpack_from('<I', entry, 0)[0] + 12 + 4
                struct.pack_into('<I', entry, off + 4, subid)
                return bytes(entry), oid, 'patched-subid'
        return None, None, 'missing'


# ── vmap 读取 ─────────────────────────────────────────────────────────────────
def read_vmap(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        header = json.loads(z.read('header.json'))
        tfiles = sorted(n for n in names if n.endswith('_terrain.json'))
        terrains = [json.loads(z.read(n)) for n in tfiles]
        objs_raw = json.loads(z.read('objects.json'))
    objects = list(objs_raw.values()) if isinstance(objs_raw, dict) else objs_raw
    return header, terrains, objects


def parse_tile(s):
    """tile 字符串 'gr24r' / 'gr24rrd00...' → (terrain_code, view, flags)"""
    m = re.match(r'([a-z]{1,2})(\d+)([a-zA-Z]?)', s)
    if not m:
        return TERRAIN_CODE['gr'], 0, 0
    code = TERRAIN_CODE.get(m.group(1), TERRAIN_CODE['gr'])
    view = int(m.group(2)) & 0xFF
    flags = FLIP_MAP.get(m.group(3), 0)
    return code, view, flags


# ── H3M writer ────────────────────────────────────────────────────────────────
class W:
    def __init__(self):
        self.buf = bytearray()

    def u8(self, v):
        self.buf += struct.pack('<B', v & 0xFF)

    def u16(self, v):
        self.buf += struct.pack('<H', v & 0xFFFF)

    def u32(self, v):
        self.buf += struct.pack('<I', v & 0xFFFFFFFF)

    def i8(self, v):
        self.buf += struct.pack('<b', v)

    def raw(self, b):
        self.buf += b

    def lstr(self, s):
        b = s.encode('utf-8')
        self.u32(len(b))
        self.buf += b

    def creature_set(self, army):
        """7 槽 × (u16 creatureId, u16 count); SOD creature=u16"""
        for i in range(7):
            cid, cnt = 0, 0
            if i < len(army) and army[i]:
                cid, cnt = army[i]
            self.u16(cid)
            self.u16(cnt)


def map_owner(o):
    if o is None:
        return 255
    return OWNER_CODE.get(str(o).lower(), 255)


def map_army(army_opts, creatures):
    """vmap army [{}] → [(cid,cnt)] 过滤空槽"""
    out = []
    for slot in army_opts or []:
        if isinstance(slot, dict) and slot.get('type'):
            short = str(slot['type']).split(':')[-1]
            cid = creatures.get(short)
            if cid is None:
                raise KeyError(f"creature '{slot['type']}' 不在引擎 index 表")
            out.append((cid, int(slot.get('amount', 1))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('in_vmap')
    ap.add_argument('out_h3m')
    ap.add_argument('--engine-root', default='/home/administrator/vcmi-native/rel/bin')
    ap.add_argument('--donor', action='append', default=[],
                    help='donor h3m 模板库来源 (可多次)')
    ap.add_argument('--name')
    ap.add_argument('--desc', default='')
    ap.add_argument('--report')
    args = ap.parse_args()

    print(f"[1] 读 vmap: {args.in_vmap}")
    header, terrains, objects = read_vmap(args.in_vmap)

    print(f"[2] 载引擎 index 表: {args.engine_root}")
    creatures, heroes = load_engine_indexes(args.engine_root)
    print(f"    creatures={len(creatures)} heroes={len(heroes)}")

    print(f"[3] donor 模板库")
    lib = TemplateLib()
    donors = args.donor or sorted(glob.glob(os.path.join(args.engine_root, 'data/Maps/*.h3m')))
    # 逐张加载直到模板足够 (上限 60 张, 控制耗时)
    need_probe = objects
    for d in donors[:60]:
        try:
            n = lib.add_h3m(d)
            if n:
                print(f"    {os.path.basename(d)}: +{n}")
        except Exception as e:  # noqa: BLE001
            print(f"    [warn] donor 跳过 {d}: {e}", file=sys.stderr)
        # 覆盖检查: 五类都至少有 patch fallback 即可继续
    print(f"    库容: {len(lib.by_key)} 条 (来自 {len(lib.sources)} 张)")

    # ── 对象准备: 匹配模板 + 求文件 subid ──
    print(f"[4] 对象映射 ({len(objects)} 个)")
    w = W()
    template_index = {}   # (oid, subid_used) → defIdx
    template_list = []
    h3m_objects = []      # (x, y, z, defIdx, kind, payload_fn)
    report = {'objects': [], 'missing': [], 'templates': []}

    for o in objects:
        kind = o.get('type')
        opts = o.get('options', {}) or {}
        sub_raw = str(o.get('subtype', '')).split(':')[-1]
        x, y, z = int(o.get('x', 0)), int(o.get('y', 0)), int(o.get('l', 0) or 0)
        entry = rec = None

        if kind == 'town':
            fidx = FACTION_CODE[sub_raw]
            entry, oid, how = lib.fetch(CANDIDATE_IDS['town'], fidx)
            rec = ('town', {'owner': map_owner(opts.get('owner')), 'faction': fidx})
        elif kind == 'hero':
            hero_short = str(opts.get('type') or o.get('subtype', '')).split(':')[-1]
            hidx = heroes.get(hero_short)
            if hidx is None:
                report['missing'].append(f"hero '{hero_short}' 不在引擎 index 表")
                continue
            army = map_army(opts.get('army'), creatures)
            entry, oid, how = lib.fetch(CANDIDATE_IDS['hero'], hidx)
            rec = ('hero', {'owner': map_owner(opts.get('owner')), 'hero_type': hidx,
                            'exp': int(opts.get('experience', 0)), 'army': army})
        elif kind == 'monster':
            cidx = creatures.get(sub_raw)
            if cidx is None:
                report['missing'].append(f"creature '{sub_raw}' 不在引擎 index 表")
                continue
            army = [(cidx, int(opts.get('amount', 1)))]
            entry, oid, how = lib.fetch(CANDIDATE_IDS['monster'], cidx)
            rec = ('monster', {'count': int(opts.get('amount', 1)),
                               'character': 4, 'never_flees': 1 if opts.get('neverFlees') else 0})
        elif kind == 'resource':
            ridx = RESOURCE_CODE[sub_raw]
            entry, oid, how = lib.fetch(CANDIDATE_IDS['resource'], ridx)
            rec = ('resource', {'amount': int(opts.get('amount', 0))})
        elif kind == 'mine':
            ridx = MINE_CODE.get(sub_raw, RESOURCE_CODE.get(sub_raw))
            if ridx is None:
                raise KeyError(f"mine '{sub_raw}' 无 subid 映射")
            if ridx < 0:  # abandoned 无 donor 模板, 走 report.missing 静默跳过
                report['missing'].append(f"mine '{sub_raw}' abandoned: donor 无独立模板, 跳过")
                continue
            entry, oid, how = lib.fetch(CANDIDATE_IDS['mine'], ridx)
            rec = ('mine', {'owner': map_owner(opts.get('owner'))})
        else:
            report['missing'].append(f"跳过不支持类型: {kind}")
            continue

        if entry is None:
            report['missing'].append(f"{kind} {sub_raw}: donor 无 (id 集 {CANDIDATE_IDS[kind]}, subid)")
            continue

        oid_used = struct.unpack_from('<I', entry, 4 + struct.unpack_from('<I', entry, 0)[0] + 12 + 4)[0]
        subid_used = struct.unpack_from('<I', entry, 4 + struct.unpack_from('<I', entry, 0)[0] + 12 + 4 + 4)[0]
        key = (oid_used, subid_used)
        if key not in template_index:
            template_index[key] = len(template_list)
            template_list.append(entry)
        def_idx = template_index[key]
        h3m_objects.append((x, y, z, def_idx, rec))
        report['objects'].append({'name': o.get('instanceName') or o.get('type'), 'kind': kind,
                                  'pos': [x, y, z], 'template': [oid_used, subid_used], 'match': how})

    if report['missing']:
        print("    [!] 缺失/跳过:", *report['missing'], sep='\n        ')

    # ── header ──
    print(f"[5] 写 header (SOD)")
    w.u32(VERSION_OUT)
    w.u8(1)                                  # are_any_players
    lvl = header.get('mapLevels', {})
    wdt = int(lvl.get('surface', {}).get('width', 36))
    hgt = int(lvl.get('surface', {}).get('height', wdt))
    if wdt != hgt:
        print(f"    [warn] 非正方形 {wdt}x{hgt}, H3M 仅支持正方形 — 取 {min(wdt, hgt)}", file=sys.stderr)
    size = min(wdt, hgt)
    w.u32(size)
    w.u8(len(terrains) > 1)                  # has_underground
    w.lstr(args.name or str(header.get('name', 'converted')))
    w.lstr(args.desc or '')
    w.u8(1)                                  # difficulty (NORMAL)
    w.u8(1 if VERSION_OUT in (AB, SOD, CHR, WOG, HOTA) else 0)  # level_limit (AB+)

    # players ×8: slot0=red, slot1=blue
    player_specs = [None] * 8
    towns_by_owner = {}
    heroes_by_owner = {}
    for (x, y, z, _d, (kind, payload)) in h3m_objects:
        if kind == 'town':
            towns_by_owner.setdefault(payload['owner'], []).append((x, y, z))
        if kind == 'hero':
            heroes_by_owner.setdefault(payload['owner'], payload['hero_type'])
    for slot in range(8):
        active = slot in (0, 1)
        spec = {'human': 1, 'ai': 1, 'town': towns_by_owner.get(slot),
                'hero': heroes_by_owner.get(slot)} if active else None
        player_specs[slot] = spec
    inactive_skip = 6 + 6 + 1  # base6 + AB6 + SOD1
    for spec in player_specs:
        if spec is None:
            w.u8(0); w.u8(0)
            w.raw(b'\x00' * inactive_skip)
            continue
        w.u8(spec['human'])
        w.u8(spec['ai'])
        w.u8(0)                              # aiTactic
        w.u8(0)                              # SOD skip
        w.u16(0xFFFF)                        # factions 允许全部
        w.u8(0)                              # isFactionRandom
        if spec['town']:
            w.u8(1)
            w.u8(0); w.u8(0)             # (AB+) main_town 前 2 字节 (h3m_tool 实测逆向)
            tx, ty, tz = spec['town'][0]
            w.u8(tx); w.u8(ty); w.u8(tz)
        else:
            w.u8(0)
        w.u8(0)                              # hasRandomHero
        if spec['hero'] is not None:
            w.u8(spec['hero'])               # mainHero != 0xff
            w.u8(spec['hero'])               # portrait
            w.lstr('Hero')
        else:
            w.u8(0xFF)
        w.u8(0)                              # AB skip
        w.u32(0)                             # heroCount

    w.i8(-1)                                 # victory: WINSTANDARD
    w.i8(-1)                                 # loss: LOSSSTANDARD
    w.u8(0)                                  # teams
    w.raw(b'\xFF' * 20)                      # allowedHeroes (AB/SOD=20B)
    w.u32(0)                                 # placeholders (AB)
    w.u8(0)                                  # disposedHeroes (SOD)
    w.raw(b'\x00' * 31)                      # map options
    w.raw(b'\xFF' * 18)                      # allowedArtifacts (SOD=18)
    w.raw(b'\xFF' * 9)                       # allowedSpells
    w.raw(b'\xFF' * 4)                       # allowedSkills
    w.u32(0)                                 # rumors
    w.raw(b'\x00' * 156)                     # predefinedHeroes (SOD=156)

    # ── terrain ──
    print(f"[6] 写 terrain ({len(terrains)} 层, {size}x{size})")
    for terr in terrains:
        rows = terr if isinstance(terr, list) else terr.get('surface', [])
        for yy in range(size):
            row = rows[yy] if yy < len(rows) else []
            for xx in range(size):
                tile = row[xx] if xx < len(row) else 'gr00'
                code, view, flags = parse_tile(tile)
                w.u8(code); w.u8(view); w.u8(flags)
                w.u8(0); w.u8(0)             # river
                w.u8(0); w.u8(0)             # road

    # ── templates ──
    print(f"[7] 写 templates ({len(template_list)}) + objects ({len(h3m_objects)})")
    w.u32(len(template_list))
    for entry in template_list:
        w.raw(entry)
    w.u32(len(h3m_objects))
    obj_id = 0
    for (x, y, z, def_idx, (kind, p)) in h3m_objects:
        w.u8(x); w.u8(y); w.u8(z)
        w.u32(def_idx)
        w.raw(b'\x00' * 5)
        if kind == 'hero':
            w.u32(obj_id)                    # identifier (AB)
            w.u8(p['owner'])
            w.u8(p['hero_type'])
            w.u8(0)                          # hasName
            w.u8(1); w.u32(p['exp'])         # (SOD) hasExp → exp
            w.u8(0)                          # hasPortrait
            w.u8(0)                          # hasSecSkills
            w.u8(1)
            w.creature_set(p['army'])        # hasArmy
            w.i8(0)                          # formation (wide)
            w.u8(1)                          # hasArts
            w.raw(b'\xFF\xFF' * 19)          # 19 槽空 (0xffff) — SOD=19 (h3m_tool 实测)
            w.u16(0)                         # backpack 0
            w.u8(0)                          # patrolRadius
            w.u8(0)                          # (AB) hasBiography
            w.i8(-1)                         # gender
            w.u8(0)                          # (SOD) hasSpells
            w.u8(0)                          # (SOD) hasPrim
            w.raw(b'\x00' * 16)
        elif kind == 'town':
            w.u32(obj_id)                    # identifier (AB)
            w.u8(p['owner'])
            w.u8(0)                          # hasName
            w.u8(0)                          # hasGarrison
            w.i8(0)                          # formation
            w.u8(0)                          # hasCustomBuildings
            w.u8(1)                          # hasFort
            w.raw(b'\x00' * 9)               # obligatory spells (AB)
            w.raw(b'\xFF' * 9)               # possible spells
            w.u32(0)                         # castleEvents
            w.u8(0xFF)                       # (SOD) alignment
            w.raw(b'\x00' * 3)
        elif kind == 'resource':
            # readResource: bool hasMessage(skip4 仅在 msg=1 分支内) + u32 amount + skip4
            w.u8(0)                          # hasMessage = 0 (1B)
            w.u32(p['amount'])
            w.raw(b'\x00' * 4)
        elif kind == 'mine':
            w.u32(p['owner'])
        elif kind == 'monster':
            w.u32(obj_id)                    # identifier (AB)
            w.u16(p['count'])
            w.i8(p['character'])
            w.u8(0)                          # hasMessage
            w.u8(p['never_flees'])
            w.u8(0)
            w.raw(b'\x00' * 2)
        obj_id += 1

    with open(args.out_h3m, 'wb') as fh:
        fh.write(gzip.compress(bytes(w.buf)))
    print(f"[8] 输出: {args.out_h3m} ({len(w.buf)}B raw)")

    report['size'] = size
    report['templates'] = [f"{oid},{subid}" for oid, subid in template_index]
    report['counts'] = {}
    for (_x, _y, _z, _di, (kind, _p)) in h3m_objects:
        report['counts'][kind] = report['counts'].get(kind, 0) + 1
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
        print(f"    report → {args.report}")
    print(f"    counts: {report['counts']}")


if __name__ == '__main__':
    main()
