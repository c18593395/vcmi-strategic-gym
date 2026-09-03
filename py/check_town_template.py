# 2026-09-02 晚: 查 VCMI 原版城模板 visitableOffset (拍2诊断: P1c 守卫 visitable 口径杀邻接英雄)
# visitablePos = pos - visitableOffset; offset = 模板内第一个 visitable 格 (ObjectTemplate::calculateVisitableOffset)
import json, os, glob, sys

CANDS = [
    "/home/administrator/vcmi-native/mods/vcmi/config/objects/town.json",
]
# 兜底: 全盘找 town.json
if not os.path.exists(CANDS[0]):
    hits = glob.glob("/home/administrator/vcmi-native/**/objects/town.json", recursive=True)
    CANDS = hits[:3]

for path in CANDS:
    if not os.path.exists(path):
        print("MISS", path); continue
    print("FILE", path)
    d = json.load(open(path))
    for faction, body in d.items():
        tmpls = body.get("templates", {}) if isinstance(body, dict) else {}
        for tname, t in tmpls.items():
            vis = t.get("visitable")
            blk = t.get("blocked")
            print(f"  {faction}/{tname}: base={t.get('base','')} visitable={vis} blocked={blk}")
