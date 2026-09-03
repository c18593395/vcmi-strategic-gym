#!/bin/bash
echo "=== battles:"
grep -cE 'startBattle DONE' /tmp/smoke_out.log
echo "=== battleFinished / exception / segfault:"
grep -E 'battleFinished RETURN|battleStart exception|segfault' /tmp/smoke_out.log | head -5
echo
echo "=== battleStarted 动作流 (bid=0 后 35 行):"
N=$(grep -n 'begin bid=0' /tmp/smoke_out.log | tail -1 | cut -d: -f1)
if [ -n "$N" ]; then sed -n "${N},$((N+35))p" /tmp/smoke_out.log | grep -vE '^\s*$' | head -30; fi
echo
echo "=== traj:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'][:25])
"
