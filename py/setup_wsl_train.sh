#!/bin/bash
# =====================================================================
# setup_wsl_train.sh — HoMM3 PPO 训练 WSL 一键重建总装脚本 (防再犯三件套③)
# =====================================================================
# 适用场景: rootfs 丢失/重装后，在新 Ubuntu(24.04) 上从零恢复训练环境。
# 前提(人工完成, 见知识库 09-19 章):
#   1) wsl --import Ubuntu D:\wsl\Ubuntu <rootfs.tar>
#   2) /etc/wsl.conf 配 systemd=true；administrator 用户 + sudo 免密已配
#   3) 网络可用(.wslconfig: firewall/dnsTunneling/autoProxy=false)
# 用法:
#   WSL 内:  sudo bash /mnt/d/Bigdata/hero3_fresh/py/setup_wsl_train.sh
#   编译阶段建议在持久终端跑；或整体 systemd-run 托管:
#     wsl -u root systemd-run --unit=setup919 --collect \
#         bash -c 'bash /mnt/d/Bigdata/hero3_fresh/py/setup_wsl_train.sh'
# 幂等: 全阶段可重复执行，已完成步骤自动跳过。
# 预计耗时: 全新环境 40-70min (大头=venv pip 下载 + mlclient 全量编译)
# =====================================================================
set -e
PROJ=/mnt/d/Bigdata/hero3_fresh
WS=/home/administrator/vcmi-workspace
NATIVE=/home/administrator/vcmi-native
SRC=$PROJ/vcmi   # 仓#3 主仓（含 mmai-ml-wsl，09-24 已收编仓#2 的 10 提交）；镜像仓已于 09-24 删除
VENV=$WS/venv
PIP="$VENV/bin/pip -i https://mirrors.aliyun.com/pypi/simple/ --default-timeout=60"

step() { echo; echo "==== [$1] $(date +%H:%M:%S) ===="; }

# ---- 0. 前置检查 ------------------------------------------------------------
step "0.前置检查"
[ -d "$PROJ/py" ] || { echo "FATAL: 找不到 $PROJ/py (D 盘项目未挂载?)"; exit 1; }
curl -s -m 8 -o /dev/null http://mirrors.aliyun.com/ubuntu/ && echo "网络 OK" || { echo "FATAL: WSL 出站网络不通 (查 .wslconfig / 360, 踩坑 #269 关联)"; exit 1; }

# ---- 1. apt 依赖 -------------------------------------------------------------
step "1.apt 依赖"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  build-essential cmake ninja-build pkg-config git wget curl ca-certificates \
  python3-dev python3-pip python3-venv \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libboost-all-dev \
  libavformat-dev libavcodec-dev libavutil-dev libswscale-dev libswresample-dev \
  libsquish-dev libtbb-dev liblua5.4-dev \
  zlib1g-dev liblzma-dev libpng-dev libfreetype6-dev libgif-dev \
  libxkbcommon-dev libwayland-dev \
  libminizip-dev libsqlite3-dev libcurl4-openssl-dev \
  libprotobuf-dev protobuf-compiler uuid-dev
echo "apt 完成"

# ---- 2. venv + Python 依赖 ----------------------------------------------------
step "2.venv"
if [ ! -x "$VENV/bin/python" ]; then
  mkdir -p "$WS"
  python3 -m venv "$VENV"
fi
$VENV/bin/python -m pip install -q --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
# 注意: gymnasium 必装 (vcmi_gym import 链, 踩坑: 漏装→ep_runner 秒退轮换)
$VENV/bin/python -m pip install --default-timeout=60 torch onnxruntime numpy gymnasium \
  -i https://mirrors.aliyun.com/pypi/simple/
$VENV/bin/python "$PROJ/py/check_torch_cuda_0919.py" || echo "WARN: CUDA 不可用(将继续用 CPU, 查 GPU 直通)"

# ---- 3. onnxruntime C++ (MMAI 依赖) -------------------------------------------
step "3.onnxruntime C++"
if [ -f /opt/onnxruntime/lib/libonnxruntime.so ]; then
  echo "已装，跳过"
else
  cd /tmp
  wget -q https://github.com/microsoft/onnxruntime/releases/download/v1.30.0/onnxruntime-linux-x64-1.30.0.tgz -O ort.tgz
  tar xzf ort.tgz
  mkdir -p /opt/onnxruntime
  cp -r onnxruntime-linux-x64-1.30.0/* /opt/onnxruntime/
  # 绕 ORT release 包 cmake config 的 lib64/include 路径 bug: 走 MMAI 手工查找分支
  rm -rf /opt/onnxruntime/lib/cmake
  echo "ORT 1.30.0 安装完成"
fi

# ---- 4. vcmi-native 源码 + 补丁 -------------------------------------------------
step "4.vcmi-native 源码"
if [ ! -d "$NATIVE/.git" ]; then
  # 09-24: 原从镜像仓 D:\Bigdata\git-mirrors\vcmi-native.git 克隆，该镜像已删除 → 改为直连仓#3。
  # 旧 fallback `cp -r $PROJ/vcmi` 已移除: 它拷的是仓#3 的 fix_action_mapping 工作树
  # (无 .git、且不是 mmai-ml-wsl)，会静默回退掉 #298 与 09-24 全部修复 —— 宁可 FATAL 也不静默降级。
  [ -d "$SRC/.git" ] || { echo "FATAL: 源仓缺失 $SRC (D 盘项目未挂载?)"; exit 1; }
  git clone "$SRC" "$NATIVE"
  git -C "$NATIVE" checkout mmai-ml-wsl
fi
# 补丁重放(全部幂等): clone 自仓#3 已含补丁则全跳过; 旧历史则正好打上
python3 "$PROJ/py/patch_passable_0917.py"          || true   # passable 豁免
python3 "$PROJ/py/patch_vcmidirs_0919.py"          || true   # VCMIDirs 纯虚实现
python3 "$PROJ/py/patch_gameengine_0919.py"        || true   # 死锁打点跨平台
python3 "$PROJ/py/patch_schema13_battleround_0919.py" || true # v13 BATTLE_ROUND
python3 "$PROJ/py/patch_static_ai_0919.py"         || true   # STATIC_AI + 解除 ML/MMAI 互斥
python3 "$PROJ/py/patch_mmai_build_0919.py"        || true   # MMAI 半成品 8 处

# ---- 5. cmake + 编译 mlclient --------------------------------------------------
step "5.编译 mlclient (全量 ~40min, 增量 <5min)"
cd "$NATIVE"
cmake -S . -B rel -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DENABLE_LAUNCHER=OFF -DENABLE_EDITOR=OFF -DENABLE_TEST=OFF \
  -DENABLE_MMAI=ON -DENABLE_DISCORD=OFF -DENABLE_ML=ON
cmake --build rel --target mlclient -j8
ls -la rel/bin/libmlclient.so

# ---- 6. connectors (pybind11) ---------------------------------------------------
step "6.connectors"
CONN=$WS/vcmi_gym/connectors
rm -rf "$CONN/build"
cd "$CONN"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j8
cp build/connector_v*.so rel/
ls rel/connector_v13.so

# ---- 7. vcmi_gym + 引擎数据树 + 地图校验 ------------------------------------------
step "7.数据树"
if [ ! -d "$WS/vcmi_gym" ]; then
  cp -r "$PROJ/vcmi_gym" "$WS/"
  cp "$CONN"/build/connector_v*.so "$WS/vcmi_gym/connectors/rel/" 2>/dev/null || true
fi
# 引擎数据树(H3 DATA/Mp3/config/Maps) 在 vcmi-native 仓库内; 缺失时从 D 盘底子拷
if [ ! -d "$NATIVE/data/DATA" ]; then
  cp -r "$PROJ/vcmi/data" "$NATIVE/data" 2>/dev/null || echo "WARN: data 树缺失且 D 盘底子拷贝失败"
fi
"$VENV/bin/python" "$PROJ/py/sync_maps_to_runtime.py" --check | tail -2

# ---- 8. unit 装回 + 启动 ---------------------------------------------------------
step "8.systemd unit"
systemctl daemon-reload
bash "$PROJ/py/restart_train_v5_sys.sh" start

# ---- 完成 -----------------------------------------------------------------------
step "完成"
cat <<'EOF'
恢复完成! 收尾清单:
1) Windows 侧手工拉 keepalive:  wsl.exe -d Ubuntu sleep infinity   (踩坑 #267 纪律)
2) 验证:  wsl bash -c "systemctl is-active homm3-train-v5; tail -5 /mnt/d/Bigdata/hero3_fresh/train_loop.log"
3) 首局观察: train_loop.log 应见 ep_steps/step 累加; 异常查 /tmp/hermes_ep_*.log
4) s2_auto_review.py / WIN-4 批转等后台任务按任务清单逐个重拉
EOF
