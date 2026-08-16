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
#include "mapObjects/army/CArmedInstance.h"
#include "mapObjects/army/CStackInstance.h"
#include "constants/EntityIdentifiers.h"
#include "CCreatureHandler.h"
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
        g_strategic_state->_version = 2;
        for (int d = 0; d < 8; d++)
            g_strategic_state->passable[d] = 1;
    }
}

AdventureYourTurnCallback g_adventure_cb = nullptr;
void* g_adventure_cb_userdata = nullptr;
// 由 AAI::yourTurn 设置的全局 CCallback 指针（跨 .so 可见）
extern "C" void* g_ml_player_cb = nullptr;

// H.5: 军队战力 (army × getAIValue 求和)
// CArmedInstance::Slots() → CStackInstance::getCreature() → CCreature::getAIValue()
static int64_t calc_army_power(const CArmedInstance* armed) {
    int64_t power = 0;
    if (!armed) return 0;
    for (const auto& [slot, stack] : armed->Slots()) {
        const auto* cr = stack->getCreature();
        if (cr) power += (int64_t)cr->getAIValue() * (int64_t)stack->getCount();
    }
    return power;
}

// H.5: 守卫对象战力 (getGuardingCreatures 返回的守卫对象, 通常是 MONSTER/CGCreature)
static int64_t calc_guard_power(const CGObjectInstance* obj) {
    const auto* armed = dynamic_cast<const CArmedInstance*>(obj);
    return armed ? calc_army_power(armed) : 0;
}

// B 态势感知: 填充 active_hero + local_tiles + global_explored
// 探索状态读取: CGameState 的 fogOfWarMap (TeamState, 1=visible/explored, 0=hidden)
static void fill_exploration(StrategicState* state, CGameState& gs) {
    // 数据竞争修复 (2026-08-01): fill 在 NK2/MMAI 后台线程执行, 无锁直读 CGameState 会与
    // AI 规划线程竞争 (NK2 决策损坏 → moveHero 全被拒)。加 shared_lock (与 AAI.cpp 同模式,
    // 读锁可并发, 只挡写)。
    std::shared_lock gsLock(CGameState::mutex);
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

    // local_tiles: active hero 所在层 15×15 窗口
    if (state->heroes[ah].id >= 0) {
        int cx = state->heroes[ah].pos_x;
        int cy = state->heroes[ah].pos_y;
        int cz = state->heroes[ah].pos_z;
        const auto& from_tile = map.getTile(int3(cx, cy, cz));  // isClear 需要 from (VCMI 实现 nullptr 会崩)
        for (int dy = -7; dy <= 7; dy++) {
            for (int dx = -7; dx <= 7; dx++) {
                int x = cx + dx, y = cy + dy;
                int8_t v = 0;
                if (x >= 0 && x < mw && y >= 0 && y < mh) {
                    int3 pos(x, y, cz);
                    if (team->fogOfWarMap[pos]) {  // 已探索
                        const auto& tile = map.getTile(pos);
                        v = tile.isClear(&from_tile) ? 1 : 2;  // 1=可通行, 2=不可通行; 有物体与1合并, 宁简勿错

                        // H.5 v3 通道1: 对象类型 (Obj 枚举值, 0=无) — top object
                        if (!tile.visitableObjects.empty()) {
                            const CGObjectInstance* top = gs.getObjInstance(tile.visitableObjects.front());
                            if (top) {
                                int32_t objType = top->ID.getNum();
                                if (objType > 0 && objType < 128)  // int8 范围保护
                                    state->local_tiles[1][dy + 7][dx + 7] = (int8_t)objType;
                            }
                        }

                        // H.5 v3 通道2: 守卫战力 (log 压缩, 防 int8 溢出)
                        int64_t guard = 0;
                        for (const auto* g : gs.guardingCreatures(pos))
                            guard += calc_guard_power(g);
                        if (guard > 0) {
                            int32_t gv = (int32_t)std::log2((double)guard + 1.0);
                            state->local_tiles[2][dy + 7][dx + 7] = (int8_t)std::min(gv, 127);
                        }
                    }
                }
                state->local_tiles[0][dy + 7][dx + 7] = v;
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
    // 数据竞争修复 (2026-08-01): 同 fill_exploration — 无锁直读 map.objects 与 AI 线程竞争
    std::shared_lock gsLock(CGameState::mutex);
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

// H.5: v3 扩展字段填充 — 战力/驻守/招募/建造/威胁/预测 (obs 段 1/2/3/10/11)
// 全知直读 gs.players/heroes/towns 实体 (与 fill_strategic_state 同模式)。
// 调用前提: heroes/towns/players 段已按全知直读填好 id/owner (槽位靠 id 匹配)。
static void fill_v3_fields(StrategicState* state, CGameInfoCallback* gicb) {
    std::shared_lock gsLock(CGameState::mutex);
    auto& gs = gicb->gameState();

    // 重置 (fill 每次全量重算, 无残留)
    for (int i = 0; i < MAX_PLAYERS; i++) {
        state->players[i].total_power = 0;
        state->players[i].weekly_income = 0;
        state->players[i].relation_to_me = 0;
    }
    for (int i = 0; i < MAX_HEROES; i++) {
        state->heroes[i].total_power = 0;
        state->heroes[i].is_garrisoned = 0;
        state->heroes[i].has_commander = 0;
    }
    for (int i = 0; i < MAX_TOWNS; i++) {
        state->towns[i].recruit_mask_lo = 0;
        state->towns[i].recruit_mask_hi = 0;
        state->towns[i].build_mask_lo = 0;
        state->towns[i].build_mask_hi = 0;
    }
    memset(state->enemy_threat, 0, sizeof(state->enemy_threat));
    memset(state->battle_pred, 0, sizeof(state->battle_pred));

    // 1) heroes: total_power / is_garrisoned / has_commander (按 id 匹配 state 槽位)
    for (const auto& [color, ps] : gs.players) {
        for (const auto* hero : ps.getHeroes()) {
            if (!hero) continue;
            int64_t power = calc_army_power(hero);
            for (int i = 0; i < MAX_HEROES; i++) {
                if (state->heroes[i].id == hero->id.getNum() && state->heroes[i].owner == color.getNum()) {
                    state->heroes[i].total_power = (int32_t)power;
                    state->heroes[i].has_commander = hero->getCommander() ? 1 : 0;
                    break;
                }
            }
        }
    }
    // is_garrisoned: 城镇 garrisonHero 字段指向驻守英雄 id (private, 用 getUpperArmy 判断)
    for (const auto& [color, ps] : gs.players) {
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            const auto* upperArmy = town->getUpperArmy();
            const auto* gh = dynamic_cast<const CGHeroInstance*>(upperArmy);
            if (!gh) continue;
            for (int i = 0; i < MAX_HEROES; i++) {
                if (state->heroes[i].id == gh->id.getNum()) {
                    state->heroes[i].is_garrisoned = 1;
                    break;
                }
            }
        }
    }

    // 2) towns: recruit_mask (dwelling 已建) / build_mask (canBuildStructure==ALLOWED)
    for (const auto& [color, ps] : gs.players) {
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            int slot = -1;
            for (int i = 0; i < MAX_TOWNS; i++) {
                if (state->towns[i].id == town->id.getNum() && state->towns[i].owner == color.getNum()) {
                    slot = i;
                    break;
                }
            }
            if (slot < 0) continue;
            auto& t = state->towns[slot];

            // recruit_mask: bit = level*2 + upgrade (level 0-6, upgrade 0=base/1=up)
            // dwelling 建筑已建 → 该级兵可招募
            uint32_t rlo = 0, rhi = 0;
            const auto& townCreatures = town->getTown()->creatures;  // level → creature list
            for (size_t lvl = 0; lvl < townCreatures.size() && lvl < 7; lvl++) {
                if (townCreatures[lvl].empty()) continue;
                for (int up = 0; up < 2; up++) {
                    BuildingID bid = BuildingID::getDwellingFromLevel((int)lvl, up);
                    if (town->hasBuilt(bid)) {
                        int bit = (int)lvl * 2 + up;
                        if (bit < 32) rlo |= (1u << bit);
                        else rhi |= (1u << (bit - 32));
                    }
                }
            }
            t.recruit_mask_lo = (int32_t)rlo;
            t.recruit_mask_hi = (int32_t)rhi;

            // build_mask: 只算己方城镇 (owner==0) — canBuildStructure 对敌城返回 TOWN_NOT_OWNED 并打 ERROR 刷屏
            // bit = 建筑在城镇 buildings map (按 BuildingID 排序) 中的索引, 前 32 个可建
            // 置位条件: ALLOWED(现在能建) | CANT_BUILD_TODAY(今天已建过, 明天可建) | NO_RESOURCES(缺资源, 凑齐可建)
            // 排除: ALREADY_PRESENT(已建) / PREREQUIRES·MISSING_BASE(前置未满足) / FORBIDDEN / BUILDING_ERROR
            uint32_t blo = 0, bhi = 0;
            if (color.getNum() == 0) {
                int bidx = 0;
                for (const auto& [bid, bptr] : town->getTown()->buildings) {
                    if (bidx >= 64) break;
                    auto st = gicb->canBuildStructure(town, bid);
                    if (st == EBuildingState::ALLOWED || st == EBuildingState::CANT_BUILD_TODAY || st == EBuildingState::NO_RESOURCES) {
                        if (bidx < 32) blo |= (1u << bidx);
                        else bhi |= (1u << (bidx - 32));
                    }
                    bidx++;
                }
            }
            t.build_mask_lo = (int32_t)blo;
            t.build_mask_hi = (int32_t)bhi;
        }
    }

    // 3) players: total_power (该玩家所有英雄求和) / weekly_income (城镇日收入×7) / relation_to_me
    for (const auto& [color, ps] : gs.players) {
        int pi = color.getNum();
        if (pi < 0 || pi >= MAX_PLAYERS) continue;
        // 匹配 state->players 槽位 (color 段已填)
        int slot = -1;
        for (int i = 0; i < state->player_count; i++) {
            if (state->players[i].color == pi) { slot = i; break; }
        }
        if (slot < 0) continue;
        auto& p = state->players[slot];

        int64_t totalPower = 0;
        for (const auto* hero : ps.getHeroes())
            if (hero) totalPower += calc_army_power(hero);
        p.total_power = (int32_t)totalPower;

        int64_t weeklyGold = 0;
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            auto income = town->dailyIncome();  // ResourceSet
            weeklyGold += income[EGameResID::GOLD] * 7;
        }
        p.weekly_income = (int32_t)weeklyGold;

        // PlayerRelations: ENEMIES=0, ALLIES=1, SAME_PLAYER=2 → 映射 0=中立 1=敌对 2=结盟
        PlayerRelations rel = gs.getPlayerRelations(PlayerColor(0), PlayerColor(pi));
        if (rel == PlayerRelations::ENEMIES) p.relation_to_me = 1;
        else if (rel == PlayerRelations::ALLIES) p.relation_to_me = 2;
        else p.relation_to_me = 0;  // SAME_PLAYER(自己)/其他
    }

    // 4) enemy_threat[7]: 每敌方玩家 (排除自己) 总战力 — 按 players 段顺序
    {
        int et = 0;
        for (int i = 0; i < state->player_count && et < ENEMY_THREAT; i++) {
            if (state->players[i].color == 0) continue;  // 排除自己 (red)
            state->enemy_threat[et++] = state->players[i].total_power;
        }
    }

    // 5) battle_pred[4]: my_power / target_power(最近守卫) / win_prob
    {
        int ah = state->active_hero;
        if (ah >= 0 && ah < MAX_HEROES && state->heroes[ah].id >= 0) {
            int64_t myPower = state->heroes[ah].total_power;
            // target: active hero 所在格守卫战力
            int64_t targetPower = 0;
            int3 hpos(state->heroes[ah].pos_x, state->heroes[ah].pos_y, state->heroes[ah].pos_z);
            for (const auto* g : gs.guardingCreatures(hpos))
                targetPower += calc_guard_power(g);
            state->battle_pred[0] = (int32_t)myPower;
            state->battle_pred[1] = (int32_t)targetPower;
            if (myPower + targetPower > 0)
                state->battle_pred[2] = (int32_t)(myPower * 100 / (myPower + targetPower));  // win_prob 0-100
            state->battle_pred[3] = 0;
        }
    }
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
        auto *ps = gicb->getPlayerState(PlayerColor(0), false);

        // Players — H.4 全知直读 (遍历 gs.players, 绕过 getPlayerState 可见性限制)
        {
            const auto& gs0 = gicb->gameState();
            std::shared_lock plock(CGameState::mutex);
            state->player_count = 0;
            for (const auto& [color, ps] : gs0.players) {
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
            }
        }
        // Calendar info (day/week/month) — via gameState().day matching strategic_state_update()
        {
            const auto& gs = gicb->gameState();
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

        // Heroes — H.4 全知直读: 遍历 gs.players (绕过 CGameInfoCallback::getHeroes 的 isVisibleFor 过滤)
        // C8.4 教训: 无锁直读 gs.players 与 NK2 规划线程竞争 → 加 shared_lock
        std::shared_lock hlock(CGameState::mutex);
        {
            const auto& gs2 = gicb->gameState();
            for (int i = 0; i < MAX_HEROES; i++) state->heroes[i].id = -1;
            int hi = 0;
            for (const auto& [color, ps] : gs2.players) {
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
                    }
                    h.in_battle = 0;
                }
            }
        }

        // Passability from tile data (N-start CW, matching AAI.cpp moveHero)
        // Use CGameInfoCallback::getTile().isClear() — checks terrain + obstacles
        // B 态势感知: 先填 active_hero/local_tiles/global_explored, passability 用 active hero
        // B 态势感知: 先填 active_hero/local_tiles/global_explored, passability 用 active hero
        fill_exploration(state, gicb->gameState());
        if (state->heroes[state->active_hero].id >= 0) {
            // N-start CW: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
            static const int32_t dx[8] = {0,1,1,1,0,-1,-1,-1};
            static const int32_t dy[8] = {-1,-1,0,1,1,1,0,-1};
            int3 hpos(state->heroes[state->active_hero].pos_x, state->heroes[state->active_hero].pos_y, state->heroes[state->active_hero].pos_z);
            // Get hero's own tile for isClear(from) check
            const TerrainTile* hposTile = gicb->getTile(hpos, false);
            for (int d = 0; d < 8; d++) {
                int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
                const TerrainTile* tt = gicb->getTile(target, false);
                if (!tt) {
                    state->passable[d] = 0;  // off map
                } else {
                    state->passable[d] = tt->isClear(hposTile) ? 1 : 0;
                }
            }
        } else {
            memset(state->passable, 0, sizeof(state->passable));
        }

                // Towns — H.4 全知直读 (8-2 fill 遗漏, 补上; 遍历 gs.players 拿全部城镇)
        {
            const auto& gs3 = gicb->gameState();
            std::shared_lock tlock(CGameState::mutex);
            for (int i = 0; i < MAX_TOWNS; i++) state->towns[i].id = -1;
            int ti = 0;
            for (const auto& [color, ps] : gs3.players) {
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
                    memset(t.garrison, 0, sizeof(t.garrison));
                    t.gold_income = 0;
                    t.recruit_mask_lo = 0; t.recruit_mask_hi = 0;
                    t.build_mask_lo = 0; t.build_mask_hi = 0;
                }
            }
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
        // C 事件奖励: 矿归属表 (battle_result 不清零)
        fill_mines(state, gicb->gameState());

        // H.5: v3 扩展字段 (战力/驻守/招募/建造/威胁/预测)
        fill_v3_fields(state, gicb);
}

extern "C" void adventure_process_turn(int playerColor, void* userData) {
    if (playerColor != 0) return;  // 只拦截红方 (player 0)

    if (!g_strategic_state) {
        g_strategic_state = new StrategicState();
        memset(g_strategic_state, 0, sizeof(StrategicState));
        g_strategic_state->_version = 2;
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
        g_strategic_state->_version = 2;
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

// VCMI 冒险地图 AI 的 getAction 回调中调用此函数填充状态
// 参数：指向 CGameState 的指针（VCMI 内部类型，C++ 侧有完整访问）
extern "C" void strategic_state_update(void* game_state_ptr) {
    if (!g_strategic_state) {
        g_strategic_state = new StrategicState();
        memset(g_strategic_state, 0, sizeof(StrategicState));
        g_strategic_state->_version = 2;
    }
    if (!game_state_ptr) return;
    {
        auto& gs = *static_cast<CGameState*>(game_state_ptr);
        auto& state = *g_strategic_state;

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
        }

        state.heroes[0].id = -1;
        int hi = 0;
        for (int pi = 0; pi < state.player_count && hi < MAX_HEROES; pi++) {
            if (!gs.players.count(PlayerColor(pi))) continue;
            auto& ps = gs.players.at(PlayerColor(pi));
            auto heroes = ps.getHeroes();
            for (size_t i = 0; i < heroes.size() && hi < MAX_HEROES; i++, hi++) {
                const auto* hero = heroes[i];
                auto& h = state.heroes[hi];
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
            }
        }

        memset(state.passable, 0, sizeof(state.passable));
        // B 态势感知: 先填 active_hero/local_tiles/global_explored, passability 用 active hero
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
                    state.passable[d] = tile.isClear(&hpos_tile) ? 1 : 0;
                }
            }
        }

        int ti = 0;
        for (int pi = 0; pi < state.player_count && ti < MAX_TOWNS; pi++) {
            if (!gs.players.count(PlayerColor(pi))) continue;
            auto& ps = gs.players.at(PlayerColor(pi));
            auto towns = ps.getTowns();
            for (size_t i = 0; i < towns.size() && ti < MAX_TOWNS; i++, ti++) {
                const auto* town = towns[i];
                auto& t = state.towns[ti];
                t.id = town->id.getNum();
                t.owner = pi;
                t.pos_x = town->pos.x;
                t.pos_y = town->pos.y;
                t.pos_z = town->pos.z;
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
    }
}
