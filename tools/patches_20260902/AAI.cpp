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
#include "battle/BattleAction.h"
#include "battle/CPlayerBattleCallback.h"
#include "callback/CCallback.h"
#include "callback/CDynLibHandler.h"
#include "constants/EntityIdentifiers.h"
#include "constants/Enumerations.h"
#include "constants/NumericConstants.h"
#include "gameState/CGameState.h"
#include "mapping/CMap.h"
#include "mapObjects/CGDwelling.h"
#include "mapObjects/CGObjectInstance.h"
#include "mapObjects/CGHeroInstance.h"
#include "mapObjects/CGTownInstance.h"
#include "mapObjects/army/CArmedInstance.h"
#include "mapObjects/army/CStackInstance.h"
#include "networkPacks/BattleChanges.h"
#include "networkPacks/PacksForClientBattle.h"
#include "networkPacks/SetStackEffect.h"
#include "spells/CSpellHandler.h"

#include "AAI/AAI.h"
#include "common.h"
#include "schema/base.h"

extern "C" void adventure_process_turn(int playerColor, void* userData);
extern "C" int adventure_get_action();
extern "C" void adventure_send_action(int action);

// 跨 .so 引用 strategic_state.cpp 定义的 active hero 全局变量
extern "C" { extern int32_t g_active_hero; }

static const int3 dirs[8] = {
	int3(1,0,0), int3(1,-1,0), int3(0,-1,0), int3(-1,-1,0),
	int3(-1,0,0), int3(-1,1,0), int3(0,1,0), int3(1,1,0),
};

// =============================================================================
// 动作 11-24 辅助: v1 引擎侧"最近目标"解析 (欧氏距离含 z, 跳过敌方 owner != PlayerColor(0))
// =============================================================================
namespace {

int64_t distSq(const int3 & a, const int3 & b)
{
	int64_t dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
	return dx * dx + dy * dy + dz * dz;
}

// 最近友方英雄 (排除 cur 自己; getHeroesInfo 只含己方英雄, 仍按 owner 过滤)
const CGHeroInstance * nearestAllyHero(const std::vector<const CGHeroInstance*> & heroes, const CGHeroInstance * cur)
{
	const CGHeroInstance * best = nullptr;
	int64_t bestDist = std::numeric_limits<int64_t>::max();
	for (const auto * h : heroes)
	{
		if (!h || h == cur) continue;
		if (h->getOwner() != PlayerColor(0)) continue; // 跳过敌方
		int64_t d = distSq(h->pos, cur->pos);
		if (d < bestDist) { bestDist = d; best = h; }
	}
	return best;
}

// 最近己方城镇
const CGTownInstance * nearestOwnTown(CCallback * cb, const CGHeroInstance * cur)
{
	const CGTownInstance * best = nullptr;
	int64_t bestDist = std::numeric_limits<int64_t>::max();
	for (const auto * t : cb->getTownsInfo())
	{
		if (!t || t->getOwner() != PlayerColor(0)) continue; // 跳过敌方
		int64_t d = distSq(t->pos, cur->pos);
		if (d < bestDist) { bestDist = d; best = t; }
	}
	return best;
}

// 最近可交互对象 (getAllVisitableObjs 已过滤可见/可访问/非 EVENT)
// 排除: dist==0 (英雄自身格)
// 返回目标对象供 MOVE_TO/INTERACT 逐格逼近 (moveHero 单格版只允许相邻格, 见 CGameHandler STANDARD 检查)
const CGObjectInstance * nearestInteractable(CCallback * cb, const CGHeroInstance * cur)
{
	const CGObjectInstance * best = nullptr;
	int64_t bestDist = std::numeric_limits<int64_t>::max();
	for (const auto * obj : cb->getAllVisitableObjs())
	{
		if (!obj || obj->ID == Obj::HERO) continue;
		auto owner = obj->getOwner();
		if (owner != PlayerColor(0) && owner != PlayerColor::NEUTRAL) continue; // 跳过敌方
		int3 op = obj->visitablePos();
		int64_t d = distSq(op, cur->pos);
		if (d == 0) continue;  // 跳过英雄自身所在格 (moveHero 同格无意义)
		if (d < bestDist) { bestDist = d; best = obj; }
	}
	return best;
}

// INTERACT 目标: 优先最近己方城镇 (进城/招兵/建造/驻守), 其次最近可交互对象
const CGObjectInstance * interactTarget(CCallback * cb, const CGHeroInstance * cur)
{
	// 最近己方城镇 (owner==0)
	const CGTownInstance * bestTown = nullptr;
	int64_t bestTownDist = std::numeric_limits<int64_t>::max();
	for (const auto * t : cb->getTownsInfo())
	{
		if (!t || t->getOwner() != PlayerColor(0)) continue;
		int64_t d = distSq(t->pos, cur->pos);
		if (d < bestTownDist) { bestTownDist = d; bestTown = t; }
	}
	// 城镇在 3 格内 → 优先城镇 (可站格==heroPos 时 moveHero 到城镇格进城)
	if (bestTown && bestTownDist <= 9)
		return bestTown;
	// 否则最近可交互对象
	auto obj = nearestInteractable(cb, cur);
	if (obj) return obj;
	return bestTown;  // 兜底城镇
}

// 朝目标方向移动一格 (8 方向, N-start CW) — moveHero 单格版只允许相邻格
// 返回是否发出了移动请求
bool moveOneStepToward(CCallback * cb, const CGHeroInstance * hero, const int3 & target)
{
	if (!cb || !hero) return false;
	int dx = target.x - hero->pos.x;
	int dy = target.y - hero->pos.y;
	int dz = target.z - hero->pos.z;
	if (dz != 0) return false;  // 跨层无法单格逼近 (需要楼梯, v1 放弃)
	if (dx == 0 && dy == 0) return false;

	// N-start CW: 0=N 1=NE 2=E 3=SE 4=S 5=SW 6=W 7=NW
	static const int ddx[8] = {0, 1, 1, 1, 0, -1, -1, -1};
	static const int ddy[8] = {-1, -1, 0, 1, 1, 1, 0, -1};

	// 选移动方向: 与 (dx,dy) 夹角最小的 8 方向
	int bestDir = -1;
	int64_t bestDot = std::numeric_limits<int64_t>::min();
	for (int d = 0; d < 8; d++)
	{
		int64_t dot = (int64_t)dx * ddx[d] + (int64_t)dy * ddy[d];
		if (dot > bestDot) { bestDot = dot; bestDir = d; }
	}
	if (bestDir < 0) return false;
	try {
		int3 targetPos(hero->pos.x + ddx[bestDir], hero->pos.y + ddy[bestDir], hero->pos.z);
		cb->moveHero(hero, targetPos, false);
		return true;
	} catch(...) { return false; }
}

// 执行动作 11-24。MOVE_TO 返回目标格 (供锁外 2s 等待), 其余返回 (-1,-1,-1)。
int3 executeAdvancedAction(CCallback * cb, int a, const CGHeroInstance * cur)
{
	{FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[execAdv] a=%d\n", a); fclose(dg); } }
	const int3 noTarget(-1, -1, -1);
	if (!cb || !cur) return noTarget;

	const auto heroes = cb->getHeroesInfo();

	switch (a)
	{
	case 11: // SPLIT_1OF3: 分 1/3 兵力给最近友方英雄
	case 12: // SPLIT_1OF2: 分 1/2 兵力给最近友方英雄
	{
		auto dst = nearestAllyHero(heroes, cur);
		if (!dst) return noTarget;
		for (const auto & [slot, stack] : cur->Slots())
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
	case 13: // SPLIT_ALL: 全部兵力给最近友方英雄 (bulkMoveArmy 服务器端搬整个军队, srcSlot 仅做合法性检查)
	{
		auto dst = nearestAllyHero(heroes, cur);
		if (!dst) return noTarget;
		for (const auto & [slot, stack] : cur->Slots())
		{
			if (stack->getCreatureID() == CreatureID::NONE) continue;
			cb->bulkMoveArmy(cur->id, dst->id, slot);
			break;
		}
		break;
	}
	case 14: // MERGE_FROM: 从最近友方英雄合并全部兵力到当前英雄
	{
		auto src = nearestAllyHero(heroes, cur);
		if (!src) return noTarget;
		for (const auto & [slot, stack] : src->Slots())
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
	case 15: // SWAP_ARMY: 与最近友方英雄逐槽交换兵力 (swapCreatures 空槽↔非空槽 = 搬运)
	{
		auto other = nearestAllyHero(heroes, cur);
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
		{int nT = (int)cb->getTownsInfo().size(); FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-DIAG6] towns=%d heroPos=(%d,%d)\n", nT, (int)cur->pos.x, (int)cur->pos.y); fclose(dg); } }
		const CGTownInstance * townX = nullptr;
		try { townX = nearestOwnTown(cb, cur); } catch (const std::exception & e) { FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-DIAG6] nearestOwnTown EXC: %s\n", e.what()); fclose(dg); } } catch (...) { FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-DIAG6] nearestOwnTown EXC unknown\n"); fclose(dg); } }
		if (townX) { FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-DIAG6] town owner=%d pos=(%d,%d)\n", (int)townX->getOwner().getNum(), (int)townX->pos.x, (int)townX->pos.y); fclose(dg); } }
		auto town = nearestOwnTown(cb, cur);
		if (!town) return noTarget;
				// 2026-09-01 取兵链路修复 (P1): 招兵前确保 visit 状态 —
		// 旧逻辑: 英雄未进城时 getUpperArmy()=城驻军, 兵招进 garrison 黑洞
		// (obs garrison 恒 0 看不见, 79 集 13 取兵窗 0 效果的根因); 引擎 recruitCreatures
		// 只认 garrisonHero/visitingHero dst (CGameHandler L2438)。
		// 同 case 22 进城流程: moveHero 城锚点触发 visit (VCMI 自动弹 query 自动接受),
		// visiting 状态下 getUpperArmy()=英雄, 新兵直上英雄部队 (取兵直上设计落地)。
		fprintf(stderr, "[RL-DIAG5] townFound=%d visitedNow=%d\n", town ? 1 : 0, (cur->getVisitedTown() == town) ? 1 : 0);
		if (!cur->getVisitedTown() || cur->getVisitedTown() != town)
		{
			int3 tp = town->visitablePos();
			int3 standPos = cur->convertFromVisitablePos(tp);
			// 2026-09-01 P1 修正: 仅相邻才尝试进城 (moveHero 单格限制, 远距离必失败白等 2s);
			// 远距离 → 快速放弃本次招兵 (等 TOWN_VISIT 取兵窗引导英雄回城后再招)
			if (distSq(standPos, cur->pos) > 2)
				return noTarget;
			cb->moveHero(cur, standPos, false);
			for (int i2 = 0; i2 < 20; i2++) {
				std::this_thread::sleep_for(std::chrono::milliseconds(100));
				if (cur->getVisitedTown() == town)
					break;
			}
			for (int i3 = 0; i3 < 20; i3++) { std::this_thread::sleep_for(std::chrono::milliseconds(100)); fprintf(stderr, "[RL-DIAG5] wait i3=%d visited=%d\n", i3, cur->getVisitedTown() ? 1 : 0); if (cur->getVisitedTown()) break; }
if (!cur->getVisitedTown())
				return noTarget;  // 进城失败, 放弃本次招兵 (不招进 garrison 黑洞)
		}
{FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-RECRUIT-DIAG] visit=%d\n", (cur->getVisitedTown() == town) ? 1 : 0); fclose(dg); } }
const CArmedInstance * dst = town->getUpperArmy();
		// 2026-09-01 P1b: VCMI 1.8 getUpperArmy() = garrisonHero 或 town 本身, 不含 visiting hero
		// (实测 visit=1 但 dstIsHero=0, 兵继续进 garrison 黑洞); visit 成功后显式取
		// getVisitingHero() 作为 dst — 引擎校验 hero==getVisitingHero() 通过, 兵直上英雄
		const CGHeroInstance * vh = town->getVisitingHero();
		if (vh) dst = vh;
		const auto & creatures = town->creatures; // creatures[level(0-based)] -> {count, {base, upgrades}}
		if (a == 16 || a == 17)
		{
			int from = 0, to = (int)creatures.size() - 1, step = 1;
			if (a == 17) { from = to; to = 0; step = -1; }
			for (int i = from; step > 0 ? i <= to : i >= to; i += step)
			{
				if (i < 0 || i >= (int)creatures.size()) continue;
				// 可招募判断用 second (生物列表) 非空 — first (可招数量) 由每周 newWeek 填充, day1 可能为 0
				// 引擎侧 recruitCreatures 会自行 clamp 到 cur.first (招 0 个不扣钱=本周无兵, 正确行为)
				if (!creatures[i].second.empty())
				{
					{FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-RECRUIT-DIAG] tier=%d avail=%d dstIsHero=%d n=0\n", i, (int)creatures[i].first, (int)(dynamic_cast<const CGHeroInstance*>(dst) != nullptr), 0); fclose(dg); } }
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
					{FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[RL-RECRUIT-DIAG] tier=%d avail=%d dstIsHero=%d n=1\n", i, (int)creatures[i].first, (int)(dynamic_cast<const CGHeroInstance*>(dst) != nullptr), 1); fclose(dg); } }
					cb->recruitCreatures(town, dst, creatures[i].second.front(), 1, i);
			}
		}
		break;
	}
	case 19: // BUILD_1: 最近己方城镇建大厅链第一个未建 (村/镇/城/首都)
	case 20: // BUILD_2: 最近己方城镇建兵种链第一个未建 (1-7 级兵巢)
	case 21: // BUILD_3: 最近己方城镇建防御链第一个未建 (堡垒/要塞/城堡)
	{
		auto town = nearestOwnTown(cb, cur);
		if (!town) return noTarget;
		std::vector<BuildingID> chain;
		if (a == 19)
			chain = { BuildingID::VILLAGE_HALL, BuildingID::TOWN_HALL, BuildingID::CITY_HALL, BuildingID::CAPITOL };
		else if (a == 20)
			chain = { BuildingID::DWELL_LVL_1, BuildingID::DWELL_LVL_2, BuildingID::DWELL_LVL_3,
			          BuildingID::DWELL_LVL_4, BuildingID::DWELL_LVL_5, BuildingID::DWELL_LVL_6, BuildingID::DWELL_LVL_7 };
		else
			chain = { BuildingID::FORT, BuildingID::CITADEL, BuildingID::CASTLE };
		for (const auto & b : chain)
		{
			if (cb->canBuildStructure(town, b) == EBuildingState::ALLOWED)
			{
				cb->buildBuilding(town, b);
				break;
			}
		}
		break;
	}
	case 22: // GARRISON: 当前英雄驻守最近己方城镇 (交换访问/驻守英雄)
	{
		auto town = nearestOwnTown(cb, cur);
		if (!town) return noTarget;
		// 英雄必须 visiting 城镇才能 swapGarrisonHero (NK2 DefenceBehavior 同款)
		// 若未进城: moveHero 到城镇入口格触发进城 (VCMI 自动弹 query, AAI 自动接受)
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
				return noTarget;  // 仍未进城, 放弃
		}
		cb->swapGarrisonHero(town);
		break;
	}
	case 23: // RECRUIT_HERO: 最近己方城镇招募第一个可用新英雄
	{
		auto town = nearestOwnTown(cb, cur);
		if (!town) return noTarget;
		auto avail = cb->getAvailableHeroes(town);
		if (avail.empty()) return noTarget;
		cb->recruitHero(town, avail.front());
		break;
	}
	case 24: // MOVE_TO: 高层移动 — 朝最近可交互对象方向逐格移动 (v1: moveHero 单格版只允许相邻格)
	{
		auto target = nearestInteractable(cb, cur);
		if (!target) return noTarget;
		int3 tp = target->visitablePos();
		// moveHero 目标必须是可站格 (convertFromVisitablePos), 直接传 visitablePos 会被 BLOCK (城镇格 terrain 不可站)
		int3 standPos = cur->convertFromVisitablePos(tp);
		// 已相邻 (dist<=2): 直接 moveHero 到目标可站格触发交互; 否则朝方向走一格
		if (distSq(standPos, cur->pos) <= 2)
		{
			cb->moveHero(cur, standPos, false);
			return standPos;
		}
		if (moveOneStepToward(cb, cur, standPos))
			return standPos;  // 返回目标格供锁外等待 (实际可能只走了一格)
		return noTarget;
	}
	default:
		break;
	}
	return noTarget;
}

} // namespace

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
	in_battle = true;  // ML fix (08-27 backport)
}

void AAI::battleEnd(const BattleID & bid, const BattleResult * br, QueryID queryID)
{
	info("*** battleEnd (QueryID: " + std::to_string(static_cast<int>(queryID)) + ") ***");
	in_battle = false;  // ML fix (08-27 backport): 战斗结束, 允许 yourTurn 完成 endTurn

	battleAI->battleEnd(bid, br, queryID);

	if(cb->getBattle(bid)->battleGetMySide() == BattleSide::ATTACKER)
	{
		if(queryID.getNum() != -1)  // ML fix (08-27 backport): 守卫战斗无 CBattleDialogQuery -> queryID=-1, 跳过 replay 应答防断言崩
		{
			info("Answering query " + std::to_string(queryID) + " to re-play battle");

			asyncTasks->run(
				[this, queryID]()
				{
					std::shared_lock gsLock(CGameState::mutex);
					cb->selectionMade(1, queryID);
				}
			);
		}
	}
	else
	{
		// My patch in CGameHandler::endBattle allows replay even when
		// both sides are non-neutrals. Could not figure out how to
		// send the query only to the attacker.

		// The defender should not answer replay battle queries
		info("Ignoring query " + std::to_string(queryID));
	}

	// ML fix (08-27 backport): 战斗结束收尾挂起的回合
	bool expected = true;
	if (pending_endturn.compare_exchange_strong(expected, false)) {
		info("Battle ended, ending pending turn (delayed 0.5s)");
		asyncTasks->run([this]() {
			std::this_thread::sleep_for(std::chrono::milliseconds(500));
			cb->waitTillRealize = false;
			cb->selectionMade(0, last_query);
			cb->endTurn();
			cb->waitTillRealize = true;
		});
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
	{FILE* dg = fopen("/tmp/rl_recruit_diag.log", "a"); if (dg) { fprintf(dg, "[yourTurn] a=%d\n", a); fclose(dg); } }
	adventure_send_action(-1);

	if (a < 0) {
		cb->selectionMade(0, queryID);
		// ML fix (ring6): red yourTurn runs on the runNetwork thread; waitTillRealize=true
		// would wait for a PackageApplied that only runNetwork itself can deliver -> self-deadlock.
		cb->waitTillRealize = false;
		cb->endTurn();
		cb->waitTillRealize = true;
		return;
	}

	// act==9 (NEXT_HERO): 切换到下一个英雄, 不移动, 直接结束回合
	if (a == 9) {
		auto h = cb->getHeroesInfo();
		int n = (int)h.size();
		if (n > 0) {
			if (g_active_hero < 0 || g_active_hero >= n)
				g_active_hero = 0;  // 越界/无效回退 0
			g_active_hero = (g_active_hero + 1) % n;
		}
		// n==0 保持 g_active_hero 不变
		cb->selectionMade(0, queryID);
		// ML fix (ring6): same self-deadlock guard as a<0 path
		cb->waitTillRealize = false;
		cb->endTurn();
		cb->waitTillRealize = true;
		return;
	}

	// act==8 (INTERACT): 朝最近可交互对象移动 — 相邻则 moveHero 到目标格触发交互 (拾取/占矿/进城/对话),
	// 不相邻则朝方向走一格 (逐格逼近, v1 简化)
	if (a == 8) {
		cb->waitTillRealize = false;
		auto h = cb->getHeroesInfo();
		if (!h.empty()) {
			int hidx = g_active_hero;
			if (hidx < 0 || hidx >= (int)h.size())
				hidx = 0;
			const CGHeroInstance * cur = h[hidx];
			asyncTasks->run(
				[this, cur]()
				{
					std::shared_lock gsLock(CGameState::mutex);
					try {
						auto target = interactTarget(cb.get(), cur);
						if (target) {
							int3 tp = target->visitablePos();
							int3 standPos = cur->convertFromVisitablePos(tp);
							if (standPos == cur->pos) {
								// 已站在可站格: moveHero 到对象格本身触发交互 (进城/访问)
								cb->moveHero(cur, tp, false);
							} else if (distSq(standPos, cur->pos) <= 2) {
								cb->moveHero(cur, standPos, false);   // 相邻: 一步到位
							} else {
								moveOneStepToward(cb.get(), cur, standPos);  // 远: 朝方向走一格
							}
							// 锁外等 2s 让移动实现 (C8.5 同款)
							for (int i = 0; i < 20; i++) {
								std::this_thread::sleep_for(std::chrono::milliseconds(100));
								auto p = cur->pos;
								if (p.x == standPos.x && p.y == standPos.y && p.z == standPos.z)
									break;
							}
						}
					} catch(...) {}
				}
			);
			asyncTasks->wait();
		}
		cb->selectionMade(0, queryID);
		cb->endTurn();
		cb->waitTillRealize = true;
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
				// B 态势感知: 用 g_active_hero 选英雄, 越界回退 h[0]
				int hidx = g_active_hero;
				if (hidx < 0 || hidx >= (int)h.size())
					hidx = 0;
				int3 target(h[hidx]->pos.x + dx[a], h[hidx]->pos.y + dy[a], h[hidx]->pos.z);
				cb->moveHero(h[hidx], target, false);
				// ML fix (C8.5): 等待移动实现后再 endTurn (最多 2s), 移动失败(BLOCKED)快速继续
				for (int i = 0; i < 20; i++) {
					std::this_thread::sleep_for(std::chrono::milliseconds(100));
					auto cur = h[hidx]->pos;
					if (cur.x == target.x && cur.y == target.y && cur.z == target.z)
						break; // 已到达
				}
			} catch(...) {}
		}
	}

	// 动作 11-24: 分兵/合兵/换兵/招兵/建造/驻守/招募英雄/高层移动
	// 全部在 asyncTasks 线程内执行 (lambda 内持 CGameState::mutex 共享锁), try/catch 静默包裹
	if (a >= 11 && a <= 24) {
		auto h = cb->getHeroesInfo();
		if (!h.empty()) {
			int hidx = g_active_hero;
			if (hidx < 0 || hidx >= (int)h.size())
				hidx = 0;
			const CGHeroInstance * cur = h[hidx];
			asyncTasks->run(
				[this, a, cur]()
				{
					int3 targetPos(-1, -1, -1);
					{
						std::shared_lock gsLock(CGameState::mutex);
						try {
							targetPos = executeAdvancedAction(cb.get(), a, cur);
						} catch(...) {}
					}
					// MOVE_TO: 锁外等 2s 让移动实现, 失败(BLOCKED)快速继续 (C8.5 同款)
					if (a == 24 && targetPos.x >= 0) {
						for (int i = 0; i < 20; i++) {
							std::this_thread::sleep_for(std::chrono::milliseconds(100));
							auto p = cur->pos;
							if (p.x == targetPos.x && p.y == targetPos.y && p.z == targetPos.z)
								break; // 已到达
						}
					}
				}
			);
			asyncTasks->wait();
		}
	}

	// ML fix (08-27 backport): 战斗中不 endTurn, 挂起等 battleEnd 收尾; 兜底 CAS 防漏
	if (in_battle) {
		bool expected = false;
		if (pending_endturn.compare_exchange_strong(expected, true)) {
			last_query = queryID;
			info("yourTurn: in_battle, pending endTurn until battleEnd");
		}
		return;
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
