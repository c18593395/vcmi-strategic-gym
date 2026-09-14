#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RedLossProbe_adventure_20X20.vmap — standardDefeat 红败定向实证图 (09-14, H3 立项配套)

目的: 定向制造"红方无将无城被 vanquished"局面, 实证败北信号断链 (根因 B):
  修复前预期 = 蓝杀红将+占空城后, 红 yourTurn 不再回调 -> probe wait 300s 超时,
               终局全零 obs / game_over=0 / r=0 (真 -200 丢失)
  修复后预期 = wait 轮询发现红 status=LOSER -> 秒回 -2 -> game_over=2, r 含 -200

布局 (20x20 全草地, 零遮挡):
  red  town_0 @ (2,2)  0 驻军 (options 无 garrison, 与现网训练图同口径)
  red  hero_0 @ (3,3)  1 peasant (edric)
  blue town_1 @ (11,11)
  blue hero_1 @ (6,4)  100 swordsman (iona), 距红英雄 4 格, 首日即可接敌
  无 mine/resource/monster — 蓝行军零干扰; 红方 probe --idle 全程 END_TURN

header 13 字段齐全 (0914 #225 口径): triggeredEvents standardDefeat=daysWithoutTown 7
作为双保险 (丢城 7 天也判负); 主动判负路径 = checkVanquished(无将 AND 无城)。

不入 train MAPS (纯探针图, 防污染训练池); 权威源 maps/training/ + 直接复制运行时
真实目录 vcmi/data/Maps (两棵 VCMI 树 data/Maps 软链同一目录)。
"""
import json
import shutil
import zipfile
from pathlib import Path

SRC = Path("/mnt/d/Bigdata/hero3_fresh/maps/training/T03smoke_adventure_20X20_bai.vmap")
DST_NAME = "RedLossProbe_adventure_20X20.vmap"
DST_SRC = Path("/mnt/d/Bigdata/hero3_fresh/maps/training") / DST_NAME
RUNTIME_REAL = Path("/mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps") / DST_NAME  # 软链真实目录

NAME = "RedLossProbe_adventure_20X20"

# 0914 #225 完整 header 模板 (与修复回池的 T06 图同口径)
TRIGGERED_EVENTS = {
    "specialVictory": {
        "condition": ["allOf", ["isHuman", {"value": 1}],
                      ["haveResources", {"type": 0, "value": 100}]],
        "effect": {"type": "victory"},
        "message": {"exactStrings": None, "localStrings": None,
                    "message": [2], "numbers": None,
                    "stringsTextID": ["core.genrltxt.278"]},
    },
    "standardDefeat": {
        "condition": ["daysWithoutTown", {"value": 7}],
        "effect": {"type": "defeat"},
        "message": {"exactStrings": None, "localStrings": None,
                    "message": [2], "numbers": None,
                    "stringsTextID": ["core.genrltxt.7"]},
    },
}


def main():
    z = zipfile.ZipFile(SRC)
    header = json.loads(z.read("header.json"))
    terrain = json.loads(z.read("surface_terrain.json"))
    objects = json.loads(z.read("objects.json"))
    z.close()

    # --- 全草地重置 (消除 rc00_/wt00_ 遮挡, 蓝军路径绝对畅通) ---
    terrain = [["gr24_" for _ in range(20)] for _ in range(20)]

    # --- 只留 2 hero + 2 town, 删一切干扰物 ---
    keep = {"hero_0", "hero_1", "town_0", "town_1"}
    objects = {k: v for k, v in objects.items() if k in keep}
    assert set(objects) == keep, f"底板物体异常: {list(objects)}"

    # --- red: 1 城 0 驻军 + 1 将 1 peasant, 贴城 ---
    t0 = objects["town_0"]
    assert t0["options"]["owner"] == "red"
    t0["x"], t0["y"] = 2, 2

    h0 = objects["hero_0"]
    assert h0["options"]["owner"] == "red" and h0["options"]["type"] == "core:edric"
    h0["x"], h0["y"] = 3, 3
    h0["options"]["army"] = [{"amount": 1, "type": "core:peasant"}, {}, {}, {}, {}, {}, {}]

    # --- blue: 1 城 + 1 将 100 swordsman, 贴红 4 格 ---
    t1 = objects["town_1"]
    assert t1["options"]["owner"] == "blue"
    t1["x"], t1["y"] = 11, 11

    h1 = objects["hero_1"]
    assert h1["options"]["owner"] == "blue" and h1["options"]["type"] == "core:iona"
    h1["x"], h1["y"] = 6, 4
    h1["options"]["army"] = [{"amount": 100, "type": "core:swordsman"}, {}, {}, {}, {}, {}, {}]

    # --- header: 改名 + 13 字段补齐, players 映射保持底板原样 (现网验证可加载) ---
    header["name"] = NAME
    header["description"] = "H3 red-defeat probe (red 1 peasant vs blue 100 swordsman, standardDefeat)"
    header["victoryConditions"] = ["standardDefeat", "specialVictory"]
    header["triggeredEvents"] = TRIGGERED_EVENTS
    header["mods"] = header.get("mods") if header.get("mods") is not None else None

    ordered_header = {
        "allowedArtifacts": header["allowedArtifacts"],
        "defeatIconIndex": header["defeatIconIndex"],
        "description": header["description"],
        "difficulty": header["difficulty"],
        "mapLevels": header["mapLevels"],
        "mods": header["mods"],
        "name": header["name"],
        "players": header["players"],
        "victoryConditions": header["victoryConditions"],
        "triggeredEvents": header["triggeredEvents"],
        "versionMajor": header["versionMajor"],
        "versionMinor": header["versionMinor"],
        "victoryIconIndex": header["victoryIconIndex"],
    }

    DST_SRC.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DST_SRC, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("header.json", json.dumps(ordered_header, ensure_ascii=False, indent=1))
        zout.writestr("surface_terrain.json", json.dumps(terrain))
        zout.writestr("objects.json", json.dumps(objects, ensure_ascii=False, indent=1))

    # --- 运行时真实目录双写 (两树软链同目录, 一处即生效) ---
    RUNTIME_REAL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(DST_SRC, RUNTIME_REAL)

    print(f"OK {DST_NAME}")
    print(f"  src     : {DST_SRC}")
    print(f"  runtime : {RUNTIME_REAL}")
    print(f"  red  town(2,2) 0garrison + hero(3,3) 1 peasant")
    print(f"  blue town(11,11) + hero(6,4) 100 swordsman")


if __name__ == "__main__":
    main()
