#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 S2 新基线恢复段完整评估: 20局分段趋势 + duel 净胜率/困死 + 按图分组.

duel 净胜率 (MVP 指标): 净胜率 = 守卫胜率 - 困死率 (duel 图), 目标 ≥50%.
分图统计: duel 图按 map 分别统计 守卫胜/困死/r 均值, 避免总均值稀释.

用法:
  1) 直接运行: 用内置 START 行号 (默认最后 40 局)
  2) 改 START 行号评估其他窗口 (见 eval_new_baseline_0919.py 头部注释)
"""
import re, statistics, collections

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").readlines()

# 评估起点 (行号, 1-based) — 09-21 T7.8 终版窗 (#292 三次修复 + pick 拉黑, banner step=848792 重启)
START = 134517
seg = lines[START - 1:]
SEG_END = len(seg)
print(f"评估窗口: 行 {START}..{START + len(seg)} ({len(seg)} 行)\n")

# 解析所有 EP_TIME (全局行号从 START 起)
eps = []
for i, ln in enumerate(seg, start=START):
    m = re.search(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=\d+ r=(-?[\d.]+) err=(\w+)", ln)
    if m:
        eps.append({"line": i, "map": m.group(1), "steps": int(m.group(2)),
                    "r": float(m.group(3)), "err": m.group(4)})
print(f"共 {len(eps)} 局\n")


def block_of(e, eps_list, idx):
    """某局到下一局的日志块 (全局行号)."""
    end = eps_list[idx + 1]["line"] if idx + 1 < len(eps_list) else (START + SEG_END + 1)
    s = e["line"] - START
    eoff = min(end, START + SEG_END) - START
    return "".join(seg[s:eoff])


# 1) 20 局分段趋势
print("== 20 局分段趋势 ==")
for b in range(0, len(eps), 20):
    ch = eps[b:b + 20]
    rs = [e["r"] for e in ch]
    de = 0
    steps_m = statistics.mean([e["steps"] for e in ch])
    for idx in range(len(ch)):
        e = ch[idx]
        lm_idx = b + idx
        end = eps[lm_idx + 1]["line"] if lm_idx + 1 < len(eps) else (START + SEG_END + 1)
        s = e["line"] - START
        eoff = min(end, START + SEG_END) - START
        de += "".join(seg[s:eoff]).count("[HERO_DEATH]")
        de += "".join(seg[s:eoff]).count("[RED_DEAD]")
    print(f"  局{b + 1:03d}-{b + len(ch):03d}: r均值={statistics.mean(rs):7.1f} "
          f"min={min(rs):7.1f} 死亡={de}({de / len(ch) * 100:.0f}%) "
          f"步均值={steps_m:.0f}")

# 2) duel 图汇总 — MVP 净胜率指标
print("\n== duel 图汇总 (MVP 净胜率指标) ==")
duel_eps = [e for e in eps if "duel" in e["map"]]
n = len(duel_eps)
duel_d = 0
duel_rd = 0
duel_g = 0
for idx, e in enumerate(duel_eps):
    lm_idx = eps.index(e)
    end = eps[lm_idx + 1]["line"] if lm_idx + 1 < len(eps) else (START + SEG_END + 1)
    s = e["line"] - START
    eoff = min(end, START + SEG_END) - START
    blk = "".join(seg[s:eoff])
    duel_d += blk.count("[HERO_DEATH]")
    duel_rd += blk.count("[RED_DEAD]")
    duel_g += blk.count("fought & won")
duel_r = [e["r"] for e in duel_eps]
guard_rate = duel_g / max(1, n) * 100
death_rate = (duel_d + duel_rd) / max(1, n) * 100
net_rate = guard_rate - death_rate
print(f"duel 局数={n} r均值={statistics.mean(duel_r) if duel_r else 0:.1f}")
print(f"  守卫胜={duel_g}({guard_rate:.0f}%) 困死={duel_d}({duel_d / max(1, n) * 100:.0f}%) "
      f"战死={duel_rd}({duel_rd / max(1, n) * 100:.0f}%)")
print(f"  duel 净胜率 = 守卫胜 - (困死+战死) = {net_rate:.0f}%  (MVP 目标 ≥50%)")
print(f"  duel r 分布(升序): {sorted(duel_r)}")

# 3) duel 图分图统计 (MVP 关键: 避免总均值稀释)
print("\n== duel 图分图统计 (MVP 分图净胜率) ==")
duel_by_map = collections.defaultdict(list)
for e in duel_eps:
    duel_by_map[e["map"]].append(e)
print(f"  {'图':36s} {'局':>4s} {'r均值':>8s} {'守卫胜':>8s} {'困死':>7s} {'战死':>7s} {'净胜率':>8s}")
for mp in sorted(duel_by_map):
    mp_eps = duel_by_map[mp]
    mn = len(mp_eps)
    mp_d = 0
    mp_rd = 0
    mp_g = 0
    for e in mp_eps:
        lm_idx = eps.index(e)
        end = eps[lm_idx + 1]["line"] if lm_idx + 1 < len(eps) else (START + SEG_END + 1)
        s = e["line"] - START
        eoff = min(end, START + SEG_END) - START
        blk = "".join(seg[s:eoff])
        mp_d += blk.count("[HERO_DEATH]")
        mp_rd += blk.count("[RED_DEAD]")
        mp_g += blk.count("fought & won")
    mp_r = [e["r"] for e in mp_eps]
    mp_guard = mp_g / max(1, mn) * 100
    mp_death = (mp_d + mp_rd) / max(1, mn) * 100
    mp_net = mp_guard - mp_death
    flag = " ✅" if mp_net >= 50 else (" ⚠️" if mp_net >= 20 else " ❌")
    print(f"  {mp:36s} {mn:4d} {statistics.mean(mp_r):8.1f} "
          f"{mp_guard:7.0f}% {mp_d:6.0f}% {mp_rd:6.0f}% {mp_net:+7.0f}%{flag}")

# 4) 按图分组 (全部图, 含 duel + 非 duel)
print("\n== 按图分组 (全部) ==")
by_map_r = collections.defaultdict(list)
by_map_d = collections.defaultdict(int)
by_map_rd = collections.defaultdict(int)
by_map_g = collections.defaultdict(int)
for idx, e in enumerate(eps):
    end = eps[idx + 1]["line"] if idx + 1 < len(eps) else (START + SEG_END + 1)
    s = e["line"] - START
    eoff = min(end, START + SEG_END) - START
    blk = "".join(seg[s:eoff])
    by_map_r[e["map"]].append(e["r"])
    by_map_d[e["map"]] += blk.count("[HERO_DEATH]")
    by_map_rd[e["map"]] += blk.count("[RED_DEAD]")
    by_map_g[e["map"]] += blk.count("fought & won")
for mp in sorted(by_map_r):
    rs = by_map_r[mp]
    d = by_map_d.get(mp, 0)
    rd = by_map_rd.get(mp, 0)
    g = by_map_g.get(mp, 0)
    net = g / len(rs) * 100 - (d + rd) / len(rs) * 100
    print(f"  {mp:36s} {len(rs):3d}局 r均值={statistics.mean(rs):7.1f} "
          f"min={min(rs):6.1f} 困死={d} 战死={rd}({(d + rd) / len(rs) * 100:.0f}%) "
          f"守卫胜={g}({g / len(rs) * 100:.0f}%) 净胜率={net:+.0f}%")
total_d = sum(by_map_d.values())
total_rd = sum(by_map_rd.values())
print(f"\n  困死(HERO_DEATH) {total_d} / {len(eps)} 局 = {total_d / max(1, len(eps)) * 100:.0f}%")
print(f"  战死(RED_DEAD)   {total_rd} / {len(eps)} 局 = {total_rd / max(1, len(eps)) * 100:.0f}%")

# 5) MVP 结论
print("\n== MVP 结论 ==")
if net_rate >= 50:
    print(f"  duel 净胜率 {net_rate:.0f}% ≥ 50% → MVP 达标 ✅")
elif net_rate >= 20:
    print(f"  duel 净胜率 {net_rate:.0f}% (20-50%) → 接近, 需多攒局观察 ⚠️")
else:
    print(f"  duel 净胜率 {net_rate:.0f}% < 20% → 未达标, 需调整 duel reward ❌")
