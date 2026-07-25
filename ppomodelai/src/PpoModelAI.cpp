#include "StdInc.h"
#include "PpoModelAI.h"

#include "callback/CCallback.h"
#include "battle/BattleAction.h"
#include "battle/CPlayerBattleCallback.h"
#include "mapObjects/CGHeroInstance.h"
#include "int3.h"
#include "vstd/CLoggerBase.h"

VCMI_LIB_NAMESPACE_BEGIN

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
        model = std::make_unique<ModelInference>("D:/Bigdata/hero3_fresh/wsl2_model.onnx");
        logAi->info("PpoModelAI: model loaded successfully");
    } catch (const std::exception& e) {
        logAi->error("PpoModelAI: failed to load model: %s", e.what());
    }
}

std::string PpoModelAI::getBattleAIName() const
{
    return "BattleAI";
}

void PpoModelAI::yourTurn(QueryID queryID)
{
    logAi->info("PpoModelAI: yourTurn (query=%d, player=%d)", queryID.getNum(), playerID.getNum());

    if (!model) {
        logAi->warn("PpoModelAI: no model loaded, ending turn");
        cb->endTurn();
        return;
    }

    // Build observation
    auto obs = ObsBuilder::buildObs(cb.get(), playerID);

    // Run inference
    int action = model->predict(obs);

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
            int3 dest = moveHero->pos + DIR_OFFSETS[action];
            logAi->info("PpoModelAI: moving hero %d from (%d,%d) to (%d,%d)",
                moveHero->id.getNum(),
                moveHero->pos.x, moveHero->pos.y,
                dest.x, dest.y);
            try {
                cb->moveHero(moveHero->id, dest, 0, false, playerID, EPathfindingLayer::LAND);
            } catch (const std::exception& e) {
                logAi->warn("PpoModelAI: move failed: %s", e.what());
                cb->endTurn();
            }
        } else {
            logAi->info("PpoModelAI: no hero with movement, ending turn");
            cb->endTurn();
        }
    } else if (action == 8) {
        // Interact: just end turn (simplified)
        logAi->info("PpoModelAI: interact - ending turn");
        cb->endTurn();
    } else if (action == 9) {
        // Next hero: just end turn (simplified)
        logAi->info("PpoModelAI: next hero - ending turn");
        cb->endTurn();
    } else {
        // End turn (action 10 or unknown)
        logAi->info("PpoModelAI: ending turn");
        cb->endTurn();
    }
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

void PpoModelAI::showGarrisonDialog(const CArmedInstance* up, const CArmedInstance* down, bool removableUnits, QueryID queryID, const MetaString& customTitle)
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
