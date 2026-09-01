#!/usr/bin/env bash
# OPS-20260828-01  清理旧训练进程
set +e
echo '=== 1) ps list of processes to kill ==='
ps -ef | grep -E 'train_wsl2_ppo_v2|ep_runner_one|tee train_loop' | grep -v grep

echo '=== 2) signal SIGTERM ==='
PIDS=$(ps -ef | grep -E 'train_wsl2_ppo_v2|ep_runner_one|python3 -u train_wsl2_ppo_v2' | grep -v grep | awk '{print $2}')
BASH_PID=$(ps -ef | grep -E 'bash -c cd /mnt/d/Bigdata/hero3_fresh && python3 -u train_wsl2_ppo_v2' | grep -v grep | awk '{print $2}')
echo "PIDS=$PIDS BASH_PID=$BASH_PID"
[ -n "$PIDS" ]    && kill -15 $PIDS    2>&1 | sed 's/^/[kill15] /'
[ -n "$BASH_PID" ] && kill -15 $BASH_PID 2>&1 | sed 's/^/[kill15bash] /'

echo '=== 3) wait 10s ==='
sleep 10

echo '=== 4) remaining check ==='
ps -ef | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo 'none left'
REST=$(ps -ef | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep | awk '{print $2}' | tr '\n' ' ')
if [ -n "$REST" ]; then
  echo "kill -9 $REST"
  kill -9 $REST 2>&1 | sed 's/^/[kill9] /'
  sleep 2
fi

echo '=== 5) final ps ==='
ps -ef | grep -E 'train_wsl2_ppo|ep_runner' | grep -v grep || echo 'no running train processes (GOOD)'
