# -*- coding: utf-8 -*-
"""
OPS-JEV-03 WIN-4 后续: h3m_pool 图池训练价值排序 (2026-09-21)
====================================================
定位: 批转 PASS 图攒起来后, 用 JEV 对每张图做一次并行 3 问
      (训练价值 score / 主导风险 choice / 是否建议入主训练池 noul),
      产出按价值降序的入池优先级, 替代人工逐图挑图。
      模式来源: jevable.com TC39 Atlas / 批量评分项目 (一图一调用, ~$0.0001/图)。

输入 (三路 join, key = h3m 文件名):
  py/h3m_type_survey.json            rows[] 普查特征 (size/players/teams/water/island/...)
  maps/h3m_to_vmap/_pipeline_report.json  PASS 条目 (verify_steps/verify/stripped)
  maps/training/h3m_pool/<safe>_h3m.vmap  池内实际存在文件

输出:
  maps/h3m_to_vmap/_pool_rank.json   每图 {value, risk, include, ...}
  控制台: 按 train_value 降序 + 聚类统计

用法:
  python h3m_pool_rank.py                # 全池排序 (已排序的跳过)
  python h3m_pool_rank.py --limit 3      # 试跑前 3 张
  python h3m_pool_rank.py --force        # 已排序的重跑
  python h3m_pool_rank.py --top 20       # 只显示前 20
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r"D:\Bigdata\hero3_fresh")
SURVEY = BASE / "py" / "h3m_type_survey.json"
REPORT = BASE / "maps" / "h3m_to_vmap" / "_pipeline_report.json"
POOL = BASE / "maps" / "training" / "h3m_pool"
OUT = BASE / "maps" / "h3m_to_vmap" / "_pool_rank.json"

PROVIDER = "openrouter"
JEV_TIMEOUT = 60

QUESTIONS = {
    "train_value": {
        "type": "score",
        "instructions": ("How valuable is this map as a 1v7 PPO training environment "
                         "for our HoMM3 AI (red player vs blue alliance of MMAI bots, "
                         "250-step episodes)? Consider map variety, reachability of "
                         "objectives within the step budget, and opponent diversity."),
        "criteria": [
            "low - little training value (degenerate layout, unreachable objectives)",
            "below average - usable but redundant with better maps",
            "average - solid standard training map",
            "good - diverse layout or interesting strategic texture",
            "high - excellent variety, reachable objectives, strong training signal",
        ],
    },
    "risk_tag": {
        "type": "choice",
        "instructions": "What is the dominant risk of this map for training?",
        "criteria": {
            "open_water_isolation": "large open water may isolate starts or make naval objectives unreachable on foot",
            "start_trap": "start position risks early all-blocked death or tiny enclosed region",
            "unreachable_objective": "victory objective likely out of reach within 250 steps (huge map / far objective)",
            "ally_chaos": "many allied players/teams may make blue-side MMAI behavior unpredictable",
            "dense_neutral": "very heavy neutral monster presence may dominate early episodes",
            "none": "no dominant risk",
        },
    },
    "include": {
        "type": "noul",
        "instructions": "Should this map be included in the main training map pool now?",
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


def build_state(h3m: str, survey_row: dict, entry: dict) -> str:
    s = survey_row or {}
    lines = [
        f"Map: {h3m} (pool name: {entry.get('final')})",
        f"version={s.get('version')} size={s.get('size')} players={s.get('players')} "
        f"teams={s.get('teams')} difficulty={s.get('difficulty')}",
        f"victory={s.get('victory')} loss={s.get('loss')}",
        f"terrain: layer={s.get('layer')} water_pct={s.get('water_pct')} "
        f"swamp_pct={s.get('swamp_pct')} land_components={s.get('land_components')} "
        f"has_island={s.get('has_island')}",
        f"objects: count={s.get('obj_count')} monsters={s.get('monster')} "
        f"underground_stripped={entry.get('stripped', 0)}",
        f"verification: {entry.get('verify')} (250-step model-driven episode)",
        "Background: 250-step episodes; current model trained on 36-108 size maps "
        "(duel/1v3/T06 family); underground already stripped for dual-hero same-layer play.",
    ]
    return "\n".join(lines)


def rank_one(h3m: str, survey_row: dict, entry: dict) -> dict:
    out = call_jev(build_state(h3m, survey_row, entry))
    ans, usage = out.get("answers", {}), out.get("usage", {})
    tv = ans.get("train_value", {})
    rt = ans.get("risk_tag", {})
    pick = rt.get("choice", "?")
    return {
        "train_value": tv.get("score"),
        "value_conf": tv.get("confidence"),
        "risk_tag": pick,
        "risk_p": rt.get("probabilities", {}).get(pick),
        "include": ans.get("include", {}).get("noul"),
        "cost": usage.get("cost"),
        "id": out.get("id", ""),
        "ranked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="h3m_pool 训练价值 JEV 排序")
    ap.add_argument("--limit", type=int, default=0, help="最多处理 N 张 (0=不限)")
    ap.add_argument("--force", action="store_true", help="已排序的重跑")
    ap.add_argument("--top", type=int, default=30, help="控制台显示前 N 张 (default 30)")
    args = ap.parse_args()

    if not REPORT.exists():
        print(f"[FATAL] 批转报告不存在: {REPORT}")
        return 1
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    survey = {}
    if SURVEY.exists():
        for row in json.loads(SURVEY.read_text(encoding="utf-8")).get("rows", []):
            survey[row.get("h3m")] = row
    pool_files = {p.name for p in POOL.glob("*_h3m.vmap")} if POOL.exists() else set()

    # 候选 = report PASS 且池内文件存在
    cands = {}
    for h3m, entry in report.items():
        if entry.get("status") == "PASS" and entry.get("final") in pool_files:
            cands[h3m] = entry
    if not cands:
        print("池内暂无 PASS 图 (批转完成后运行)")
        return 0
    missing_survey = [h for h in cands if h not in survey]
    if missing_survey:
        print(f"[WARN] {len(missing_survey)} 张图无普查数据, 将以 report 字段降级评分")

    ranked = {}
    if OUT.exists():
        try:
            ranked = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            ranked = {}

    done, total_cost = 0, 0.0
    items = sorted(cands.items())
    for i, (h3m, entry) in enumerate(items, 1):
        if not args.force and h3m in ranked:
            continue
        if args.limit and done >= args.limit:
            break
        try:
            res = rank_one(h3m, survey.get(h3m), entry)
            ranked[h3m] = res
            total_cost += res.get("cost") or 0.0
            done += 1
            print(f"[{i}/{len(items)}] {h3m}: value={res['train_value']}/4"
                  f"(conf={res['value_conf']}) risk={res['risk_tag']}"
                  f"(p={res['risk_p']}) include={res['include']}")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(ranked, indent=2, ensure_ascii=False),
                           encoding="utf-8")
        except Exception as e:
            print(f"[{i}/{len(items)}] {h3m}: [RANK-ERR] {str(e)[:150]}")

    # 排序视图
    rows = [(h, r) for h, r in ranked.items() if h in cands]
    rows.sort(key=lambda x: (x[1].get("train_value") or -1,
                             x[1].get("include") or 0), reverse=True)
    print(f"\n==== 入池优先级 (本次新评 {done} 张, JEV 成本 ${total_cost:.5f}) ====")
    print(f"{'#':>3} {'value':>5} {'incl':>5} {'risk_tag':<22} map")
    for n, (h, r) in enumerate(rows[:args.top], 1):
        print(f"{n:>3} {str(r.get('train_value')):>5} "
              f"{r.get('include')!s:>5} {r.get('risk_tag', '?'):<22} {h}")
    include_cnt = sum(1 for _, r in rows if (r.get("include") or 0) >= 0.5)
    print(f"\n池内共 {len(cands)} 张; JEV 建议纳入(include>=0.5): {include_cnt} 张")
    print(f"报告: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
