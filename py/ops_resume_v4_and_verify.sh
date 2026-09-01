#!/usr/bin/env bash
# OPS-20260828-01 停旧进程 + 重启训练 v4 (带 ep_log 转储 patch) + 等待 2 局后验收
set +e
cd /mnt/d/Bigdata/hero3_fresh

echo '=== step 1: kill old pipeline gracefully ==='
pkill -15 -f 'train_wsl2_ppo_v2.py' 2>/dev/null
pkill -15 -f 'ep_runner_one.py'   2>/dev/null
sleep 3
pkill -9  -f 'train_wsl2_ppo_v2.py' 2>/dev/null
pkill -9  -f 'ep_runner_one.py'   2>/dev/null
sleep 1
echo 'remaining:'
ps -ef | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '  (none, GOOD)'

echo '=== step 2: checkpoint backup pre-v4 ==='
STAMP=$(date +%Y%m%d_%H%M%S)
cp -f wsl2_model_state.pt "wsl2_model_state.pt.bak_OPS2026082801_v4_$STAMP"
cp -f wsl2_model.pt       "wsl2_model.pt.bak_OPS2026082801_v4_$STAMP"
python3_bin=/home/administrator/vcmi-workspace/venv/bin/python3
step_in_ckpt=$($python3_bin -c "import torch; sd=torch.load('wsl2_model_state.pt',map_location='cpu'); print(sd.get('step'))" 2>&1)
echo "preflight step=$step_in_ckpt backup=wsl2_model_state.pt.bak_OPS2026082801_v4_$STAMP"

echo '=== step 3: append RESUME v4 marker ==='
echo "" >> train_loop.log
echo "===== OPS-20260828-01 RESUME v4 @ $(date '+%Y-%m-%d %H:%M:%S') | expect step=${step_in_ckpt}+, maps=2, ep_log_dump_patched =====" >> train_loop.log

echo '=== step 4: setsid + nohup launch ==='
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh

setsid bash -c '
  cd /mnt/d/Bigdata/hero3_fresh
  export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
  export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
  export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh
  exec nohup /home/administrator/vcmi-workspace/venv/bin/python3 -u train_wsl2_ppo_v2.py 2>&1 \
    | tee -a train_loop.log >>/dev/null
' >/dev/null 2>&1 </dev/null &
disown || true
sleep 5

echo '=== step 5: ps alive check ==='
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '  (none, BAD!)'
PY_PID=$(ps -ef | grep 'train_wsl2_ppo_v2.py' | grep -v grep | awk 'NR==1 && $3!="?"{print $2;exit} NR==1{print $2}')
echo "PY_PID=$PY_PID"

echo '=== step 6: print init banner (head post-v4 marker, 20 lines) ==='
awk '/^===== OPS-20260828-01 RESUME v4/,0' train_loop.log | head -20

echo "=== step 7: wait ${POST_WAIT:=420}s for ~2 episodes (each ~3-4 min) ==="
sleep $POST_WAIT

echo '=== post-wait ps ==='
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(none)'
echo '=== post-wait: tail 35 whole log ==='
tail -35 train_loop.log
echo '=== 5 criteria on RESUME v4 section ==='
SEC=$(awk '/^===== OPS-20260828-01 RESUME v4/,0' train_loop.log)
echo -n "(a) Loaded step=153785 count = "; echo "$SEC" | grep -c 'Loaded train state (model+optimizer, step=153785)'
echo    "    actual loaded row sample -> "; echo "$SEC" | grep 'Loaded train state' | head -2
echo -n "(b) ep rows: "; echo "$SEC" | grep -oE ' ep=[0-9]+' | sort -uV | tr '\n' ' '; echo
echo -n "    unique_ep_cnt = "; echo "$SEC" | grep -oE ' ep=[0-9]+' | sort -uV | wc -l
echo -n "    ep>=393 rows count (old-style, if patch not needed): "; echo "$SEC" | grep -oE ' ep=[0-9]+' | awk -F= '$2>=393{n++} END{print n+0}'
echo -n "(c) maps=2 count = "; echo "$SEC" | grep -c 'maps=2'
echo    "    banner -> "; echo "$SEC" | grep 'maps=' | head -3
echo -n "(d) [ZOMBIE] or [ENDTURN_FUSE] count = "; echo "$SEC" | grep -cE '\[ZOMBIE\]|\[ENDTURN_FUSE\]'
echo    "    samples -> "; echo "$SEC" | grep -E '\[ZOMBIE\]|\[ENDTURN_FUSE\]' | head -5
echo -n "(e) unique ep_steps values after resume = "; echo "$SEC" | grep -oE 'ep_steps=[0-9]+' | sort -u | tr '\n' ' '; echo
echo    "    last 10 ep_steps/r -> "; echo "$SEC" | grep -oE 'ep_steps=[0-9]+ r=[-0-9.]+' | tail -10
