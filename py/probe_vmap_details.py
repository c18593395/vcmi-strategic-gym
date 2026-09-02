#!/usr/bin/env python3
"""vmap2h3m 前置细节调研: 对象实例全表 + heroes index 字段确认"""
import glob, json, zipfile

# 1. T04 vmap 全对象
p = '/home/administrator/vcmi-native/rel/bin/data/Maps/T04_adventure_36X36_02.vmap'
with zipfile.ZipFile(p) as z:
    objs = json.loads(z.read('objects.json'))
    terr = json.loads(z.read('terrain_0.json')) if 'terrain_0.json' in z.namelist() else None
    hdr = json.loads(z.read('header.json'))
print("zip files:", zipfile.ZipFile(p).namelist())
print(f"objects ({len(objs)}):")
for k, v in list(objs.items()):
    print(f"  {k}: type={v.get('type')} subtype={v.get('subtype')} owner={v.get('options', {}).get('owner')} pos=({v.get('x')},{v.get('y')},{v.get('l')})")
print("town sample:", json.dumps([v for v in objs.values() if v.get('type') == 'town'][0], ensure_ascii=False)[:500])
print("hero sample:", json.dumps([v for v in objs.values() if v.get('type') == 'hero'][0], ensure_ascii=False)[:500])
print("mine sample:", json.dumps([v for v in objs.values() if v.get('type') == 'mine'][0], ensure_ascii=False)[:400])
if terr:
    print("terrain sample row0:", terr[0][:8] if isinstance(terr, list) else str(terr)[:200])
print("victory:", json.dumps(hdr.get('victoryCondition', hdr.get('triggeredEvents', 'N/A')))[:300])

# 2. heroes json index 确认 (容错注释解析)
def loose_json(path):
    import re
    txt = open(path).read()
    txt = re.sub(r'//[^\n]*', '', txt)
    txt = re.sub(r'/\*.*?\*/', '', txt, flags=re.S)
    return json.loads(txt)

hf = glob.glob('/home/administrator/vcmi-native/rel/bin/Mods/vcmi/Content/config/heroes/castle.json')[0]
d = loose_json(hf)
for k in list(d.keys())[:3]:
    e = d[k]
    print("hero:", k, "index=", e.get('index'), "class=", e.get('class'))
all_heroes = {}
for f in glob.glob('/home/administrator/vcmi-native/rel/bin/Mods/vcmi/Content/config/heroes/*.json'):
    d = loose_json(f)
    for k, v in d.items():
        if isinstance(v, dict) and 'index' in v:
            all_heroes[k] = v['index']
print("alchemist in heroes?", all_heroes.get('alchemist'))
print("sample hero ids:", dict(list(sorted(all_heroes.items(), key=lambda x: x[1]))[:6]))
