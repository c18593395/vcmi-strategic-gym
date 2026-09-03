#!/bin/bash
# R6 BAI 决策回路定向冒烟 (2026-09-03)
# 前置: 训练已停 (terrain_grid.bin 共享文件冲突, 必须串行)
set -e
cd /mnt/d/Bigdata/hero3_fresh
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="/home/administrator/vcmi-native/rel/bin/libmlclient.so"
CKPT=/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt
echo "=== 冒烟局启动 (max_turns=60, 有来有回战斗图)..."
timeout 600 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py \
  60 /tmp/smoke_traj.json T04smoke_adventure_20X20_bai.vmap \
  --model "$CKPT" \
  --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
  --reward_explore 0.3 --move_to_bias 1.0 --move_to_force 60 \
  --economy_force 24 --cycle_detect 5 --act_loop_penalty 1.0 \
  --guard_done_steps 15 --objective_reward 30 --use_nk2_shaping --nk2_shaping_scale 0.45 \
  2>&1 | tail -30
echo "=== 冒烟局退出码: $?"
