# VCMI 本地 fork vs 官方 8229b274 差异扫描报告

- 本地仓库：`D:\Bigdata\hero3_fresh\vcmi`（分支 fix_action_mapping, HEAD 见下）
- 官方仓库：`D:\Bigdata\hero3_fresh\vcmi-official-20260829`
- merge-base：`5dac4318fb06feae442edd7ffb5215e1920ca3e7`
- 官方 HEAD：`8229b27486558a6969304376dc8035dca33dc5d4`
- 扫描范围：`server, lib, AI`

- 本地 HEAD：5b83ace6f2b96320430c3d75b8525d8e4b41aed4 Thu Aug 27 04:40:27 2026 +0800 守卫真战斗: AAI battleEnd queryID=-1 断言修复 + in_battle 回合挂起 + showGarrisonDialog AI 自动合并残余

## 0. 提交数

| 方向 | 提交数 |
|---|---|
| 本地落后官方（官方有、本地无） | 662 |
| 本地领先官方（本地有、官方无） | 59 |

## 1. 总量

| 侧 | 改动文件数 | 新增行 | 删除行 |
|---|---|---|---|
| 官方(5dac4318→8229b274) | 828 | 12623 | 9659 |
| 本地(5dac4318→HEAD) | 244 | 32238 | 369 |

- 双方都改：62 个文件
- 仅官方改：766 个文件
- 仅本地改：182 个文件

## 2. 双方都改 = 潜在冲突文件（按官方改动量降序）

| # | 文件 | 官方 +/- | 本地 +/- | 判读 |
|---|---|---|---|---|
| 1 | `server/battles/BattleActionProcessor.cpp` | +317/-456 | +10/-4 | 官方大改 → 重点评审 |
| 2 | `server/CGameHandler.cpp` | +245/-43 | +56/-1 | 官方大改 → 重点评审 |
| 3 | `server/battles/BattleFlowProcessor.cpp` | +15/-206 | +29/-4 | 官方大改 → 重点评审 |
| 4 | `lib/gameState/CGameState.cpp` | +87/-65 | +14/-0 | 官方大改 → 重点评审 |
| 5 | `lib/battle/CBattleInfoCallback.cpp` | +121/-24 | +9/-9 | 官方大改 → 重点评审 |
| 6 | `server/battles/BattleProcessor.cpp` | +115/-10 | +20/-6 | 官方大改 → 重点评审 |
| 7 | `AI/Nullkiller2/AIGateway.cpp` | +70/-34 | +71/-7 | 官方大改 → 重点评审 |
| 8 | `lib/mapObjects/CGCreature.cpp` | +35/-39 | +1/-0 | 官方大改 → 重点评审 |
| 9 | `lib/texts/TextLocalizationContainer.cpp` | +4/-67 | +1/-1 | 官方大改 → 重点评审 |
| 10 | `lib/filesystem/MinizipExtensions.cpp` | +56/-12 | +14/-1 | 官方大改 → 重点评审 |
| 11 | `AI/MMAI/BAI/v13/stack.cpp` | +41/-13 | +6/-0 | 官方大改 → 重点评审 |
| 12 | `lib/filesystem/AdapterLoaders.cpp` | +35/-19 | +2/-0 | 官方大改 → 重点评审 |
| 13 | `lib/CStack.cpp` | +1/-45 | +3/-0 | 官方大改 → 重点评审 |
| 14 | `lib/CMakeLists.txt` | +35/-8 | +3/-2 | 官方大改 → 重点评审 |
| 15 | `server/CVCMIServer.cpp` | +34/-5 | +7/-37 | 双方均有实质改动 → 逐hunk评审 |
| 16 | `lib/battle/CUnitState.cpp` | +7/-30 | +22/-1 | 双方均有实质改动 → 逐hunk评审 |
| 17 | `lib/logging/CLogger.cpp` | +16/-18 | +5/-3 | 双方均有实质改动 → 逐hunk评审 |
| 18 | `lib/modding/ModManager.cpp` | +21/-13 | +2/-0 | 双方均有实质改动 → 逐hunk评审 |
| 19 | `server/CGameHandler.h` | +24/-9 | +7/-0 | 双方均有实质改动 → 逐hunk评审 |
| 20 | `lib/mapping/MapFormatJson.cpp` | +26/-5 | +1/-1 | 双方均有实质改动 → 逐hunk评审 |
| 21 | `lib/bonuses/CBonusSystemNode.cpp` | +7/-8 | +5/-5 | 双方均有实质改动 → 逐hunk评审 |
| 22 | `lib/battle/BattleInfo.cpp` | +7/-7 | +2/-2 | 双方均有实质改动 → 逐hunk评审 |
| 23 | `lib/logging/CLogger.h` | +3/-11 | +1/-0 | 双方均有实质改动 → 逐hunk评审 |
| 24 | `lib/StartInfo.h` | +7/-5 | +6/-0 | 双方均有实质改动 → 逐hunk评审 |
| 25 | `AI/BattleAI/BattleAI.h` | +5/-6 | +3/-3 | 双方均有实质改动 → 逐hunk评审 |
| 26 | `AI/MMAI/BAI/v13/hex.cpp` | +6/-5 | +4/-4 | 双方均有实质改动 → 逐hunk评审 |
| 27 | `AI/BattleAI/BattleAI.cpp` | +8/-1 | +4/-8 | 双方均有实质改动 → 逐hunk评审 |
| 28 | `lib/CStack.h` | +1/-8 | +3/-0 | 双方均有实质改动 → 逐hunk评审 |
| 29 | `lib/callback/CCallback.h` | +1/-8 | +2/-0 | 双方均有实质改动 → 逐hunk评审 |
| 30 | `lib/callback/CPlayerSpecificInfoCallback.cpp` | +5/-4 | +10/-2 | 双方均有实质改动 → 逐hunk评审 |
| 31 | `lib/callback/CAdventureAI.cpp` | +2/-6 | +1/-1 | 双方均有实质改动 → 逐hunk评审 |
| 32 | `server/NetPacksLobbyServer.cpp` | +8/-0 | +26/-34 | 双方均有实质改动 → 逐hunk评审 |
| 33 | `AI/MMAI/BAI/v13/hex.h` | +4/-2 | +3/-0 | 双方均有实质改动 → 逐hunk评审 |
| 34 | `AI/MMAI/BAI/v13/render.cpp` | +3/-3 | +4/-4 | 双方均有实质改动 → 逐hunk评审 |
| 35 | `lib/VCMIDirs.cpp` | +1/-5 | +30/-0 | 双方均有实质改动 → 逐hunk评审 |
| 36 | `server/battles/BattleResultProcessor.cpp` | +3/-3 | +34/-43 | 双方均有实质改动 → 逐hunk评审 |
| 37 | `lib/callback/CGameInterface.h` | +1/-4 | +3/-1 | 双方均有实质改动 → 逐hunk评审 |
| 38 | `AI/BattleAI/BattleEvaluator.cpp` | +2/-2 | +8/-2 | 官方微改 → 手工合入 |
| 39 | `AI/MMAI/BAI/router.cpp` | +2/-2 | +160/-29 | 官方微改 → 手工合入 |
| 40 | `lib/CAndroidVMHelper.cpp` | +0/-4 | +1/-0 | 双方均有实质改动 → 逐hunk评审 |
| 41 | `lib/CConfigHandler.cpp` | +0/-4 | +2/-0 | 双方均有实质改动 → 逐hunk评审 |
| 42 | `lib/VCMIDirs.h` | +0/-4 | +10/-0 | 官方微改 → 手工合入 |
| 43 | `lib/battle/BattleAction.h` | +0/-4 | +1/-0 | 双方均有实质改动 → 逐hunk评审 |
| 44 | `lib/battle/BattleAttackInfo.cpp` | +0/-4 | +0/-1 | 双方均有实质改动 → 逐hunk评审 |
| 45 | `lib/battle/BattleInfo.h` | +0/-4 | +1/-1 | 双方均有实质改动 → 逐hunk评审 |
| 46 | `lib/battle/ReachabilityInfo.cpp` | +0/-4 | +9/-4 | 官方微改 → 手工合入 |
| 47 | `lib/battle/ReachabilityInfo.h` | +0/-4 | +1/-0 | 双方均有实质改动 → 逐hunk评审 |
| 48 | `lib/battle/SideInBattle.cpp` | +0/-4 | +1/-0 | 双方均有实质改动 → 逐hunk评审 |
| 49 | `lib/callback/AIFactory.cpp` | +0/-4 | +15/-0 | 官方微改 → 手工合入 |
| 50 | `lib/callback/CBattleGameInterface.h` | +0/-4 | +4/-3 | 双方均有实质改动 → 逐hunk评审 |
| 51 | `lib/json/JsonValidator.cpp` | +0/-4 | +3/-1 | 双方均有实质改动 → 逐hunk评审 |
| 52 | `lib/network/NetworkServer.cpp` | +0/-4 | +4/-1 | 双方均有实质改动 → 逐hunk评审 |
| 53 | `lib/rmg/MapProxy.cpp` | +0/-4 | +1/-0 | 双方均有实质改动 → 逐hunk评审 |
| 54 | `lib/texts/CLegacyConfigParser.cpp` | +0/-4 | +4/-0 | 双方均有实质改动 → 逐hunk评审 |
| 55 | `AI/Nullkiller2/AIGateway.h` | +1/-2 | +1/-1 | 双方均有实质改动 → 逐hunk评审 |
| 56 | `AI/MMAI/BAI/router.h` | +1/-1 | +8/-4 | 官方微改 → 手工合入 |
| 57 | `AI/MMAI/BAI/v13/BAI.cpp` | +1/-1 | +74/-10 | 官方微改 → 手工合入 |
| 58 | `AI/MMAI/BAI/v13/battlefield.cpp` | +1/-1 | +2/-0 | 双方均有实质改动 → 逐hunk评审 |
| 59 | `AI/MMAI/BAI/v13/state.cpp` | +1/-1 | +12/-12 | 官方微改 → 手工合入 |
| 60 | `AI/StupidAI/StupidAI.cpp` | +1/-1 | +1/-6 | 双方均有实质改动 → 逐hunk评审 |
| 61 | `server/CMakeLists.txt` | +2/-0 | +8/-0 | 官方微改 → 手工合入 |
| 62 | `lib/battle/AutocombatPreferences.h` | +1/-0 | +0/-21 | 官方微改 → 手工合入 |

## 3. 仅官方改 = 可移植候选 Top60（本地未触碰，合入零冲突）

| # | 文件 | 新增 | 删除 |
|---|---|---|---|
| 1 | `lib/mapping/HotaScriptConverter.cpp` | +1010 | -0 |
| 2 | `lib/mapObjects/Quest.cpp` | +905 | -0 |
| 3 | `lib/mapObjects/CQuest.cpp` | +0 | -878 |
| 4 | `lib/mapping/MapFormatH3M.cpp` | +72 | -750 |
| 5 | `lib/rmg/CZonePlacer.cpp` | +487 | -251 |
| 6 | `AI/BattleAI/TacticsHandler.cpp` | +665 | -0 |
| 7 | `lib/battle/DamageCalculator.cpp` | +0 | -589 |
| 8 | `AI/Nullkiller2/Pathfinding/AINodeStorage.cpp` | +326 | -191 |
| 9 | `lib/rmg/CZoneGridPlacer.cpp` | +287 | -175 |
| 10 | `lib/mapObjects/Quest.h` | +373 | -0 |
| 11 | `lib/bonuses/BonusMigration.cpp` | +280 | -0 |
| 12 | `lib/mapObjects/CQuest.h` | +0 | -256 |
| 13 | `lib/json/JsonBonus.cpp` | +72 | -143 |
| 14 | `lib/scripting/ScriptHandler.cpp` | +185 | -0 |
| 15 | `AI/Nullkiller2/Engine/Nullkiller.cpp` | +148 | -36 |
| 16 | `lib/rmg/modificators/ConnectionsPlacer.cpp` | +126 | -56 |
| 17 | `lib/gameState/ReplayLog.cpp` | +170 | -0 |
| 18 | `lib/filesystem/SavegamePath.cpp` | +164 | -0 |
| 19 | `lib/gameState/GameStatePackVisitor.cpp` | +132 | -30 |
| 20 | `lib/bonuses/BonusCustomTypes.cpp` | +144 | -15 |
| 21 | `lib/texts/MetaString.cpp` | +115 | -32 |
| 22 | `lib/mapObjects/MiscObjects.cpp` | +87 | -52 |
| 23 | `lib/mapObjects/CGHeroInstance.cpp` | +76 | -49 |
| 24 | `AI/Nullkiller2/Pathfinding/AINodeStorage.h` | +85 | -38 |
| 25 | `lib/gameState/ReplayLog.h` | +121 | -0 |
| 26 | `lib/LogicalExpression.h` | +104 | -16 |
| 27 | `lib/spells/effects/SpellEffectHandler.cpp` | +0 | -120 |
| 28 | `AI/Nullkiller2/Behaviors/DefenceBehavior.cpp` | +107 | -12 |
| 29 | `AI/Nullkiller2/Engine/PriorityEvaluator.cpp` | +91 | -27 |
| 30 | `lib/campaign/CampaignState.h` | +72 | -46 |
| 31 | `lib/combatScripts/IDamageCalculatorScript.h` | +115 | -0 |
| 32 | `AI/Nullkiller2/Helpers/ExplorationHelper.cpp` | +84 | -27 |
| 33 | `lib/rmg/modificators/TownPlacer.cpp` | +83 | -18 |
| 34 | `AI/Nullkiller2/Behaviors/CaptureObjectsBehavior.cpp` | +86 | -14 |
| 35 | `lib/gameState/QuestInfo.cpp` | +85 | -12 |
| 36 | `server/battles/BattleActionProcessor.h` | +67 | -20 |
| 37 | `lib/gameState/QuestInfo.h` | +59 | -24 |
| 38 | `lib/pathfinder/NodeStorage.cpp` | +47 | -36 |
| 39 | `lib/battle/DamageCalculator.h` | +0 | -82 |
| 40 | `lib/mapObjects/CGTownInstance.cpp` | +25 | -57 |
| 41 | `lib/mapping/HotaScriptConverter.h` | +82 | -0 |
| 42 | `lib/battle/CBattleInfoEssentials.cpp` | +44 | -36 |
| 43 | `AI/BattleAI/TacticsHandler.h` | +75 | -0 |
| 44 | `lib/campaign/CampaignState.cpp` | +56 | -18 |
| 45 | `lib/entities/hero/CHeroHandler.cpp` | +60 | -14 |
| 46 | `lib/mapping/CMap.h` | +22 | -52 |
| 47 | `lib/bonuses/BonusFilter.cpp` | +71 | -0 |
| 48 | `lib/rmg/CMapGenerator.cpp` | +55 | -16 |
| 49 | `AI/Nullkiller2/Goals/ExploreNeighbourTile.cpp` | +66 | -4 |
| 50 | `lib/rmg/CMapGenOptions.cpp` | +66 | -4 |
| 51 | `lib/scripting/ScriptService.h` | +68 | -0 |
| 52 | `lib/texts/TextOperations.cpp` | +51 | -17 |
| 53 | `lib/CBonusTypeHandler.cpp` | +61 | -6 |
| 54 | `lib/networkPacks/PacksForClientBattle.h` | +50 | -17 |
| 55 | `lib/pathfinder/CPathfinder.cpp` | +26 | -39 |
| 56 | `server/processors/NewTurnProcessor.cpp` | +51 | -14 |
| 57 | `AI/Nullkiller2/Goals/CompleteQuest.cpp` | +30 | -33 |
| 58 | `lib/mapObjects/CGObjectInstance.cpp` | +48 | -15 |
| 59 | `lib/mapObjects/CGTownInstance.h` | +28 | -34 |
| 60 | `lib/spells/ISpellMechanics.cpp` | +21 | -41 |

## 4. 仅本地改 = 自研资产 Top40（官方无此文件/未改，勿覆盖）

| # | 文件 | 新增 | 删除 |
|---|---|---|---|
| 1 | `AI/MMAI/BAI/v15/state.cpp` | +2216 | -0 |
| 2 | `AI/MMAI/BAI/v14/render.cpp` | +1645 | -0 |
| 3 | `AI/MMAI/AAI/AAI.cpp` | +1183 | -0 |
| 4 | `AI/MMAI/BAI/v15/verify.cpp` | +1119 | -0 |
| 5 | `server/ML/ServerPlugin.cpp` | +1085 | -0 |
| 6 | `AI/MMAI/BAI/fallback/MLBot.cpp` | +1050 | -0 |
| 7 | `AI/MMAI/BAI/v15/render.cpp` | +769 | -0 |
| 8 | `AI/MMAI/BAI/v14/BAI.cpp` | +762 | -0 |
| 9 | `server/strategic_state.cpp` | +734 | -0 |
| 10 | `AI/MMAI/BAI/v15/nn_model.cpp` | +716 | -0 |
| 11 | `AI/MMAI/BAI/model/NNModel.cpp` | +672 | -0 |
| 12 | `AI/MMAI/schema/v14/types.h` | +643 | -0 |
| 13 | `AI/MMAI/schema/v15/constants.h` | +636 | -0 |
| 14 | `AI/MMAI/BAI/v14/nn_model.cpp` | +616 | -0 |
| 15 | `AI/MMAI/BAI/v14/battlefield.cpp` | +598 | -0 |
| 16 | `AI/MMAI/BAI/v15/graph/graph.h` | +559 | -0 |
| 17 | `AI/MMAI/BAI/v14/stack.cpp` | +554 | -0 |
| 18 | `AI/MMAI/BAI/v15/fastbfs.h` | +525 | -0 |
| 19 | `AI/MMAI/BAI/v15/BAI.cpp` | +474 | -0 |
| 20 | `AI/MMAI/BAI/v15/graph/nodes/unit.cpp` | +438 | -0 |
| 21 | `AI/MMAI/BAI/v14/encoder.cpp` | +423 | -0 |
| 22 | `AI/MMAI/BAI/v14/hex.cpp` | +423 | -0 |
| 23 | `AI/MMAI/BAI/v14/state.cpp` | +411 | -0 |
| 24 | `AI/MMAI/schema/v15/graph.h` | +344 | -0 |
| 25 | `AI/MMAI/BAI/v15/graph/graph.cpp` | +340 | -0 |
| 26 | `AI/MMAI/schema/v14/constants.h` | +326 | -0 |
| 27 | `AI/MMAI/BAI/base.cpp` | +300 | -0 |
| 28 | `server/ML/Stats.cpp` | +287 | -0 |
| 29 | `server/ML/_notes/diagrams/routing-ClientConnected-client-server.puml` | +283 | -0 |
| 30 | `server/ML/_notes/diagrams/classes-visitors.puml` | +266 | -0 |
| 31 | `AI/MMAI/BAI/v15/graph/edge_store.h` | +254 | -0 |
| 32 | `server/ML/_notes/diagrams/routing-PlayerBlocked-server-client.puml` | +231 | -0 |
| 33 | `AI/MMAI/AAI/AAI.h` | +221 | -0 |
| 34 | `server/ML/_notes/diagrams/arch-vcmi-fullyconv.puml` | +208 | -0 |
| 35 | `lib/callback/CDynLibHandler.cpp` | +205 | -0 |
| 36 | `AI/MMAI/BAI/base.h` | +203 | -0 |
| 37 | `server/ML/LICENSE` | +201 | -0 |
| 38 | `AI/MMAI/schema/v14/util.h` | +197 | -0 |
| 39 | `server/ML/_notes/diagrams/connector-sequence.puml` | +196 | -0 |
| 40 | `AI/MMAI/BAI/v15/graph/node_store.h` | +192 | -0 |
