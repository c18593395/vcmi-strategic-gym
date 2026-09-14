#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T05 36X36_02 重评估数据拉取 + J1-J5 判据计算（WIN-2 回池窗结束后跑）

用法:
    python py/t05_02_data_pull.py [--log train_loop.log] [--n 40]

从 train_loop.log 提取 36X36_01 / 36X36_02 局数据，计算 J1-J5 判据。
判据定义见 docs/方案_T05_36X36_02重评估_20260910.md §4.3
"""
import re, sys, argparse, statistics
from pathlib import Path

def parse_args():
    ap = argparse.ArgumentParser(description="T05 36X36_02 重评估 J1-J5 判据")
    ap.add_argument("--log", default="train_loop.log", help="训练主日志路径")
    ap.add_argument("--n", type=int, default=40, help="近 N 局（默认 40）")
    return ap.parse_args()

def extract_episodes(log_path, map_keyword, n):
    """从 train_loop.log 提取含 map_keyword 的局行，返回 [(map, r, steps), ...]"""
    results = []
    pattern = re.compile(
        r'map=([^\s,]+).*?r=([-?\d.]+).*?steps=(\d+)'
    )
    fallback = re.compile(
        r'map=([^\s,]+)'
    )
    r_pattern = re.compile(r'r=([-?\d.]+)')
    steps_pattern = re.compile(r'steps?=(\d+)')
    
    with open(log_path, "r", errors="replace") as f:
        for line in f:
            if map_keyword in line and ("r=" in line or "Reward" in line):
                map_m = fallback.search(line)
                r_m = r_pattern.search(line)
                s_m = steps_pattern.search(line)
                if map_m and r_m and s_m:
                    results.append({
                        "map": map_m.group(1),
                        "r": float(r_m.group(1)),
                        "steps": int(s_m.group(1))
                    })
    return results[-n:]

def compute_j_metrics(episodes_01, episodes_02):
    """计算 J1-J5 判据"""
    results = {}
    
    # J1: 局均 r 对照
    r01 = [e["r"] for e in episodes_01] if episodes_01 else []
    r02 = [e["r"] for e in episodes_02] if episodes_02 else []
    mean_01 = statistics.mean(r01) if r01 else 0
    mean_02 = statistics.mean(r02) if r02 else 0
    ratio = mean_02 / mean_01 if mean_01 != 0 else float('inf')
    j1_pass = 0.8 <= ratio <= 1.25
    results["J1"] = {
        "desc": "局均 r 对照",
        "r_mean_01": round(mean_01, 2),
        "r_mean_02": round(mean_02, 2),
        "ratio": round(ratio, 3),
        "pass": j1_pass,
        "pass_str": "✅ 通过" if j1_pass else "❌ 出界",
        "fail_action": "02 移出，归因真实结构缺陷（近资源真空）"
    }
    
    # J2: 大负率（r < -50）
    neg_02 = [e for e in episodes_02 if e["r"] < -50]
    neg_rate_02 = len(neg_02) / len(episodes_02) if episodes_02 else 0
    neg_01 = [e for e in episodes_01 if e["r"] < -50]
    neg_rate_01 = len(neg_01) / len(episodes_01) if episodes_01 else 0
    j2_pass = neg_rate_02 <= 0.20
    results["J2"] = {
        "desc": "大负率 (r<-50)",
        "neg_rate_01": f"{neg_rate_01:.1%}",
        "neg_rate_02": f"{neg_rate_02:.1%}",
        "pass": j2_pass,
        "pass_str": "✅ 通过" if j2_pass else "❌ 超限",
        "fail_action": "确认空转循环罚，考虑第二步图 03"
    }
    
    # J3: 200 步截断率
    trunc_02 = [e for e in episodes_02 if e["steps"] >= 200]
    trunc_rate_02 = len(trunc_02) / len(episodes_02) if episodes_02 else 0
    j3_pass = trunc_rate_02 <= 0.25
    results["J3"] = {
        "desc": "200 步截断率",
        "trunc_rate_02": f"{trunc_rate_02:.1%}",
        "pass": j3_pass,
        "pass_str": "✅ 通过" if j3_pass else "❌ 超限",
        "fail_action": "目标真空未解决，第二步图 03 前置"
    }
    
    # J4: 守卫接战率（需 grep [GUARD]，日志中含 [GUARD] 行计数）
    # 简化：统计 episodes 中含 [GUARD] 标记的比例（需日志行含 [GUARD] + map 名同时出现）
    # 此处仅做框架，实际需从 highlights 行统计
    results["J4"] = {
        "desc": "守卫接战率（需手动从 [GUARD] 行统计）",
        "note": "grep [GUARD].*36X36_02 train_loop.log 手动对照",
        "pass_str": "⚠ 需手动确认"
    }
    
    # J5: avg_r 整体跌幅（需回池前后全局 avg_r 对比）
    results["J5"] = {
        "desc": "全局 avg_r 跌幅",
        "note": "对比回池前后 grep avg_r train_loop.log | tail -10",
        "pass_str": "⚠ 需回池前后对照"
    }
    
    return results

def main():
    args = parse_args()
    log = Path(args.log)
    if not log.exists():
        print(f"❌ 日志文件不存在: {log}")
        sys.exit(1)
    
    print(f"=== T05 36X36_02 重评估判据（近 {args.n} 局）===")
    print(f"日志: {log}")
    print()
    
    eps_01 = extract_episodes(log, "36X36_01", args.n)
    eps_02 = extract_episodes(log, "36X36_02", args.n)
    
    print(f"36X36_01 样本: {len(eps_01)} 局")
    print(f"36X36_02 样本: {len(eps_02)} 局")
    print()
    
    if not eps_02:
        print("⚠ 02 图尚无数据（未回池或样本不足），J1-J5 判据无法计算")
        print("  提示: 02 图回池后攒够 ~40 局再跑本脚本")
        # 仍输出 01 基线
        if eps_01:
            r01 = [e["r"] for e in eps_01]
            print(f"\n36X36_01 基线: r_mean={statistics.mean(r01):.1f} (n={len(r01)})")
        sys.exit(0)
    
    results = compute_j_metrics(eps_01, eps_02)
    
    for key in ["J1", "J2", "J3", "J4", "J5"]:
        r = results[key]
        print(f"--- {key}: {r['desc']} ---")
        for k, v in r.items():
            if k not in ("desc", "pass", "fail_action"):
                if k != "pass_str":
                    print(f"  {k}: {v}")
        print(f"  结果: {r.get('pass_str', '?')}")
        if not r.get("pass", True) and "fail_action" in r:
            print(f"  失败处置: {r['fail_action']}")
        print()
    
    # 汇总
    j1j2j3_pass = all(results[k].get("pass", False) for k in ["J1", "J2", "J3"])
    print(f"=== 汇总: J1+J2+J3 {'全部通过 → 02 可维持原样在池' if j1j2j3_pass else '有判据未通过 → 按失败处置执行'} ===")

if __name__ == "__main__":
    main()
