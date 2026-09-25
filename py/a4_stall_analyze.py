#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A4 卡死段深度分析 (09-17): 本窗 T05 局逐局重建名义轨迹 + 分段停滞形态 + 目标关联 + guide_abort K 模拟。
只读。用法: python3 py/a4_stall_analyze.py [窗口起始行号]
口径:
- 名义轨迹: 从 [START_HOME] hero=(x,y) 起, 方向动作 0-7 按 _DIRS 积分 (被拒移动不可见, 名义=上限)
- 零推进步: 非方向动作 (10/16-21/24 等) — 名义位置必不变
- 振荡: 8 步滑窗名义位置集合 <=2 (等价 runner 横跳 8 步窗检测, 但含被拒方向误差)
- 停滞步 (guide_abort 模拟口径): 零推进步 或 所在 8 步窗振荡
分段: econ 0-23 / 引导窗 24-59 (move_to_force=60) / 自由期 60+
"""
import os
import re
import statistics
import sys
from collections import defaultdict

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
DIRS = [(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]

with open(LOG, errors="replace") as f:
    lines = f.readlines()

start = int(sys.argv[1]) if len(sys.argv) > 1 else max(i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l)
seg = lines[start:]

# 切局: ep_steps 行 = 局末边界; 之前积攒的 SCORE/START_HOME 归属当前局
EPS = re.compile(r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]*)\] obs_nz=(\d+) map=(\S+)")
SCORE = re.compile(r"\[SCORE\] pick=\((-?\d+),(-?\d+)\) type=(\S+) score=(-?[\d.]+).*?at step (\d+)")
START_HOME = re.compile(r"\[START_HOME\] begin step=0 hero=\((-?\d+),(-?\d+)\)")
TVISIT = re.compile(r"\[TOWN_VISIT\] own town recruit window at step (\d+)")

episodes, cur = [], {"scores": [], "hero0": None, "tvisits": []}
for l in seg:
    m = START_HOME.search(l)
    if m:
        cur["hero0"] = (int(m.group(1)), int(m.group(2)))
    m = TVISIT.search(l)
    if m:
        cur["tvisits"].append(int(m.group(1)))
    m = SCORE.search(l)
    if m:
        cur["scores"].append({"x": int(m.group(1)), "y": int(m.group(2)), "type": m.group(3),
                              "score": float(m.group(4)), "step": int(m.group(5))})
    m = EPS.search(l)
    if m:
        cur.update({"steps": int(m.group(1)), "r": float(m.group(2)),
                    "act": [int(x) for x in m.group(3).split(",") if x.strip()],
                    "map": m.group(5)})
        episodes.append(cur)
        cur = {"scores": [], "hero0": None, "tvisits": []}

t05 = [e for e in episodes if e["map"].startswith("T05") and not e["map"].endswith("_duel.vmap")]
t06 = [e for e in episodes if e["map"].startswith("T06") and not e["map"].endswith("_duel.vmap")]
duel = [e for e in episodes if e["map"].endswith("_duel.vmap")]
print(f"生效窗 L={start}: 总 {len(episodes)} 局 = T05非duel {len(t05)} / T06非duel {len(t06)} / duel {len(duel)}")


def seg_stats(act, lo, hi, hero0):
    """段内 [lo,hi) 统计: 返回 dict"""
    a = act[lo:hi]
    if not a:
        return None
    x, y = hero0
    # 名义轨迹 (从局起点积分到 lo)
    for d in act[:lo]:
        if d < 8:
            dx, dy = DIRS[d]
            x, y = x + dx, y + dy
    pos_series, zero_run, max_zero_run = [], 0, 0
    for d in a:
        if d < 8:
            dx, dy = DIRS[d]
            x, y = x + dx, y + dy
            pos_series.append((x, y))
            zero_run = 0
        else:
            pos_series.append((x, y))
            zero_run += 1
            max_zero_run = max(max_zero_run, zero_run)
    # 8 步滑窗位置集合 <=2 计数 (振荡窗)
    osc8 = sum(1 for i in range(len(pos_series)) if len(set(pos_series[max(0, i-7):i+1])) <= 2)
    # 最长连续同动作
    max_same, run = 0, 0
    for i, d in enumerate(a):
        run = run + 1 if i > 0 and d == a[i-1] else 1
        max_same = max(max_same, run)
    # 连续停滞模拟 (零推进 或 8 步窗振荡): guide_abort 口径
    stall_run, max_stall = 0, 0
    for i in range(len(pos_series)):
        w = set(pos_series[max(0, i-7):i+1])
        if (a[i] >= 8) or len(w) <= 2:
            stall_run += 1
            max_stall = max(max_stall, stall_run)
        else:
            stall_run = 0
    return {"n": len(a), "zero_steps": sum(1 for d in a if d >= 8),
            "max_zero_run": max_zero_run, "max_same": max_same, "osc8": osc8,
            "max_stall": max_stall,
            "dir_ratio": sum(1 for d in a if d < 8) / len(a)}


def analyze(group, name):
    if not group:
        return
    print(f"\n=== {name} ({len(group)} 局) ===")
    guide_stall6 = 0
    rows = []
    for e in group:
        h0 = e["hero0"] or (5, 5)
        s_guide = seg_stats(e["act"], 24, 60, h0)
        s_free = seg_stats(e["act"], 60, min(e["steps"], len(e["act"])), h0)
        if s_guide and s_guide["max_stall"] >= 6:
            guide_stall6 += 1
        rows.append((e, s_guide, s_free))
    print(f"guide_abort 模拟: 引导窗(24-59) 连续停滞 >=6 步的局: {guide_stall6}/{len(group)} "
          f"({guide_stall6*100//len(group)}%) → 熔断可捕获面")
    # 自由期 (60+) 停滞汇总 — 真卡死嫌疑段
    free_stall6 = sum(1 for _, sf, _ in [(e, seg_stats(e["act"], 60, min(e["steps"], len(e["act"])), e["hero0"] or (5,5)), None)
                                        for e in group] if sf and sf["max_stall"] >= 6)
    tv_all = [len(e["tvisits"]) for e in group if e["tvisits"] is not None]
    print(f"自由期(60+) 连续停滞 >=6 步的局: {free_stall6}/{len(group)} | "
          f"TOWN_VISIT 次/局: mean={statistics.mean(tv_all):.1f} max={max(tv_all) if tv_all else 0}")
    for e, sg, sf in rows:
        line = f"  {e['map'][:34]:34s} r={e['r']:8.1f} steps={e['steps']:3d}"
        if sg:
            line += (f" | 引导24-59: 零推{sg['zero_steps']:2d}/同动段{sg['max_same']:2d}/停滞段{sg['max_stall']:2d}")
        if sf:
            line += (f" || 自由60+: 零推{sf['zero_steps']:2d}/同动段{sf['max_same']:2d}"
                     f"/振荡窗{sf['osc8']:2d}/停滞段{sf['max_stall']:2d}")
        line += f" | visit×{len(e['tvisits'])}@{e['tvisits'][:4]}"
        # 卡死段 (38-59) SCORE 目标
        picks = [s["type"] for s in e["scores"] if 38 <= s["step"] < 60]
        if picks:
            from collections import Counter
            line += f" | 38-59目标:{dict(Counter(picks))}"
        print(line)


analyze(t05, "T05 非duel (A4 主对象)")
analyze(t06, "T06 非duel (对照)")
analyze(duel, "duel (P-H1 关闭对照)")

# 卡死段目标分布汇总 (T05)
print("\n=== T05 引导窗 38-59 段 [SCORE] 目标分布汇总 ===")
cnt = defaultdict(int)
tot = 0
for e in t05:
    for s in e["scores"]:
        if 38 <= s["step"] < 60:
            cnt[s["type"]] += 1
            tot += 1
for t, c in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {t:12s} {c:3d} ({c*100//max(tot,1)}%)")
print(f"  合计 {tot} 次 pick (38-59 段)")
