#!/usr/bin/env python3
"""#298 专项 v3: players 完整 JSON + mapLevels + events + 课程图对照 (09-23 只读)
v2 发现: players dict 骨架级; good_to_go blue 无 mainTown; 对象数假设证伪。
"""
import json, zipfile, re

MAPS = [
    ("good_to_go_h3m.vmap", "必挂"),
    ("judgement_day_h3m.vmap", "必挂"),
    ("elbow_room_h3m.vmap", "必挂"),
    ("a_viking_we_shall_go_h3m.vmap", "能跑-对照"),
    ("arrogance_h3m.vmap", "PASS-对照"),
    ("T05_adventure_52X52_01.vmap", "课程图-对照"),
]
PATHS = {
    "T05_adventure_52X52_01.vmap": "/mnt/d/Bigdata/hero3_fresh/maps/training/T05_adventure_52X52_01.vmap",
}
POOL = "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"

def strip_comments(s):
    return re.sub(r'^\s*//.*$', '', s, flags=re.M)

def loads_permissive(s):
    try:
        return json.loads(s)
    except Exception:
        return json.loads(strip_comments(s))

for name, tag in MAPS:
    path = PATHS.get(name, f"{POOL}/{name}")
    print(f"\n===== {name} [{tag}] =====")
    try:
        z = zipfile.ZipFile(path)
    except Exception as e:
        print(f"  打开失败: {e}")
        continue
    for m in z.namelist():
        print(f"  成员 {m}: {z.getinfo(m).file_size}B")
    h = loads_permissive(z.read("header.json").decode("utf-8", "replace"))
    print(f"  mapLevels 原样: {json.dumps(h.get('mapLevels'), ensure_ascii=False)[:300]}")
    players = h.get("players")
    print(f"  players 完整: {json.dumps(players, ensure_ascii=False)[:900]}")
    ev = h.get("events")
    if ev:
        print(f"  events(timed): {json.dumps(ev, ensure_ascii=False)[:200]}")
    # terrain 尺寸线索: surface_terrain.json 顶层
    if "surface_terrain.json" in z.namelist():
        t = loads_permissive(z.read("surface_terrain.json").decode("utf-8", "replace"))
        if isinstance(t, dict):
            print(f"  surface_terrain 顶层键: {list(t.keys())[:12]}")
