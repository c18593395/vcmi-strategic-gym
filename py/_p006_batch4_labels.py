#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_p006_batch4_labels.py — P-006 batch4 数据层 5 维标签 + 岛屿 4 张分型 (09-27)

P-006 动作 (任务清单原文): _pool_index.json 补 {layer, underground, island, gate, water} 5 维标签
(复用 h3m_flat_pool.csv 的 water/land_components 信号) + island_king ×2 / thousand_islands ×2 逐张分型。
判据 (原文): mainTown 在岛而开局在大陆 = open_water_isolation (水堵 hold, BUILD_BOAT 落地前不放行,
同 a_viking batch=99 待遇)。

实现:
- water  = surface_terrain.json 中 wt* 瓦片占比 (纯水面, 沼泽 sw/sb 单独计 walkable_wet)
- island = 玩家 mainTown 所在陆地连通块 area < 20% 全部陆地 = "小岛"
- open_water_isolation = 红蓝 mainTown 不同块, 且其中一块为主大陆(最大块)另一为小岛
- gate = objects.json 有 subterraneanGate/labyrinth/openGate 类对象
- underground = header.mapLevels 有 underground 层
- 5 维标签写 batch4 全部 26 张的 index 条目 (layer/surface 恒 surface, 不动 batch 字段)
- open_water_isolation 命中的岛屿图 → index 加 batch:99 + hold_reason (水堵, 同 a_viking 待遇)
  注: 这些图当前 index 无 batch 字段 (= 已不放行, BATCH=2 下 batch=None 同样不入采样),
  标 99 只是显式记录 hold 决策, 行为零变化。

用法 (WSL 或 Windows python 均可, 无 VCMI 依赖):
  python py/_p006_batch4_labels.py --dry      # 只打印分型, 不写
  python py/_p006_batch4_labels.py            # 写本地 index + 打印待同步清单
"""
import json, os, sys, zipfile, collections, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "maps", "training", "h3m_pool")
BATCHES = os.path.join(ROOT, "maps", "h3m_to_vmap", "_pool_batches.json")
INDEX = os.path.join(ROOT, "maps", "h3m_to_vmap", "_pool_index.json")
DRY = "--dry" in sys.argv

GATE_TPL = ("subterraneanGate", "labyrinth", "openGate", "gate")
WATER_PFX = ("wt",)          # 纯水面 (sw=s 沼泽/walkable 不算水)
WET_PFX = ("sw", "sb")      # 沼泽/浅水 (可行走)


def is_water(tile):
    return tile.startswith("wt")


def land_components(grid):
    """BFS 陆地连通块 (水=wt*), 返回 (comp_id 网格, 各块面积). 网格坐标 (y, x)."""
    H = len(grid)
    W = len(grid[0]) if H else 0
    comp = [[-1] * W for _ in range(H)]
    areas = []
    for y in range(H):
        for x in range(W):
            if comp[y][x] != -1 or is_water(grid[y][x]):
                continue
            cid = len(areas)
            stack = [(y, x)]
            comp[y][x] = cid
            n = 0
            while stack:
                cy, cx = stack.pop()
                n += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and comp[ny][nx] == -1 and not is_water(grid[ny][nx]):
                        comp[ny][nx] = cid
                        stack.append((ny, nx))
            areas.append(n)
    return comp, areas


def main():
    b4 = json.load(open(BATCHES, encoding="utf-8"))["batch4_water_island"]
    idx = json.load(open(INDEX, encoding="utf-8"))
    names4 = [e["vmap"] for e in b4]
    # 4 张岛屿图 (P-006 点名): island_king ×2 / thousand_islands ×2
    island_names = [f for f in os.listdir(POOL)
                    if ("island_king" in f or "thousand_islands" in f) and f.endswith(".vmap")]
    todo = sorted(set(names4 + island_names))
    results = {}
    for v in todo:
        p = os.path.join(POOL, v)
        if not os.path.exists(p):
            print(f"[SKIP] {v} 不在池")
            continue
        z = zipfile.ZipFile(p)
        h = json.loads(z.read("header.json"))
        st = json.loads(z.read("surface_terrain.json"))
        # 部分 vmap (VCMI C++ json 序列化) objects.json 带 // game 注释行, 先剥离
        import re as _re
        _obj_raw = z.read("objects.json").decode("utf-8")
        _obj_clean = _re.sub(r"^\s*//.*$", "", _obj_raw, flags=_re.M)
        objs = json.loads(_obj_clean)
        W_ = h["mapLevels"]["surface"]["width"]
        H_ = h["mapLevels"]["surface"]["height"]
        # 网格可能比 map 小 (tile 图块=1 格), 取交集
        gh = min(len(st), H_)
        gw = min(len(st[0]), W_)
        water_frac = sum(is_water(st[y][x]) for y in range(gh) for x in range(gw)) / (gh * gw)
        wet_frac = sum(st[y][x].startswith(WET_PFX[0]) or st[y][x].startswith(WET_PFX[1])
                       for y in range(gh) for x in range(gw)) / (gh * gw)
        comp, areas = land_components(st)
        total_land = sum(areas) or 1
        main_id = areas.index(max(areas)) if areas else -1
        gate_n = sum(1 for o in objs if any(g.lower() in str(o.get("template", "")).lower() for g in GATE_TPL))
        has_ug = "underground" in (h.get("mapLevels") or {})
        # 玩家 mainTown (island_king 系/thousand_islands_allies 的 players.* = 空 dict → 主镇开局随机摆放)
        players = h.get("players") or {}
        mt = {}
        random_town = True
        for pid, p in players.items():
            m = (p or {}).get("mainTown") if isinstance(p, dict) else None
            mt[pid] = m
            if m and m.get("x") is not None:
                random_town = False
        mt_island = {}
        archipelago = len(areas) >= 2 and (areas[main_id] / total_land < 0.5)  # 无主大陆 = 群岛
        owi = False  # open_water_isolation
        for pid, m in mt.items():
            if not m:
                if random_town:
                    mt_island[pid] = "no_mainTown(主镇随机摆放)"
                continue
            x, y = m.get("x"), m.get("y")
            if x is None or y is None:
                mt_island[pid] = "no_mainTown(主镇随机摆放)" if random_town else "no_mainTown"
                continue
            if y >= gh or x >= gw or is_water(st[y][x]):
                mt_island[pid] = "on_water?!"
                continue
            cid = comp[y][x]
            mt_island[pid] = f"comp{cid}(area={areas[cid]},{areas[cid]/total_land*100:.0f}%)"
            if cid == main_id:
                mt_island[pid] += "=主大陆"
            else:
                mt_island[pid] += "=小岛"
        # open_water_isolation:
        #  (a) 群岛 (块≥2 且最大块<50% 陆地) → 主镇无论固定/随机必在岛上, 水堵
        #  (b) 双 mainTown 不同块且恰好一个主大陆一个非主大陆
        ids = [comp[mt[p]["y"]][mt[p]["x"]] for p in mt
               if mt.get(p) and mt[p].get("y") is not None
               and mt[p].get("y") < gh and mt[p].get("x") < gw]
        owi = archipelago
        if len(ids) >= 2:
            on_main = sum(1 for c in ids if c == main_id)
            owi = owi or ((len(set(ids)) > 1) and (0 < on_main < len(ids)))
        row = dict(
            layer="surface",
            underground=has_ug,
            island=(any("=小岛" in s for s in mt_island.values() if isinstance(s, str))
                    or archipelago),
            archipelago=archipelago,
            random_town=random_town,
            land_components=len(areas),
            island_note=("主镇随机摆放+群岛" if random_town and archipelago
                         else "群岛无主大陆" if archipelago
                         else ("主镇在小岛" if any("=小岛" in s for s in mt_island.values() if isinstance(s, str))
                              else ("主镇随机摆放" if random_town else None))),
            gate=gate_n,
            water=round(water_frac, 3),
            wet=round(wet_frac, 3),
            main_id_area_pct=round(areas[main_id] / total_land * 100, 1) if main_id >= 0 else None,
            mainTown_comp=mt_island,
            open_water_isolation=owi,
        )
        results[v] = row
        print(f"\n== {v}  water={row['water']:.2f} wet={row['wet']:.2f} gate={gate_n} ug={has_ug} "
              f"岛判定={row['island']} OWI={owi}")
        print(f"   mainTown: {mt_island}")
        print(f"   块数={len(areas)} 主大陆占比={row['main_id_area_pct']}%")

    if DRY:
        print(f"\n[dry] {len(results)} 张分型完成, 未写 index")
        json.dump(results, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_p006_dry.json"), "w"), indent=2)
        print("[dry] 明细落 py/_p006_dry.json")
        return

    # 写 index: 5 维标签全量 26+4, OWI 命中 → batch:99 hold
    changed = 0
    for v, row in results.items():
        e = idx.setdefault(v, {})
        e.update({k: row[k] for k in ("layer", "underground", "island", "gate", "water",
                                      "archipelago", "random_town", "land_components", "island_note")
                 if row.get(k) is not None})
        e["tag_ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        e["tag_tool"] = "_p006_batch4_labels.py"
        if row["open_water_isolation"]:
            e["batch"] = 99
            note = row.get("island_note") or "一岛一陆"
            e["hold_reason"] = f"09-27 P-006 分型 open_water_isolation ({note}), 水堵; BUILD_BOAT(P-008)落地前不放行, 同 a_viking batch:99 待遇"
        changed += 1
    json.dump(idx, open(INDEX, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    owi_hits = [v for v, r in results.items() if r["open_water_isolation"]]
    print(f"\n[write] index {INDEX} 更新 {changed} 张 | open_water_isolation 命中 {len(owi_hits)}: {owi_hits}")
    print("[sync] 需 scp 同步服务器 /DATA/hero3/train_server/pool/_pool_index.json (热生效, BATCH=2 下 99 图本就不采样)")


if __name__ == "__main__":
    main()
