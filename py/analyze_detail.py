#!/usr/bin/env python3
"""训练日志深度分析 - 晋级判据专用"""
import re, os, sys
from collections import Counter

LOG = r"D:\Bigdata\hero3_fresh\train_loop.log"
if len(sys.argv) > 1:
    LOG = sys.argv[1]

m_ep = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]\s+obs_nz=(\d+)')
m_train = re.compile(r'\s*step\s*(\d+)\s+avg_r=([-\d.]+)\s+vloss=([-\d.]+)\s+loss=([-\d.]+)\s+kl=([-\d.]+)\s+klc=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')
m_step = re.compile(r'\s*step\s*(\d+)\s+avg_r=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')

eps = []
train_rows = []
with open(LOG, encoding='utf-8', errors='replace') as f:
    for line in f:
        line = line.rstrip()
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
                'step': int(mt.group(1)),
                'avg_r': float(mt.group(2)),
                'vloss': float(mt.group(3)),
                'loss': float(mt.group(4)),
                'kl': float(mt.group(5)),
                'klc': float(mt.group(6)),
                'ep': int(mt.group(7)),
                'time': int(mt.group(8)),
            })
            continue
        ms = m_step.match(line.strip())
        if ms:
            # 回填到对应 ep
            ep_idx = int(ms.group(3)) - 1
            if 0 <= ep_idx < len(eps):
                eps[ep_idx]['step'] = int(ms.group(1))
                eps[ep_idx]['avg_r'] = float(ms.group(2))
                eps[ep_idx]['time'] = int(ms.group(4))

# 回填 train_rows 到 eps
for tr in train_rows:
    ep_idx = tr['ep'] - 1
    if 0 <= ep_idx < len(eps):
        eps[ep_idx].update(tr)

total = len(eps)
print(f"==== 总体: {total} episodes ====")

def pos_stats(subset, label):
    if not subset: return
    pos = [e for e in subset if e['r'] > 0]
    neg = [e for e in subset if e['r'] <= 0]
    r_vals = [e['r'] for e in subset]
    # 负局分类
    big_neg = [e for e in neg if e['r'] < -100]    # 超大惩罚（守矿失败/崩溃类）
    mid_neg = [e for e in neg if -100 <= e['r'] < 0]  # 一般负
    act10_ratios = []
    for e in subset:
        c = Counter(e['acts'])
        act10_ratios.append(c.get(10, 0) / len(e['acts']))
    r_gt20 = [e for e in pos if e['r'] >= 20]
    r_gt30 = [e for e in pos if e['r'] >= 30]
    r_gt40 = [e for e in pos if e['r'] >= 40]
    print(f"\n[{label}] n={len(subset)}")
    print(f"  正奖励率: {len(pos)}/{len(subset)} = {len(pos)/len(subset)*100:.1f}%  {'✅' if len(pos)/len(subset)>=0.65 else '⚠️'} (阈值65%)")
    print(f"  r mean = {sum(r_vals)/len(r_vals):.1f}  {'✅' if sum(r_vals)/len(r_vals)>=10 else '⚠️'} (阈值≥10)")
    print(f"  正局 r mean = {sum(e['r'] for e in pos)/len(pos):.1f}" if pos else "  正局 r mean = N/A")
    print(f"  正局分段: ≥20: {len(r_gt20)}局 / ≥30: {len(r_gt30)}局 / ≥40: {len(r_gt40)}局")
    print(f"  负局: 共{len(neg)}局 (大负<-100: {len(big_neg)}局, 小负: {len(mid_neg)}局)")
    if big_neg:
        bn = [e['r'] for e in big_neg]
        print(f"    大负 r: min={min(bn):.1f} max={max(bn):.1f} mean={sum(bn)/len(bn):.1f}")

for window in [(None, "全量"), (100, "最近100ep"), (50, "最近50ep"), (30, "最近30ep"), (10, "最近10ep")]:
    w, label = window
    sub = eps[-w:] if w else eps
    pos_stats(sub, label)

print(f"\n==== vloss / kl 训练指标趋势 ====")
if train_rows:
    n = len(train_rows)
    for w in (None, 20, 10, 5):
        sub = train_rows[-w:] if w else train_rows
        lbl = f"全部 {n} 个 ppo 更新点" if w is None else f"最近 {len(sub)} 个更新点 (ep{train_rows[-len(sub)]['ep']}-{train_rows[-1]['ep']})"
        vloss = [t['vloss'] for t in sub]
        kl = [t['kl'] for t in sub]
        avg_r_tr = [t['avg_r'] for t in sub]
        print(f"\n[{lbl}]")
        print(f"  vloss: mean={sum(vloss)/len(vloss):.3f}  first={vloss[0]:.3f} → last={vloss[-1]:.3f}  Δ={vloss[-1]-vloss[0]:+.3f}  {'下降✅' if vloss[-1] < vloss[0] else '上升⚠️'}")
        print(f"  kl:    mean={sum(kl)/len(kl):.3f}  first={kl[0]:.3f} → last={kl[-1]:.3f}  (klc=0.300恒定)")
        print(f"  avg_r: mean={sum(avg_r_tr)/len(avg_r_tr):.2f}  first={avg_r_tr[0]:.2f} → last={avg_r_tr[-1]:.2f}")

print(f"\n==== obs_nz(观测非零维度)分布 ====")
obs_counter = Counter(e['obs_nz'] for e in eps)
for k, v in sorted(obs_counter.items()):
    print(f"  {k}: {v}局 ({v/total*100:.1f}%)")

print(f"\n==== 晋级判据汇总 (Level 2 → 3) ====")
# 晋级要求：正奖励率≥65% & r mean≥10 & vloss 下降 （取最近50ep + 最近30ep 双窗口）
def judge(subset, name):
    if len(subset) < 20: return
    pos = [e for e in subset if e['r'] > 0]
    pr = len(pos)/len(subset)
    rm = sum(e['r'] for e in subset)/len(subset)
    ok1 = pr >= 0.65
    ok2 = rm >= 10
    print(f"  [{name} n={len(subset)}] 正奖励率={pr*100:.1f}% {'✅' if ok1 else '❌'} | r mean={rm:.1f} {'✅' if ok2 else '❌'} → {'通过🎉' if (ok1 and ok2) else '未通过⏳'}")

judge(eps[-50:], "最近50ep")
judge(eps[-30:], "最近30ep")
judge(eps[-20:], "最近20ep")
