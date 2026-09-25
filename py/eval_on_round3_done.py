#!/usr/bin/env python3
"""检测 Round 3 完成 → 跑基线评估 → 重启训练"""
import os
import subprocess, json, time, os, sys

LOG_WSL = os.environ.get("LOG_WSL", "/mnt/d/Bigdata/hero3_fresh/train_loop.log")
EVAL_FLAG = os.environ.get("EVAL_FLAG", "/mnt/d/Bigdata/hero3_fresh/.eval_round3_done")  # 检查 Round 3 是否已完成（3 个 DONE 行）
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "--", "bash", "-c",
     f'grep -c "^DONE:" {LOG_WSL}'],
    capture_output=True, text=True, timeout=15
)
done_count = int(result.stdout.strip() or 0)

if done_count < 3:
    sys.exit(0)  # Round 3 还没跑完

# 检查是否已经评估过
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "--", "bash", "-c",
     f'test -f {EVAL_FLAG} && echo "yes" || echo "no"'],
    capture_output=True, text=True, timeout=15
)
if result.stdout.strip() == "yes":
    sys.exit(0)  # 已评估过，跳过

# Round 3 完成，停止训练
subprocess.run(
    ["wsl", "-d", "Ubuntu", "--", "bash", "-c",
     "pkill -f train_loop.sh 2>/dev/null; pkill -f train_wsl2_ppo 2>/dev/null; sleep 3"],
    timeout=20
)

# 运行基线评估（取最新 checkpoint）
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "--", "bash", "-c",
     f'ls -t /mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_*.pt | head -1'],
    capture_output=True, text=True, timeout=15
)
latest_ckpt = result.stdout.strip()

# 通过 WSL python 跑评估（因为 StrategicEnv 在 WSL 里）
eval_cmd = [
    "wsl", "-d", "Ubuntu",
    "--", "bash", "-c",
    f'cd /home/administrator/vcmi-workspace && '
    f'export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel && '
    f'export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so && '
    f'python3 -u /mnt/d/Bigdata/hero3_fresh/eval_elo.py '
    f'--current_model "{latest_ckpt}" '
    f'--baseline_type stupidai '
    f'--step "$(echo {latest_ckpt} | grep -oP \'\\d+\' | tail -1)" '
    f'--games 10 2>&1'
]
print(f"Running eval: {latest_ckpt}", flush=True)
result = subprocess.run(eval_cmd, timeout=600)
print(f"Eval exit: {result.returncode}", flush=True)

# 标记已评估
subprocess.run(
    ["wsl", "-d", "Ubuntu", "--", "touch", EVAL_FLAG],
    timeout=10
)

# 重启训练
subprocess.run(
    ["wsl", "-d", "Ubuntu", "--",
     "bash", "/mnt/d/Bigdata/hero3_fresh/train_loop.sh"],
    timeout=5
)
print("Round 4 started", flush=True)
