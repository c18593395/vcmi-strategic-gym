#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大负局归因解剖: 读 traj json 的 rew_audit 逐笔标签, 聚合各惩罚/奖励来源占比.

前置: ep_runner_one.py 需以 HOMM3_REWARD_AUDIT=1 运行 (默认关零开销),
  traj["rew_audit"] = [[step, tag, delta], ...] (cycle/act_loop_rep/act_loop_alt/act_loop_p3/
  move_reject/zigzag/roundtrip/red_dead/town_capture/kill_proxy/slain/slain_epilog/mine)。

用法:
  python py/neg_ep_anatomy.py [--traj /tmp/traj_ep.json] [--top 10]
输出:
  1) total 与 tag 合计对照 (未入账部分 = step_fixed + nk2 shaping + 事件奖励混合, "untraced")
  2) 各 tag 计数/合计/均值, 按绝对值降序
  3) 大负帧 top-N (step, r, 累计)
"""
import argparse
import json

p = argparse.ArgumentParser()
p.add_argument("--traj", default="/tmp/traj_ep.json")
p.add_argument("--top", type=int, default=10)
a = p.parse_args()

t = json.load(open(a.traj, errors="replace"))
rew = t.get("rew", [])
audit = t.get("rew_audit") or []
total = sum(float(x) for x in rew)

print(f"map={t.get('mapname','?')} steps={t.get('steps')} total_r={total:.1f} audit_entries={len(audit)}")
if not audit:
    print("无 rew_audit 数据 — 请以 HOMM3_REWARD_AUDIT=1 重跑该局")
    raise SystemExit(0)

agg = {}
for step, tag, delta in audit:
    d = agg.setdefault(tag, {"n": 0, "sum": 0.0})
    d["n"] += 1
    d["sum"] += delta

traced = sum(d["sum"] for d in agg.values())
untraced = total - traced
print(f"\n{'tag':16s} {'n':>5s} {'sum':>10s} {'avg':>8s}")
for tag, d in sorted(agg.items(), key=lambda kv: -abs(kv[1]["sum"])):
    print(f"{tag:16s} {d['n']:5d} {d['sum']:10.1f} {d['sum']/d['n']:8.2f}")
print(f"{'untraced(含nk2)':16s} {'-':>5s} {untraced:10.1f}   <- step_fixed(0.1×N) + nk2 shaping + 事件奖混合")

cum = 0.0
curve = []
for i, r in enumerate(rew):
    cum += float(r)
    curve.append((i, float(r), round(cum, 1)))
worst = sorted(curve, key=lambda x: x[2])[: a.top]
print(f"\n大负累计 top{a.top} (step, frame_r, cum):")
for st, r, c in worst:
    print(f"  step {st:3d} frame_r={r:8.2f} cum={c:9.1f}")
