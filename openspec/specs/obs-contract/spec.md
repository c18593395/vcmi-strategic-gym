# OBS schema v3 双端对齐契约（OBS_DIM=3464）

## Purpose

战略 Gym obs 布局契约：C 端（`vcmi/ML/strategic_state.h` + ModelAI DLL obs_fill）与
Python 端（`py/strategic_reader.py` ctypes）字段序 / 维度 / 语义必须完全一致。

- 字段明细真相源：`docs/动作空间设计文档.md` v2（§2.1 十三段布局 + §2.2 字段级明细，全部有源码依据；OBS_DIM 2689→3464，`_version` 2→3）
- 本 spec 只锁"双端对齐不可破坏"的 SHALL 级行为；段/字段细节指针到设计文档，不重复抄表。
- 任何 obs 布局变更须先改本 spec，再动代码。

## Requirements

### Requirement: 3464 段布局冻结

OBS_DIM SHALL = 3464；段序 SHALL 按设计文档 §2.1 固定：

| 偏移 | 段 | 维度 |
|---|---|---|
| [0:8] | global | 8 |
| [8:128] | players 8×15 | 120 |
| [128:336] | heroes 8×26 | 208 |
| [336:480] | towns 8×18 | 144 |
| [480:1155] | local 15×15×3 | 675 |
| [1155:3203] | global_explored 32×32×2 | 2048 |
| [3203:3211] | active_hero + 7 pad | 8 |
| [3211:3219] | passable | 8 |
| [3219:3251] | nav | 32 |
| [3251:3315] | target_list 8×8 | 64 |
| [3315:3322] | enemy_threat | 7 |
| [3322:3326] | battle_pred | 4 |
| [3326:3330] | events | 4 |
| [3330:3464] | reserved | 134 |

冻结后禁止：增删维度、改字段语义、重排段序。
允许：填充 reserved / target_list 预留段、启用预留动作码（25-63）。
任何违反冻结规则的动作 = 用户书面批准 + 全量重采集评估。

#### Scenario: passable 固定偏移

- **WHEN** C/Python 任一端计算 passable 段位置
- **THEN** 偏移固定为 [3211:3219]（v3 起禁止用 `OBS_DIM - 8` 反推，防止未来扩维漂移）

### Requirement: 双端字段序自动对照门禁

C 头（`vcmi/ML/strategic_state.h`）与 Python ctypes（`py/strategic_reader.py`）、
以及 DLL `obs_fill` 端，任何一端 obs 相关改动后，SHALL 运行 `py/_schema_check.py`
（冒烟 #16：字段顺序错位 / 遗漏 / 类型不一致检测）全过，才允许部署 .so 或启动采集/训练。

- 双端不一致 = 阻断，对照测试是门禁而非参考。
- 新增 obs 段 / 字段时，SHALL 同步更新 C 头、Python reader 与本 spec 段布局表三处。

#### Scenario: 改 C 头加字段

- **WHEN** 在 strategic_state.h 新增字段
- **THEN** 未跑 `_schema_check.py` 全过前，rel/.so 部署与 BC/PPO 采集均视为无效

### Requirement: reserved 段全零占位 + 版本门控

- `reserved` 134 维 [3330:3464] 部署时 SHALL 填 0；未来填充（多人玩家列表/战斗层细节/宝物/技能/外交）SHALL NOT 改变 OBS_DIM。
- `target_list` 64 维 SHALL 按 `_version` 门控：v1 填 0（引擎侧"最近目标"解析），v2 起由引擎填充、模型显式选 target；模型/DLL 端 SHALL NOT 跨版本混读。

#### Scenario: v1 期 target_list 全零

- **WHEN** 当前 `_version=3` 但 target_list 填充逻辑未启用（v1 语义）
- **THEN** 该段 64 维全 0，动作侧走"最近目标"解析，行为与填充前一致
