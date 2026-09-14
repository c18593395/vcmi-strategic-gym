#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H3 patch ②: ML/strategic_state.cpp
  (a) adventure_process_turn 持久化 g_ml_player_cb = userData
  (b) adventure_wait_for_turn 增加游戏结束轮询: 红方 status!=INGAME 或 alive<=1 → 刷终局快照 → 返回 -2
目标: /home/administrator/vcmi-native/ML/strategic_state.cpp (4 空格缩进)

注意: .so 编译自 vcmi-native/ML 源码树, 改动落 vcmi-native 而非 vcmi-native-build。
"""
import sys

F = "/home/administrator/vcmi-native/ML/strategic_state.cpp"
src = open(F, encoding="utf-8").read()
applied = 0

# ---- (a) adventure_process_turn: 持久化 g_ml_player_cb ----
old_a = """    void* cbPtr = userData ? userData : g_ml_player_cb;
    if (cbPtr) fill_strategic_state(cbPtr);

    if (s_capture_mode.load(std::memory_order_acquire))"""
new_a = """    // ML H3 fix (2026-09-14): 持久化回调指针, 供 adventure_wait_for_turn 终局轮询时
    // 在红方败北 (yourTurn 不再回调) 后仍能刷新终局快照。
    if (userData) g_ml_player_cb = userData;
    void* cbPtr = userData ? userData : g_ml_player_cb;
    if (cbPtr) fill_strategic_state(cbPtr);

    if (s_capture_mode.load(std::memory_order_acquire))"""
if old_a in src:
    src = src.replace(old_a, new_a, 1)
    applied += 1
    print("patched (a) adventure_process_turn: persist g_ml_player_cb")
elif "if (userData) g_ml_player_cb = userData;" in src:
    print("(a) already patched, skip")
else:
    print("ERROR: block (a) not found. Current region:")
    i = src.find('extern "C" void adventure_process_turn')
    print(src[i:i+600])
    sys.exit(1)

# ---- (b) adventure_wait_for_turn: 游戏结束轮询 → 返回 -2 ----
old_b = """extern "C" int adventure_wait_for_turn() {
    int spins = 0;
    while (true) {
        int gen = s_turn_generation.load(std::memory_order_acquire);
        int p = s_turn_player.load(std::memory_order_acquire);
        if (p >= 0 && gen != s_last_waited_gen) break;  // new generation only: stale s_turn_player=0 must not fire
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        spins++;
    }
    int p = s_turn_player.load(std::memory_order_acquire);
    s_turn_player.store(-1, std::memory_order_release);
    s_last_waited_gen = s_turn_generation.load(std::memory_order_acquire);
    return p;
}"""
new_b = """extern "C" int adventure_wait_for_turn() {
    int spins = 0;
    while (true) {
        int gen = s_turn_generation.load(std::memory_order_acquire);
        int p = s_turn_player.load(std::memory_order_acquire);
        if (p >= 0 && gen != s_last_waited_gen) break;  // new generation only: stale s_turn_player=0 must not fire
        // ML H3 fix (2026-09-14): 终局通道 — 红方真败 (无将无城) 后引擎不再回调 yourTurn,
        // s_turn_generation 永久停住 → 旧逻辑在此白烧 300s Python 超时。
        // 轮询 gs.players (全知直读, shared_lock 同 fill 模式): 跳过 NEUTRAL, 存活玩家 <=1
        // 即终局 → 刷终局快照 (game_over=last_alive+1) → 返回 -2, Python 侧识别走 READ 路径。
        if (spins % 25 == 0 && g_ml_player_cb) {
            auto* pscb = static_cast<CPlayerSpecificInfoCallback*>(g_ml_player_cb);
            auto* gicb = static_cast<CGameInfoCallback*>(pscb);
            {
                const auto& gs = gicb->gameState();
                std::shared_lock gsLock(CGameState::mutex);
                int alive = 0;
                for (const auto& [color, ps] : gs.players) {
                    if (color == PlayerColor::NEUTRAL) continue;
                    if (ps.status == EPlayerStatus::INGAME) alive++;
                }
                if (alive <= 1) {
                    gsLock.unlock();
                    fill_strategic_state(g_ml_player_cb);
                    s_last_waited_gen = s_turn_generation.load(std::memory_order_acquire);
                    return -2;  // terminal: Python _adventure_wait → READ → game_over=2 → -200
                }
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        spins++;
    }
    int p = s_turn_player.load(std::memory_order_acquire);
    s_turn_player.store(-1, std::memory_order_release);
    s_last_waited_gen = s_turn_generation.load(std::memory_order_acquire);
    return p;
}"""
if old_b in src:
    src = src.replace(old_b, new_b, 1)
    applied += 1
    print("patched (b) adventure_wait_for_turn: terminal poll → -2")
elif "terminal: Python _adventure_wait" in src:
    print("(b) already patched, skip")
else:
    print("ERROR: block (b) not found. Current region:")
    i = src.find('extern "C" int adventure_wait_for_turn')
    print(src[i:i+600])
    sys.exit(1)

open(F, "w", encoding="utf-8").write(src)
chk = open(F, encoding="utf-8").read()
assert "if (userData) g_ml_player_cb = userData;" in chk, "(a) missing"
assert "terminal: Python _adventure_wait" in chk, "(b) missing"
assert "spins % 25 == 0" in chk, "poll missing"
print(f"verified OK, applied={applied}/2")
