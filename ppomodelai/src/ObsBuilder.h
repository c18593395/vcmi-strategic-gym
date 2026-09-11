#pragma once

#include <array>
#include <cstdint>
#include <vector>

// 3464 obs 布局常量 — 与 vcmi_gym/envs/v13/strategic_env.py 权威实现一致 (OBS schema v3)
#define MB_MAX_HEROES   8
#define MB_MAX_TOWNS    8
#define MB_MAX_PLAYERS  8
#define MB_LOCAL_WIN    15
#define MB_LOCAL_CH     3
#define MB_GLOBAL_GRID  32
#define MB_MAX_LEVELS   2
#define MB_TARGET_LIST  8
#define MB_TARGET_DIM   8
#define MB_ENEMY_THREAT 7
#define MB_BATTLE_PRED  4
#define MB_EVENTS_SIZE  4
#define MB_RESERVED     134
#define MB_GRID_SIZE    21
#define MB_GRID_CH      4
#define MB_GRID_TOTAL   (MB_GRID_SIZE * MB_GRID_SIZE * MB_GRID_CH)  // 1764
#define MB_OBS_DIM      3464
#define MB_TERRAIN_FLOAT (MB_GRID_SIZE * MB_GRID_SIZE * MB_GRID_CH)  // 1764 (CHW float)

// StrategicState 精简副本 — 字段与 vcmi/ML/strategic_state.h 完全一致 (名称对齐 Python ctypes)。
// 独立副本避免链接 ML 符号 (g_strategic_state 等); ModelAI 不走全局指针, 每回合栈上构造。
struct MBPlayer {
    int32_t color, human, gold, wood, mercury, ore, sulfur, crystal, gems;
    int32_t hero_count, town_count, alive;
    int32_t total_power, weekly_income, relation_to_me;
};

struct MBHero {
    int32_t id, owner, pos_x, pos_y, pos_z;
    int32_t movement, max_movement, level, attack, defense, power, knowledge;
    int32_t mana, max_mana, exp;
    int32_t army_count[7];
    int32_t in_battle;
    int32_t total_power, is_garrisoned, has_commander;
};

struct MBTown {
    int32_t id, owner, pos_x, pos_y, pos_z, buildings;
    int32_t garrison[7];
    int32_t gold_income;
    int32_t recruit_mask_lo, recruit_mask_hi, build_mask_lo, build_mask_hi;
};

struct MBState {
    int32_t day, week, month, current_player;
    int32_t map_width, map_height, has_underground, player_count;

    MBPlayer players[MB_MAX_PLAYERS];
    MBHero   heroes[MB_MAX_HEROES];
    MBTown   towns[MB_MAX_TOWNS];

    int32_t passable[8];
    int32_t active_hero;  // -1=无
    int8_t  local_tiles[MB_LOCAL_CH][MB_LOCAL_WIN][MB_LOCAL_WIN];
    int8_t  global_explored[MB_MAX_LEVELS][MB_GLOBAL_GRID][MB_GLOBAL_GRID];

    int32_t target_list[MB_TARGET_LIST][MB_TARGET_DIM];
    int32_t enemy_threat[MB_ENEMY_THREAT];
    int32_t battle_pred[MB_BATTLE_PRED];
    int32_t events[MB_EVENTS_SIZE];
    int32_t reserved[MB_RESERVED];

    uint8_t terrain_grid_hwc[MB_GRID_TOTAL];  // HWC uint8 (fill 产出)
};

class ObsBuilder {
public:
    // 填充 StrategicState (移植 ML/strategic_state.cpp fill 函数族, 参数化 selfPlayer)
    // activeHeroId: 当前英雄的 ObjectInstanceID 全局 id (PpoModelAI 维护, 支持 NEXT_HERO 切换);
    //   <0 或无效时自动选第一个己方英雄; 无己方英雄时 st.active_hero=-1 (调用方需防护)
    static void fillState(class CCallback* cb, int selfPlayer, int activeHeroId, MBState& st);
    // 展平为 3464 obs (移植 strategic_env.py::_strategic_state_to_obs + H.8 归一化)
    static std::array<float, MB_OBS_DIM> flatten(const MBState& st);
    // terrain_grid HWC uint8 -> CHW float /255 (训练侧 _build_terrain_grid 同变换)
    static std::array<float, MB_TERRAIN_FLOAT> terrainCHW(const MBState& st);
};
