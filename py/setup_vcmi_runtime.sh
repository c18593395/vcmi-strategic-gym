#!/bin/bash
# 固化 VCMI 运行时依赖的 XDG 用户数据链 (踩坑 #308 修复固件)
# 必须以 root 运行（需 chown）。幂等, 可反复执行。
#   restart_train_v5_sys.sh 等启动脚本应在 start 之前 source/调用本脚本。
#
# 背景: 训练服务 User=administrator; VCMI 在 $XDG_DATA_HOME/vcmi/data 下找 Maps。
#       该目录链若不存在 → CFilesystemLoader::load 打开 .vmap 失败(误报 Permission denied)
#       → C++ 抛异常 → std::terminate → SIGABRT (池图必崩, 课程图也可能受路径解析影响)。
set -u

USER_NAME=administrator
HOME_DIR=/home/$USER_NAME
XDG="$HOME_DIR/.local/share"
RUNTIME_MAPS=/home/administrator/vcmi-native/rel/bin/data/Maps   # sync_maps_to_runtime.py 的目标(真实目录)

log() { echo "[setup_vcmi_runtime] $*"; }

[ "$(id -u)" = "0" ] || { log "必须以 root 运行"; exit 1; }

log "1) 预建 XDG 数据链 $XDG/vcmi/{data,config}"
mkdir -p "$XDG/vcmi/data" "$XDG/vcmi/config"
chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.local"

log "2) 解析运行时 Maps 真实目录"
if [ ! -d "$RUNTIME_MAPS" ]; then
  # 兜底: 若默认入口不在, 尝试 readlink rel/bin/data/Maps
  ALT=$(readlink -f /home/administrator/vcmi-native/rel/bin/data/Maps 2>/dev/null)
  if [ -n "$ALT" ] && [ -d "$ALT" ]; then RUNTIME_MAPS="$ALT"; fi
fi
log "   运行时 Maps = $RUNTIME_MAPS ($(ls "$RUNTIME_MAPS" 2>/dev/null | wc -l) 项)"
[ -d "$RUNTIME_MAPS" ] || { log "!! 运行时 Maps 不存在, 跳过软链"; exit 1; }

log "3) 软链 $XDG/vcmi/data/Maps -> $RUNTIME_MAPS"
rm -rf "$XDG/vcmi/data/Maps"          # 可能是早期误建的空目录
ln -s "$RUNTIME_MAPS" "$XDG/vcmi/data/Maps"
chown -h "$USER_NAME:$USER_NAME" "$XDG/vcmi/data/Maps"

log "4) 校验 (以 $USER_NAME 身份读取池图)"
sudo -u "$USER_NAME" -H bash -c "cat '$XDG/vcmi/data/Maps/King_of_Pain_h3m.vmap' >/dev/null 2>&1" \
  && log "   OK 可读 King_of_Pain" || log "   !! 不可读, 请检查权限链"
if ls "$XDG/vcmi/data/Maps/" 2>/dev/null | grep -q 'good_to_go_h3m'; then
  log "   OK 池图可见于 XDG Maps"
else
  log "   ⚠ 池图尚未同步到运行时 Maps (可跑 py/sync_maps_to_runtime.py)"
fi

log "完成: $XDG/vcmi/data/Maps -> $(readlink -f "$XDG/vcmi/data/Maps")"