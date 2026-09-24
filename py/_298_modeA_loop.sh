#!/bin/bash
# Mode A 元凶抓捕循环 (gdb 命令走 py/_modeA.gdb)
set -u
OUT=/tmp/_298_evidence/modeA
mkdir -p $OUT
TS=$(date +%H%M%S)
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

for i in 1 2 3 4 5 6 7 8 9 10; do
  LOG=$OUT/mB_${TS}_r$i.log
  ST=$OUT/mB_${TS}_r${i}_killer.txt
  timeout 360 gdb -batch -nx -x /mnt/d/Bigdata/hero3_fresh/py/_modeA.gdb --args \
    /home/administrator/vcmi-workspace/venv/bin/python \
    /mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py 30 /tmp/traj_298.json elbow_room_h3m.vmap \
    --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $ST 2>&1
  HIT=$(grep -c 'KILLER HIT' $ST)
  echo "r$i killer_hit=$HIT stack=$ST"
  if [ "$HIT" != "0" ]; then
    echo "=== CAUGHT ==="
    break
  fi
done
echo done