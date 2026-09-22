#!/bin/bash
# #298 run1 ep 全量日志解剖: 终局原因 + 事件流 + [SCORE]/[START_HOME]
set -u
OUT=/tmp/_298_evidence
E=$OUT/ep_good_to_go_h3m_r1_022710.log
echo "=== 行数/mtime ==="
wc -l $E; stat -c '%y' $E
echo ""
echo "=== 终局相关事件 (EP_TIME/RED_DEAD/ZOMBIE/FUSE/BOOT/error/Traceback) ==="
grep -aE 'EP_TIME|RED_DEAD|ZOMBIE|FUSE|BOOT|error|Traceback|Error|fishy|END' $E | grep -avE 'MUTEX|THREAD' | tail -25
echo ""
echo "=== [SCORE]/[START_HOME]/[GUIDE]/[TOWN] 引导事件 ==="
grep -aE '\[SCORE\]|\[START_HOME\]|\[GUIDE|\[TOWN|\[GUARD\]|\[MINE\]' $E | head -20
echo ""
echo "=== ep 侧 Cannot answer / fishy / blocked 计数 ==="
echo "Cannot answer: $(grep -ac 'Cannot answer' $E)"
echo "fishy: $(grep -ac 'fishy' $E)"
echo "not neighboring: $(grep -ac 'not neighboring' $E)"
echo "blocked: $(grep -ac 'destination tile is blocked' $E)"
echo "already visited: $(grep -ac 'already visited' $E)"
echo ""
echo "=== 尾 30 行 (终局现场) ==="
tail -30 $E
