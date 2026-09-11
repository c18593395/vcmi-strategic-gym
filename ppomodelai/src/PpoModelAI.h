#pragma once

#include "callback/CAdventureAI.h"
#include "ModelInference.h"
#include "ObsBuilder.h"

#include <atomic>

VCMI_LIB_NAMESPACE_BEGIN

// v5 部署 AI (2026-09-11 模型质量线 mq-2b):
// 25 动作语义 (0-7 移动 N-start CW / 8 INTERACT / 9 NEXT_HERO / 10 END_TURN / 11-24 高层),
// ObsBuilder::fillState 3464 obs + terrain 21x21x4, AAI 模式延迟 endTurn (ML fix 08-27).
class PpoModelAI : public CAdventureAI
{
    std::shared_ptr<CCallback> cb;
    ModelInference* model = nullptr;  // 非拥有指针: 进程级单例 (见 ModelInference.h)
    bool human = false;
    PlayerColor playerID;

    // ML fix (08-27) 延迟 endTurn 模式 (AAI 同款): moveHero 后不立即 endTurn,
    // 守卫战斗触发时 endTurn 会被服务器拒 ("has to answer queries").
    // 战斗由 battleEnd 回调收尾; 无战斗由兜底线程 500ms 后 endTurn.
    std::atomic<bool> in_battle{false};
    std::atomic<bool> pending_endturn{false};
    QueryID last_query;

    // 当前决策英雄 (ObjectInstanceID 全局 id; NEXT_HERO 切换;
    // ObsBuilder::fillState 内按 id+owner 定位槽位, 无效时 fallback 第一个己方英雄)
    ObjectInstanceID curHeroId;

    // 兜底/战斗收尾共用的延迟 endTurn (detached 线程, 500ms 后 CAS+应答+endTurn)
    void scheduleDelayedEndTurn(int delayMs);

public:
    PpoModelAI();
    ~PpoModelAI() override;

    // Core AI interface
    void initGameInterface(std::shared_ptr<Environment> ENV, std::shared_ptr<CCallback> CB, AICombatOptions aiCombatOptions) override;
    void yourTurn(QueryID queryID) override;
    std::string getBattleAIName() const override;

    // Battle lifecycle — 维护 in_battle + 创建/释放 BattleAI (AAI 同款)
    void battleStart(const BattleID& battleID, const CCreatureSet* army1, const CCreatureSet* army2, int3 tile, const CGHeroInstance* hero1, const CGHeroInstance* hero2, BattleSide side, bool replayAllowed) override;
    void battleEnd(const BattleID& battleID, const BattleResult* br, QueryID queryID) override;

    // Battle callbacks — 转发 BattleAI (判空保护)
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
