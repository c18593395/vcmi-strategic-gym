import zipfile, json
p = '/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_30X30_01.vmap'
z = zipfile.ZipFile(p)
t = json.loads(z.read("surface_terrain.json"))
print("=== terrain 类型:", type(t).__name__)
if isinstance(t, list):
    print("=== 行数:", len(t), " 首行类型:", type(t[0]).__name__)
    print("=== 首行前 10:", t[0][:10] if isinstance(t[0], list) else t[0][:10])
    if isinstance(t[0], list):
        print("=== 字段样例:", t[0][0])
else:
    print("=== keys:", list(t.keys())[:10])
h = json.loads(z.read("header.json"))
print("=== victoryConditions:", json.dumps(h.get('victoryConditions'), ensure_ascii=False)[:300])
print("=== players:", json.dumps(h.get('players'), ensure_ascii=False)[:300])
print("=== mapLevels:", json.dumps(h.get('mapLevels'))[:200])
