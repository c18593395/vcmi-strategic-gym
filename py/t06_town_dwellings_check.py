#!/usr/bin/env python3
"""judgement_day_h3m 城镇定义参照 (鲁棒解析)"""
import json, zipfile

z = zipfile.ZipFile('/home/administrator/vcmi-native/rel/bin/data/Maps/judgement_day_h3m.vmap')
print('members:', z.namelist()[:8])
raw = z.read('objects.json').decode('utf-8', 'ignore')
print('head 200:', raw[:200])

try:
    objs = json.loads(raw)
except Exception as e:
    print('json 解析失败:', e)
    # 可能是 NDJSON 或其他 — 找 town 关键字上下文
    idx = raw.find('town')
    print('town 上下文:', raw[max(0, idx-100):idx+500] if idx >= 0 else '无 town 字样')
    raise SystemExit(0)

lst = objs if isinstance(objs, list) else objs
if isinstance(lst, dict):
    items = lst.items()
else:
    items = [(str(i), o) for i, o in enumerate(lst)]

for k, o in items:
    if not isinstance(o, dict):
        continue
    if 'town' in str(o.get('type', '')).lower():
        opts = o.get('options', {})
        print(f"[{k}] owner={opts.get('owner')} pos=({o.get('x')},{o.get('y')})")
        for kk in sorted(opts.keys()):
            s = json.dumps(opts[kk], ensure_ascii=False)
            if len(s) > 400:
                s = s[:400] + "..."
            print(f"    {kk}: {s}")
        print()
