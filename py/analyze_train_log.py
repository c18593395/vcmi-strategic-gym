#!/usr/bin/env python
# 分析 train_loop.log: ent 趋势 / avg_r 分布 / 地图表现 / 异常事件
import re, sys, json
from collections import defaultdict, deque

LOG = sys.argv[1] if len(sys.argv) > 1 else r"D:\Bigdata\hero3_fresh\train_loop.log"

# --- 第一遍: 收集指标行 ---
step_avg_r = []          # (step, ep, avg_r)
ent_lines = []           # 完整 ent 行 (含 loss/kl/ent)
ep_time = []             # (map, steps, secs, r)
zombie_lines = []
fuse_lines = []
shutdown_lines = []
score_lines = []         # (step, type, score)

RE_STEP = re.compile(r"step(\d+) avg_r=([-\d.]+) ep=(\d+)")
RE_STEP_FULL = re.compile(r"step(\d+) avg_r=([-\d.]+) vloss=([\d.]+) loss=([\d.]+) kl=([\d.]+) klc=([\d.]+) ep=(\d+) time=(\d+)s( entc=([\d.]+) ent=([\d.]+))?")
RE_EP_TIME = re.compile(r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=([-\d.]+)")
RE_ZOMBIE = re.compile(r"\[ZOMBIE\]")
RE_FUSE = re.compile(r"\[ENDTURN_FUSE\]")
RE_SHUTDOWN = re.compile(r"Shutdown signal received, saving current state")
RE_SCORE = re.compile(r"\[SCORE\] pick=\((\d+),(\d+)\) type=(\S+) score=([-\d.]+)")

with open(LOG, encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        m = RE_STEP_FULL.search(line)
        if m:
            step_avg_r.append((int(m.group(1)), int(m.group(7)), float(m.group(2)), m.group(9), m.group(10)))
            if m.group(9):
                ent_lines.append((int(m.group(1)), int(m.group(7)), m.group(3), m.group(4), m.group(5), m.group(6), m.group(9), m.group(10), i))
        else:
            m2 = RE_STEP.search(line)
            if m2:
                step_avg_r.append((int(m2.group(1)), int(m2.group(3)), float(m2.group(2)), None, None))
        me = RE_EP_TIME.search(line)
        if me:
            ep_time.append((me.group(1), int(me.group(2)), int(me.group(3)), float(me.group(4))))
        if RE_ZOMBIE.search(line):
            zombie_lines.append((i, line.strip()))
        if RE_FUSE.search(line):
            fuse_lines.append((i, line.strip()))
        if RE_SHUTDOWN.search(line):
            shutdown_lines.append(i)
        ms = RE_SCORE.search(line)
        if ms:
            score_lines.append((ms.group(3), float(ms.group(4))))

print(f"总行数: {i}")
print(f"step 指标行: {len(step_avg_r)} | 含ent行: {len(ent_lines)} | EP_TIME行: {len(ep_time)}")
print(f"ZOMBIE: {len(zombie_lines)} | ENDTURN_FUSE: {len(fuse_lines)} | Shutdown: {len(shutdown_lines)}")
if shutdown_lines:
    print(f"Shutdown 行号范围: {min(shutdown_lines)} ~ {max(shutdown_lines)}")

# --- avg_r 趋势 (按 step 分桶) ---
print("\n===== avg_r 趋势 (按 500 ep 桶) =====")
buckets = defaultdict(list)
for step, ep, r, _, _ in step_avg_r:
    buckets[ep // 500 * 500].append(r)
for b in sorted(buckets):
    vs = buckets[b]
    pos = sum(1 for x in vs if x > 0)
    print(f"ep {b:>4}-{b+499:<4}: n={len(vs):>4}  mean={sum(vs)/len(vs):+.3f}  pos_rate={pos/len(vs)*100:.0f}%")

# --- 最近 500 个 step ---
print("\n===== 最近 500 step 明细 =====")
recent = step_avg_r[-500:]
if recent:
    s0, s1 = recent[0][0], recent[-1][0]
    rs = [x[2] for x in recent]
    pos = sum(1 for x in rs if x > 0)
    print(f"step {s0} -> {s1}  mean={sum(rs)/len(rs):+.3f}  pos_rate={pos/len(rs)*100:.0f}%  min={min(rs):+.2f} max={max(rs):+.2f}")
    ent_recent = [x for x in recent if x[3]]
    if ent_recent:
        print("ent 行 (resume 后):")
        for x in ent_recent:
            print(f"  step {x[0]} ep={x[1]} entc={x[3]} ent={x[4]}")
    else:
        print("resume 后尚无新 ent 行 (baseline: step706495 ent=1.562 entc=0.0851)")

# --- 地图维度统计 ---
print("\n===== 地图维度 EP_TIME 统计 (全量) =====")
by_map = defaultdict(list)
for m, st, secs, r in ep_time:
    by_map[m].append((st, secs, r))
rows = []
for m, vs in by_map.items():
    n = len(vs)
    avg_r = sum(x[2] for x in vs) / n
    win = sum(1 for x in vs if x[2] > 0)
    avg_secs = sum(x[1] for x in vs) / n
    rows.append((m, n, avg_r, win / n * 100, avg_secs))
rows.sort(key=lambda x: -x[4])
print(f"{'map':<40} {'n':>5} {'avg_r':>8} {'pos%':>6} {'avg_s':>8}")
for m, n, ar, pr, secs in rows[:40]:
    print(f"{m:<40} {n:>5} {ar:>+8.1f} {pr:>5.0f}% {secs:>7.0f}s")

# --- 大图 vs 小图对比 ---
print("\n===== 大/小图对比 =====")
def size_of(m):
    mm = re.search(r"(\d+)X(\d+)", m)
    return int(mm.group(1)) * int(mm.group(2)) if mm else 0
big = [x for x in ep_time if size_of(x[0]) >= 100 * 100]
small = [x for x in ep_time if size_of(x[0]) < 100 * 100]
def summ(vs, label):
    if not vs:
        print(f"{label}: 无数据")
        return
    rs = [x[3] for x in vs]
    print(f"{label}: n={len(vs)} avg_r={sum(rs)/len(rs):+.2f} pos_rate={sum(1 for x in rs if x>0)/len(rs)*100:.0f}% avg_secs={sum(x[2] for x in vs)/len(vs):.0f}")
summ(big, "  大图(>=100x100)")
summ(small, "  小图(<100x100)")

# --- ZOMBIE / FUSE 明细 ---
if zombie_lines:
    print(f"\n===== ZOMBIE 最近 5 条 =====")
    for ln in zombie_lines[-5:]:
        print(f"  L{ln[0]}: {ln[1][:200]}")
if fuse_lines:
    print(f"\n===== ENDTURN_FUSE 最近 3 条 =====")
    for ln in fuse_lines[-3:]:
        print(f"  L{ln[0]}: {ln[1][:200]}")

# --- 保存数据供进一步分析 ---
out = {
    "total_lines": i,
    "step_avg_r_count": len(step_avg_r),
    "ent_lines": [e[:8] for e in ent_lines],
    "ep_time_by_map": {m: {"n": len(vs), "avg_r": sum(x[2] for x in vs)/len(vs),
                            "pos_rate": sum(1 for x in vs if x[2]>0)/len(vs),
                            "avg_secs": sum(x[1] for x in vs)/len(vs)}
                       for m, vs in by_map.items()},
    "recent_step_range": [recent[0][0], recent[-1][0]] if recent else None,
}
try:
    with open(LOG + ".analysis.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n[OK] 详细数据已保存: {LOG}.analysis.json")
except Exception as e:
    print(f"\n[warn] JSON 保存失败: {e}")
