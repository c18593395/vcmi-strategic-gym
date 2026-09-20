#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe: a_warm_and_familiar_place 清洗前后 mainTown 与城坐标对照"""
import zipfile, json, sys
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
from h3m2vmap import _loads_permissive

RAW = "/tmp/h3m_pipeline/a_warm_and_familiar_place.raw.vmap"

z = zipfile.ZipFile(RAW)
h = _loads_permissive(z.read("header.json").decode())
pl = h.get("players") or {}
print("=== header.players ===")
for pid in ("red", "blue", "green", "tan", "orange", "purple", "teal", "pink"):
    if pid in pl:
        print(f"  {pid}: {json.dumps(pl[pid])}")
print(f"\n=== header.heroes ===")
print(json.dumps(h.get("heroes"), indent=2)[:500] or "  (无)")
print(f"\n=== header.predefinedHeroes (前3) ===")
for hd in (h.get("predefinedHeroes") or [])[:3]:
    print(" ", json.dumps(hd)[:300])
print(f"\n=== header.teams ===")
print(json.dumps(h.get("teams"), indent=2) if h.get("teams") else "  (无)")

objs = _loads_permissive(z.read("objects.json").decode())
towns = [o for o in objs if "town" in str(o.get("type", "")).lower()]
print(f"\n=== towns ({len(towns)}) ===")
for t in towns:
    print(f"  type={t.get('type')} owner={t.get('owner', t.get('options',{}).get('owner'))} "
          f"l={t.get('l')} x={t.get('x')} y={t.get('y')} name={t.get('instanceName')}")

# 清洗后的 vmap（已部署到 rel/bin 的那个）
REL = "/home/administrator/vcmi-native/rel/bin/data/Maps/a_warm_and_familiar_place_h3m.vmap"
print(f"\n=== 已部署 vmap: {REL} ===")
try:
    z2 = zipfile.ZipFile(REL)
    h2 = _loads_permissive(z2.read("header.json").decode())
    pl2 = h2.get("players") or {}
    print("  header.players:")
    for pid in ("red", "blue"):
        if pid in pl2:
            print(f"    {pid}: {json.dumps(pl2[pid])}")
    print(f"  header.teams: {json.dumps(h2.get('teams'))}")
    objs2 = _loads_permissive(z2.read("objects.json").decode())
    towns2 = [o for o in objs2 if "town" in str(o.get("type", "")).lower()]
    print(f"  towns ({len(towns2)}):")
    for t in towns2:
        print(f"    type={t.get('type')} owner={t.get('owner',t.get('options',{}).get('owner'))} "
              f"l={t.get('l')} x={t.get('x')} y={t.get('y')} name={t.get('instanceName')}")
except Exception as e:
    print(f"  (部署 vmap 不存在或读失败: {e})")
