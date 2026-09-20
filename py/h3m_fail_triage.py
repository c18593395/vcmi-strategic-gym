# -*- coding: utf-8 -*-
"""
OPS-JEV-02 WIN-4 批转 FAIL 归因 (2026-09-21)
====================================================
定位: h3m_batch_pipeline.py 批跑产生的 FAIL 条目, 用 JEV 做根因归因分类,
      替代人工逐图翻 traj/日志。Windows 侧运行 (jev CLI + key 都在 Windows)。

数据流:
  批跑 (WSL) verify_fail 现场取证 → maps/h3m_to_vmap/_fail_triage/<safe>/
      entry.json (report 条目 + traj 摘要: steps/rew/末 10 act/末 20 rew)
      verify_tail.log (验证日志尾 32KB)
  本脚本 (Windows) 读 report + 取证 → JEV 一次并行 3 问 → _fail_triage/_triage_report.json

JEV 3 问 (每图一次调用, ~$0.0001/图, 159 张全 fail 也 < $0.02):
  fail_cause     choice: open_trapped / water_path_fail / battle_crash / timeout_no_terminal / convert_defect / reward_mismatch / other
  fix_worthwhile noul:   修复重试是否值得 (vs 放弃该图)
  fix_difficulty score:  0 重试即可 / 1 改管线参数 / 2 需修管线代码 / 3 需改 h3m2vmap 引擎

用法:
  python h3m_fail_triage.py                 # 全量 FAIL 归因 (已归因的跳过)
  python h3m_fail_triage.py --one warm      # 只归因名字含 warm 的 FAIL 图
  python h3m_fail_triage.py --force         # 已归因的重跑
  python h3m_fail_triage.py --limit 3       # 只跑前 3 张 (试跑)
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r"D:\Bigdata\hero3_fresh")
REPORT = BASE / "maps" / "h3m_to_vmap" / "_pipeline_report.json"
TRIAGE_DIR = BASE / "maps" / "h3m_to_vmap" / "_fail_triage"
OUT = TRIAGE_DIR / "_triage_report.json"

PROVIDER = "openrouter"
JEV_TIMEOUT = 60
TAIL_CHARS = 6000          # verify_tail.log 送 JEV 的最大字符数

FAIL_STATUSES = ("convert_fail", "strip_fail", "verify_fail")

QUESTIONS = {
    "fail_cause": {
        "type": "choice",
        "instructions": "What is the most likely root cause of this map's verification failure?",
        "criteria": {
            "open_trapped": "hero gets fully blocked at/near start (all-blocked death), map layout traps the hero",
            "water_path_fail": "water/terrain makes objectives unreachable, hero wanders without progress",
            "battle_crash": "engine crash in battle or SIGSEGV/SIGABRT killed the runner",
            "timeout_no_terminal": "episode ran to step limit without terminal - map too large or objective too far for the step budget",
            "convert_defect": "h3m2vmap conversion defect - missing/corrupted objects, players, layers or invalid map structure",
            "reward_mismatch": "model behaves pathologically on this map (loops, farm-negative) - reward/map mismatch rather than map defect",
            "other": "anything else",
        },
    },
    "fix_worthwhile": {
        "type": "noul",
        "instructions": "Is it worthwhile to fix and retry this map, rather than abandoning it from the training pool?",
    },
    "fix_difficulty": {
        "type": "score",
        "instructions": "How hard is the fix likely to be?",
        "criteria": [
            "trivial - just retry or tweak a flag",
            "easy - adjust pipeline parameter (steps, strip options)",
            "moderate - needs pipeline/tooling code change",
            "hard - needs h3m2vmap converter or engine work",
        ],
    },
}


def call_jev(state_text: str, timeout: int = JEV_TIMEOUT) -> dict:
    req = {"state": state_text, "questions": QUESTIONS}
    r = subprocess.run(
        ["jev", "run", "--provider", PROVIDER, "-"],
        input=json.dumps(req, ensure_ascii=False).encode("utf-8"),
        capture_output=True, timeout=timeout)
    out = json.loads(r.stdout.decode("utf-8", errors="replace"))
    if not out.get("ok", True) and "error" in out:
        raise RuntimeError(str(out["error"])[:200])
    return out


def build_state_verify(ev: dict, tail_text: str, h3m: str) -> str:
    ts = ev.get("traj_summary") or {}
    lines = [
        f"H3M map: {h3m}",
        f"verify detail: {ev.get('entry', {}).get('verify')}",
        f"traj_summary: steps={ts.get('steps')} total_rew={ts.get('total_rew')} error={ts.get('error')}",
        f"last_acts: {ts.get('last_acts')}",
        f"last_rews: {ts.get('last_rews')}",
        "---- verify log tail ----",
        tail_text[-TAIL_CHARS:],
    ]
    return "\n".join(lines)


def build_state_simple(h3m: str, entry: dict) -> str:
    return (f"H3M map: {h3m}\n"
            f"stage: {entry.get('status')}\n"
            f"error: {entry.get('err')}\n"
            f"detail: {entry.get('verify')}")


def triage_one(h3m: str, entry: dict, evidence: dict) -> dict:
    """evidence: {"entry_json": dict|None, "tail": str} — verify_fail 用, 其余 None/""."""
    if entry.get("status") == "verify_fail" and evidence.get("entry_json"):
        state = build_state_verify(evidence["entry_json"], evidence.get("tail", ""), h3m)
    else:
        state = build_state_simple(h3m, entry)
    out = call_jev(state)
    ans, usage = out.get("answers", {}), out.get("usage", {})
    fc = ans.get("fail_cause", {})
    pick = fc.get("choice", "?")
    return {
        "status": entry.get("status"),
        "fail_cause": pick,
        "cause_p": fc.get("probabilities", {}).get(pick),
        "cause_conf": fc.get("confidence"),
        "fix_worthwhile": ans.get("fix_worthwhile", {}).get("noul"),
        "fix_difficulty": ans.get("fix_difficulty", {}).get("score"),
        "cost": usage.get("cost"),
        "id": out.get("id", ""),
        "triaged_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="WIN-4 批转 FAIL 的 JEV 归因")
    ap.add_argument("--one", default="", help="只归因名字含该关键词的 FAIL 图")
    ap.add_argument("--limit", type=int, default=0, help="最多处理 N 张 (0=不限)")
    ap.add_argument("--force", action="store_true", help="已归因的也重跑")
    args = ap.parse_args()

    if not REPORT.exists():
        print(f"[FATAL] 报告不存在: {REPORT}")
        return 1
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    out_report = {}
    if OUT.exists():
        try:
            out_report = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            out_report = {}

    fails = {k: v for k, v in report.items()
             if v.get("status") in FAIL_STATUSES}
    if args.one:
        fails = {k: v for k, v in fails.items() if args.one.lower() in k.lower()}
    if not fails:
        print("无可归因的 FAIL 条目")
        return 0

    total_cost = 0.0
    done = 0
    simple_cache = {}   # (status, err) → 结果 — convert/strip_fail 同 err 系统性问题去重
    cause_counter = {}
    for i, (h3m, entry) in enumerate(sorted(fails.items()), 1):
        if not args.force and h3m in out_report:
            continue
        if args.limit and done >= args.limit:
            break
        safe = entry.get("final", "").replace("_h3m.vmap", "")
        evidence = {"entry_json": None, "tail": ""}
        if entry.get("status") == "verify_fail":
            ev_dir = TRIAGE_DIR / safe
            ev_file = ev_dir / "entry.json"
            if ev_file.exists():
                try:
                    evidence["entry_json"] = json.loads(ev_file.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"  [WARN] {h3m}: entry.json 解析失败 {e}")
            tail_file = ev_dir / "verify_tail.log"
            if tail_file.exists():
                evidence["tail"] = tail_file.read_text(encoding="utf-8", errors="replace")
            else:
                print(f"  [WARN] {h3m}: 无取证 (老条目或取证失败), 仅用 report err 归因")

        try:
            cache_key = (entry.get("status"), entry.get("err", "")) \
                if entry.get("status") != "verify_fail" else None
            if cache_key and cache_key in simple_cache:
                res = dict(simple_cache[cache_key])
                res["dedup"] = True   # 同 err 系统性问题, 复用首次归因
            else:
                res = triage_one(h3m, entry, evidence)
                if cache_key:
                    simple_cache[cache_key] = dict(res)
            out_report[h3m] = res
            cause_counter[res["fail_cause"]] = cause_counter.get(res["fail_cause"], 0) + 1
            if not res.get("dedup"):
                total_cost += res.get("cost") or 0.0
            done += 1
            print(f"[{i}/{len(fails)}] {h3m}: cause={res['fail_cause']}"
                  f"(p={res['cause_p']},conf={res['cause_conf']}) "
                  f"fix_worth={res['fix_worthwhile']} diff={res['fix_difficulty']}/3"
                  f"{' [同err去重]' if res.get('dedup') else ''}")
            # 每图落盘断点
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(out_report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
        except Exception as e:
            print(f"[{i}/{len(fails)}] {h3m}: [TRIAGE-ERR] {str(e)[:150]}")

    # 聚类汇总: 人一眼看出系统性模式
    print(f"\n==== 归因汇总: 完成 {done} 张 (新增调用), JEV 总成本 ${total_cost:.5f} ====")
    print("--- 按根因聚类 ---")
    for cause, n in sorted(cause_counter.items(), key=lambda x: -x[1]):
        print(f"  {cause}: {n} 张")
    steps1 = sum(1 for v in fails.values() if "steps=1<" in (v.get("verify") or ""))
    if steps1:
        print(f"  [模式提示] verify_fail 中 steps=1 (开局即死) 共 {steps1} 张 — "
              f"同模式系统性问题概率高, 优先查共性而非逐图修复")
    print(f"报告: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
