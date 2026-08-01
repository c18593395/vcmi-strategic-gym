#!/bin/bash
# 复现崩溃 + addr2line 解析 libMMAI.so 崩溃函数
cd /home/administrator/vcmi-workspace
timeout 200 /home/administrator/vcmi-workspace/venv/bin/python -u /mnt/d/Bigdata/hero3_fresh/scripts/diag_repro.py > /tmp/diag_crash.log 2>&1
# 提取栈帧
grep -aE "^ *[0-9]+# " /tmp/diag_crash.log > /tmp/crash_stack.txt
head -8 /tmp/crash_stack.txt
# 找 libMMAI.so 帧地址
MMAI_FRAME=$(grep -aE "# 0x.*libMMAI" /tmp/crash_stack.txt | head -1)
echo "MMAI frame: $MMAI_FRAME"
# 从崩溃日志找进程 pid 和 maps
P=$(pgrep -f diag_repro | head -1)
echo "pid=$P (may be dead)"
