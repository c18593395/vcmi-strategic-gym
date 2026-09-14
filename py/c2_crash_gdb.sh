#!/usr/bin/env bash
# C2 L1 crash dump 取证脚本（复发时临时使用）
# 用法：先解禁 core（wsl -u root），复现崩溃后调用本脚本
# 输入：CORE_FILE=core 路径, VCMISERVER=二进制路径
set -e

CORE_FILE="${1:?用法: c2_crash_gdb.sh <core_file> [vcmiserver_path]}"
VCMISERVER="${2:-/home/administrator/vcmi-workspace/rel/bin/vcmiserver}"

echo "=== C2 L1 crash dump analysis ==="
echo "core:   ${CORE_FILE}"
echo "server: ${VCMISERVER}"
echo ""

echo "--- bt 30 (主线程) ---"
gdb -batch -ex "bt 30" "${VCMISERVER}" "${CORE_FILE}" 2>&1

echo ""
echo "--- thread apply all bt 10 (全线程) ---"
gdb -batch -ex "thread apply all bt 10" "${VCMISERVER}" "${CORE_FILE}" 2>&1

echo ""
echo "--- info proc mappings (so 加载地址) ---"
gdb -batch -ex "info proc mappings" "${VCMISERVER}" "${CORE_FILE}" 2>&1 | head -40

echo ""
echo "=== 若栈在 ML 自有 .so (libmlclient/libmlserverplugin/libMMAI) → 走 L2 C++ 插桩 ==="
echo "=== 若栈在 libvcmi 引擎 → 评估上游/规避, 不死磕 (#105 教训) ==="
