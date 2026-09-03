#!/bin/bash
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
echo "FILE=$F  mtime=$(stat -c %y "$F" | cut -d. -f1)  lines=$(wc -l < "$F")"
echo "=== 尾部 35 行:"
tail -35 "$F"
echo
echo "=== 战斗事件:"
grep -nE 'startBattle|battleStart|battleFinished|BAI|StupidAI' "$F" | tail -10
echo
echo "=== traj2:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj2.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'])
" 2>/dev/null || echo "traj2 不存在"
