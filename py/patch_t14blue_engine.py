#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_t14blue_engine.py — T14.3 T14Blue 蓝方战略层插件引擎侧接入（7 处门控改动，默认 OFF 存量零 diff）

架构定谳 (fact #64, 09-26 八轮探针):
  本 fork = STATIC_AI 构建 (CDynLibHandler.cpp:10 #define STATIC_AI), 无 dlopen 通路。
  蓝方评测链路: client/Client.cpp initPlayerInterfaces → CDynLibHandler::getNewAI("T14Blue")
  → createAny 特化按 libpath.stem()=="libT14Blue" 匹配 → T14Blue::T14BlueGateway。
  T14BlueMod = NK2 同款 OBJECT 库 (AI/T14BlueMod/) → libFacade 聚进 libvcmi.so。

7 处改动 (全 #ifdef ENABLE_T14_BLUE / if(ENABLE_T14_BLUE) 门控, option 默认 OFF):
  1. CMakeLists.txt            option(ENABLE_T14_BLUE OFF)
  2. CMakeLists.txt            add_definitions(-DENABLE_T14_BLUE)
  3. AI/CMakeLists.txt         add_subdirectory(T14BlueMod) 门控
  4. libFacade/CMakeLists.txt  target_link_libraries(vcmi PRIVATE T14BlueMod) 门控
  5. CDynLibHandler.cpp        include + createAny 特化 stem=="libT14Blue" 分支
  6. AIFactory.cpp             include + createAdventureAI 名字分支
  7. AIFactory.cpp             isAvailableAdventureAI 名字分支

用法 (WSL):  python3 /mnt/d/Bigdata/hero3_fresh/py/patch_t14blue_engine.py [apply|--check|--rollback]
备份: 各文件 .bak_t14blue (已预建则复用)
"""
import sys, shutil, os

ROOT = "/home/administrator/vcmi-native"
SRC  = "/mnt/c/Users/Administrator/AppData/Local/hermes/profiles/h3_32b_homm3/cache/scratch/t14blue_files"
BAK  = ".bak_t14blue"

EDITS = []  # (relpath, old, new)

# ---- 1+2 root CMakeLists ----
EDITS.append((
 "CMakeLists.txt",
 'option(ENABLE_MMAI "Enable compilation of MMAI AI library" ON)\n',
 'option(ENABLE_MMAI "Enable compilation of MMAI AI library" ON)\n'
 'option(ENABLE_T14_BLUE "Enable compilation of T14Blue blue-side strategic AI (NK2-derived)" OFF)\n',
))
EDITS.append((
 "CMakeLists.txt",
 'if(ENABLE_MMAI)\n\tadd_definitions(-DENABLE_MMAI)\nendif()\n',
 'if(ENABLE_MMAI)\n\tadd_definitions(-DENABLE_MMAI)\nendif()\n'
 'if(ENABLE_T14_BLUE)\n\tadd_definitions(-DENABLE_T14_BLUE)\nendif()\n',
))

# ---- 3 AI/CMakeLists.txt ----
EDITS.append((
 "AI/CMakeLists.txt",
 'if(ENABLE_NULLKILLER2_AI)\n\tadd_subdirectory(Nullkiller2)\nendif()\n',
 'if(ENABLE_NULLKILLER2_AI)\n\tadd_subdirectory(Nullkiller2)\nendif()\n'
 '\nif(ENABLE_T14_BLUE)\n\tadd_subdirectory(T14BlueMod)\nendif()\n',
))

# ---- 4 libFacade/CMakeLists.txt ----
EDITS.append((
 "libFacade/CMakeLists.txt",
 '\t\tif(ENABLE_MMAI)\n\t\t\ttarget_link_libraries(vcmi PRIVATE MMAI)\n\t\tendif()\n',
 '\t\tif(ENABLE_MMAI)\n\t\t\ttarget_link_libraries(vcmi PRIVATE MMAI)\n\t\tendif()\n'
 '\t\tif(ENABLE_T14_BLUE)\n\t\t\ttarget_link_libraries(vcmi PRIVATE T14BlueMod)\n\t\tendif()\n',
))

# ---- 5 CDynLibHandler.cpp ----
EDITS.append((
 "lib/callback/CDynLibHandler.cpp",
 '#  ifdef ENABLE_MMAI\n#    include "../../AI/MMAI/MMAI.h"\n#  endif\n#  include "../../AI/EmptyAI/CEmptyAI.h"',
 '#  ifdef ENABLE_MMAI\n#    include "../../AI/MMAI/MMAI.h"\n#  endif\n'
 '#  ifdef ENABLE_T14_BLUE\n#    include "../../AI/T14BlueMod/T14BlueGateway.h"\n#  endif\n'
 '#  include "../../AI/EmptyAI/CEmptyAI.h"',
))
EDITS.append((
 "lib/callback/CDynLibHandler.cpp",
 '#ifdef ENABLE_ML\n\t// AAI is used for ML only, not during regular gameplay\n'
 '\tif(libpath.stem() == "libMMAI") {\n\t\treturn std::make_shared<MMAI::AAI::AAI>();\n\t}\n#endif\n'
 '\n\treturn std::make_shared<CEmptyAI>();\n}',
 '#ifdef ENABLE_ML\n\t// AAI is used for ML only, not during regular gameplay\n'
 '\tif(libpath.stem() == "libMMAI") {\n\t\treturn std::make_shared<MMAI::AAI::AAI>();\n\t}\n#endif\n'
 '\n#ifdef ENABLE_T14_BLUE\n\t// T14 blue-side strategic AI (NK2-derived harvest layer, 09-26 T14.3)\n'
 '\tif(libpath.stem() == "libT14Blue")\n\t\treturn std::make_shared<T14Blue::T14BlueGateway>();\n#endif\n'
 '\n\treturn std::make_shared<CEmptyAI>();\n}',
))

# ---- 6+7 AIFactory.cpp ----
EDITS.append((
 "lib/callback/AIFactory.cpp",
 '#ifdef ENABLE_MMAI\n#  include "../../AI/MMAI/MMAI.h"\n#endif\n',
 '#ifdef ENABLE_MMAI\n#  include "../../AI/MMAI/MMAI.h"\n#endif\n'
 '#ifdef ENABLE_T14_BLUE\n#  include "../../AI/T14BlueMod/T14BlueGateway.h"\n#endif\n',
))
EDITS.append((
 "lib/callback/AIFactory.cpp",
 '\tauto ret = std::make_shared<CEmptyAI>();\n\tret->dllName = name;\n\treturn ret;\n}\n\n'
 'std::shared_ptr<CBattleGameInterface> AIFactory::createBattleAI',
 '#ifdef ENABLE_T14_BLUE\n\tif(name == "T14Blue")\n\t{\n#ifdef ENABLE_NULLKILLER2_AI\n'
 '\t\tauto ret = std::make_shared<T14Blue::T14BlueGateway>();\n\t\tret->dllName = name;\n\t\treturn ret;\n'
 '#else\n\t\tthrow std::runtime_error("T14Blue requires ENABLE_NULLKILLER2_AI in this build!");\n#endif\n\t}\n#endif\n'
 '\nauto ret = std::make_shared<CEmptyAI>();\n\tret->dllName = name;\n\treturn ret;\n}\n\n'
 'std::shared_ptr<CBattleGameInterface> AIFactory::createBattleAI',
))
EDITS.append((
 "lib/callback/AIFactory.cpp",
 '#ifdef ENABLE_NULLKILLER2_AI\n\tif(name == "Nullkiller2")\n\t\treturn true;\n#endif\n\treturn false;\n}',
 '#ifdef ENABLE_NULLKILLER2_AI\n\tif(name == "Nullkiller2")\n\t\treturn true;\n#endif\n'
 '#ifdef ENABLE_T14_BLUE\n\tif(name == "T14Blue")\n\t\treturn true;\n#endif\n'
 '\treturn false;\n}',
))

# ---- 8+9 Nullkiller.h / Nullkiller.cpp: onPursueTurn() 钩子 (R13 必需接缝) ----
# .h: makeTurn decl 后插默认空虚函数 (NK2 实例调空实现=零行为变化)
EDITS.append((
 "AI/Nullkiller2/Engine/Nullkiller.h",
 '\tvoid init(const std::shared_ptr<CCallback> & cbInput, AIGateway * aiGwInput);\n\tvirtual void makeTurn();\n',
 '\tvoid init(const std::shared_ptr<CCallback> & cbInput, AIGateway * aiGwInput);\n'
 '\tvirtual void makeTurn();\n'
 '\t/// T14 (09-26): per-turn pursuit hook, called from makeTurn after defender reservation.\n'
 '\t/// NK2 default = empty (zero behavior change); T14Blue::T14Nullkiller overrides it (R13 harvest nudge).\n'
 '\tvirtual void onPursueTurn() {}\n',
))
# .cpp: makeTurn 的 reserveRequiredTownDefenders() 后调用钩子
EDITS.append((
 "AI/Nullkiller2/Engine/Nullkiller.cpp",
 '\t\treserveRequiredTownDefenders();\n\n\t\ttasks.clear();\n',
 '\t\treserveRequiredTownDefenders();\n\n'
 '\t\t// T14 (09-26): per-turn pursuit hook — NK2 empty default (zero behavior change);\n'
 '\t\t// T14Nullkiller overrides it to re-assert strongest-hero -> enemy-town march target.\n'
 '\t\tonPursueTurn();\n\n\t\ttasks.clear();\n',
))

NEWFILES = [
 "AI/T14BlueMod/StdInc.h",
 "AI/T14BlueMod/T14Nullkiller.h",
 "AI/T14BlueMod/T14Nullkiller.cpp",
 "AI/T14BlueMod/T14BlueGateway.h",
 "AI/T14BlueMod/T14BlueGateway.cpp",
 "AI/T14BlueMod/CMakeLists.txt",
]

def rel(p): return os.path.join(ROOT, p)

def main():
    mode = sys.argv[1].lstrip("-") if len(sys.argv) > 1 else "apply"

    if mode == "check":
        ok = True
        for p, old_s, new_s in EDITS:
            text = open(rel(p), encoding="utf-8").read()
            if new_s in text:
                print("ALREADY ", p)
            elif old_s in text:
                print("WILL-APPLY ", p)
            else:
                ok = False
                print("ANCHOR-FAIL ", p)
        print("CHECK", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    if mode == "rollback":
        for p in ["CMakeLists.txt","AI/CMakeLists.txt","libFacade/CMakeLists.txt",
                  "lib/callback/CDynLibHandler.cpp","lib/callback/AIFactory.cpp"]:
            src = rel(p + BAK)
            if os.path.exists(src):
                shutil.copy2(src, rel(p)); print("ROLLED", p)
            else:
                print("NOBAK", p)
        return

    # 1) copy new files (tolerant: scratch pruned after 24h idle -> tree files canonical)
    n_new = 0
    for f in NEWFILES:
        s = os.path.join(SRC, os.path.basename(f))
        d = rel(f)
        if os.path.exists(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d); n_new += 1
        elif not os.path.exists(d):
            print("MISSING both scratch and tree:", s, "->", d); sys.exit(1)
    print("NEWFILES OK (copied=%d, in-tree=%d)" % (n_new, len(NEWFILES) - n_new))

    # 2) apply edits (idempotent: skip if new already present)
    n_applied = n_skip = 0
    for p, old, new in EDITS:
        path = rel(p)
        text = open(path, encoding="utf-8").read()
        if new in text:
            n_skip += 1
            print("SKIP (idempotent)", p)
            continue
        if old not in text:
            print("ANCHOR FAIL", p, "missing:\n" + old[:120])
            sys.exit(1)
        bak = path + BAK
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
        n_applied += 1
        print("APPLIED", p)
    print("EDITS applied=%d skipped=%d" % (n_applied, n_skip))

if __name__ == "__main__":
    main()
