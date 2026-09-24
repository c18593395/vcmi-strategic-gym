#!/bin/bash
# 读取指定栈文件中若干线程的完整帧（一次性小工具）
S=${1:-/tmp/_298_evidence/capture2/cap2_094610_r8_stacks.txt}
shift
for T in "$@"; do
  echo "########## $T ##########"
  awk -v t="^Thread $T " '$0 ~ t {f=1} f && /^Thread / && $0 !~ t {exit} f' "$S" | head -30
  echo
done