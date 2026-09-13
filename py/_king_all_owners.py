"""检查 King 全部 town/hero 的 owner 颜色分布"""
import json, zipfile
from pathlib import Path
from collections import Counter

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

p = BASE / "maps" / "training" / "King_of_Pain_h3m.vmap"
with zipfile.ZipFile(p) as z:
    objs = json.loads(z.read("objects.json").decode("utf-8", errors="replace"))

towns = [o for o in objs.values() if o.get("type") in ("town","randomTown")]
heroes = [o for o in objs.values() if o.get("type") in ("hero","randomHero")]
mines = [o for o in objs.values() if o.get("type") == "mine"]
monsters = [o for o in objs.values() if o.get("type") in ("monster","randomMonster")]

print(f"KING towns ({len(towns)}):")
for i, (k, t) in enumerate(objs.items()):
    if t.get("type") in ("town","randomTown"):
        o = t.get("options", {})
        print(f"  {k:>10} x={t['x']:>3} y={t['y']:>3} subtype={t.get('subtype'):20s} owner={o.get('owner')!r}")

print(f"\nKING heroes ({len(heroes)}):")
for h in heroes:
    o = h.get("options", {})
    print(f"  x={h['x']:>3} y={h['y']:>3} subtype={h.get('subtype'):20s} owner={o.get('owner')!r} type={o.get('type')}")

# 检查 T01 vs King 的 players+hero owner 关系
print("\n===== T01 objects (完整列表) =====")
t01_p = BASE / "maps" / "training" / "T01_adventure_36X36_01.vmap"
with zipfile.ZipFile(t01_p) as z:
    t01_objs = json.loads(z.read("objects.json").decode("utf-8", errors="replace"))
for k, v in t01_objs.items():
    if v.get("type") in ("town","hero","randomTown","randomHero","mine","randomMonster"):
        opt = v.get("options", {})
        print(f"  {k}: type={v.get('type')} subtype={v.get('subtype')} x={v.get('x')} y={v.get('y')} owner={opt.get('owner')}")

print("\n===== 分布统计 =====")
def color_counts(items, owner_path):
    c = Counter()
    for it in items:
        # 按 owner_path 取
        obj = it
        for p in owner_path:
            obj = obj.get(p, {}) if isinstance(obj, dict) else {}
        c[obj] += 1
    return c

print(f"  King town owners: {dict(color_counts(towns, ['options','owner']))}")
print(f"  King hero owners: {dict(color_counts(heroes, ['options','owner']))}")
print(f"  T01 town owners:  {dict(color_counts([o for o in t01_objs.values() if o.get('type')=='town'], ['options','owner']))}")
print(f"  T01 hero owners:  {dict(color_counts([o for o in t01_objs.values() if o.get('type')=='hero'], ['options','owner']))}")
