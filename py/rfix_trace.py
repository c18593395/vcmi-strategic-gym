#!/usr/bin/env python3
"""最终判定: obs 权威态的 红 garrison + 红英雄 army 全轨迹 (招的兵到底进了哪)"""
import json

t = json.load(open("/tmp/rfix_out_1.json"))
obs = t.get("obs", [])
print(f"steps={len(obs)}")
# 红 town 槽: owner=0 的第一个
tb = None
o0 = obs[0]
for ti in range(8):
    b = 336 + ti * 18
    if int(o0[b + 1]) == 0 and (int(o0[b + 2]) > 0 or int(o0[b + 3]) > 0):
        tb = b
        print(f"red town id={int(o0[b])} pos=({int(o0[b+2])},{int(o0[b+3])})")
        break

prev = None
for s in range(len(obs)):
    o = obs[s]
    ah = int(o[3203])
    gar = tuple(int(o[tb + 6 + i]) for i in range(7)) if tb is not None else ()
    army = None
    if ah >= 0:
        hb = 128 + ah * 26
        army = tuple(int(o[hb + 15 + i]) for i in range(7))
    cur = (gar, army)
    if cur != prev:
        dead = " (hero dead)" if ah < 0 else ""
        print(f" step{s:3d} | garrison={list(gar)} hero_army={list(army) if army else None}{dead}")
        prev = cur
