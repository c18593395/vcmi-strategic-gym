#!/usr/bin/env python3
"""大负局根因分析：act 10 连喷(守矿守卫战斗) vs 其他"""
import re, sys
from collections import Counter

LOG = r"D:\Bigdata\hero3_fresh\train_loop.log"
m_ep = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]\s+obs_nz=(\d+)')

eps = []
with open(LOG, encoding='utf-8', errors='replace') as f:
    for line in f:
        m = m_ep.search(line)
        if m:
            acts = [int(x.strip()) for x in m.group(3).split(',')]
            eps.append({'r': float(m.group(2)), 'acts': acts, 'obs_nz': int(m.group(4))})

big = [e for e in eps if e['r'] < -100]
small_neg = [e for e in eps if -100 <= e['r'] <= 0]
pos = [e for e in eps if e['r'] > 0]

def analyze(subset, name):
    if not subset: return
    print(f"\n=== {name} (n={len(subset)}) ===")
    # 计算每个局的 act 10 连续段最长长度和占比
    def max_run(acts, a):
        cur, mx = 0, 0
        for x in acts:
            if x == a:
                cur += 1
                mx = max(mx, cur)
            else:
                cur = 0
        return mx
    a10_runs = [max_run(e['acts'], 10) for e in subset]
    a10_ratios = [Counter(e['acts']).get(10,0)/len(e['acts']) for e in subset]
    # act=4 也是守矿相关（触发守卫），与10配对
    a4_runs = [max_run(e['acts'], 4) for e in subset]
    a4a10_ratios = [(Counter(e['acts']).get(4,0)+Counter(e['acts']).get(10,0))/len(e['acts']) for e in subset]

    # 分类：act10 连续≥10 或 占比≥25% → 守矿守卫战斗失败型
    type_guard = []
    type_other = []
    for e, run10, rat10 in zip(subset, a10_runs, a10_ratios):
        if run10 >= 10 or rat10 >= 0.25:
            type_guard.append(e)
        else:
            type_other.append(e)
    r_g = [e['r'] for e in type_guard]
    r_o = [e['r'] for e in type_other]
    print(f"  守矿战斗失败型(act10占比≥25%或连续≥10): {len(type_guard)}/{len(subset)} ({len(type_guard)/len(subset)*100:.0f}%)  r mean={sum(r_g)/len(r_g):.1f}" if type_guard else "  守矿战斗失败型: 0")
    print(f"  其他类型: {len(type_other)}/{len(subset)}  r mean={sum(r_o)/len(r_o):.1f}" if type_other else "  其他类型: 0")
    print(f"  act10 最长连喷: min={min(a10_runs)} max={max(a10_runs)} mean={sum(a10_runs)/len(a10_runs):.1f}")
    print(f"  act10 占比: min={min(a10_ratios)*100:.0f}% max={max(a10_ratios)*100:.0f}% mean={sum(a10_ratios)/len(a10_ratios)*100:.0f}%")
    print(f"  act4+10(守矿链)占比: mean={sum(a4a10_ratios)/len(a4a10_ratios)*100:.0f}%")

analyze(big, "大负局 (r<-100, 即守矿崩溃惩罚)")
analyze(small_neg, "小负局 (-100≤r≤0)")
analyze(pos, "正奖励局 (r>0)")

# 大负局按 obs_nz 分布（obs_nz 不同=地图不同）
print("\n=== 大负局 obs_nz(地图) 分布 ===")
c = Counter(e['obs_nz'] for e in big)
# 对应全体分布
c_all = Counter(e['obs_nz'] for e in eps)
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print(f"  obs_nz={k}: 大负{v}局 / 全体{c_all[k]}局 = {v/c_all[k]*100:.0f}%")
