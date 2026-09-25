#!/bin/bash
# 检查 T06 源文件和已生成 duel 文件的 zip 内容 (terrain_0.json 是否存在)
DIR_SRC="${DIR_SRC:-/mnt/d/Bigdata/hero3_fresh/Maps/training}"
DIR_RUN="${DIR_RUN:-/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps}"

check_zip() {
    local f="$1"
    local label="$2"
    echo "=== $label ==="
    if [ -f "$f" ]; then
        python3 -c "
import zipfile, sys
z = zipfile.ZipFile('$f')
names = z.namelist()
print('  files: ' + str(len(names)))
for n in sorted(names):
    print('  ' + n)
has_terrain0 = any('terrain_0' in n for n in names)
has_surface = any('surface_terrain' in n for n in names)
print('  terrain_0.json: ' + ('YES' if has_terrain0 else 'MISSING'))
print('  surface_terrain.json: ' + ('YES' if has_surface else 'MISSING'))
"
    else
        echo "  FILE NOT FOUND: $f"
    fi
    echo ""
}

check_zip "$DIR_SRC/T06_adventure_72X72_02.vmap" "源 72X72_02 (1v3)"
check_zip "$DIR_SRC/T06_adventure_108X108_01.vmap" "源 108X108_01 (1v3)"
check_zip "$DIR_SRC/T06_adventure_108X108_02.vmap" "源 108X108_02 (1v3)"
check_zip "$DIR_RUN/T06_adventure_72X72_02_duel.vmap" "已生成 72X72_02_duel"
check_zip "$DIR_RUN/T06_adventure_108X108_01_duel.vmap" "已生成 108X108_01_duel"
check_zip "$DIR_RUN/T06_adventure_108X108_02_duel.vmap" "已生成 108X108_02_duel"
check_zip "$DIR_RUN/T06_adventure_72X72_01_duel.vmap" "已有 72X72_01_duel (fix_t06_maps)"
