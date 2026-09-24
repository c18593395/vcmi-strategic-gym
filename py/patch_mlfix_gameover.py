#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ML fix: PlayerEndsGame → 强制 game_over（09-24，冻结最后一环）。

根因（r12 冻结栈）: 占城胜利后 yourTurn 不再回调，NK2 卡 waitTillFree 空转，
strategic_state_update 永远不再跑 → python 侧读不到 game_over → ep 永久挂起（拖 400s 看门狗）。

修复: 客户端收到 PlayerEndsGame 时立即强制置位 game_over（含胜负方映射），
adventure_wait_for_turn / adventure_try_wait 的等待循环检测到后返回 -2
（python 已有 -2 → done 路径，且随后读 state.game_over 得正确胜负奖励）。

改动面（幂等 + 备份 .bak_mlgo）:
  1) ML/strategic_state.cpp   — force atomic + 两个 wait 检查 + 两处 update 覆盖
  2) ML/strategic_state.h     — 声明
  3) client/NetPacksClient.cpp— visitPlayerEndsGame 开头调用
注意: 仅改 ML/ 副本（python 实际加载的 libmlclient 版本）；server/ 副本已与 ML/ 分叉且 stale，不动。
"""
import os
import shutil
import sys

ROOT = "/home/administrator/vcmi-native"
CPP = os.path.join(ROOT, "ML/strategic_state.cpp")
H = os.path.join(ROOT, "ML/strategic_state.h")
NPC = os.path.join(ROOT, "client/NetPacksClient.cpp")
BAK = ".bak_mlgo"

SP4 = "    "


def patch(path, pairs):
    src = open(path, encoding="utf-8").read()
    if not os.path.exists(path + BAK):
        shutil.copy2(path, path + BAK)
        os.utime(path, None)
    changed = 0
    for old, new in pairs:
        if new in src:
            changed += 1
            continue
        if old not in src:
            print("  anchor miss in %s: %r..." % (path, old[:60]), file=sys.stderr)
            return 0
        src = src.replace(old, new, 1)
        changed += 1
    open(path, "w", encoding="utf-8").write(src)
    return changed


def main():
    ok = True

    # ---- 1. ML/strategic_state.cpp ----
    pairs_cpp = [
        # atomic 声明
        ("static std::atomic<int> s_turn_player{-1};",
         "static std::atomic<int> s_force_game_over{-1};  // ML fix (09-24): PlayerEndsGame 强制终局\n"
         "static std::atomic<int> s_turn_player{-1};"),
        # try_wait 开头检查
        ('extern "C" int adventure_try_wait() {\n'
         "    int p = s_turn_player.load(std::memory_order_acquire);",
         'extern "C" int adventure_try_wait() {\n'
         "    // ML fix (09-24): 终局强制置位后立即返回 -2 (done 路径)\n"
         "    if (s_force_game_over.load(std::memory_order_acquire) >= 0) return -2;\n"
         "    int p = s_turn_player.load(std::memory_order_acquire);"),
        # wait_for_turn 循环内检查
        ("        if (p >= 0 && gen != s_last_waited_gen) break;  // new generation only: stale s_turn_player=0 must not fire\n"
         "        std::this_thread::sleep_for(std::chrono::milliseconds(10));",
         "        if (p >= 0 && gen != s_last_waited_gen) break;  // new generation only: stale s_turn_player=0 must not fire\n"
         "        // ML fix (09-24): 终局后 yourTurn 不再来, 检测到强制置位立即退出等待 (-2 → done)\n"
         "        if (s_force_game_over.load(std::memory_order_acquire) >= 0) return -2;\n"
         "        std::this_thread::sleep_for(std::chrono::milliseconds(10));"),
        # update 覆盖（引用版）
        ("        if (alive_count <= 1 && state.player_count > 1)\n"
         "            state.game_over = last_alive + 1;",
         "        if (alive_count <= 1 && state.player_count > 1)\n"
         "            state.game_over = last_alive + 1;\n"
         "        // ML fix (09-24): 强制终局优先于 alive 推导 (胜利后 update 可能不再触发)\n"
         "        if (s_force_game_over.load(std::memory_order_acquire) >= 0)\n"
         "            state.game_over = s_force_game_over.load(std::memory_order_acquire) + 1;"),
        # update 覆盖（指针版）
        ("        if (alive_count <= 1 && state->player_count > 1)\n"
         "            state->game_over = last_alive + 1;",
         "        if (alive_count <= 1 && state->player_count > 1)\n"
         "            state->game_over = last_alive + 1;\n"
         "        // ML fix (09-24): 强制终局优先 (同引用版)\n"
         "        if (s_force_game_over.load(std::memory_order_acquire) >= 0)\n"
         "            state->game_over = s_force_game_over.load(std::memory_order_acquire) + 1;"),
        # force 函数定义（挂在 try_wait 前）
        ('extern "C" int adventure_try_wait() {',
         "// ML fix (09-24): 终局强制置位 — 由 client 侧 visitPlayerEndsGame 调用\n"
         'extern "C" void strategic_state_force_game_over(int winner_player) {\n'
         "    s_force_game_over.store(winner_player, std::memory_order_release);\n"
         "    fprintf(stderr, \"[ML-fix] force game_over: winner=%d\\n\", winner_player);\n"
         "}\n\n"
         'extern "C" int adventure_try_wait() {'),
    ]
    n = patch(CPP, pairs_cpp)
    print("ML/strategic_state.cpp: %d/%d" % (n, len(pairs_cpp)))
    ok = ok and (n == len(pairs_cpp))

    # ---- 2. ML/strategic_state.h ----
    pairs_h = [
        ('extern "C" int  adventure_try_wait();',
         'extern "C" int  adventure_try_wait();\n'
         'extern "C" void strategic_state_force_game_over(int winner_player);  // ML fix (09-24)'),
    ]
    n = patch(H, pairs_h)
    print("ML/strategic_state.h: %d/%d" % (n, len(pairs_h)))
    ok = ok and (n == len(pairs_h))

    # ---- 3. client/NetPacksClient.cpp ----
    pairs_npc = [
        ("void ApplyClientNetPackVisitor::visitPlayerEndsGame(PlayerEndsGame & pack)\n"
         "{",
         'extern "C" void strategic_state_force_game_over(int winner_player);  // ML fix: ML/strategic_state\n\n'
         "void ApplyClientNetPackVisitor::visitPlayerEndsGame(PlayerEndsGame & pack)\n"
         "{\n"
         "    // ML fix (09-24): 胜负判定后 yourTurn 不再回调 → NK2/connector 永久等。\n"
         "    // 立即强制置位 game_over, 唤醒 adventure_wait_* 返回 -2 (connector 按game_over结算)。\n"
         "    // 1v1 口径: player 0=RED 1=BLUE; victory 时赢家=pack.player, 否则=对手。\n"
         "    {\n"
         "        const int p = pack.player.getNum();\n"
         "        const int winner = pack.victoryLossCheckResult.victory() ? p : (1 - p);\n"
         "        if (p == 0 || p == 1)\n"
         "            strategic_state_force_game_over(winner);\n"
         "    }"),
    ]
    n = patch(NPC, pairs_npc)
    print("client/NetPacksClient.cpp: %d/%d" % (n, len(pairs_npc)))
    ok = ok and (n == len(pairs_npc))

    print("结论:", "全部锚点命中" if ok else "有锚点未命中 — 人工核对", file=sys.stderr if not ok else sys.stdout)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())