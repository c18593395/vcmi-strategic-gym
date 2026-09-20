# -*- coding: utf-8 -*-
"""
OPS-JEV-04 JEV 判决金标回归 (2026-09-21)
====================================================
定位: 三个 JEV 判决脚本 (train_alert_triage / h3m_fail_triage / h3m_pool_rank)
      的问题集 criteria 一旦改动, 判决行为可能静默漂移。本脚本持有一组
      真实金标 (固定 state 输入 + 期望输出约束), 对当前生效问题集重放,
      断言分类/建议仍在预期区间。改任何 criteria/措辞前后各跑一次。

问题集来源: 直接 import 各脚本模块常量 (测的就是线上生效版, 不复制不脱钩):
  train_alert_triage._REQUESTS  -> RED / YELLOW
  h3m_fail_triage.QUESTIONS     -> FAIL
  h3m_pool_rank.QUESTIONS       -> POOL

金标 (5 条, 2026-09-21 真实判决种子, 见 docs 汇报):
断言哲学 = 行为带 (概率下限 / noul 区间 / score 区间), 不点值不 argmax ——
JEV 概率输出有固有波动, 贴边判决 (如 p=0.54) 的 argmax 天然不稳定;
回归要抓的是 "criteria 改坏导致期望分类概率崩塌", 不是复刻单次采样。

  red_stale_01   日志 25min 无更新+keepalive 缺失+PID 存活 -> keepalive 缺失概率下限+MONITOR 侧
  red_crash_01   C2 L0 崩溃计数告警(实际 0 崩溃)          -> crash_recurrence 概率下限
  yellow_neg_01  连续 3 局大负(含 duel 底噪图)            -> escalate 上限 (非立即升级)
  fail_conv_01   h3m2vmap symbol size mismatch            -> convert_defect 概率下限
  pool_water_01  Brave New World 108 尺寸水域图           -> open_water_isolation 概率下限

用法:
  python jev_eval_regress.py                 # 全量 (5 条, ~$0.0002)
  python jev_eval_regress.py --suite RED     # 只跑 RED 套件
  python jev_eval_regress.py --json          # 机器可读输出
退出码: 有失败 -> 1 (可挂改动前检查)
"""

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PROVIDER = "openrouter"
JEV_TIMEOUT = 60

# ---------------------------------------------------------------- 金标集

GOLDENS = [
    {
        "id": "red_stale_01", "suite": "RED",
        "state": (
            "ALERT: train_loop.log 25.0 分钟无更新，训练可能死; file_size=123456 bytes\n"
            "log_staleness_minutes: 25.0\n"
            "recent_episodes(last5, map:steps,r,obs_nz): t06_72_02:steps=250,r=-42.35,obs_nz=264; "
            "t06_72_02:steps=250,r=-802.47,obs_nz=291; t06_108_02_duel:steps=59,r=125.62,obs_nz=249; "
            "t06_108_02_duel:steps=44,r=98.07,obs_nz=223; t06_72_02:steps=74,r=64.97,obs_nz=302\n"
            "crashes_last100_episodes: 0\n"
            "systemd_unit: is_active=active, main_pid=812345, pid_elapsed=3-04:22:10\n"
            "windows_keepalive_running: False"),
        "expect": [
            ("prob", "root_cause", "keepalive_missing_idle", 0.25),
            ("prob", "root_cause", "ep_runner_stuck", 0.10),
            ("noul_max", "need_human_now", 0.90),
        ],
        "note": "2026-09-21 真实判决: keepalive_missing_idle(0.81,conf=0.74) advice=MONITOR_ONLY",
    },
    {
        "id": "red_crash_01", "suite": "RED",
        "state": (
            "ALERT: C2 L0: 近 100 局中 4 次崩溃 (SIGSEGV/SIGABRT)，触发复发 SOP，翻 crashlog/\n"
            "log_staleness_minutes: 2.7\n"
            "recent_episodes(last5, map:steps,r,obs_nz): t06_72_02:steps=250,r=-85.78,obs_nz=223; "
            "t06_72_02:steps=250,r=57.88,obs_nz=249; t06_72_02:steps=113,r=-17.03,obs_nz=348\n"
            "crashes_last100_episodes: 0\n"
            "systemd_unit: is_active=active, main_pid=812345, pid_elapsed=3-04:15:00\n"
            "windows_keepalive_running: True"),
        "expect": [
            ("prob", "root_cause", "crash_recurrence", 0.20),
            ("noul_max", "need_human_now", 0.85),
        ],
        "note": "2026-09-21 真实判决: crash_recurrence(0.67,conf=0.58) advice=MONITOR_ONLY",
    },
    {
        "id": "yellow_neg_01", "suite": "YELLOW",
        "state": (
            "ALERT: 连续 3 局大负 r=[-802.47,-165.97,-147.77]\n"
            "log_staleness_minutes: 4.0\n"
            "recent_episodes(last5, map:steps,r,obs_nz): t06_72_02:steps=250,r=-42.35,obs_nz=264; "
            "t06_72_02:steps=250,r=-802.47,obs_nz=291; t06_108_02_duel:steps=59,r=125.62,obs_nz=249; "
            "t06_108_02_duel:steps=44,r=98.07,obs_nz=223; t06_72_02:steps=74,r=64.97,obs_nz=302\n"
            "crashes_last100_episodes: 0\n"
            "systemd_unit: is_active=active, main_pid=812345, pid_elapsed=3-04:22:10\n"
            "windows_keepalive_running: True"),
        "expect": [
            ("noul_max", "escalate_watch", 0.85),
            ("noul_min", "is_known_noise", 0.05),
            ("score_range", "severity", 0, 3),
        ],
        "note": "2026-09-21 真实判决: known_noise=0.39 escalate=0.49 advice=KEEP_WATCHING",
    },
    {
        "id": "fail_conv_01", "suite": "FAIL",
        "state": (
            "H3M map: Dragon Orb.h3m\n"
            "stage: convert_fail\n"
            "error: /home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap: "
            "Symbol `_ZN13GameConstants12VCMI_VERSIONE' has different size in shared object, "
            "consider re-linking\n"
            "detail: "),
        "expect": [
            ("prob", "fail_cause", "convert_defect", 0.12),
        ],
        "note": "2026-09-21 真实判决: convert_defect(p=0.54~0.64, conf≈0.5, 贴边判决取概率带)",
    },
    {
        "id": "pool_water_01", "suite": "POOL",
        "state": (
            "Map: Brave New World.h3m (pool name: brave_new_world_h3m.vmap)\n"
            "version=AB size=108 players=8 teams=2 difficulty=1\n"
            "victory=集兵 loss=标准\n"
            "terrain: layer=单层 water_pct=48.2 swamp_pct=0.0 land_components=3 has_island=True\n"
            "objects: count=3119 monsters=True underground_stripped=0\n"
            "verification: steps=250/250 rew=-41.2 (250-step model-driven episode)\n"
            "Background: 250-step episodes; current model trained on 36-108 size maps "
            "(duel/1v3/T06 family); underground already stripped for dual-hero same-layer play."),
        "expect": [
            ("prob", "risk_tag", "open_water_isolation", 0.15),
            ("score_range", "train_value", 1, 4),
        ],
        "note": "2026-09-21 真实判决: value=2.11 risk=open_water_isolation(0.48)",
    },
]

# ---------------------------------------------------------------- JEV 调用


def call_jev(questions: dict, state_text: str) -> dict:
    req = {"state": state_text, "questions": questions}
    r = subprocess.run(
        ["jev", "run", "--provider", PROVIDER, "-"],
        input=json.dumps(req, ensure_ascii=False).encode("utf-8"),
        capture_output=True, timeout=JEV_TIMEOUT)
    out = json.loads(r.stdout.decode("utf-8", errors="replace"))
    if not out.get("ok", True) and "error" in out:
        raise RuntimeError(str(out["error"])[:200])
    return out


def load_question_sets() -> dict:
    """import 三个脚本当前生效的问题集 (criteria 改动自动被覆盖)。"""
    triage = importlib.import_module("train_alert_triage")
    fail_mod = importlib.import_module("h3m_fail_triage")
    pool_mod = importlib.import_module("h3m_pool_rank")
    return {
        "RED": triage._REQUESTS["RED"],
        "YELLOW": triage._REQUESTS["YELLOW"],
        "FAIL": fail_mod.QUESTIONS,
        "POOL": pool_mod.QUESTIONS,
    }, triage.advice_of


# ---------------------------------------------------------------- 断言


def check(g: dict, ans: dict, advice_fn) -> list:
    """行为带断言: 返回失败原因列表 (空 = 通过)。
    断言元组:
      ("prob", <question>, <option>, <min_p>)   期望选项概率下限 (choice)
      ("noul_max"/"noul_min", <question>, <bound>)  noul 概率上下限
      ("score_range", <question>, <lo>, <hi>)   score 区间
    """
    fails = []
    for rule in g["expect"]:
        kind, q = rule[0], rule[1]
        if kind == "prob":
            opt, floor = rule[2], rule[3]
            p = ans.get(q, {}).get("probabilities", {}).get(opt)
            if p is None or p < floor:
                fails.append(f"{q}: {opt} p={p} < {floor}")
        elif kind == "noul_max":
            v = ans.get(q, {}).get("noul")
            if v is None or v > rule[2]:
                fails.append(f"{q}: noul={v} > {rule[2]}")
        elif kind == "noul_min":
            v = ans.get(q, {}).get("noul")
            if v is None or v < rule[2]:
                fails.append(f"{q}: noul={v} < {rule[2]}")
        elif kind == "score_range":
            v = ans.get(q, {}).get("score")
            lo, hi = rule[2], rule[3]
            if v is None or not (lo <= v <= hi):
                fails.append(f"{q}: score={v} outside [{lo},{hi}]")
        else:
            fails.append(f"unknown rule kind: {kind}")
    return fails


# ---------------------------------------------------------------- 主流程


def main() -> int:
    ap = argparse.ArgumentParser(description="JEV 判决金标回归 (改 criteria 前后必跑)")
    ap.add_argument("--suite", choices=["RED", "YELLOW", "FAIL", "POOL"], default="")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    sets, advice_fn = load_question_sets()
    goldens = [g for g in GOLDENS if not args.suite or g["suite"] == args.suite]

    results, total_cost, n_pass = [], 0.0, 0
    for g in goldens:
        try:
            out = call_jev(sets[g["suite"]], g["state"])
            ans, usage = out.get("answers", {}), out.get("usage", {})
            total_cost += usage.get("cost") or 0.0
            fails = check(g, ans, advice_fn)
            ok = not fails
            n_pass += ok
            results.append({"id": g["id"], "suite": g["suite"], "pass": ok,
                            "fails": fails, "answers": ans, "cost": usage.get("cost")})
            print(f"[{'PASS' if ok else 'FAIL'}] {g['id']:<14} {('; '.join(fails) or g['note'])}")
        except Exception as e:
            results.append({"id": g["id"], "suite": g["suite"], "pass": False,
                            "fails": [f"error: {str(e)[:150]}"]})
            print(f"[FAIL] {g['id']:<14} error: {str(e)[:150]}")

    summary = {"total": len(goldens), "passed": n_pass,
               "failed": len(goldens) - n_pass, "cost": total_cost,
               "results": results}
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n==== 金标回归: {n_pass}/{len(goldens)} 通过, JEV 成本 ${total_cost:.5f} ====")
    if n_pass < len(goldens):
        print("存在行为漂移: 若为有意变更, 请同步更新本脚本 GOLDENS 与 note")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
