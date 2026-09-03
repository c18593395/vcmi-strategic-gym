#!/bin/bash
echo "=== smoke_t05.log 尾部 20:"
tail -20 /tmp/smoke_t05.log
echo
echo "=== traj:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_t05.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'][:45])
print('done tail:', t['done'][-3:])
"
