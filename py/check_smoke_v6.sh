#!/bin/bash
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj.json'))
print('steps:', t['steps'], 'rew:', round(t['total_rew'],1), 'error:', t.get('error'))
print('acts:', t['act'])
print('done tail:', t['done'][-3:])
"
echo "=== log 中 24/MOVE_TO/目标相关:"
grep -iE 'move_to|MOVE_TO|obj_best|\[24\]' /tmp/smoke_out.log | head -8
echo "=== 事件词:"
grep -oE '\[[A-Z_-]+\]' /tmp/smoke_out.log | sort | uniq -c | sort -rn | head -10
