#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""72_01_duel 战死解剖: 从主日志重建每局 RED_DEAD 前最后 12 拍的 [SCORE] pick 序列.

读 train_loop.log 最后 100 局窗口, 筛 72_01_duel 的 RED_DEAD 局,
逐局输出: r / steps / 死局前最后 N 个 SCORE pick (坐标/type/F/plen/是否同 pick 重复).
判读要点:
  - 同 pick 连续重复次数 (≥8 次 = 应触发 SCORE_BLACK 拉黑但未触发 → F 闸漏洞候选)
  - 死局前 pick 的 type (1=资源 2=守卫目标 3=英雄?) 与 F 值 (F<-0.2 = 打不过还踩)
  - min_d / contact 是否出现 (贴脸战死 vs 游走战死)
用法: wsl bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/anatomy_72_01_duel.py"
      (START 行号随窗滚动, 先 grep 定位最后 100 局起点)
"""
import os
import re
import collections

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
START = 152775          # 最后 100 局窗口起点 (行号 1-based), 跑前先重定位
TARGET = "T06_adventure_72X72_01_duel.vmap"
TAIL_N = 12            # 死局前回看 SCORE 拍数

lines = open(LOG, errors="replace").readlines()
seg = lines[START - 1:]

# 定位该图全部 EP_TIME 行; 每局块 = [上一局 EP_TIME 行, 本局 EP_TIME 行]
ep_lines = [i for i, ln in enumerate(seg, start=START) if f"[EP_TIME] map={TARGET}" in ln]
blocks = []
prev = START
for ep_line in ep_lines:
    blocks.append((prev, ep_line))
    prev = ep_line

# 死局时刻: RED_DEAD 行内的 "end ep at step N"
# 每局块的 SCORE pick 队列 (保留顺序, 取死局步前最后 TAIL_N 拍)
score_re = re.compile(
    r"\[SCORE\] pick=\((\d+),(\d+)\) type=(\d+) score=([\d.]+) plen=(\d+) V=(\d+) F=(-?[\d.]+) .*?at step (\d+)")
blk_picks = [collections.deque(maxlen=TAIL_N) for _ in blocks]
blk_step = [None] * len(blocks)   # 每局 RED_DEAD 步 (无则 = 满步)
for (b, e), q in zip(blocks, blk_picks):
    for ln in seg[b - START: e - START]:
        m = score_re.search(ln)
        if m:
            x, y, tp, sc, plen, v, f, st = m.groups()
            q.append((int(st), x, y, tp, float(sc), int(plen), int(v), float(f)))
        md = re.search(r"\[RED_DEAD\].*end ep at step (\d+)", ln)
        if md:
            blk_step[blk_picks.index(q)] = int(md.group(1))

print(f"图={TARGET} 总 {len(blocks)} 局, 战死局逐局解剖 (回看 {TAIL_N} 拍 SCORE):")
print("=" * 100)
n_cases = 0
for blk_i, ((b, e), q) in enumerate(zip(blocks, blk_picks)):
    blk_txt = "".join(seg[b - START: e - START])
    if "[RED_DEAD]" not in blk_txt:
        continue
    n_cases += 1
    epm = re.search(r"\[EP_TIME\] map=\S+ steps=(\d+) secs=\d+ r=(-?[\d.]+)", blk_txt)
    steps, r = epm.group(1), epm.group(2)
    rd_step = blk_step[blk_i]
    picks = list(q)
    print(f"\n-- 战死#{n_cases} 行 {b}..{e} EP_TIME steps={steps} r={r} RED_DEAD@step{rd_step}")
    if rd_step is not None:
        kept = [p for p in picks if p[0] <= rd_step][-TAIL_N:]
    else:
        kept = picks
    print(f"   死局前最后 {len(kept)} 拍 SCORE pick (step/pick):")
    cnt = collections.Counter()
    for i, (st, x, y, tp, sc, plen, v, f) in enumerate(kept, 1):
        key = f"({x},{y})"
        cnt[key] += 1
        flag = "  ←RED_DEAD 后" if st > rd_step else ""
        print(f"   {i:2d}. step={st:4d} pick={key:10s} type={tp} score={sc:6.1f} plen={plen:3d} V={v:3d} F={f:5.2f}{flag}")
    dup = {k: c for k, c in cnt.items() if c >= 3}
    if dup:
        print(f"   !! 高频 pick: {dup} (≥8 次将触发 SCORE_BLACK 拉黑)")
print(f"\n共 {n_cases} 局战死 / {len(blocks)} 局")
