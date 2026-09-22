"""对比 T06/T05 训练图的 town subtype 命名 vs King of Pain 精简版"""
import zipfile, json, glob, os

for v in sorted(glob.glob('maps/training/*.vmap')):
    try:
        z = zipfile.ZipFile(v)
        o = json.loads(z.read('objects.json'))
    except Exception as e:
        print(f"{os.path.basename(v)}: {e}")
        continue
    subs = set()
    for k, v2 in o.items():
        if v2.get('type') == 'town':
            subs.add(v2.get('subtype'))
    towns = sum(1 for v2 in o.values() if v2.get('type') == 'town')
    print(f"{os.path.basename(v)}: towns={towns} subtypes={sorted(subs)}")
