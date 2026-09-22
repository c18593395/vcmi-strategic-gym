#!/bin/bash
# #296 mlclient query -1 引擎侧排查 (2026-09-23)
set -u
echo "=== WSL vcmi-native 源码树定位 'Cannot answer the query' ==="
grep -rn "Cannot answer the query" /home/administrator/vcmi-native 2>/dev/null | grep -v Binary
echo ""
echo "=== 定位 CServerHandler.cpp runNetwork / query 相关 ==="
grep -n "query\|runNetwork\|Cannot answer\|CServerNetwork" /home/administrator/vcmi-native/client/CServerHandler.cpp 2>/dev/null | head -40
echo ""
echo "=== CServerNetwork / 网络层 query 实现文件 ==="
ls /home/administrator/vcmi-native/client/ 2>/dev/null | grep -iE "network|server|handler"
echo ""
echo "=== 当前 hermes 日志 'Cannot answer' 最新计数 + 上下文 ==="
f=$(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -n 1)
echo "log: $f"
echo "count: $(grep -c 'Cannot answer the query -1' "$f")"
echo ""
echo "=== 报错行上下文 (首条前后 6 行, 看触发场景) ==="
ln=$(grep -n 'Cannot answer the query -1' "$f" | head -1 | cut -d: -f1)
echo "first at line $ln"
sed -n "$((ln-6)),$((ln+6))p" "$f"
echo ""
echo "=== 报错行的线程标签分布 ==="
grep -oE '\[[0-9]+/[A-Za-z 0-9]+\]' "$f" | grep -B0 -A0 'Cannot' | head -5
grep 'Cannot answer' "$f" | grep -oE '\[[0-9]+/[^\]]+\]' | sort | uniq -c | sort -rn
echo ""
echo "=== 是否伴随 Can not end turn / fishy 等连锁报错 ==="
grep -cE 'Can not end turn|fishy|Disaster|THREW' "$f"
echo ""
echo "=== 训练进程是否受影响 (主日志最后 EP_TIME 行) ==="
grep 'EP_TIME' /mnt/d/Bigdata/hero3_fresh/train_loop.log 2>/dev/null | tail -5
echo ""
echo "=== 当前 vcmiserver / ep_runner 是否活着 ==="
ps -ef | grep -E 'vcmiserver|ep_runner|train_wsl2' | grep -v grep
echo ""
echo "=== libmlclient.so 副本 md5 (确认是否双副本一致) ==="
md5sum /home/administrator/vcmi-native/rel/bin/libmlclient.so /home/administrator/vcmi-native-build/rel/bin/libmlclient.so 2>/dev/null
