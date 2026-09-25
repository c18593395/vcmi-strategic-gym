#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ML fix: AAI::battleStart 无英雄防守方 null 解引用 (09-24, core.5836 实锤)。

缺陷(非上游冲掉, MMAI fork 既有): 中立怪/无英雄防守方开战时 army2 非 CGHeroInstance,
dynamic_cast 返回 null → info("..." + hero->getNameTextID()) 直接 SEGV。
实证: core.5836 — AAI.cpp:413 (DEFENDER 分支), hero2=0x0。
同型: ATTACKER 分支 (413 上一行) 也无判空, 一并保护。

幂等: 已打则 skip。写入前备份 <file>.bak_mlaai。
"""
import os
import shutil
import sys

ROOT = os.environ.get("ROOT", "/home/administrator/vcmi-native")
TARGET = os.path.join(ROOT, "AI/MMAI/AAI/AAI.cpp")
BAK = TARGET + ".bak_mlaai"

T = "\t"

OLD = (
    T + "if(side == BattleSide::ATTACKER)\n"
    + T + "{\n"
    + T + T + "hero = dynamic_cast<const CGHeroInstance *>(army1);\n"
    + T + T + "info(\"Will play with \" + hero->getNameTextID() + \" on the left side (ATTACKER) in this battle\");\n"
    + T + "}\n"
    + T + "else\n"
    + T + "{\n"
    + T + T + "hero = dynamic_cast<const CGHeroInstance *>(army2);\n"
    + T + T + "info(\"Will play with \" + hero->getNameTextID() + \" on the right side (DEFENDER) in this battle\");\n"
    + T + "}"
)

NEW = (
    T + "if(side == BattleSide::ATTACKER)\n"
    + T + "{\n"
    + T + T + "hero = dynamic_cast<const CGHeroInstance *>(army1);\n"
    + T + T + "// ML fix (09-24): 无英雄参战(中立怪战)时 dynamic_cast 得 null, 判空防 SEGV (core.5836)\n"
    + T + T + "info(std::string(\"Will play with \") + (hero ? hero->getNameTextID() : std::string(\"<no hero>\")) + \" on the left side (ATTACKER) in this battle\");\n"
    + T + "}\n"
    + T + "else\n"
    + T + "{\n"
    + T + T + "hero = dynamic_cast<const CGHeroInstance *>(army2);\n"
    + T + T + "info(std::string(\"Will play with \") + (hero ? hero->getNameTextID() : std::string(\"<no hero>\")) + \" on the right side (DEFENDER) in this battle\");\n"
    + T + "}"
)


def main():
    if not os.path.isfile(TARGET):
        print("file missing:", TARGET, file=sys.stderr)
        return 2
    src = open(TARGET, encoding="utf-8").read()
    if "<no hero>" in src:
        print("already patched")
        return 0
    if OLD not in src:
        print("anchor not found — source may have drifted", file=sys.stderr)
        return 1
    if not os.path.exists(BAK):
        shutil.copy2(TARGET, BAK)
        os.utime(TARGET, None)
    open(TARGET, "w", encoding="utf-8").write(src.replace(OLD, NEW, 1))
    out = open(TARGET, encoding="utf-8").read()
    ok = out.count("<no hero>") == 2
    print("patched, verify(2 branches):", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())