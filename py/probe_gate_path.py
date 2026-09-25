#!/usr/bin/env python3
"""实锤 approach2 移动失败: (3,4)->门格(0,3) 地形级 BFS 可达性 + 局部 ASCII 图
背景: P1d-v2 approach2 13 次 from==to=(3,4), moveHero 直进门格 0 推进 (2026-09-03 凌晨)
"""
import os
import zipfile, json, os
from collections import deque

MAP_DIR = os.environ.get("MAP_DIR", "/mnt/d/Bigdata/hero3_fresh/maps/training")
MAPS = [
    "T04_adventure_20X20_01.vmap",
    "T04_adventure_20X20_02.vmap",
    "T04_adventure_30X30_01.vmap",
    "T04_adventure_30X30_02.vmap",
    "T04_adventure_36X36_01.vmap",
    "T04_adventure_36X36_02.vmap",
]
_DIRS = [(-1,0),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)]  # 动作码 0-7 (N,NE,E,SE,S,SW,W,NW)

def load(mapname):
    p = os.path.join(MAP_DIR, mapname)
    with zipfile.ZipFile(p) as z:
        terr = json.loads(z.read("surface_terrain.json"))
        objs = json.loads(z.read("objects.json"))
    H, W = len(terr), len(terr[0])
    grid = [[True]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            c = str(terr[y][x])
            if c.startswith("rc") or c.startswith("wa"):
                grid[y][x] = False
    towns = []
    for k, o in objs.items():
        if k.startswith("town_"):
            towns.append((k, int(o["x"]), int(o["y"]), str(o.get("options", {}).get("owner", "?"))))
    return grid, towns, terr

def bfs(grid, sx, sy, tx, ty, allow_target_blocked=False):
    """8邻 BFS, 对角禁穿双岩角; 返回 (路径长度, 路径list) 或 (None, None)"""
    H, W = len(grid), len(grid[0])
    if allow_target_blocked:
        pass  # 目标格允许不可站 (城格 visit 语义), 但中间格仍需可走
    elif not (0 <= tx < W and 0 <= ty < H and grid[ty][tx]):
        return None, None
    prev = {(sx, sy): None}
    q = deque([(sx, sy)])
    while q:
        cx, cy = q.popleft()
        if (cx, cy) == (tx, ty):
            path = []
            cur = (tx, ty)
            while cur:
                path.append(cur)
                cur = prev[cur]
            return len(path) - 1, path[::-1]
        for dx, dy in _DIRS:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < W and 0 <= ny < H) or (nx, ny) in prev or not grid[ny][nx]:
                continue
            if dx != 0 and dy != 0:
                if not grid[cy][nx] or not grid[ny][cx]:
                    continue
            prev[(nx, ny)] = (cx, cy)
            q.append((nx, ny))
    return None, None

def ascii_map(grid, terr, cx, cy, r=6):
    lines = []
    for y in range(max(0, cy-r), min(len(grid), cy+r+1)):
        row = ""
        for x in range(max(0, cx-r), min(len(grid[0]), cx+r+1)):
            if (x, y) == (cx, cy): row += "H"       # hero
            elif (x, y) == (2, 3): row += "T"       # town anchor
            elif (x, y) == (0, 3): row += "G"       # gate (visitablePos)
            elif not grid[y][x]: row += "#"
            else: row += "."
        lines.append(f"  y={y:2d} {row}")
    return "\n".join(lines)

for mapname in MAPS:
    grid, towns, terr = load(mapname)
    red_towns = [t for t in towns if t[3].lower() == "red"]
    if not red_towns:
        continue
    k, tx, ty, own = red_towns[0]
    if (tx, ty) != (2, 3):
        print(f"{mapname}: red town {k} at ({tx},{ty}) != (2,3), skip")
        continue
    print(f"=== {mapname} red_town={k} anchor=(2,3) ===")
    H, W = len(grid), len(grid[0])
    print(f"hero(3,4) walkable={grid[4][3]}  gate(0,3) walkable={grid[3][0]}")
    # 门格 8 邻
    nb = []
    for dx, dy in _DIRS:
        nx, ny = 0+dx, 3+dy
        if 0 <= nx < W and 0 <= ny < H:
            nb.append(f"({nx},{ny})={'W' if grid[ny][nx] else 'X'}")
    print(f"gate(0,3) 8-neighbors: {nb}")
    plen, path = bfs(grid, 3, 4, 0, 3, allow_target_blocked=True)
    if plen is None:
        print("BFS (3,4)->(0,3): UNREACHABLE (地形级不通!)")
    else:
        print(f"BFS (3,4)->(0,3): plen={plen} path={path}")
    plen2, _ = bfs(grid, 3, 4, 0, 3, allow_target_blocked=False)
    print(f"BFS 目标需可站口径: {'UNREACHABLE' if plen2 is None else f'plen={plen2}'}")
    print(ascii_map(grid, terr, 3, 4))
    print()
