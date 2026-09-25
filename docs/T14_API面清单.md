# T14.1 API 面定谳清单（蓝方战略 AI 能否用 Lua 实现）

> 09-25 T14.1 摸底产出。**结论先行：蓝方战略层 AI 无法用 Lua 实现，必须走 C++ `CAdventureAI` 子类（NK2 同构）。** 任务单原「纯 Lua MOD」前提不成立，六-B 拆解已据此改路线。

## 一、两大前提勘误

1. **NK2（Nullkiller2）是纯 C++，不是 Lua**。
   - 实际位置 `vcmi/ai/Nullkiller2/`（子模块内，非 `vcmi-native`；任务单原写 `ai/Nullkiller/*.lua` 路径+语言均误）。
   - 全 `.cpp/.h`：`AIGateway.cpp`(58KB) / `Engine/PriorityEvaluator.cpp`(63KB) / `Engine/Nullkiller.cpp` / `Behaviors/*`(13 个) / `Goals/*`(20+) / `Analyzers/*`(5 个)。无一个 `.lua`。
   - 入口 = `AIGateway : public CAdventureAI`（继承冒险层 AI 接口，`yourTurn(QueryID)` 被引擎调用 → 自己规划 → `endTurn`）。

2. **VCMI 的 `luascript/` 是 MOD 脚本运行时（读数据 + 战斗控制），不是 AI 运行时。**
   - 仓库内 `.lua` 全是 spell effect / 战斗单位效果脚本（`damage.lua`/`summon.lua`/`unitEffect.lua`…），**没有战略 AI 脚本**。
   - Lua 层暴露的 API 面（`luascript/api/Registry.cpp` 全量登记）见下。

## 二、Lua 层实际暴露的 API 面（权威清单）

来源：`luascript/api/Registry.cpp` 的 `Registry()` 注册块 + 各 `*Proxy::registerMethods`。

**A. 只读接口（library / adventure）**
| 类型 | 能力 | 注 |
|------|------|-----|
| `Services` | library 数据查询（creature/spell/artifact/faction…） | 只读 |
| `HeroInstance` | `getStack(slot)`/`getOwner()`/`getNameTextID()`/`isMale`/`isFemale` + BonusBearer 绑定 | **纯读，0 个动作方法** |
| `StackInstance` | 读队伍 | 只读 |
| `Creature`/`Faction`/`HeroClass`/`HeroType`/`Skill`/`Spell`/`SpellSchool`/`Artifact` | 静态数据 | 只读 |
| `IBattleInfoCallback`/`IGameInfoCallback` | 读 battle/game 状态 | 只读 |
| `Enums` | 枚举 | — |

**B. 战斗域 mutation（`ServerCallback`，仅 server 侧脚本，battle 域）**
`addUnit` / `removeUnit` / `removeObstacle` / `moveUnit(battleHex)` / `appendLog` / `describeChanges` / `removeUnitBonuses` / `addUnitBonus` / `addBattleBonus` / `addObstacle` / `catapultAttack` / `rngInt` / `healUnit` / `changeUnit` / `damageUnit`。
→ 全是**战斗内**改单位/改伤害/改障碍，**不含任何冒险层战略动作**。

**C. 战斗域读/微调（`battle/*`）**
`BattleHex`/`BattleHexArray`/`Unit`(含 `setCastSpellThisTurn`) / `LuaUnitState` / `Obstacle` / `spells.Mechanics` / `spells.Problem`。

## 三、缺口定谳（决定路线的关键）

| 战略动作 | Lua 是否暴露 | 战略 AI 必需性 |
|----------|:---:|:---:|
| 移动英雄 / 战略寻路 | ❌ 无 | 必需 |
| `endTurn` / `yourTurn` 回合驱动 | ❌ 无 | 必需 |
| 招募英雄 / 招募部队 | ❌ 无 | 必需（经济线） |
| 建筑 / 升级建筑 | ❌ 无 | 必需（城建线） |
| 购买宝物 | ❌ 无 | 中 |
| 战略层施法（回城术/飞行奇术等） | ❌ 无（只有战斗 spell 读） | 高（handicap 类） |
| 占领对象（矿/城/酒馆） | ❌ 无 | 必需 |

**判定**：不是「缺 1-2 项」，而是**整个冒险层动作面在 Lua 里都不存在**。Lua 运行时定位 =「**冒险层只读 + 战斗层读写**」，服务于改 spell / 改战斗单位 / 读数据做 UI 的 MOD，**驱动不了一个玩家走完自己的战略回合**。

## 四、可执行路线（修正后）

| 路线 | 可行性 | 说明 |
|------|:---:|------|
| ❌ 纯 Lua 蓝方战略 AI | 不可行 | 无冒险层动作 API（本清单 C 节全 ❌） |
| ✅ **C++ 新 AI 模块（NK2 同构，推荐）** | 可行 | 写 `T14BlueAI : public CAdventureAI`，实现 `yourTurn` 内规则状态机 + 5 原型 seed 参数化；注册进 `ai/` CMake（加一个 `add_subdirectory`，与 NK2/MMAI/StupidAI 平级）+ AIFactory 加一个名字。**只编新 AI .so，不碰 libvcmi.so（铁律 3 边界内）**。蓝方可插拔 = AI 选择参数化，NK2 一键回退 |
| △ Lua 辅助 MOD（非战略） | 可行但价值低 | 只做战斗层微调（仿 AMER_HumanAI 的 DemonFarm/LossRecovery/Necromancy 三条战斗启发），不产蓝方对手，排除出 T14 |

**代价重估**：路线 B 要**编译**（新 AI 模块，非热插拔 Lua），从「纯 Lua 零重编」变为「C++ 编译新 .so」。仍符合铁律 3（不重编引擎本体，加编译单元）。NK2 的 `Goals/`+`Behaviors/`+`PriorityEvaluator` 骨架可直接抄结构、只换规则权重与原型参数。

## 五、T14.1 判定

- API 面清单 ✅ 完整，每项有源文件锚（`Registry.cpp` / `HeroInstance.cpp` / `ServerCallback.h` / `CAdventureAI.h` / `CGameInterface.h`）。
- **核心结论**：招募/城建/购宝物/移动/结束回合 **Lua 全不暴露**（比「缺 1 项」严重）→ 纯 Lua 路线否决，改 **C++ 新 AI 模块**。
- **无「API 面仅剩 move+endTurn」的弱对手风险**——那套风险是针对 Lua 假设的；C++ 路线里 `CGameInterface`/`CAdventureAI` 暴露的是完整战略面（`yourTurn` 全权 + 可读 `env`/`env->` 数据），MOD 上限由「你写的规则」决定，不由 API 面卡死。

## 六、给 T14.2-T14.4 的输入

- T14.2 规则设计：骨架抄 `ai/Nullkiller2/{Goals,Behaviors,Engine}`；AMER_HumanAI 三条战斗启发（Necromancy/DemonFarm/LossRecovery）降级为「可选 Lua 战斗层辅助 MOD」，不进战略主路线；handicap 参数（日金/回城术 L20/飞行 L28 等）改为 C++ 侧读 `Settings`（`Engine/Settings.cpp`）或地图属性。
- T14.3 实现：落 `vcmi/ai/T14BlueMod/`（C++，CMake `add_subdirectory` + `ENABLE_T14_BLUE_AI` 门控）+ AIFactory 注册名 `t14blue`；KTV 冒烟需一次 AI 模块重编。
- T14.4 验收不变（NK2 基线 N≥4，DRAW 率 / go 字段 / 同 seed 可复现）。
