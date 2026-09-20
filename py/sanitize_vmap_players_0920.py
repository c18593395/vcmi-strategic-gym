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

    if "objects.json" in payload:
        objects = _loads_permissive(payload["objects.json"].decode("utf-8"))
        if isinstance(objects, list):
            keep, obj_changes = sanitize_objects(objects)
            changes.extend(obj_changes)
            if len(keep) != len(objects):
                payload["objects.json"] = json.dumps(keep, ensure_ascii=False, indent=1).encode("utf-8")

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
