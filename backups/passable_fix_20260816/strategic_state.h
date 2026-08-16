// strategic_state.h — VCMI 冒险地图状态，C 结构体，Python ctypes 直读
// 放在 vcmi/ML/ 下，和 MLClient.h 同级

#pragma once
#include <cstdint>

#define MAX_HEROES  8
#define MAX_TOWNS   8
#define MAX_PLAYERS 8

#define LOCAL_WIN     15
#define LOCAL_CH      3   // v3: 0=可通行性 1=对象类型 2=守卫战力
#define GLOBAL_GRID   32
#define MAX_LEVELS    2

#define NAV_SIZE      32
#define TARGET_LIST   8   // 目标槽数
#define TARGET_DIM    8   // 每目标维度 (type,idx,x,y,z,dist,power,flags)
#define ENEMY_THREAT  7   // 敌方玩家数 (排除自己)
#define BATTLE_PRED   4
#define EVENTS_SIZE   4
#define RESERVED_SIZE 134

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
    // ===== v3 扩展 =====
    int32_t total_power;    // 该英雄总战力 (army × getAIValue 求和)
    int32_t is_garrisoned;  // 0=野外 1=驻守城镇中
    int32_t has_commander;  // 0=无 1=有指挥官
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
    // ===== v3 扩展 =====
    int32_t recruit_mask_lo;  // 可招募兵种 bitmask 低16位
    int32_t recruit_mask_hi;  // 可招募兵种 bitmask 高16位
    int32_t build_mask_lo;    // 可建建筑 bitmask 低16位
    int32_t build_mask_hi;    // 可建建筑 bitmask 高16位
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
    // ===== v3 扩展 =====
    int32_t total_power;    // 该玩家总战力 (所有英雄 army×AIValue 求和)
    int32_t weekly_income;  // 金币周收入
    int32_t relation_to_me; // 0=中立 1=敌对 2=结盟 (多人联网用)
};

// 单个矿 (C 事件奖励: Python 比较 owner 变化 → 占矿奖励)
#define MAX_MINES 64

struct StrategicMine {
    int32_t id;      // 地图对象 id (CGObjectInstance::id)
    int32_t type;    // 矿类型 subID: 1=锯木厂 2=水银 3=铁矿 4=硫磺 5=水晶 6=宝石 7=金矿, 0=未知
    int32_t owner;   // -1=中立, 0-7=玩家
    int32_t pos_x;
    int32_t pos_y;
    int32_t pos_z;
};

// 全局状态 — 平面结构体 (v3: obs 3456 维)
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
    int32_t _version;       // 结构体版本号，防 ABI 错位 (v3)
    int32_t passable[8];    // 当前玩家英雄8方向可通行性 (0=不可走, 1=可走)

    // ===== B 态势感知扩展 (v2) =====
    int32_t active_hero;    // 当前活动英雄在 heroes[] 中的索引, -1=无
    int8_t  local_tiles[LOCAL_CH][LOCAL_WIN][LOCAL_WIN]; // v3: 3通道 15×15 (ch 外层, 与 ctypes [ch][y][x] 对齐)
    int8_t  global_explored[MAX_LEVELS][GLOBAL_GRID][GLOBAL_GRID]; // 2×32×32=2048 全图下采样探索图 (z 外层)

    // ===== C 事件奖励扩展 =====
    int32_t mine_count;              // 有效矿数 (0-64)
    StrategicMine mines[MAX_MINES];  // 矿归属表
    int32_t battle_result;           // 0=无 1=red赢 2=red输 3=平局 (ServerPlugin endBattleHook 写入)

    // ===== H 动作空间扩展 (v3, obs 3456) =====
    int32_t nav[NAV_SIZE];                              // 邻接/导航上下文 (32)
    int32_t target_list[TARGET_LIST][TARGET_DIM];       // 可选目标列表 (8×8): type,idx,x,y,z,dist,power,flags
    int32_t enemy_threat[ENEMY_THREAT];                 // 每敌方玩家总战力 (7)
    int32_t battle_pred[BATTLE_PRED];                   // 战斗预测 (4): my_power,target_power,win_prob,reserved
    int32_t events[EVENTS_SIZE];                        // 事件 (4): week_type,last_action_result,last_reward,reserved
    int32_t reserved[RESERVED_SIZE];                    // 统一预留 (134), 全 0 占位
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
extern "C" void adventure_cb_trampoline(int playerColor, void* userData);
extern "C" void register_adventure_delegate(void (*delegate)(int, void*), void* userdata);
