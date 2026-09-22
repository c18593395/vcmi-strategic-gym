#!/bin/bash
# #297 收口: batch1 混合轴挂起 (MIX=0), 恢复纯课程图训练 (09-22)
set -e
U1=/etc/systemd/system/homm3-train-v5.service
U2=/mnt/d/Bigdata/hero3_fresh/py/homm3-train-v5.service
for U in "$U1" "$U2"; do
  sed -i 's|^Environment=HOMM3_H3M_MIX=0.10.*|Environment=HOMM3_H3M_MIX=0  # 09-22: batch1 三图开局随机失败 (#297), 挂起待专项; BATCH=1 保留随时可启|' "$U"
  echo "[OK] $U:"
  grep -n 'HOMM3_H3M' "$U"
done
# good_to_go 部署文件恢复 pool 原版 (清掉实验用的重打包版)
cp /mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool/good_to_go_h3m.vmap \
   /home/administrator/vcmi-native/rel/bin/data/Maps/good_to_go_h3m.vmap
systemctl daemon-reload
systemctl restart homm3-train-v5
sleep 4
systemctl is-active homm3-train-v5
