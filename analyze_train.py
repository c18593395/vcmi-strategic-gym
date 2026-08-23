#!/usr/bin/env python3
"""训练日志分析脚本 — 从 train.log 提取指标"""
import re, sys, os
from collections import Counter

LOG_PATH = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/train.log"

def parse_log(path):
    episodes = []
    with open(path) as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Match: ep_steps=200 r=-97.70 act=[...]
        m_ep = re.match(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]', line)
        # Match: step XXXX avg_r=X.X ep=N time=Ns
        m_step = re.match(r'step\s+(\d+)\s+avg_r=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s', line)
        # Match: step XXXX avg_r=X.X vloss=X loss=X kl=X.XXX klc=X.XXX ep=N time=Ns
        m_train = re.match(r'step\s+(\d+)\s+avg_r=([-\d.]+)\s+vloss=([-\d.]+)\s+loss=([-\d.]+)\s+kl=([-\d.]+)\s+klc=([-\d.]+)\s+ep=(\d+)\s+time=(\d+)s', line)
        
        if m_ep:
            steps = int(m_ep.group(1))
            r = float(m_ep.group(2))
            acts = [int(x.strip()) for x in m_ep.group(3).split(',')]
            episodes.append({
                'steps': steps, 'r': r, 'acts': acts,
                'avg_r': None, 'kl': None, 'klc': None, 'step': None, 'time': None
            })
        elif m_train and episodes:
            ep = episodes[-1]
            ep['step'] = int(m_train.group(1))
            ep['avg_r'] = float(m_train.group(2))
            ep['kl'] = float(m_train.group(5))
            ep['klc'] = float(m_train.group(6))
            ep['time'] = int(m_train.group(8))
        elif m_step and episodes:
            ep = episodes[-1]
            if ep['avg_r'] is None:
                ep['step'] = int(m_step.group(1))
                ep['avg_r'] = float(m_step.group(2))
                ep['time'] = int(m_step.group(4))
        i += 1
    return episodes

def analyze(episodes):
    if not episodes:
        print("No episodes found.")
        return
    
    n = len(episodes)
    pos = [e for e in episodes if e['r'] > 0]
    neg = [e for e in episodes if e['r'] <= 0]
    
    # Per-episode table
    print(f"{'ep':>4} {'steps':>5} {'r':>8} {'avg_r':>6} {'kl':>6} {'klc':>6} {'acts':>5} {'flag':>4}")
    print("-" * 60)
    for i, e in enumerate(episodes):
        flag = "+" if e['r'] > 0 else ""
        kl_s = f"{e['kl']:.3f}" if e['kl'] is not None else "—"
        klc_s = f"{e['klc']:.1f}" if e['klc'] is not None else "—"
        avg_s = f"{e['avg_r']:.1f}" if e['avg_r'] is not None else "—"
        print(f"{i+1:>4} {e['steps']:>5} {e['r']:>8.1f} {avg_s:>6} {kl_s:>6} {klc_s:>6} {len(e['acts']):>5} {flag:>4}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Total: {n} episodes, {len(pos)} positive ({100*len(pos)/n:.0f}%), {len(neg)} negative")
    
    rs = [e['r'] for e in episodes]
    print(f"Reward: min={min(rs):.1f}, max={max(rs):.1f}, mean={sum(rs)/n:.1f}")
    
    avg_rs = [e['avg_r'] for e in episodes if e['avg_r'] is not None]
    if avg_rs:
        print(f"Avg_r: min={min(avg_rs):.1f}, max={max(avg_rs):.1f}, last={avg_rs[-1]:.1f}")
    
    # klc saturation
    klcs = [e['klc'] for e in episodes if e['klc'] is not None]
    if klcs:
        sat = sum(1 for k in klcs if k >= 9.0)
        print(f"klc saturation: {sat}/{len(klcs)} ({100*sat/len(klcs):.0f}%)")
        print(f"klc: min={min(klcs):.1f}, max={max(klcs):.1f}, mean={sum(klcs)/len(klcs):.1f}")
    
    # Action distribution
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
    
    # Positive episodes detail
    if pos:
        print(f"\nPositive episodes:")
        for e in pos:
            avg_val = f"{e['avg_r']:.1f}" if e['avg_r'] is not None else "—"
            print(f"  ep{episodes.index(e)+1}: r={e['r']:.1f}, steps={e['steps']}, avg_r={avg_val}")
    
    # Sliding window positive rate (10-ep window)
    if n >= 10:
        print(f"\nSliding 10-ep positive rate:")
        for i in range(9, n):
            window = episodes[i-9:i+1]
            p = sum(1 for e in window if e['r'] > 0)
            print(f"  ep{i-8:>3}-{i+1:>3}: {p}/10 = {10*p}%", end="")
            if p >= 5:
                print(" <<<", end="")
            print()

if __name__ == "__main__":
    episodes = parse_log(LOG_PATH)
    analyze(episodes)
