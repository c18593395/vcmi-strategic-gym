#!/usr/bin/env python3
"""
h3m_batch_pipeline.py — 官方 H3M 全量 → 训练池管线 (2026-09-18)

用户需求: 所有官方 H3M 一个一个转, 转换 → 真实训练测试通过 → 改名 _h3m →
转入新建目录, 准备加入训练。

流程 (每张图):
  1. 断点: h3m_pool/<safe>_h3m.vmap 已存在且 report PASS → skip
  2. 转换: h3m2vmap --save --no-r1 (R2v2 智能重配默认开)
  3. 地下检测: mapLevels 有 underground → strip_underground 去地下层
     (双方英雄同层作战; 无地下图天然满足, 跳过)
  4. 命名: <原名空格转下划线小写>_h3m.vmap (_h3m 过 strategic_env 图名断言)
  5. 部署 rel/bin/data/Maps + 100 步模型驱动训练验证
     (当前 checkpoint + 训练同款引导; 结构性死因 3-5 秒即暴露)
  6. PASS → maps/training/h3m_pool/; FAIL → 删 rel/bin 副本, 记录原因
  7. 断点报告 maps/h3m_to_vmap/_pipeline_report.json

用法:
  python py/h3m_batch_pipeline.py                 # 全量 (跳过已完成)
  python py/h3m_batch_pipeline.py --only KEYWORD  # 只跑名字含 KEYWORD 的图
  python py/h3m_batch_pipeline.py --steps 250     # 验证步数 (默认 100)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")

ROOT = "/mnt/d/Bigdata/hero3_fresh"
H3M_DIR = "/home/administrator/vcmi-native/rel/bin/data/Maps"
BIN = "/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap"
REL_MAPS = "/home/administrator/vcmi-native/rel/bin/data/Maps"
POOL = f"{ROOT}/maps/training/h3m_pool"
WORK = "/tmp/h3m_pipeline"
REPORT = f"{ROOT}/maps/h3m_to_vmap/_pipeline_report.json"
CKPT_DIR = f"{ROOT}/checkpoints"
VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = f"{ROOT}/ep_runner_one.py"


def newest_ckpt():
    cks = sorted(CKPT_DIR and [f for f in os.listdir(CKPT_DIR)
                               if f.startswith("wsl2_ckpt_") and f.endswith(".pt")],
                 key=lambda f: int(f.replace("wsl2_ckpt_", "").replace(".pt", "")))
    return os.path.join(CKPT_DIR, cks[-1]) if cks else None


def safe_name(h3m_path):
    """When Dragons Clash → when_dragons_clash (管线统一加 _h3m 后缀)"""
    stem = Path(h3m_path).stem
    s = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_").lower()
    return s


def run(cmd, timeout, **kw):
    # #248 口径: 转换器必须 cwd=vcmi-native (config/Mods 数据依赖)
    kw.setdefault("cwd", "/home/administrator/vcmi-native")
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, **kw)
    except subprocess.TimeoutExpired:
        return None


def train_verify(vmap_name, steps, ckpt, log_path):
    """250 步模型驱动局 = 与主训练 run_episode 完全同构 (含 WIN1 全套激励参数).
    返回 (ok, detail)."""
    traj = f"{WORK}/verify_traj.json"
    if os.path.exists(traj):
        os.remove(traj)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ("/home/administrator/vcmi-native/rel/bin:"
                              "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    cmd = [VENV, RUNNER, str(steps), traj, vmap_name,
           "--model", ckpt,
           "--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",
           "--reward_explore", "0.3",
           "--move_to_bias", "1.92", "--move_to_force", "60", "--act_loop_from_step", "60",
           "--economy_force", "24", "--cycle_detect", "5", "--act_loop_penalty", "1.0",
           "--guard_done_steps", "15", "--objective_reward", "30",
           "--blue_hero_grad", "0.2", "--blue_hero_grad_cap", "25",
           "--blue_hero_contact_r", "15", "--blue_hero_contact_d", "2",
           "--kill_r_first", "40", "--kill_r_next", "30",
           "--own_town_decay", "0.5", "--own_town_max_visits", "4",
           "--blue_hero_attack_bypass", "1", "--attack_f_min", "-1",
           "--use_nk2_shaping", "--nk2_shaping_scale", "0.45",
           "--target_chain", "scorer"]
    with open(log_path, "w") as lf:
        p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT,
                           env=env, timeout=steps * 12 + 300)
    rc = p.returncode
    if rc not in (0, 124):
        return False, f"runner rc={rc} (139=segfault)"
    if not os.path.exists(traj):
        return False, "traj missing"
    try:
        t = json.load(open(traj))
    except Exception:
        return False, "traj 损坏"
    if t.get("error"):
        return False, f"traj error: {t['error']}"
    steps_done = t.get("steps") or 0
    if steps_done < max(30, steps // 2):
        return False, f"steps={steps_done}<50% (早期死亡/异常)"
    return True, f"steps={steps_done}/{steps} rew={t.get('total_rew')}"


def has_underground(vmap_path):
    import zipfile
    import strip_underground_vmap as su
    with zipfile.ZipFile(vmap_path) as z:
        h = su.load_json(z, "header.json")   # 带 // 注释剥离 (VCMI saveMap 特产)
        return "underground" in (h.get("mapLevels") or {})


def _extract_steps(detail):
    """'steps=198/250 rew=...' → 198"""
    m = re.search(r"steps=(\d+)", detail or "")
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只处理名字含该关键词的 h3m")
    ap.add_argument("--steps", type=int, default=250, help="验证局步数 (默认 250 = 训练 STEPS_PER_EP 同款)")
    args = ap.parse_args()

    os.makedirs(POOL, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    report = {}
    if os.path.exists(REPORT):
        try:
            report = json.load(open(REPORT))
        except Exception:
            report = {}

    ckpt = newest_ckpt()
    if not ckpt:
        print("[FATAL] checkpoints/ 无可用 checkpoint")
        return 1
    print(f"checkpoint: {os.path.basename(ckpt)}")

    h3ms = sorted(Path(H3M_DIR).glob("*.h3m"))
    if args.only:
        h3ms = [h for h in h3ms if args.only.lower() in h.name.lower()]
    print(f"待处理 {len(h3ms)} 张 (全池 {len(list(Path(H3M_DIR).glob('*.h3m')))})")

    n_ok = n_fail = n_skip = 0
    for i, h3m in enumerate(h3ms, 1):
        safe = safe_name(h3m)
        final_name = f"{safe}_h3m.vmap"
        final_path = os.path.join(POOL, final_name)
        st = report.get(h3m.name, {})
        if (st.get("status") == "PASS" and os.path.exists(final_path)
                and st.get("verify_steps", 0) >= args.steps):
            n_skip += 1
            continue

        print(f"\n[{i}/{len(h3ms)}] {h3m.name} → {final_name}", flush=True)
        t0 = time.time()
        entry = {"final": final_name}

        # 2) 转换 (R1 关, R2v2/R3/R4/R6/R7 默认) — 引擎偶发段错误, 最多 3 试
        raw = f"{WORK}/{safe}.raw.vmap"
        if os.path.exists(raw):
            os.remove(raw)
        r = None
        for attempt in range(3):
            r = run([BIN, "--save", str(h3m), raw, "--no-r1"], timeout=180)
            ok = (r is not None and r.returncode == 0
                  and os.path.exists(raw) and os.path.getsize(raw) > 100
                  and "SAVE OK" in (r.stdout or ""))
            if ok:
                break
            print(f"  convert 第{attempt+1}次失败, 重试...", flush=True)
            if os.path.exists(raw):
                os.remove(raw)
            time.sleep(2)
        if not ok:
            entry.update(status="convert_fail",
                         err=(r.stderr or r.stdout or "timeout")[-200:] if r else "timeout")
            report[h3m.name] = entry
            n_fail += 1
            print(f"  [FAIL] convert: {entry['err']}", flush=True)
            continue

        # 3) 地下检测 + 去地下
        cur = raw
        try:
            if has_underground(raw):
                import strip_underground_vmap as su
                outp, audit = su.strip_underground(raw, WORK)
                if audit.get("selfcheck") != "OK":
                    entry.update(status="strip_fail", err=audit.get("selfcheck"))
                    report[h3m.name] = entry
                    n_fail += 1
                    print(f"  [FAIL] strip: {audit.get('selfcheck')}", flush=True)
                    continue
                cur = str(outp)
                entry["stripped"] = audit.get("objects_removed_underground", 0)
        except Exception as e:
            entry.update(status="strip_fail", err=str(e)[:200])
            report[h3m.name] = entry
            n_fail += 1
            print(f"  [FAIL] strip 异常: {e}", flush=True)
            continue

        # 5) 部署 + 训练验证
        dst = os.path.join(REL_MAPS, final_name)
        import shutil
        shutil.copy(cur, dst)
        ok, detail = train_verify(final_name, args.steps, ckpt,
                                  f"{WORK}/verify_{safe}.log")
        entry["verify"] = detail
        entry["verify_steps"] = steps_done if (steps_done := _extract_steps(detail)) else 0
        if not ok:
            entry["status"] = "verify_fail"
            report[h3m.name] = entry
            n_fail += 1
            print(f"  [FAIL] 训练验证: {detail} ({time.time()-t0:.0f}s)", flush=True)
            try:
                os.remove(dst)  # 不合格图清出运行时
            except OSError:
                pass
            continue

        # 6) 入池
        shutil.copy(cur, final_path)
        entry.update(status="PASS")
        report[h3m.name] = entry
        n_ok += 1
        print(f"  [PASS] {detail} → h3m_pool ({time.time()-t0:.0f}s)", flush=True)

        # 每张落盘断点
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n==== 管线汇总: PASS={n_ok} FAIL={n_fail} SKIP={n_skip} ====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
