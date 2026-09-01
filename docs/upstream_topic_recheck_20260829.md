# 三专题重核报告：moveHero 链路 / 胜负判定 / endTurn

生成时间：2026年08月29日
对比基准：本地 `fix_action_mapping`（HEAD `5b83ace6f2`） vs 官方 `8229b274`（2026-08-28）
前置报告：`docs/upstream_diff_report_20260829.md`（步骤①差异分析）

---

## 结论速览

| 专题 | 核心逻辑是否变化 | 必须处理项 | 对 MMAI 影响 |
| --- | --- | --- | --- |
| moveHero 链路 | **是**，7 处差异 | 移植前须给 MMAI 补 layer 参数 | **破坏性** |
| 胜负判定 | 核心**未变** | 补 `sendAndApply(CArtifactOperationPack&)` | 影响胜利结算时机 |
| endTurn | 核心**未变** | 无（分流改动对 AI 无影响） | **无影响** |

---

# 专题一：moveHero 链路

## 1.1 差异总表

`moveHero()` 本地 837-1112 行 vs 官方 853-1145 行，共约 61 行差异，分 7 处。

| 序 | 差异点 | 本地 | 官方 | 上游来源 | 处置 |
| --- | --- | --- | --- | --- | --- |
| 1 | `hasDisembarkIntent` | 多出 `isForcedBoatDisembark` 强制分支 | 仅 `(layer == LAND)` | `943d26b0a8` 引入 / `0981f48837` 删除 | 移植 `0981f48837` 取代 |
| 2 | layer 合法性校验 | **无** | 新增 `requiresLayer` 校验 | `0981f48837` | **破坏性，见 1.2** |
| 3 | `getMovementCost` | 传 `nullptr`（不区分层） | 传 `layer` + `usesMovementCost` 门控 | `0981f48837`（PR #7692） | 修航行 MP 算错 |
| 4 | 下船落水检查 | 仅查 `t.blocked()` | 增加 `isTileBlockedByHole()` | `15034e38c9` | 直接摘（CLEAN） |
| 5 | `passableFor` 参数 | `passableFor(h->tempOwner)` | `passableFor(h)` + `requiresQuestToPass()` | `c9023e74c1` + `406116c30b` | **放弃**（依赖 seer_rework） |
| 6 | BeforeVisitSave 路径 | 硬编码 `"Saves/BeforeVisitSave"` | `SavegamePath::getPath()` | 存档目录整理 | 可选 |
| 7 | `getNameTranslated()` | 旧 API | `getNameTextID()` | MetaString 重构 | 跳过 |

## 1.2 ⚠️ 破坏性变更：layer 合法性校验

官方新增（本地没有）：

```cpp
const bool requiresLayer = movementMode == EMovementMode::STANDARD && dst != h->pos;
const bool hasValidLayer = layer >= EPathfindingLayer::LAND && layer < EPathfindingLayer::NUM_LAYERS;
if(requiresLayer && !hasValidLayer)
    return complainRet("Invalid movement layer!");
```

枚举定义（`lib/constants/EntityIdentifiers.h:726`）：

```
LAND = 0, SAIL = 1, WATER, AVIATE, AIR, NUM_LAYERS, WRONG, AUTO
```

1. 合法区间是 `[0, 5)`，即 `LAND/SAIL/WATER/AVIATE/AIR`。
2. **`WRONG = 6`、`AUTO = 7` 均不合法。**
3. `CCallback::moveHero(destination)` 的默认参数**正是 `AUTO`**：

```cpp
void moveHero(const CGHeroInstance *h, const int3 & destination, bool transit,
              const EPathfindingLayer & layer = EPathfindingLayer::AUTO) override;
```

4. 因此：任何使用 3 参数形式（不显式传 layer）的**真实移动**（`dst != h->pos` 且 `STANDARD`）都会被直接拒绝。

### 上游自身的合规写法

官方 `AIGateway.cpp` 三处调用中：

| 行号 | 调用 | 是否安全 |
| --- | --- | --- |
| 1061 | `cc->moveHero(*heroPtr, convertFromVisitablePos(dst), false)` | 安全——位于 `if(startHpos == dst)` 分支内 |
| 1114 | `cc->moveHero(*heroPtr, ..., transit, layer)` | 显式传 `nextNode.layer`，取自寻路节点 |
| 1127 | `cc->moveHero(*heroPtr, heroPtr->pos, false)` | 安全——`dst == pos` |

**规则：真实移动必须显式传 layer，且 layer 来自寻路节点。**

## 1.3 MMAI 待修点（6 处）

`AI/MMAI/AAI/AAI.cpp` 中 6 处调用全部使用 3 参数形式，均为真实移动：

| 行号 | 调用 | 场景 |
| --- | --- | --- |
| 164 | `cb->moveHero(hero, targetPos, false);` | 8 方向逐格逼近 |
| 308 | `cb->moveHero(cur, standPos, false);` | 进城：移动到城镇入口格 |
| 340 | `cb->moveHero(cur, standPos, false);` | MOVE_TO 高层移动 |
| 565 | `cb->moveHero(cur, tp, false);` | 站可站格时移动到对象格 |
| 567 | `cb->moveHero(cur, standPos, false);` | 相邻一步到位 |
| 603 | `cb->moveHero(h[hidx], target, false);` | 通用移动 |

**移植 `0981f48837` 前不修这 6 处，MMAI 所有英雄移动会被全部拒绝。**

### 修复方案

`EPathfindingLayer` 所在头文件 `lib/constants/EntityIdentifiers.h` 已在 `AAI.cpp` include 列表内（第 25 行），无需新增 include。

可用 API（均已核实）：

1. `cb->getTile(int3, bool verbose = true)` — 声明于 `lib/callback/CGameInfoCallback.h:83`，public，`CCallback` 经 `CPlayerSpecificInfoCallback` 继承可得。
2. `TerrainTile::isLand()` — 定义于 `lib/mapping/TerrainTile.h:109`。
3. `hero->inBoat()` / `hero->getBoat()->layer`。

建议新增辅助函数并按调用点替换：

```cpp
// 计算单格移动应使用的寻路层；英雄在船上且目标是陆地时按登岸(LAND)处理
static EPathfindingLayer layerForSingleStep(CCallback * cb, const CGHeroInstance * h, const int3 & dst)
{
	if(h->inBoat())
	{
		const auto * tile = cb->getTile(dst, false);
		if(tile && tile->isLand())
			return EPathfindingLayer::LAND;   // 登岸
		return h->getBoat()->layer;
	}
	return EPathfindingLayer::LAND;
}
```

调用点改为：

```cpp
cb->moveHero(hero, targetPos, false, layerForSingleStep(cb, hero, targetPos));
```

## 1.4 `isForcedBoatDisembark` 是已废弃的旧 hack

1. 由 `943d26b0a8`（2026-06-01，Refactor disembarking condition）引入。
2. 该提交是 `5dac4318` 的**祖先**——即本地分支是从 fork 继承来的旧代码，**不是**本地自研补丁（已用 `git merge-base --is-ancestor` 证实）。
3. `0981f48837`（2026-08-10）沿 AI → CCallback → CPathfinder → server 全链路透传 layer，从根上解决，并删除该 hack。
4. 结论：移植 `0981f48837` 即自动替换，**不要**手工保留本地这段逻辑。

## 1.5 为何放弃 `c9023e74c1`（边境守卫）

1. 冲突内容：`object->passableFor(h->tempOwner)` [本地] vs `object->passableFor(h)` [官方]。
2. 该差异由 `406116c30b Better Quest Gate support` 引入，属大特性 PR #7535（seer_rework，任务系统重构）。
3. `406116c30b` 自身在 `CGObjectInstance.h`、`CQuest.cpp`、`CQuest.h` 三处冲突。
4. 时间序前置 `0981f48837`、`15034e38c9` 落地后重测**仍然冲突**，故零散摘取不可行。

---

# 专题二：胜负判定

## 2.1 核心逻辑未变（已逐字节比对）

以下函数本地与官方**完全一致**，无需任何改动：

1. `CGameHandler::checkVictoryLossConditions(const std::set<PlayerColor> &)`
2. `CGameHandler::checkVictoryLossConditionsForAll()`
3. `CGameHandler::checkVictoryLossConditionsForPlayer(PlayerColor)`
4. `CGameHandler::getVictoryLossMessage(...)`
5. lib 侧 `CGameState::checkForVictoryAndLoss` —— 用 `git log -S` 在 `5dac4318..upstream/develop` 范围内检索，**无任何提交改动**。

## 2.2 唯一差异：神器操作不触发胜负检查

`f4c622c842 Grant victory instantly on receiving victory-granting artifact in quest`

官方新增（本地完全没有 `CArtifactOperationPack` 这个重载）：

```cpp
void CGameHandler::sendAndApply(CArtifactOperationPack & pack)
{
	sendAndApply(static_cast<CPackForClient &>(pack));
	checkVictoryLossConditionsForAll();
}
```

同时删除 `assembleArtifacts()` 末尾的窄检查：

```cpp
-	checkVictoryLossConditionsForPlayer(hero->getOwner());
```

### 影响分析

| 状态 | 行为 |
| --- | --- |
| 本地 | 神器相关操作**完全不触发**胜负检查；仅在 `assembleArtifacts`（组装/拆卸神器）时检查该英雄所属玩家 |
| 官方 | 任何神器操作都触发**全玩家**胜负检查 |

1. 胜利条件为"收集神器 X"或"运送神器至城镇"时，本地要等到下一次无关的全量检查（如新回合的 `checkVictoryLossConditionsForAll`）才结算胜利。
2. 对训练的影响：可能出现"AI 已完成胜利条件但本回合未判胜"的偏差，导致回合数统计与奖励信号失真。
3. 另注：本地第 1396 行对应处的 `checkVictoryLossConditionsForPlayer(hero->tempOwner); //transported artifact?` 两边一致，非差异点。

### 移植性

`f4c622c842`：2 文件 / +8 / -2，**cherry-pick 预演 CLEAN**，可直接摘。

---

# 专题三：endTurn

## 3.1 核心逻辑未变

| 函数 | 结论 |
| --- | --- |
| `TurnOrderProcessor::onPlayerEndsTurn(PlayerColor)` | 本地 340 行 / 官方 357 行，**逐字节一致** |
| `CGameHandler::onPlayerTurnStarted(PlayerColor)` | 本地 630 行 / 官方 639 行，**逐字节一致** |
| `PlayerMessageProcessor` | 仅 MetaString 文本 ID + SavegamePath 改动，无回合逻辑变化 |

## 3.2 唯一变化：`doStartPlayerTurn` 按人类/AI 分流

提交：`e250a179b7 Send PlayerStartsTurn before deferred turn-start visit dialogs`（1 文件 / +21 / -4，**预演 CLEAN**）

```cpp
if(isHuman)
{
	gameHandler->sendAndApply(pst);
	// 先让客户端进入新回合流程，避免延迟访问(如 Battle Scholar Academy)抢先弹对话框
	if (!wasAlreadyActing)
		gameHandler->onPlayerTurnStarted(which);
}
else
{
	// AI 从 PlayerStartsTurn/yourTurn 立即开始行动，保持原顺序
	if (!wasAlreadyActing)
		gameHandler->onPlayerTurnStarted(which);

	gameHandler->sendAndApply(pst);
}
```

**关键：AI 分支保持改动前的原顺序。** 因此对纯 AI 对战/训练场景**行为完全不变**，移植与否都不影响 MMAI。该改动只修人类客户端的对话框时序问题。

## 3.3 NewTurnProcessor 中的可选修复

`a913005722 Do not select creatures without map object for special weeks`（1 文件 / +27 / -8，**预演 CLEAN**）

1. 修复内容：特殊周（如 DOUBLE_GROWTH 双倍生长）不再选没有地图物件的生物——这类生物无法作为游荡怪生成，选中会导致特殊周实际无效果。
2. 对训练的影响：若训练图随机到特殊周，本地可能选中无效生物，造成环境动态与官方不一致。建议摘。

NewTurnProcessor 其余改动（Lua `MapEventDispatcher` 脚本钩子、`ScenarioEventJournalInfo`、MetaString 文本 ID）为特性扩展与重构，与训练无关，跳过。

---

# 行动清单（按优先级）

1. **阻断项**：移植 `0981f48837` 前，先给 `AI/MMAI/AAI/AAI.cpp` 的 6 处 `moveHero` 补 layer 参数（见 1.3）。
2. 摘 `0981f48837`（移动层传播，CLEAN）——同时自动替换掉废弃的 `isForcedBoatDisembark` hack。
3. 摘 `f4c622c842`（神器操作触发胜负检查，CLEAN）。
4. 摘 `15034e38c9`（下船落水检查，CLEAN）。
5. 摘 `a913005722`（特殊周生物过滤，CLEAN）。
6. 可选摘 `e250a179b7`（回合分流，CLEAN，对 AI 无影响）。
7. 后续：PR #7744 地图加载加速 → PR #7632 NK2 寻路性能（见步骤①报告第八节）。
8. 放弃：`c9023e74c1`、seer_rework 整包、MetaString 重构。

---

# 复核方法备忘

1. 抽取对比函数时**不要**用固定行号偏移（两边行号不同会错位）——先用 `grep -n` 定位函数起始行，再各自 `sed -n` 抽取。
2. 判断某逻辑是否被上游改动：`git log -S "<关键标识符>" <base>..upstream/develop -- <path>`，比 `--grep` 精确。
3. 判断本地代码是"自研"还是"继承自 fork"：`git merge-base --is-ancestor <commit> <merge-base>`，成立即为继承。
4. 枚举类校验类改动务必回查默认值——默认参数落在合法区间之外是最隐蔽的破坏性变更。
