import zipfile, json
z = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_adventure_36X36_01.vmap')
o = json.loads(z.read("objects.json"))
print(json.dumps(o["hero_0"], ensure_ascii=False, indent=1)[:600])
print("==== T04 hero_0 (已验证):")
z2 = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T04_adventure_30X30_01.vmap')
o2 = json.loads(z2.read("objects.json"))
print(json.dumps(o2["hero_0"], ensure_ascii=False, indent=1)[:600])
