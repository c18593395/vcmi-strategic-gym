#!/usr/bin/env python3
# B2 冒烟前置检查 v2: B2_KneeDeep.vmap 零改写直通产物
# header.json 可能带注释/非严格 JSON (引擎 fixStringsTextIDInJson 产物) → 宽松解析
import zipfile, json, collections, os, re

MAPS_TRAINING = "/mnt/d/Bigdata/hero3_fresh/maps/training"
RUNTIME = "/home/administrator/vcmi-native/rel/bin/data/Maps"
NAME = "B2_KneeDeep.vmap"

def strip_json_comments(s: str) -> str:
    """逐字符剥 // 与 /* */ 注释 (跳过字符串字面量内的 #), 引擎 header 带 // 行注释"""
    out, i, n = [], 0, len(s)
    in_str = False
    while i < n:
        ch = s[i]
        if in_str:
            out.append(ch)
            if ch == '"' and s[i-1] != '\\':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch); i += 1; continue
        if ch == '/' and i + 1 < n and s[i+1] == '/':
            while i < n and s[i] != '\n':
                i += 1
            continue
        if ch == '/' and i + 1 < n and s[i+1] == '*':
            i += 2
            while i + 1 < n and not (s[i] == '*' and s[i+1] == '/'):
                i += 1
            i += 2
            continue
        out.append(ch); i += 1
    return ''.join(out)

def loose_json(raw: bytes):
    """容忍引擎 JSON 的注释/尾逗号: 严格 → 去尾逗号 → 剥注释 逐级放宽"""
    s = raw.decode("utf-8", errors="replace")
    for variant in (s, re.sub(r",\s*([}\]])", r"\1", s), strip_json_comments(s)):
        try:
            return json.loads(variant)
        except json.JSONDecodeError:
            continue
    print("  [ERR] loose JSON failed on all variants")
    raise

def probe(zpath, label):
    print(f"=== {label}: {zpath} ===")
    if not os.path.exists(zpath):
        print("  MISSING")
        return None
    z = zipfile.ZipFile(zpath)
    entries = z.namelist()
    for rf in ["header.json", "surface_terrain.json", "objects.json"]:
        print(f"  [{'OK' if rf in entries else 'MISSING'}] {rf} ({z.getinfo(rf).file_size if rf in entries else '-'}B)"
              if rf in entries else f"  [MISSING] {rf}")
    hdr = loose_json(z.read("header.json"))
    print("  name:", hdr.get("name"))
    print("  mapLevels:", json.dumps(hdr.get("mapLevels"), ensure_ascii=False)[:300])
    players = hdr.get("players")
    print("  players shape:", type(players).__name__)
    print("  players:", json.dumps(players, ensure_ascii=False)[:1000])
    keys = set(hdr.keys())
    must = ["name","description","mapLevels","players","teams","randomEvents","triggeredEvents","mods","howManyTeams","howManyPlayers","startingGold","startingResources","startingSpells"]
    missing = [k for k in must if k not in keys]
    print("  header keys:", len(keys), "| missing-of-13:", missing if missing else "none")
    objs = loose_json(z.read("objects.json"))
    items = list(objs.values()) if isinstance(objs, dict) else list(objs)
    types = collections.Counter()
    hero_towns = []
    for v in items:
        types[v.get("type")] += 1
        if "hero" in str(v.get("type")) or "town" in str(v.get("type")):
            hero_towns.append((v.get("type"), v.get("subtype"), v.get("options", {}).get("type"), v.get("x"), v.get("y"), v.get("instanceName")))
    print(f"  obj count: {len(items)}")
    for t, c in types.most_common(50):
        print(f"    {c:4d}  {t}")
    print("  hero/town instances:")
    for h in hero_towns[:20]:
        print("   ", h)
    return hdr

probe(f"{MAPS_TRAINING}/{NAME}", "maps/training")
probe(f"{RUNTIME}/{NAME}", "rel/bin/data/Maps")
