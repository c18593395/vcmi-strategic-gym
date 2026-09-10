#include "StdInc.h"
#include "PpoModelAI.h"

#include "callback/CCallback.h"
#include "battle/BattleAction.h"
#include "battle/CUnitState.h"
#include "CStack.h"
#include "battle/CPlayerBattleCallback.h"
#include "mapObjects/CGHeroInstance.h"
#include "int3.h"
#include "vstd/CLoggerBase.h"
#include "pathfinder/PathfinderCache.h"
#include "pathfinder/PathfinderOptions.h"
#include "pathfinder/CGPathNode.h"
#include "mapping/TerrainTile.h"
#include "TerrainHandler.h"

#include <chrono>
#include <cstdio>

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

static const int3 DIR_OFFSETS[8] = {
    int3(1, 0, 0),   // 0: Right
    int3(1, 1, 0),   // 1: Down-Right
    int3(0, 1, 0),   // 2: Down
    int3(-1, 1, 0),  // 3: Down-Left
    int3(-1, 0, 0),  // 4: Left
    int3(-1, -1, 0), // 5: Up-Left
    int3(0, -1, 0),  // 6: Up
    int3(1, -1, 0),  // 7: Up-Right
};

PpoModelAI::PpoModelAI() {}
PpoModelAI::~PpoModelAI() = default;

void PpoModelAI::initGameInterface(std::shared_ptr<Environment> ENV, std::shared_ptr<CCallback> CB, AICombatOptions aiCombatOptions)
{
    cb = CB;
    env = ENV;
    this->aiCombatOptions = aiCombatOptions;
    human = false;
    playerID = *cb->getPlayerID();

    logAi->info("PpoModelAI: initializing for player %d", playerID.getNum());

    try {
        model = &ModelInference::instance("D:/Bigdata/hero3_fresh/wsl2_model.onnx");
        AI_TRACE("initGameInterface: shared model ready");
        logAi->info("PpoModelAI: model loaded successfully");
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

    if (!model) {
        AI_TRACE("no model loaded, ending turn");
        logAi->warn("PpoModelAI: no model loaded, ending turn");
        cb->endTurn();
        return;
    }

    try {
        // Build observation
        AI_TRACE("buildObs begin");
        auto obs = ObsBuilder::buildObs(cb.get(), playerID);
        AI_TRACE("buildObs done (%lld ms)", elapsedMs());

        // Run inference
        AI_TRACE("predict begin");
        int action = model->predict(obs);
        AI_TRACE("predict done action=%d (%lld ms)", action, elapsedMs());

        logAi->info("PpoModelAI: action=%d obs[0..3]=%.0f %.0f %.0f %.0f",
            action, obs[0], obs[1], obs[2], obs[3]);

        // Execute action
        if (action >= 0 && action <= 7) {
            // Movement: find first owned hero with movement
            auto heroes = cb->getHeroesInfo();
            const CGHeroInstance* moveHero = nullptr;
            for (auto* h : heroes) {
                if (h->tempOwner == playerID && h->movementPointsRemaining() > 0) {
                    moveHero = h;
                    break;
                }
            }

            if (moveHero) {
                // VCMI 双坐标语义 (gui9 实测踩坑):
                //   hero->pos (anchorPos) = 模板锚点格; 英雄实际交互格
                //   visitablePos() = pos - getVisitableOffset() (英雄模板 1x2, offset 非 0).
                //   server (CGameHandler::moveHero) 对收到的 dst 再做
                //   convertToVisitablePos(dst) = dst - offset, 且成功后
                //   setAnchorPos(pack.end) — 即请求参数 dst 是 anchor 语义.
                //   因此: 本地 tile/pathfinder 判定用 visitable 语义目标,
                //   请求参数转回 anchor 语义, 否则双方判的格子错位一格,
                //   server 判 blocked 拒绝 → client onPacketReceived 崩溃.
                int3 heroVisitable = moveHero->visitablePos();
                int3 visitableDest = heroVisitable + DIR_OFFSETS[action];
                int3 dest = visitableDest + moveHero->getVisitableOffset(); // anchor 语义, 请求参数
                AI_TRACE("move hero %d: pos=(%d,%d) visitable=(%d,%d) vOffset=(%d,%d)",
                    moveHero->id.getNum(),
                    moveHero->pos.x, moveHero->pos.y,
                    heroVisitable.x, heroVisitable.y,
                    moveHero->getVisitableOffset().x, moveHero->getVisitableOffset().y);
                logAi->info("PpoModelAI: moving hero %d visitable (%d,%d)->(%d,%d), dst anchor (%d,%d)",
                    moveHero->id.getNum(),
                    heroVisitable.x, heroVisitable.y,
                    visitableDest.x, visitableDest.y,
                    dest.x, dest.y);

                // server 判定格 = dst - offset = visitableDest, tile 判定须对 visitableDest
                const TerrainTile* tile = cb->getTile(visitableDest, false);
                const CGObjectInstance* topObj = tile ? cb->getTopObj(visitableDest) : nullptr;
                AI_TRACE("dest (%d,%d) diag: visible=%d tile=%s blocked=%d visitable=%d topObjId=%d",
                    visitableDest.x, visitableDest.y,
                    cb->isVisible(visitableDest) ? 1 : 0,
                    tile ? "ok" : "null",
                    tile ? (tile->blocked() ? 1 : 0) : -1,
                    tile ? (tile->visitable() ? 1 : 0) : -1,
                    topObj ? topObj->ID.getNum() : -1);

                // server 同款拒绝条件 (CGameHandler.cpp:949): 岩石地形 / blocked 且非 visitable
                bool tileReject = !tile
                    || !tile->getTerrain()->isPassable()
                    || (tile->blocked() && !tile->visitable());

                // server (CGameHandler.cpp:930-945): simultaneous turns 下目标格有
                // 其他玩家所属对象 → 拒绝. client 无法预判 isContactAllowed,
                // 保守起见: 目标格有他人所属对象就 endTurn.
                bool simTurnReject = topObj
                    && topObj->getOwner().isValidPlayer()
                    && topObj->getOwner() != moveHero->tempOwner;

                // pathfinder 校验: dest 本回合剩余移动力内可达 (turns==0)
                PathfinderOptions pOpts(*cb);
                PathfinderCache pathCache(cb.get(), pOpts);
                auto paths = pathCache.getPathsInfo(moveHero);
                const CGPathNode* node = paths->getPathInfo(visitableDest);
                AI_TRACE("path diag: node=%s turns=%u accessible=%d",
                    node ? "ok" : "null",
                    node ? static_cast<unsigned>(node->turns) : 255u,
                    node ? static_cast<int>(node->accessible) : -1);

                if (tileReject) {
                    AI_TRACE("dest rejected by tile check - endTurn");
                    logAi->info("PpoModelAI: dest (%d,%d) rejected by tile check, ending turn",
                        visitableDest.x, visitableDest.y);
                    cb->endTurn();
                } else if (simTurnReject) {
                    AI_TRACE("dest has object owned by another player (simultaneous turns) - endTurn");
                    logAi->info("PpoModelAI: dest (%d,%d) has object of player %d, ending turn",
                        visitableDest.x, visitableDest.y,
                        topObj->getOwner().getNum());
                    cb->endTurn();
                } else if (!node || !node->reachable() || node->turns > 0) {
                    AI_TRACE("dest (%d,%d) not reachable this turn (blocked or no MP) - endTurn",
                        visitableDest.x, visitableDest.y);
                    logAi->info("PpoModelAI: dest (%d,%d) not reachable this turn, ending turn",
                        visitableDest.x, visitableDest.y);
                    cb->endTurn();
                } else {
                    try {
                        cb->moveHero(moveHero, dest, false, EPathfindingLayer::LAND);
                        AI_TRACE("moveHero request sent");
                    } catch (const std::exception& e) {
                        AI_TRACE("move failed: %s — endTurn", e.what());
                        logAi->warn("PpoModelAI: move failed: %s", e.what());
                        cb->endTurn();
                    }
                }
            } else {
                AI_TRACE("no hero with movement, ending turn");
                logAi->info("PpoModelAI: no hero with movement, ending turn");
                cb->endTurn();
            }
        } else if (action == 8) {
            // Interact: just end turn (simplified)
            AI_TRACE("interact - ending turn");
            logAi->info("PpoModelAI: interact - ending turn");
            cb->endTurn();
        } else if (action == 9) {
            // Next hero: just end turn (simplified)
            AI_TRACE("next hero - ending turn");
            logAi->info("PpoModelAI: next hero - ending turn");
            cb->endTurn();
        } else {
            // End turn (action 10 or unknown)
            AI_TRACE("ending turn");
            logAi->info("PpoModelAI: ending turn");
            cb->endTurn();
        }
    } catch (const std::exception& e) {
        // 兜底: 任何异常都必须结束回合, 防止 AI 回合卡死全局
        AI_TRACE("EXCEPTION: %s — fallback endTurn", e.what());
        logAi->error("PpoModelAI: yourTurn exception: %s", e.what());
        cb->endTurn();
    }

    AI_TRACE("yourTurn leave (%lld ms)", elapsedMs());
}

// ===== Battle callbacks =====

void PpoModelAI::activeStack(const BattleID& battleID, const CStack* stack)
{
    cb->battleMakeUnitAction(battleID, BattleAction::makeDefend(stack));
}

void PpoModelAI::yourTacticPhase(const BattleID& battleID, int distance)
{
    auto battle = cb->getBattle(battleID);
    if (battle)
        cb->battleMakeTacticAction(battleID, BattleAction::makeEndOFTacticPhase(battle->battleGetTacticsSide()));
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
