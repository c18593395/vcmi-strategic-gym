#!/usr/bin/env python3
"""v4 段深度核对 (resume marker 后段) — 用于验证用户判断
   特性：① 只取 "OPS-20260828-01 RESUME v4" 段以后 ② 算晋级窗口 + 用户给出的 98 局窗口匹配项
   ③ ZOMBIE / ENDTURN_FUSE 统计 ④ 前后段对比 (首半/后半) ⑤ batch 指标 近10更新点趋势
"""
import re, os
from collections import Counter

LOG = r"D:\Bigdata\hero3_fresh\train_loop.log"
MARKER_V4 = "OPS-20260828-01 RESUME v4"

m_ep = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]\s+obs_nz=(\d+)')
m_train = re.compile(r'\s*step\s*(\d+)\s+avg_r=([-\d.]+)\s+vloss=([-\d.]+)\s+loss=([-\d.]+)\s+kl=([-\d.]+)\s+klc=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')
m_step = re.compile(r'\s*step\s*(\d+)\s+avg_r=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')
m_zombie = re.compile(r'\[(ZOMBIE|ENDTURN_FUSE)\]\s*(.+?)\s*,\s*end ep at step\s+(\d+)')
m_load = re.compile(r'Loaded train state.*step=(\d+)')
m_banner = re.compile(r'WSL2 PPO v2.*maps=(\d+)')

lines_after_v4 = []
start_collect = False
with open(LOG, encoding='utf-8', errors='replace') as f:
    for line in f:
        if MARKER_V4 in line:
            start_collect = True
            lines_after_v4 = []
            continue
        if start_collect:
            lines_after_v4.append(line.rstrip())

print(f"==== v4 段日志行数: {len(lines_after_v4)} ====")
if not lines_after_v4:
    exit(0)

# (1) banner / loaded
for line in lines_after_v4[:20]:
    m = m_load.search(line);
    if m: print(f"(a) Loaded: step={m.group(1)}")
    m = m_banner.search(line)
    if m: print(f"(c) maps banner: maps={m.group(1)}")

# (2) parse ep / train_rows / zombies
eps = []
train_rows = []
zombies = []
for line in lines_after_v4:
    m = m_ep.search(line)
    if m:
        acts = [int(x.strip()) for x in m.group(3).split(',')]
        eps.append({
            'steps': int(m.group(1)),
            'r': float(m.group(2)),
            'acts': acts,
            'obs_nz': int(m.group(4)),
        })
        continue
    mt = m_train.match(line.strip())
    if mt:
        train_rows.append({
            'step': int(mt.group(1)), 'avg_r': float(mt.group(2)),
            'vloss': float(mt.group(3)), 'loss': float(mt.group(4)),
            'kl': float(mt.group(5)), 'klc': float(mt.group(6)),
            'ep': int(mt.group(7)), 'time': int(mt.group(8)),
        })
        continue
    ms = m_step.match(line.strip())
    if ms:
        idx = int(ms.group(3)) - 1
        if 0 <= idx < len(eps):
            eps[idx]['step'] = int(ms.group(1))
            eps[idx]['avg_r'] = float(ms.group(2))
            eps[idx]['time'] = int(ms.group(4))
        continue
    mz = m_zombie.search(line)
    if mz:
        zombies.append({'type': mz.group(1), 'detail': mz.group(2).strip(), 'end_step': int(mz.group(3))})

# 回填
for tr in train_rows:
    idx = tr['ep'] - 1
    if 0 <= idx < len(eps):
        eps[idx].update(tr)

n = len(eps)
print(f"\n==== v4 段共 {n} episodes ====")
if n == 0:
    exit(0)

# (A) 每局步数
steps_dist = Counter(e['steps'] for e in eps)
print(f"\n[A] 每局步数分布: {dict(sorted(steps_dist.items()))}")
full200 = steps_dist.get(200, 0)
print(f"    满 200 步占比: {full200}/{n} = {full200/n*100:.1f}%  {'✅ 用户判断(全满步)' if full200 == n else '⚠️ (用户说全满步，但实际有<200截断)'}")
# <200 局列表
short = [(i+1, e['steps'], e['r']) for i,e in enumerate(eps) if e['steps'] < 200]
if short:
    print(f"    截断局 (ep_local#, steps, r): {short[:20]}  {'... total '+str(len(short)) if len(short)>20 else ''}")

# (B) r 值分析
rs = [e['r'] for e in eps]
pos = [e for e in eps if e['r'] > 0]
neg = [e for e in eps if e['r'] < 0]
zero = [e for e in eps if e['r'] == 0]
print(f"\n[B] r 值分布:")
print(f"    r: min={min(rs):.2f}  max={max(rs):.2f}  mean={sum(rs)/len(rs):.2f}")
print(f"    正局: {len(pos)}/{n} = {len(pos)/n*100:.1f}%   负局: {len(neg)}/{n} = {len(neg)/n*100:.1f}% (min={min([e['r'] for e in neg]):.2f})   零局: {len(zero)}/{n} = {len(zero)/n*100:.1f}%")
# 前半 vs 后半
mid = n//2
first, second = eps[:mid], eps[mid:]
r1, r2 = sum(e['r'] for e in first)/len(first), sum(e['r'] for e in second)/len(second)
print(f"    前半(ep1~{mid}): mean r = {r1:.2f}")
print(f"    后半(ep{mid+1}~{n}): mean r = {r2:.2f}   {'↑改善' if r2>r1 else '↓退化'} by {r2-r1:+.2f}")
# 正收益尖峰 (top 10)
top = sorted(eps, key=lambda x: -x['r'])[:10]
print(f"    Top10 r: {[(i+1, round(e['r'],2)) for i,e in enumerate(top)]}")

# (C) obs_nz
print(f"\n[C] obs_nz 分布 (应该只有 T03 20×20 的两张图):")
c_nz = Counter(e['obs_nz'] for e in eps)
for k,v in sorted(c_nz.items()):
    print(f"    {k}: {v}局 ({v/n*100:.1f}%)")

# (D) 动作开局序列
print(f"\n[D] 开局前 8 动作 top 分布（验证「高度固定」）:")
open8 = Counter(tuple(e['acts'][:8]) for e in eps if len(e['acts']) >= 8)
for seq, cnt in open8.most_common(5):
    print(f"    {list(seq)}: {cnt}/{n} = {cnt/n*100:.1f}%")
act_counter_overall = Counter()
for e in eps:
    act_counter_overall.update(e['acts'])
tot_a = sum(act_counter_overall.values())
print(f"    全段动作占比 (TOP6): {[(a, f'{c/tot_a*100:.1f}%') for a,c in act_counter_overall.most_common(6)]}")

# (E) ZOMBIE / ENDTURN_FUSE 事件
print(f"\n[E] Zombie / Fuse 事件: {len(zombies)} 条")
for z in zombies:
    print(f"    [{z['type']}] end_step={z['end_step']}  details: {z['detail']}")
if zombies:
    print(f"    对应本地 ep# 近似 (按end_step推断): ", end='')
    ep_steps_cum = 0
    matched = []
    for i,e in enumerate(eps):
        ep_steps_cum += e['steps']
        for z in zombies:
            if e['steps'] < 200 and z['end_step'] == e['steps'] and (i+1) not in matched:
                matched.append(i+1); break
    print(matched if matched else '(无精确匹配，参考)')
    print(f"    近段频率: 98局里{len(zombies)}条 = {len(zombies)/n*100:.1f}%")

# (F) 优化指标 (最近10个 ppo 更新点)
print(f"\n[F] 优化指标 (v4 段 ppo 更新点共 {len(train_rows)} 个):")
if train_rows:
    last10 = train_rows[-10:]
    vlosses = [t['vloss'] for t in last10]
    kls    = [t['kl']    for t in last10]
    avgs   = [t['avg_r'] for t in last10]
    ep_last = [t['ep'] for t in last10]
    def q(xs, p):
        s = sorted(xs); idx = int(len(s) * p); return s[min(idx, len(s)-1)]
    print(f"  近10更新点 ep范围: ep{ep_last[0]} → ep{ep_last[-1]}")
    print(f"  vloss: 最小值={min(vlosses):.3f} q25={q(vlosses,.25):.3f} q50={q(vlosses,.5):.3f} q75={q(vlosses,.75):.3f} 最大值={max(vlosses):.3f}   first={vlosses[0]:.3f}→last={vlosses[-1]:.3f}  Δ={vlosses[-1]-vlosses[0]:+.3f}")
    print(f"  kl:    min={min(kls):.3f}  mean={sum(kls)/len(kls):.3f}  max={max(kls):.3f}  (klc={last10[0]['klc']}恒定)")
    print(f"  avg_r: min={min(avgs):.2f}  mean={sum(avgs)/len(avgs):.2f}  max={max(avgs):.2f}")
    # 30 更新点趋势
    if len(train_rows) >= 5:
        for wl in [30, 20, 10]:
            seg = train_rows[-wl:] if len(train_rows) >= wl else train_rows
            vv = [t['vloss'] for t in seg]
            print(f"  近{len(seg)}更新点 vloss: {vv[0]:.3f} → {vv[-1]:.3f}  Δ={vv[-1]-vv[0]:+.3f}  {'下降✅' if vv[-1]<vv[0] else '上升⚠️'}")

# (G) 晋级判据窗口 (v4 段内所有窗口)
print(f"\n[G] 晋级判据窗口汇总 (要求 正奖励率≥65% AND r mean≥10):")
def judge(sub, name):
    if len(sub) < 10: return
    pp = [e for e in sub if e['r'] > 0]
    pr = len(pp)/len(sub)
    rm = sum(e['r'] for e in sub)/len(sub)
    ok1 = pr >= .65; ok2 = rm >= 10
    big = [e for e in sub if e['r'] < -100]
    print(f"  [{name:>10s} n={len(sub):>3d}] 正奖励率={pr*100:>5.1f}% {'✅' if ok1 else '❌'}  r mean={rm:>+6.2f} {'✅' if ok2 else '❌'}  大负<-100={len(big)} → {'🎉通过' if (ok1 and ok2) else '⏳未通过'}")
for w,name in [(10,'近10'),(20,'近20'),(30,'近30'),(50,'近50'),(n,'v4全段')]:
    judge(eps[-w:], name)

print("\n==== end ====")
