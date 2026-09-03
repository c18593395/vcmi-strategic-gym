#!/bin/bash
echo "=== log 尾部 15:"
tail -15 /tmp/smoke_out.log
echo
echo "=== traj:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'])
"
echo
echo "=== log 中 monster/battle 相关:"
grep -cE 'monster|startBattle' /tmp/smoke_out.log
