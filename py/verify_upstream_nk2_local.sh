#!/bin/bash
# 验证上游 NK2 修复是否已存在于本地树 (反向同步检查)
cd /mnt/d/Bigdata/hero3_fresh/vcmi
for kw in "isInTactics" "garrison army" "dwelling" "anchor position" "exploration point"; do
  echo "--- [$kw] local commits ---"
  git log --oneline -3 --all --grep="$kw" -- AI/ 2>/dev/null | head -3
done
