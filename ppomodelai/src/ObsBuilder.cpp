// ObsBuilder.cpp — MBState 填充 + 3464 obs 展平 (部署版)
// 移植自 vcmi/ML/strategic_state.cpp (fill 函数族) + vcmi_gym/envs/v13/strategic_env.py::_strategic_state_to_obs
// 与训练侧的差异:
//   1. selfPlayer 参数化 (训练恒 0); 2. activeHeroId 传英雄 ObjectInstanceID 全局 id;
//   3. 无全局指针/训练桥/terrain 文件写出; 4. 锁改为每段独立作用域 (训练外层 hlock 长持有
//      + 内部再 lock_shared 是 std::shared_mutex 递归共享获取, 标准未定义, MinGW 不保证);
//   5. 去 fill_mines/game_over/nav (MBState 无对应字段, obs 对应段恒 0 — 与训练一致)

#include "StdInc.h"
#include "ObsBuilder.h"

#include "callback/CCallback.h"
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
#include "constants/Enumerations.h"
#include "CCreatureHandler.h"
#include "CPlayerState.h"
#include "ResourceSet.h"

#include <cstring>
#include <algorithm>
#include <cmath>
#include <shared_mutex>
#include <vector>

// ---------------------------------------------------------------------------
// H.5: 军队战力 (army x getAIValue 求和) — 同 strategic_state.cpp::calc_army_power
// ---------------------------------------------------------------------------
static int64_t mb_calc_army_power(const CArmedInstance* armed) {
    int64_t power = 0;
    if (!armed) return 0;
    for (const auto& [slot, stack] : armed->Slots()) {
        const auto* cr = stack->getCreature();
        if (cr) power += (int64_t)cr->getAIValue() * (int64_t)stack->getCount();
    }
    return power;
}

// H.5: 守卫对象战力
static int64_t mb_calc_guard_power(const CGObjectInstance* obj) {
    const auto* armed = dynamic_cast<const CArmedInstance*>(obj);
    return armed ? mb_calc_army_power(armed) : 0;
}

// ---------------------------------------------------------------------------
// B 态势感知: active_hero + local_tiles + global_explored
// (同 strategic_state.cpp::fill_exploration; activeHeroId=英雄全局 id, selfPlayer 参数化)
// ---------------------------------------------------------------------------
static void mb_fill_exploration(MBState* state, CGameState& gs, int selfPlayer, int activeHeroId) {
    std::shared_lock gsLock(CGameState::mutex);

    // activeHeroId (全局 id) → heroes 槽位: 要求 id+owner==selfPlayer;
    // fallback: 第一个己方英雄; 仍无 → -1 (调用方需防护 active_hero<0)
    int32_t ah = -1;
    if (activeHeroId >= 0) {
        for (int i = 0; i < MB_MAX_HEROES; i++) {
            if (state->heroes[i].id == activeHeroId && state->heroes[i].owner == selfPlayer) {
                ah = i;
                break;
            }
        }
    }
    if (ah < 0) {
        for (int i = 0; i < MB_MAX_HEROES; i++) {
            if (state->heroes[i].id >= 0 && state->heroes[i].owner == selfPlayer) {
                ah = i;
                break;
            }
        }
    }
    state->active_hero = ah;

    memset(state->local_tiles, 0, sizeof(state->local_tiles));
    memset(state->global_explored, 0, sizeof(state->global_explored));

    auto& map = gs.getMap();
    int mw = (int)map.width, mh = (int)map.height;
    if (mw <= 0 || mh <= 0) return;

    const auto* team = gs.getPlayerTeam(PlayerColor(selfPlayer));
    if (!team) return;

    // local_tiles: active hero 所在层 15x15 窗口 (中心 = visitablePos, 与服务器 moveHero 坐标系对齐)
    if (ah >= 0 && state->heroes[ah].id >= 0) {
        int cx = state->heroes[ah].pos_x;
        int cy = state->heroes[ah].pos_y;
        int cz = state->heroes[ah].pos_z;
        const CGHeroInstance* hero = dynamic_cast<const CGHeroInstance*>(gs.getObjInstance(ObjectInstanceID(state->heroes[ah].id)));
        if (hero) {
            int3 hc = hero->visitablePos();
            cx = hc.x; cy = hc.y; cz = hc.z;
        }
        const auto& from_tile = map.getTile(int3(cx, cy, cz));  // isClear 需要 from
        for (int dy = -7; dy <= 7; dy++) {
            for (int dx = -7; dx <= 7; dx++) {
                int x = cx + dx, y = cy + dy;
                int8_t v = 0;
                if (x >= 0 && x < mw && y >= 0 && y < mh) {
                    int3 pos(x, y, cz);
                    if (team->fogOfWarMap[pos]) {  // 已探索
                        const auto& tile = map.getTile(pos);
                        v = tile.isClear(&from_tile) ? 1 : 2;

                        // 通道1: 对象类型 (Obj 枚举值, 0=无)
                        if (!tile.visitableObjects.empty()) {
                            const CGObjectInstance* top = gs.getObjInstance(tile.visitableObjects.front());
                            if (top) {
                                int32_t objType = top->ID.getNum();
                                if (objType > 0 && objType < 128)
                                    state->local_tiles[1][dy + 7][dx + 7] = (int8_t)objType;
                            }
                        }

                        // 通道2: 守卫战力 (log2 压缩)
                        int64_t guard = 0;
                        for (const auto* g : gs.guardingCreatures(pos))
                            guard += mb_calc_guard_power(g);
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

    // global_explored: 全图下采样 32x32x2, 块内任一 tile 已探索则块=1
    int bw = (mw + MB_GLOBAL_GRID - 1) / MB_GLOBAL_GRID;
    int bh = (mh + MB_GLOBAL_GRID - 1) / MB_GLOBAL_GRID;
    for (int z = 0; z < MB_MAX_LEVELS && z < map.levels(); z++) {
        for (int gy = 0; gy < MB_GLOBAL_GRID; gy++) {
            for (int gx = 0; gx < MB_GLOBAL_GRID; gx++) {
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

// ---------------------------------------------------------------------------
// H.8: target_list — 最近 8 个可采集目标 (同 strategic_state.cpp::fill_target_list)
// ---------------------------------------------------------------------------
static void mb_fill_target_list(MBState* state, CGameState& gs) {
    std::shared_lock gsLock(CGameState::mutex);
    int ah = state->active_hero;
    if (ah < 0 || ah >= MB_MAX_HEROES || state->heroes[ah].id < 0) return;
    int hx = state->heroes[ah].pos_x, hy = state->heroes[ah].pos_y, hz = state->heroes[ah].pos_z;

    struct TargetCand {
        int type, idx, x, y, z, dist;
        int64_t guard;
    };
    std::vector<TargetCand> cands;
    auto& map = gs.getMap();
    for (const auto& objPtr : map.objects) {
        if (!objPtr) continue;
        const auto* obj = objPtr.get();
        int type = 0;
        if (obj->ID == Obj::MINE) {
            int owner = obj->getOwner().getNum();
            if (owner >= 0 && owner < 8) continue;  // 已占矿跳过
            type = 1;
        } else if (obj->ID == Obj::RESOURCE) type = 2;
        else if (obj->ID == Obj::CAMPFIRE) type = 3;
        else if (obj->ID == Obj::TREASURE_CHEST) type = 4;
        else if (obj->ID == Obj::ARTIFACT) type = 5;
        else continue;
        if (obj->pos.z != hz) continue;  // 同层
        int dist = std::abs(obj->pos.x - hx) + std::abs(obj->pos.y - hy);
        if (dist <= 0) continue;
        int64_t guard = 0;
        for (const auto* g : gs.guardingCreatures(obj->pos))
            guard += mb_calc_guard_power(g);
        cands.push_back({type, obj->id.getNum(), obj->pos.x, obj->pos.y, obj->pos.z, dist, guard});
    }
    std::sort(cands.begin(), cands.end(),
              [](const TargetCand& a, const TargetCand& b) { return a.dist < b.dist; });
    int n = std::min<int>(MB_TARGET_LIST, (int)cands.size());
    for (int i = 0; i < n; i++) {
        state->target_list[i][0] = cands[i].type;
        state->target_list[i][1] = cands[i].idx;
        state->target_list[i][2] = cands[i].x;
        state->target_list[i][3] = cands[i].y;
        state->target_list[i][4] = cands[i].z;
        state->target_list[i][5] = cands[i].dist;
        state->target_list[i][6] = (int32_t)std::log2((double)cands[i].guard + 1.0);
        state->target_list[i][7] = 0;
    }
    for (int i = n; i < MB_TARGET_LIST; i++)
        for (int j = 0; j < MB_TARGET_DIM; j++)
            state->target_list[i][j] = 0;
}

// ---------------------------------------------------------------------------
// I.2: BFS 首步方向 → reserved[0..7], 诊断 reserved[8..15]
// (同 strategic_state.cpp::fill_next_dir; N-start CW 与训练/部署动作语义一致)
// ---------------------------------------------------------------------------
static void mb_fill_next_dir(MBState* state, CGameInfoCallback* gicb) {
    for (int i = 0; i < 16; i++)
        state->reserved[i] = -1;

    int ah = state->active_hero;
    if (ah < 0 || ah >= MB_MAX_HEROES || state->heroes[ah].id < 0) return;

    std::shared_lock gsLock(CGameState::mutex);  // 训练依赖外层 hlock, 部署独立加锁

    const CGHeroInstance* hero = dynamic_cast<const CGHeroInstance*>(
        gicb->gameState().getObjInstance(ObjectInstanceID(state->heroes[ah].id)));
    if (!hero) return;
    int3 hpos = hero->visitablePos();
    int hx = hpos.x, hy = hpos.y, hz = hpos.z;
    int W = state->map_width;
    int H = state->map_height;

    if (hx < 0 || hx >= W || hy < 0 || hy >= H) return;

    state->reserved[8] = hx; state->reserved[9] = hy; state->reserved[10] = hz;
    state->reserved[11] = W; state->reserved[12] = H;

    // N 起顺时针: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW (与 v5 动作 0-7 一致)
    static const int DX[8] = {0, 1, 1, 1, 0, -1, -1, -1};
    static const int DY[8] = {-1, -1, 0, 1, 1, 1, 0, -1};
    auto& map = gicb->gameState().getMap();

    for (int t = 0; t < MB_TARGET_LIST; t++) {
        if (state->target_list[t][0] == 0) continue;
        int tx = state->target_list[t][2];
        int ty = state->target_list[t][3];
        int tz = state->target_list[t][4];
        if (tz != hz) continue;
        if (tx == hx && ty == hy) continue;

        std::vector<int> parent(W * H, -1);
        std::vector<bool> visited(W * H, false);
        int si = hy * W + hx;
        visited[si] = true;
        std::vector<int> q; q.reserve(256); q.push_back(si);
        int qh = 0; bool found = false;

        while (qh < (int)q.size() && !found) {
            int ci = q[qh++];
            int cx = ci % W, cy = ci / W;
            for (int d = 0; d < 8 && !found; d++) {
                int nx = cx + DX[d], ny = cy + DY[d];
                if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
                int ni = ny * W + nx;
                if (visited[ni]) continue;
                bool isTarget = (nx == tx && ny == ty);
                if (!isTarget) {
                    auto& dstTile = map.getTile(int3(nx, ny, hz));
                    if (!dstTile.getTerrain()->isLand() || !dstTile.getTerrain()->isPassable() || dstTile.blocked()) continue;
                }
                visited[ni] = true;
                parent[ni] = ci;
                if (isTarget) {
                    int step = ni;
                    while (parent[step] != si) step = parent[step];
                    int sx = step % W, sy = step / W;
                    int fdx = sx - hx, fdy = sy - hy;
                    for (int k = 0; k < 8; k++)
                        if (DX[k] == fdx && DY[k] == fdy) { state->reserved[t] = k; break; }
                    found = true;
                }
                q.push_back(ni);
            }
        }
        if (t == 0) {
            state->reserved[13] = state->reserved[0];
            state->reserved[14] = (int)q.size();
        }
    }
}

// ---------------------------------------------------------------------------
// Phase I.4: 地形栅格 21x21x4 HWC uint8 (同 strategic_state.cpp::fill_terrain_grid,
// 去文件写出/stderr — ModelInference 直接读内存)
// ---------------------------------------------------------------------------
static void mb_fill_terrain_grid_mem(MBState* state, CGameInfoCallback* gicb) {
    int ah = state->active_hero;
    if (ah < 0 || ah >= MB_MAX_HEROES || state->heroes[ah].id < 0) return;

    std::shared_lock gsLock(CGameState::mutex);  // 训练依赖外层 hlock, 部署独立加锁

    const CGHeroInstance* hero = dynamic_cast<const CGHeroInstance*>(
        gicb->gameState().getObjInstance(ObjectInstanceID(state->heroes[ah].id)));
    if (!hero) return;

    int3 hpos = hero->visitablePos();
    int hx = hpos.x, hy = hpos.y, hz = hpos.z;
    int W = state->map_width, H = state->map_height;
    int half = MB_GRID_SIZE / 2;  // 10
    auto& map = gicb->gameState().getMap();
    auto& gs = gicb->gameState();

    for (int r = 0; r < MB_GRID_SIZE; r++) {
        for (int c = 0; c < MB_GRID_SIZE; c++) {
            int mx = hx + (c - half);
            int my = hy + (r - half);
            int idx = (r * MB_GRID_SIZE + c) * MB_GRID_CH;

            // 越界: C1=1 (不可通行), 其余 0
            if (mx < 0 || mx >= W || my < 0 || my >= H) {
                state->terrain_grid_hwc[idx + 0] = 0;
                state->terrain_grid_hwc[idx + 1] = 1;
                state->terrain_grid_hwc[idx + 2] = 0;
                state->terrain_grid_hwc[idx + 3] = 0;
                continue;
            }

            auto& tile = map.getTile(int3(mx, my, hz));

            // C0: terrain type
            state->terrain_grid_hwc[idx + 0] = (uint8_t)tile.terrainType;

            // C1: blocked
            state->terrain_grid_hwc[idx + 1] = tile.blocked() ? 1 : 0;

            // C2: 对象类型 (优先级体系, 同训练)
            uint8_t obj_type = 0;
            for (auto objId : tile.visitableObjects) {
                auto obj = gs.getObjInstance(objId);
                if (!obj) continue;
                uint8_t t = 10;
                if (obj->ID == Obj::HERO) t = 6;
                else if (obj->ID == Obj::TOWN) t = 2;
                else if (obj->ID == Obj::MONSTER || obj->ID == Obj::RANDOM_MONSTER) t = 5;
                else if (obj->ID == Obj::ARTIFACT) t = 7;
                else if (obj->ID == Obj::TREASURE_CHEST) t = 4;
                else if (obj->ID == Obj::RESOURCE) t = 3;
                else if (obj->ID == Obj::MINE) t = 1;
                else if (obj->ID == Obj::CREATURE_GENERATOR1 || obj->ID == Obj::CREATURE_GENERATOR2) t = 8;
                else if (obj->ID == Obj::SUBTERRANEAN_GATE || obj->ID == Obj::BORDER_GATE) t = 9;
                static const int prio[] = {0, 5, 9, 6, 7, 8, 10, 8, 4, 3, 1};
                if (t < 11 && (obj_type == 0 || prio[t] > prio[obj_type]))
                    obj_type = t;
            }
            state->terrain_grid_hwc[idx + 2] = obj_type;

            // C3: visibility (训练期全可见, 部署同值保持分布一致)
            state->terrain_grid_hwc[idx + 3] = 1;
        }
    }
}

// ---------------------------------------------------------------------------
// H.5: v3 扩展字段 — 战力/驻守/招募/建造/威胁/预测 (selfPlayer 参数化)
// ---------------------------------------------------------------------------
static void mb_fill_v3_fields(MBState* state, CGameInfoCallback* gicb, int selfPlayer) {
    std::shared_lock gsLock(CGameState::mutex);
    auto& gs = gicb->gameState();

    for (int i = 0; i < MB_MAX_PLAYERS; i++) {
        state->players[i].total_power = 0;
        state->players[i].weekly_income = 0;
        state->players[i].relation_to_me = 0;
    }
    for (int i = 0; i < MB_MAX_HEROES; i++) {
        state->heroes[i].total_power = 0;
        state->heroes[i].is_garrisoned = 0;
        state->heroes[i].has_commander = 0;
    }
    for (int i = 0; i < MB_MAX_TOWNS; i++) {
        state->towns[i].recruit_mask_lo = 0;
        state->towns[i].recruit_mask_hi = 0;
        state->towns[i].build_mask_lo = 0;
        state->towns[i].build_mask_hi = 0;
    }
    memset(state->enemy_threat, 0, sizeof(state->enemy_threat));
    memset(state->battle_pred, 0, sizeof(state->battle_pred));

    // 1) heroes: total_power / is_garrisoned / has_commander
    for (const auto& [color, ps] : gs.players) {
        for (const auto* hero : ps.getHeroes()) {
            if (!hero) continue;
            int64_t power = mb_calc_army_power(hero);
            for (int i = 0; i < MB_MAX_HEROES; i++) {
                if (state->heroes[i].id == hero->id.getNum() && state->heroes[i].owner == color.getNum()) {
                    state->heroes[i].total_power = (int32_t)power;
                    state->heroes[i].has_commander = hero->getCommander() ? 1 : 0;
                    break;
                }
            }
        }
    }
    // is_garrisoned: getUpperArmy 是驻守英雄 → 置位
    for (const auto& [color, ps] : gs.players) {
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            const auto* upperArmy = town->getUpperArmy();
            const auto* gh = dynamic_cast<const CGHeroInstance*>(upperArmy);
            if (!gh) continue;
            for (int i = 0; i < MB_MAX_HEROES; i++) {
                if (state->heroes[i].id == gh->id.getNum()) {
                    state->heroes[i].is_garrisoned = 1;
                    break;
                }
            }
        }
    }

    // 2) towns: recruit_mask / build_mask
    for (const auto& [color, ps] : gs.players) {
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            int slot = -1;
            for (int i = 0; i < MB_MAX_TOWNS; i++) {
                if (state->towns[i].id == town->id.getNum() && state->towns[i].owner == color.getNum()) {
                    slot = i;
                    break;
                }
            }
            if (slot < 0) continue;
            auto& t = state->towns[slot];

            // recruit_mask: bit = level*2 + upgrade
            uint32_t rlo = 0, rhi = 0;
            const auto& townCreatures = town->getTown()->creatures;
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

            // build_mask: 只算己方城镇 (canBuildStructure 对敌城返回 TOWN_NOT_OWNED 并刷 ERROR)
            // bit = buildings map 索引; 置位: ALLOWED | CANT_BUILD_TODAY | NO_RESOURCES
            uint32_t blo = 0, bhi = 0;
            if (color.getNum() == selfPlayer) {
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

    // 3) players: total_power / weekly_income / relation_to_me
    for (const auto& [color, ps] : gs.players) {
        int pi = color.getNum();
        if (pi < 0 || pi >= MB_MAX_PLAYERS) continue;
        int slot = -1;
        for (int i = 0; i < state->player_count; i++) {
            if (state->players[i].color == pi) { slot = i; break; }
        }
        if (slot < 0) continue;
        auto& p = state->players[slot];

        int64_t totalPower = 0;
        for (const auto* hero : ps.getHeroes())
            if (hero) totalPower += mb_calc_army_power(hero);
        p.total_power = (int32_t)totalPower;

        int64_t weeklyGold = 0;
        for (const auto* town : ps.getTowns()) {
            if (!town) continue;
            auto income = town->dailyIncome();
            weeklyGold += income[EGameResID::GOLD] * 7;
        }
        p.weekly_income = (int32_t)weeklyGold;

        // ENEMIES=0, ALLIES=1, SAME_PLAYER=2 → 映射 0=中立 1=敌对 2=结盟
        PlayerRelations rel = gs.getPlayerRelations(PlayerColor(selfPlayer), PlayerColor(pi));
        if (rel == PlayerRelations::ENEMIES) p.relation_to_me = 1;
        else if (rel == PlayerRelations::ALLIES) p.relation_to_me = 2;
        else p.relation_to_me = 0;
    }

    // 4) enemy_threat[7]: 每敌方玩家总战力 (排除自己)
    {
        int et = 0;
        for (int i = 0; i < state->player_count && et < MB_ENEMY_THREAT; i++) {
            if (state->players[i].color == selfPlayer) continue;
            state->enemy_threat[et++] = state->players[i].total_power;
        }
    }

    // 5) battle_pred[4]: my_power / target_power(最近守卫) / win_prob
    {
        int ah = state->active_hero;
        if (ah >= 0 && ah < MB_MAX_HEROES && state->heroes[ah].id >= 0) {
            int64_t myPower = state->heroes[ah].total_power;
            int64_t targetPower = 0;
            int3 hpos(state->heroes[ah].pos_x, state->heroes[ah].pos_y, state->heroes[ah].pos_z);
            for (const auto* g : gs.guardingCreatures(hpos))
                targetPower += mb_calc_guard_power(g);
            state->battle_pred[0] = (int32_t)myPower;
            state->battle_pred[1] = (int32_t)targetPower;
            if (myPower + targetPower > 0)
                state->battle_pred[2] = (int32_t)(myPower * 100 / (myPower + targetPower));
            state->battle_pred[3] = 0;
        }
    }
}

// ---------------------------------------------------------------------------
// fillState — 同 strategic_state.cpp::fill_strategic_state (去 mines/game_over, selfPlayer 化)
// ---------------------------------------------------------------------------
void ObsBuilder::fillState(CCallback* cb, int selfPlayer, int activeHeroId, MBState& st) {
    auto* gicb = static_cast<CGameInfoCallback*>(cb);
    MBState* state = &st;

    memset(state, 0, sizeof(MBState));

    // Players — 全知直读 gs.players (块锁, 不嵌套)
    {
        const auto& gs0 = gicb->gameState();
        std::shared_lock plock(CGameState::mutex);
        state->player_count = 0;
        for (const auto& [color, ps] : gs0.players) {
            if (state->player_count >= MB_MAX_PLAYERS) break;
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

    // Calendar (绝对天数, 同训练)
    {
        const auto& gs = gicb->gameState();
        std::shared_lock clock(CGameState::mutex);
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

    state->current_player = selfPlayer;

    // Heroes — 全知直读 (独立块锁)
    {
        const auto& gs2 = gicb->gameState();
        std::shared_lock hlock(CGameState::mutex);
        for (int i = 0; i < MB_MAX_HEROES; i++) state->heroes[i].id = -1;
        int hi = 0;
        for (const auto& [color, ps] : gs2.players) {
            int pi = color.getNum();
            for (const auto* hero : ps.getHeroes()) {
                if (hi >= MB_MAX_HEROES) break;
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

    // B 态势感知 (内部自带锁)
    mb_fill_exploration(state, gicb->gameState(), selfPlayer, activeHeroId);

    // Passability — N-start CW, visitablePos 坐标系 (独立块锁)
    if (state->active_hero >= 0 && state->heroes[state->active_hero].id >= 0) {
        std::shared_lock slock(CGameState::mutex);
        // 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
        static const int32_t dx[8] = {0,1,1,1,0,-1,-1,-1};
        static const int32_t dy[8] = {-1,-1,0,1,1,1,0,-1};
        const CGHeroInstance* hero = dynamic_cast<const CGHeroInstance*>(gicb->gameState().getObjInstance(ObjectInstanceID(state->heroes[state->active_hero].id)));
        int3 hpos(state->heroes[state->active_hero].pos_x, state->heroes[state->active_hero].pos_y, state->heroes[state->active_hero].pos_z);
        if (hero) hpos = hero->visitablePos();
        const TerrainTile* hposTile = gicb->getTile(hpos, false);
        for (int d = 0; d < 8; d++) {
            int3 target(hpos.x + dx[d], hpos.y + dy[d], hpos.z);
            const TerrainTile* tt = gicb->getTile(target, false);
            if (!tt) {
                state->passable[d] = 0;
            } else {
                state->passable[d] = tt->isClear(hposTile) ? 1 : 0;
            }
        }
    } else {
        memset(state->passable, 0, sizeof(state->passable));
    }

    // Towns — 全知直读 (独立块锁; 空槽 id=-1, Python 展平判 t.id != 0 → 空槽行写 -1, 必须复刻)
    {
        const auto& gs3 = gicb->gameState();
        std::shared_lock tlock(CGameState::mutex);
        for (int i = 0; i < MB_MAX_TOWNS; i++) state->towns[i].id = -1;
        int ti = 0;
        for (const auto& [color, ps] : gs3.players) {
            int pi = color.getNum();
            for (const auto* town : ps.getTowns()) {
                if (ti >= MB_MAX_TOWNS) break;
                auto& t = state->towns[ti++];
                t.id = town->id.getNum();
                t.owner = pi;
                t.pos_x = town->pos.x;
                t.pos_y = town->pos.y;
                t.pos_z = town->pos.z;
                t.buildings = 0;
                memset(t.garrison, 0, sizeof(t.garrison));
                // 驻军: getUpperArmy (敌城=守军, 无 visiting=城防)
                {
                    const CArmedInstance* garArmy = town->getUpperArmy();
                    for (int gi = 0; gi < 7; gi++) {
                        auto* gst = garArmy ? garArmy->getStackPtr(SlotID(gi)) : nullptr;
                        t.garrison[gi] = gst ? gst->getCount() : 0;
                    }
                }
                t.gold_income = 0;
                t.recruit_mask_lo = 0; t.recruit_mask_hi = 0;
                t.build_mask_lo = 0; t.build_mask_hi = 0;
            }
        }
    }

    // H.8: target_list (内部锁)
    mb_fill_target_list(state, gicb->gameState());

    // I.2: next_dir BFS (独立锁)
    mb_fill_next_dir(state, gicb);

    // H.5: v3 扩展字段 (内部锁)
    mb_fill_v3_fields(state, gicb, selfPlayer);

    // 地形栅格 (独立锁, 写内存不落盘)
    mb_fill_terrain_grid_mem(state, gicb);
}

// ---------------------------------------------------------------------------
// flatten — 3464 obs (逐行移植 strategic_env.py::_strategic_state_to_obs + H.8 归一化)
// ---------------------------------------------------------------------------
std::array<float, MB_OBS_DIM> ObsBuilder::flatten(const MBState& st) {
    std::array<float, MB_OBS_DIM> obs{};
    int idx = 0;

    // --- Global (8) ---
    obs[idx++] = (float)st.day;
    obs[idx++] = (float)st.week;
    obs[idx++] = (float)st.month;
    obs[idx++] = (float)st.current_player;
    obs[idx++] = (float)st.map_width;
    obs[idx++] = (float)st.map_height;
    obs[idx++] = (float)st.has_underground;
    obs[idx++] = (float)st.player_count;

    // --- Players (8 * 15) — 空槽判定: pi < player_count ---
    for (int pi = 0; pi < MB_MAX_PLAYERS; pi++) {
        const MBPlayer& p = st.players[pi];
        if (pi < st.player_count) {
            obs[idx++] = (float)p.color;
            obs[idx++] = (float)p.human;
            obs[idx++] = (float)p.gold;
            obs[idx++] = (float)p.wood;
            obs[idx++] = (float)p.mercury;
            obs[idx++] = (float)p.ore;
            obs[idx++] = (float)p.sulfur;
            obs[idx++] = (float)p.crystal;
            obs[idx++] = (float)p.gems;
            obs[idx++] = (float)p.hero_count;
            obs[idx++] = (float)p.town_count;
            obs[idx++] = (float)p.alive;
            obs[idx++] = (float)p.total_power;
            obs[idx++] = (float)p.weekly_income;
            obs[idx++] = (float)p.relation_to_me;
        } else {
            idx += 15;
        }
    }

    // --- Heroes (8 * 26) — 空槽判定: id >= 0 ---
    for (int hi = 0; hi < MB_MAX_HEROES; hi++) {
        const MBHero& h = st.heroes[hi];
        if (h.id >= 0) {
            obs[idx++] = (float)h.id;
            obs[idx++] = (float)h.owner;
            obs[idx++] = (float)h.pos_x;
            obs[idx++] = (float)h.pos_y;
            obs[idx++] = (float)h.pos_z;
            obs[idx++] = (float)h.movement;
            obs[idx++] = (float)h.max_movement;
            obs[idx++] = (float)h.level;
            obs[idx++] = (float)h.attack;
            obs[idx++] = (float)h.defense;
            obs[idx++] = (float)h.power;
            obs[idx++] = (float)h.knowledge;
            obs[idx++] = (float)h.mana;
            obs[idx++] = (float)h.max_mana;
            obs[idx++] = (float)h.exp;
            for (int ai = 0; ai < 7; ai++)
                obs[idx++] = (float)h.army_count[ai];
            obs[idx++] = (float)h.in_battle;
            obs[idx++] = (float)h.total_power;
            obs[idx++] = (float)h.is_garrisoned;
            obs[idx++] = (float)h.has_commander;
        } else {
            idx += 26;
        }
    }

    // --- Towns (8 * 18) — 空槽判定: id != 0 (训练 quirk: C++ 空槽 id=-1 → -1 行写入 obs!) ---
    for (int ti = 0; ti < MB_MAX_TOWNS; ti++) {
        const MBTown& t = st.towns[ti];
        if (t.id != 0) {
            obs[idx++] = (float)t.id;
            obs[idx++] = (float)t.owner;
            obs[idx++] = (float)t.pos_x;
            obs[idx++] = (float)t.pos_y;
            obs[idx++] = (float)t.pos_z;
            obs[idx++] = (float)t.buildings;
            for (int ai = 0; ai < 7; ai++)
                obs[idx++] = (float)t.garrison[ai];
            obs[idx++] = (float)t.gold_income;
            obs[idx++] = (float)t.recruit_mask_lo;
            obs[idx++] = (float)t.recruit_mask_hi;
            obs[idx++] = (float)t.build_mask_lo;
            obs[idx++] = (float)t.build_mask_hi;
        } else {
            idx += 18;
        }
    }

    // --- Local window (15*15*3=675) — ch 外层, 行主序 ---
    for (int ch = 0; ch < MB_LOCAL_CH; ch++)
        for (int li = 0; li < MB_LOCAL_WIN; li++)
            for (int lj = 0; lj < MB_LOCAL_WIN; lj++)
                obs[idx++] = (float)st.local_tiles[ch][li][lj];

    // --- Global explored (32*32*2=2048) — z 外层 ---
    for (int z = 0; z < MB_MAX_LEVELS; z++)
        for (int gy = 0; gy < MB_GLOBAL_GRID; gy++)
            for (int gx = 0; gx < MB_GLOBAL_GRID; gx++)
                obs[idx++] = (float)st.global_explored[z][gy][gx];

    // idx 此处 = 3203; 以下全部固定偏移
    // --- Active hero (8) @3203 ---
    obs[3203] = (float)st.active_hero;

    // --- Passable (8) @3211 ---
    for (int di = 0; di < 8; di++)
        obs[3211 + di] = (float)st.passable[di];

    // --- Nav (32) @3219 — MBState 无 nav 字段, 训练恒 0 → 保持 0 ---

    // --- Target list (64) @3251 ---
    for (int i = 0; i < MB_TARGET_LIST; i++)
        for (int j = 0; j < MB_TARGET_DIM; j++)
            obs[3251 + i * MB_TARGET_DIM + j] = (float)st.target_list[i][j];

    // --- Enemy threat (7) @3315 ---
    for (int i = 0; i < MB_ENEMY_THREAT; i++)
        obs[3315 + i] = (float)st.enemy_threat[i];

    // --- Battle pred (4) @3322 ---
    for (int i = 0; i < MB_BATTLE_PRED; i++)
        obs[3322 + i] = (float)st.battle_pred[i];

    // --- Events (4) @3326 (fill 恒 0) ---
    for (int i = 0; i < MB_EVENTS_SIZE; i++)
        obs[3326 + i] = (float)st.events[i];

    // --- Reserved (134) @3330 — 前 16 用: next_dir[8] + diagnostics[8] ---
    for (int i = 0; i < 16; i++)
        obs[3330 + i] = (float)st.reserved[i];

    // --- H.8 归一化 (大数值字段) ---
    // build_mask_lo/hi (336 + ti*18 + 16/+17) / 2^31
    for (int ti = 0; ti < MB_MAX_TOWNS; ti++) {
        obs[336 + ti * 18 + 16] /= 2147483648.0f;
        obs[336 + ti * 18 + 17] /= 2147483648.0f;
    }
    // log1p(max(x,0)): players gold(+2)/total_power(+12)/weekly_income(+13);
    //                  heroes movement(+5)/max_movement(+6)/exp(+14)/total_power(+23);
    //                  enemy_threat 3315-3321; battle_pred 3322-3325
    for (int pi = 0; pi < MB_MAX_PLAYERS; pi++) {
        int b = 8 + pi * 15;
        for (int c : {b + 2, b + 12, b + 13}) {
            float v = std::max(obs[c], 0.0f);
            obs[c] = std::log1p(v);
        }
    }
    for (int hi = 0; hi < MB_MAX_HEROES; hi++) {
        int b = 128 + hi * 26;
        for (int c : {b + 5, b + 6, b + 14, b + 23}) {
            float v = std::max(obs[c], 0.0f);
            obs[c] = std::log1p(v);
        }
    }
    for (int c = 3315; c < 3322; c++) {
        float v = std::max(obs[c], 0.0f);
        obs[c] = std::log1p(v);
    }
    for (int c = 3322; c < 3326; c++) {
        float v = std::max(obs[c], 0.0f);
        obs[c] = std::log1p(v);
    }

    return obs;
}

// ---------------------------------------------------------------------------
// terrainCHW — HWC uint8 (21,21,4) → CHW float /255 (同训练 _build_terrain_grid)
// ---------------------------------------------------------------------------
std::array<float, MB_TERRAIN_FLOAT> ObsBuilder::terrainCHW(const MBState& st) {
    std::array<float, MB_TERRAIN_FLOAT> out{};
    constexpr int plane = MB_GRID_SIZE * MB_GRID_SIZE;  // 441
    for (int ch = 0; ch < MB_GRID_CH; ch++)
        for (int r = 0; r < MB_GRID_SIZE; r++)
            for (int c = 0; c < MB_GRID_SIZE; c++)
                out[ch * plane + r * MB_GRID_SIZE + c] =
                    (float)st.terrain_grid_hwc[(r * MB_GRID_SIZE + c) * MB_GRID_CH + ch] / 255.0f;
    return out;
}
