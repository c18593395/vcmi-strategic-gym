#!/usr/bin/env python3
"""R6 BAI 决策回路定向冒烟图 v6 (2026-09-03)
机制链: start_home 回城取兵(~8步) → move_to_force 60 强制 a=24 走向 obj_best 目标(最近矿 (15,15))
       → BFS 路径穿守卫格 (Python BFS 不知道守卫) → moveHero 踩守卫 = 强制战斗
守卫: core:archer x8 放 (8,9) (红城→矿对角路径中段); 兵力相当 = 多回合攻防
参数: --economy_force 0 (消除 16-21 对 move_to 的覆盖)
"""
import os
import zipfile, json, os

SRC = os.environ.get("SRC", "/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_20X20_01.vmap")
DST = os.environ.get("DST", "/mnt/d/Bigdata/hero3_fresh/maps/training/T04smoke_adventure_20X20_bai.vmap")
with zipfile.ZipFile(SRC) as zin:
    header = json.loads(zin.read("header.json"))
    terrain = json.loads(zin.read("surface_terrain.json"))
    objects = json.loads(zin.read("objects.json"))

# 红英雄开局位, 蓝英雄远角不干扰
objects["hero_0"]["x"], objects["hero_0"]["y"] = 5, 7
objects["hero_0"]["options"]["army"] = [{}, {}, {}, {"amount": 8, "type": "core:swordsman"}, {}, {}, {}]
objects["hero_1"]["x"], objects["hero_1"]["y"] = 17, 15
objects["hero_1"]["options"]["army"] = [{}, {}, {}, {"amount": 8, "type": "core:archer"}, {}, {}, {}]

# 双城对角
objects["town_0"]["x"], objects["town_0"]["y"] = 2, 3
objects["town_1"]["x"], objects["town_1"]["y"] = 17, 16

# 守卫怪: 红城(2,3)/红英雄(5,7) → 矿(15,15) 对角路径中段, 双守卫纵深拦截
mk_monster = lambda x, y: {
    "l": 0,
    "options": {"amount": 8, "aggression": "guard", "formation": "wide"},
    "subtype": "core:archer",
    "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"],
                 "visitableFrom": ["+++", "+-+", "+++"]},
    "type": "monster", "x": x, "y": y,
}
objects["monster_0"] = mk_monster(8, 9)
objects["monster_1"] = mk_monster(10, 11)

header["name"] = "T04smoke_adventure_20X20_bai"
header["description"] = "R6 BAI decision-loop smoke v6: guard monsters on path to mine"

with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
    zout.writestr("surface_terrain.json", json.dumps(terrain))
    zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))

with zipfile.ZipFile(DST) as z:
    o = json.loads(z.read("objects.json"))
h = len(terrain); w = len(terrain[0])
for k, obj in o.items():
    assert 0 <= obj["x"] < w and 0 <= obj["y"] < h, f"{k} 越界"
print(f"OK {DST}")
print(f"  mine at: {(o['mine_0']['x'], o['mine_0']['y'])}")
print(f"  guards: {[(o['monster_0']['x'], o['monster_0']['y']), (o['monster_1']['x'], o['monster_1']['y'])]}")
print(f"  hero_0(red): {(o['hero_0']['x'], o['hero_0']['y'])}")
