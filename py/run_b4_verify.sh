#!/usr/bin/env bash
# B4 验证: R2 开关对账 (no_r2 vs default) + 全规则正式产出 + header.json 校验
set -u
# #248: GameLibrary cwd 依赖, 必须 cd vcmi-native (CResourceHandler 相对路径)
cd /home/administrator/vcmi-native || exit 1
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:${LD_LIBRARY_PATH:-}
BIN=/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap
PY=/home/administrator/vcmi-workspace/venv/bin/python
KNEE="/home/administrator/vcmi-native/data/Maps/Knee Deep in the Dead.h3m"
[ -f "$KNEE" ] || KNEE="/home/administrator/vcmi-native/rel/bin/data/Maps/Knee Deep in the Dead.h3m"
CHECK=/mnt/d/Bigdata/hero3_fresh/py/b4_recon_players.py
OUTDIR=/tmp/b4_out
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"
RC_ALL=0

echo "=== [case no_r2] R1/R3/R4/R6/R7 on, R2 off ==="
"$BIN" --save "$KNEE" "$OUTDIR/no_r2.vmap" --no-r2 --map-name "P10_B4_KNEE_NO_R2" 2>&1 | grep -E 'IN |RULED|OUT|SAVE|ROUNDTRIP|REPORT'
RC=${PIPESTATUS[0]}; [ $RC -ne 0 ] && RC_ALL=1
echo "no_r2 RC=$RC"
"$PY" "$CHECK" "$OUTDIR/no_r2.vmap" 2>&1 | grep -E 'canPlay|howManyTeams|R2|red|blue' | head -12

echo ""
echo "=== [case default] all rules on (R1-R7, r3_scale=1.0) ==="
"$BIN" --save "$KNEE" "$OUTDIR/default.vmap" --map-name "P10_B4_KNEE_1V1" 2>&1 | grep -E 'IN |RULED|OUT|SAVE|ROUNDTRIP|REPORT'
RC=${PIPESTATUS[0]}; [ $RC -ne 0 ] && RC_ALL=1
echo "default RC=$RC"
echo "--- report.json ---"
cat "$OUTDIR/report.json" 2>/dev/null || echo "(no report)"
echo "--- header check ---"
"$PY" "$CHECK" "$OUTDIR/default.vmap" 2>&1 | tail -40

echo ""
echo "=== [formal] B4 正式产出 (全规则 r3_scale=1.0 → B4_adventure_knee_deep.vmap) ==="
"$BIN" --save "$KNEE" "$OUTDIR/B4_adventure_knee_deep.vmap" --map-name "P10_B4_KneeDeep_1v1" 2>&1 | grep -E 'RULED|SAVE|ROUNDTRIP|REPORT'
RC=${PIPESTATUS[0]}; [ $RC -ne 0 ] && RC_ALL=1
ls -la "$OUTDIR/B4_adventure_knee_deep.vmap"
echo "formal RC=$RC"

echo ""
echo "=== VERDICT: RC_ALL=$RC_ALL ==="
exit $RC_ALL
