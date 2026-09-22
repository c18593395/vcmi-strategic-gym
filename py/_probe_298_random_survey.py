#!/usr/bin/env python3
"""#298 专项 v5: 全池 137 张图随机对象普查 (09-23 只读)
假设: randomTown/randomHero/random* 对象加载期随机解析 → 概率性触发引擎 bug。
对照批转结果(池内=PASS): 若含随机对象的图普遍带雷而 viking(纯实体)幸存 → 假设成立。
"""
import json, zipfile, re, os
from collections import Counter

POOL = "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool"
IDX = json.load(open("/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_index.json", encoding="utf-8"))

RANDOM_PAT = re.compile(r'^random', re.I)  # type 以 random 开头

rows = []
for f in sorted(os.listdir(POOL)):
    if not f.endswith(".vmap"):
        continue
    entry = IDX.get(f, {})
    if entry.get("blue_ai") == "skip":
        continue
    try:
        z = zipfile.ZipFile(os.path.join(POOL, f))
        objs = json.loads(z.read("objects.json").decode("utf-8", "replace"))
        olist = objs.get("objects", objs) if isinstance(objs, dict) else objs
        h = json.loads(z.read("header.json").decode("utf-8", "replace"))
    except Exception as e:
        rows.append((f, -1, f"parse_err:{e}", ""))
        continue
    rc = Counter()
    for o in olist:
        t = str(o.get("type", "?")).split(":")[-1]
        if RANDOM_PAT.match(t):
            rc[t] += 1
    # header 玩家随机标记
    pl = h.get("players", {})
    hdr_rand = []
    if isinstance(pl, dict):
        for k, p in pl.items():
            if not isinstance(p, dict):
                continue
            if p.get("randomFaction"):
                hdr_rand.append(f"{k}:randomFaction")
            if any(str(hk).startswith("randomHero") for hk in (p.get("heroes") or {})):
                hdr_rand.append(f"{k}:randomHero")
    n_rand_objs = sum(rc.values())
    batch = entry.get("batch", "")
    hold = "hold" if entry.get("batch") == 99 else ""
    rows.append((f, n_rand_objs, dict(rc), ",".join(hdr_rand), batch, hold))

# 汇总
n_total = len(rows)
n_zero = sum(1 for r in rows if r[1] == 0)
print(f"池内图总数(非skip): {n_total} / 无随机对象: {n_zero} / 含随机对象: {n_total - n_zero}")
print(f"\n{'图名':<44}{'随机对象数':<6} 随机类型 / header随机标记 / batch")
for r in rows:
    if r[1] == 0 and not r[3]:
        continue
    f, n, rc, hdr, batch, hold = (r + ("", ""))[:6]
    print(f"{f:<44}{n:<6} {rc} hdr[{hdr}] batch={batch} {hold}")

# batch1 三图 + viking 重点核对
print("\n===== batch1 相关图核对 =====")
for r in rows:
    if any(k in r[0] for k in ("good_to_go", "judgement_day", "elbow_room", "a_viking")):
        print(f"  {r[0]}: 随机对象={r[1]} hdr随机=[{r[3]}] batch={r[4]}")
