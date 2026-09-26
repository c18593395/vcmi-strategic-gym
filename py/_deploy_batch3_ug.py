#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_deploy_batch3_ug.py — 基于已转好的 /tmp/batch3_ug/*.raw.vmap 入池 + index 标记
13 张真地下 → batch:3; darwin_s_prize_allies(空地下层) → batch:99 hold
幂等: 已在池且 index batch 已对的就 skip.
"""
import json, os, sys, time, shutil, glob, zipfile
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
import _convert_batch3_ug as c
import strip_underground_vmap as su

ROOT = c.ROOT
POOL = c.POOL
POOL_INDEX = c.POOL_INDEX
H3M_DIR = c.H3M_DIR
BATCHES = c.BATCHES

EXCLUDE = {"darwin_s_prize_allies": "underground_empty(0对象0城, 无地下训练价值)"}

pb = json.load(open(BATCHES, encoding="utf-8"))
idx = json.load(open(POOL_INDEX, encoding="utf-8"))
os.makedirs(POOL, exist_ok=True)

n_pool = n_excl = n_skip = 0
for e in pb["batch3_underground"]:
    safe = e["vmap"].replace("_h3m.vmap", "")
    fn = f"{safe}_ug_h3m.vmap"
    raw = f"/tmp/batch3_ug/{safe}_ug.raw.vmap"
    if not os.path.exists(raw):
        print(f"  [MISS-RAW] {safe}"); continue
    ok, detail = c.selfcheck(raw)
    if safe in EXCLUDE or not ok:
        # 排除入池, 但登记 index 防误采 + 记录原因
        idx[fn] = {"blue_ai": "MMAI_RANDOM", "layer": "underground", "batch": 99,
                   "hold_reason": EXCLUDE.get(safe, "selfcheck_fail:" + detail),
                   "h3m": e.get("h3m", ""), "verify": detail,
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        print(f"  [EXCLUDE] {safe} → batch:99 {EXCLUDE.get(safe, detail)}")
        n_excl += 1
        continue
    # 真入池
    if os.path.exists(f"{POOL}/{fn}") and idx.get(fn, {}).get("batch") == 3:
        print(f"  [SKIP] {fn} 已在池 batch=3"); n_skip += 1; continue
    shutil.copy(raw, f"{POOL}/{fn}")
    shutil.copy(raw, os.path.join(H3M_DIR, fn))   # 运行时
    idx[fn] = {"blue_ai": "MMAI_RANDOM", "layer": "underground", "batch": 3,
               "h3m": e.get("h3m", ""), "based_on": e["vmap"], "verify": detail,
               "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
    print(f"  [POOL] {fn} ← {detail}")
    n_pool += 1
    with open(POOL_INDEX, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)

print(f"\n==== 部署汇总: 入池={n_pool} 排除={n_excl} 跳过={n_skip} ====")
# 复核 index batch 分布
from collections import Counter
dist = Counter()
for k, v in idx.items():
    b = v.get("batch") if isinstance(v, dict) else None
    dist[b] += 1
print("index batch 分布:", dict(dist))
