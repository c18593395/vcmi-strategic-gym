// Minimal model AI DLL stub for VCMI 1.7.5 Windows (AI DLL interface)
// Exports: GetGlobalAiVersion / GetAiName / GetNewAI
#include "lib/callback/CGlobalAI.h"
#include "lib/callback/IGameEventsReceiver.h"
#include "lib/callback/CCallback.h"
#include "lib/battle/BattleAction.h"
#include <cstring>

static const char * const g_cszAiName = "ModelAI";

class ModelAI : public CGlobalAI, public IGameEventsReceiver
{
	std::shared_ptr<CCallback> cc;
public:
	// ---- required pure virtuals from CGameInterface ----
	void showBlockingDialog(const std::string &, const std::vector<Component> &, QueryID qid, const int, bool, bool, bool) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
	void showGarrisonDialog(const CArmedInstance *, const CGHeroInstance *, bool, QueryID qid, const MetaString &) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
	void showTeleportDialog(const CGHeroInstance *, TeleportChannelID, TTeleportExitsList, bool, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
	void showMapObjectSelectDialog(QueryID qid, const Component &, const MetaString &, const MetaString &, const std::vector<ObjectInstanceID> &) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
	std::optional<BattleAction> makeSurrenderRetreatDecision(const BattleID &, const BattleStateInfoForRetreat &) override { return std::nullopt; }
	void heroGotLevel(const CGHeroInstance *, PrimarySkill, std::vector<SecondarySkill> &, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
	void commanderGotLevel(const CCommanderInstance *, std::vector<ui32>, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
	// ---- battle interface pure virtuals (CBattleGameInterface) ----
	void activeStack(const BattleID &, const CStack *) override {}
	void yourTacticPhase(const BattleID &, int) override {}
    void buildChanged(const CGTownInstance *town, BuildingID, int) override {}
        void battleResultsApplied() override {}
        void battleEnded() override {}
        void garrisonsChanged(ObjectInstanceID, ObjectInstanceID) override {}
        void artifactPut(const ArtifactLocation &al) override {}
        void artifactRemoved(const ArtifactLocation &al) override {}
        void artifactAssembled(const ArtifactLocation &al) override {}
        void artifactDisassembled(const ArtifactLocation &al) override {}
        void artifactMoved(const ArtifactLocation &src, const ArtifactLocation &dst) override {}
        void bulkArtMovementStart(size_t, size_t) override {}
        void askToAssembleArtifact(const ArtifactLocation &) override {}
        void heroVisit(const CGHeroInstance *visitor, const CGObjectInstance *visitedObj, bool) override {}
        void heroCreated(const CGHeroInstance*) override {}
        void heroInGarrisonChange(const CGTownInstance *town) override {}
        void heroMoved(const TryMoveHero &, bool) override {}
        void heroExperienceChanged(const CGHeroInstance *, si64) override {}
        void heroPrimarySkillChanged(const CGHeroInstance *, PrimarySkill, si64) override {}
        void heroSecondarySkillChanged(const CGHeroInstance *, int, int) override {}
        void heroManaPointsChanged(const CGHeroInstance *) override {}
        void heroMovePointsChanged(const CGHeroInstance *) override {}
        void heroVisitsTown(const CGHeroInstance*, const CGTownInstance *) override {}
        void receivedResource() override {}
        void showInfoDialog(EInfoWindowMode, const std::string &, const std::vector<Component> &, int) override {}
        void showRecruitmentDialog(const CGDwelling *dwelling, const CArmedInstance *dst, int, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
        void showShipyardDialog(const IShipyard *obj) override {}
        void showPuzzleMap() override {}
        void viewWorldMap() override {}
        void showMarketWindow(const IMarket *, const CGHeroInstance *, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
        void showUniversityWindow(const IMarket *market, const CGHeroInstance *visitor, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
        void showHillFortWindow(const CGObjectInstance *object, const CGHeroInstance *visitor) override {}
        void showThievesGuildWindow(const CGObjectInstance *) override {}
        void showTavernWindow(const CGObjectInstance *, const CGHeroInstance *, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
        void showQuestLog() override {}
        void advmapSpellCast(const CGHeroInstance *, SpellID) override {}
        void tileHidden(const FowTilesType &pos) override {}
        void tileRevealed(const FowTilesType &pos) override {}
        void newObject(const CGObjectInstance *) override {}
        void availableArtifactsChanged(const CGBlackMarket *bm) override {}
        void centerView(int3, int) override {}
        void availableCreaturesChanged(const CGDwelling *town) override {}
        void heroBonusChanged(const CGHeroInstance *hero, const Bonus &bonus, bool) override {}
        void playerBonusChanged(const Bonus &bonus, bool) override {}
        void requestSent(const CPackForServer *pack, int) override {}
        void requestRealized(PackageApplied *pa) override {}
        void beforeObjectPropertyChanged(const SetObjectProperty *) override {}
        void objectPropertyChanged(const SetObjectProperty *) override {}
        void objectRemoved(const CGObjectInstance *obj, const PlayerColor &) override {}
        void objectRemovedAfter() override {}
        void playerBlocked(int, bool) override {}
        void gameOver(PlayerColor, const EVictoryLossCheckResult &) override {}
        void playerStartsTurn(PlayerColor) override {}
        void playerEndsTurn(PlayerColor) override {}
        void responseStatistic(StatisticDataSet &) override {}
        void heroExchangeStarted(ObjectInstanceID, ObjectInstanceID, QueryID qid) override { if(qid != QueryID(-1)) cc->selectionMade(0, qid); }
        void initGameInterface(std::shared_ptr<Environment> env_, std::shared_ptr<CCallback> cb) override { env = env_; cc = cb; }
        void yourTurn(QueryID queryID) override
        {
            if(queryID != QueryID(-1))
                cc->selectionMade(0, queryID);
            // give the server a beat to process the query reply, then end turn
            std::this_thread::sleep_for(std::chrono::milliseconds(300));
            cc->endTurn();
        }
        void finish() override {}
        void showWorldViewEx(const std::vector<ObjectPosInfo> &, bool) override {}
        void invalidatePaths() override {}
        void setColorScheme(ColorScheme) override {}
        void initBattleInterface(std::shared_ptr<Environment>, std::shared_ptr<CBattleCallback>) override {}
        void initBattleInterface(std::shared_ptr<Environment>, std::shared_ptr<CBattleCallback>, AutocombatPreferences) override {}
};

extern "C" __declspec(dllexport) int GetGlobalAiVersion()
{
	return AI_INTERFACE_VER;
}

extern "C" __declspec(dllexport) void GetAiName(char * name)
{
	strcpy_s(name, strlen(g_cszAiName) + 1, g_cszAiName);
}

extern "C" __declspec(dllexport) void GetNewAI(std::shared_ptr<CGlobalAI> & out)
{
	out = std::make_shared<ModelAI>();
}
