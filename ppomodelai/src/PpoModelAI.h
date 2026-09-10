#pragma once

#include "callback/CAdventureAI.h"
#include "ModelInference.h"
#include "ObsBuilder.h"

VCMI_LIB_NAMESPACE_BEGIN

class PpoModelAI : public CAdventureAI
{
    std::shared_ptr<CCallback> cb;
    ModelInference* model = nullptr;  // 非拥有指针: 进程级单例 (见 ModelInference.h)
    std::unique_ptr<ObsBuilder> obsBuilder;
    bool human = false;
    PlayerColor playerID;

public:
    PpoModelAI();
    ~PpoModelAI() override;

    // Core AI interface
    void initGameInterface(std::shared_ptr<Environment> ENV, std::shared_ptr<CCallback> CB, AICombatOptions aiCombatOptions) override;
    void yourTurn(QueryID queryID) override;
    std::string getBattleAIName() const override;

    // Battle callbacks — delegate to BattleAI
    void activeStack(const BattleID& battleID, const CStack* stack) override;
    void yourTacticPhase(const BattleID& battleID, int distance) override;

    // Dialog auto-accept
    void heroGotLevel(const CGHeroInstance* hero, PrimarySkill pskill, std::vector<SecondarySkill>& skills, QueryID queryID) override;
    void commanderGotLevel(const CCommanderInstance* commander, std::vector<ui32> skills, QueryID queryID) override;
    void showBlockingDialog(const std::string& text, const std::vector<Component>& components, QueryID askID, const int soundID, bool selection, bool cancel, bool safeToAutoaccept) override;
    void showTeleportDialog(const CGHeroInstance* hero, TeleportChannelID channel, TTeleportExitsList exits, bool impassable, QueryID askID) override;
    void showGarrisonDialog(const CArmedInstance* up, const CGHeroInstance* down, bool removableUnits, QueryID queryID, const MetaString& customTitle) override;
    void showMapObjectSelectDialog(QueryID askID, const Component& icon, const MetaString& title, const MetaString& description, const std::vector<ObjectInstanceID>& objects) override;
    std::optional<BattleAction> makeSurrenderRetreatDecision(const BattleID& battleID, const BattleStateInfoForRetreat& battleState) override;
};

VCMI_LIB_NAMESPACE_END
