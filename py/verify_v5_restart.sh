#!/bin/bash
# 重启后验证: checkpoint 续训 + C 方案代码路径生效
sleep 20
echo "== unit 状态 =="
systemctl --user is-active homm3-train-v5
echo "== 训练进程 =="
ps aux | grep -E 'train_wsl2_ppo_v2|ep_runner' | grep -v grep | head -5
echo "== train_loop.log 尾部 =="
tail -15 /mnt/d/Bigdata/hero3_fresh/train_loop.log
echo "== 语法级验证: 运行中的 ep_runner 是否带 C 方案标志 =="
grep -c '_t06_hero_kill_capture' /mnt/d/Bigdata/hero3_fresh/ep_runner_one.py
