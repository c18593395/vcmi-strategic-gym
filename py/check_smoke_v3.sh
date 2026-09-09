#!/bin/bash
echo "=== log 前 40 行:"
head -40 /tmp/smoke_out.log
echo
echo "=== traj 前 15 acts + rew:"
python3 -c "
import json
t = json.load(open('/tmp/smoke_traj.json'))
print('steps:', t['steps'])
print('acts:', t['act'][:15])
print('rews:', [round(r,1) for r in t['rew'][:15]])
"
