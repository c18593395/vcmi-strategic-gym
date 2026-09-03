# -*- coding: utf-8 -*-
# P1e-r2: pfProbe 实锤 standGoal=(1,3) 城 body blocked (turns=255 acc=0)
#   修正: 中间目标 = 门格 8 邻中 pathfinder 可达格 (turns==0), path 至该格;
#         尾补 standGoal 单步 (邻接合法, server 落位 hmpos=门格自动 visit)
import io

P = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
lines = io.open(P, "r", encoding="utf-8").read().split("\n")

def find_all(sub):
    return [i for i, l in enumerate(lines) if sub in l]

a = find_all("int3 preP = cur->pos;")
assert len(a) == 1, "preP anchor"
a = a[0]
b = find_all("approach2P from=")
assert len(b) == 1, "diag anchor"
b = b[0]
IND = lines[a][: len(lines[a]) - len(lines[a].lstrip())]

blk = []
def A(s):
    blk.append(IND + s)

A("int3 preP = cur->pos;")
A("int3 standGoal = cur->convertFromVisitablePos(tp);  // 门格左邻普通坐标 (P1e-r2: 实测城 body blocked, 仅作最终步 dst)")
A("std::vector<int3> pathVec;")
A("int pturns = -1;")
A("try")
A("{")
A("\t// P1e 修复 P1d-v2 双病灶: ①moveHero dst=普通坐标, 传 visitable 门格被 server 二次换算出图拒 (13 次 0 推进根因1)")
A("\t// ②单点 moveHero 受 areNeighbours 限一格, 跨多格必拒 (根因2); 改 client pathfinder + path 版逐格推进")
A("\t// P1e-r2: pfProbe 实测 standGoal=(1,3) 城 body blocked (turns=255 acc=0) — 中间目标改门格 8 邻中")
A("\t// pathfinder 可达格, path 至该格后尾补 standGoal 单步, server 落位 hmpos=门格自动 visit")
A("\tPathfinderCache pfCache(cb, PathfinderOptions(*cb));")
A("\tauto paths = pfCache.getPathsInfo(cur);")
A("\tint3 msz = cb->getMapSize();")
A("\tint3 midGoal(-1,-1,-1);")
A("\tbool midOK = false;")
A("\tfor (int dy = -1; dy <= 1 && !midOK; dy++)")
A("\t\tfor (int dx = -1; dx <= 1 && !midOK; dx++)")
A("\t\t{")
A("\t\t\tif (dx == 0 && dy == 0)")
A("\t\t\t\tcontinue;")
A("\t\t\tint3 c = tp + int3(dx, dy, 0);")
A("\t\t\tif (c.x < 0 || c.y < 0 || c.z < 0 || c.x >= msz.x || c.y >= msz.y || c.z >= msz.z)")
A("\t\t\t\tcontinue;")
A("\t\t\tconst CGPathNode * pn = paths->getPathInfo(c);")
A("\t\t\tbool ok = pn && pn->reachable() && pn->turns == 0;")
A("\t\t\t{FILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] pfCand (%d,%d) turns=%u acc=%d ok=%d\\n\", (int)c.x, (int)c.y, pn ? (unsigned)pn->turns : 255, pn ? (int)pn->accessible : -1, ok ? 1 : 0); fclose(dg); } }")
A("\t\t\tif (ok)")
A("\t\t\t{")
A("\t\t\t\tmidGoal = c;")
A("\t\t\t\tmidOK = true;")
A("\t\t\t}")
A("\t\t}")
A("\tif (midOK)")
A("\t\tpturns = 0;")
A("\tif (midOK && midGoal != cur->pos)")
A("\t{")
A("\t\tCGPath cgpath;")
A("\t\tif (paths->getPath(cgpath, midGoal))")
A("\t\t\tfor (auto it = cgpath.nodes.rbegin(); it != cgpath.nodes.rend(); ++it)")
A("\t\t\t{")
A("\t\t\t\tif (it->coord == cur->pos)")
A("\t\t\t\t\tcontinue;")
A("\t\t\t\tif (it->turns > 0)")
A("\t\t\t\t\tbreak;  // 移动力尽段截断: server 逐格校验必拒, 留下拍续走")
A("\t\t\t\tpathVec.push_back(it->coord);")
A("\t\t\t}")
A("\t}")
A("}")
A("catch (const std::exception & e)")
A("{")
A("\tFILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] approach2P EXC: %s\\n\", e.what()); fclose(dg); }")
A("}")
A("catch (...)")
A("{")
A("\tFILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] approach2P EXC unknown\\n\"); fclose(dg); }")
A("}")
A("// 尾补最终步: 尾位(实际/将到)与 standGoal 邻接 → 追加; server 落位 hmpos=门格自动 visit")
A("{")
A("\tint3 tail = pathVec.empty() ? cur->pos : pathVec.back();")
A("\tint adx = tail.x - standGoal.x; if (adx < 0) adx = -adx;")
A("\tint ady = tail.y - standGoal.y; if (ady < 0) ady = -ady;")
A("\tif (adx <= 1 && ady <= 1 && tail.z == standGoal.z && !(tail == standGoal))")
A("\t\tpathVec.push_back(standGoal);")
A("}")
A("if (!pathVec.empty())")
A("\tcb->moveHero(cur, pathVec, false);  // path 版: server 逐格推进, 末步踏 standGoal 触发 visit")
A("else")
A("\tcb->moveHero(cur, standGoal, false);  // fallback 单步 (邻接时合法; pathfinder 失败兜底)")
A("{FILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\"); if (dg) { fprintf(dg, \"[RL-DIAG7] approach2P from=(%d,%d) to=(%d,%d) goal=(%d,%d) plen=%d turns=%d\\n\", (int)preP.x, (int)preP.y, (int)cur->pos.x, (int)cur->pos.y, (int)standGoal.x, (int)standGoal.y, (int)pathVec.size(), pturns); fclose(dg); } }")

lines[a : b + 1] = blk
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("OK r2 lines[%d:%d] -> %d blk" % (a, b, len(blk)))
