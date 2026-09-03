#!/bin/bash
echo "=== 崩溃记录 (dmesg):"
dmesg 2>/dev/null | tail -5
echo
echo "=== core 文件:"
ls -la /mnt/d/Bigdata/hero3_fresh/core* /tmp/core* /var/lib/apport/coredump/ 2>/dev/null | head -5
cat /proc/sys/kernel/core_pattern
echo
echo "=== ulimit:"
ulimit -c
echo
echo "=== journal 崩溃:"
journalctl --user -n 5 --no-pager 2>/dev/null | tail -5
