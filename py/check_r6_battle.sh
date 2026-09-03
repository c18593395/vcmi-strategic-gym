#!/bin/bash
# R6 正向验证: hermes 日志中战斗痕迹 (BAI 初始化/战斗动作/allowMlBot)
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
# 本次启动后有哪些 ep 文件在更新 (按 mtime 最近 3 个)
echo "--- 最近 hermes 文件:"
ls -lt /tmp/hermes_ep_*.log | head -3
for F in $(ls -t /tmp/hermes_ep_*.log | head -2); do
  echo "=== $F"
  echo "  战斗行 (yourTurn in_battle / battle):"
  grep -icE 'in_battle|battleStart|battle' "$F"
  grep -iE 'in_battle' "$F" | tail -3
  echo "  MMAI/BAI 行:"
  grep -iE 'MMAI|BAI|mlbot' "$F" | tail -5
done
