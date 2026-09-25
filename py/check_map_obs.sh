#!/bin/bash
# map= 标签与 obs_nz 对应性验证 (mir 补齐后)
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
tail -n +$LINE "$LOG" > /tmp/seg.log
echo "=== 本次启动 ep 数: $(grep -c 'ep_steps=' /tmp/seg.log)"
echo
echo "=== 按图分组 obs_nz 分布 (标签造假检验: 同图应同 obs_nz 特征带):"
grep 'ep_steps=' /tmp/seg.log | grep -oE 'obs_nz=[0-9]+ map=[^ ]+' | sort | uniq -c | sort -k3
echo
echo "=== 明细 (map, steps, r, obs_nz):"
grep 'ep_steps=' /tmp/seg.log | sed -E 's/act=\[[^]]*\] //; s/ep_steps=//' | awk '{print $NF, $1, $2, $3}' | tail -20
