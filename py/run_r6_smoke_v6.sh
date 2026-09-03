#!/bin/bash
# R6 冒烟 v6: economy_force 0 (move_to 24 主导), 守卫拦路图
set -e
cd /mnt/d/Bigdata/hero3_fresh
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="/home/administrator/vcmi-native/rel/bin/libmlclient.so"
timeout 400 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py \
  60 /tmp/smoke_traj.json T04smoke_adventure_20X20_bai.vmap \
  --model /mnt/d/Bigdata/hero3_fresh/wsl2_model.pt \
  --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
  --reward_explore 0.3 --move_to_bias 1.0 --move_to_force 60 \
  --economy_force 0 --cycle_detect 5 --act_loop_penalty 1.0 \
  --guard_done_steps 15 --objective_reward 30 --use_nk2_shaping --nk2_shaping_scale 0.45 \
  > /tmp/smoke_out.log 2>&1
echo "EXIT=$?"
echo "battles=$(grep -cE 'startBattle DONE' /tmp/smoke_out.log)"
grep -E 'battleFinished RETURN|battleStart exception|segfault' /tmp/smoke_out.log | head -5
