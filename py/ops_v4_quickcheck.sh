#!/usr/bin/env bash
# 2-min 快速验收 v4 启动，抢时间给用户先确认
set +e
cd /mnt/d/Bigdata/hero3_fresh
echo '=== ps alive ==='
ps -efH | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(none)'
echo '=== log stat ==='
stat -c 'mtime=%y size=%s' train_loop.log
echo '=== RESUME v4 section lines count ==='
SEC=$(awk '/^===== OPS-20260828-01 RESUME v4/,0' train_loop.log)
LINES=$(echo "$SEC" | wc -l)
echo "lines_after_v4_marker=$LINES"
echo '=== tail 12 after v4 marker ==='
echo "$SEC" | tail -12
echo '=== quick 5-criteria so far ==='
echo -n "(a) step=153785 -> "; echo "$SEC" | grep -c 'Loaded train state (model+optimizer, step=153785)'
echo -n "(b) ep list   -> "; echo "$SEC" | grep -oE ' ep=[0-9]+' | sort -uV | tr '\n' ' '; echo
echo -n "(c) maps=2     -> "; echo "$SEC" | grep -c 'maps=2'
echo -n "(d) Z/E fuse   -> "; echo "$SEC" | grep -cE '\[ZOMBIE\]|\[ENDTURN_FUSE\]'
echo -n "(e) ep_steps   -> "; echo "$SEC" | grep -oE 'ep_steps=[0-9]+' | sort -u | tr '\n' ' '; echo
