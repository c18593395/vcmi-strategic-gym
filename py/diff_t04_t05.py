import zipfile, json, glob
print("=== T04 (已验证可加载) 全对象 subtype:")
z = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T04_adventure_30X30_01.vmap')
o = json.loads(z.read("objects.json"))
for k, v in o.items():
    print(f"  {k}: type={v['type']} subtype={v.get('subtype')} options={json.dumps(v.get('options',{}))[:80]}")
print()
print("=== T05 (待修) 全对象 subtype:")
z = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_adventure_36X36_01.vmap')
o = json.loads(z.read("objects.json"))
for k, v in o.items():
    print(f"  {k}: type={v['type']} subtype={v.get('subtype')} options={json.dumps(v.get('options',{}))[:80]}")
