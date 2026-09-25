#!/bin/bash
# 查 Mode B trade cap 修复是否已编入当前 .so + git 状态
B="${B:-/home/administrator/vcmi-native}"
echo "=== 当前 .so mtime ==="
stat -c '%y %n' "$B/rel/bin/libvcmi.so" "$B/rel/bin/libmlclient.so" 2>/dev/null
echo
echo "=== .so 是否已含 trade cap / BREAK 哨兵 ==="
for so in "$B/rel/bin/libvcmi.so" "$B/rel/bin/libmlclient.so"; do
  echo "-- $(basename "$so") --"
  echo -n "  'trade' 相关字符串: "
  strings "$so" 2>/dev/null | grep -ciE 'tradecap|trade BREAK|_mlTrade' || echo 0
  echo -n "  [ML-fix] 标记: "
  strings "$so" 2>/dev/null | grep -c 'ML-fix' || echo 0
done
echo
echo "=== 源码 ResourceTrader.cpp 是否含 cap / BREAK ==="
grep -nE 'cap|tradecap|_mlTrade|BREAK' "$B/AI/Nullkiller2/Engine/ResourceTrader.cpp" 2>/dev/null | head
echo
echo "=== 源码里是否有 patch_mlfix_tradecap 写入的标记 ==="
grep -nE 'ML-time|trade cap|_mlTradeCap' "$B/AI/Nullkiller2/Engine/ResourceTrader.cpp" 2>/dev/null | head
echo
echo "=== vcmi-native git 最近 10 提交 ==="
cd "$B" && git log --oneline -10 2>/dev/null
echo
echo "=== 工作区是否有未提交（ResourceTrader / AIGateway）==="
cd "$B" && git status -s 2>/dev/null | grep -E 'ResourceTrader|AIGateway|strategic_state|patch_mlfix' | head
echo
echo "=== patch_mlfix_tradecap.py 是否存在 ==="
ls -la /mnt/d/Bigdata/hero3_fresh/py/patch_mlfix_tradecap.py 2>/dev/null
