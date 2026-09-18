# -*- coding: utf-8 -*-
"""A2 只读归因: 批次B 窗 contact 为何仍 0 + 红蓝位置轨迹实证
用法: python3 py/a2_contact_probe.py [窗口起始标记关键字, 默认最后一个 WIN1_BATCH]
只读 train_loop.log, 不碰训练。"""
import re, sys, io
from collections import defaultdict

LOG = '/mnt/d/Bigdata/hero3_fresh/train_loop.log'
MARK = sys.argv[1] if len(sys.argv) > 1 else 'WIN1_BATCH'

re_ep  = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[(.+?)\]\s+obs_nz=(\d+)\s+map=(\S+)')
re_grad = re.compile(r'\[BHERO_GRAD\] map=(\S+) grad_total=([-+\d.]+) cap=([-+\d.]+) '
                     r'final_min_d=(\S+) slain=(\[[^\]]*\]) contact=(\[[^\]]*\])')

# 1) 定位最后一个 MARK 行号
start_ln = 0
with io.open(LOG, encoding='utf-8', errors='replace') as f:
    for ln, line in enumerate(f, 1):
        if MARK in line:
            start_ln = ln

eps, grads, events = [], [], defaultdict(list)
banner_args = None
with io.open(LOG, encoding='utf-8', errors='replace') as f:
    for ln, line in enumerate(f, 1):
        if ln < start_ln:
            continue
        if 'env-injected runner args' in line and banner_args is None:
            banner_args = line.strip()
        m = re_ep.search(line)
        if m:
            eps.append(dict(ln=ln, steps=int(m.group(1)), r=float(m.group(2)),
                            mp=m.group(5)))
        m = re_grad.search(line)
        if m:
            d = m.group(4)
            grads.append(dict(ln=ln, mp=m.group(1), grad=float(m.group(2)),
                              md=None if d == 'None' else int(float(d)),
                              slain=m.group(5), contact=m.group(6)))
        for tag in ('BHERO_CONTACT', 'BHERO_KILL', 'TOWN_CAPTURE', 'TOWN_EMPTY',
                    '[GUARD] guard', 'HEROSEG_EMPTY', 'BattleStart'):
            if tag in line:
                events[tag].append((ln, line.strip()[:150]))

print(f'窗口起点: L{start_ln} (最后 {MARK})')
print(f'banner: {banner_args}')
print(f'ep 局数={len(eps)}  BHERO_GRAD 汇总行={len(grads)}')
print()
print('--- 每局 final_min_d (按时间) ---')
for g in grads:
    print(f'  L{g["ln"]:<7} md={str(g["md"]):>4} grad={g["grad"]:>5} '
          f'slain={g["slain"]} contact={g["contact"]}  {g["mp"]}')
mds = [g['md'] for g in grads if g['md'] is not None]
if mds:
    s = sorted(mds)
    p50 = s[len(s)//2]
    le2 = sum(1 for d in mds if d <= 2)
    print(f'\n非duel局={len(mds)}  min_d: min={s[0]} p50={p50} max={s[-1]}  d<=2 的局={le2}')
print()
print('--- 事件计数 ---')
for tag, lst in events.items():
    print(f'  {tag}: {len(lst)}')
print()
# duel vs 非duel 局 r 对照
by = defaultdict(list)
for e in eps:
    k = 'duel' if 'duel' in e['mp'] else ('T05' if e['mp'].startswith('T05') else '1v3/H3M')
    by[k].append(e['r'])
print('--- 分组 r ---')
for k, v in by.items():
    print(f'  {k:<9} n={len(v):<3} mean={sum(v)/len(v):.1f}')
# contact 样例
if events['BHERO_CONTACT']:
    print('\n--- BHERO_CONTACT 样例 ---')
    for ln, s in events['BHERO_CONTACT'][:5]:
        print(f'  L{ln}: {s}')
