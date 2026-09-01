# VCMI 上游差异分析报告（server / lib / AI 侧）

生成时间：2026年08月29日
对比对象：`vcmi/`（smanolloff fork + 本地 fix_action_mapping 分支） vs `upstream/develop`（官方 8229b274，2026-08-28）

---

## 一、基线与方法

| 项目 | 值 |
| --- | --- |
| 本地分支 HEAD | `5b83ace6f2`（守卫真战斗 AAI battleEnd 断言修复） |
| 上游目标 | `upstream/develop` = `8229b27486558a6969304376dc8035dca33dc5d4` |
| merge-base | `5dac4318fb06feae442edd7ffb5215e1920ca3e7` |
| 落后（upstream..HEAD 之外） | 662 个提交 |
| 本地领先 | 59 个提交 |

1. `vcmi-official-20260829/` 是 `depth=1` 浅克隆，只有 1 个提交，**无法**参与 merge-base 计算，只能当"最新版源码快照"用于阅读。
2. 本报告改用子模块内已存在的 `upstream` 远程（其 `upstream/develop` 已指向 8229b274），可直接得到"纯粹的 662 个上游提交改了什么"，不会混入本地 59 个定制提交。
3. 冲突判定一律用 `git merge-tree --write-tree`（真实三方合并）预演，**不动工作区**，结果可信度高于人工估计。

---

## 二、变更规模总览

| 目录 | 变更文件 | 新增行 | 删除行 | 说明 |
| --- | --- | --- | --- | --- |
| `server/` | 38 | 1057 | 839 | 含 288 行的 CGameHandler.cpp |
| `AI/` | 84 | 2201 | 625 | 大头是 NK2 寻路 |
| `lib/` | 706 | 9365 | 8195 | 大头是 MetaString / 翻译重构 |
| 合计 | 828 | 12623 | 9659 | |
| 全仓库（含 client/test 等） | 1809 | — | — | |

1. 本地 59 个提交共改动 **328** 个文件。
2. 与上游 1809 个文件的**真实交集是 71 个文件**——这才是实际冲突面（此前整体合并遇到的 22 个冲突就落在这批里）。
3. 交集里与本项目强相关的：`server/CGameHandler.cpp`、`server/CGameHandler.h`、`server/battles/*`、`AI/Nullkiller2/AIGateway.cpp/.h`、`AI/MMAI/BAI/*`、`lib/battle/*`、`lib/pathfinder/*`。

---

## 三、冲突根因分类（重要）

预演发现冲突分两类，处理方式完全不同。

### 3.1 机械漂移（易解）

典型代表：`662c819065 Remove VCMI namespace macro`

1. 该提交一次性改动 **1004 个文件**（+31 / -3785），删除 `VCMI_LIB_NAMESPACE_BEGIN/END` 宏。
2. 本地树停在 `5dac4318`（宏删除之前），凡是上游补丁上下文落在文件头尾（宏所在位置）的，都会撞上。
3. 这类冲突**不含语义分歧**，解法就是删掉对应两行宏，零风险。

### 3.2 真实语义分歧（需判断）

典型代表：`moveHero()` 内的 `passableFor()` 参数

1. 本地（ours）：`object->passableFor(h->tempOwner)`
2. 上游（theirs）：`object->passableFor(h)`
3. 由 `406116c30b Better Quest Gate suport`（属大特性 PR #7535 seer_rework）引入。
4. 由于 seer_rework 是整块任务系统重构，不建议零散摘取，需整体评估。

---

## 四、可移植性实测结果（cherry-pick 预演）

### 4.1 推荐移植（高性价比）

| 目标 | 提交 / PR | 组成 | 预演结果 | 处置建议 |
| --- | --- | --- | --- | --- |
| NK2 寻路性能优化 | PR #7632 `starius/optimize` | 11 提交 | **9 CLEAN / 2 冲突** | 整包摘，2 个冲突均为单头文件机械漂移 |
| 地图加载加速 | PR #7744 `mapload_speedup` | 8 提交 | **7 CLEAN / 1 冲突** | 整包摘，唯一冲突是测试文件 modify/delete，直接丢弃 |
| 胜负判定-神器即胜 | `f4c622c842` | 1 提交 | **CLEAN** | 直接摘 |
| 移动层传播修复 | `0981f48837` | 1 提交 | **CLEAN** | 直接摘（PR #7692 主提交） |
| 下船落水检查 | `15034e38c9` | 1 提交 | **CLEAN** | 直接摘 |

### 4.2 需人工介入（冲突但可控）

| 目标 | 提交 / PR | 冲突文件 | 性质 | 建议 |
| --- | --- | --- | --- | --- |
| 序列化重分配优化 | PR #7756（3 提交） | `lib/serializer/BinaryDeserializer.h` | 语义 | 1 冲突 / 2 CLEAN，值得解 |
| 传送门查找 O(n) 修复 | PR #7774 `b932db71c8` | `lib/gameState/CGameState.cpp` | 语义 | 单文件，可解 |
| Lua 并行执行 | `7526787a67` | `LuaContext.h`、`LuaScriptPool.h` | 语义 | 收益小，优先级低 |
| Lua 伤害计算优化 | `4f041e7458` | `scripts/combat/damageCalculator.lua` | modify/delete | 上游后已删除该文件，跳过 |
| NK2 丢失英雄防护 | `fba66e3060` | `AI/Nullkiller2/AIGateway.cpp` | 真实冲突 | 本地该处改了 72 行，需人工合 |
| NK2 守军升级 | `8b9796ad35` | 仅 `test/server/queries/QueriesProcessorTest.cpp` | 测试文件 | 若只要源码，跳过测试即可 |

### 4.3 不建议零散摘取

1. `c9023e74c1` 边境守卫（Do not allow going through border guards without keymaster visit）
   1. 冲突点：`server/CGameHandler.cpp` 的 `moveHero()`。
   2. 已按时间序先落地 `0981f48837`、`15034e38c9` 两个前置，**仍然冲突**。
   3. 根因是依赖 `406116c30b`（seer_rework 大重构），该提交自身在 `CGObjectInstance.h`、`CQuest.cpp`、`CQuest.h` 三处冲突。
   4. 结论：要么整包引入 seer_rework，要么放弃此条。
2. MetaString / 翻译系统重构（`95a6980281`、`6589c53399`、`9bfa70aa81`、`239cecec51`、`46345c022f`）
   1. 横跨 lib / server / AI 三侧，是 `lib/` 9365 行新增的主要来源。
   2. 与本地定制无交集，但对 MMAI 无任何收益，属于纯重构噪音。
   3. 结论：跳过。

---

## 五、PR #7632（NK2 寻路性能）逐提交明细

时间序（全部为 2026-07-24，**早于** 8-21 的翻译重构，故自包含无外部依赖）：

| 序 | 提交 | 说明 | 预演 |
| --- | --- | --- | --- |
| 1 | `296828ce4a` | Reuse unobserved pathfinding buffers | CLEAN |
| 2 | `6298f44a83` | Initialize regular path nodes on first use | **CONFLICT** `lib/pathfinder/NodeStorage.h` |
| 3 | `55f44328bb` | Reuse priority evaluation contexts across tiers | CLEAN |
| 4 | `f6c59fd179` | Cache Dimension Door capabilities per path update | CLEAN |
| 5 | `7558d8c514` | Tune AI parallel loop grain sizes | CLEAN |
| 6 | `48e2fd929f` | Evaluate AI path accessibility on first use | **CONFLICT** `AI/Nullkiller2/Pathfinding/AINodeStorage.h` |
| 7 | `e947e7e819` | Allocate AI path states only for occupied tiles | CLEAN |
| 8 | `770a9c1afb` | Filter exploration candidates before rebuilding paths | CLEAN |
| 9 | `13c7c7c2f1` | Drop redundant unique pointer tracking | CLEAN |
| 10 | `6e70ff6bc2` | Avoid invalidating unchanged bonus branches | CLEAN |
| 11 | `0f139ff6d6` | Match AI spell reward evaluation to granting | CLEAN |

1. 两个冲突**只各涉及 1 个头文件**，且本地均未改动过这两个文件（已用 `git diff 5dac4318..HEAD` 核实为空）。
2. 冲突根因：`662c819065` 命名空间宏重构。证据——冲突三方中 ours 侧的 blob `dca8f17245` 正是带宏版本，base/theirs 为 `359e3603b1`（已删宏）。
3. 第 10 项 `6e70ff6bc2` 虽触碰 `lib/bonuses/CBonusSystemNode.cpp`（在 71 文件交集内），实测 **CLEAN**，本地改动落在不同区域。
4. 整包真实改动：22 文件 / +742 / -345（排除 test 后）。

---

## 六、PR #7744（地图加载加速）逐提交明细

| 序 | 提交 | 说明 | 预演 |
| --- | --- | --- | --- |
| 1 | `7d4655fde6` | Cache iconv conversion descriptors per thread | **CONFLICT** 仅测试文件 modify/delete |
| 2 | `6515369134` | Use shared_mutex for filesystem loader file list | CLEAN |
| 3 | `c6cffb5ff7` | Resolve full file path of map entries on demand | CLEAN |
| 4 | `d78ec174ce` | Avoid copying active mod list on every resource lookup | CLEAN |
| 5 | `eeeab112f7` | Reuse already resolved mod when determining resource encoding | CLEAN |
| 6 | `ccb37a2d4c` | Locate resource once per filesystem list lookup | CLEAN |
| 7 | `76d2faf5ac` | Decompress map headers in blocks instead of field by field | CLEAN |
| 8 | `14734563a2` | Precompute set of heroes allowed by default on map load | CLEAN |

1. 唯一冲突是 `test/texts/TextOperationsTest.cpp`（该文件后被上游删除），与训练用的 `vcmi-native` 无关，摘取时排除 test 目录即可。
2. 该项对训练吞吐最直接（每次开图都要走一遍加载路径），**建议优先于 NK2 性能优化落地**。

---

## 七、与 MMAI 直接相关的改动

1. `server/processors/TurnOrderProcessor.cpp`（endTurn 专题）
   1. `doStartPlayerTurn()` 现在按**人类 / AI 分流**调用 `onPlayerTurnStarted()`。
   2. 人类：先 `sendAndApply(pst)`，再 `onPlayerTurnStarted()`——让客户端先进入新回合流程，避免 Battle Scholar Academy 之类的延迟访问先弹对话框。
   3. AI：保持原顺序，先 `onPlayerTurnStarted()` 再 `sendAndApply(pst)`。
   4. 对 MMAI 的影响：AI 分支维持旧行为，但需确认本地分支是否复刻了人类分支的修正。
2. `AI/Nullkiller2/AIGateway.cpp`（本地已改 72 行）
   1. 上游在 `0981f48837` 中改了 28 行（移动层传播）。
   2. 上游在 `fba66e3060` 中改了丢失英雄防护，与本地改动**真实冲突**。
3. `server/CGameHandler.cpp`（本地已改 56 行 / 7 处 hunk）
   1. 本地改动位置：`init`、`giveSpells`、`showBlockingDialog`、`queryReply`、`showGarrisonDialog`、`isBlockedByQueries`。
   2. **未触碰** `moveHero()`——因此 moveHero 区域的冲突全部来自上游漂移，而非本地定制。

---

## 八、建议执行顺序

1. 第一步，摘 PR #7744 地图加载加速（test 目录除外），风险最低、收益最直接。
2. 第二步，摘 PR #7632 NK2 寻路性能，手工解 2 个命名空间宏冲突。
3. 第三步，摘 `f4c622c842`、`15034e38c9`、`0981f48837` 三个 CLEAN 的逻辑修复。
4. 第四步，评估 `TurnOrderProcessor` 的 AI/人类分流是否需要同步到本地。
5. 暂缓，seer_rework（PR #7535）与 MetaString 重构整包。

---

## 九、复核方法备忘

1. 冲突预演命令（不碰工作区）：

```bash
git merge-tree --write-tree --merge-base=<commit>^ <本地tree> <commit>
```

返回码 0 且无 `CONFLICT` 字样即为可干净 cherry-pick。链式预演时每次取输出首行作为下一次的输入 tree。

2. 判断冲突性质：取冲突三方的 blob，用 `git show <commit>:<path>` 对比 ours 与 theirs，即可区分"本地定制冲突"与"上游漂移冲突"。
