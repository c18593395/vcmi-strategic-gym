#!/bin/bash
# #298 拆轴取证 (09-23): 区分「单次卡死窗口」vs「全程慢速步进」
# 原理: 每 2s 采样 ep_runner 日志字节数 → 零增长窗口 = 卡死; 稳定小增长 = 慢速步进
# 用法: wsl -u root bash /mnt/d/Bigdata/hero3_fresh/py/_298_stepprofile.sh [map] [max_turns]
set -u
MAP=${1:-good_to_go_h3m.vmap}
TURNS=${2:-30}
OUT=/tmp/_298_evidence
mkdir -p $OUT
PY="${PY:-/home/administrator/vcmi-workspace/venv/bin/python}"
RUNNER="${RUNNER:-/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py}"
TS=$(date +%H%M%S)
LOG=$OUT/ep_profile_${MAP%.vmap}_${TS}.log
SAMP=$OUT/profile_${MAP%.vmap}_${TS}.csv

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

echo "t,bytes" > $SAMP
echo "=== [profile] $MAP turns=$TURNS start $(date +%T) ==="
timeout 480 $PY $RUNNER $TURNS /tmp/traj_298.json $MAP --blue_ai MMAI_RANDOM --target_chain scorer --objective_reward 30 > $LOG 2>&1 &
PID=$!
T0=$(date +%s)
while kill -0 $PID 2>/dev/null; do
  echo "$(( $(date +%s) - T0 )),$(stat -c%s $LOG 2>/dev/null || echo 0)" >> $SAMP
  sleep 2
done
wait $PID; RC=$?
echo "=== rc=$RC log=$LOG ==="
tail -2 $LOG | cut -c1-150
echo ""
echo "=== 增长剖面分析 ==="
awk -F, 'NR==2{prev=$1; prevb=$2; firstb=$2; next}
NR>2{
  d=$1-prev; db=$2-prevb;
  if (db==0) { flat+=d; if (flat>maxflat) {maxflat=flat; mfs=prev-flat+2; mfe=$1} }
  else { flat=0 }
  prev=$1; prevb=$2
}
END{
  total=prev; grow=prevb-firstb;
  printf "总时长: %ds  日志总字节: %d\n", total, prevb
  printf "最长零增长窗口: %ds  区间: %ds -> %ds\n", maxflat, mfs, mfe
  act=total-maxflat
  if (act>0) printf "活跃期: %ds  活跃期平均产出: %.0f B/s\n", act, grow/act
  printf "零增长占比: %.0f%%\n", (total>0? 100*maxflat/total : 0)
}' $SAMP
echo ""
echo "=== 原始采样 (前 20 行) ==="
head -20 $SAMP
echo "..."
echo "=== 原始采样 (后 10 行) ==="
tail -10 $SAMP
