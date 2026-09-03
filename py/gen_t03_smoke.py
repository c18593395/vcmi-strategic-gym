import zipfile, json
# R6 冒烟: T03 守卫加强 3→8 (与红 8 swordsman 均势) → 强制多回合攻防
p = '/mnt/d/Bigdata/hero3_fresh/Maps/training/T03_adventure_20X20_01.vmap'
dst = '/mnt/d/Bigdata/hero3_fresh/Maps/training/T03smoke_adventure_20X20_bai.vmap'
z = zipfile.ZipFile(p)
header = json.loads(z.read("header.json"))
terrain = json.loads(z.read("surface_terrain.json"))
objects = json.loads(z.read("objects.json"))

for k, v in objects.items():
    if v["type"] == "monster":
        v["options"]["amount"] = 8  # 3→8 均势

header["name"] = "T03smoke_adventure_20X20_bai"
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
    zout.writestr("surface_terrain.json", json.dumps(terrain))
    zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))
print("OK", dst, "guards→8")
