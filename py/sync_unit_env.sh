#!/bin/bash
# 统一设置 homm3-train-v5 unit 的环境变量 —— 双副本同步（防踩坑 #301 漂移）
#   U1 = /etc/systemd/system/homm3-train-v5.service   ← 运行时权威（systemd 实读，不在 git）
#   U2 = py/homm3-train-v5.service                    ← 仓内副本（可版本控制/bootstrap 源）
# 用法（root）: bash py/sync_unit_env.sh HOMM3_H3M_MIX=0.20 [OTHER_KEY=VALUE ...]
set -u
U1=/etc/systemd/system/homm3-train-v5.service
U2=/mnt/d/Bigdata/hero3_fresh/py/homm3-train-v5.service

if [ "$#" -eq 0 ]; then
  echo "用法: bash $0 KEY=VALUE [KEY=VALUE ...]"
  exit 2
fi

for kv in "$@"; do
  K="${kv%%=*}"
  V="${kv#*=}"
  for U in "$U1" "$U2"; do
    [ -f "$U" ] || { echo "[FAIL] 缺 $U"; exit 1; }
    if grep -q "^Environment=$K=" "$U"; then
      sed -i "s|^Environment=$K=.*|Environment=$K=$V|" "$U"
    else
      # 新键: 插到 MIX 行后（不存在则插到最后一个 Environment 行后）
      # 注意: 值可能含 '/' (如路径), 插入分支必须用 '|' 作分隔符, 不能用默认 '/'
      if grep -q '^Environment=HOMM3_H3M_MIX=' "$U"; then
        sed -i "\|^Environment=HOMM3_H3M_MIX=|a Environment=$K=$V" "$U"
      else
        sed -i "0,\|^Environment=|s||Environment=$K=$V\n&|" "$U"
      fi
    fi
  done
  echo "[OK] $K=$V  （已双写 U1+U2）"
done

systemctl daemon-reload
echo
echo "===== 权威实读 systemctl show ====="
systemctl show -p Environment homm3-train-v5
echo
echo "===== 双副本 diff ====="
if diff -q "$U1" "$U2" >/dev/null 2>&1; then
  echo "(两份完全一致 ✓)"
else
  diff "$U1" "$U2"
fi
echo
echo "===== 双副本 HOMM3 行 ====="
echo "-- U1($U1) --"; grep -n 'HOMM3' "$U1"
echo "-- U2($U2) --"; grep -n 'HOMM3' "$U2"