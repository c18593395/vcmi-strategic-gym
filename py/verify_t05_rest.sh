#!/bin/bash
cd /mnt/d/Bigdata/hero3_fresh
export LD_LIBRARY_PATH="/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="/home/administrator/vcmi-native/rel/bin/libmlclient.so"
for MAP in T05_adventure_36X36_02.vmap T05_adventure_52X52_02.vmap; do
  echo "=== $MAP"
  timeout 400 /home/administrator/vcmi-workspace/venv/bin/python ep_runner_one.py \
    40 /tmp/t05_test.json "$MAP" \
    --model /mnt/d/Bigdata/hero3_fresh/wsl2_model.pt \
    --blue_ai MMAI_RANDOM --blue_adventure_ai MMAI \
    --economy_force 0 --reward_explore 0.3 --move_to_force 40 \
    --use_nk2_shaping --nk2_shaping_scale 0.45 \
    > /tmp/t05_test.log 2>&1
  echo "  EXIT=$?"
  python3 -c "
import json
t = json.load(open('/tmp/t05_test.json'))
print('  steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
" 2>/dev/null || echo "  (traj 未生成)"
done
