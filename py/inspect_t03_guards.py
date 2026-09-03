import zipfile, json
p = '/mnt/d/Bigdata/hero3_fresh/Maps/training/T03_adventure_20X20_01.vmap'
z = zipfile.ZipFile(p)
o = json.loads(z.read("objects.json"))
for k, v in o.items():
    if v["type"] == "monster":
        print(k, (v["x"], v["y"]), v["subtype"], v["options"].get("amount"), v["options"].get("aggression"))
    if v["type"] == "hero":
        print(k, (v["x"], v["y"]), v["options"].get("owner"), v["options"]["army"][3])
