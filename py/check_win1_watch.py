#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WIN-1 capture +100 激励观察窗 — 五判据聚合面板 (只读, 不碰训练)

建: 2026-09-14 (H3 #228 修复 / 干净 MAPS=10 池上线后)
口径与 py/check_duel_watch.py 对齐:
  - 数据源 = train_loop.log, 顺序扫描, 事件行先于所属局 ep_steps= 行 → pending 归并
  - 有效局 = err=no 且 obs_nz>0 (obs_nz==0 = reset 冷启动脏样本, #214)
  - 自发经济 = act 序列下标 >=24 (economy_force=24 步强制窗外) 且 16<=a<=21
  - 200 步局 = ep_steps>=200 (truncation)
  - 守卫胜闭环 = 出现过 [GUARD] fought & won 的局占比 (同 09-08 结案口径)
  - TOWN_CAPTURE #213 后 duel 图已排除 proxy, 故判据①只统计非 duel 的 T06 (1v3)
WIN-1 五判据 (见 docs/当前任务清单.md WIN-1):
  ① T06(非duel) [TOWN_CAPTURE] 非零
  ② 守卫胜局占比 >=80% (1v3 组)
  ③ avg_r 不塌: 后1/3 局均值 / 前1/3 局均值 >=0.8
  ④ 自发经济局占比 >=80% (1v3 组)
  ⑤ 200 步局占比 <=20% (1v3 组)
  目标样本 ~40 有效局再聚合。

用法:
  python3 check_win1_watch.py            # 默认: 当前生产 run (最后一个 WSL2 PPO v2 banner 起)
  python3 check_win1_watch.py --last 40  # 尾窗 40 有效局口径
  python3 check_win1_watch.py --from-line 88446
"""
import os
import re
import sys
from collections import defaultdict

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
TARGET_N = 40          # WIN-1 聚合目标局数
OBS5_MAX_STEPS = 60    # OBS-5 无标记短终局: 步数上限

EP_PAT = re.compile(
    r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]*)\] obs_nz=(\d+) map=(\S+)"
)
EPTIME_PAT = re.compile(
    r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\S+)"
)
STEP_PAT = re.compile(r"step(\d+) avg_r=(-?[\d.]+) ep=(\d+)")
BANNER = "WSL2 PPO v2"

EV_TAGS = {
    "[GUARD_DONE]": "guard_done",
    "[GUARD]": "guard",
    "[TOWN_CAPTURE]": "capture",
    "[ZOMBIE]": "zombie",
    "[MINE]": "mine",
    "[TOWNSTALL]": "townstall",
    "[TOWN_BLOCKED]": "town_blocked",
    "[RECRUITED]": "recruited",
    "[BUILD_NEW]": "build_new",
}
TERMINAL_TAGS = ("guard", "guard_done", "capture", "zombie")


def group_of(mp):
    if "duel" in mp:
        return "duel"
    if mp.startswith("T06"):
        return "1v3"
    if mp.startswith("T05"):
        return "T05"
    return "H3M"


def parse_rows():
    """返回 (所有 ep 行列表, 最后 banner 行号 1-based)。事件 pending 归并到紧随的 ep 行。"""
    rows = []
    pending = defaultdict(int)
    pending_cap = []
    last_banner = 0
    with open(LOG, errors="replace") as f:
        for ln0, line in enumerate(f, 1):
            if BANNER in line:
                last_banner = ln0
            if "[EP_TIME]" in line:
                m = EPTIME_PAT.search(line)
                if m:
                    pending["_secs"] = int(m.group(3))
                    pending["_err"] = m.group(5)
                continue
            if "ep_steps=" in line and "map=" in line:
                m = EP_PAT.search(line)
                if not m:
                    continue
                steps, r, acts_s, nz, mp = m.groups()
                rows.append({
                    "ln": ln0, "map": mp, "steps": int(steps), "r": float(r),
                    "acts": [int(x) for x in acts_s.split(",") if x.strip()],
                    "nz": int(nz),
                    "ev": dict(pending),
                    "cap_lines": list(pending_cap),
                    "secs": pending.get("_secs"),
                    "err": pending.get("_err", "?"),
                    "gstep": None, "epno": None,
                })
                pending = defaultdict(int)
                pending_cap = []
                continue
            m = STEP_PAT.search(line)
            if m and rows:
                rows[-1]["gstep"] = int(m.group(1))
                rows[-1]["epno"] = int(m.group(3))
                continue
            for tag, name in EV_TAGS.items():
                if tag in line:
                    pending[name] += 1
                    if name == "capture":
                        pending_cap.append(line.strip())
    return rows, last_banner


def spont(acts):
    """自发经济动作数: 强制窗(前24拍)外的 16-21。"""
    return sum(1 for i, a in enumerate(acts) if i >= 24 and 16 <= a <= 21)


def valid(row):
    return row["err"] == "no" and row["nz"] > 0


def panel(title, rows):
    rows = [r for r in rows if valid(r)]
    n = len(rows)
    print("=" * 78)
    print(f"窗口: {title}")
    if not rows:
        print("  无有效局")
        return
    g0, g1 = rows[0]["gstep"], rows[-1]["gstep"]
    print(f"  有效局 {n} (err=no 且 obs_nz>0)  全局 step {g0} → {g1}"
          f"  样本目标 {TARGET_N} 局")

    groups = defaultdict(list)
    for r in rows:
        groups[group_of(r["map"])].append(r)

    # --- 分组统计表 ---
    print("\n  组        局数 avg_r   r范围          200步局    自发经济   守卫闭环  capture  mine")
    for g in ("1v3", "duel", "T05", "H3M"):
        rs = groups.get(g)
        if not rs:
            continue
        gn = len(rs)
        avg = sum(r["r"] for r in rs) / gn
        t200 = sum(1 for r in rs if r["steps"] >= 200)
        sp = sum(1 for r in rs if spont(r["acts"]) > 0)
        gd = sum(1 for r in rs if r["ev"].get("guard"))
        cap = sum(r["ev"].get("capture", 0) for r in rs)
        mine = sum(r["ev"].get("mine", 0) for r in rs)
        rmin, rmax = min(r["r"] for r in rs), max(r["r"] for r in rs)
        print(f"  {g:<8} {gn:>4} {avg:>7.1f}  {rmin:>7.1f}~{rmax:<7.1f}"
              f" {t200:>4}({t200*100//gn:>3}%) {sp:>3}({sp*100//gn:>3}%)"
              f" {gd:>3}({gd*100//gn:>3}%) {cap:>7}  {mine:>5}")

    # --- WIN-1 五判据 (1v3 组) ---
    rs = groups.get("1v3", [])
    print("\n--- WIN-1 五判据 (1v3 = 非 duel 的 T06 图) ---")
    if not rs:
        print("  窗内无 1v3 局")
        return
    nn = len(rs)
    cap_eps = sum(1 for r in rs if r["ev"].get("capture"))
    cap_tot = sum(r["ev"].get("capture", 0) for r in rs)
    gd = sum(1 for r in rs if r["ev"].get("guard"))
    sp = sum(1 for r in rs if spont(r["acts"]) > 0)
    t200 = sum(1 for r in rs if r["steps"] >= 200)
    k = max(nn // 3, 1)
    avg_f = sum(r["r"] for r in rs[:k]) / k
    avg_b = sum(r["r"] for r in rs[-k:]) / k
    ratio = avg_b / avg_f if abs(avg_f) > 1e-9 else float("nan")

    def mark(ok):
        return "✅" if ok else "❌"

    enough = nn >= TARGET_N
    print(f"  样本量: {nn}/{TARGET_N} 有效局"
          + ("" if enough else "  ⏳ 未到聚合目标, 以下为中途快照"))
    print(f"  {mark(cap_tot > 0)} ① TOWN_CAPTURE 触发: "
          f"{cap_tot} 次 / {cap_eps} 局 (核心判据: 非零)")
    print(f"  {mark(gd * 100 >= 80 * nn)} ② 守卫胜闭环: {gd}/{nn} = {gd*100/nn:.0f}% (判据 ≥80%)")
    print(f"  {mark(ratio >= 0.8)} ③ avg_r 趋势: 前1/3 {avg_f:.1f} → 后1/3 {avg_b:.1f}"
          f" (比值 {ratio:.2f}, 判据 ≥0.80)")
    print(f"  {mark(sp * 100 >= 80 * nn)} ④ 自发经济局: {sp}/{nn} = {sp*100/nn:.0f}% (判据 ≥80%)")
    print(f"  {mark(t200 * 100 <= 20 * nn)} ⑤ 200 步局: {t200}/{nn} = {t200*100/nn:.0f}% (判据 ≤20%)")

    # --- capture 明细 ---
    if cap_tot:
        print("\n  capture 明细:")
        for r in rs:
            for cl in r["cap_lines"]:
                print(f"    L{r['ln']} step={r['gstep']} {r['map']}: {cl}")

    # --- OBS-5 候选: 108_02_duel 无标记短终局 ---
    obs5 = []
    for r in rows:
        if "108X108_02_duel" not in r["map"] or r["steps"] > OBS5_MAX_STEPS:
            continue
        if any(r["ev"].get(t) for t in TERMINAL_TAGS):
            continue
        sps = r["secs"] / r["steps"] if r["secs"] else None
        obs5.append((r, sps))
    print(f"\n--- OBS-5 候选 (108_02_duel ≤{OBS5_MAX_STEPS}步 无终局标记 err=no): "
          f"{len(obs5)} 局 ---")
    for r, sps in obs5:
        extra = f"{sps:.1f}s/步" if sps is not None else "secs 缺"
        print(f"    L{r['ln']} step={r['gstep']} steps={r['steps']} r={r['r']:.1f} {extra}")


def main():
    rows, last_banner = parse_rows()
    if len(sys.argv) >= 3 and sys.argv[1] == "--last":
        n = int(sys.argv[2])
        panel(f"尾窗 {n} 个 ep 行 (全部历史口径)", rows[-n:])
    elif len(sys.argv) >= 3 and sys.argv[1] == "--from-line":
        ln = int(sys.argv[2])
        panel(f"L{ln} 起 (手动指定)", [r for r in rows if r["ln"] >= ln])
    else:
        panel(f"当前生产 run (最后 banner L{last_banner} 起)",
              [r for r in rows if r["ln"] >= last_banner])


if __name__ == "__main__":
    main()
