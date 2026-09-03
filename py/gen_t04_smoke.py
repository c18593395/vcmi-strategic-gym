#!/usr/bin/env python3
"""R6 BAI 决策回路定向冒烟图生成 (2026-09-03)
目的: 造一场"有来有回"的战斗 — 双英雄初始相邻 (第一回合必然相遇) + 兵力旗鼓相当 (多回合攻防)
设计: 基于 T04_adventure_20X20_01 结构, 20X20, 双城对角保留,
      hero_0(red) @(8,8) swordsman x8, hero_1(blue) @(11,11) archer x8  (间隔 3 格, 移动即接敌)
      兵力价值相当 (swordsman vs archer 同 tier), 保证多回合
运行: wsl bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/gen_t04_smoke.py"
"""
import zipfile, json, os

SRC = "/mnt/d/Bigdata/hero3_fresh/maps/training/T04_adventure_20X20_01.vmap"
DST = "/mnt/d/Bigdata/hero3_fresh/maps/training/T04smoke_adventure_20X20_bai.vmap"

with zipfile.ZipFile(SRC) as zin:
    header = json.loads(zin.read("header.json"))
    terrain = json.loads(zin.read("surface_terrain.json"))
    objects = json.loads(zin.read("objects.json"))

# 双英雄强制遭遇 v5 (终版): 敌英雄格 moveHero 会被 blocked 拒 (实测), 怪物格才会触发战斗
# → 岩石封死红英雄全部邻格, 唯一出口 (5,6) 放守卫怪 (core:archer x8, 兵力相当多回合)
# → 红方唯一合法移动 = 踩守卫格 = 强制战斗 (T03 验证过的机制)
# 蓝英雄挪回自己城边 (17,15) 不干扰
h0 = objects["hero_0"]
h0["x"], h0["y"] = 5, 7
h0["options"]["army"] = [{}, {}, {}, {"amount": 8, "type": "core:swordsman"}, {}, {}, {}]

h1 = objects["hero_1"]
h1["x"], h1["y"] = 17, 15
h1["options"]["army"] = [{}, {}, {}, {"amount": 8, "type": "core:archer"}, {}, {}, {}]

# 地形封锁: (5,7) 的 7 个非出口邻格全部岩石
for rx, ry in [(4, 6), (6, 6), (4, 7), (6, 7), (4, 8), (5, 8), (6, 8)]:
    terrain[ry][rx] = "rc00_"

# 守卫怪: 唯一出口 (5,6), 8 archer vs 8 swordsman = 兵力相当多回合攻防
objects["monster_0"] = {
    "l": 0,
    "options": {"amount": 8, "aggression": "guard", "formation": "wide"},
    "subtype": "core:archer",
    "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"],
                 "visitableFrom": ["+++", "+-+", "+++"]},
    "type": "monster",
    "x": 5, "y": 6,
}

# 城保留对角 (town_0 red 原位, town_1 blue 挪对角远端), 矿/资源保留
objects["town_0"]["x"], objects["town_0"]["y"] = 2, 3
objects["town_1"]["x"], objects["town_1"]["y"] = 17, 16

# R6 冒烟 v2 (2026-09-03): 守卫怪堵红城门 (2,6) — 红 start_home 回城/出城必经, 强制触发战斗
# 类型用 core:peasant (T05 验证存在; core:footman 在当前 fork 缺失 — T05 图加载失败实锤)
# 兵量 8 vs 红 8 swordsman+招兵 = 可赢但多回合攻防
objects["monster_0"] = {
    "l": 0,
    "options": {"amount": 8, "aggression": "guard", "formation": "wide"},
    "subtype": "core:peasant",
    "template": {"animation": "", "mask": ["VVV", "VAV", "VVV"],
                 "visitableFrom": ["+++", "+-+", "+++"]},
    "type": "monster",
    "x": 2, "y": 6,
}

header["name"] = "T04smoke_adventure_20X20_bai"
header["description"] = "R6 BAI decision-loop smoke map: adjacent equal-strength heroes, multi-round combat"

with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("header.json", json.dumps(header, ensure_ascii=False, indent=1))
    zout.writestr("surface_terrain.json", json.dumps(terrain))
    zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))

# 自校验
with zipfile.ZipFile(DST) as z:
    o = json.loads(z.read("objects.json"))
    h = len(json.loads(z.read("surface_terrain.json")))
    w = len(json.loads(z.read("surface_terrain.json"))[0])
for k, obj in o.items():
    assert 0 <= obj["x"] < w and 0 <= obj["y"] < h, f"{k} 越界"
dx = abs(o["hero_0"]["x"] - o["hero_1"]["x"])
dy = abs(o["hero_0"]["y"] - o["hero_1"]["y"])
print(f"OK {DST}")
print(f"  heroes dist chebyshev={max(dx,dy)} (3 = 相邻可达, 移动即接敌)")
print(f"  hero_0(red): {o['hero_0']['options']['army'][3]}")
print(f"  hero_1(blue): {o['hero_1']['options']['army'][3]}")
print(f"  towns: {[(o['town_0']['x'], o['town_0']['y']), (o['town_1']['x'], o['town_1']['y'])]}")
