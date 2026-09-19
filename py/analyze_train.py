#!/usr/bin/env python3
"""训练日志分析脚本 — 从 train.log 提取指标,按 Loaded train state 分段"""
import re, sys, os
from collections import Counter

def resolve_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for p in ["/mnt/d/Bigdata/hero3_fresh/train.log",
              "D:/Bigdata/hero3_fresh/train.log",
              "C:/Bigdata/hero3_fresh/train.log"]:
        if os.path.exists(p):
            return p
    return "/mnt/d/Bigdata/hero3_fresh/train.log"

LOG_PATH = resolve_path()

def parse_log(path):
    """返回 (runs, episodes)。runs: [{start_step, end_step, ep_lo, ep_hi}],
    episodes: [{run, steps, r, acts, avg_r, kl, klc, step, time}]"""
    runs = []
    episodes = []
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    cur_run = 0
    m_load = re.compile(r'Loaded train state.*step=(\d+)')
    m_ep = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]')
    m_train = re.compile(r'\s*step\s*(\d+)\s+avg_r=([-\d.]+)\s+vloss=([-\d.]+)\s+loss=([-\d.]+)\s+kl=([-\d.]+)\s+klc=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')
    m_step = re.compile(r'\s*step\s*(\d+)\s+avg_r=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s')

    for line in lines:
        line = line.strip()
        ml = m_load.match(line)
        if ml:
            runs.append({'start_step': int(ml.group(1)), 'end_step': None,
                         'ep_lo': len(episodes) + 1, 'ep_hi': None})
            cur_run = len(runs) - 1
            continue
        me = m_ep.match(line)
        if me:
            episodes.append({
                'run': cur_run,
                'steps': int(me.group(1)),
                'r': float(me.group(2)),
                'acts': [int(x.strip()) for x in me.group(3).split(',')],
                'avg_r': None, 'kl': None, 'klc': None, 'step': None, 'time': None
            })
            continue
        if not episodes:
            continue
        ep = episodes[-1]
        mt = m_train.match(line)
        if mt:
            ep['step'] = int(mt.group(1))
            ep['avg_r'] = float(mt.group(2))
            ep['kl'] = float(mt.group(5))
            ep['klc'] = float(mt.group(6))
            ep['time'] = int(mt.group(8))
            continue
        ms = m_step.match(line)
        if ms:
            ep['step'] = int(ms.group(1))
            ep['avg_r'] = float(ms.group(2))
            ep['time'] = int(ms.group(4))

    # 回填 run 段的 ep_hi / end_step
    for i, r in enumerate(runs):
        if i < len(runs) - 1:
            r['ep_hi'] = runs[i+1]['ep_lo'] - 1
        else:
            r['ep_hi'] = len(episodes)
        for e in reversed(episodes):
            if e['run'] == i and e['step'] is not None:
                r['end_step'] = e['step']
                break
    return runs, episodes

def summarize(runs, episodes):
    n = len(episodes)
    pos = [e for e in episodes if e['r'] > 0]
    neg = [e for e in episodes if e['r'] <= 0]
    print(f"{'='*64}")
    print(f"Total: {n} episodes, {len(pos)} positive ({100*len(pos)/n:.0f}%), {len(neg)} negative")
    rs = [e['r'] for e in episodes]
    print(f"Reward: min={min(rs):.1f}, max={max(rs):.1f}, mean={sum(rs)/n:.1f}")
    avg_rs = [e['avg_r'] for e in episodes if e['avg_r'] is not None]
    if avg_rs:
        print(f"Avg_r: min={min(avg_rs):.1f}, max={max(avg_rs):.1f}, last={avg_rs[-1]:.1f}")
    klcs = [e['klc'] for e in episodes if e['klc'] is not None]
    if klcs:
        sat = sum(1 for k in klcs if k >= 9.0)
        print(f"klc saturation: {sat}/{len(klcs)} ({100*sat/len(klcs):.0f}%), klc mean={sum(klcs)/len(klcs):.1f}")

    # 按 run 分段
    print(f"\n{'RUN段统计':-^64}")
    for i, r in enumerate(runs):
        seg = [e for e in episodes if e['run'] == i]
        if not seg:
            continue
        sp = sum(1 for e in seg if e['r'] > 0)
        srs = [e['r'] for e in seg]
        s_avg = [e['avg_r'] for e in seg if e['avg_r'] is not None]
        last10 = seg[-10:]
        l10p = sum(1 for e in last10 if e['r'] > 0)
        avg_last = s_avg[-1] if s_avg else float('nan')
        print(f"Run{i+1}: step {r['start_step']}->{r['end_step']} | ep {r['ep_lo']}-{r['ep_hi']} "
              f"({len(seg)} ep) | 正r {sp}/{len(seg)} ({100*sp/len(seg):.0f}%) | "
              f"r mean={sum(srs)/len(srs):.1f} | 最近10ep正r {l10p}/10 | avg_r last={avg_last:.2f}")

    # 最近 10ep 窗口
    if n >= 10:
        tail = episodes[-10:]
        tp = sum(1 for e in tail if e['r'] > 0)
        print(f"\n最近10ep (ep{n-9}-{n}): 正r {tp}/10, "
              f"r mean={sum(e['r'] for e in tail)/10:.1f}")

    # 正局特征:是否都是短局
    pos_short = [e for e in pos if e['steps'] < 100]
    pos_full = [e for e in pos if e['steps'] >= 100]
    if pos:
        print(f"正局特征: 短局(<100步) {len(pos_short)}/{len(pos)}, 长局(>=100步) {len(pos_full)}/{len(pos)}")

    # 动作分布
    all_acts = []
    for e in episodes:
        all_acts.extend(e['acts'])
    if all_acts:
        counter = Counter(all_acts)
        total = len(all_acts)
        print(f"\nAction distribution ({total} total):")
        for a in sorted(counter.keys()):
            pct = 100 * counter[a] / total
            bar = "#" * int(pct / 2)
            print(f"  {a:>2}: {counter[a]:>4} ({pct:>5.1f}%) {bar}")

if __name__ == "__main__":
    runs, episodes = parse_log(LOG_PATH)
    summarize(runs, episodes)
