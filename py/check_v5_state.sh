#!/bin/bash
# 查 v5 训练服务真实位置与当前状态
echo "== id / HOME =="
id; echo "HOME=$HOME"
echo "== 用户 systemd 单元目录 =="
ls -la "$HOME/.config/systemd/user/" 2>&1 | head -20
echo "== 系统级单元 =="
ls /etc/systemd/system/ 2>/dev/null | grep -i -E 'homm|train'
ls /usr/lib/systemd/system/ /lib/systemd/system/ 2>/dev/null | grep -i -E 'homm|train'
echo "== systemd user 实例状态 =="
systemctl --user is-system-running 2>&1 | head -1
echo "== 全盘找 homm3-train 单元/脚本 =="
find / -maxdepth 6 \( -path /proc -o -path /sys -o -path /dev \) -prune -o -name '*homm3*' -print 2>/dev/null | head -20
echo "== python / vcmi 进程 =="
ps aux | grep -E 'python|vcmi' | grep -v grep | head -10
echo "== vcmi-native 训练目录 =="
ls /mnt/d/Bigdata/hero3_fresh/*.log 2>/dev/null | head -5
echo "== train_loop.log 尾部 =="
tail -5 /mnt/d/Bigdata/hero3_fresh/train_loop.log 2>/dev/null
