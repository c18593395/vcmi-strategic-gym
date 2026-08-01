#!/bin/bash
# 抓训练卡死现场: 显示线程头 + 关键帧
cd /home/administrator/vcmi-workspace
for attempt in $(seq 1 10); do
  E=$(pgrep -f "ep_runner_one" | head -1)
  if [ -n "$E" ]; then
    echo "=== attempt $attempt: ep runner pid=$E ==="
    gdb -p "$E" -batch -ex "set pagination off" -ex "thread apply all bt 12" 2>&1 > /tmp/gdb_out.txt
    # 打印线程头 + 非 numpy 帧
    awk '
    /^Thread [0-9]+ \(Thread/ { print "---"; print; show=1; next }
    { if (show && $0 !~ /openblas|blas_thread|PyThread_acquire|numpy/) print }
    ' /tmp/gdb_out.txt | head -80
    break
  fi
  sleep 5
done
rm -f /tmp/gdb_out.txt
