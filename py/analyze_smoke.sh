#!/bin/bash
# 冒烟局结果分析
echo "=== 最新 hermes 文件:"
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
echo "$F ($(stat -c %y "$F" | cut -d. -f1), $(wc -l < "$F") 行)"
echo
echo "=== 战斗事件:"
grep -nE 'startBattle DONE|battleStarted|battleFinished|battleStart exception' "$F" | tail -10
echo
echo "=== 战斗回合动作流 (battleStarted 后 40 行):"
N=$(grep -n 'begin bid=0' "$F" | tail -1 | cut -d: -f1)
if [ -n "$N" ]; then sed -n "${N},$((N+40))p" "$F" | grep -vE '^\s*$'; fi
echo
echo "=== traj 结果:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj.json'))
print('steps:', t['steps'], ' total_rew:', round(t['total_rew'],1))
print('acts:', t['act'][:40])
print('done flags:', t['done'][-5:])
print('error:', t.get('error'))
"
