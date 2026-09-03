#!/bin/bash
echo "=== traj mtime:"
ls -la /tmp/smoke_traj*.json 2>/dev/null
echo
echo "=== smoke_traj 内容:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'])
print('done tail:', t['done'][-3:])
"
echo
echo "=== hermes 文件按 mtime:"
ls -lt /tmp/hermes_ep_*.log | head -3
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
echo "=== 最新 $F 战斗事件:"
grep -nE 'startBattle DONE|begin bid=|battleFinished|battleStart exception|segfault' "$F" | tail -10
