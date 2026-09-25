# -*- coding: utf-8 -*-
# P1e-r3: 修复 pathfinder 格子坐标 → moveHero 锚点坐标 错配
#
# 根因 (server/CGameHandler.cpp L874 实锤):
#   const int3 hmpos = h->convertToVisitablePos(dst);
#   → moveHero 的 dst 是锚点坐标, server 内部减 offset(1,0) 得真实落格
#   → CGPathNode/CGPath 坐标是格子坐标 (pathfinder 口径)
#   → r2 把格子坐标直接喂 moveHero(pathVec) → 执行路径整体 x-1 幽灵偏移
#     本图 (T04_01) 走廊空旷侥幸推进; 幽灵步撞障碍/出图 → 每拍 0 推进死循环风险
#
# 修复 (2 行, for 循环体内):
#   1. 起点跳过: it->coord(格子) 改与 hero 真实落格 convertToVisitablePos(cur->pos) 比较
#   2. 入队换算: pathVec.push_back(cur->convertFromVisitablePos(it->coord))  格子→锚点
# 修复后: path 各步落格与规划一致, 尾补 standGoal 单步可同拍连上 → 直达门格 visit
import os
import io, sys

PATH = os.environ.get("PATH", "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp")
BAK = PATH + ".bak_p1e_r2"

with io.open(PATH, "r", encoding="utf-8") as f:
    src = f.read()

with io.open(BAK, "w", encoding="utf-8") as f:
    f.write(src)

T8 = "\t" * 8
T9 = "\t" * 9

OLD = (
    T8 + "if (it->coord == cur->pos)\n"
    + T9 + "continue;\n"
    + T8 + "if (it->turns > 0)\n"
    + T9 + "break;  // 移动力尽段截断: server 逐格校验必拒, 留下拍续走\n"
    + T8 + "pathVec.push_back(it->coord);"
)

NEW = (
    T8 + "if (it->coord == cur->convertToVisitablePos(cur->pos))\n"
    + T9 + "continue;  // P1e-r3: 起点按格子坐标比较 (CGPathNode=格子坐标, cur->pos=锚点坐标)\n"
    + T8 + "if (it->turns > 0)\n"
    + T9 + "break;  // 移动力尽段截断: server 逐格校验必拒, 留下拍续走\n"
    + T8 + "pathVec.push_back(cur->convertFromVisitablePos(it->coord));  // P1e-r3: 格子→锚点坐标 (moveHero 内部 convertToVisitablePos(dst) 减 offset 得落格, 错配=幽灵 x-1 偏移)"
)

cnt = src.count(OLD)
if cnt != 1:
    print("FAIL old-block count=%d (expect 1)" % cnt)
    sys.exit(1)

src = src.replace(OLD, NEW)

with io.open(PATH, "w", encoding="utf-8") as f:
    f.write(src)

print("OK r3 patched; %d -> %d chars" % (len(src) - len(NEW) + len(OLD), len(src)))
