// =============================================================================
// Copyright 2024 Simeon Manolov <s.manolloff@gmail.com>.  All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// =============================================================================

#include "StdInc.h"

#include "AsyncRunner.h"
#include "CStack.h"

extern "C" void adventure_process_turn(int playerColor, void* userData);
extern "C" int adventure_get_action();
extern "C" void adventure_send_action(int action);

static const int3 dirs[8] = {
	int3(1,0,0), int3(1,-1,0), int3(0,-1,0), int3(-1,-1,0),
	int3(-1,0,0), int3(-1,1,0), int3(0,1,0), int3(1,1,0),
};
#include "battle/BattleAction.h"
#include "battle/CPlayerBattleCallback.h"
#include "callback/CCallback.h"
#include "callback/CDynLibHandler.h"
#include "gameState/CGameState.h"
#include "mapObjects/CGHeroInstance.h"
#include "networkPacks/BattleChanges.h"
#include "networkPacks/PacksForClientBattle.h"
#include "networkPacks/SetStackEffect.h"
#include "spells/CSpellHandler.h"

#include "AAI/AAI.h"
#include "common.h"
#include "schema/base.h"

namespace MMAI::AAI
{
__attribute__((used, visibility("default"))) AAI::AAI()
{
	std::ostringstream oss;
	oss << this; // Store this memory address
	addrstr = oss.str();
	info("+++ constructor +++");
	asyncTasks = std::make_unique<AsyncRunner>();
}

AAI::~AAI()
{
	info("--- (destructor) ---");
}

std::string AAI::getBattleAIName() const
{
	debug("*** getBattleAIName ***");
	return "MMAI";
}

/*
     * Hybrid call-ins (conecrning both AAI and BAI)
     */

void AAI::battleStart(
	const BattleID & bid,
	const CCreatureSet * army1,
	const CCreatureSet * army2,
	int3 tile,
	const CGHeroInstance * hero1,
	const CGHeroInstance * hero2,
	BattleSide side_,
	bool replayAllowed
)
{
	info("*** battleStart ***");

	side = side_;

	const CGHeroInstance * hero;

	// Battles are ALWAYS between a RED hero and a BLUE hero
	// If --random-heroes is provided, side_, hero1 and hero2 will be different
	// Regardless hero1 and hero2's real owner, RED and BLUE AAIs will
	// receive them as battleStart arguments as if they were the owners.
	// (hero1->tempOwner is set to 0 (RED) or 1 (BLUE) for that purpose)

	// XXX: fix wrong color if --swap-sides option is used
	if(side == BattleSide::ATTACKER)
	{
		hero = dynamic_cast<const CGHeroInstance *>(army1);
		info("Will play with " + hero->getNameTextID() + " on the left side (ATTACKER) in this battle");
	}
	else
	{
		hero = dynamic_cast<const CGHeroInstance *>(army2);
		info("Will play with " + hero->getNameTextID() + " on the right side (DEFENDER) in this battle");
	}

	// just copied code from CAdventureAI::battleStart
	// only difference is argument to initBattleInterface()
	assert(!battleAI);
	assert(cbc);

	auto ainame = getBattleAIName();
	battleAI = CDynLibHandler::getNewBattleAI("MMAI");
	battleAI->initBattleInterface(env, cbc, aiCombatOptions);
	battleAI->battleStart(bid, army1, army2, tile, hero1, hero2, side_, replayAllowed);
}

void AAI::battleEnd(const BattleID & bid, const BattleResult * br, QueryID queryID)
{
	info("*** battleEnd (QueryID: " + std::to_string(static_cast<int>(queryID)) + ") ***");

	battleAI->battleEnd(bid, br, queryID);

	if(cb->getBattle(bid)->battleGetMySide() == BattleSide::ATTACKER)
	{
		ASSERT(queryID != -1, "QueryID is -1, but we are ATTACKER");
		info("Answering query " + std::to_string(queryID) + " to re-play battle");

		asyncTasks->run(
			[this, queryID]()
			{
				std::shared_lock gsLock(CGameState::mutex);
				cb->selectionMade(1, queryID);
			}
		);
	}
	else
	{
		// My patch in CGameHandler::endBattle allows replay even when
		// both sides are non-neutrals. Could not figure out how to
		// send the query only to the attacker.

		// The defender should not answer replay battle queries
		info("Ignoring query " + std::to_string(queryID));
	}

	battleAI.reset();
}

/*
     * AAI call-ins
     */
std::optional<BattleAction> AAI::makeSurrenderRetreatDecision(const BattleID & bid, const BattleStateInfoForRetreat & bs)
{
	debug("*** makeSurrenderRetreatDecision ***");
	return std::nullopt;
}

void AAI::initGameInterface(std::shared_ptr<Environment> ENV, std::shared_ptr<CCallback> CB, AICombatOptions aiCombatOptions_)
{
	info("*** initGameInterface ***");

	aiCombatOptions = aiCombatOptions_;
	color = CB->getPlayerID()->toString();

	env = ENV;
	cb = CB;
	cbc = CB;

	// XXX: not sure if needed
	cb->waitTillRealize = true;
	cb->unlockGsWhenWaiting = true;
};

void AAI::yourTurn(QueryID queryID)
{
	info("*** yourTurn *** (" + std::to_string(queryID.getNum()) + ")");

	// Non-red players: auto-end turn immediately
	if (!cb) return;
	auto pid = cb->getPlayerID();
	if (!pid || pid->getNum() != 0) {
		cb->selectionMade(0, queryID);
		cb->waitTillRealize = false;
		cb->endTurn();
		cb->waitTillRealize = true;
		return;
	}

	// Red player (0): block and wait for Python action
	adventure_process_turn(cb->getPlayerID().value(), (void*)cb.get());
	int a = adventure_get_action();
	adventure_send_action(-1);

	if (a < 0) {
		cb->selectionMade(0, queryID);
		cb->endTurn();
		return;
	}

	// Execute move (async), then end turn
	cb->waitTillRealize = false;
	if (a >= 0 && a <= 7) {
		static const int dx[] = {0, 1, 1, 1, 0, -1, -1, -1};
		static const int dy[] = {-1, -1, 0, 1, 1, 1, 0, -1};
		auto h = cb->getHeroesInfo();
		if (!h.empty()) {
			try {
				int3 target(h[0]->pos.x + dx[a], h[0]->pos.y + dy[a], h[0]->pos.z);
				cb->moveHero(h[0], target, false);
				// ML fix (C8.5): 等待移动实现后再 endTurn (最多 2s), 移动失败(BLOCKED)快速继续
				for (int i = 0; i < 20; i++) {
					std::this_thread::sleep_for(std::chrono::milliseconds(100));
					auto cur = h[0]->pos;
					if (cur.x == target.x && cur.y == target.y && cur.z == target.z)
						break; // 已到达
				}
			} catch(...) {}
		}
	}

	cb->selectionMade(0, queryID);
	cb->endTurn();
	cb->waitTillRealize = true;
}

void AAI::commanderGotLevel(const CCommanderInstance * commander, std::vector<ui32> skills, QueryID queryID)
{
	debug("*** commanderGotLevel ***");
	fprintf(stderr, "[AAI DBG] commanderGotLevel: cb=%p queryID=%d\n", (void*)cb.get(), queryID.getNum()); if(cb) cb->selectionMade(0, queryID);
}

void AAI::finish()
{
	debug("*** finish ***");
}

void AAI::heroGotLevel(const CGHeroInstance * hero, PrimarySkill pskill, std::vector<SecondarySkill> & skills, QueryID queryID)
{
	debug("*** heroGotLevel ***");
	fprintf(stderr, "[AAI DBG] heroGotLevel: cb=%p queryID=%d skills=%zu\n", (void*)cb.get(), queryID.getNum(), skills.size()); if(cb) cb->selectionMade(0, queryID);
}

void AAI::showBlockingDialog(
	const std::string & text,
	const std::vector<Component> & components,
	QueryID askID,
	const int soundID,
	bool selection,
	bool cancel,
	bool safeToAutoaccept
)
{
	debug("*** showBlockingDialog ***");
	fprintf(stderr, "[AAI DBG] showBlockingDialog: cb=%p askID=%d\n", (void*)cb.get(), askID.getNum()); if(cb) cb->selectionMade(0, askID);
}

void AAI::showGarrisonDialog(const CArmedInstance * up, const CGHeroInstance * down, bool removableUnits, QueryID queryID)
{
	debug("*** showGarrisonDialog ***");
	fprintf(stderr, "[AAI DBG] showGarrisonDialog: cb=%p queryID=%d\n", (void*)cb.get(), queryID.getNum()); if(cb) cb->selectionMade(0, queryID);
}

void AAI::showMapObjectSelectDialog(
	QueryID askID,
	const Component & icon,
	const MetaString & title,
	const MetaString & description,
	const std::vector<ObjectInstanceID> & objects
)
{
	debug("*** showMapObjectSelectDialog ***");
	fprintf(stderr, "[AAI DBG] showMapObjectSelectDialog: cb=%p askID=%d\n", (void*)cb.get(), askID.getNum()); if(cb) cb->selectionMade(0, askID);
}

void AAI::showTeleportDialog(const CGHeroInstance * hero, TeleportChannelID channel, TTeleportExitsList exits, bool impassable, QueryID askID)
{
	debug("*** showTeleportDialog ***");
	fprintf(stderr, "[AAI DBG] showTeleportDialog: cb=%p askID=%d\n", (void*)cb.get(), askID.getNum()); if(cb) cb->selectionMade(0, askID);
}

void AAI::showWorldViewEx(const std::vector<ObjectPosInfo> & objectPositions, bool showTerrain)
{
	debug("*** showWorldViewEx ***");
}

void AAI::advmapSpellCast(const CGHeroInstance * caster, SpellID spellID)
{
	debug("*** advmapSpellCast ***");
}

void AAI::artifactAssembled(const ArtifactLocation & al)
{
	debug("*** artifactAssembled ***");
}

void AAI::artifactDisassembled(const ArtifactLocation & al)
{
	debug("*** artifactDisassembled ***");
}

void AAI::artifactMoved(const ArtifactLocation & src, const ArtifactLocation & dst)
{
	debug("*** artifactMoved ***");
}

void AAI::artifactPut(const ArtifactLocation & al)
{
	debug("*** artifactPut ***");
}

void AAI::artifactRemoved(const ArtifactLocation & al)
{
	debug("*** artifactRemoved ***");
}

void AAI::availableArtifactsChanged(const CGBlackMarket * bm)
{
	debug("*** availableArtifactsChanged ***");
}

void AAI::availableCreaturesChanged(const CGDwelling * town)
{
	debug("*** availableCreaturesChanged ***");
}

void AAI::battleResultsApplied()
{
	debug("*** battleResultsApplied ***");
}

void AAI::battleStartBefore(
	const BattleID & bid,
	const CCreatureSet * army1,
	const CCreatureSet * army2,
	int3 tile,
	const CGHeroInstance * hero1,
	const CGHeroInstance * hero2
)
{
	debug("*** battleStartBefore ***");
	// XXX: battleAI is nullptr here
}

void AAI::beforeObjectPropertyChanged(const SetObjectProperty * sop)
{
	debug("*** beforeObjectPropertyChanged ***");
}

void AAI::buildChanged(const CGTownInstance * town, BuildingID buildingID, int what)
{
	debug("*** buildChanged ***");
}

void AAI::centerView(int3 pos, int focusTime)
{
	debug("*** centerView ***");
}

void AAI::gameOver(PlayerColor player, const EVictoryLossCheckResult & victoryLossCheckResult)
{
	debug("*** gameOver ***");
}

void AAI::garrisonsChanged(ObjectInstanceID id1, ObjectInstanceID id2)
{
	debug("*** garrisonsChanged ***");
}

void AAI::heroBonusChanged(const CGHeroInstance * hero, const Bonus & bonus, bool gain)
{
	debug("*** heroBonusChanged ***");
}

void AAI::heroCreated(const CGHeroInstance *)
{
	debug("*** heroCreated ***");
}

void AAI::heroInGarrisonChange(const CGTownInstance * town)
{
	debug("*** heroInGarrisonChange ***");
}

void AAI::heroManaPointsChanged(const CGHeroInstance * hero)
{
	debug("*** heroManaPointsChanged ***");
}

void AAI::heroMovePointsChanged(const CGHeroInstance * hero)
{
	debug("*** heroMovePointsChanged ***");
}

void AAI::heroMoved(const TryMoveHero & details, bool verbose)
{
	debug("*** heroMoved ***");
}

void AAI::heroPrimarySkillChanged(const CGHeroInstance * hero, PrimarySkill which, si64 val)
{
	debug("*** heroPrimarySkillChanged ***");
}

void AAI::heroSecondarySkillChanged(const CGHeroInstance * hero, int which, int val)
{
	debug("*** heroSecondarySkillChanged ***");
}

void AAI::heroVisit(const CGHeroInstance * visitor, const CGObjectInstance * visitedObj, bool start)
{
	debug("*** heroVisit ***");
}

void AAI::heroVisitsTown(const CGHeroInstance * hero, const CGTownInstance * town)
{
	debug("*** heroVisitsTown ***");
}

void AAI::newObject(const CGObjectInstance * obj)
{
	debug("*** newObject ***");
}

void AAI::objectPropertyChanged(const SetObjectProperty * sop)
{
	debug("*** objectPropertyChanged ***");
}

void AAI::objectRemoved(const CGObjectInstance * obj, const PlayerColor & initiator)
{
	debug("*** objectRemoved ***");
}

void AAI::playerBlocked(int reason, bool start)
{
	debug("*** playerBlocked ***");
}

void AAI::playerBonusChanged(const Bonus & bonus, bool gain)
{
	debug("*** playerBonusChanged ***");
}

void AAI::receivedResource()
{
	debug("*** receivedResource ***");
}

void AAI::requestRealized(PackageApplied * pa)
{
	debug("*** requestRealized ***");
}

void AAI::requestSent(const CPackForServer * pack, int requestID)
{
	debug("*** requestSent ***");
}

void AAI::showHillFortWindow(const CGObjectInstance * object, const CGHeroInstance * visitor)
{
	debug("*** showHillFortWindow ***");
}

void AAI::showInfoDialog(EInfoWindowMode type, const std::string & text, const std::vector<Component> & components, int soundID)
{
	debug("*** showInfoDialog ***");
}

void AAI::showMarketWindow(const IMarket * market, const CGHeroInstance * visitor, QueryID queryID)
{
	debug("*** showMarketWindow ***");
}

void AAI::showPuzzleMap()
{
	debug("*** showPuzzleMap ***");
}

void AAI::showRecruitmentDialog(const CGDwelling * dwelling, const CArmedInstance * dst, int level, QueryID queryID)
{
	debug("*** showRecruitmentDialog ***");
}

void AAI::showShipyardDialog(const IShipyard * obj)
{
	debug("*** showShipyardDialog ***");
}

void AAI::showTavernWindow(const CGObjectInstance * object, const CGHeroInstance * visitor, QueryID queryID)
{
	debug("*** showTavernWindow ***");
}

void AAI::showThievesGuildWindow(const CGObjectInstance * obj)
{
	debug("*** showThievesGuildWindow ***");
}

void AAI::showUniversityWindow(const IMarket * market, const CGHeroInstance * visitor, QueryID queryID)
{
	debug("*** showUniversityWindow ***");
}

void AAI::tileHidden(const FowTilesType & pos)
{
	debug("*** tileHidden ***");
}

void AAI::tileRevealed(const FowTilesType & pos)
{
	debug("*** tileRevealed ***");
}

void AAI::bulkArtMovementStart(size_t numOfArts, size_t possibleAssemblyNumOfArts)
{
	debug("*** bulkArtMovementStart ***");
}

void AAI::askToAssembleArtifact(const ArtifactLocation & dst)
{
	debug("*** askToAssembleArtifact ***");
}

void AAI::viewWorldMap()
{
	debug("*** viewWorldMap ***");
}

void AAI::showQuestLog()
{
	debug("*** showQuestLog ***");
}

void AAI::objectRemovedAfter()
{
	debug("*** objectRemovedAfter ***");
}

void AAI::playerStartsTurn(PlayerColor player)
{
	debug("*** playerStartsTurn ***");
}

void AAI::heroExchangeStarted(ObjectInstanceID hero1, ObjectInstanceID hero2, QueryID query)
{
	debug("*** heroExchangeStarted ***");
}

/*
     * BAI call-ins
     */

void AAI::actionFinished(const BattleID & bid, const BattleAction & action)
{
	battleAI->actionFinished(bid, action);
}

void AAI::actionStarted(const BattleID & bid, const BattleAction & action)
{
	battleAI->actionStarted(bid, action);
}

void AAI::activeStack(const BattleID & bid, const CStack * stack)
{
	battleAI->activeStack(bid, stack);
}

void AAI::battleAttack(const BattleID & bid, const BattleAttack * ba)
{
	battleAI->battleAttack(bid, ba);
}

void AAI::battleCatapultAttacked(const BattleID & bid, const CatapultAttack & ca)
{
	battleAI->battleCatapultAttacked(bid, ca);
}

void AAI::battleGateStateChanged(const BattleID & bid, const EGateState state)
{
	battleAI->battleGateStateChanged(bid, state);
}

void AAI::battleLogMessage(const BattleID & bid, const std::vector<MetaString> & lines)
{
	battleAI->battleLogMessage(bid, lines);
}

void AAI::battleNewRound(const BattleID & bid)
{
	battleAI->battleNewRound(bid);
}

void AAI::battleNewRoundFirst(const BattleID & bid)
{
	battleAI->battleNewRoundFirst(bid);
}

void AAI::battleObstaclesChanged(const BattleID & bid, const std::vector<ObstacleChanges> & obstacles)
{
	battleAI->battleObstaclesChanged(bid, obstacles);
}

void AAI::battleSpellCast(const BattleID & bid, const BattleSpellCast * sc)
{
	battleAI->battleSpellCast(bid, sc);
}

void AAI::battleStackMoved(const BattleID & bid, const CStack * stack, const BattleHexArray & dest, int distance, bool teleport)
{
	battleAI->battleStackMoved(bid, stack, dest, distance, teleport);
}

void AAI::battleStacksAttacked(const BattleID & bid, const std::vector<BattleStackAttacked> & bsa, bool ranged)
{
	battleAI->battleStacksAttacked(bid, bsa, ranged);
}

void AAI::battleStacksEffectsSet(const BattleID & bid, const SetStackEffect & sse)
{
	battleAI->battleStacksEffectsSet(bid, sse);
}

void AAI::battleTriggerEffect(const BattleID & bid, const BattleTriggerEffect & bte)
{
	battleAI->battleTriggerEffect(bid, bte);
}

void AAI::battleUnitsChanged(const BattleID & bid, const std::vector<UnitChanges> & changes)
{
	battleAI->battleUnitsChanged(bid, changes);
}

void AAI::yourTacticPhase(const BattleID & bid, int distance)
{
	battleAI->yourTacticPhase(bid, distance);
}

/*
* private
*/

template<typename... Args>
void AAI::_log(const ELogLevel::ELogLevel level, const std::string & format, Args... args) const
{
	logAi->log(level, "AAI-%s [%s] " + format, addrstr, color, args...);
}

template<typename... Args>
void AAI::error(const std::string & format, Args... args) const
{
	log(ELogLevel::ERROR, format, args...);
}
template<typename... Args>
void AAI::warn(const std::string & format, Args... args) const
{
	log(ELogLevel::WARN, format, args...);
}
template<typename... Args>
void AAI::info(const std::string & format, Args... args) const
{
	log(ELogLevel::INFO, format, args...);
}
template<typename... Args>
void AAI::debug(const std::string & format, Args... args) const
{
	log(ELogLevel::DEBUG, format, args...);
}
template<typename... Args>
void AAI::trace(const std::string & format, Args... args) const
{
	log(ELogLevel::DEBUG, format, args...);
}
template<typename... Args>
void AAI::log(const ELogLevel::ELogLevel level, const std::string & format, Args... args) const
{
	if(logAi->getEffectiveLevel() <= level)
		_log(level, format, args...);
}

void AAI::error(const std::string & text) const
{
	log(ELogLevel::ERROR, text);
}
void AAI::warn(const std::string & text) const
{
	log(ELogLevel::WARN, text);
}
void AAI::info(const std::string & text) const
{
	log(ELogLevel::INFO, text);
}
void AAI::debug(const std::string & text) const
{
	log(ELogLevel::DEBUG, text);
}
void AAI::trace(const std::string & text) const
{
	log(ELogLevel::TRACE, text);
}
void AAI::log(ELogLevel::ELogLevel level, const std::string & text) const
{
	if(logAi->getEffectiveLevel() <= level)
		_log(level, "%s", text);
}

void AAI::error(const std::function<std::string()> & cb) const
{
	log(ELogLevel::ERROR, cb);
}
void AAI::warn(const std::function<std::string()> & cb) const
{
	log(ELogLevel::WARN, cb);
}
void AAI::info(const std::function<std::string()> & cb) const
{
	log(ELogLevel::INFO, cb);
}
void AAI::debug(const std::function<std::string()> & cb) const
{
	log(ELogLevel::DEBUG, cb);
}
void AAI::trace(const std::function<std::string()> & cb) const
{
	log(ELogLevel::TRACE, cb);
}
void AAI::log(ELogLevel::ELogLevel level, const std::function<std::string()> & cb) const
{
	if(logAi->getEffectiveLevel() <= level)
		_log(level, "%s", cb());
}

}
