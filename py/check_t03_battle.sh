#!/bin/bash
echo "=== 战斗段动作流 (battleStart 到 Finished):"
N=$(grep -n 'begin bid=0' /tmp/smoke_t03.log | tail -1 | cut -d: -f1)
M=$(grep -n 'battleFinished RETURN' /tmp/smoke_t03.log | tail -1 | cut -d: -f1)
echo "battleStarted L$N → battleFinished L$M (间隔 $((M-N)) 行)"
sed -n "${N},${M}p" /tmp/smoke_t03.log | grep -vE '^\s*$' | head -40
echo
echo "=== traj:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_t03.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'][:40])
"
