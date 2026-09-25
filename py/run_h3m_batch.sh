#!/bin/bash
# 09-19 官方 H3M 全量批跑: 停训 → 后台批跑(断点续跑) → 自动重启训练 (纯串行, 踩坑#131 禁并行压死)
# 用法: wsl -u root bash /mnt/d/Bigdata/hero3_fresh/py/run_h3m_batch.sh [STEPS]
#   断点续跑: 中断后直接重跑本脚本即可 (PASS 条目自动 skip)
set -u
ROOT="${ROOT:-/mnt/d/Bigdata/hero3_fresh}"
STEPS=${1:-250}
LOG="$ROOT/tmp/h3m_batch_run.log"
VENV="${VENV:-/home/administrator/vcmi-workspace/venv/bin/python}"
# 09-23 路径环境化: 本脚本以 root 运行 (HOME=/root), 显式声明引擎/工作区路径
# (strategic_env.py 的默认值由 ~ 派生, root 下会指向 /root — 必须在此覆盖)
export VCMI_NATIVE_DIR=/home/administrator/vcmi-native
export VCMI_WORKSPACE_DIR=/home/administrator/vcmi-workspace

mkdir -p "$ROOT/tmp"

echo "[$(date '+%F %T')] [1/3] 停训 (systemctl stop homm3-train-v5)..."
systemctl stop homm3-train-v5 || true
sleep 2

echo "[$(date '+%F %T')] [2/3] 后台启动批跑 --resume-fail (steps=$STEPS, 断点续跑)..."
nohup "$VENV" "$ROOT/py/h3m_batch_pipeline.py" --resume-fail --steps "$STEPS" >> "$LOG" 2>&1 &
BATCH_PID=$!
echo "  批跑 pid=$BATCH_PID  日志=$LOG"

# 等批跑结束 (轮询 30s; 批跑写 report, 结束后自动重启训练)
echo "[$(date '+%F %T')] 等待批跑完成 (每 30s 轮询一次)..."
while kill -0 "$BATCH_PID" 2>/dev/null; do
    sleep 30
done
echo "[$(date '+%F %T')] 批跑结束 rc=$(wait $BATCH_PID 2>/dev/null; echo $?) 尾部日志:"
tail -5 "$LOG"

echo "[$(date '+%F %T')] [3/3] 重启训练 (checkpoint resume)..."
systemctl start homm3-train-v5
sleep 3
systemctl is-active homm3-train-v5
