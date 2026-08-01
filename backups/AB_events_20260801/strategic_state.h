// strategic_state.h — VCMI 冒险地图状态，C 结构体，Python ctypes 直读
// 放在 vcmi/ML/ 下，和 MLClient.h 同级

#pragma once
#include <cstdint>

#define MAX_HEROES  8
#define MAX_TOWNS   8
#define MAX_PLAYERS 8

#define LOCAL_WIN     15
#define GLOBAL_GRID   32
#define MAX_LEVELS    2

// 单个英雄
struct StrategicHero {
    int32_t id;
    int32_t owner;          // 0-7
    int32_t pos_x;
    int32_t pos_y;
    int32_t pos_z;          // 0=地表 1=地下
    int32_t movement;       // 剩余移动力
    int32_t max_movement;
    int32_t level;
    int32_t attack;
    int32_t defense;
    int32_t power;
    int32_t knowledge;
    int32_t mana;
    int32_t max_mana;
    int32_t exp;
    int32_t army_count[7];  // 7格兵力
    int32_t army_type[7];   // 兵种ID
    int32_t in_battle;      // 0=正常 1=战斗中
    char    name[32];
};

// 单个城镇
struct StrategicTown {
    int32_t id;
    int32_t owner;
    int32_t pos_x;
    int32_t pos_y;
    int32_t pos_z;
    int32_t buildings;      // 建筑位掩码
    int32_t garrison[7];    // 驻兵数量
    int32_t gold_income;    // 日收入
    char    name[32];
};

// 单个玩家
struct StrategicPlayer {
    int32_t color;          // 0-7
    int32_t human;          // 0=AI 1=人类
    int32_t gold;
    int32_t wood;
    int32_t mercury;
    int32_t ore;
    int32_t sulfur;
    int32_t crystal;
    int32_t gems;
    int32_t hero_count;
    int32_t town_count;
    int32_t alive;          // 0=淘汰
};

// 全局状态 — 一个 4KB 以内的平面结构体
struct StrategicState {
    int32_t day;
    int32_t week;
    int32_t month;
    int32_t current_player; // 当前回合玩家ID
    int32_t map_width;
    int32_t map_height;
    int32_t has_underground; // 0=单层 1=双层
    int32_t player_count;

    StrategicPlayer players[MAX_PLAYERS];
    StrategicHero   heroes[MAX_HEROES];
    StrategicTown   towns[MAX_TOWNS];

    int32_t game_over;      // 0=进行中 1=红赢 2=蓝赢

    int32_t action;         // Python 写入的 RL 动作，C++ yourTurn 据此移动英雄
    int32_t _version;       // 结构体版本号，防 ABI 错位
    int32_t passable[8];    // 当前玩家英雄8方向可通行性 (0=不可走, 1=可走)

    // ===== B 态势感知扩展 (v2) =====
    int32_t active_hero;    // 当前活动英雄在 heroes[] 中的索引, -1=无
    int8_t  local_tiles[LOCAL_WIN][LOCAL_WIN];               // 15×15=225, active hero 所在层局部探索窗口
    int8_t  global_explored[MAX_LEVELS][GLOBAL_GRID][GLOBAL_GRID]; // 2×32×32=2048 全图下采样探索图 (z 外层, 与 ctypes [z][gy][gx] 对齐)
};

// Python 写入的 RL 动作（不放在 StrategicState 内，避免改变 struct 尺寸导致 ABI 错位）
extern "C" {
    extern int32_t g_rl_action;
}

extern "C" {
    extern StrategicState* g_strategic_state;
}

// 冒险地图 yourTurn 回调 — connector 设置此指针，AAI::yourTurn() 调用
typedef void (*AdventureYourTurnCallback)(int playerColor, void* userData);
extern AdventureYourTurnCallback g_adventure_cb;
extern void* g_adventure_cb_userdata;

// 更新战略状态 — 从 VCMI CGameState 填充 StrategicState 结构体
extern "C" void strategic_state_update(void* game_state_ptr);

// 冒险回合处理 — AAI::yourTurn() 直接调用，不走函数指针（避开跨 .so 崩溃）
extern "C" void adventure_process_turn(int playerColor, void* userData);
extern "C" void adventure_send_action(int action);
extern "C" void adventure_capture_turn(int playerColor, void* userData, int action);
extern "C" void adventure_capture_noblock(int playerColor, void* userData, int action);
extern "C" int  adventure_try_wait();
extern "C" int  adventure_get_action();
