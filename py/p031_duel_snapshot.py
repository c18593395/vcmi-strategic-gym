#!/usr/bin/env python3
"""P-031 duel 新窗时间桶 (部署 step>=1655053)"""
import re

STEP_NEW = 1655053
lines = []
with open("/DATA/hero3/train_server/train_full.log", encoding="utf-8", errors="ignore") as f:
    for ln in f:
        if "[SLOT]" not in ln or "duel" not in ln:
            continue
        m = re.search(r"step(\d+)", ln)
        a = re.search(r"avg_r=([0-9.-]+)", ln)
        if not m or not a:
            continue
        step = int(m.group(1))
        ar = float(a.group(1))
        lines.append((step, ar))

lines.sort(key=lambda x: x[0])
new = [l for l in lines if l[0] >= STEP_NEW]
print(f"duel 局总数={len(lines)}  新窗(>={STEP_NEW})={len(new)}")
if new:
    print(f"  首局: step={new[0][0]} avg_r={new[0][1]:.1f}")
    print(f"  末局: step={new[-1][0]} avg_r={new[-1][1]:.1f}")
    # 桶
    k = max(1, len(new) // 3)
    for i in range(3):
        seg = new[i * k:(i + 1) * k]
        if not seg:
            break
        s = sum(x[1] for x in seg) / len(seg)
        pos = sum(1 for x in seg if x[1] > 0) / len(seg) * 100
        print(f"  桶{i+1}: n={len(seg)} avg_r={s:.2f} 正局={pos:.0f}% step {seg[0][0]}~{seg[-1][0]}")
    # 前后对比
    first10 = [x[1] for x in new[:10]]
    last10 = [x[1] for x in new[-10:]]
    print(f"  前10局 avg_r={sum(first10)/len(first10):.2f}")
    print(f"  后10局 avg_r={sum(last10)/len(last10):.2f}")
else:
    # 看全量
    s = sum(x[1] for x in lines) / len(lines) if lines else 0
    print(f"  全量 avg_r={s:.2f} step 范围 {lines[0][0]}~{lines[-1][0]}")
