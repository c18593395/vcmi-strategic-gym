#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WIN-1 判据⑤专项: 200 步截断局地图分布 x 行为特征分析 (只读, 不碰训练)

建: 2026-09-15
口径与 check_win1_watch.py 完全对齐 (同 EP_PAT / pending 归并 / 有效局=err=no 且 obs_nz>0)。
新增:
  - 逐局行为分类: A=已 capture (胜后继续走到 trunc) / B=无cap有guard (推进未竟) / C=无cap无guard
  - capture 发生时机 (at step N → 胜后空转 = 200-N 步)
  - 末 20 拍动作画像: 方向(0-7)/END_TURN(10)/经济(16-21)/MOVE_TO(>=24) 占比 + 最频动作 + 熵
  - 步数直方图 + 同图截断/非截断对照 (判断 "差一点 180-199" vs "全程空转")
事实 (ep_runner_one.py L134-136): T06 无条件 move_to_force=200 全程 + guard_done_steps=0,
  200 truncation 是 T06 唯一收局机制; capture proxy +100 不 break (L951-961)。

用法:
  python3 py/analyze_trunc200.py            # 当前生产 run
  python3 py/analyze_trunc200.py --last 60  # 尾窗 60 个 ep 行
  python3 py/analyze_trunc200.py --all      # 全历史
"""
import math
import re
import sys
from collections import Counter, defaultdict

LOG = "/mnt/d/Bigdata/hero3_fresh/train_loop.log"

EP_PAT = re.compile(
    r"ep_steps=(\d+) r=(-?[\d.]+) act=\[([0-9, ]*)\] obs_nz=(\d+) map=(\S+)"
)
EPTIME_PAT = re.compile(
    r"\[EP_TIME\] map=(\S+) steps=(\d+) secs=(\d+) r=(-?[\d.]+) err=(\S+)"
)
STEP_PAT = re.compile(r"step(\d+) avg_r=(-?[\d.]+) ep=(\d+)")
CAP_STEP_PAT = re.compile(r"at step (\d+)")
BANNER = "WSL2 PPO v2"

EV_TAGS = {
    "[GUARD_DONE]": "guard_done", "[GUARD]": "guard",
    "[TOWN_CAPTURE]": "capture", "[ZOMBIE]": "zombie",
    "[MINE]": "mine", "[TOWNSTALL]": "townstall",
    "[TOWN_BLOCKED]": "town_blocked", "[RECRUITED]": "recruited",
    "[BUILD_NEW]": "build_new", "[HERO_DEATH]": "hero_death",
    "[ENDTURN_FUSE]": "endturn_fuse",
}
TRUNC = 200
TAIL_N = 20


def group_of(mp):
    if "duel" in mp:
        return "duel"
    if mp.startswith("T06"):
        return "1v3"
    if mp.startswith("T05"):
        return "T05"
    return "H3M"


def parse_rows():
    rows, pending, pending_cap, last_banner = [], defaultdict(int), [], 0
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
                cap_steps = [int(x) for x in (CAP_STEP_PAT.search(c).group(1)
                                              for c in pending_cap) if x is not None]
                rows.append({
                    "ln": ln0, "map": mp, "steps": int(steps), "r": float(r),
                    "acts": [int(x) for x in acts_s.split(",") if x.strip()],
                    "nz": int(nz), "ev": dict(pending), "cap_lines": list(pending_cap),
                    "cap_at": cap_steps,
                    "secs": pending.get("_secs"), "err": pending.get("_err", "?"),
                    "gstep": None, "epno": None,
                })
                pending, pending_cap = defaultdict(int), []
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


def valid(r):
    return r["err"] == "no" and r["nz"] > 0


def act_kind(a):
    if 0 <= a <= 7:
        return "dir"
    if a == 10:
        return "endturn"
    if 16 <= a <= 21:
        return "econ"
    if a >= 24:
        return "moveto"
    return "other"


def tail_profile(acts, n=TAIL_N):
    tail = acts[-n:]
    if not tail:
        return None
    k = len(tail)
    cnt = Counter(act_kind(a) for a in tail)
    top_a, top_c = Counter(tail).most_common(1)[0]
    ent = 0.0
    for c in Counter(tail).values():
        p = c / k
        ent -= p * math.log2(p) * (p and 1)
    return {
        "dir": cnt.get("dir", 0) / k, "endturn": cnt.get("endturn", 0) / k,
        "econ": cnt.get("econ", 0) / k, "moveto": cnt.get("moveto", 0) / k,
        "top_a": top_a, "top_ratio": top_c / k, "ent": ent, "k": k,
    }


def avg(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def med(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n else float("nan")


def analyze(title, rows, tail_n=TAIL_N, map_filter=None):
    rows = [r for r in rows if valid(r)]
    if map_filter:
        rows = [r for r in rows if map_filter in r["map"]]
    n = len(rows)
    print("=" * 86)
    print(f"窗口: {title}")
    if not rows:
        print("  无有效局")
        return
    tr = [r for r in rows if r["steps"] >= TRUNC]
    print(f"  有效局 {n}  200 截断 {len(tr)} ({len(tr)*100/n:.0f}%)  "
          f"step {rows[0]['gstep']} → {rows[-1]['gstep']}")

    # --- 步数直方图 (1v3 组 = 判据⑤口径) ---
    print("\n--- 步数分布 (1v3 组, 判据⑤口径) ---")
    buckets = [(0, 59, "<60"), (60, 99, "60-99"), (100, 149, "100-149"),
               (150, 179, "150-179"), (180, 199, "180-199"), (200, 10_000, "=200 截断")]
    g1v3 = [r for r in rows if group_of(r["map"]) == "1v3"]
    for lo, hi, name in buckets:
        c = sum(1 for r in g1v3 if lo <= r["steps"] <= hi)
        bar = "#" * c
        print(f"  {name:<10} {c:>3}  {bar}")
    if g1v3:
        nt = sum(1 for r in g1v3 if r["steps"] >= TRUNC)
        near = sum(1 for r in g1v3 if 180 <= r["steps"] < TRUNC)
        print(f"  1v3 截断率 {nt}/{len(g1v3)} = {nt*100/len(g1v3):.0f}% (判据 ≤20%); "
              f"180-199 临界 {near} 局")

    # --- 截断局 x 具体地图 ---
    print("\n--- 200 截断局 × 具体地图 (对照同图非截断局) ---")
    print(f"  {'地图':<34} {'截断/总':>8} {'率':>5} {'r截断':>7} {'r非截':>7} "
          f"{'cap局':>5} {'guard':>5} {'矿均':>5} {'s/步':>5}")
    by_map = defaultdict(list)
    for r in tr:
        by_map[r["map"]].append(r)
    for mp in sorted(by_map):
        tset = by_map[mp]
        allm = [r for r in rows if r["map"] == mp]
        non_t = [r for r in allm if r["steps"] < TRUNC]
        cap_e = sum(1 for r in tset if r["ev"].get("capture"))
        gd = sum(1 for r in tset if r["ev"].get("guard"))
        mine = avg([r["ev"].get("mine", 0) for r in tset])
        sps = avg([r["secs"] / r["steps"] for r in tset if r["secs"]])
        print(f"  {mp:<34} {len(tset):>3}/{len(allm):<3} "
              f"{len(tset)*100/len(allm):>4.0f}% {avg([r['r'] for r in tset]):>7.1f} "
              f"{avg([r['r'] for r in non_t]):>7.1f} {cap_e:>5} {gd:>5} {mine:>5.1f} {sps:>5.1f}")

    # --- 截断局逐局明细 + 行为分类 ---
    print(f"\n--- 200 截断局逐局明细 (按时间序, 末{tail_n}拍画像) ---")
    cls_cnt = Counter()
    for r in tr:
        ev = r["ev"]
        if ev.get("capture"):
            cls = "A 胜后空转"
        elif ev.get("guard"):
            cls = "B 推进未竟"
        else:
            cls = "C 未打出去"
        cls_cnt[cls] += 1
        tp = tail_profile(r["acts"], tail_n)
        cap_at = ",".join(str(x) for x in r["cap_at"]) or "-"
        tail = (f"方向{tp['dir']*100:.0f}% END{tp['endturn']*100:.0f}% "
                f"经济{tp['econ']*100:.0f}% M2{tp['moveto']*100:.0f}% "
                f"top={tp['top_a']}({tp['top_ratio']*100:.0f}%) H={tp['ent']:.2f}")
        flags = []
        for tag in ("zombie", "townstall", "town_blocked", "endturn_fuse",
                    "hero_death", "guard_done", "recruited"):
            if ev.get(tag):
                flags.append(f"{tag}x{ev[tag]}")
        sps = r["secs"] / r["steps"] if r["secs"] else float("nan")
        print(f"  L{r['ln']:<6} step={r['gstep']} {r['map']:<32} "
              f"r={r['r']:>7.1f} cap@{cap_at:<7} guard={ev.get('guard',0)} "
              f"mine={ev.get('mine',0)} {sps:4.1f}s/步 [{cls}]")
        print(f"           {tail}  {' '.join(flags) if flags else ''}")

    print("\n--- 截断局行为分类汇总 ---")
    for cls in ("A 胜后空转", "B 推进未竟", "C 未打出去"):
        c = cls_cnt.get(cls, 0)
        print(f"  {cls:<10} {c:>3} 局 ({c*100/max(len(tr),1):.0f}%)")

    # --- 1v3 非截断对照 ---
    print("\n--- 1v3 非截断局对照 (截断局到底差在哪) ---")
    nt = [r for r in g1v3 if r["steps"] < TRUNC]
    if nt:
        print(f"  非截断 {len(nt)} 局: avg_r={avg([r['r'] for r in nt]):.1f}  "
              f"步长中位={med([r['steps'] for r in nt]):.0f}  "
              f"cap局={sum(1 for r in nt if r['ev'].get('capture'))}  "
              f"guard局={sum(1 for r in nt if r['ev'].get('guard'))}  "
              f"矿均={avg([r['ev'].get('mine',0) for r in nt]):.1f}  "
              f"s/步={avg([r['secs']/r['steps'] for r in nt if r['secs']]):.1f}")
    t1v3 = [r for r in g1v3 if r["steps"] >= TRUNC]
    if t1v3:
        print(f"  截断 {len(t1v3)} 局: avg_r={avg([r['r'] for r in t1v3]):.1f}  "
              f"cap局={sum(1 for r in t1v3 if r['ev'].get('capture'))}  "
              f"guard局={sum(1 for r in t1v3 if r['ev'].get('guard'))}  "
              f"矿均={avg([r['ev'].get('mine',0) for r in t1v3]):.1f}  "
              f"s/步={avg([r['secs']/r['steps'] for r in t1v3 if r['secs']]):.1f}")


def main():
    args = sys.argv[1:]
    tail_n, map_filter = TAIL_N, None
    if "--tail" in args:
        tail_n = int(args[args.index("--tail") + 1])
    if "--map" in args:
        map_filter = args[args.index("--map") + 1]
    rows, last_banner = parse_rows()
    if len(args) >= 2 and args[0] == "--last":
        analyze(f"尾窗 {args[1]} 个 ep 行", rows[-int(args[1]):], tail_n, map_filter)
    elif args and args[0] == "--all":
        analyze("全历史", rows, tail_n, map_filter)
    else:
        analyze(f"当前生产 run (banner L{last_banner} 起)",
                [r for r in rows if r["ln"] >= last_banner], tail_n, map_filter)


if __name__ == "__main__":
    main()
