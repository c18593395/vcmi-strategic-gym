#!/bin/bash
# 验证 grep 管道过滤是否生效 + fd 指向 (2026-09-23)
set -u
echo "=== 当前 Popen 管道进程 ==="
ps -ef | grep -E 'grep -vE Cannot|sh -c grep' | grep -v grep
echo ""
echo "=== ep_runner fd 1/2 指向 ==="
ep_pid=$(ps -ef | grep 'ep_runner_one.py' | grep -v grep | head -1 | awk '{print $2}')
echo "ep_runner pid=$ep_pid"
ls -la /proc/$ep_pid/fd/1 /proc/$ep_pid/fd/2 2>/dev/null
echo ""
echo "=== hermes 日志行数分布 ==="
f=/tmp/hermes_ep_130617.log
echo "mtime: $(stat -c '%y' $f 2>/dev/null)"
echo "total lines: $(wc -l < $f)"
echo "Cannot answer: $(grep -c 'Cannot answer the query -1' $f)"
echo "MUTEX: $(grep -c 'MUTEX' $f)"
echo "THREAD: $(grep -c 'THREAD' $f)"
echo "NK2: $(grep -c 'NK2' $f)"
echo "ECON: $(grep -c 'ECON' $f)"
echo "TERRAIN: $(grep -c 'TERRAIN' $f)"
echo ""
echo "=== 主日志最后 3 行 (训练是否推进) ==="
tail -3 /mnt/d/Bigdata/hero3_fresh/train_loop.log
