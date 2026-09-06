#!/usr/bin/env python3
"""duel 观察窗统计 (09-06): 自发经济 / 200 步局占比 / r 与步数分布, T05 同口径对照

口径:
- 数据源 = train_loop.log 的 ep_steps= 行 (含 act=[...] / obs_nz / map=)
- 自发经济 = act 序列中 index>=24 (economy_force 24 步强制窗外) 的 16-21 动作
- 200 步局 = ep_steps=200 (truncation)
"""
import re, sys
from collections import defaultdict

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 200  # 最近 N 个 ep 行

pat = re.compile(
    r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]+)\] obs_nz=(\d+) map=(\S+)"
)

stats = defaultdict(lambda: {"n": 0, "r": [], "steps": [], "spont_eps": 0,
                             "spont_total": 0, "obs_nz": set()})
rows = []
with open(LOG, errors="replace") as f:
    for line in f:
        if "ep_steps=" in line and "map=" in line:
            rows.append(line)

for line in rows[-WINDOW:]:
    m = pat.search(line)
    if not m:
        continue
    steps, r, acts, nz, mp = m.groups()
    acts = [int(x) for x in acts.split(",") if x.strip()]
    s = stats[mp]
    s["n"] += 1
    s["r"].append(float(r))
    s["steps"].append(int(steps))
    s["obs_nz"].add(nz)
    spont = sum(1 for i, a in enumerate(acts) if i >= 24 and 16 <= a <= 21)
    s["spont_total"] += spont
    if spont > 0:
        s["spont_eps"] += 1

total = sum(s["n"] for s in stats.values())
print(f"=== 最近 {total} ep (train_loop.log 尾窗) ===\n")
print(f"{'map':<36}{'局数':>4}{'avg_r':>8}{'r范围':>16}{'200步局':>8}{'自发局':>6}{'自发次':>7}  obs_nz")
for mp, s in sorted(stats.items()):
    n = s["n"]
    t200 = sum(1 for x in s["steps"] if x >= 200)
    avg = sum(s["r"]) / n
    print(f"{mp:<36}{n:>4}{avg:>8.1f}{min(s['r']):>8.1f}~{max(s['r']):<7.1f}"
          f"{t200:>5}({t200*100//n}%){s['spont_eps']:>5}{s['spont_total']:>7}  {sorted(s['obs_nz'])}")

duel = [mp for mp in stats if "duel" in mp]
if duel:
    s = stats[duel[0]]
    n = s["n"]
    t200 = sum(1 for x in s["steps"] if x >= 200)
    print(f"\n=== duel 专项 ===")
    print(f"局数={n} 200步局={t200} ({t200*100/max(n,1):.0f}%) 自发经济={s['spont_eps']}/{n} 局 {s['spont_total']} 次")
    print(f"r 分布: {[round(x,1) for x in sorted(s['r'])]}")
else:
    print("\nduel 局尚未出现在尾窗 (7 图轮换, 等待)")
