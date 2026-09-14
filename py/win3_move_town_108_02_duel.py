#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WIN-3: 108X108_02_duel 蓝城挪位脚本（备料，WIN-1 达标 + 错窗确认后才执行）

背景: 108_02_duel red_hero -> blue_town 曼哈顿距离=200, /200步=100%,
      200 步内走满才到蓝镇门口，capture 不可完成。
      方案: 蓝城 (105,105) -> (98,98), 距离 200->174 (69%), 200 步内可完成。

用法:
    # 干跑（只报告，不写）
    python py/win3_move_town_108_02_duel.py --dry-run
    # 执行挪城
    python py/win3_move_town_108_02_duel.py
    # 执行后必须跑 sync
    # wsl bash -c "/home/administrator/vcmi-workspace/venv/bin/python py/sync_maps_to_runtime.py --strict"

纪律: 地图轴变更，与激励轴(T7.4/capture)/难度轴(duel 轴)不同窗。
      一次只加一个难度轴（错窗纪律）。
"""
import zipfile, json, shutil, argparse, os, sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "maps" / "training"
VMAP = SRC_DIR / "T06_adventure_108X108_02_duel.vmap"
OLD_TOWN_POS = (105, 105)
NEW_TOWN_POS = (98, 98)

def load_vmap(p):
    with zipfile.ZipFile(p, "r") as z:
        data = {n: z.read(n) for n in z.namelist()}
    return data

def save_vmap(p, data):
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, blob in data.items():
            zout.writestr(name, blob)

def find_blue_town(objects):
    """找到 blue owner 的 town 对象"""
    for k, v in objects.items():
        if v.get("type") == "town" and v.get("options", {}).get("owner") == "blue":
            return k, v
    return None, None

def main():
    ap = argparse.ArgumentParser(description="WIN-3 108_02_duel 蓝城挪位")
    ap.add_argument("--dry-run", action="store_true", help="只报告不写")
    args = ap.parse_args()

    if not VMAP.exists():
        print(f"❌ vmap 不存在: {VMAP}")
        sys.exit(1)

    print(f"=== WIN-3 108X108_02_duel 蓝城挪位 ===")
    print(f"文件: {VMAP}")
    print(f"挪位: {OLD_TOWN_POS} -> {NEW_TOWN_POS}")
    print()

    data = load_vmap(VMAP)
    header = json.loads(data["header.json"])
    objects = json.loads(data["objects.json"])

    # 找蓝城
    town_key, town_obj = find_blue_town(objects)
    if not town_obj:
        print("❌ 未找到 blue owner 的 town 对象")
        sys.exit(1)

    cur_x, cur_y = town_obj["x"], town_obj["y"]
    print(f"当前蓝城: key={town_key} pos=({cur_x},{cur_y}) owner=blue")
    if (cur_x, cur_y) != OLD_TOWN_POS:
        print(f"⚠ 当前位置 ({cur_x},{cur_y}) 与预期 {OLD_TOWN_POS} 不符，可能已挪过")
        if (cur_x, cur_y) == NEW_TOWN_POS:
            print("  蓝城已在目标位置，无需操作")
            sys.exit(0)

    # 找红英雄算距离
    red_hero = None
    for k, v in objects.items():
        if v.get("type") == "hero" and v.get("options", {}).get("owner") == "red":
            red_hero = v
            break
    if red_hero:
        dist_old = abs(red_hero["x"] - OLD_TOWN_POS[0]) + abs(red_hero["y"] - OLD_TOWN_POS[1])
        dist_new = abs(red_hero["x"] - NEW_TOWN_POS[0]) + abs(red_hero["y"] - NEW_TOWN_POS[1])
        print(f"红英雄: ({red_hero['x']},{red_hero['y']})")
        print(f"  距离(挪前): {dist_old} / 200步 = {dist_old/200:.0%}")
        print(f"  距离(挪后): {dist_new} / 200步 = {dist_new/200:.0%}")
    print()

    if args.dry_run:
        print("[DRY-RUN] 以下为将要执行的修改:")
        print(f"  1. {town_key}: x={cur_x}->x={NEW_TOWN_POS[0]}, y={cur_y}->y={NEW_TOWN_POS[1]}")
        print(f"  2. 保存 vmap: {VMAP}")
        print(f"  3. 跑 sync: wsl bash -c '/home/administrator/vcmi-workspace/venv/bin/python py/sync_maps_to_runtime.py --strict'")
        return

    # 执行挪城
    town_obj["x"] = NEW_TOWN_POS[0]
    town_obj["y"] = NEW_TOWN_POS[1]
    objects[town_key] = town_obj

    data["objects.json"] = json.dumps(objects, ensure_ascii=False, indent=1).encode()

    # 备份原文件
    backup = VMAP.with_suffix(".vmap.bak")
    if not backup.exists():
        shutil.copy2(VMAP, backup)
        print(f"备份: {backup}")

    save_vmap(VMAP, data)
    print(f"✅ 挪城完成: {town_key} -> ({NEW_TOWN_POS[0]},{NEW_TOWN_POS[1]})")
    print()
    print("⚠ 下一步必须跑同步:")
    print("  wsl bash -c '/home/administrator/vcmi-workspace/venv/bin/python py/sync_maps_to_runtime.py --strict'")
    print("  (自带 header.players/owner/identifier 预检 + 原子写 + 写后校验)")

if __name__ == "__main__":
    main()
