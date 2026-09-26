#!/usr/bin/env bash
# ============================================================================
# 服务器 → WSL 回切训练 一键 SOP (09-26 固化, 无损续训)
#
# 场景: 服务器 172.16.2.40 挂掉 / 网络不可达时, WSL 侧从 state checkpoint 无损接手
#       (模型+优化器+step 全恢复, 仅丢服务器"最后一轮 PPO 更新"未消费的 buffer ~4-16 局)
#
# 用法 (在 WSL 内跑):
#   wsl bash -c "bash /mnt/d/Bigdata/hero3_fresh/py/restore_train_to_wsl.sh"
#   或 WSL 终端: bash /mnt/d/Bigdata/hero3_fresh/py/restore_train_to_wsl.sh
#
# 6 步: ①拉 state ②torch 验证 ③前置(unit enabled/XDG Maps/课程图) ④keepalive ⑤清 pycache ⑥启动
# 退出码: 0=全部通过 / 非0=某步失败(见 stderr)
# ============================================================================
set -uo pipefail   # 不用 -e: 第 1 步 scp 允许失败(网络挂), 本地 state 兜底

# ---- 路径常量 (全部 WSL 视角) ----
HERMES_ROOT="/mnt/d/Bigdata/hero3_fresh"
SERVER="root@172.16.2.40"
STATE_ON_SERVER="/DATA/hero3/train_server/assets/wsl2_model_state.pt"
STATE_LOCAL="$HERMES_ROOT/wsl2_model_state.pt"
VENV_PY="/home/administrator/vcmi-workspace/venv/bin/python"
UNIT="homm3-train-v5"

step() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }

# ---- 视角守卫: 必须在 WSL 内跑 ----
if [ ! -d "/mnt/d" ]; then
  echo "❌ 本脚本必须在 WSL 内跑 (检测到非 WSL 环境)"
  echo "   用法: wsl bash -c \"bash /mnt/d/Bigdata/hero3_fresh/py/restore_train_to_wsl.sh\""
  exit 2
fi

echo "=================================================="
echo "  服务器 → WSL 回切训练 SOP  (09-26 固化)"
echo "=================================================="

# ============ 1. 拉回最新 state checkpoint ============
step "[1/6] 拉回服务器最新 wsl2_model_state.pt"
if scp -o BatchMode=yes -o ConnectTimeout=10 "${SERVER}:${STATE_ON_SERVER}" "$STATE_LOCAL" 2>/dev/null; then
  echo "  ✅ 拉回成功: $(stat -c '%y' "$STATE_LOCAL" 2>/dev/null)"
else
  echo "  ⚠️ scp 失败 (服务器不可达 — 正常场景), 用本地已有 state 兜底"
  if [ -f "$STATE_LOCAL" ]; then
    echo "  本地已有: $(stat -c '%y %s' "$STATE_LOCAL")"
  else
    echo "  ❌ 本地也无 state, 无法续训 (需先手工 scp 一份)"
    exit 1
  fi
fi

# ============ 2. 验证 state 可加载 + step 号 + 无 NaN ============
step "[2/6] 验证 wsl2_model_state.pt (torch.load + 无 NaN)"
if "$VENV_PY" - "$STATE_LOCAL" <<'PY'
import sys, os, torch
p = sys.argv[1]
sd = torch.load(p, map_location='cpu', weights_only=False)
s = sd.get('step', 0)
nan = sum(1 for v in sd.get('model', {}).values()
          if torch.is_tensor(v) and (torch.isnan(v).any() or torch.isinf(v).any()))
print(f"  step={s}  keys={list(sd.keys())}  NaN/Inf={nan}  size={os.path.getsize(p)/1e6:.2f}M")
if nan != 0:
    print("  ❌ state 含 NaN/Inf, 不可用"); sys.exit(1)
if s <= 0:
    print(f"  ❌ step={s} 异常"); sys.exit(1)
print(f"  ✅ state 可加载, step={s}, 续训权威源就绪 (模型+优化器+step 全恢复)")
PY
then :; else echo "  ❌ state 验证失败"; exit 1; fi

# ============ 3. 前置检查: unit enabled + XDG Maps + 课程图 ============
step "[3/6] 前置检查"
# 3a. unit enabled (决定 WSL 重启自启, 必做)
ENABLED=$(systemctl is-enabled "$UNIT" 2>/dev/null || echo "disabled")
echo "  unit enabled: $ENABLED"
if [ "$ENABLED" != "enabled" ]; then
  echo "  补 enable..."; systemctl enable "$UNIT" 2>&1 | sed 's/^/    /'
fi

# 3b. XDG Maps dir (踩坑 #308 前置, 缺则池图必崩)
if [ -d /home/administrator/.local/share/vcmi/data/Maps ]; then
  echo "  ✅ XDG Maps dir OK"
else
  echo "  ❌ XDG Maps dir 缺失, 跑 setup_vcmi_runtime.sh..."
  bash "$HERMES_ROOT/py/setup_vcmi_runtime.sh" 2>&1 | tail -5 | sed 's/^/    /'
fi

# 3c. 课程图 10 张 (两棵 VCMI 树 data/Maps 软链到 maps/training)
NCOUNT=$(ls /home/administrator/vcmi-native/rel/bin/data/Maps/T0[56]_*.vmap \
          /home/administrator/vcmi-native/rel/bin/data/Maps/King_of_Pain*.vmap 2>/dev/null | wc -l)
echo "  课程图数量: $NCOUNT (期望 ≥10)"
if [ "$NCOUNT" -lt 10 ]; then
  echo "  ⚠️ 课程图不足 10 张, 确认 maps/training/ 权威源是否需要 sync (py/sync_maps_to_runtime.py --strict)"
fi

# ============ 4. keepalive 判活 (WSL 内部拉不了 Windows 进程) ============
step "[4/6] keepalive 判活提示"
echo "  ⚠️ WSL 内部无法检测/拉起 Windows keepalive, 请确认 Windows 侧已:"
echo "     Start-Process wsl.exe -ArgumentList '-d','Ubuntu','sleep','infinity' -WindowStyle Hidden"
echo "  判活 (Windows PowerShell): (Get-CimInstance Win32_Process -Filter \"Name='wsl.exe'\" | Where-Object { \$_.CommandLine -like '*sleep*infinity*' } | Measure-Object).Count ≥1"
echo "  若为 0, WSL 启动后 ~60s 会被 idle shutdown, 训练被杀"

# ============ 5. 清 __pycache__ (项目铁律) ============
step "[5/6] 清 __pycache__"
find "$HERMES_ROOT/py" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
echo "  已清"

# ============ 6. 启动 WSL 训练 (checkpoint resume) ============
step "[6/6] 启动 $UNIT (N_SUBPROC=4, checkpoint resume)"
systemctl start "$UNIT"
sleep 10
ACTIVE=$(systemctl is-active "$UNIT" 2>/dev/null || echo "unknown")
MAINPID=$(systemctl show "$UNIT" -p MainPID 2>/dev/null | cut -d= -f2)
echo "  is-active: $ACTIVE   MainPID: $MAINPID"
if [ "$ACTIVE" = "active" ]; then
  echo "  最新日志 (确认 resume 到正确 step):"
  tail -15 "$HERMES_ROOT/train_loop.log" 2>/dev/null | sed 's/^/    /'
fi

# ============ 总结 ============
echo
echo "=================================================="
if [ "${ACTIVE:-unknown}" = "active" ]; then
  echo "✅ WSL 已接手训练"
else
  echo "⚠️ 前置完成但训练未 active, 查: systemctl status $UNIT + journalctl -u $UNIT"
fi
echo "  数据语义: 模型+优化器+step 全恢复, 仅丢服务器最后一轮 PPO buffer (~4-16 局, 秒级)"
echo "  吞吐: N_SUBPROC=4 (比服务器 N=16 慢 ~4x, 模型质量无损)"
echo "  监控: systemctl status $UNIT + tail -f $HERMES_ROOT/train_loop.log"
echo "  回退: 改 unit HOMM3_N_SUBPROC=1 + daemon-reload + 重启 = 完全恢复串行"
echo "=================================================="
