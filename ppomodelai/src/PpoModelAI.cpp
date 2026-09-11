#include "StdInc.h"
#include "PpoModelAI.h"

#include "callback/CCallback.h"
#include "callback/CDynLibHandler.h"
#include "battle/BattleAction.h"
#include "battle/CUnitState.h"
#include "CStack.h"
#include "battle/CPlayerBattleCallback.h"
#include "constants/EntityIdentifiers.h"
#include "constants/Enumerations.h"
#include "constants/NumericConstants.h"
#include "GameConstants.h"
#include "gameState/CGameState.h"
#include "int3.h"
#include "mapObjects/CGObjectInstance.h"
#include "mapObjects/CGHeroInstance.h"
#include "mapObjects/CGTownInstance.h"
#include "mapObjects/army/CArmedInstance.h"
#include "mapObjects/army/CStackInstance.h"
#include "mapping/TerrainTile.h"
#include "TerrainHandler.h"
#include "vstd/CLoggerBase.h"
#include "pathfinder/PathfinderCache.h"
#include "pathfinder/PathfinderOptions.h"
#include "pathfinder/CGPathNode.h"

#include <atomic>
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <limits>
#include <thread>

VCMI_LIB_NAMESPACE_BEGIN

// 直通 stderr 打点 (2026-09-11): 本 DLL 的 logAi 输出丢失 (client log 中
// PpoModelAI 零命中), teal 卡死时无法观测 yourTurn 内部进度.
// stderr 无缓冲 + 强制 flush, 配合客户端 stdout/stderr 管道可实时取证.
#define AI_TRACE(...) do { \
    fprintf(stderr, "[ModelAI p%d] ", static_cast<int>(playerID.getNum())); \
    fprintf(stderr, __VA_ARGS__); \
    fprintf(stderr, "\n"); \
    fflush(stderr); \
} while(0)

// =============================================================================
// v5 动作 0-7 方向表 (训练侧 strategic_env.py 语义, N-start 顺时针):
//   0=N 1=NE 2=E 3=SE 4=S 5=SW 6=W 7=NW
// 2026-09-11 修复: 旧部署版误用 E-start 表 (0=Right), 与训练动作语义错位 45 度.
// =============================================================================
static const int DIR_DX[8] = { 0, 1, 1, 1, 0, -1, -1, -1 };
static const int DIR_DY[8] = { -1, -1, 0, 1, 1, 1, 0, -1 };

// =============================================================================
// 动作 11-24 辅助 (移植自 vcmi/AI/MMAI/AAI/AAI.cpp, selfPlayer 参数化:
// 训练版硬编码 PlayerColor(0), 部署版任意玩家色)
// =============================================================================
namespace {

int64_t distSq(const int3& a, const int3& b)
{
    int64_t dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return dx * dx + dy * dy + dz * dz;
}

// 最近友方英雄 (排除 cur 自己; getHeroesInfo 只含己方英雄, 仍按 owner 过滤)
const CGHeroInstance* nearestAllyHero(const std::vector<const CGHeroInstance*>& heroes, const CGHeroInstance* cur, int selfPlayer)
{
    const CGHeroInstance* best = nullptr;
    int64_t bestDist = std::numeric_limits<int64_t>::max();
    for (const auto* h : heroes)
    {
        if (!h || h == cur) continue;
        if (h->getOwner() != PlayerColor(selfPlayer)) continue;  // 跳过敌方
        int64_t d = distSq(h->pos, cur->pos);
        if (d < bestDist) { bestDist = d; best = h; }
    }
    return best;
}

// 最近己方城镇
const CGTownInstance* nearestOwnTown(CCallback* cb, const CGHeroInstance* cur, int selfPlayer)
{
    const CGTownInstance* best = nullptr;
    int64_t bestDist = std::numeric_limits<int64_t>::max();
    for (const auto* t : cb->getTownsInfo())
    {
        if (!t || t->getOwner() != PlayerColor(selfPlayer)) continue;  // 跳过敌方
        int64_t d = distSq(t->pos, cur->pos);
        if (d < bestDist) { bestDist = d; best = t; }
    }
    return best;
}

// 最近可交互对象 (getAllVisitableObjs 已过滤可见/可访问/非 EVENT)
// 排除: dist==0 (英雄自身格)
const CGObjectInstance* nearestInteractable(CCallback* cb, const CGHeroInstance* cur, int selfPlayer)
{
    const CGObjectInstance* best = nullptr;
    int64_t bestDist = std::numeric_limits<int64_t>::max();
    for (const auto* obj : cb->getAllVisitableObjs())
    {
        if (!obj || obj->ID == Obj::HERO) continue;
        auto owner = obj->getOwner();
        if (owner != PlayerColor(selfPlayer) && owner != PlayerColor::NEUTRAL) continue;  // 跳过敌方
        int3 op = obj->visitablePos();
        int64_t d = distSq(op, cur->pos);
        if (d == 0) continue;  // 跳过英雄自身所在格
        if (d < bestDist) { bestDist = d; best = obj; }
    }
    return best;
}

// INTERACT 目标: 优先最近己方城镇 (进城/招兵/建造/驻守), 其次最近可交互对象
const CGObjectInstance* interactTarget(CCallback* cb, const CGHeroInstance* cur, int selfPlayer)
{
    const CGTownInstance* bestTown = nullptr;
    int64_t bestTownDist = std::numeric_limits<int64_t>::max();
    for (const auto* t : cb->getTownsInfo())
    {
        if (!t || t->getOwner() != PlayerColor(selfPlayer)) continue;
        int64_t d = distSq(t->pos, cur->pos);
        if (d < bestTownDist) { bestTownDist = d; bestTown = t; }
    }
    // 城镇在 3 格内 → 优先城镇
    if (bestTown && bestTownDist <= 9)
        return bestTown;
    auto obj = nearestInteractable(cb, cur, selfPlayer);
    if (obj) return obj;
    return bestTown;  // 兜底城镇
}

// 朝目标方向移动一格 (8 方向 N-start CW) — moveHero 单格版只允许相邻格
// 返回是否发出了移动请求
bool moveOneStepToward(CCallback* cb, const CGHeroInstance* hero, const int3& target)
{
    if (!cb || !hero) return false;
    int dx = target.x - hero->pos.x;
    int dy = target.y - hero->pos.y;
    int dz = target.z - hero->pos.z;
    if (dz != 0) return false;  // 跨层无法单格逼近
    if (dx == 0 && dy == 0) return false;

    // 选移动方向: 与 (dx,dy) 夹角最小的 8 方向
    int bestDir = -1;
    int64_t bestDot = std::numeric_limits<int64_t>::min();
    for (int d = 0; d < 8; d++)
    {
        int64_t dot = (int64_t)dx * DIR_DX[d] + (int64_t)dy * DIR_DY[d];
        if (dot > bestDot) { bestDot = dot; bestDir = d; }
    }
    if (bestDir < 0) return false;
    try {
        int3 targetPos(hero->pos.x + DIR_DX[bestDir], hero->pos.y + DIR_DY[bestDir], hero->pos.z);
        cb->moveHero(hero, targetPos, false);
        return true;
    } catch (...) { return false; }
}

// 执行动作 11-24 (分兵/合兵/换兵/招兵/建造/驻守/招募英雄/高层移动)
int3 executeAdvancedAction(CCallback* cb, int a, const CGHeroInstance* cur, int selfPlayer)
{
    const int3 noTarget(-1, -1, -1);
    if (!cb || !cur) return noTarget;

    const auto heroes = cb->getHeroesInfo();

    switch (a)
    {
    case 11: // SPLIT_1OF3: 分 1/3 兵力给最近友方英雄
    case 12: // SPLIT_1OF2: 分 1/2 兵力给最近友方英雄
    {
        auto dst = nearestAllyHero(heroes, cur, selfPlayer);
        if (!dst) return noTarget;
        for (const auto& [slot, stack] : cur->Slots())
        {
            if (stack->getCreatureID() == CreatureID::NONE) continue;
            int total = stack->getCount();
            int give = (a == 11) ? total / 3 : total / 2;
            if (give <= 0) continue;
            auto freeSlots = dst->getFreeSlots();
            if (freeSlots.empty()) return noTarget;
            cb->splitStack(cur, dst, slot, freeSlots.front(), give);
            break;
        }
        break;
    }
    case 13: // SPLIT_ALL: 全部兵力给最近友方英雄
    {
        auto dst = nearestAllyHero(heroes, cur, selfPlayer);
        if (!dst) return noTarget;
        for (const auto& [slot, stack] : cur->Slots())
        {
            if (stack->getCreatureID() == CreatureID::NONE) continue;
            cb->bulkMoveArmy(cur->id, dst->id, slot);
            break;
        }
        break;
    }
    case 14: // MERGE_FROM: 从最近友方英雄合并全部兵力到当前英雄
    {
        auto src = nearestAllyHero(heroes, cur, selfPlayer);
        if (!src) return noTarget;
        for (const auto& [slot, stack] : src->Slots())
        {
            if (stack->getCreatureID() == CreatureID::NONE) continue;
            auto targetSlot = cur->getSlotFor(stack->getCreatureID());
            if (targetSlot.validSlot())
                cb->mergeStacks(src, cur, slot, targetSlot);
            else
            {
                auto freeSlots = cur->getFreeSlots();
                if (freeSlots.empty()) break;
                cb->bulkMoveArmy(src->id, cur->id, slot);
            }
        }
        break;
    }
    case 15: // SWAP_ARMY: 与最近友方英雄逐槽交换兵力
    {
        auto other = nearestAllyHero(heroes, cur, selfPlayer);
        if (!other) return noTarget;
        for (int i = 0; i < GameConstants::ARMY_SIZE; i++)
        {
            SlotID s(i);
            if (!cur->slotEmpty(s) || !other->slotEmpty(s))
                cb->swapCreatures(cur, other, s, s);
        }
        break;
    }
    case 16: // RECRUIT_1: 最近己方城镇招最低级可招兵×1
    case 17: // RECRUIT_2: 最近己方城镇招最高级可招兵×1
    case 18: // RECRUIT_3: 最近己方城镇全部可招兵各×1
    {
        auto town = nearestOwnTown(cb, cur, selfPlayer);
        if (!town) return noTarget;
        const CArmedInstance* dst = town->getUpperArmy();
        const auto& creatures = town->creatures;
        if (a == 16 || a == 17)
        {
            int from = 0, to = (int)creatures.size() - 1, step = 1;
            if (a == 17) { from = to; to = 0; step = -1; }
            for (int i = from; step > 0 ? i <= to : i >= to; i += step)
            {
                if (i < 0 || i >= (int)creatures.size()) continue;
                if (!creatures[i].second.empty())
                {
                    cb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);
                    break;
                }
            }
        }
        else
        {
            for (int i = 0; i < (int)creatures.size(); i++)
            {
                if (!creatures[i].second.empty())
                    cb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);
            }
        }
        break;
    }
    case 19: // BUILD_1: 大厅链第一个未建
    case 20: // BUILD_2: 兵种链第一个未建
    case 21: // BUILD_3: 防御链第一个未建
    {
        auto town = nearestOwnTown(cb, cur, selfPlayer);
        if (!town) return noTarget;
        std::vector<BuildingID> chain;
        if (a == 19)
            chain = { BuildingID::VILLAGE_HALL, BuildingID::TOWN_HALL, BuildingID::CITY_HALL, BuildingID::CAPITOL };
        else if (a == 20)
            chain = { BuildingID::DWELL_LVL_1, BuildingID::DWELL_LVL_2, BuildingID::DWELL_LVL_3,
                      BuildingID::DWELL_LVL_4, BuildingID::DWELL_LVL_5, BuildingID::DWELL_LVL_6, BuildingID::DWELL_LVL_7 };
        else
            chain = { BuildingID::FORT, BuildingID::CITADEL, BuildingID::CASTLE };
        for (const auto& b : chain)
        {
            if (cb->canBuildStructure(town, b) == EBuildingState::ALLOWED)
            {
                cb->buildBuilding(town, b);
                break;
            }
        }
        break;
    }
    case 22: // GARRISON: 当前英雄驻守最近己方城镇
    {
        auto town = nearestOwnTown(cb, cur, selfPlayer);
        if (!town) return noTarget;
        // 英雄必须 visiting 城镇才能 swapGarrisonHero; 未进城先 moveHero 到城镇入口
        if (!cur->getVisitedTown() || cur->getVisitedTown() != town)
        {
            int3 tp = town->visitablePos();
            int3 standPos = cur->convertFromVisitablePos(tp);
            cb->moveHero(cur, standPos, false);
            // 锁内等 2s 让进城完成 (query 自动应答)
            for (int i = 0; i < 20; i++) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                if (cur->getVisitedTown() == town)
                    break;
            }
            if (!cur->getVisitedTown())
                return noTarget;
        }
        cb->swapGarrisonHero(town);
        break;
    }
    case 23: // RECRUIT_HERO: 最近己方城镇招募第一个可用新英雄
    {
        auto town = nearestOwnTown(cb, cur, selfPlayer);
        if (!town) return noTarget;
        auto avail = cb->getAvailableHeroes(town);
        if (avail.empty()) return noTarget;
        cb->recruitHero(town, avail.front());
        break;
    }
    case 24: // MOVE_TO: 朝最近可交互对象方向逐格移动
    {
        auto target = nearestInteractable(cb, cur, selfPlayer);
        if (!target) return noTarget;
        int3 tp = target->visitablePos();
        int3 standPos = cur->convertFromVisitablePos(tp);
        // 已相邻: 直接 moveHero 到目标可站格触发交互; 否则朝方向走一格
        if (distSq(standPos, cur->pos) <= 2)
        {
            cb->moveHero(cur, standPos, false);
            return standPos;
        }
        if (moveOneStepToward(cb, cur, standPos))
            return standPos;
        return noTarget;
    }
    default:
        break;
    }
    return noTarget;
}

} // namespace

PpoModelAI::PpoModelAI() {}
PpoModelAI::~PpoModelAI() = default;

// 兜底/战斗收尾共用的延迟 endTurn (detached 线程替代 TBB AsyncRunner;
// ML fix 08-27: 500ms 后 CAS 抢占 + 战斗检查 + 应答 query + endTurn)
void PpoModelAI::scheduleDelayedEndTurn(int delayMs)
{
    std::thread([this, delayMs]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(delayMs));
        bool expected = true;
        if (pending_endturn.compare_exchange_strong(expected, false) && !in_battle.load()) {
            cb->waitTillRealize = false;
            cb->selectionMade(0, last_query);
            cb->endTurn();
            cb->waitTillRealize = true;
            AI_TRACE("delayed endTurn done");
        }
    }).detach();
}

void PpoModelAI::initGameInterface(std::shared_ptr<Environment> ENV, std::shared_ptr<CCallback> CB, AICombatOptions aiCombatOptions)
{
    cb = CB;
    env = ENV;
    cbc = CB;  // battleAI 初始化需要 (CAdventureAI 基类成员)
    this->aiCombatOptions = aiCombatOptions;
    human = false;
    playerID = *cb->getPlayerID();
    cb->waitTillRealize = true;      // AAI 同款: 游戏运行时 cb 调用同步等待 realize
    cb->unlockGsWhenWaiting = true;

    logAi->info("PpoModelAI: initializing for player %d", playerID.getNum());

    try {
        // v5 双输入模型 (mq-2 导出, 对拍 maxdiff=1.43e-06 非退化)
        model = &ModelInference::instance("D:/Bigdata/hero3_fresh/rl_model_v5_0911.onnx");
        AI_TRACE("initGameInterface: shared v5 model ready");
        logAi->info("PpoModelAI: v5 model loaded successfully");
    } catch (const std::exception& e) {
        model = nullptr;
        AI_TRACE("initGameInterface: FAILED to load model: %s", e.what());
        logAi->error("PpoModelAI: failed to load model: %s", e.what());
    }
}

std::string PpoModelAI::getBattleAIName() const
{
    return "BattleAI";
}

void PpoModelAI::yourTurn(QueryID queryID)
{
    const auto t0 = std::chrono::steady_clock::now();
    auto elapsedMs = [&t0]() -> long long {
        return std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - t0).count();
    };

    AI_TRACE("yourTurn enter (query=%d)", queryID.getNum());
    logAi->info("PpoModelAI: yourTurn (query=%d, player=%d)", queryID.getNum(), playerID.getNum());
    last_query = queryID;

    if (!model || !cb) {
        AI_TRACE("no model loaded, immediate endTurn");
        logAi->warn("PpoModelAI: no model loaded, ending turn");
        cb->selectionMade(0, queryID);
        cb->endTurn();
        return;
    }

    const CGHeroInstance* cur = nullptr;
    std::vector<const CGHeroInstance*> heroes;

    try {
        cb->waitTillRealize = false;

        // 定位当前决策英雄 (curHeroId + fallback 第一个己方英雄)
        heroes = cb->getHeroesInfo();
        for (const auto* h : heroes) {
            if (h->id == curHeroId) { cur = h; break; }
        }
        if (!cur && !heroes.empty()) {
            cur = heroes.front();
            curHeroId = cur->id;
        }
        if (!cur) {
            AI_TRACE("no heroes, immediate endTurn");
            logAi->info("PpoModelAI: no heroes, ending turn");
            cb->selectionMade(0, queryID);
            cb->endTurn();
            return;
        }

        // ===== 3464 obs + terrain → v5 推理 =====
        AI_TRACE("fillState begin (hero=%d)", curHeroId.getNum());
        MBState st;
        ObsBuilder::fillState(cb.get(), playerID.getNum(), curHeroId.getNum(), st);
        auto obs = ObsBuilder::flatten(st);
        auto terrain = ObsBuilder::terrainCHW(st);
        AI_TRACE("obs ready (%lld ms)", elapsedMs());

        int action = model->predict(obs, terrain);
        AI_TRACE("predict action=%d (%lld ms)", action, elapsedMs());
        logAi->info("PpoModelAI: action=%d hero=%d obs[0..3]=%.0f %.0f %.0f %.0f",
            action, curHeroId.getNum(), obs[0], obs[1], obs[2], obs[3]);

        // ===== 动作分发 (v5 25 动作语义) =====
        if (action >= 0 && action <= 7) {
            // 移动: N-start CW 方向 (0=N..7=NW)
            if (cur->movementPointsRemaining() <= 0) {
                AI_TRACE("hero has no movement points, skip move");
            } else {
                // VCMI 双坐标语义 (gui9 实测踩坑):
                //   hero->pos (anchorPos) = 模板锚点格; 交互格 visitablePos() = pos - getVisitableOffset().
                //   server (CGameHandler::moveHero) 对 dst 再做 convertToVisitablePos(dst) = dst - offset,
                //   即请求参数 dst 是 anchor 语义. tile/pathfinder 判定用 visitable 语义目标.
                int3 heroVisitable = cur->visitablePos();
                int3 visitableDest = heroVisitable + int3(DIR_DX[action], DIR_DY[action], 0);
                int3 dest = visitableDest + cur->getVisitableOffset();  // anchor 语义, 请求参数
                AI_TRACE("move hero %d: action=%d dir=(%d,%d) visitable (%d,%d)->(%d,%d)",
                    cur->id.getNum(), action, DIR_DX[action], DIR_DY[action],
                    heroVisitable.x, heroVisitable.y, visitableDest.x, visitableDest.y);

                // server 判定格 = dst - offset = visitableDest
                const TerrainTile* tile = cb->getTile(visitableDest, false);
                const CGObjectInstance* topObj = tile ? cb->getTopObj(visitableDest) : nullptr;

                // server 同款拒绝条件: 岩石地形 / blocked 且非 visitable
                bool tileReject = !tile
                    || !tile->getTerrain()->isPassable()
                    || (tile->blocked() && !tile->visitable());

                // simultaneous turns 下目标格有其他玩家所属对象 → 拒绝
                bool simTurnReject = topObj
                    && topObj->getOwner().isValidPlayer()
                    && topObj->getOwner() != cur->tempOwner;

                // pathfinder 校验: dest 本回合剩余移动力内可达 (turns==0)
                PathfinderOptions pOpts(*cb);
                PathfinderCache pathCache(cb.get(), pOpts);
                auto paths = pathCache.getPathsInfo(cur);
                const CGPathNode* node = paths->getPathInfo(visitableDest);

                if (tileReject || simTurnReject || !node || !node->reachable() || node->turns > 0) {
                    AI_TRACE("dest (%d,%d) rejected (tile=%d simTurn=%d path turns=%u accessible=%d) - skip move",
                        visitableDest.x, visitableDest.y,
                        tileReject ? 1 : 0, simTurnReject ? 1 : 0,
                        node ? static_cast<unsigned>(node->turns) : 255u,
                        node ? static_cast<int>(node->accessible) : -1);
                } else {
                    try {
                        cb->moveHero(cur, dest, false, EPathfindingLayer::LAND);
                        // 等移动实现 (AAI 同款 3×100ms 轮询)
                        for (int i = 0; i < 3; i++) {
                            std::this_thread::sleep_for(std::chrono::milliseconds(100));
                            auto p = cur->pos;
                            if (p.x == dest.x && p.y == dest.y && p.z == dest.z)
                                break;
                        }
                        AI_TRACE("moveHero request sent");
                    } catch (const std::exception& e) {
                        AI_TRACE("move failed: %s", e.what());
                        logAi->warn("PpoModelAI: move failed: %s", e.what());
                    }
                }
            }
        } else if (action == 8) {
            // INTERACT: 相邻则一步交互 (拾取/占矿/进城), 否则朝目标走一格 (逐格逼近)
            const CGHeroInstance* heroPtr = cur;
            std::thread([this, heroPtr]() {
                std::shared_lock gsLock(CGameState::mutex);
                try {
                    auto target = interactTarget(cb.get(), heroPtr, playerID.getNum());
                    if (target) {
                        int3 tp = target->visitablePos();
                        int3 standPos = heroPtr->convertFromVisitablePos(tp);
                        if (standPos == heroPtr->pos) {
                            cb->moveHero(heroPtr, tp, false);  // 已站可站格: 移到对象格触发交互
                        } else if (distSq(standPos, heroPtr->pos) <= 2) {
                            cb->moveHero(heroPtr, standPos, false);  // 相邻: 一步到位
                        } else {
                            moveOneStepToward(cb.get(), heroPtr, standPos);  // 远: 朝方向走一格
                        }
                        // 锁内等 2s 让移动实现
                        for (int i = 0; i < 20; i++) {
                            std::this_thread::sleep_for(std::chrono::milliseconds(100));
                            auto p = heroPtr->pos;
                            if (p.x == standPos.x && p.y == standPos.y && p.z == standPos.z)
                                break;
                        }
                    }
                } catch (...) {}
            }).join();  // 主线程等执行线程完成 (内含最多 2s 等待)
            cb->waitTillRealize = true;
            AI_TRACE("interact done");
        } else if (action == 9) {
            // NEXT_HERO: 切换到下一个己方英雄 (heroes 序 +1 取模)
            if (!heroes.empty()) {
                int idx = 0;
                for (int i = 0; i < (int)heroes.size(); i++) {
                    if (heroes[i]->id == curHeroId) { idx = i; break; }
                }
                curHeroId = heroes[(idx + 1) % (int)heroes.size()]->id;
                AI_TRACE("next hero -> %d", curHeroId.getNum());
            }
        } else if (action >= 11 && action <= 24) {
            // 高层动作: 分兵/合兵/换兵/招兵/建造/驻守/招募英雄/高层移动
            const CGHeroInstance* heroPtr = cur;
            const int a = action;
            std::thread([this, a, heroPtr]() {
                int3 targetPos(-1, -1, -1);
                {
                    std::shared_lock gsLock(CGameState::mutex);
                    try {
                        targetPos = executeAdvancedAction(cb.get(), a, heroPtr, playerID.getNum());
                    } catch (...) {}
                }
                // MOVE_TO: 锁外等 2s 让移动实现
                if (a == 24 && targetPos.x >= 0) {
                    for (int i = 0; i < 20; i++) {
                        std::this_thread::sleep_for(std::chrono::milliseconds(100));
                        auto p = heroPtr->pos;
                        if (p.x == targetPos.x && p.y == targetPos.y && p.z == targetPos.z)
                            break;
                    }
                }
            }).join();
            cb->waitTillRealize = true;
            AI_TRACE("advanced action %d done", action);
        }
        // action == 10 (END_TURN) 或未知: 无操作, 直接走延迟 endTurn
    } catch (const std::exception& e) {
        // 兜底: 任何异常都必须结束回合, 防止 AI 回合卡死全局
        AI_TRACE("EXCEPTION: %s — fallback endTurn", e.what());
        logAi->error("PpoModelAI: yourTurn exception: %s", e.what());
        try {
            cb->selectionMade(0, queryID);
            cb->endTurn();
        } catch (...) {}
        return;
    }

    // ===== ML fix (08-27): 延迟 endTurn =====
    // 不立即 endTurn — 守卫战斗触发时 endTurn 被服务器拒 ("has to answer queries").
    // 挂起回合: 战斗由 battleEnd 回调收尾; 无战斗由兜底线程 500ms 后 endTurn.
    pending_endturn = true;
    scheduleDelayedEndTurn(500);
    cb->waitTillRealize = true;
    AI_TRACE("yourTurn leave (%lld ms), endTurn pending", elapsedMs());
}

// ===== Battle lifecycle (AAI 同款: 创建/释放 BattleAI + in_battle 维护) =====

void PpoModelAI::battleStart(const BattleID& battleID, const CCreatureSet* army1, const CCreatureSet* army2, int3 tile, const CGHeroInstance* hero1, const CGHeroInstance* hero2, BattleSide side, bool replayAllowed)
{
    AI_TRACE("battleStart (side=%d)", static_cast<int>(side));
    assert(!battleAI);
    assert(cbc);

    battleAI = CDynLibHandler::getNewBattleAI(getBattleAIName());
    battleAI->initBattleInterface(env, cbc, aiCombatOptions);
    battleAI->battleStart(battleID, army1, army2, tile, hero1, hero2, side, replayAllowed);
    in_battle = true;
}

void PpoModelAI::battleEnd(const BattleID& battleID, const BattleResult* br, QueryID queryID)
{
    AI_TRACE("battleEnd (query=%d)", queryID.getNum());
    in_battle = false;

    if (battleAI) {
        battleAI->battleEnd(battleID, br, queryID);
        battleAI.reset();
    }

    // ML fix (08-27): 战斗结束收尾挂起的回合 (守卫战斗场景: yourTurn 不 endTurn, 这里补上)
    bool expected = true;
    if (pending_endturn.compare_exchange_strong(expected, false))
        scheduleDelayedEndTurn(500);
}

// ===== Battle callbacks — 转发 BattleAI (判空保护; 缺失时防御性兜底) =====

void PpoModelAI::activeStack(const BattleID& battleID, const CStack* stack)
{
    if (battleAI)
        battleAI->activeStack(battleID, stack);
    else
        cb->battleMakeUnitAction(battleID, BattleAction::makeDefend(stack));
}

void PpoModelAI::yourTacticPhase(const BattleID& battleID, int distance)
{
    if (battleAI) {
        battleAI->yourTacticPhase(battleID, distance);
    } else {
        auto battle = cb->getBattle(battleID);
        if (battle)
            cb->battleMakeTacticAction(battleID, BattleAction::makeEndOFTacticPhase(battle->battleGetTacticsSide()));
    }
}

// ===== Dialog auto-accept =====

void PpoModelAI::heroGotLevel(const CGHeroInstance* hero, PrimarySkill pskill, std::vector<SecondarySkill>& skills, QueryID queryID)
{
    cb->selectionMade(0, queryID);
}

void PpoModelAI::commanderGotLevel(const CCommanderInstance* commander, std::vector<ui32> skills, QueryID queryID)
{
    cb->selectionMade(0, queryID);
}

void PpoModelAI::showBlockingDialog(const std::string& text, const std::vector<Component>& components, QueryID askID, const int soundID, bool selection, bool cancel, bool safeToAutoaccept)
{
    cb->selectionMade(0, askID);
}

void PpoModelAI::showTeleportDialog(const CGHeroInstance* hero, TeleportChannelID channel, TTeleportExitsList exits, bool impassable, QueryID askID)
{
    cb->selectionMade(0, askID);
}

void PpoModelAI::showGarrisonDialog(const CArmedInstance* up, const CGHeroInstance* down, bool removableUnits, QueryID queryID, const MetaString& customTitle)
{
    // ML fix (08-27): 守卫残余合并进英雄 (NK2 pickBestCreatures 同款) —
    // 不合并则残余对象不移除 → 访问流程卡死
    if (up && down && up->tempOwner == down->tempOwner) {
        for (auto it = up->stacks.begin(); it != up->stacks.end(); ++it) {
            try {
                SlotID dst = down->getSlotFor(it->second->getCreature());
                if (dst.validSlot())
                    cb->mergeStacks(up, down, it->first, dst);
            } catch (...) {}
        }
    }
    cb->selectionMade(0, queryID);
}

void PpoModelAI::showMapObjectSelectDialog(QueryID askID, const Component& icon, const MetaString& title, const MetaString& description, const std::vector<ObjectInstanceID>& objects)
{
    cb->selectionMade(0, askID);
}

std::optional<BattleAction> PpoModelAI::makeSurrenderRetreatDecision(const BattleID& battleID, const BattleStateInfoForRetreat& battleState)
{
    return std::nullopt;
}

VCMI_LIB_NAMESPACE_END

// ===== DLL exports (VCMI adventure AI plugin interface) =====
// 2026-09-11: exports.def 要求 GetAiName/GetNewAI, 源码缺失导致链接失败;
// 参照 AI/MMAI/main.cpp 与 AI/BattleAI/main.cpp 的导出约定补齐
#ifdef __GNUC__
#define strcpy_s(a, b, c) strncpy(a, c, b)
#endif

static const char* const g_cszAiName = "PpoModelAI";

extern "C" DLL_EXPORT void GetAiName(char* name)
{
    strcpy_s(name, strlen(g_cszAiName) + 1, g_cszAiName);
}

extern "C" DLL_EXPORT void GetNewAI(std::shared_ptr<CGlobalAI>& out)
{
    out = std::make_shared<PpoModelAI>();
}
