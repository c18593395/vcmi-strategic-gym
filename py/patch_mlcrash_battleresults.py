#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ML fix: visitBattleResultsApplied / visitBattleCancelled 防守方英雄战死 null 解引用
(09-24, core.2888 实锤)。

上游缺陷: 战斗中英雄阵亡 → 英雄对象已从 gs 移除 (objects[id]=nullptr),
但 side.heroID 残留 → getSideHero(i)->id / gs.getHero(...) 未判空 → SIGSEGV。
两处同款: visitBattleResultsApplied (mana=min) + visitBattleCancelled (mana=)。

幂等: 已打则 skip。写入前备份 <file>.bak_mlcrash。
"""
import os
import shutil
import sys

ROOT = "/home/administrator/vcmi-native"
TARGET = os.path.join(ROOT, "lib/gameState/GameStatePackVisitor.cpp")
BAK = TARGET + ".bak_mlcrash"

T = "\t"

OLD_1 = (
    T + "for(auto i : {BattleSide::ATTACKER, BattleSide::DEFENDER})\n"
    + T + "{\n"
    + T + T + "if (currentBattle.getSide(i).heroID.hasValue())\n"
    + T + T + "{\n"
    + T + T + T + "CGHeroInstance * hero = gs.getHero(currentBattle.getSideHero(i)->id);\n"
    + T + T + T + "hero->mana = std::min(hero->mana, currentBattle.getSide(i).initialMana);\n"
    + T + T + "}\n"
    + T + "}"
)

NEW_1 = (
    T + "for(auto i : {BattleSide::ATTACKER, BattleSide::DEFENDER})\n"
    + T + "{\n"
    + T + T + "if (currentBattle.getSide(i).heroID.hasValue())\n"
    + T + T + "{\n"
    + T + T + T + "// ML fix (09-24): 英雄战死时已被移出 gs (objects[id]=nullptr), 但 side.heroID 残留\n"
    + T + T + T + "// → getHero 返回 null → mana 解引用 SEGV (core.2888 实锤: 防守方英雄阵亡局)\n"
    + T + T + T + "const CGHeroInstance * sideHero = currentBattle.getSideHero(i);\n"
    + T + T + T + "CGHeroInstance * hero = sideHero ? gs.getHero(sideHero->id) : nullptr;\n"
    + T + T + T + "if(!hero)\n"
    + T + T + T + "{\n"
    + T + T + T + T + "fprintf(stderr, \"[ML-fix] battleResultsApplied: side %d hero gone (died in battle), skip mana restore\\n\", static_cast<int>(i));\n"
    + T + T + T + T + "continue;\n"
    + T + T + T + "}\n"
    + T + T + T + "hero->mana = std::min(hero->mana, currentBattle.getSide(i).initialMana);\n"
    + T + T + "}\n"
    + T + "}"
)

OLD_2 = (
    T + "for(auto i : {BattleSide::ATTACKER, BattleSide::DEFENDER})\n"
    + T + "{\n"
    + T + T + "if (currentBattle.getSide(i).heroID.hasValue())\n"
    + T + T + "{\n"
    + T + T + T + "CGHeroInstance * hero = gs.getHero(currentBattle.getSideHero(i)->id);\n"
    + T + T + T + "hero->mana = currentBattle.getSide(i).initialMana;\n"
    + T + T + "}\n"
    + T + "}"
)

NEW_2 = (
    T + "for(auto i : {BattleSide::ATTACKER, BattleSide::DEFENDER})\n"
    + T + "{\n"
    + T + T + "if (currentBattle.getSide(i).heroID.hasValue())\n"
    + T + T + "{\n"
    + T + T + T + "// ML fix (09-24): 同 visitBattleResultsApplied, 英雄战死后判空 (防 SEGV)\n"
    + T + T + T + "const CGHeroInstance * sideHero = currentBattle.getSideHero(i);\n"
    + T + T + T + "CGHeroInstance * hero = sideHero ? gs.getHero(sideHero->id) : nullptr;\n"
    + T + T + T + "if(!hero)\n"
    + T + T + T + "{\n"
    + T + T + T + T + "fprintf(stderr, \"[ML-fix] battleCancelled: side %d hero gone (died in battle), skip mana restore\\n\", static_cast<int>(i));\n"
    + T + T + T + T + "continue;\n"
    + T + T + T + "}\n"
    + T + T + T + "hero->mana = currentBattle.getSide(i).initialMana;\n"
    + T + T + "}\n"
    + T + "}"
)


def main():
    if not os.path.isfile(TARGET):
        print("file missing:", TARGET, file=sys.stderr)
        return 2
    src = open(TARGET, encoding="utf-8").read()
    if "side hero gone (died in battle)" in src:
        print("already patched")
        return 0
    if not os.path.exists(BAK):
        shutil.copy2(TARGET, BAK)
        os.utime(TARGET, None)

    hits = 0
    for old, new in ((OLD_1, NEW_1), (OLD_2, NEW_2)):
        if old in src:
            src = src.replace(old, new, 1)
            hits += 1
    if hits == 0:
        print("no anchor hit — source may have drifted", file=sys.stderr)
        return 1
    open(TARGET, "w", encoding="utf-8").write(src)
    out = open(TARGET, encoding="utf-8").read()
    ok1 = "battleResultsApplied: side %d hero gone" in out
    ok2 = "battleCancelled: side %d hero gone" in out
    print("patched blocks:", hits, "verify1:", ok1, "verify2:", ok2)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())