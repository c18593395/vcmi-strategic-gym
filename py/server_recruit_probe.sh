#!/bin/bash
# 服务器活体 ep 日志 RECRUITED 真实状态核查 (绕主日志白名单)
echo "===== [1] 活体 ep 日志清单 (最近 8 份) ====="
ls -lt /tmp/hermes_ep_*.log 2>/dev/null | head -8
echo
echo "===== [2] 最近 20 份 ep 日志打点统计 ====="
for f in $(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -20); do
  R=$(grep -c 'RECRUITED' "$f" 2>/dev/null)
  T=$(grep -c 'TOWN_RETRY' "$f" 2>/dev/null)
  E=$(grep -c 'ECON. recruit' "$f" 2>/dev/null)
  M=$(grep -oE 'map=[^ ]+' "$f" 2>/dev/null | head -1)
  echo "$f  RECRUITED=$R TOWN_RETRY=$T ECON_recruit=$E  $M"
done
echo
echo "===== [3] 最近 60 份里有 RECRUITED 的样例 ====="
FOUND=0
for f in $(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -60); do
  C=$(grep -c 'RECRUITED' "$f" 2>/dev/null)
  if [ "${C:-0}" -gt 0 ]; then
    echo "FOUND: $f count=$C"
    grep 'RECRUITED' "$f" | head -4
    grep 'EP_TIME' "$f" | head -1
    FOUND=1
    break
  fi
done
[ "$FOUND" -eq 0 ] && echo "最近 60 份 ep 日志 RECRUITED 全 0"
echo
echo "===== [4] ep 日志总数与时间跨度 ====="
ls /tmp/hermes_ep_*.log 2>/dev/null | wc -l
ls -lt /tmp/hermes_ep_*.log 2>/dev/null | tail -2
