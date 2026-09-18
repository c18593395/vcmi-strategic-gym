#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""passable 闸门方案甲补丁 (09-17): strategic_state.cpp 两处 isClear 口径 → 对齐 GHandler movingOntoObstacle。
精确替换+断言次数, 失败即退出不改文件。"""
import sys

F = "/home/administrator/vcmi-native/ML/strategic_state.cpp"
src = open(F).read()

# ---- 补丁1: 第一处填充 (state-> 指针版) ----
old1 = """            const TerrainTile* hposTile = gicb->getTile(hpos, false);
            for (int d = 0; d < 8; d++) {
                int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
                const TerrainTile* tt = gicb->getTile(target, false);
                if (!tt) {
                    state->passable[d] = 0;  // off map / not visible
                } else {
                    state->passable[d] = tt->isClear(hposTile) ? 1 : 0;
                }
            }"""
new1 = """            for (int d = 0; d < 8; d++) {
                int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
                const TerrainTile* tt = gicb->getTile(target, false);
                if (!tt) {
                    state->passable[d] = 0;  // off map / not visible
                } else {
                    // passable 闸门修正 (09-17 方案甲): 口径对齐 CGameHandler::moveHero movingOntoObstacle
                    // (CGameHandler.cpp:916 blocked && !visitable; 拒绝仅: 地形不可通行 || 障碍且不可访问)。
                    // blocked-visitable 格 (敌英雄/怪/城) 可走且触发访问/战斗 (CGHeroInstance::onHeroVisit
                    // ENEMIES→startBattle 无条件); 旧 isClear 口径把它们标 0 = 观测错误, 模型/MOVE_TO/蓝AI
                    // 三方结构性不可达 → 真实战斗恒不触发 (WIN-1 真实击杀=0 机械根因, 踩坑索引见预研文档)
                    state->passable[d] = (tt->getTerrain()->isPassable()
                                          && !(tt->blocked() && !tt->visitable())) ? 1 : 0;
                }
            }"""

# ---- 补丁2: 第二处填充 (state. 引用版) ----
old2 = """            auto& hpos_tile = gs.getMap().getTile(hpos);
            for (int d = 0; d < 8; d++) {
                int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
                if (target.x < 0 || target.x >= (int)map.width || target.y < 0 || target.y >= (int)map.height) {
                    state.passable[d] = 0;
                } else {
                    auto& tile = gs.getMap().getTile(target);
                    state.passable[d] = tile.isClear(&hpos_tile) ? 1 : 0;
                }
            }"""
new2 = """            for (int d = 0; d < 8; d++) {
                int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
                if (target.x < 0 || target.x >= (int)map.width || target.y < 0 || target.y >= (int)map.height) {
                    state.passable[d] = 0;
                } else {
                    // passable 闸门修正 (09-17 方案甲): 同第一处, 口径对齐 GHandler movingOntoObstacle
                    auto& tile = gs.getMap().getTile(target);
                    state.passable[d] = (tile.getTerrain()->isPassable()
                                         && !(tile.blocked() && !tile.visitable())) ? 1 : 0;
                }
            }"""

for name, old, new in [("补丁1", old1, new1), ("补丁2", old2, new2)]:
    n = src.count(old)
    if n != 1:
        print(f"{name}: 匹配 {n} 次 (期望 1), 中止不改文件")
        sys.exit(1)
    src = src.replace(old, new)

open(F, "w").write(src)
print("两处补丁应用成功")
