#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#215 headless if(ENGINE) 守卫重写 (09-26)

背景: 09-16 首次修复 (commit 65515ef24, 14 处) 被 09-19/09-23 上游全量重同步
冲掉, 原 commit 对象随 WSL rootfs 事故丢失, 现按 fact #215 记录重写
P8 终局可达路径的守卫。

崩溃点实录 (#215): headless 模式 EntryPoint `if(!headless) ENGINE=make_unique`
→ ENGINE 恒 null; 收 171KB LobbyStartGame 广播必经 startGameplay 路径即崩:
  首崩点 CServerHandler startGameplay 路径 ENGINE->discord()
        (unique_ptr::operator* this=null → null+0x80 = GameEngine 内 Discord 成员偏移)
  二次崩点 Client::removeGUI → ENGINE->windows()

本补丁 9 处 (P8 可达, 最小集):
  CServerHandler.cpp: sendRestartGame×2 / sendStartGame×2 /
                      showHighScoresAndEndGameplay×1 / endGameplay×1 / showServerError×2
  Client.cpp:         removeGUI×1
上游自带 9 处 if(ENGINE) (L108/126/284/306/329/355/788/1084/1103) 不动;
campaign/lobby-preview 路径 headless 不可达, 不补 (最小改动原则)。

运行:  wsl -u root bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/patch_215_engine_guard.py"
回退:  同命令加 rollback (.bak_215)
幂等:  任一编辑锚点命中 new 文本即 SKIP
"""
import os
import shutil
import sys

BASE = os.environ.get("BASE", "/home/administrator/vcmi-native")
CSH = BASE + "/client/CServerHandler.cpp"
CC = BASE + "/client/Client.cpp"
T = "\t"

EDITS = [
    # 1. sendRestartGame: CLoadingScreen 双分支收进 if(ENGINE){} (L695-698, 1-tab 缩进)
    (CSH,
     T + "if(si->campState && !si->campState->getLoadingBackground().empty())\n"
     + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>(si->campState->getLoadingBackground());\n"
     + T + "else\n"
     + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>();\n",
     T + "if (ENGINE) // #215 guard (09-26): headless ENGINE 恒 null, 收 LobbyStartGame 广播必经此路径\n"
     + T + "{\n"
     + T + "if(si->campState && !si->campState->getLoadingBackground().empty())\n"
     + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>(si->campState->getLoadingBackground());\n"
     + T + "else\n"
     + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>();\n"
     + T + "}\n",
     1),
    # 2. sendStartGame: 同款双分支 (L734-737, 2-tab 缩进 — 与 #1 靠缩进区分)
    (CSH,
     T + T + "if(si->campState && !si->campState->getLoadingBackground().empty())\n"
     + T + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>(si->campState->getLoadingBackground());\n"
     + T + T + "else\n"
     + T + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>();\n",
     T + T + "if (ENGINE) // #215 guard (09-26): 同上 (sendStartGame)\n"
     + T + T + "{\n"
     + T + T + "if(si->campState && !si->campState->getLoadingBackground().empty())\n"
     + T + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>(si->campState->getLoadingBackground());\n"
     + T + T + "else\n"
     + T + T + T + "ENGINE->windows().createAndPushWindow<CLoadingScreen>();\n"
     + T + T + "}\n",
     1),
    # 3. showHighScoresAndEndGameplay else 分支 (L810)
    (CSH,
     T + T + "GAME->mainmenu()->menu->switchToTab(\"main\");\n"
     + T + T + "ENGINE->windows().createAndPushWindow<CHighScoreInputScreen>(victory, scenarioHighScores, statistic);\n",
     T + T + "GAME->mainmenu()->menu->switchToTab(\"main\");\n"
     + T + T + "if (ENGINE) // #215 guard (09-26)\n"
     + T + T + T + "ENGINE->windows().createAndPushWindow<CHighScoreInputScreen>(victory, scenarioHighScores, statistic);\n",
     1),
    # 4. endGameplay 尾部 discord().setStatus (L833)
    (CSH,
     T + "ENGINE->discord().setStatus(\"\", \"\", {0, 0});\n",
     T + "if (ENGINE) // #215 guard (09-26)\n"
     + T + T + "ENGINE->discord().setStatus(\"\", \"\", {0, 0});\n",
     1),
    # 5. showServerError (L949-950)
    (CSH,
     T + "if(auto w = ENGINE->windows().topWindow<CLoadingScreen>())\n"
     + T + T + "ENGINE->windows().popWindow(w);\n",
     T + "if (ENGINE) // #215 guard (09-26)\n"
     + T + "{\n"
     + T + "if(auto w = ENGINE->windows().topWindow<CLoadingScreen>())\n"
     + T + T + "ENGINE->windows().popWindow(w);\n"
     + T + "}\n",
     1),
    # 6. Client.cpp removeGUI (L587, #215 二次崩点)
    (CC,
     T + "// CClient::endGame\n"
     + T + "ENGINE->windows().clear();\n",
     T + "// CClient::endGame\n"
     + T + "if (ENGINE) // #215 guard (09-26): headless 无 GUI, 二次崩点\n"
     + T + T + "ENGINE->windows().clear();\n",
     1),
]


def main():
    if "rollback" in sys.argv:
        for f in (CSH, CC):
            bak = f + ".bak_215"
            if os.path.exists(bak):
                shutil.copy2(bak, f)
                print("[OK] 回退 %s" % f)
            else:
                print("[SKIP] 无备份 %s" % bak)
        return

    contents = {}
    for f in (CSH, CC):
        contents[f] = open(f, encoding="utf-8").read()

    bad = 0
    for f, anchor, _new, expect in EDITS:
        n = contents[f].count(anchor)
        if n != expect:
            print("[FAIL] %s 锚点命中 %d (期望 %d): %r"
                  % (os.path.basename(f), n, expect, anchor[:70]))
            bad += 1
    if bad:
        print("[FAIL] %d 处锚点不匹配, 未写入任何文件" % bad)
        sys.exit(1)
    print("[OK] 锚点全量校验通过 (%d 处)" % len(EDITS))

    for f in (CSH, CC):
        shutil.copy2(f, f + ".bak_215")
    for f, anchor, new, _e in EDITS:
        contents[f] = contents[f].replace(anchor, new, 1)
    for f in (CSH, CC):
        open(f, "w", encoding="utf-8").write(contents[f])
    print("[OK] #215 守卫写入 %d 处 (备份 .bak_215)" % len(EDITS))


if __name__ == "__main__":
    main()
