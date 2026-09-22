#!/usr/bin/env python3
"""#298 专项 v4: objects 层 town/hero/owner 分布 + pipeline report + pool rank (09-23 只读)"""
import json, zipfile, re
from collections import Counter

POOL = "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"
MAPS = [
    "good_to_go_h3m.vmap", "judgement_day_h3m.vmap", "elbow_room_h3m.vmap",
    "a_viking_we_shall_go_h3m.vmap", "arrogance_h3m.vmap",
]

def loads_permissive(s):
    try:
        return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'^\s*//.*$', '', s, flags=re.M))

for name in MAPS:
    print(f"\n===== {name} =====")
    z = zipfile.ZipFile(f"{POOL}/{name}")
    objs = loads_permissive(z.read("objects.json").decode("utf-8", "replace"))
    olist = objs.get("objects", objs) if isinstance(objs, dict) else objs
    towns, heroes, others_owner = [], [], Counter()
    kinds = Counter()
    for o in olist:
        t = str(o.get("type", "?"))
        tid = t.split(":")[-1] if ":" in t else t
        kinds[tid] += 1
        own = o.get("owner", "?")
        if "town" in tid.lower() or "RandomTown".lower() in t.lower():
            towns.append((o.get("instanceName"), own, o.get("x"), o.get("y"), t))
        if "hero" in tid.lower():
            heroes.append((o.get("instanceName"), own, o.get("x"), o.get("y"), t))
    print(f"  总对象 {len(olist)}")
    print(f"  城对象: {len(towns)}")
    for t in towns[:12]:
        print(f"    {t}")
    print(f"  英雄对象: {len(heroes)}")
    for hh in heroes[:8]:
        print(f"    {hh}")
    print(f"  类型 top12: {kinds.most_common(12)}")

# pipeline report + rank
print("\n===== _pipeline_report.json (三图+viking) =====")
try:
    rep = json.load(open("/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pipeline_report.json", encoding="utf-8"))
    entries = rep if isinstance(rep, list) else rep.get("entries", rep.get("maps", []))
    if isinstance(entries, dict):
        entries = list(entries.values())
    for e in entries:
        nm = str(e.get("map") or e.get("name") or e.get("file") or "")
        if any(k in nm.lower() for k in ("good_to_go", "judgement", "elbow_room", "viking")):
            print(f"  {json.dumps(e, ensure_ascii=False)[:400]}")
except Exception as ex:
    print(f"  读取失败: {ex}")

print("\n===== _pool_rank.json (五图) =====")
try:
    rank = json.load(open("/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_rank.json", encoding="utf-8"))
    rl = rank if isinstance(rank, list) else rank.get("maps", rank.get("entries", []))
    if isinstance(rl, dict):
        rl = list(rl.values())
    for e in rl:
        nm = str(e.get("map") or e.get("name") or "")
        if any(k in nm.lower() for k in ("good_to_go", "judgement", "elbow_room", "viking", "arrogance")):
            print(f"  {json.dumps(e, ensure_ascii=False)[:400]}")
except Exception as ex:
    print(f"  读取失败: {ex}")
