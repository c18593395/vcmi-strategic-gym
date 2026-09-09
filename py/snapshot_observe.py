#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0910 观察窗快照复核 — 新口径基线画像 (visitable 判据 + EP_TIME)
用法 (WSL): python3 py/snapshot_observe.py [train_loop.log 路径]
只统计最后一次 'Loaded train state' 之后的数据。
"""
import re, sys, statistics
from collections import defaultdict

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").read().splitlines()

# 只取最后一次 resume 之后
start = 0
for i, l in enumerate(lines):
    if "Loaded train state" in l:
        start = i + 1
w = lines[start:]
print(f"窗口: 最后 resume 之后 {len(w)} 行")

# --- [EP_TIME] 画像 ---
eps = []
pat_et = re.compile(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\w+)")
for l in w:
    m = pat_et.search(l)
    if m:
        eps.append({"map": m.group(1), "steps": int(m.group(2)),
                    "secs": int(m.group(3)), "r": float(m.group(4)), "err": m.group(5)})

per_map = defaultdict(list)
for e in eps:
    per_map[e["map"]].append(e)
print(f"\n== 局画像 (n={len(eps)}) ==")
for mp, es in sorted(per_map.items()):
    rs = [e["r"] for e in es]
    sps = [e["secs"] / max(e["steps"], 1) for e in es]
    print(f"  {mp}: n={len(es)} avg_r={statistics.mean(rs):.1f} r范围=[{min(rs):.1f},{max(rs):.1f}] "
          f"avg_steps={statistics.mean(e['steps'] for e in es):.0f} s/步={statistics.mean(sps):.2f}")
slow = [e for e in eps if e["secs"] / max(e["steps"], 1) > 2.0]
print(f"  慢局 (>2s/步): {len(slow)}" + ("" if not slow else " -> " + "; ".join(f"{e['map'][:24]} {e['secs']}/{e['steps']}步={e['secs']/max(e['steps'],1):.1f}s" for e in slow[:5])))
errs = [e for e in eps if e["err"] != "no"]
print(f"  异常局: {len(errs)}")

# --- 事件计数 ---
cnt = defaultdict(int)
for l in w:
    for tag in ("[GUARD]", "[MINE]", "[TOWN_CAPTURE]", "[TOWNSTALL]", "[ZOMBIE]", "[ENDTURN_FUSE]",
                "[START_HOME]", "[RECRUITED]", "[TOWN_VISIT]", "[HEROSEG_EMPTY]", "[EP_TIME]"):
        if tag in l:
            cnt[tag] += 1
print("\n== 事件计数 ==")
for k in sorted(cnt):
    print(f"  {k}: {cnt[k]}")

# --- ep 行 r 分布 (含进行中局外的完整局) ---
pat_ep = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+).*obs_nz=(\d+) map=(\S+)")
eps2 = []
for l in w:
    m = pat_ep.search(l)
    if m:
        eps2.append({"steps": int(m.group(1)), "r": float(m.group(2)), "nz": int(m.group(3)), "map": m.group(4)})
if eps2:
    rs = [e["r"] for e in eps2]
    print(f"\n== ep 行 (n={len(eps2)}) avg_r={statistics.mean(rs):.1f} 中位={statistics.median(rs):.1f} "
          f"正局率={sum(1 for r in rs if r > 0)}/{len(rs)} 200步局={sum(1 for e in eps2 if e['steps'] >= 200)}")
    nz_band = defaultdict(int)
    for e in eps2:
        nz_band[e["nz"]] += 1
    print("  obs_nz 特征带:", dict(sorted(nz_band.items())))

# --- [GUARD] 位置新口径核对 (顺序关联下一个 EP_TIME 的 map) ---
pat_g = re.compile(r"\[GUARD\] guard \((\d+),(\d+)\)")
guards_seq = []  # (x, y, map_or_None)
last_map = None
for l in w:
    mg = pat_g.search(l)
    if mg:
        guards_seq.append((int(mg.group(1)), int(mg.group(2)), None))
        continue
    me = pat_et.search(l)
    if me:
        last_map = me.group(1)
        if guards_seq and guards_seq[-1][2] is None:
            guards_seq[-1] = (guards_seq[-1][0], guards_seq[-1][1], last_map)

import zipfile, json
MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training/"
def vis_set(mapname):
    try:
        z = zipfile.ZipFile(MAP_DIR + mapname)
        objs = json.loads(z.read("objects.json"))
        out = set()
        for k, o in objs.items():
            if k.startswith("monster_"):
                mask = o["template"]["mask"]
                for y, row in enumerate(mask):
                    done = False
                    for x, ch in enumerate(row):
                        if ch in ("A", "T"):
                            out.add((int(o["x"]) - x, int(o["y"]) - y)); done = True; break
                    if done: break
        return out
    except Exception:
        return None

vis_cache = {}
hit = miss = unknown = 0
miss_list = []
for gx, gy, mp in guards_seq:
    if mp is None:
        unknown += 1; continue
    if mp not in vis_cache:
        vis_cache[mp] = vis_set(mp)
    s = vis_cache[mp]
    if s is None:
        unknown += 1
    elif (gx, gy) in s:
        hit += 1
    else:
        miss += 1; miss_list.append((mp.split("/")[-1][:28], gx, gy))
print(f"\n== [GUARD] 新口径核对 (n={len(guards_seq)}) hit(vis位)={hit} miss={miss} unknown={unknown}")
for t in miss_list[:5]:
    print("  MISS:", t)
print("\n[快照完成]")
