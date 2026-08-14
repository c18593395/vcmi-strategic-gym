// strategic_state.cpp — 全局指针 + 填充函数
// 放到 vcmi/ML/ 下编译进 libmlclient.so

#include "StdInc.h"
#include "strategic_state.h"
#include "callback/CGameInfoCallback.h"
#include "callback/CPlayerSpecificInfoCallback.h"
#include "gameState/CGameState.h"
#include "mapping/CMap.h"
#include "mapObjects/CGObjectInstance.h"
#include "mapObjects/CGHeroInstance.h"
#include "mapObjects/CGTownInstance.h"
#include "mapObjects/CGCreature.h"
#include "constants/EntityIdentifiers.h"
#include "CPlayerState.h"
#include "ResourceSet.h"
#include <cstring>
#include <atomic>
#include <thread>
#include <chrono>
#include <algorithm>
#include <shared_mutex>
#include <cmath>

// 全局指针 — VCMI 每帧更新，Python ctypes 读取
extern "C" {
    StrategicState* g_strategic_state = nullptr;
}

// Python 写入的 RL 动作 (头文件声明 extern, 定义必须在此)
extern "C" {
    int32_t g_rl_action = 0;
}

// 跨 .so 共享的 active hero 全局变量（AAI.cpp 写，本文件读）
extern "C" {
    int32_t g_active_hero = 0;
}

// Allocate state on library load — ensures Python can always read it
// regardless of which path calls adventure_process_turn.
__attribute__((constructor))
static void init_strategic_state() {
    if (!g_strategic_state) {
        g_strategic_state = new StrategicState();
        memset(g_strategic_state, 0, sizeof(StrategicState));
        g_strategic_state->_version = 3;
        for (int d = 0; d < 8; d++)
            g_strategic_state->passable[d] = 1;
    }
}

AdventureYourTurnCallback g_adventure_cb = nullptr;
void* g_adventure_cb_userdata = nullptr;
// 由 AAI::yourTurn 设置的全局 CCallback 指针（跨 .so 可见）
extern "C" void* g_ml_player_cb = nullptr;

// H.4 修复: 全知直读英雄战力 (army × getAIValue 求和)
static int64_t hero_total_power(const CGHeroInstance* hero) {
    int64_t power = 0;
    if (!hero) return 0;
    for (int ai = 0; ai < 7; ai++) {
        auto* stack = hero->getStackPtr(SlotID(ai));
        if (!stack) continue;
        int count = stack->getCount();
        if (count <= 0) continue;
        auto creature = stack->getCreatureID().toCreature();
        if (creature)
            power += (int64_t)creature->getAIValue() * count;
    }
    return power;
}

// H.4 修复: 英雄是否驻守 (在任一城镇 garrison 或 visiting)
static bool hero_is_garrisoned(const CGameState& gs, const CGHeroInstance* hero) {
    if (!hero) return false;
    ObjectInstanceID hid = hero->id;
    for (const auto& [color, ps] : gs.players) {
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            const auto* gh = town->getGarrisonHero();
            const auto* vh = town->getVisitingHero();
            if ((gh && gh->id == hid) || (vh && vh->id == hid))
                return true;
        }
    }
    return false;
}

// B 态势感知: 填充 active_hero + local_tiles + global_explored
// 探索状态读取: CGameState 的 fogOfWarMap (TeamState, 1=visible/explored, 0=hidden)
static void fill_exploration(StrategicState* state, CGameState& gs) {
    // 锁由调用方 fill_strategic_state 持有 (fillLock), 此处不再加锁 (shared_mutex 非递归, 同线程重复加锁会死锁)
    // active_hero: g_active_hero 越界/无效时回退 0
    int32_t ah = g_active_hero;
    if (ah < 0 || ah >= MAX_HEROES || state->heroes[ah].id < 0)
        ah = 0;
    state->active_hero = ah;

    // 全零初始化 (新字段在 memset 中已为 0, 此处显式清零)
    memset(state->local_tiles, 0, sizeof(state->local_tiles));
    memset(state->global_explored, 0, sizeof(state->global_explored));

    auto& map = gs.getMap();
    int mw = (int)map.width, mh = (int)map.height;
    if (mw <= 0 || mh <= 0) return;

    const auto* team = gs.getPlayerTeam(PlayerColor(0));
    if (!team) return;  // 无队伍数据, 保持全 0

    // local_tiles: active hero 所在层 15×15 窗口, 3 通道 (0=可通行性 1=对象类型 2=守卫战力)
    if (state->heroes[ah].id >= 0) {
        int cx = state->heroes[ah].pos_x;
        int cy = state->heroes[ah].pos_y;
        int cz = state->heroes[ah].pos_z;
        const auto& from_tile = map.getTile(int3(cx, cy, cz));  // isClear 需要 from (VCMI 实现 nullptr 会崩)
        for (int dy = -7; dy <= 7; dy++) {
            for (int dx = -7; dx <= 7; dx++) {
                int x = cx + dx, y = cy + dy;
                int8_t v = 0, objt = 0, guard = 0;
                if (x >= 0 && x < mw && y >= 0 && y < mh) {
                    int3 pos(x, y, cz);
                    if (team->fogOfWarMap[pos]) {  // 已探索
                        const auto& tile = map.getTile(pos);
                        v = (tile.getTerrain()->isPassable() && !(tile.blocked() && !tile.visitable())) ? 1 : 2;
                        // 通道1: 顶对象类型 (Obj 枚举值, 0=无)
                        // TODO(debug): getObject 暂停排查崩溃
                        /* ObjectInstanceID top = tile.topVisitableObj(false);
                        if (top != ObjectInstanceID::NONE) {
                            const auto* obj = map.getObject(top);
                            if (obj) objt = (int8_t)obj->ID.getNum();
                        } */
                        // 通道2: 守卫战力 (0=无守卫, >0=守卫怪 AIValue/1000 粗略编码)
                        // TODO(debug): guardingCreatures 暂停排查崩溃
                        /* auto guards = gs.guardingCreatures(pos);
                        if (!guards.empty()) {
                            const auto* mon = dynamic_cast<const CGCreature*>(guards.front());
                            if (mon) {
                                auto cid = mon->getCreatureID();
                                if (cid.toCreature())
                                    guard = (int8_t)std::min<int64_t>(255, cid.toCreature()->getAIValue() / 1000);
                            }
                        } */
                    }
                }
                state->local_tiles[0][dy + 7][dx + 7] = v;
                state->local_tiles[1][dy + 7][dx + 7] = objt;
                state->local_tiles[2][dy + 7][dx + 7] = guard;
            }
        }
    }

    // global_explored: 全图下采样 32×32×2, 块内任一 tile 已探索则块=1
    int bw = (mw + GLOBAL_GRID - 1) / GLOBAL_GRID;  // ceil
    int bh = (mh + GLOBAL_GRID - 1) / GLOBAL_GRID;
    for (int z = 0; z < MAX_LEVELS && z < map.levels(); z++) {
        for (int gy = 0; gy < GLOBAL_GRID; gy++) {
            for (int gx = 0; gx < GLOBAL_GRID; gx++) {
                int x0 = gx * bw, y0 = gy * bh;
                int x1 = std::min(x0 + bw, mw), y1 = std::min(y0 + bh, mh);
                int8_t explored = 0;
                for (int y = y0; y < y1 && !explored; y++)
                    for (int x = x0; x < x1 && !explored; x++)
                        if (team->fogOfWarMap[int3(x, y, z)])
                            explored = 1;
                state->global_explored[z][gy][gx] = explored;
            }
        }
    }
}

// C 事件奖励: 填充矿归属表 mines[] — 遍历 CMap::objects 筛 Obj::MINE
// battle_result 不清零 (由 ServerPlugin endBattleHook 写入, fill 保留)
static void fill_mines(StrategicState* state, CGameState& gs) {
    // 锁由调用方持有 (fillLock), 此处不再加锁
    state->mine_count = 0;
    auto& map = gs.getMap();
    for (const auto& objPtr : map.objects) {
        if (!objPtr) continue;
        const auto* obj = objPtr.get();
        if (obj->ID != Obj::MINE) continue;   // Obj::MINE = 53
        if (state->mine_count >= MAX_MINES) break;
        auto& m = state->mines[state->mine_count++];
        m.id = obj->id.getNum();
        m.type = obj->subID.getNum();          // 1=锯木厂 ... 7=金矿
        int owner = obj->getOwner().getNum();  // PlayerColor::NEUTRAL=255
        m.owner = (owner >= 0 && owner < 8) ? owner : -1;  // -1=中立
        m.pos_x = obj->pos.x;
        m.pos_y = obj->pos.y;
        m.pos_z = obj->pos.z;
    }
}

// ===== H 扩展 (v3): 填充 v3 新字段 =====
// 前置: 调用方须已填充 players/heroes/towns 段
static void fill_v3_fields(StrategicState* state, CGameState& gs) {
    // 锁由调用方持有 (fillLock), 此处不再加锁

    // 1. 英雄战力/驻守/指挥官 + 玩家战力累加
    for (int i = 0; i < MAX_HEROES; i++) {
        auto& h = state->heroes[i];
        if (h.id < 0) continue;
        const auto* hero = dynamic_cast<const CGHeroInstance*>(gs.getMap().getObject(ObjectInstanceID(h.id)));
        h.total_power = hero ? (int32_t)hero_total_power(hero) : 0;
        h.is_garrisoned = hero ? (hero_is_garrisoned(gs, hero) ? 1 : 0) : 0;
        h.has_commander = hero && hero->getCommander() ? 1 : 0;
        // 累加到所属玩家
        if (h.owner >= 0 && h.owner < MAX_PLAYERS)
            state->players[h.owner].total_power += h.total_power;
    }

    // 2. 城镇: 招募 mask / 建造 mask / 玩家收入累加
    for (int i = 0; i < MAX_TOWNS; i++) {
        auto& t = state->towns[i];
        if (t.id < 0) continue;
        const auto* town = dynamic_cast<const CGTownInstance*>(gs.getMap().getObject(ObjectInstanceID(t.id)));
        if (!town) continue;
        const auto* townType = town->getTown();
        if (!townType) continue;

        // 招募 mask: DWELL_LVL_1..7 (30..36) + 升级版 (37..43)
        uint32_t rm_lo = 0, rm_hi = 0;
        for (int lvl = 1; lvl <= 7; lvl++) {
            BuildingID dwell(BuildingID::DWELL_LVL_1 + (lvl - 1));
            if (town->hasBuilt(dwell)) {
                if (lvl <= 16) rm_lo |= (1u << (lvl - 1));
                else rm_hi |= (1u << (lvl - 17));
            }
        }
        t.recruit_mask_lo = (int32_t)rm_lo;
        t.recruit_mask_hi = (int32_t)rm_hi;

        // 建造 mask: 未建的 DWELL/HALL/FORT/MAGE 建筑 (前 64 个, 位序=建筑枚举序)
        uint32_t bm_lo = 0, bm_hi = 0;
        int bi = 0;
        for (const auto& [bid, bptr] : townType->buildings) {
            if (!bptr) continue;
            int num = bid.getNum();
            if (num < 0) continue;
            if (!town->hasBuilt(bid)) {
                if (bi < 32) bm_lo |= (1u << bi);
                else if (bi < 64) bm_hi |= (1u << (bi - 32));
            }
            bi++;
        }
        t.build_mask_lo = (int32_t)bm_lo;
        t.build_mask_hi = (int32_t)bm_hi;

        // 玩家周收入累加 (gold_income 字段填充: 城镇等级×250 简化)
        int income = town->getTownLevel() * 250;
        t.gold_income = income;
        if (t.owner >= 0 && t.owner < MAX_PLAYERS)
            state->players[t.owner].weekly_income += income;
    }

    // 3. 玩家关系
    for (int i = 0; i < state->player_count; i++) {
        auto& p = state->players[i];
        if (p.color == 0) { p.relation_to_me = 2; continue; }  // 自己=结盟
        auto rel = gs.getPlayerRelations(PlayerColor(0), PlayerColor(p.color));
        p.relation_to_me = (rel == PlayerRelations::ALLIES) ? 2 : (rel == PlayerRelations::ENEMIES ? 1 : 0);
    }

    // 4. nav: 最近友方/敌方英雄, 最近城镇
    memset(state->nav, 0, sizeof(state->nav));
    int32_t ah = state->active_hero;
    if (ah >= 0 && ah < MAX_HEROES && state->heroes[ah].id >= 0) {
        auto& ahh = state->heroes[ah];
        int64_t best_f = -1, best_fd = 1 << 30, best_e = -1, best_ed = 1 << 30;
        for (int i = 0; i < MAX_HEROES; i++) {
            auto& h = state->heroes[i];
            if (h.id < 0 || i == ah) continue;
            int64_t d = std::abs((int64_t)h.pos_x - ahh.pos_x) + std::abs((int64_t)h.pos_y - ahh.pos_y);
            if (h.owner == 0) {
                if (d < best_fd) { best_fd = d; best_f = i; }
            } else {
                if (d < best_ed) { best_ed = d; best_e = i; }
            }
        }
        state->nav[0] = (int32_t)best_f; state->nav[1] = (int32_t)(best_f >= 0 ? best_fd : -1);
        state->nav[2] = (int32_t)best_e; state->nav[3] = (int32_t)(best_e >= 0 ? best_ed : -1);
        // 最近城镇
        int64_t best_t = -1, best_td = 1 << 30;
        for (int i = 0; i < MAX_TOWNS; i++) {
            auto& t = state->towns[i];
            if (t.id < 0) continue;
            int64_t d = std::abs((int64_t)t.pos_x - ahh.pos_x) + std::abs((int64_t)t.pos_y - ahh.pos_y);
            if (d < best_td) { best_td = d; best_t = i; }
        }
        state->nav[4] = (int32_t)best_t; state->nav[5] = (int32_t)(best_t >= 0 ? best_td : -1);
    }

    // 5. enemy_threat: 每敌方玩家总战力
    memset(state->enemy_threat, 0, sizeof(state->enemy_threat));
    int et = 0;
    for (int i = 0; i < state->player_count && et < ENEMY_THREAT; i++) {
        if (state->players[i].color != 0)
            state->enemy_threat[et++] = state->players[i].total_power;
    }

    // 6. battle_pred: 当前英雄战力 / 最近敌方战力 / 胜率估计
    memset(state->battle_pred, 0, sizeof(state->battle_pred));
    if (ah >= 0 && ah < MAX_HEROES && state->heroes[ah].id >= 0) {
        int64_t myp = state->heroes[ah].total_power;
        int64_t enp = 0;
        if (state->nav[2] >= 0) enp = state->heroes[state->nav[2]].total_power;
        state->battle_pred[0] = (int32_t)myp;
        state->battle_pred[1] = (int32_t)enp;
        if (myp + enp > 0)
            state->battle_pred[2] = (int32_t)(100.0 * myp / (myp + enp));
    }

    // 7. events: week_type (0=普通, 简化) — last_action_result/last_reward 由 Python 侧写
    state->events[0] = 0;
    state->events[1] = 0;
    state->events[2] = 0;

    // 8. target_list / reserved 保持 0 (v2 启用)
}

// 冒险回合处理 — 被 AAI::yourTurn 直接调用
static std::atomic<int> s_turn_player{-1};
static std::atomic<bool> s_turn_action_ready{false};
static std::atomic<int> s_turn_action{0};
static std::atomic<bool> s_capture_mode{false};
static std::atomic<int> s_capture_action{0};

static void fill_strategic_state(void* cbPtr) {

        auto *pscb = static_cast<CPlayerSpecificInfoCallback*>(cbPtr);
        auto *gicb = static_cast<CGameInfoCallback*>(pscb);
        auto* state = g_strategic_state;

        // H.4 修复: 从 CGameState 全知直读 (绕过 CGameInfoCallback::getHeroes 的 isVisibleFor 过滤)
        // 训练期全知视角 (部署期用 isVisibleFor 掩码, 见部署映射设计.md)
        // C8.4 教训: 无锁直读 gs.players 与 NK2 规划线程数据竞争 → NK2 决策损坏 → 死循环!
        // 因此主体加 shared_lock (与 fill_exploration/fill_mines 同模式, 读锁可并发)
        const auto& gs = gicb->gameState();
        std::shared_lock fillLock(CGameState::mutex);

        // Players — 全知直读
        state->player_count = 0;
        for (const auto& [color, ps] : gs.players) {
            if (state->player_count >= MAX_PLAYERS) break;
            int pi = color.getNum();
            auto& p = state->players[state->player_count++];
            p.color = pi;
            p.human = ps.human ? 1 : 0;
            p.gold     = ps.resources[EGameResID::GOLD];
            p.wood     = ps.resources[EGameResID::WOOD];
            p.mercury  = ps.resources[EGameResID::MERCURY];
            p.ore      = ps.resources[EGameResID::ORE];
            p.sulfur   = ps.resources[EGameResID::SULFUR];
            p.crystal  = ps.resources[EGameResID::CRYSTAL];
            p.gems     = ps.resources[EGameResID::GEMS];
            p.hero_count = (int)ps.getHeroes().size();
            p.town_count = (int)ps.getTowns().size();
            p.alive = (ps.status == EPlayerStatus::INGAME) ? 1 : 0;
            p.total_power = 0;   // fill_v3_fields 累加
            p.weekly_income = 0;
            p.relation_to_me = 0;
        }
        // Calendar info (day/week/month)
        {
            state->day = static_cast<int32_t>(gs.day);
            state->week = (gs.day - 1) / 7 + 1;
            state->month = (gs.day - 1) / 28 + 1;
        }

        // Map dimensions
        {
            int3 mapSize = gicb->getMapSize();
            state->map_width = mapSize.x;
            state->map_height = mapSize.y;
            state->has_underground = mapSize.z > 1 ? 1 : 0;
        }

        state->current_player = 0;

        // Heroes — 全知直读 (H.4 修复核心: 不再走 gicb->getHeroes, 直接遍历 gs.players)
        // 在 fillLock 保护下直读 (C8.4 数据竞争教训)
        for (int i = 0; i < MAX_HEROES; i++) state->heroes[i].id = -1;
        int hi = 0;
        for (const auto& [color, ps] : gs.players) {
            int pi = color.getNum();
            for (const auto* hero : ps.getHeroes()) {
                if (hi >= MAX_HEROES) break;
                auto& h = state->heroes[hi++];
                h.id = hero->id.getNum();
                h.owner = pi;
                h.pos_x = hero->pos.x;
                h.pos_y = hero->pos.y;
                h.pos_z = hero->pos.z;
                h.movement = hero->movementPointsRemaining();
                h.max_movement = hero->movementPointsLimit();
                h.level = hero->level;
                h.attack = hero->getPrimSkillLevel(PrimarySkill::ATTACK);
                h.defense = hero->getPrimSkillLevel(PrimarySkill::DEFENSE);
                h.power = hero->getPrimSkillLevel(PrimarySkill::SPELL_POWER);
                h.knowledge = hero->getPrimSkillLevel(PrimarySkill::KNOWLEDGE);
                h.mana = hero->mana;
                h.max_mana = hero->manaLimit();
                h.exp = hero->exp;
                for (int ai = 0; ai < 7; ai++) {
                    auto* stack = hero->getStackPtr(SlotID(ai));
                    h.army_count[ai] = stack ? stack->getCount() : 0;
                    h.army_type[ai] = stack ? stack->getCreatureID().getNum() : 0;
                }
                h.in_battle = 0;
                h.total_power = 0;
                h.is_garrisoned = 0;
                h.has_commander = 0;
            }
        }

        // Towns — 全知直读
        for (int i = 0; i < MAX_TOWNS; i++) state->towns[i].id = -1;
        int ti = 0;
        for (const auto& [color, ps] : gs.players) {
            int pi = color.getNum();
            for (const auto* town : ps.getTowns()) {
                if (ti >= MAX_TOWNS) break;
                auto& t = state->towns[ti++];
                t.id = town->id.getNum();
                t.owner = pi;
                t.pos_x = town->pos.x;
                t.pos_y = town->pos.y;
                t.pos_z = town->pos.z;
                t.buildings = 0;
                t.gold_income = 0;
                memset(t.garrison, 0, sizeof(t.garrison));
                t.recruit_mask_lo = 0; t.recruit_mask_hi = 0;
                t.build_mask_lo = 0; t.build_mask_hi = 0;
            }
        }

        // Passability from tile data (N-start CW, matching AAI.cpp moveHero)
        fill_exploration(state, gicb->gameState());
        if (state->heroes[state->active_hero].id >= 0) {
            // N-start CW: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
            static const int32_t dx[8] = {0,1,1,1,0,-1,-1,-1};
            static const int32_t dy[8] = {-1,-1,0,1,1,1,0,-1};
            int3 hpos(state->heroes[state->active_hero].pos_x, state->heroes[state->active_hero].pos_y, state->heroes[state->active_hero].pos_z);
            const TerrainTile* hposTile = gicb->getTile(hpos, false);
            for (int d = 0; d < 8; d++) {
                int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
                const TerrainTile* tt = gicb->getTile(target, false);
                if (!tt) {
                    state->passable[d] = 0;  // off map
                } else {
                    state->passable[d] = (tt->getTerrain()->isPassable() && !(tt->blocked() && !tt->visitable())) ? 1 : 0;
                }
            }
        } else {
            memset(state->passable, 0, sizeof(state->passable));
        }

        // Game over
        state->game_over = 0;
        int alive_count = 0, last_alive = -1;
        for (int p = 0; p < state->player_count; p++) {
            if (state->players[p].alive) { alive_count++; last_alive = p; }
        }
        if (alive_count <= 1 && state->player_count > 1)
            state->game_over = last_alive + 1;

        // C 事件奖励: 矿归属表 (battle_result 不清零)
        fill_mines(state, gicb->gameState());

        // H 扩展 (v3): 战力/驻守/招募/建造/威胁/预测
        // TODO(debug): fill_v3_fields 暂时禁用排查崩溃
        // fill_v3_fields(state, gicb->gameState());
}

extern "C" void adventure_process_turn(int playerColor, void* userData) {
    if (playerColor != 0) return;  // 只拦截红方 (player 0)

    if (!g_strategic_state) {
        g_strategic_state = new StrategicState();
        memset(g_strategic_state, 0, sizeof(StrategicState));
        g_strategic_state->_version = 3;
    }

    void* cbPtr = userData ? userData : g_ml_player_cb;
    if (cbPtr) fill_strategic_state(cbPtr);

    if (s_capture_mode.load(std::memory_order_acquire))
        s_turn_action.store(s_capture_action.load(std::memory_order_acquire), std::memory_order_release);
    s_turn_action_ready.store(false, std::memory_order_release);
    s_turn_player.store(playerColor, std::memory_order_release);
    int spins = 0;
    while (!s_turn_action_ready.load(std::memory_order_acquire)) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        spins++;
    }
}

// 采集模式 (C8.3 方案A): 阻塞 — NK2 moveHeroToTile/endTurn 决策点调用
// 填 obs + 记录 NK2 动作 + 阻塞等 Python 读走。fill 在 NK2 后台线程执行（无跨线程锁竞争）。
extern "C" void adventure_capture_turn(int playerColor, void* userData, int action) {
    if (playerColor != 0) return;
    s_capture_mode.store(true, std::memory_order_release);
    s_capture_action.store(action, std::memory_order_release);
    adventure_process_turn(playerColor, userData);  // fill + 阻塞等 Python
    s_capture_mode.store(false, std::memory_order_release);
}

// 非阻塞版 (实验废弃, 保留备用)
extern "C" void adventure_capture_noblock(int playerColor, void* userData, int action) {
    if (playerColor != 0) return;
    if (s_turn_player.load(std::memory_order_acquire) >= 0) return;  // 上次未消费, 丢弃
    if (!g_strategic_state) {
        g_strategic_state = new StrategicState();
        memset(g_strategic_state, 0, sizeof(StrategicState));
        g_strategic_state->_version = 3;
    }
    s_capture_mode.store(true, std::memory_order_release);
    s_capture_action.store(action, std::memory_order_release);
    void* cbPtr = userData ? userData : g_ml_player_cb;
    if (cbPtr) fill_strategic_state(cbPtr);
    s_turn_player.store(playerColor, std::memory_order_release);
}

// 非阻塞轮询: 有新数据返回玩家号并消费, 无数据返回 -2
extern "C" int adventure_try_wait() {
    int p = s_turn_player.load(std::memory_order_acquire);
    if (p >= 0) {
        s_turn_player.store(-1, std::memory_order_release);
        return p;
    }
    return -2;
}

extern "C" int adventure_wait_for_turn() {
    int spins = 0;
    while (s_turn_player.load(std::memory_order_acquire) < 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        spins++;
    }
    int p = s_turn_player.load(std::memory_order_acquire);
    s_turn_player.store(-1, std::memory_order_release);
    return p;
}
extern "C" void adventure_send_action(int action) {
    g_rl_action = action;
    s_turn_action.store(action, std::memory_order_release);
    s_turn_action_ready.store(true, std::memory_order_release);
}

extern "C" int adventure_get_action() {
    return s_turn_action.load(std::memory_order_acquire);
}

extern "C" void adventure_cb_trampoline(int playerColor, void* userData) {
    adventure_process_turn(playerColor, userData);
}

extern "C" void register_adventure_delegate(void (*delegate)(int, void*), void* userdata) {
    // 不再需要 delegate — 一切通过 atomic 通信
}

extern "C" void strategic_state_update(void* game_state_ptr) {
    if (!g_strategic_state) {
        g_strategic_state = new StrategicState();
        memset(g_strategic_state, 0, sizeof(StrategicState));
        g_strategic_state->_version = 3;
    }
    if (!game_state_ptr) return;
    {
        auto& gs = *static_cast<CGameState*>(game_state_ptr);
        auto& state = *g_strategic_state;
        // 主体锁 (内部 fill_exploration/fill_mines/fill_v3_fields 不再自带锁)
        std::shared_lock fillLock(CGameState::mutex);

        state.day = gs.day;
        state.week = (gs.day - 1) / 7 + 1;
        state.month = (gs.day - 1) / 28 + 1;
        state.current_player = 0;
        if (!gs.actingPlayers.empty())
            state.current_player = static_cast<int32_t>(gs.actingPlayers.begin()->getNum());

        auto& map = gs.getMap();
        state.map_width = map.width;
        state.map_height = map.height;
        state.has_underground = map.levels() > 1 ? 1 : 0;

        // Players
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
            p.hero_count = (int)ps.getHeroes().size();
            p.town_count = (int)ps.getTowns().size();
            p.alive = (ps.status == EPlayerStatus::INGAME) ? 1 : 0;
            p.total_power = 0; p.weekly_income = 0; p.relation_to_me = 0;
        }

        // Heroes
        for (int i = 0; i < MAX_HEROES; i++) state.heroes[i].id = -1;
        int hi = 0;
        for (auto& [color, ps] : gs.players) {
            int pi = color.getNum();
            for (const auto* hero : ps.getHeroes()) {
                if (hi >= MAX_HEROES) break;
                auto& h = state.heroes[hi++];
                h.id = hero->id.getNum();
                h.owner = pi;
                h.pos_x = hero->pos.x;
                h.pos_y = hero->pos.y;
                h.pos_z = hero->pos.z;
                h.movement = hero->movementPointsRemaining();
                h.max_movement = hero->movementPointsLimit();
                h.level = hero->level;
                h.mana = hero->mana;
                h.exp = hero->exp;
                for (int ai = 0; ai < 7; ai++) {
                    auto* stack = hero->getStackPtr(SlotID(ai));
                    h.army_count[ai] = stack ? stack->getCount() : 0;
                    h.army_type[ai] = stack ? stack->getCreatureID().getNum() : 0;
                }
                h.total_power = 0; h.is_garrisoned = 0; h.has_commander = 0;
            }
        }

        memset(state.passable, 0, sizeof(state.passable));
        fill_exploration(&state, gs);
        if (state.heroes[state.active_hero].id >= 0) {
            // N-start CW: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
            static const int32_t dx[8] = {0,1,1,1,0,-1,-1,-1};
            static const int32_t dy[8] = {-1,-1,0,1,1,1,0,-1};
            auto& hpos_tile = gs.getMap().getTile(int3(state.heroes[state.active_hero].pos_x, state.heroes[state.active_hero].pos_y, state.heroes[state.active_hero].pos_z));
            for (int d = 0; d < 8; d++) {
                int3 target(state.heroes[state.active_hero].pos_x + dx[d], state.heroes[state.active_hero].pos_y + dy[d], state.heroes[state.active_hero].pos_z);
                if (target.x < 0 || target.x >= (int)map.width || target.y < 0 || target.y >= (int)map.height) {
                    state.passable[d] = 0;
                } else {
                    auto& tile = gs.getMap().getTile(target);
                    state.passable[d] = (tile.getTerrain()->isPassable() && !(tile.blocked() && !tile.visitable())) ? 1 : 0;
                }
            }
        }

        // Towns
        for (int i = 0; i < MAX_TOWNS; i++) state.towns[i].id = -1;
        int ti = 0;
        for (auto& [color, ps] : gs.players) {
            int pi = color.getNum();
            for (const auto* town : ps.getTowns()) {
                if (ti >= MAX_TOWNS) break;
                auto& t = state.towns[ti++];
                t.id = town->id.getNum();
                t.owner = pi;
                t.pos_x = town->pos.x;
                t.pos_y = town->pos.y;
                t.pos_z = town->pos.z;
                memset(t.garrison, 0, sizeof(t.garrison));
                t.recruit_mask_lo = 0; t.recruit_mask_hi = 0;
                t.build_mask_lo = 0; t.build_mask_hi = 0;
            }
        }

        state.game_over = 0;
        int alive_count = 0, last_alive = -1;
        for (int p = 0; p < state.player_count; p++) {
            if (state.players[p].alive) { alive_count++; last_alive = p; }
        }
        if (alive_count <= 1 && state.player_count > 1)
            state.game_over = last_alive + 1;

        // C 事件奖励: 矿归属表 (battle_result 不清零)
        fill_mines(&state, gs);

        // H 扩展 (v3)
        fill_v3_fields(&state, gs);
    }
}
