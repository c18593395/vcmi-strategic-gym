#!/bin/bash
echo "=== smoke_t03.log 关键行:"
grep -E 'Bad value|Failed|START_HOME|battles|TERRAIN.*OK' /tmp/smoke_t03.log | head -6
echo
cp /mnt/d/Bigdata/hero3_fresh/Maps/training/T03_adventure_20X20_01.vmap /home/administrator/vcmi-native/rel/bin/data/Maps/
echo "=== T03 已复制, 重跑:"
cd /mnt/d/Bigdata/hero3_fresh
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="/home/administrator/vcmi-native/rel/bin/libmlclient.so"
timeout 400 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py \
  60 /tmp/smoke_t03.json T03_adventure_20X20_01.vmap \
  --model /mnt/d/Bigdata/hero3_fresh/wsl2_model.pt \
  --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
  --economy_force 0 --reward_explore 0.3 --guard_done_steps 15 \
  --use_nk2_shaping --nk2_shaping_scale 0.45 \
  > /tmp/smoke_t03.log 2>&1
echo "EXIT=$?"
echo "battles=$(grep -cE 'startBattle DONE' /tmp/smoke_t03.log)"
grep -E 'battleFinished RETURN|battleStart exception|segfault' /tmp/smoke_t03.log | head -4
