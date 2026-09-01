#!/usr/bin/env python3
"""检查 6 张 T03 地图的 hero 出生点 vs 守卫曼哈顿距离 (项目 1 守卫 patch 是否已做)"""
import zipfile, json, os

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/Maps/training"
MAPS = [
    "T03_adventure_20X20_01.vmap",
    "T03_adventure_20X20_02.vmap",
    "T03_adventure_30X30_01.vmap",
    "T03_adventure_30X30_02.vmap",
    "T03_adventure_36X36_01.vmap",
    "T03_adventure_36X36_02.vmap",
]
hero_mapsize_offsets = {  # vmap map size -> default hero spawn red (左下)
    20: (1, 18),
    30: (1, 28),
    36: (1, 34),
}

for name in MAPS:
    p = os.path.join(MAP_DIR, name)
    if not os.path.exists(p):
        print(f"{name}: NOT FOUND")
        continue
    try:
        with zipfile.ZipFile(p) as z:
            objs = json.loads(z.read("objects.json"))
            try:
                meta = json.loads(z.read("map.json"))
                w, h = int(meta["width"]), int(meta["height"])
            except:
                # 从名字取尺寸
                sz = int(name.split("_")[2].split("X")[0])
                w = h = sz
    except Exception as e:
        print(f"{name}: zip/parse ERR {e}")
        continue

    hero_x = hero_y = None
    monsters = []
    towns = []
    mines = []
    resources = []
    for k, o in objs.items():
        t = o.get("type", "")
        opts = o.get("options", {})
        # 2026-08-29 修复: vmap owner 在 options 内 ("red"/"blue" 字符串), 顶层 get("owner",1)
        # 恒取默认值 1 → 两个 hero 都命中且 blue(后遍历)覆盖 red → 历史输出全是 blue hero 距离 (bug)
        if "hero" in k or t == "hero":
            if opts.get("owner") == "red":
                hero_x, hero_y = int(o["x"]), int(o["y"])
        if k.startswith("monster_") or t == "monster":
            monsters.append((int(o["x"]), int(o["y"]), o.get("name","?"), opts.get("character","?"), opts))
        if "town" in k or t == "town":
            if opts.get("owner") == "red":
                towns.append((int(o["x"]), int(o["y"])))
        if t == "mine":
            mines.append((int(o["x"]), int(o["y"]), o.get("subtype", "?")))
        if t == "resource":
            resources.append((int(o["x"]), int(o["y"]), o.get("subtype", "?")))
    # 若没找到 hero 对象，按左下基线
    if hero_x is None:
        hero_x, hero_y = hero_mapsize_offsets.get(w, (1, w-2))
    dists = []
    for (mx, my, nm, ch, opts) in monsters:
        d = abs(mx - hero_x) + abs(my - hero_y)
        dists.append((d, mx, my, nm, ch, str(opts)[:60]))
    dists.sort()
    print(f"\n{name} ({w}x{h})  RED hero=({hero_x},{hero_y})  towns_red={towns}  monsters={len(monsters)}")
    for d, mx, my, nm, ch, opts in dists:
        mark = "⚠️FAR" if d >= 15 else "🔴" if d >= 10 else "🟡" if d >= 6 else "🟢"
        amt = opts.get("amount", "?") if isinstance(opts, dict) else "?"
        print(f"  {mark} d={d:2d}  ({mx:2},{my:2})  name={nm}  char={ch}  amount={amt}")
    if hero_x is not None:
        for (rx, ry, st) in mines:
            print(f"  [mine] d={abs(rx-hero_x)+abs(ry-hero_y):2d}  ({rx:2},{ry:2})  {st}")
        for (rx, ry, st) in resources:
            print(f"  [res ] d={abs(rx-hero_x)+abs(ry-hero_y):2d}  ({rx:2},{ry:2})  {st}")
