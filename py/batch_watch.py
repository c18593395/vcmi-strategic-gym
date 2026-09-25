#!/usr/bin/env python3
"""批转监控: 从指定起点行号读 h3m_batch_run.log 新轮次内容, 过滤 sanitize 明细噪声.
用法: python py/batch_watch.py [起始行号, 默认找最后一个 '^\\[1/']"""
import os
import re
import sys

LOG = os.environ.get("LOG", "/mnt/d/Bigdata/hero3_fresh/tmp/h3m_batch_run.log")
start_marker = sys.argv[1] if len(sys.argv) > 1 else None

lines = open(LOG, errors="replace").readlines()
if start_marker is None:
    # 找最后一个 "[N/160]" 且 N 很小的新轮次起点 (160=小写枚举张数)
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r"^\[1/16\d\]", lines[i]):
            start_marker = i
            break
start = int(start_marker) if start_marker else 0
noise = re.compile(r"availableFor|\* header\.|events\[|\.players")
out = [l.rstrip() for l in lines[start:] if not noise.search(l)]
# 压缩连续 SANITIZE 明细后的空行
print(f"== 从第 {start} 行起 ({len(lines)} 行总计) ==")
print("\n".join(out[-60:]))
