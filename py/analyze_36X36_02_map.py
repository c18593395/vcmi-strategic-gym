#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0910 36X36_02 地形障碍图: rocks/water ASCII 可视化 + red 路线阻塞分析 (对照 01)"""
import zipfile, json

MAP_DIR = "/mnt/d/Bigdata/hero3_fresh/maps/training/"

def load(name):
    z = zipfile.ZipFile(MAP_DIR + name)
    terr = json.loads(z.read("surface_terrain.json"))
    objs = json.loads(z.read("objects.json"))
    return terr, objs

def obstacles(terr):
    """返回 rock/water 坐标集 (y,x) — 统计每格地形码"""
    rocks, waters = set(), set()
    for y, row in enumerate(terr):
        for x, code in enumerate(row):
            c = str(code)
            if c.startswith("rc"): rocks.add((x, y))
            elif c.startswith("wa"): waters.add((x, y))
    return rocks, waters

def ascii_map(terr, objs, rocks, waters):
    # 对象标记: H=hero R=red town B=blue town M=monster m=mine .=资源
    marks = {}
    for k, o in objs.items():
        x, y = int(o["x"]), int(o["y"])
        t = o.get("type")
        ch = {"hero": "H", "town": "R" if o.get("options", {}).get("owner") == "red" else "B",
              "monster": "M", "mine": "m", "resource": "."}.get(t, "?")
        marks[(x, y)] = ch
    lines = []
    for y in range(len(terr)):
        row = []
        for x in range(len(terr[0])):
            if (x, y) in marks: row.append(marks[(x, y)])
            elif (x, y) in rocks: row.append("#")
            elif (x, y) in waters: row.append("~")
            else: row.append(" ")
        lines.append("".join(row))
    return lines

for name in ["T05_adventure_36X36_01.vmap", "T05_adventure_36X36_02.vmap"]:
    terr, objs = load(name)
    rocks, waters = obstacles(terr)
    print("=====", name, " rocks=%d water=%d" % (len(rocks), len(waters)))
    for i, ln in enumerate(ascii_map(terr, objs, rocks, waters)):
        print("%2d|%s|" % (i, ln))
