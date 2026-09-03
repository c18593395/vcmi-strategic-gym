import zipfile, json
# 解包检查现有 T04 图结构 (对象/城/守卫)
p = '/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_30X30_01.vmap'
z = zipfile.ZipFile(p)
print("=== zip 内容:", z.namelist())
objs = json.loads(z.read("objects.json"))
print("=== objects keys:", list(objs.keys()))
for k, o in objs.items():
    print(f"--- {k}: {json.dumps(o, ensure_ascii=False)[:260]}")
hdr = json.loads(z.read("header.json"))
print("=== header keys:", list(hdr.keys())[:15])
print("=== victory/defeat:", json.dumps(hdr.get('victoryString', hdr.get('victory', '')))[:150])
