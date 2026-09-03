import zipfile, json
z = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T05_adventure_36X36_01.vmap')
o = json.loads(z.read("objects.json"))
print(json.dumps(o.get('monster_0'), ensure_ascii=False, indent=1))
# T04 hero 的 army 生物类型（验证哪些 subtype 存在）
z2 = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T04_adventure_30X30_01.vmap')
o2 = json.loads(z2.read("objects.json"))
print("T04 hero_0 army slot3:", o2["hero_0"]["options"]["army"][3])
