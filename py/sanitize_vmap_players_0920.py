#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sanitize_vmap_players — vmap 玩家痕迹清洗 (09-20 A 类 adventure 卡死修复)

根因: 官方 h3m 多玩家图, C++ R2v2 重配只裁了 8 槽 canHuman/canComputer 与对象 tempOwner,
但 header 的 TIMED events[].players / triggeredEvents / predefinedHeroes 仍引用 green/tan 等
非 red/blue 色别 → 引擎启动建 StartInfo.playerInfos 时为不存在的玩家取 settings → throw
("Cannot find info about player green") → Failed to launch game → adventure_wait 300s。

处理:
  1. events[i].players           → 只留 red+blue (TIMED 奖励事件双方保留, AI 也吃红利)
  2. triggeredEvents[*].players  → 同上 (胜利/失败触发)
  3. predefinedHeroes            → 只留 owner 为 red/blue/neutral 的定义 (他色 hero 定义删除)
  4. players (8 槽 dict)         → 只留 red/blue 槽
  5. 剥 // 注释 + 合法 JSON 写回 (顺带治 saveMap 注释特产)

用法: python py/sanitize_vmap_players_0920.py <vmap路径> [--dry-run]
"""
import sys
import json
import copy
import zipfile
import shutil
import tempfile
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3m2vmap import _loads_permissive  # 读侧剥 // 注释

KEEP = {"red", "blue"}


def sanitize(header: dict, verbose=True):
    changes = []

    # 递归清洗 (09-20 泛化): 全树遍历, 键名 players/availableFor 的数组裁到 red|blue —
    # 实锤引用点: TIMED events[].players / predefinedHeroes[*].availableFor / players 8 槽,
    # 逐字段追会漏 (availableFor 130 个英雄定义每个都有), 递归一次治本。
    kept_arr = [c for c in ("red", "blue")]

    def _prune(node, path):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if k in ("players", "availableFor") and isinstance(v, list):
                    kept = [c for c in v if c in KEEP]
                    if len(kept) != len(v):
                        node[k] = kept
                        changes.append(f"{path}.{k} {v} -> {kept}")
                        continue
                _prune(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                _prune(v, f"{path}[{i}]")

    _prune(header, "header")
    return changes


def sanitize_v2(header: dict, objects: list, changes: list) -> bool:
    """09-21 #294 第 7 钉: teams 结盟 + mainTown 无效指向 — adventure timeout 根因对.

    实锤 (09-21 批转取证 diff):
      - a viking we shall go allied: teams=[["red","blue"]] 红蓝同队 → 引擎无敌人
        → "Can not end turn for player that is not in game!" → adventure 300s 卡死
        (PASS 对照图唯一 header diff 即此键; VCMI 缺省无 teams = 各自敌对 = 1v1 标准态)
      - a warm and familiar place: blue.mainTown 指向 (17,16) 但全图仅 1 城 (red 的,
        (14,15)) → blue 英雄无法生成 → 英雄段全空 [0/0×8] → 同症状卡死

    冒烟教训 (09-21 v2 首版): 直接删 mainTown → blue 无英雄 → 引擎
    "Expected at least 2 non-neutral players for non-randomHeroes mode, got 1"
    → Failed to launch。故改为**造城**: copy 现有城模板改 owner/坐标,
    generateHero=true 在城处生成英雄, 保住 2 non-neutral players。
    """
    modified_objects = False

    # 1) teams: 红蓝同队违反 1v1 对战结构 → 删键 (allied 图冒烟 700s 超时 → 33s 过 ✓)
    if "teams" in header:
        changes.append(f"teams 删除: {json.dumps(header['teams'], ensure_ascii=False)}")
        del header["teams"]

    # 2) mainTown 校验: 坐标处无城对象 → 造一座 (用清洗后 objects — 被删城不能当出生点)
    town_objs = [ob for ob in objects
                 if isinstance(ob, dict) and "town" in str(ob.get("type", "")).lower()]
    town_pos = {(ob.get("l"), ob.get("x"), ob.get("y")) for ob in town_objs}
    players = header.get("players")
    if isinstance(players, dict):
        for pid, p in players.items():
            if not isinstance(p, dict) or "mainTown" not in p:
                continue
            mt = p["mainTown"]
            key = (mt.get("l"), mt.get("x"), mt.get("y"))
            if key in town_pos:
                continue
            if not town_objs:
                changes.append(f"players.{pid}.mainTown 删除 (全图无城可参照造城)")
                del p["mainTown"]
                continue
            template = copy.deepcopy(town_objs[0])
            template["x"] = mt.get("x")
            template["y"] = mt.get("y")
            template["l"] = mt.get("l", 0)
            template["instanceName"] = f"town_main_{pid}"
            template.setdefault("options", {})["owner"] = pid
            objects.append(template)
            town_pos.add(key)
            modified_objects = True
            changes.append(f"players.{pid}.mainTown 造城 @({mt.get('x')},{mt.get('y')}) owner={pid}")
    return modified_objects


def sanitize_objects(objects: list, verbose=True):
    """objects 层清洗: 删非 red/blue/neutral owner 对象 + 无 type 对象.

    实锤 (Battle of the Sexes 3297 obj):
      - 1 green + 1 tan owner 漏网对象 → 引擎为 green 建 player → StartInfo 无 green
        → "Cannot find info about player green" → Failed to launch → adventure 卡死
      - 130 个无 type 对象 → "Object type missing" ×130 (引擎不认识, 加载即废)
    """
    changes = []
    keep_objs = []
    for ob in objects:
        if not isinstance(ob, dict):
            changes.append(f"非 dict 对象删除: {str(ob)[:60]}")
            continue
        own = ob.get("owner", ob.get("options", {}).get("owner"))
        typ = ob.get("type")
        if isinstance(own, str) and own.lower() not in KEEP and own.lower() != "neutral":
            changes.append(f"owner={own} 对象删除: {str(ob)[:80]}")
            continue
        align = ob.get("options", {}).get("alignmentToPlayer")
        if isinstance(align, str) and align.lower() not in KEEP and align.lower() != "neutral":
            changes.append(f"alignmentToPlayer={align} 对象删除: {str(ob)[:80]}")
            continue
        if not typ:
            changes.append(f"无 type 对象删除: {str(ob)[:80]}")
            continue
        keep_objs.append(ob)
    return keep_objs, changes


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    path = sys.argv[1]
    dry = "--dry-run" in sys.argv
    changes = sanitize_and_save(path, dry=dry)
    if changes is None:
        print("无玩家痕迹需清洗, 文件不变")
    else:
        print(f"OK: {len(changes)} 处已写回 {path}")


def sanitize_and_save(path, dry=False):
    """对 vmap 做玩家痕迹清洗并原位写回. 返回 changes 列表 (None=无需清洗)."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        payload = {n: z.read(n) for n in names}

    header = _loads_permissive(payload["header.json"].decode("utf-8"))
    changes = sanitize(header)

    objects_final = []
    objects_dirty = False
    if "objects.json" in payload:
        objects = _loads_permissive(payload["objects.json"].decode("utf-8"))
        if isinstance(objects, list):
            keep, obj_changes = sanitize_objects(objects)
            changes.extend(obj_changes)
            objects_final = keep
            if len(keep) != len(objects):
                objects_dirty = True
            # 09-21 v2: teams 结盟 + mainTown 造城 (#294 第 7 钉, adventure timeout 根因对)
            if sanitize_v2(header, objects_final, changes):
                objects_dirty = True
            if objects_dirty:
                payload["objects.json"] = json.dumps(objects_final, ensure_ascii=False, indent=1).encode("utf-8")

    if not changes:
        return None

    for c in changes:
        print("  *", c)

    clean = json.dumps(header, ensure_ascii=False, indent=1)  # 干净 JSON (无注释)
    payload["header.json"] = clean.encode("utf-8")

    if not dry:
        fd, tmp = tempfile.mkstemp(suffix=".vmap", dir=os.path.dirname(path) or ".")
        os.close(fd)
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for n in names:
                z.writestr(n, payload[n])
        shutil.move(tmp, path)
    return changes


if __name__ == "__main__":
    main()
