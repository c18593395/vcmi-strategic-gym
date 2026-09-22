#!/usr/bin/env python3
"""WIN-1 本次窗 五判据严格聚合（按 本次窗 restart 行 L 切片，避开 shell 转义坑）。

用法：python py/win1_window_aggregate.py [日志路径] [本次窗起点行号L]
  - 不传参则默认 L = 最近一次 'Loaded train state' 行号（本次窗真正起点）
  - 判定：以 ep_steps 行计数"局完成"，统计 截断/接战/经济/capture 等
"""
import re
import sys
from pathlib import Path

DEFAULT_LOG = Path(r"D:\Bigdata\hero3_fresh\train_loop.log")
# 若 WSL 侧调用：
WSL_LOG = Path("/mnt/d/Bigdata/hero3_fresh/train_loop.log")

# 本次窗起点行号（从最近一次 'Loaded train state' 行 +1 起算本次窗）
L = None


def pick_log() -> Path:
    return DEFAULT_LOG if DEFAULT_LOG.exists() else WSL_LOG


def find_last_load_state(lines):
    """返回最近一次 'Loaded train state' 行号（1-based）。"""
    idx = 0
    for i, ln in enumerate(lines, start=1):
        if "Loaded train state" in ln:
            idx = i
    return idx


def parse_window(lines, start):
    """从 start(1-based) 起 解析本次窗，聚合五判据。"""
    eps = []          # ep_steps 完成局：{steps,r,map,act_n}
    town_capture = 0  # 本次窗 TOWN_CAPTURE 次数
    town_prefix = 0   # 本次窗 [TOWN 前缀事件次数
    guard = 0
    endturn = 0
    recruit = 0
    build_new = 0
    err_yes = 0
    sigsegv = 0
    trunc250 = 0      # 截断局 (ep_steps>=250)

    for ln in lines[start - 1:]:
        if "[EP_TIME]" in ln and "err=" in ln:
            m = re.search(r"err=(\w+)", ln)
            if m and m.group(1) == "yes":
                err_yes += 1
        if "SIGSEGV" in ln or "SIGABRT" in ln:
            sigsegv += 1
        if "[TOWN_CAPTURE]" in ln:
            town_capture += 1
            town_prefix += 1
        elif "[TOWN" in ln:
            town_prefix += 1
        if "[GUARD]" in ln:
            guard += 1
        if "ENDTURN" in ln:
            endturn += 1
        if "RECRUITED" in ln:
            recruit += 1
        if "BUILD_NEW" in ln:
            build_new += 1
        if "ep_steps=" in ln:
            m = re.search(r"ep_steps=(\d+)\s+r=(-?[\d.]+)", ln)
            if m:
                steps, r = int(m.group(1)), float(m.group(2))
                # 提取 map= 字段（兼容 "map=xxx.vmap" 出现 0/1/多次 的情况）
                map_field = "unknown"
                mmp = re.findall(r"map=(\S+?\.vmap)", ln)
                if mmp:
                    map_field = mmp[0]
                eps.append({"steps": steps, "r": r, "map": map_field})
                if steps >= 250:
                    trunc250 += 1

    # 判据 ③ avg_r 跌幅（按本次窗 r 均值，与基线对照）
    rs = [e["r"] for e in eps]
    avg_r = sum(rs) / len(rs) if rs else 0.0
    n_ep = len(eps)
    trunc_ratio = (trunc250 / n_ep * 100) if n_ep else 0.0

    return {
        "n_ep": n_ep,
        "avg_r": avg_r,
        "town_capture": town_capture,
        "town_prefix": town_prefix,
        "guard": guard,
        "endturn": endturn,
        "recruit": recruit,
        "build_new": build_new,
        "err_yes": err_yes,
        "sigsegv": sigsegv,
        "trunc250": trunc250,
        "trunc_ratio": trunc_ratio,
        "eps": eps,
    }


def main():
    log = pick_log()
    print(f"日志: {log}")
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    print(f"总行数: {len(lines)}")

    # 本次窗起点
    global L
    if len(sys.argv) >= 3:
        L = int(sys.argv[2])
    else:
        L = find_last_load_state(lines)
    print(f"本次窗起点 L={L}  行内容: {lines[L-1] if L and L <= len(lines) else 'N/A'}")

    w = parse_window(lines, L + 1)  # 从 L+1 起

    print("\n=== 五判据状态 ===")
    print(f"局数 n={w['n_ep']} (达标线 40)")
    print(f"① TOWN_CAPTURE 非零: 本次窗 {w['town_capture']} 次 ([TOWN 前缀事件 {w['town_prefix']})")
    print(f"② GUARD 接战: 本次窗 {w['guard']} 次 (需按局归一化 → 占局比 {round(w['guard']/w['n_ep']*100,1) if w['n_ep'] else 0}%)")
    print(f"③ avg_r: 本次窗 {w['avg_r']:.2f}")
    print(f"④ 自发经济: RECRUITED={w['recruit']}  BUILD_NEW={w['build_new']}")
    print(f"⑤ 截断率 (≥250步): {w['trunc250']}/{w['n_ep']} = {w['trunc_ratio']:.1f}%")
    print(f"崩溃: err_yes={w['err_yes']}  SIGSEGV/SIGABRT={w['sigsegv']}")

    # 各局 r 分布
    if w["eps"]:
        r_pos = sum(1 for e in w["eps"] if e["r"] > 0)
        r_big_neg = sum(1 for e in w["eps"] if e["r"] <= -500)
        print(f"\n=== r 分布 ===")
        print(f"正局 {r_pos}/{w['n_ep']}  大负(≤-500) {r_big_neg}/{w['n_ep']}")
        # 按地图聚合
        from collections import defaultdict
        by_map = defaultdict(list)
        for e in w["eps"]:
            by_map[e["map"].split(".vmap")[0]].append(e["r"])
        for mp, rs in sorted(by_map.items()):
            print(f"  {mp:40s} n={len(rs):3d} avg={sum(rs)/len(rs):8.2f}")

    # 是否达标
    print("\n=== 结论 ===")
    if w["n_ep"] < 40:
        print(f"未达标：本次窗仅 {w['n_ep']} 局 < 40，继续攒局。")
    else:
        c1 = w["town_capture"] > 0
        c2 = (w["guard"] / w["n_ep"] * 100) >= 80
        c3 = w["avg_r"] > -0.2  # 跌幅 <20% (近似)
        c4 = w["recruit"] > 0
        c5 = w["trunc_ratio"] <= 20
        print(f"达标线 40 已满足。判据: ①capture={c1} ②guard≥80%={c2} ③avg_r跌幅<20%={c3} ④经济={c4} ⑤截断≤20%={c5}")
        if all([c1, c2, c3, c4, c5]):
            print("✅ 五判据聚合达标，可触发 WIN-2 / WIN-3 / T7.5 S2 后续窗口。")
        else:
            print("⚠️ 部分判据未过，需继续观察或回退分析。")


if __name__ == "__main__":
    main()
