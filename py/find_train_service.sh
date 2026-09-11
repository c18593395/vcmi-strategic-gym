#!/bin/bash
# 排查 v5 训练服务所在用户与单元位置
echo "== passwd 可登录用户 =="
awk -F: '$3>=1000 && $3<65534 {print $1, $3}' /etc/passwd
echo "== 查找 homm3-train 服务单元 =="
find /root /home -maxdepth 4 -name 'homm3-train*' 2>/dev/null
echo "== 各用户 systemd user 目录 =="
for u in root $(awk -F: '$3>=1000 {print $1}' /etc/passwd); do
  ls /home/$u/.config/systemd/user/ 2>/dev/null | sed "s/^/[$u:home] /"
  [ "$u" = "root" ] && ls /root/.config/systemd/user/ 2>/dev/null | sed "s/^/[$u] /"
done
echo "== 当前是否有训练进程 =="
ps aux | grep -E 'train_wsl2_ppo_v2|vcmi' | grep -v grep | head -5
echo "== is-active 各用户 =="
for u in $(awk -F: '$3>=1000 {print $1}' /etc/passwd); do
  echo -n "[$u] "
  su - "$u" -c "systemctl --user is-active homm3-train-v5" 2>&1 | head -1
done
