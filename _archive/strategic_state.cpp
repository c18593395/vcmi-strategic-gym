// strategic_state.cpp — 全局指针 + 填充函数
// 放到 vcmi/ML/ 下编译进 libmlclient.so

#include "StdInc.h"
#include "strategic_state.h"
#include "gameState/CGameState.h"
#include "CPlayerState.h"
#include "ResourceSet.h"
#include <cstring>

// 全局指针 — VCMI 每帧更新，Python ctypes 读取
extern "C" {
    StrategicState* g_strategic_state = nullptr;
}

// VCMI 冒险地图 AI 的 getAction 回调中调用此函数填充状态
// 参数：指向 CGameState 的指针（VCMI 内部类型，C++ 侧有完整访问）
void strategic_state_update(void* game_state_ptr) {
    if (!g_strategic_state) return;

    auto& gs = *static_cast<CGameState*>(game_state_ptr);
    auto& state = *g_strategic_state;

    // 基础信息
    state.day = gs.day;
    // week/month 从 day 推算
    state.week = (gs.day - 1) / 7 + 1;
    state.month = (gs.day - 1) / 28 + 1;
    state.current_player = 0;
    if (!gs.actingPlayers.empty())
        state.current_player = static_cast<int32_t>(gs.actingPlayers.begin()->getNum());

    // 地图 (CMap forward-declared, skip geometry)
    state.map_width = 0;
    state.map_height = 0;
    state.has_underground = 0;

    // 玩家
    state.player_count = 0;
    for (auto& [color, ps] : gs.players) {
        if (state.player_count >= MAX_PLAYERS) break;
        auto& p = state.players[state.player_count++];
        p.color = color.getNum();
        p.human = ps.human ? 1 : 0;
        p.gold = ps.resources[EGameResID::GOLD];
        p.wood = ps.resources[EGameResID::WOOD];
        p.mercury = ps.resources[EGameResID::MERCURY];
        p.ore = ps.resources[EGameResID::ORE];
        p.sulfur = ps.resources[EGameResID::SULFUR];
        p.crystal = ps.resources[EGameResID::CRYSTAL];
        p.gems = ps.resources[EGameResID::GEMS];
        p.hero_count = 0;
        p.town_count = 0;
        p.alive = (ps.status == EPlayerStatus::INGAME) ? 1 : 0;
    }

    // 英雄和城镇 — 后续在完整游戏上下文中补充
    // (PlayerState::getObjectsOfType 模板仅声明，需 CGameState 完整上下文)
    state.heroes[0].id = -1; // sentinel

    // 检测游戏结束
    state.game_over = 0;
    int alive_count = 0, last_alive = -1;
    for (int p = 0; p < state.player_count; p++) {
        if (state.players[p].alive) {
            alive_count++;
            last_alive = p;
        }
    }
    if (alive_count <= 1 && state.player_count > 1)
        state.game_over = last_alive + 1; // 1=红赢 2=蓝赢
}
