# -*- coding: utf-8 -*-
"""
OPS-JEV-01 训练告警根因分类旁路 (2026-09-20, 09-21 扩展黄警)
====================================================
定位: train_health_monitor.ps1 触发 TRAIN RED/YELLOW 告警时, 后台调用本脚本,
      收集训练现场上下文 -> JEV 决策模型 (OpenRouter 路由) 一次并行多问 ->
      根因分类 + 置信度 + 处置建议, 追加到 monitor_alerts.log。

铁律:
  - 纯旁路: 不拦截/不修改/不重启任何训练进程; 失败只写 [TRIAGE-ERR], 永不抛出
  - 不进 WSL 训练进程, 只在 Windows 监控侧运行
  - key 不经过本脚本 (jev CLI 从 OS 凭据库自取)

RED 4 问 (单次并行调用, 实测 ~$0.00003/次):
  root_cause        choice: keepalive_missing_idle / ep_runner_stuck / crash_recurrence / slow_episode_normal / other
  need_human_now    noul:   是否需要立即人工介入
  safe_auto_restart noul:   systemctl restart (checkpoint resume) 是否安全
  severity          score:  L1 无影响 .. L5 危及数据/反复崩溃

YELLOW 3 问 (大负局定性, 09-21):
  is_known_noise    noul:   大负局是否为 duel 族已知底噪
  escalate_watch    noul:   是否提示真退化需加密观察
  severity          score:  L0 底噪可忽略 .. L4 快速退化

处置建议 (本地规则, 不依赖模型):
  RED:    need_human>=0.70 -> HUMAN_NOW; need_human<0.50 且 safe_restart>=0.70 -> AUTO_RESTART_OK; 其余 MONITOR_ONLY
  YELLOW: noise>=0.70 且 escalate<0.50 -> DISMISS_AS_NOISE; escalate>=0.70 -> INVESTIGATE_NOW; 其余 KEEP_WATCHING

用法:
  python train_alert_triage.py --alert "<告警原文>"                          # RED 默认
  python train_alert_triage.py --alert "连续 3 局大负 r=..." --level YELLOW  # 黄警
  python train_alert_triage.py --alert "..." --dry-run                       # 只收集上下文打印
  python train_alert_triage.py --alert "..." --cooldown-min 0                # 跳过防抖强制分诊
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\Bigdata\hero3_fresh")
TRAIN_LOG = BASE / "train_loop.log"
ALERT_LOG = Path(r"D:\Bigdata\hero3_fresh\py\monitor_alerts.log")
STATE_FILE = Path(r"D:\Bigdata\hero3_fresh\py\.triage_state.json")

PROVIDER = "openrouter"          # jev CLI 路由 (key 存于 jev-cli credentials)
JEV_TIMEOUT = 45                 # JEV 调用整体超时秒
WSL_TIMEOUT = 15
TAIL_BYTES = 256 * 1024          # 读日志尾部 256KB

# 告警签名归类 (防抖键; 告警原文每轮含变化数字, 必须归一)
SIG_RULES = [
    ("missing_log", ("不存在",)),
    ("crash_recurrence", ("C2 L0",)),
    ("stale_log", ("无更新",)),
    ("neg_r_streak", ("连续 3 局",)),
]


def classify_alert(msg: str) -> str:
    for sig, keys in SIG_RULES:
        if any(k in msg for k in keys):
            return sig
    return "generic:" + msg[:20]


# ---------------------------------------------------------------- 上下文收集

def read_log_tail(path: Path, nbytes: int = TAIL_BYTES) -> str:
    if not path.exists():
        return ""
    size = path.stat().st_size
    with open(path, "rb") as f:
        f.seek(max(0, size - nbytes))
        return f.read().decode("utf-8", errors="replace")


def collect_context() -> dict:
    ctx = {}
    # 1) train_loop.log 年龄与最近局面
    if TRAIN_LOG.exists():
        age_s = time.time() - TRAIN_LOG.stat().st_mtime
        ctx["log_age_minutes"] = round(age_s / 60, 1)
        tail = read_log_tail(TRAIN_LOG)
        ep_rows = re.findall(
            r"ep_steps=(\d+)\s+r=([-+]?\d*\.?\d+).*?obs_nz=(\d+)(?:\s+map=(\S+))?", tail)
        ctx["recent_episodes"] = [
            {"ep_steps": int(a), "r": float(b), "obs_nz": int(c), "map": m or "?"}
            for a, b, c, m in ep_rows[-10:]
        ]
        flt = re.findall(r"\[FILTER\].*", tail)
        last100 = flt[-100:]
        ctx["crashes_last100"] = sum(
            1 for l in last100 if re.search(r"SIGSEGV|SIGABRT", l))
    else:
        ctx["log_age_minutes"] = None
        ctx["recent_episodes"] = []
        ctx["crashes_last100"] = None

    # 2) WSL 侧训练单元状态 (system 级 unit, 踩坑 #195/#201: 禁 --user)
    try:
        r = subprocess.run(
            ["wsl", "bash", "-c",
             'P=$(systemctl show -p MainPID --value homm3-train-v5 2>/dev/null);'
             'echo "is_active=$(systemctl is-active homm3-train-v5 2>&1)";'
             'echo "main_pid=$P";'
             'echo "pid_elapsed=$(ps -o etime= -p "$P" 2>/dev/null | tr -d \x27 \x27)"'],
            capture_output=True, text=True, timeout=WSL_TIMEOUT)
        kv = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
        ctx["wsl_unit"] = {
            "is_active": kv.get("is_active", "unknown"),
            "main_pid": kv.get("main_pid", "unknown"),
            "pid_elapsed": kv.get("pid_elapsed") or "n/a",
        }
    except Exception as e:
        ctx["wsl_unit"] = {"error": str(e)[:80]}

    # 3) Windows keepalive (踩坑 #114: wsl.exe sleep infinity 常驻防 idle shutdown)
    try:
        ps_cmd = ("Get-CimInstance Win32_Process -Filter \"name='wsl.exe'\" "
                  "| Select-Object -ExpandProperty CommandLine")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd],
                           capture_output=True, text=True, timeout=WSL_TIMEOUT)
        ctx["keepalive_running"] = "sleep infinity" in (r.stdout or "")
    except Exception as e:
        ctx["keepalive_running"] = None
        ctx["keepalive_error"] = str(e)[:80]
    return ctx


def build_state_text(ctx: dict, alert: str) -> str:
    eps = ctx.get("recent_episodes") or []
    ep_str = "; ".join(f"{e.get('map', '?')}:steps={e['ep_steps']},r={e['r']},obs_nz={e['obs_nz']}"
                       for e in eps[-5:]) or "none"
    wu = ctx.get("wsl_unit") or {}
    lines = [
        f"ALERT: {alert}",
        f"log_staleness_minutes: {ctx.get('log_age_minutes')}",
        f"recent_episodes(last5, map:steps,r,obs_nz): {ep_str}",
        f"crashes_last100_episodes: {ctx.get('crashes_last100')}",
        f"systemd_unit: is_active={wu.get('is_active')}, main_pid={wu.get('main_pid')}, pid_elapsed={wu.get('pid_elapsed')}",
        f"windows_keepalive_running: {ctx.get('keepalive_running')}",
        "Background: PPO training of HoMM3 AI in WSL, managed by systemd unit homm3-train-v5.",
        "Map pool note: maps whose name contains 'duel' (e.g. 36X36_02_duel, 72X72_02_duel, 108X108_02_duel) "
        "are known hard negatives - large negative reward on them is an accepted baseline, not a regression.",
        "Known failure modes: (a) WSL idle shutdown when Windows keepalive process missing - unit appears dead; "
        "(b) ep_runner subprocess hung while trainer process alive - log stalls but PID alive; "
        "(c) recurring VCMI SIGSEGV/SIGABRT crashes; (d) a single long episode can legitimately take minutes.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- JEV 调用

_RED_QUESTIONS = {
    "root_cause": {
        "type": "choice",
        "instructions": "What is the most likely root cause of this training alert?",
        "criteria": {
            "keepalive_missing_idle": "WSL distro idle shutdown because the Windows keepalive process is missing; training died with it",
            "ep_runner_stuck": "ep_runner episode subprocess hung/deadlocked while the trainer process is still alive",
            "crash_recurrence": "repeated VCMI SIGSEGV/SIGABRT crashes killing episodes",
            "slow_episode_normal": "just one unusually long/slow episode, no real fault",
            "other": "anything else",
        },
    },
    "need_human_now": {
        "type": "noul",
        "instructions": "Does this situation require a human to intervene right now?",
    },
    "safe_auto_restart": {
        "type": "noul",
        "instructions": "Would it be safe and useful to restart the training unit now via systemctl restart with checkpoint resume?",
    },
    "severity": {
        "type": "score",
        "instructions": "How severe is this alert?",
        "criteria": [
            "cosmetic, no impact",
            "minor, monitor only",
            "moderate, degraded but training continues",
            "serious, training stalled, restart needed",
            "critical, data loss risk or repeated crashes",
        ],
    },
}

# 黄警轻量 3 问: 大负局定性 (duel 底噪 vs 真退化)
_YELLOW_QUESTIONS = {
    "is_known_noise": {
        "type": "noul",
        "instructions": "Are these large-negative episodes explained by known hard-negative maps (name contains 'duel') or other accepted baseline noise, rather than a real regression?",
    },
    "escalate_watch": {
        "type": "noul",
        "instructions": "Does this pattern suggest a real training regression that deserves closer monitoring or early intervention?",
    },
    "severity": {
        "type": "score",
        "instructions": "How concerning is this yellow-level alert?",
        "criteria": [
            "accepted baseline noise, ignore",
            "mild, keep watching",
            "moderate, correlated with a recent change, investigate soon",
            "serious, likely real regression, investigate now",
            "critical, training is degrading rapidly",
        ],
    },
}

_REQUESTS = {"RED": _RED_QUESTIONS, "YELLOW": _YELLOW_QUESTIONS}


def call_jev(state_text: str, timeout: int = JEV_TIMEOUT, level: str = "RED") -> dict:
    req = {"state": state_text, "questions": _REQUESTS.get(level, _RED_QUESTIONS)}
    payload = json.dumps(req, ensure_ascii=False)
    t0 = time.time()
    r = subprocess.run(
        ["jev", "run", "--provider", PROVIDER, "-"],
        input=payload.encode("utf-8"), capture_output=True, timeout=timeout)
    elapsed = round(time.time() - t0, 2)
    out = json.loads(r.stdout.decode("utf-8", errors="replace"))
    if not out.get("ok", True) and "error" in out:
        raise RuntimeError(out["error"][:200])
    out["_elapsed_s"] = elapsed
    return out


# ---------------------------------------------------------------- 输出与防抖

def advice_of(level: str, answers: dict) -> str:
    if level == "YELLOW":
        noise = answers.get("is_known_noise", {}).get("noul", 0.5)
        esc = answers.get("escalate_watch", {}).get("noul", 0.5)
        if noise >= 0.70 and esc < 0.50:
            return "DISMISS_AS_NOISE"
        if esc >= 0.70:
            return "INVESTIGATE_NOW"
        return "KEEP_WATCHING"
    nh = answers.get("need_human_now", {}).get("noul", 0.5)
    sr = answers.get("safe_auto_restart", {}).get("noul", 0.0)
    if nh >= 0.70:
        return "HUMAN_NOW"
    if nh < 0.50 and sr >= 0.70:
        return "AUTO_RESTART_OK"
    return "MONITOR_ONLY"


def append_alert_log(line: str):
    with open(ALERT_LOG, "a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(sig: str):
    STATE_FILE.write_text(json.dumps(
        {"last_triage_ts": datetime.now().isoformat(timespec="seconds"),
         "last_sig": sig}, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser(description="JEV 告警根因分类旁路 (纯旁路, 永不阻塞监控)")
    ap.add_argument("--alert", required=True, help="告警原文 (来自 train_health_monitor.ps1)")
    ap.add_argument("--level", choices=["RED", "YELLOW"], default="RED",
                    help="告警级别: RED=死亡/停滞 4 问, YELLOW=大负局定性 3 问 (default RED)")
    ap.add_argument("--cooldown-min", type=float, default=10.0,
                    help="同类告警分诊冷却分钟数 (default 10)")
    ap.add_argument("--timeout", type=int, default=JEV_TIMEOUT)
    ap.add_argument("--dry-run", action="store_true", help="只收集上下文打印, 不调 JEV 不写日志")
    args = ap.parse_args()

    sig = f"{args.level}:{classify_alert(args.alert)}"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        ctx = collect_context()
        if args.dry_run:
            state_text = build_state_text(ctx, args.alert)
            print(json.dumps({"sig": sig, "context": ctx,
                              "state_text": state_text},
                             ensure_ascii=False, indent=2))
            return 0

        # 防抖: 同签名冷却期内跳过
        st = load_state()
        if st.get("last_sig") == sig and st.get("last_triage_ts"):
            last = datetime.fromisoformat(st["last_triage_ts"])
            dt_min = (datetime.now() - last).total_seconds() / 60
            if dt_min < args.cooldown_min:
                return 0  # 静默跳过, 不刷屏告警日志

        out = call_jev(build_state_text(ctx, args.alert),
                       timeout=args.timeout, level=args.level)
        ans, usage = out.get("answers", {}), out.get("usage", {})
        cost = usage.get("cost")

        if args.level == "YELLOW":
            noise = ans.get("is_known_noise", {}).get("noul")
            esc = ans.get("escalate_watch", {}).get("noul")
            sev = ans.get("severity", {})
            line = (f"[TRIAGE-{args.level}] {ts} sig={sig} alert=\"{args.alert}\" | "
                    f"known_noise={noise} escalate={esc} "
                    f"severity={sev.get('score')}/4(conf={sev.get('confidence')}) "
                    f"advice={advice_of(args.level, ans)} | "
                    f"cost=${cost} tok_in={usage.get('input_tokens')} "
                    f"elapsed={out.get('_elapsed_s')}s id={out.get('id', '')}")
        else:
            rc = ans.get("root_cause", {})
            rc_pick = rc.get("choice", "?")
            rc_p = rc.get("probabilities", {}).get(rc_pick)
            rc_conf = rc.get("confidence")
            sev = ans.get("severity", {})
            nh = ans.get("need_human_now", {}).get("noul")
            sr = ans.get("safe_auto_restart", {}).get("noul")
            line = (f"[TRIAGE-{args.level}] {ts} sig={sig} alert=\"{args.alert}\" | "
                    f"cause={rc_pick}(p={rc_p},conf={rc_conf}) "
                    f"need_human={nh} safe_restart={sr} "
                    f"severity={sev.get('score')}/4(conf={sev.get('confidence')}) "
                    f"advice={advice_of(args.level, ans)} | "
                    f"cost=${cost} tok_in={usage.get('input_tokens')} "
                    f"elapsed={out.get('_elapsed_s')}s id={out.get('id', '')}")
        append_alert_log(line)
        save_state(sig)
        print(line)
        return 0

    except Exception as e:
        # 旁路铁律: 任何失败只记一行, 不上抛
        try:
            append_alert_log(f"[TRIAGE-ERR] {ts} sig={sig} error={str(e)[:200]}")
        except Exception:
            pass
        print(f"[TRIAGE-ERR] {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
