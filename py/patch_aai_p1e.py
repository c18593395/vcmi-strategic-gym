# -*- coding: utf-8 -*-
# P1e: 修复 approach2 moveHero 双病灶 (2026-09-03 源码实锤)
#   根因1: moveHero dst 语义=普通坐标, server convertToVisitablePos(dst) 二次换算;
#          传 visitable 门格 tp=(0,3) → (-1,3) 出图 → "outside the map" 拒
#   根因2: 单点 moveHero 要求 areNeighbours(h->pos,dst) 只支持一格, 跨多格必拒
#   解法: client 端 PathfinderCache 算路径 (目标=standGoal 城旁普通坐标),
#         path 版 moveHero 由 server 逐格推进; turns>0 段截断留下拍续走
import io, sys, shutil

P = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
src = io.open(P, "r", encoding="utf-8").read()
lines = src.split("\n")
n0 = len(lines)

def idx_of(sub, start=0):
    for i in range(start, len(lines)):
        if sub in lines[i]:
            return i
    return -1

# ---- 替换1: include PathfinderCache 头 ----
i = idx_of('#include "callback/CCallback.h"')
assert i >= 0 and "#include \"pathfinder/PathfinderCache.h\"" not in src, "include anchor"
if "#include \"pathfinder/CGPathNode.h\"" not in src:
    lines.insert(i + 1, '#include "pathfinder/PathfinderCache.h"')
    lines.insert(i + 2, '#include "pathfinder/CGPathNode.h"')

# ---- 替换2: approach2 主刀 (dxv>1||dyv>1 分支) ----
j = idx_of("cb->moveHero(cur, tp, false);  // tp = town->visitablePos()")
assert j >= 0, "approach2 anchor"
assert "int3 preP = cur->pos;" in lines[j - 1], "preP line"
IND = lines[j - 1][: len(lines[j - 1]) - len(lines[j - 1].lstrip())]
# 区间 [j-1, j+1]: preP 行 / moveHero 行 / DIAG 行; 保留其后的 return noTarget;
assert "RL-DIAG7] approach2 from=" in lines[j + 1], "diag line"
blk = []
blk.append(IND + "int3 preP = cur->pos;")
blk.append(IND + "int3 standGoal = cur->convertFromVisitablePos(tp);  // P1e: 门格左邻普通坐标, 落位 hmpos=门格即自动 visit")
blk.append(IND + "std::vector<int3> pathVec;")
blk.append(IND + "int pturns = -1;")
blk.append(IND + "try")
blk.append(IND + "{")
blk.append(IND + "\t// P1e 修复 P1d-v2 双病灶: ①moveHero dst=普通坐标, 传 visitable 门格被 server 二次换算出图拒 (13 次 0 推进根因1)")
blk.append(IND + "\t// ②单点 moveHero 受 areNeighbours 限一格, 跨多格必拒 (根因2); 改 client pathfinder + path 版逐格推进")
blk.append(IND + "\tPathfinderCache pfCache(cb.get(), PathfinderOptions(*cb));")
blk.append(IND + "\tauto paths = pfCache.getPathsInfo(cur);")
blk.append(IND + "\tif (const CGPathNode * dstNode = paths->getPathInfo(standGoal))")
blk.append(IND + "\t{")
blk.append(IND + "\t\tpturns = (int)dstNode->turns;")
blk.append(IND + "\t\tCGPath cgpath;")
blk.append(IND + "\t\tif (dstNode->reachable() && paths->getPath(cgpath, standGoal))")
blk.append(IND + "\t\t{")
blk.append(IND + "\t\t\t// cgpath.nodes 逆序 [dst,...,start]: 跳过起点, turns>0 段截断 (server 移动力逐格校验必拒)")
blk.append(IND + "\t\t\tfor (auto it = cgpath.nodes.rbegin(); it != cgpath.nodes.rend(); ++it)")
blk.append(IND + "\t\t\t{")
blk.append(IND + "\t\t\t\tif (it->coord == cur->pos)")
blk.append(IND + "\t\t\t\t\tcontinue;")
blk.append(IND + "\t\t\t\tif (it->turns > 0)")
blk.append(IND + "\t\t\t\t\tbreak;")
blk.append(IND + "\t\t\t\tpathVec.push_back(it->coord);")
blk.append(IND + "\t\t\t}")
blk.append(IND + "\t\t}")
blk.append(IND + "\t}")
blk.append(IND + "}")
blk.append(IND + "catch (const std::exception & e)")
blk.append(IND + "{")
blk.append(IND + "\tFILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] approach2P EXC: %s\\n\", e.what()); fclose(dg); }")
blk.append(IND + "}")
blk.append(IND + "catch (...)")
blk.append(IND + "{")
blk.append(IND + "\tFILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] approach2P EXC unknown\\n\"); fclose(dg); }")
blk.append(IND + "}")
blk.append(IND + "if (!pathVec.empty())")
blk.append(IND + "\tcb->moveHero(cur, pathVec, false);  // path 版: server 逐格推进, 踏上 standGoal 即 visit")
blk.append(IND + "else")
blk.append(IND + "\tcb->moveHero(cur, standGoal, false);  // fallback 单步 (仅邻接时合法; pathfinder 失败兜底)")
blk.append(IND + "{FILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] approach2P from=(%d,%d) to=(%d,%d) goal=(%d,%d) plen=%d turns=%d\\n\", (int)preP.x, (int)preP.y, (int)cur->pos.x, (int)cur->pos.y, (int)standGoal.x, (int)standGoal.y, (int)pathVec.size(), pturns); fclose(dg); } }")
lines[j - 1 : j + 2] = blk

# ---- 替换3: 主路径 else 分支删除带病 moveHero(tp) ----
k = idx_of("cb->moveHero(cur, tp, false);  // 已在锚点")
assert k >= 0, "else anchor"
assert lines[k - 1].strip() == "else", "else line"
IND2 = lines[k][: len(lines[k]) - len(lines[k].lstrip())]
lines[k - 1 : k + 1] = [
    "// P1e: 已在 standPos — 落位那步 server 已按 hmpos=门格触发 visit; 旧 moveHero(tp) 传",
    "// visitable 坐标必被 convertToVisitablePos 二次换算出图拒 (根因1 同源), 删除该无效调用",
]

shutil.copy(P, P + ".bak_p1d_v2")
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("OK lines %d -> %d" % (n0, len(lines)))
print("include@%d approach2@%d else@%d" % (i, j, k))
