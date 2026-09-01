# -*- coding: utf-8 -*-
"""对比 20X20_01/02 地形: 守卫格/hero 邻域通行性差异"""
import zipfile, json

for name in ["T03_adventure_20X20_01.vmap", "T03_adventure_20X20_02.vmap"]:
    z = zipfile.ZipFile(f"/mnt/d/Bigdata/hero3_fresh/Maps/training/{name}")
    terr = json.loads(z.read("surface_terrain.json"))
    print(f"\n=== {name} === type={type(terr).__name__} len={len(terr)}")
    print("row0 样本:", json.dumps(terr[0][:4], ensure_ascii=False)[:300])
    # 障碍布局: wt00_=水 rc00_=岩
    hero = (7, 6) if "01" in name else (5, 4)
    guards = [(5, 6), (6, 5)] if "01" in name else [(8, 7), (9, 6)]
    mine = (6, 6) if "01" in name else (9, 7)
    print(f"hero={hero} guards={guards} mine={mine}  (H=hero G=guard M=mine ~=水 ^=岩)")
    for y in range(20):
        row = ""
        for x in range(20):
            c = terr[y][x]
            if (x, y) == hero: ch = "H"
            elif (x, y) in guards: ch = "G"
            elif (x, y) == mine: ch = "M"
            elif c.startswith("wt"): ch = "~"
            elif c.startswith("rc"): ch = "^"
            else: ch = "."
            row += ch
        print(f"  y{y:02d} {row}")
    # hero 8 邻域 + 守卫格 8 邻域的地形
    TN = lambda x, y: terr[y][x]
    print("hero 8邻域:")
    for d, (dx, dy) in enumerate([(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]):
        nx, ny = hero[0]+dx, hero[1]+dy
        if 0 <= nx < 20 and 0 <= ny < 20:
            print(f"  d{d} -> ({nx},{ny}) {TN(nx,ny)}")
    for gx, gy in guards:
        print(f"guard({gx},{gy}) tile={TN(gx,gy)}; 8邻域:")
        for d, (dx, dy) in enumerate([(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]):
            nx, ny = gx+dx, gy+dy
            if 0 <= nx < 20 and 0 <= ny < 20:
                print(f"  d{d} -> ({nx},{ny}) {TN(nx,ny)}")
