#!/usr/bin/env bash
# B3 各规则独立开关对账 (设计稿 §7: 每个开关单独验证 report.json 计数)
# 必须在 /home/administrator/vcmi-native cwd 下跑引擎 (GameLibrary 找 config/)
set -u
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:${LD_LIBRARY_PATH:-}
BIN="${BIN:-/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap}"
KNEE="${KNEE:-/home/administrator/vcmi-native/data/Maps/Knee Deep in the Dead.h3m}"
[ -f "$KNEE" ] || KNEE="/home/administrator/vcmi-native/rel/bin/data/Maps/Knee Deep in the Dead.h3m"
cd /home/administrator/vcmi-native

OUTDIR=/tmp/b3_matrix
mkdir -p "$OUTDIR"

run_case() {
    local label="$1"; shift
    echo ""
    echo "===== CASE: $label ====="
    rm -f "$OUTDIR/$label.vmap" "$OUTDIR/report_$label.json"
    $BIN --save "$KNEE" "$OUTDIR/$label.vmap" "$@" 2>&1 | grep -E '  IN |  RULED|  OUT |ROUNDTRIP|SAVE OK'
    local rc=$?
    # report.json 写在 vmap 同目录, 挪走避免下个 case 残留误读
    if [ -f "$OUTDIR/report.json" ]; then
        mv "$OUTDIR/report.json" "$OUTDIR/report_$label.json"
        cat "$OUTDIR/report_$label.json"
    else
        echo "report.json: NOT WRITTEN"
    fi
}

# 1. 纯直通: 全部规则关 (B2 行为基线)
run_case "no_rules" --no-rules

# 2. 关 R1: 城镇不归零
run_case "no_r1" --no-r1

# 3. 关 R4: 全对象保留 (413)
run_case "no_r4" --no-r4

# 4. 关 R6: 保留原胜负事件
run_case "no_r6" --no-r6

# 5. 关 R7: 不改图名
run_case "no_r7" --no-r7

# 6. R3 半速: 守卫 x0.5
run_case "r3_050" --r3_scale 0.5

# 7. R3 关缩放 (1.0=原版, 仍做 neverFlees+SAVAGE)
run_case "r3_100" --r3_scale 1.0

# 8. R5 地形全草开
run_case "flatten" --terrain-flatten

# 9. 默认全开 (基线对照)
run_case "default"

echo ""
echo "===== MATRIX DONE ====="
