#!/usr/bin/env python3
"""A/B 分层统计 + Level 2→3 晋级评估 (2026-08-29)

按 map= 字段分组统计: 局数/正奖励率/大负率(r<-100)/r mean/灾难深度/真首胜率。
旧格式日志(无 map=)归入 unknown 组, 仅新日志参与 A/B 判定。

用法:
  python3 py/analyze_ab.py                      # 默认读 /mnt/d/Bigdata/hero3_fresh/train_loop.log
  python3 py/analyze_ab.py <log路径>            # 指定日志

A/B 判定线 (T03_adventure_30X30_01.vmap):
  >=50 局: 大负率 <=15% → 成功, 依次启用其余 3 张
           大负率 >=25% → 失败, 回退 2 张在训图
           15%~25%  → 延长至 80 局
  提前终止: 前 20 局出现 >=3 局 r<-100 且这些局 r 均 <-300 → 判失败

晋级评估 (Phase II.1, 基于 v5+ 段全部新格式局):
  首胜判定: r >= 80 且 ep_steps < 60 (守卫+100 短局模式, 实测首胜局 ep_steps 31~49 / r 93~101;
            阈值留余量覆盖 NK2/explore 波动) — 每局最多计 1 次首胜 (多守卫图 r 可再叠, 但单局判定按局)
  晋级线: 最近 100 局首胜率 >= 30% 或 avg_r 持续为正 (连续两窗口 r_mean > 0)
"""
import re, sys
from collections import defaultdict

LOG = sys.argv[1] if len(sys.argv) > 1 else "/mnt/d/Bigdata/hero3_fresh/train_loop.log"
AB_MAP = "T03_adventure_30X30_01.vmap"
N_JUDGE, N_EXTEND = 50, 80
WIN_R, WIN_STEPS = 80.0, 60          # 首胜判定阈值
PROMO_N = 100                        # 晋级窗口
PROMO_WIN_RATE = 0.30                # 晋级线①: 胜率下限 (观察目标 30~50%)
PROMO_AVG_R = 0.0                    # 晋级线②: avg_r 持续为正
PROMO_POSITIVE_WINDOWS = 2           # 连续 N 个 50 局窗口 r_mean > 0

# 兼容新旧格式: map= 可缺省
m_ep = re.compile(r'ep_steps=(\d+)\s+r=([-\d.]+)\s+act=\[.*?\]\s+obs_nz=(\d+)(?:\s+map=(\S+))?')

stats = defaultdict(list)  # map -> [(steps, r, nz), ...]
with open(LOG, errors="replace") as f:
    for line in f:
        m = m_ep.search(line)
        if not m:
            continue
        steps_i, r_f = int(m.group(1)), float(m.group(2))
        if steps_i == 1 and r_f < 5:
            continue  # P4 (08-29): 剔除空转局 (steps=1, r≈1.7 的 .so 事故段垃圾数据, 会虚高正率)
        stats[m.group(4) or "(旧格式·无map字段)"].append((steps_i, r_f, int(m.group(3))))

def summarize(name, eps):
    n = len(eps)
    rs = [r for _, r, _ in eps]
    pos = sum(1 for r in rs if r > 0)
    big_neg = [r for r in rs if r < -100]
    wins = sum(1 for s, r, _ in eps if r >= WIN_R and s < WIN_STEPS)
    r_mean = sum(rs) / n
    print(f"\n{name}: n={n}  pos_rate={pos/n:.1%}  big_neg_rate={len(big_neg)/n:.1%}  "
          f"win_rate={wins/n:.1%}  r_mean={r_mean:.1f}  r_max={max(rs):.1f}  r_min={min(rs):.1f}")
    if big_neg:
        print(f"  大负局深度: mean={sum(big_neg)/len(big_neg):.1f}  worst={min(big_neg):.1f}  count={len(big_neg)}")
    if wins:
        print(f"  首胜局: {wins} (r>={WIN_R:.0f} 且 steps<{WIN_STEPS})")

print(f"A/B 分层统计 — {LOG}")
for name, eps in sorted(stats.items()):
    summarize(name, eps)
    # 最近 50 局滚动窗口
    recent = eps[-50:]
    if len(eps) > 50:
        summarize(f"  {name} [最近50局]", recent)

# === 30X30_01 判定 ===
ab = stats.get(AB_MAP, [])
if not ab:
    print(f"\n[A/B] {AB_MAP}: 尚无新格式样本 (等待自然重启后积累)")
else:
    ab_rs = [r for _, r, _ in ab]
    big_neg = [r for r in ab_rs if r < -100]
    rate = len(big_neg) / len(ab_rs)
    print(f"\n[A/B 判定] {AB_MAP}: n={len(ab_rs)}  big_neg_rate={rate:.1%}")
    # 提前终止检查 (前 20 局)
    first20 = ab_rs[:20]
    fn = [r for r in first20 if r < -100]
    if len(first20) <= 20 and len(fn) >= 3 and sum(fn) / len(fn) < -300:
        print(f"  ❌ 提前终止触发: 前{len(first20)}局大负{len(fn)}局且均值{sum(fn)/len(fn):.0f} < -300 → 判失败, 回退 2 张在训图")
    elif len(ab_rs) < N_JUDGE:
        print(f"  ⏳ 样本不足: {len(ab_rs)}/{N_JUDGE} 局 (中间带延长至 {N_EXTEND} 局), 继续积累")
    else:
        if rate <= 0.15:
            print(f"  ✅ 判成功: big_neg_rate {rate:.1%} <= 15% → 依次启用 30X30_02 / 36X36_01 / 36X36_02")
        elif rate >= 0.25:
            print(f"  ❌ 判失败: big_neg_rate {rate:.1%} >= 25% → 回退仅 2 张 20X20 在训图")
        else:
            need = N_EXTEND - len(ab_rs)
            print(f"  ⏳ 灰色带 (15%~25%): 延长评估, 还需 {max(0, need)} 局到 {N_EXTEND}")

# === Phase II.1 晋级评估 (v5+ 段全部新格式局, 不分图 — 晋级看整体能力) ===
# 线性二次扫描保持日志时间序 (stats 按图分组丢失顺序)
linear = []
with open(LOG, errors="replace") as f:
    for line in f:
        m = m_ep.search(line)
        if m and m.group(4):  # 仅新格式
            if int(m.group(1)) == 1 and float(m.group(2)) < 5:
                continue  # P4: 剔除空转局 (同上, 防虚高)
            linear.append((int(m.group(1)), float(m.group(2)), int(m.group(3)), m.group(4)))

print(f"\n[晋级评估 Phase II.1] (最近 {PROMO_N} 局新格式, 不分图)")
if len(linear) < PROMO_N:
    print(f"  ⏳ 样本不足: {len(linear)}/{PROMO_N} 局, 继续积累")
else:
    recent = linear[-PROMO_N:]
    rs = [r for _, r, _, _ in recent]
    wins = sum(1 for s, r, _, _ in recent if r >= WIN_R and s < WIN_STEPS)
    win_rate = wins / len(recent)
    r_mean = sum(rs) / len(rs)
    # avg_r 持续为正: 连续 PROMO_POSITIVE_WINDOWS 个 50 局窗口
    pos_windows = 0
    w_size = 50
    n_windows = len(linear) // w_size
    for i in range(max(0, n_windows - PROMO_POSITIVE_WINDOWS), n_windows):
        wr = [r for _, r, _, _ in linear[i*w_size:(i+1)*w_size]]
        if wr and sum(wr)/len(wr) > PROMO_AVG_R:
            pos_windows += 1
    sustained = pos_windows >= PROMO_POSITIVE_WINDOWS
    cond1 = win_rate >= PROMO_WIN_RATE
    cond2 = sustained
    verdict = "✅ 达晋级线" if (cond1 or cond2) else "⏳ 未达晋级线"
    print(f"  胜率线①: 最近{PROMO_N}局首胜率 {win_rate:.1%} (阈值 ≥{PROMO_WIN_RATE:.0%}) {'✅' if cond1 else '❌'}")
    print(f"  avg_r 线②: 最近 {PROMO_POSITIVE_WINDOWS} 个 {w_size} 局窗口 r_mean>0 的个数 = {pos_windows} {'✅' if cond2 else '❌'}")
    print(f"  {verdict} → {'可启动 II.2 切 T04 (不开经济)' if (cond1 or cond2) else '继续训练积累'}")
    print(f"  参考: 最近{PROMO_N}局 r_mean={r_mean:.1f}  首胜局={wins}")
