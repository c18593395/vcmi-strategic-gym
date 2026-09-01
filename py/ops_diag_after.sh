#!/usr/bin/env bash
# OPS-20260828-01 诊断脚本：检查进程存活+日志尾部
set +e
cd /mnt/d/Bigdata/hero3_fresh
echo '=== ps alive (train + ep_runner) ==='
ps -ef | grep -E 'train_wsl2_ppo_v2|ep_runner_one' | grep -v grep || echo '(none)'

echo '=== log stat (mtime + size + lines) ==='
stat -c 'mtime=%y size=%s' train_loop.log
wc -l train_loop.log

echo '=== tail 60 whole log ==='
tail -60 train_loop.log

echo '=== tail from resume marker ==='
awk '/^===== OPS-20260828-01 RESUME/,0' train_loop.log | tail -50
