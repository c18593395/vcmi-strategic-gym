#!/bin/bash
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash -c "
source /home/administrator/vcmi-workspace/venv/bin/activate
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
cd /home/administrator/vcmi-workspace
python3 -u /mnt/d/Bigdata/hero3_fresh/ep_runner.py 3 /mnt/d/Bigdata/hero3_fresh/traj_latest.pkl
" 2>/dev/null