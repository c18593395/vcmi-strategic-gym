#!/bin/bash
# [DIAG-0829] 查看最新 ep 明细日志尾部
L=$(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -1)
echo "latest: $L"
echo '--- tail 40 (filtered) ---'
tail -40 "$L" | grep -E 'ZOMBIE|ENDTURN|step|reward|done|error|Error|timeout|guard|win|game_over|traj' | head -20
echo '--- traj files ---'
ls -l --time-style=long-iso /tmp/traj_ep.json /tmp/hermes_ep_model_*.pt 2>/dev/null | head -5
echo '--- train_loop last 12 ---'
tail -12 /mnt/d/Bigdata/hero3_fresh/train_loop.log
