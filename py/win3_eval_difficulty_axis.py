#!/usr/bin/env python3
"""WIN-3 难度轴评估：72_02_duel 即插即用确认 + 108 duel 可完成度分析
vmap 结构：objects.json 是 dict {key: {l, x, y, type, options:{owner,...}}}
"""
import json, zipfile, os

BASE = "/mnt/d/Bigdata/hero3_fresh/maps/training"
STEPS_LIMIT = 200  # 当前 STEPS_PER_EP

for name in ["T06_adventure_72X72_02_duel", "T06_adventure_108X108_02_duel"]:
    p = os.path.join(BASE, f"{name}.vmap")
    with zipfile.ZipFile(p) as z:
        with z.open("header.json") as f:
            hdr = json.load(f)
        with z.open("objects.json") as f:
            objs = json.load(f)

    print(f"=== {name} ===")
    w = hdr.get("width", "?")
    h = hdr.get("height", "?")
    print(f"  size={w}x{h}")

    heroes = {k: v for k, v in objs.items() if "hero" in k.lower()}
    towns = {k: v for k, v in objs.items() if "town" in k.lower()}

    for k, v in heroes.items():
        owner = v.get("options", {}).get("owner", "?")
        print(f"  {k} pos=({v.get('x')},{v.get('y')}) owner={owner}")
    for k, v in towns.items():
        owner = v.get("options", {}).get("owner", "?")
        print(f"  {k} pos=({v.get('x')},{v.get('y')}) owner={owner}")

    # red hero -> blue town 曼哈顿距离
    red_h = {k: v for k, v in heroes.items() if v.get("options", {}).get("owner") == "red"}
    blue_t = {k: v for k, v in towns.items() if v.get("options", {}).get("owner") == "blue"}
    if red_h and blue_t:
        rh, bt = list(red_h.values())[0], list(blue_t.values())[0]
        dist = abs(rh["x"] - bt["x"]) + abs(rh["y"] - bt["y"])
        ratio = dist / STEPS_LIMIT
        print(f"  red_hero({rh['x']},{rh['y']}) -> blue_town({bt['x']},{bt['y']}) manhattan={dist} / {STEPS_LIMIT} = {ratio:.1%}")
        if ratio > 0.7:
            print(f"  ⚠ 距离比 {ratio:.0%} > 70%：200 步内完成 capture 偏紧，需 250 步或挪城")
        else:
            print(f"  ✓ 距离比 {ratio:.0%} ≤ 70%：200 步内可完成")
    print()
