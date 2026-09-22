#!/bin/bash
# #298: elbow/judgement 卡死现场 (09-23)
set -u
echo "=== elbow_room ep 现场 ==="
f=$(ls -t /tmp/_298_evidence/ep_elbow_room*.log 2>/dev/null | head -1)
echo "$f"
grep -aE 'timed out|HEROSEG|ML-q|fishy|neighboring|START_HOME|Cannot answer' "$f" | tail -15
echo ""
echo "=== judgement ep 现场 ==="
g=$(ls -t /tmp/_298_evidence/ep_judgement*.log 2>/dev/null | head -1)
echo "$g"
grep -aE 'timed out|HEROSEG|ML-q|fishy' "$g" | tail -12
echo ""
echo "=== viking 对照局进度 ==="
h=$(ls -t /tmp/_298_evidence/ep_a_viking*.log 2>/dev/null | head -1)
echo "$h"
if [ -n "$h" ]; then
  grep -aE 'EP_TIME|timed out' "$h" | tail -3
  tail -3 "$h"
fi
echo ""
ps -ef | grep 'ep_runner_one' | grep -v grep | head -2 || echo "(viking 局已结束)"
