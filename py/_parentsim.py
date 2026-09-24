#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐字复刻 train_wsl2_ppo_v2.py 的 run_episode spawn 方式, 复现池图 traj 丢失。
用法: python3 _parentsim.py <map> <steps> <runs>
"""
import os, sys, time, subprocess, glob

VENV = "/home/administrator/vcmi-workspace/venv/bin/python"
RUNNER = "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py"
EP_TRAJ = "/tmp/traj_ep.json"          # 与训练完全同一路径
CKPTS = sorted(glob.glob("/mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_*.pt"),
               key=lambda p: int(p.rsplit("_", 1)[1].split(".")[0]), reverse=True)
CKPT = CKPTS[0] if CKPTS else None

MAP = sys.argv[1] if len(sys.argv) > 1 else "good_to_go_h3m.vmap"
STEPS = int(sys.argv[2]) if len(sys.argv) > 2 else 250
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 1

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = ("/home/administrator/vcmi-native/rel/bin:"
                          "/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel")
env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"

print("CKPT =", CKPT)

for i in range(1, RUNS + 1):
    if os.path.exists(EP_TRAJ):
        os.remove(EP_TRAJ)
    ep_log = "/tmp/_parentsim_ep_%d.log" % i
    cmd = [VENV, RUNNER, str(STEPS), EP_TRAJ, MAP, "--model", CKPT]
    cmd += ["--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",
            "--blue_hero_attack_bypass", "1", "--blue_hero_contact_d", "2",
            "--attack_f_min", "0.0",
            "--reward_explore", "0.3", "--move_to_bias", "1.95",
            "--move_to_force", "29", "--economy_force", "24",
            "--cycle_detect", "5", "--act_loop_penalty", "1.0",
            "--guard_done_steps", "15", "--objective_reward", "30",
            "--use_nk2_shaping", "--nk2_shaping_scale", "0.45",
            "--target_chain", "scorer"]

    print("--- [run %d] %s steps=%d %s ---" % (i, MAP, STEPS, time.strftime("%T")))
    print("    EP_TRAJ 存在(赛前):", os.path.exists(EP_TRAJ))

    _grep_filter = "grep -vE 'Cannot answer the query -1' || true"
    ep_log_fh = open(ep_log, "w")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    _grep_proc = subprocess.Popen(
        ["sh", "-c", _grep_filter],
        stdin=proc.stdout, stdout=ep_log_fh, stderr=subprocess.DEVNULL)
    proc.stdout.close()
    try:
        proc.wait(timeout=STEPS * 60 + 300)
    except subprocess.TimeoutExpired:
        proc.kill(); proc.wait()
    rc = proc.returncode
    el = time.time() - t0
    try:
        _grep_proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _grep_proc.kill()
    ep_log_fh.close()

    ex = os.path.exists(EP_TRAJ)
    sz = os.path.getsize(EP_TRAJ) if ex else 0
    print("    elapsed=%.0fs rc=%s  EP_TRAJ存在=%s size=%d" % (el, rc, ex, sz))
    for line in subprocess.run(["grep", "-aE", "EP_TIME|EP298_SWALLOW|error", ep_log],
                               capture_output=True, text=True).stdout.splitlines()[-3:]:
        print("    log:", line[:150])
    print()