"""检查 4 张空 players VMAP 的对象分布"""
import json, zipfile
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
MAPS = BASE / "maps" / "training"

TARGETS = [
    "T06_adventure_72X72_02_duel.vmap",   # ← 在训练 MAPS 名单 L64
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_02_duel.vmap",
    "T06_adventure_108X108_02.vmap",
]

for name in TARGETS:
    p = MAPS / name
    if not p.exists():
        print(f"\n=== {name} NOT FOUND ===")
        continue
    print(f"\n=== {name} ({p.stat().st_size} bytes) ===")
    with zipfile.ZipFile(p) as z:
        h = json.loads(z.read("header.json").decode("utf-8", errors="replace"))
        print(f"  header.players = {h.get('players')}")
        print(f"  header.mods    = {h.get('mods')}")
        print(f"  mapLevels      = {h.get('mapLevels')}")
        objs = json.loads(z.read("objects.json").decode("utf-8", errors="replace"))
        print(f"  objects total  = {len(objs)}")
        towns, heroes = [], []
        for k, v in objs.items():
            t = v.get("type")
            if t == "town":
                towns.append((k, v.get("x"), v.get("y"), v.get("options", {}).get("owner"), v.get("options", {}).get("subtype")))
            elif t == "hero":
                heroes.append((k, v.get("x"), v.get("y"), v.get("options", {}).get("owner"), v.get("options", {}).get("subtype")))
        print(f"  towns ({len(towns)}):")
        for row in towns:
            print(f"    {row[0]:12s} x={row[1]:>3} y={row[2]:>3} owner={row[3]!r} subtype={row[4]}")
        print(f"  heroes ({len(heroes)}):")
        for row in heroes:
            print(f"    {row[0]:12s} x={row[1]:>3} y={row[2]:>3} owner={row[3]!r} subtype={row[4]}")
