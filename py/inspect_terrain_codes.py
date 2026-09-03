import zipfile, json
z = zipfile.ZipFile('/mnt/d/Bigdata/hero3_fresh/Maps/training/T04_adventure_20X20_01.vmap')
t = json.loads(z.read("surface_terrain.json"))
from collections import Counter
c = Counter(code for row in t for code in row)
print("地形码分布:", dict(c))
print("样例行 5:", t[5][:20])
