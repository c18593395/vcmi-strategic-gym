#!/bin/bash
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
tail -n +$LINE "$LOG" > /tmp/seg.log
echo "eps=$(grep -c 'ep_steps=' /tmp/seg.log)"
echo "GUARD=$(grep -c '\[GUARD\]' /tmp/seg.log)  MINE=$(grep -c '\[MINE\]' /tmp/seg.log)  TOWN=$(grep -c '\[TOWN\]' /tmp/seg.log)"
grep 'ep_steps=' /tmp/seg.log | sed -E 's/act=\[[^]]*\] //; s/obs_nz=[0-9]+ //' | tail -8
systemctl --user is-active homm3-train-v5
