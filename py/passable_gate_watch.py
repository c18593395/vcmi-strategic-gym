#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""passable 闸门（方案甲）4 判据验证看板。只读 train_loop.log，窗起点 = 最后一条 WIN1_BATCH 行。
判据: ① passable 新口径不炸(无 moveHero 全拒/#143 复发) ② 首个真实战斗事件 ③ BHERO_KILL 非零 ④ 死亡局占比<20% + avg_r 无塌
"""
import re
import statistics

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
lines = open(LOG, errors="replace").readlines()
start = max(i for i, l in enumerate(lines, 1) if "WIN1_BATCH" in l)
seg = lines[start:]
j = "".join(seg)
print(f"== 窗起点 L={start} / 全文 {len(lines)} 行, 段内 {len(seg)} 行 ==")
print("[窗起点行] " + lines[start - 1].strip()[:200])

# 信号计数
for tag in ["BHERO_CONTACT", "BHERO_KILL", "ZOMBIE", "ENDTURN_FUSE", "TOWN_VISIT", "TOWN_EMPTY", "START_HOME"]:
    print(f"{tag}: {len(re.findall(tag, j))}")

# 判据①: 不炸 = 局正常完结 (EP_TIME err=no)
eps = re.findall(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\w+)", j)
errs = [e for e in eps if e[4] != "no"]
print(f"\n== 判据① 不炸 == 完结局数={len(eps)} err!=no={len(errs)}")
for e in errs[:5]:
    print("  ERR局:", e)

# 判据④: 死亡局占比 + avg_r 无塌
rs = [float(e[3]) for e in eps]
if rs:
    neg = [r for r in rs if r < 0]
    dead = [r for r in rs if r <= -100]
    print("\n== 判据④ 死亡局/通胀 ==")
    print(f"r: mean={statistics.mean(rs):.1f} median={statistics.median(rs):.1f} min={min(rs):.1f} max={max(rs):.1f}")
    print(f"负局 {len(neg)}/{len(rs)}; r<=-100 局 {len(dead)}/{len(rs)} = {100 * len(dead) / len(rs):.0f}% (判据<20%)")
avg = re.findall(r"step(\d+) avg_r=(-?[\d.]+) ep=(\d+)", j)
print("avg_r 序列:", " ".join(f"ep{a[2]}:{a[1]}@{a[0]}" for a in avg))

# 判据②③: BHERO_GRAD 明细 (min_d 走低 + slain 非空)
grads = re.findall(r"\[BHERO_GRAD\] map=(\S+) grad_total=(-?[+\d.]+) cap=([\d.]+) final_min_d=(\d+) slain=\[([^\]]*)\] contact=\[([^\]]*)\]", j)
print(f"\n== 判据②③ BHERO_GRAD {len(grads)} 局 (对照批次B首窗 min_d=[14,37,42,48,48,50,60,60,96]) ==")
mind = [int(g[3]) for g in grads]
if mind:
    print(f"min_d: p50={statistics.median(mind):.0f} min={min(mind)} max={max(mind)}")
    print(f"min_d 序列={mind}")
kill = [g for g in grads if g[4].strip()]
contact = [g for g in grads if g[5].strip()]
print(f"slain 非空局: {len(kill)}; contact 非空局: {len(contact)}")
for g in kill:
    print(f"  SLAIN: {g[0]} slain=[{g[4]}] contact=[{g[5]}]")
for g in contact:
    print(f"  CONTACT: {g[0]} contact=[{g[5]}] min_d={g[3]}")

# 行为证据: passable 解锁后模型敢选蓝英雄方向
bh = len(re.findall(r"type=blue_hero", j))
mine = len(re.findall(r"\[MINE\]", j))
print(f"\n== 行为证据 == [SCORE] type=blue_hero pick: {bh} 次; [MINE] captured: {mine}")

# 大负局上下文 (死亡局定性: 红败信号 or ZOMBIE)
print("\n== 大负局 (r<=-100) 上下文 ==")
for i, l in enumerate(seg):
    m = re.search(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-[\d.]+) err=no", l)
    if m and float(m.group(4)) <= -100:
        print(f"--- {l.strip()}")
        for k in range(max(0, i - 8), i + 1):
            t = seg[k].strip()
            if any(x in t for x in ["BHERO", "TOWNSTALL", "DEFEAT", "defeat", "ENDTURN", "ZOMBIE", "ep_steps", "GOAL"]):
                print("   ", t[:160])
