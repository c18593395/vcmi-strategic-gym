#!/usr/bin/env python3
"""checkpoint 推送链路 (WSL2 训练侧编排):
  WSL 训练存档(.pt) → 导出 ONNX → scp 到服务器 → POST /models/load + activate
  → (WSL2 本地跑 WIN RATE 评测, 因为服务器是 ARM64 旧架构无法跑新模型)
  → 评测结果 POST 到服务器 :8088 结果中枢 + scp 落盘 → 打印摘要.

设计要点 (见 README / 知识库 §十五):
  - 服务器 172.16.2.40 的 .so 是 ARM64 旧架构 (256 维), 跑不了本 3464+terrain 模型, 故 WIN RATE 在 WSL2 算, 结果回传.
  - 服务器 :8080 仅做模型加载/推理注册 (部署侧); :8088 是 WIN RATE 历史中枢.
  - 本脚本必须在 WSL2 内运行 (依赖 venv + vcmi 引擎 + libmlclient).

用法:
  python3 ckpt_push_hook.py [--ckpt /path/wsl2_ckpt_123450.pt]
                           [--maps ...] [--games 8] [--blue MMAI_RANDOM]
                           [--no-eval] [--no-push]
"""
import argparse
import os
import sys
import json
import time
import subprocess

# ===== 路径配置 (WSL2) =====
VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
EXPORT = os.environ.get("EXPORT", "/mnt/d/Bigdata/hero3_fresh/scripts/export_rl_onnx.py")
WINRATE = os.environ.get("WINRATE", "/mnt/d/Bigdata/hero3_fresh/py/winrate_eval.py")
CKPT_DIR = os.environ.get("CKPT_DIR", "/mnt/d/Bigdata/hero3_fresh/checkpoints")
MODELS_BASE = os.environ.get("MODELS_BASE", "/mnt/d/Bigdata/hero3_fresh")  # VCMI / libmlclient 运行环境 (与 train_wsl2_ppo_v2.run_episode 一致)
LD_LIBRARY_PATH = os.environ.get("LD_LIBRARY_PATH", "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")
STRATEGIC_STATE_LIB = os.environ.get("STRATEGIC_STATE_LIB", "/home/administrator/vcmi-native/rel/bin/libmlclient.so")  # ===== 服务器配置 =====
SERVER = "172.16.2.40"
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15"]
INCOMING_DIR = "/DATA/hero3/models_incoming"
OUTPUT_DIR = "/DATA/hero3/output"
LOAD_URL = f"http://{SERVER}:8080/models/load"
ACTIVATE_URL = lambda name: f"http://{SERVER}:8080/models/{name}/activate"
RESULTS_URL = f"http://{SERVER}:8088/results"


def run(cmd, env=None, timeout=1800):
    print(f"[hook] $ {' '.join(cmd)}", flush=True)
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
    if p.stdout.strip():
        for l in p.stdout.strip().splitlines()[-20:]:
            print(f"  | {l}", flush=True)
    if p.returncode != 0:
        print(f"[hook] !! exit={p.returncode}", flush=True)
        if p.stderr.strip():
            for l in p.stderr.strip().splitlines()[-10:]:
                print(f"  ! {l}", flush=True)
    return p


def latest_checkpoint():
    if not os.path.isdir(CKPT_DIR):
        return None
    pts = [f for f in os.listdir(CKPT_DIR) if f.startswith("wsl2_ckpt_") and f.endswith(".pt")]
    if not pts:
        return None
    pts.sort(key=lambda f: int(f.replace("wsl2_ckpt_", "").replace(".pt", "")))
    return os.path.join(CKPT_DIR, pts[-1])


def ssh(cmd):
    return run(["ssh"] + SSH_OPTS + [f"root@{SERVER}"] + cmd)


def main():
    global SERVER, LOAD_URL, ACTIVATE_URL, RESULTS_URL
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="", help="指定 checkpoint .pt; 默认取 checkpoints/ 最新 wsl2_ckpt_<step>.pt")
    ap.add_argument("--maps", default="T05_adventure_36X36_01.vmap,T06_adventure_72X72_01_duel.vmap,King_of_Pain_h3m.vmap")
    ap.add_argument("--games", type=int, default=8)
    ap.add_argument("--blue", default="MMAI_RANDOM")
    ap.add_argument("--max_turns", type=int, default=250)
    ap.add_argument("--no-eval", action="store_true", help="只推送模型, 不跑 WIN RATE 评测")
    ap.add_argument("--no-push", action="store_true", help="只本地评测, 不推送服务器")
    ap.add_argument("--server", default=SERVER)
    args = ap.parse_args()

    SERVER = args.server
    LOAD_URL = f"http://{SERVER}:8080/models/load"
    ACTIVATE_URL = lambda name: f"http://{SERVER}:8080/models/{name}/activate"
    RESULTS_URL = f"http://{SERVER}:8088/results"

    ckpt = args.ckpt or latest_checkpoint()
    if not ckpt or not os.path.exists(ckpt):
        print(f"[hook] no checkpoint found (tried {ckpt})", flush=True)
        sys.exit(1)
    name = os.path.basename(ckpt).replace(".pt", "")
    print(f"[hook] checkpoint: {ckpt}  ->  model name: {name}", flush=True)

    t0 = time.time()

    # 1) 导出 ONNX (用于服务器 :8080 模型注册 / 部署侧)
    onnx_path = f"/tmp/{name}.onnx"
    if not args.no_push:
        p = run([VENV, EXPORT, ckpt, onnx_path], timeout=300)
        if p.returncode != 0 or not os.path.exists(onnx_path):
            print(f"[hook] ONNX 导出失败, 终止推送", flush=True)
            sys.exit(2)

    # 2) 推送 ONNX 到服务器 + /models/load + activate
    if not args.no_push:
        ssh(["mkdir", "-p", INCOMING_DIR])
        scp = run(["scp"] + SSH_OPTS + [onnx_path, f"root@{SERVER}:{INCOMING_DIR}/{name}.onnx"])
        if scp.returncode != 0:
            print(f"[hook] scp 失败", flush=True)
            sys.exit(3)
        # /models/load (若已加载会 400, 忽略)
        import urllib.request
        import urllib.error
        payload = json.dumps({"name": name, "path": f"{INCOMING_DIR}/{name}.onnx", "model_type": "onnx"}).encode()
        try:
            req = urllib.request.Request(LOAD_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"[hook] /models/load -> {resp.read().decode()[:200]}", flush=True)
        except urllib.error.HTTPError as e:
            print(f"[hook] /models/load HTTP {e.code}: {e.read().decode()[:160]} (已加载则忽略)", flush=True)
        # activate
        try:
            req = urllib.request.Request(ACTIVATE_URL(name), method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"[hook] activate -> {resp.read().decode()[:160]}", flush=True)
        except Exception as e:
            print(f"[hook] activate 失败 (非致命): {e}", flush=True)

    # 3) WSL2 本地 WIN RATE 评测 (服务器为 ARM64 旧架构, 跑不了新模型)
    result = None
    if not args.no_eval:
        out_json = f"/tmp/{name}_winrate.json"
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = LD_LIBRARY_PATH
        env["STRATEGIC_STATE_LIB"] = STRATEGIC_STATE_LIB
        p = run([VENV, WINRATE, "--model", ckpt, "--maps", args.maps,
                 "--games", str(args.games), "--blue", args.blue,
                 "--max_turns", str(args.max_turns), "--out", out_json],
                env=env, timeout=7200)
        if p.returncode == 0 and os.path.exists(out_json):
            with open(out_json) as f:
                result = json.load(f)
            print(f"[hook] WIN RATE = {result.get('win_rate')}%  (W={result.get('wins')} "
                  f"L={result.get('losses')} D={result.get('draws')} E={result.get('errors')})", flush=True)

    # 4) 结果回传服务器 (落盘 + POST :8088)
    if result and not args.no_push:
        # 解析 step
        step = ""
        if name.startswith("wsl2_ckpt_"):
            try:
                step = int(name.replace("wsl2_ckpt_", ""))
            except Exception:
                step = ""
        result["tag"] = "auto-push"
        result["step"] = step
        result["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        # scp 落盘
        ssh(["mkdir", "-p", OUTPUT_DIR])
        tmp_local = f"/tmp/{name}_winrate.json"
        with open(tmp_local, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        run(["scp"] + SSH_OPTS + [tmp_local, f"root@{SERVER}:{OUTPUT_DIR}/{name}_winrate.json"])
        # POST 结果中枢
        import urllib.request
        payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
        try:
            req = urllib.request.Request(RESULTS_URL, data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"[hook] results POST -> {resp.read().decode()[:160]}", flush=True)
        except Exception as e:
            print(f"[hook] results POST 失败 (非致命): {e}", flush=True)

    print(f"[hook] DONE in {time.time()-t0:.0f}s  model={name}  step={step}", flush=True)


if __name__ == "__main__":
    main()
