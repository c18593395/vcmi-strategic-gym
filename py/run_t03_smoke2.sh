#!/bin/bash
cd /mnt/d/Bigdata/hero3_fresh
python3 /mnt/d/Bigdata/hero3_fresh/py/gen_t03_smoke.py
cp /mnt/d/Bigdata/hero3_fresh/Maps/training/T03smoke_adventure_20X20_bai.vmap /home/administrator/vcmi-native/rel/bin/data/Maps/
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="/home/administrator/vcmi-native/rel/bin/libmlclient.so"
timeout 400 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py \
  60 /tmp/smoke_t03.json T03smoke_adventure_20X20_bai.vmap \
  --model /mnt/d/Bigdata/hero3_fresh/wsl2_model.pt \
  --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
  --economy_force 0 --reward_explore 0.3 --guard_done_steps 15 \
  --use_nk2_shaping --nk2_shaping_scale 0.45 \
  > /tmp/smoke_t03.log 2>&1
echo "EXIT=$?"
N=$(grep -n 'begin bid=0' /tmp/smoke_t03.log | tail -1 | cut -d: -f1)
M=$(grep -n 'battleFinished RETURN' /tmp/smoke_t03.log | tail -1 | cut -d: -f1)
echo "battleStarted L$N → battleFinished L$M (间隔 $((M-N)) 行)"
echo "=== 战斗段:"
sed -n "${N},${M}p" /tmp/smoke_t03.log | grep -vE '^\s*$' | head -30
