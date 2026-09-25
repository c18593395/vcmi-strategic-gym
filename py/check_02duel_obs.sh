#!/bin/bash
# 检查 72X72_02_duel vmap 的 obs 初始化相关字段（蓝方英雄/城镇坐标）
PYBIN="${PYBIN:-/home/administrator/vcmi-workspace/venv/bin/python3}"
$PYBIN - <<'PY'
import zipfile, json, os
base="${base:-/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps}"
print("=== 72X72 相关 vmap 列表 ===")
cands=[f for f in sorted(os.listdir(base)) if '72X72' in f and f.endswith('.vmap')]
print(cands)
for fn in cands:
    p=os.path.join(base,fn)
    with zipfile.ZipFile(p) as z:
        files=z.namelist()
        print(f"\n=== {fn} ({len(files)} files) ===")
        print("  files:", files)
        h=json.loads(z.read('header.json'))
        print("  size:", h.get('size'), "mapLevels keys:", list(h.get('mapLevels',{}).keys()))
        # 找蓝方英雄
        for ml in h.get('mapLevels',{}).values():
            if isinstance(ml, dict):
                for k,v in ml.items():
                    if 'hero' in k.lower():
                        print(f"  mapLevels.hero[{k}] =", v)
        # objects.json 里的英雄/城镇
        for of in ('objects.json','objectTypes.json'):
            if of in files:
                o=json.loads(z.read(of))
                if isinstance(o, dict):
                    print(f"  {of} keys:", list(o.keys())[:10])
                    # 找英雄
                    for kk,vv in o.items():
                        if 'hero' in kk.lower():
                            print(f"    {kk} = {vv}")
                else:
                    print(f"  {of} list len={len(o)}")
                    for item in o[:5]:
                        print("   ", item)
PY
