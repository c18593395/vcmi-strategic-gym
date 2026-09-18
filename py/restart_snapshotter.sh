#!/bin/bash
# 快照器重启 (09-18): 杀旧实例(排除自身) + 拉起新实例 + 验证
SELF=$$
for p in $(pgrep -f contact_log_snapshot.py); do
  [ "$p" != "$SELF" ] && kill "$p" 2>/dev/null
done
sleep 1
nohup /home/administrator/vcmi-workspace/venv/bin/python /mnt/d/Bigdata/hero3_fresh/py/contact_log_snapshot.py >/tmp/snapshot.log 2>&1 &
sleep 3
ps aux | grep contact_log_snapshot.py | grep -v grep | grep -c 'bin/python'
