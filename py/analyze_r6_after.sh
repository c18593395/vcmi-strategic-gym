#!/bin/bash
# R6 修复后日志综合分析 (2026-09-03)
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
SEG=$(tail -n +$LINE "$LOG")
echo "=== resume 后运行时长与 ep 数:"
echo "$SEG" | grep 'ep_steps=' | wc -l
echo "$SEG" | grep -E '^  step[0-9]+' | tail -1
echo
echo "=== ep 明细 (map + r + 步数):"
echo "$SEG" | grep 'ep_steps=' | sed -E 's/act=\[[^]]*\] //; s/obs_nz=[0-9]+ //' | tail -15
echo
echo "=== avg_r 轨迹 (每 ep 抽样):"
echo "$SEG" | grep -oE 'step[0-9]+ avg_r=[0-9.-]+ ep=[0-9]+' | tail -12
echo
echo "=== 关键事件计数 (resume 后):"
printf "Router fallback: %s\n" "$(echo "$SEG" | grep -c 'battleStart exception')"
printf "ZOMBIE: %s\n" "$(echo "$SEG" | grep -c 'ZOMBIE')"
printf "ENDTURN_FUSE: %s\n" "$(echo "$SEG" | grep -c 'ENDTURN_FUSE')"
printf "TOWN visit: %s\n" "$(echo "$SEG" | grep -c '\[TOWN\]')"
printf "TOWN_CAPTURE: %s\n" "$(echo "$SEG" | grep -c 'TOWN_CAPTURE')"
printf "RECRUITED: %s\n" "$(echo "$SEG" | grep -c 'RECRUITED')"
printf "START_HOME: %s\n" "$(echo "$SEG" | grep -c 'START_HOME')"
printf "TOWNSTALL: %s\n" "$(echo "$SEG" | grep -c 'TOWNSTALL')"
echo
echo "=== act 分布 (resume 后全部 ep):"
echo "$SEG" | grep -oE 'act=\[[^]]*\]' | tr -d 'act=[] ' | tr ',' '\n' | sort | uniq -c | sort -rn
echo
echo "=== hermes 战斗事件 (最近 2 个文件):"
for F in $(ls -t /tmp/hermes_ep_*.log | head -2); do
  echo "--- $F"
  grep -c 'battleStart exception' "$F" 2>/dev/null
  grep -E 'battleFinished RETURN|notifyObjectAboutRemoval ENTER' "$F" | tail -6
  grep -E 'ML-battle\] BattleProcessor::startBattle DONE' "$F" | wc -l
done
