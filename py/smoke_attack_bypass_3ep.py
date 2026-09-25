#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 冒烟 3 局 T06_adventure_72X72_02_duel + 3 参数 (bypass=1 contact_d=2 f_min=-1.0).

目的: 验证 A2 贴脸强攻修复 — 看 [BHERO_ATTACK] 触发率 (铁证里 tried=False 全 0 → 改后应 tried=True + 战斗触发).
用法: python py/smoke_attack_bypass_3ep.py
  - 手动启动 3 局 ep_runner_one (不走 train_wsl2_ppo_v2, 直接调 ep_runner + 3 参数)
  - 跑完 grep BHERO_ATTACK + ATK_DBG + HERO_DEATH, 转储 [BHERO_ATTACK] 触发率

09-19 FORCE 验证 (根因 B 对症): 主训练继续跑不干扰, 单局设 HOMM3_ATK_DEBUG_FORCE=1
  - ep_runner_one.py L1004-1016 调试旁路: 不要求 SCORE pick 蓝英雄, 任何贴脸敌英雄 d<=2 即强攻
  - 对症 "蓝英雄 obs 外 → move_blue_hero_target 恒 False → 旁路 0 进入" 的困死场景
  - 验证目标: FORCE=1 下 [BHERO_ATTACK] 是否 >0 (对比 bypass 仅 0 条)
"""
import os
import subprocess, os, re, sys, time

VENV = os.environ.get("VENV", "/home/administrator/vcmi-workspace/venv/bin/python")
RUNNER = os.environ.get("RUNNER", "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py")
MAP = "T06_adventure_72X72_02_duel.vmap"
CKPT = os.environ.get("CKPT", "/mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_818598.pt")
LOG_BASE = "/tmp/smoke_force_ep_%d.log"

# 3 参数 (A2 贴脸强攻)
ATTACK_PARAMS = ["--blue_hero_attack_bypass", "1",
                 "--blue_hero_contact_d", "2",
                 "--attack_f_min", "-1.0"]
# 其余参数对齐当前 systemd 实参 (从 ps 实参抓的)
OTHER_PARAMS = [
    "--blue_ai", "MMAI_RANDOM", "--blue_adventure_ai", "MMAI",
    "--reward_explore", "0.3", "--move_to_bias", "1.0", "--move_to_force", "60",
    "--economy_force", "24", "--cycle_detect", "5", "--act_loop_penalty", "1.0",
    "--act_loop_from_step", "60", "--guard_done_steps", "15", "--objective_reward", "30",
    "--use_nk2_shaping", "--nk2_shaping_scale", "0.45",
    "--blue_model", "/mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_772429.pt",
    "--target_chain", "scorer",
]
STEPS_PER_EP = "250"
N_EP = 3

def run_ep(ep_idx):
    ep_ckpt = f"/tmp/smoke_force_ep{ep_idx}.pt"
    traj = f"/tmp/smoke_force_traj{ep_idx}.json"
    logf = LOG_BASE % ep_idx
    # 手动保存当前 model ckpt (用最新 checkpoint 当输入, 跑 250 步, 不用 PPO 更新)
    # 直接 cp 最新 ckpt 当 ep_ckpt (冒烟不需要更新)
    import shutil
    shutil.copy(CKPT, ep_ckpt)
    cmd = [VENV, RUNNER, STEPS_PER_EP, traj, MAP, "--model", ep_ckpt]
    cmd.extend(ATTACK_PARAMS)
    cmd.extend(OTHER_PARAMS)
    env = os.environ.copy()
    # FORCE 验证 (根因 B 对症): 不靠 SCORE pick, 任何贴脸敌英雄 d<=2 即强攻
    env["HOMM3_ATK_DEBUG_FORCE"] = "1"
    env["LD_LIBRARY_PATH"] = "/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
    env["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    print(f"\n[EP {ep_idx+1}/3] 启动: {MAP}", flush=True)
    print(f"  cmd: {' '.join(cmd)}", flush=True)
    t0 = time.time()
    with open(logf, "w") as f:
        p = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT)
    elapsed = time.time() - t0
    print(f"[EP {ep_idx+1}/3] 完成 rc={p.returncode} 耗时 {elapsed:.0f}s log={logf}", flush=True)
    return logf, p.returncode

def analyze():
    print("\n" + "=" * 60, flush=True)
    print("== [BHERO_ATTACK] 触发分析 ==", flush=True)
    print("=" * 60, flush=True)
    total_atk = 0
    total_dbg = 0
    total_dbg_tried = 0
    total_death = 0
    total_ep = 0
    for i in range(N_EP):
        logf = LOG_BASE % i
        if not os.path.exists(logf):
            continue
        text = open(logf, errors="replace").read()
        atk_n = len(re.findall(r"\[BHERO_ATTACK\]", text))
        dbg_n = len(re.findall(r"\[ATK_DBG\]", text))
        dbg_tried_n = len(re.findall(r"\[ATK_DBG\].*tried=True", text))
        death_n = len(re.findall(r"\[HERO_DEATH\]", text))
        m = re.search(r"\[EP_TIME\].*?r=(-?[\d.]+)", text)
        r = m.group(1) if m else "?"
        total_atk += atk_n
        total_dbg += dbg_n
        total_dbg_tried += dbg_tried_n
        total_death += death_n
        total_ep += 1
        print(f"  EP{i+1}: [BHERO_ATTACK]={atk_n} [ATK_DBG]={dbg_n} (tried=True {dbg_tried_n}) "
              f"[HERO_DEATH]={death_n} r={r}", flush=True)
    print("-" * 60, flush=True)
    print(f"  3 局合计: [BHERO_ATTACK]={total_atk} [ATK_DBG]={total_dbg} "
          f"(tried=True {total_dbg_tried}) [HERO_DEATH]={total_death}", flush=True)
    if total_ep > 0:
        print(f"  [BHERO_ATTACK] 触发率 = {total_atk} / {total_ep} 局 = {total_atk/total_ep*100:.0f}%", flush=True)
        if total_atk > 0:
            print(f"  ✅ 贴脸强攻已激活 (改前 tried=False 全 0 → 改后 [BHERO_ATTACK] {total_atk} 条)", flush=True)
        else:
            print(f"  ❌ [BHERO_ATTACK] 仍 0 — 贴脸未触发 (蓝英雄 d>2 或被 _attack_tried 拦截)", flush=True)

if __name__ == "__main__":
    for i in range(N_EP):
        run_ep(i)
    analyze()
