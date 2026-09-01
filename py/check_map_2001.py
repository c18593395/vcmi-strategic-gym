# -*- coding: utf-8 -*-
"""20X20_01 0胜归因: ① hermes_ep 明细 GUARD 触发统计 ② 地形连通性检查"""
import zipfile, json, glob, os, re
from collections import Counter

# ---------- ① hermes_ep 明细 ----------
print("=" * 30, "① hermes_ep 明细", "=" * 30)
for f in sorted(glob.glob("/tmp/hermes_ep_*.log"), key=os.path.getmtime):
    txt = open(f, encoding="utf-8", errors="ignore").read()
    m = re.search(r"mapname[=:'\"]+(\S+?\.vmap)", txt)
    mapn = m.group(1) if m else "?"
    wins = len(re.findall(r"GUARD.*won", txt))
    steps = len(re.findall(r"\[NK2\] step=", txt))
    print(f"{os.path.basename(f)}: map={mapn} guard_win={wins} nk2_steps={steps}")

# ---------- ② vmap 地形连通性 ----------
print("\n" + "=" * 30, "② 地形连通性", "=" * 30)

def load_map(name):
    p = f"/mnt/d/Bigdata/hero3_fresh/Maps/training/{name}"
    z = zipfile.ZipFile(p)
    names = z.namelist()
    objs = json.loads(z.read("objects.json"))
    terr = None
    for cand in ("terrain.json", "map.json"):
        if cand in names:
            terr = json.loads(z.read(cand))
    return names, objs, terr

for name in ["T03_adventure_20X20_01.vmap", "T03_adventure_20X20_02.vmap"]:
    names, objs, terr = load_map(name)
    print(f"\n--- {name} ---")
    print("zip entries:", names)
    # 提取 hero / monster / 地形
    hero = None
    guards = []
    blocked = set()
    if isinstance(terr, dict):
        tg = terr.get("terrain") or terr.get("grid")
        if tg:
            print("terrain grid: %d x %d rows=%d" % (len(tg[0]), len(tg), len(tg)))
    for k, o in objs.items():
        t = o.get("type", "")
        opts = o.get("options", {})
        if "hero" in k or t == "hero":
            if opts.get("owner") == "red":
                hero = (int(o["x"]), int(o["y"]))
        if k.startswith("monster_") or t == "monster":
            guards.append((int(o["x"]), int(o["y"])))
        # 障碍物类型
        if t in ("mountain", "rock", "tree", "obstacle", "lake", "water"):
            blocked.add((int(o["x"]), int(o["y"])))
    print(f"hero={hero} guards={guards} blocked_objs={len(blocked)}")
    if terr:
        # terrain 编码未知 → 统计取值分布
        def walk(v, out):
            if isinstance(v, list):
                for x in v: walk(x, out)
            elif isinstance(v, (int, float)):
                out.append(v)
        vals = []
        walk(tg if tg else terr, vals)
        c = Counter(vals)
        print("terrain value distribution:", dict(sorted(c.items())[:12]) if c else "N/A")
