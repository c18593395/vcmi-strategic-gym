// strategic_state.h — VCMI 冒险地图状态，C 结构体，Python ctypes 直读
// 放在 vcmi/ML/ 下，和 MLClient.h 同级

#pragma once
#include <cstdint>

#define MAX_HEROES  8
#define MAX_TOWNS   8
#define MAX_PLAYERS 8

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

    int32_t _version;       // 结构体版本号，防 ABI 错位
};

// 全局指针声明 — 其他 .cpp 文件 include 此头文件后可访问
extern "C" {
    extern StrategicState* g_strategic_state;
}
