# -*- coding: utf-8 -*-
# P1e-DIAG: approach2P 增加 pathfinder 八格探针 (hero 邻域 + 门格邻域 turns/accessible)
# 判据: 全 255 = calculatePaths 未生效; 仅 goal=255 = goal 格 blocked (城 body)
import io

P = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
lines = io.open(P, "r", encoding="utf-8").read().split("\n")

def idx_of(sub):
    for i, l in enumerate(lines):
        if sub in l:
            return i
    return -1

assert idx_of("pfProbe") < 0, "already patched"
j = idx_of("CGPath cgpath;")
assert j >= 0, "anchor"
IND = lines[j][: len(lines[j]) - len(lines[j].lstrip())]
probe = [
    IND + "\t\t\t{",
    IND + "\t\t\t\tint3 pr[8] = {cur->pos, cur->pos + int3(-1,0,0), cur->pos + int3(0,-1,0), cur->pos + int3(0,1,0), tp, standGoal, tp + int3(0,1,0), tp + int3(0,-1,0)};",
    IND + "\t\t\t\tconst char* pnm[8] = {\"hero\", \"heroW\", \"heroN\", \"heroS\", \"gate\", \"goal\", \"gateS\", \"gateN\"};",
    IND + "\t\t\t\tFILE* dg = fopen(\"/tmp/rl_recruit_diag.log\", \"a\");",
    IND + "\t\t\t\tif (dg) { for (int pi = 0; pi < 8; pi++) { const CGPathNode * pn = paths->getPathInfo(pr[pi]); if (pn) fprintf(dg, \"[RL-DIAG7] pfProbe %s (%d,%d) turns=%u acc=%d rem=%d\\n\", pnm[pi], (int)pr[pi].x, (int)pr[pi].y, (unsigned)pn->turns, (int)pn->accessible, pn->moveRemains); } fclose(dg); }",
    IND + "\t\t\t}",
]
lines[j:j] = probe
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("OK probe@%d total=%d" % (j, len(lines)))
