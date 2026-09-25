#!/bin/bash
# 批次制对齐: MIX 0.25→0.10 + HOMM3_H3M_BATCH=1 (09-22, WIN-5 batch1)
set -e
U1=/etc/systemd/system/homm3-train-v5.service
U2="${U2:-/mnt/d/Bigdata/hero3_fresh/py/homm3-train-v5.service}"
for U in "$U1" "$U2"; do
  sed -i 's|^Environment=HOMM3_H3M_MIX=0.25.*|Environment=HOMM3_H3M_MIX=0.10  # WIN-5 batch1 (09-22): 10% 局采首批 5 张|' "$U"
  if ! grep -q 'HOMM3_H3M_BATCH' "$U"; then
    sed -i '/^Environment=HOMM3_H3M_MIX=/a Environment=HOMM3_H3M_BATCH=1  # 只采 _pool_index.json batch<=1 的图 (防负数: 水/岛/地下图不放行)' "$U"
  fi
  echo "[OK] $U:"
  grep -n 'HOMM3_H3M' "$U"
done
systemctl daemon-reload
systemctl restart homm3-train-v5
sleep 4
systemctl is-active homm3-train-v5
