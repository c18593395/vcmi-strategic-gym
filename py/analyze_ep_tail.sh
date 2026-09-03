#!/bin/bash
# 当前活跃 ep 文件尾部: 短局如何结束
F=/tmp/hermes_ep_11638.log
echo "=== 文件大小/行数:"
wc -l "$F"
echo "=== 尾部 25 行:"
tail -25 "$F"
