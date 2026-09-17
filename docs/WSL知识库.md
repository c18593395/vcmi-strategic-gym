# 知识库 — HoMM3 全盘操盘 AI（体系总索引）

> 本文件是项目文档体系的**总索引**（2026-08-31 重构）。知识库内容分三层，请按需取读，勿在单文件内堆砌。
> - **稳定参考**：结论性内容，就地修订，标注截至日期。
> - **问题登记册**：踩坑点，每条带状态字段（✅/⚠️/❌/🔄）。
> - **日期工作日志**：每轮会话一份，append-only，永不回编。
>
> **约定（AI 必读）**：收到“保存知识库”→ 追加到本文件末尾「待整理」区（不自动分发到子文档，由用户定期自行归档）；收到“保存踩坑点”→ 追加到 `WSL踩坑点.md` 末尾「待归档新增」区（不自动分发）；收到“记日志/今天进展”→ 写 `WSL日志/YYYY-MM-DD.md`（新日期新建一份）。模型读取本索引后应**自动取读下方子文档与日志目录**获取完整内容。
> **docs 行尾约定**: 知识库/踩坑点/当前任务清单 = CRLF, 总任务.md = LF+BOM (python 验证, 防 \r\r\n, 显式追加); 踩坑记录旧 LF

---

## 一、稳定参考

- [概述与决策](WSL知识库-概述与决策.md) — 项目目标、双轨架构、关键技术决策（Passability / 两段式 / Nullkiller2 / VMAP / 观测动作 / step 机制）
  - 章节：一 项目概述 / 二 双轨并行架构 / 三 关键技术决策（含 3.1 Passability / 3.2 两段式 / 3.3 放弃ARM64 / 3.4 选Nullkiller2 / 3.5 VMAP / 3.6 观测与动作 / 3.7 step通信 / 3.8 C7动作映射 / 3.9 战斗处理）
- [训练状态](WSL知识库-训练状态.md) — 当前训练参数、环境搭建与部署（截至 2026-08-29）
  - 章节：一 训练参数（当前训练C4 / 观测256维 / 动作空间11）/ 二 环境搭建（WSL2编译 / Connector / 启动训练）
- [参考速查](WSL知识库-参考速查.md) — 内存偏移表、StrategicState ABI、关键文件索引、数据流、WSL 双目录构建陷阱
  - 章节：一 内存偏移表 / 二 关键文件索引 / 三 StrategicState ABI / 四 数据流 / 五 WSL双目录陷阱

## 二、问题登记册（踩坑点）

- [WSL踩坑点.md](WSL踩坑点.md) — 总索引，下含 5 个主题子文档：环境-WSL与进程 / 构建-编译与部署 / 引擎-VCMI-API / 训练-奖励与策略 / 地图-vmap生成

### 踩坑大全速查（原“四、踩坑大全”已改为链接，不再复述）

| 主题 | 归属子文档 |
| --- | --- |
| 4.1 step2 挂死（SEND→WAIT 顺序） | 引擎-VCMI-API |
| 4.2 MMAI core dump（切 Nullkiller2） | 构建-编译与部署 |
| 4.3 ABI 不兼容（三件套重编） | 构建-编译与部署 |
| 4.4 .pyc 缓存（NTFS） | 环境-WSL与进程 |
| 4.5 subprocess 僵尸（os._exit） | 引擎-VCMI-API |
| 4.6 DummyVecEnv 短路 | 训练-奖励与策略 |
| 4.7 子 agent 401（provider→deepseek） | 环境-WSL与进程 |
| 4.8 vmap 跑战略训练（见 #84-90） | 地图-vmap生成 |

## 三、日期工作日志

- [2026-07-29.md](WSL日志/2026-07-29.md) — 十四、StrategicEnv 循环打通 (2026-07-29)
- [2026-07-31.md](WSL日志/2026-07-31.md) — C8.2 验证结论 — Nullkiller2 对手链路打通 (2026-07-31)
- [2026-08-15.md](WSL日志/2026-08-15.md) — H.6-H.7 动作空间落地（2026-08-15 完成）
- [2026-08-16.md](WSL日志/2026-08-16.md) — H.8 obs 归一化规范 (2026-08-16 数值爆炸根因修复)
- [2026-08-18.md](WSL日志/2026-08-18.md) — 有头验证结论 (2026-08-18)
- [2026-08-19.md](WSL日志/2026-08-19.md) — 十七、奖励塑形与训练配置 (2026-08-19 记忆迁移)
- [2026-08-23.md](WSL日志/2026-08-23.md) — Phase I.2 C++ BFS 全图寻路 (2026-08-23)
- [2026-08-26.md](WSL日志/2026-08-26.md) — 守卫战斗根因链 (2026-08-26 闭环)
- [2026-08-28.md](WSL日志/2026-08-28.md) — v5 训练运维 + Phase II 经济前置准备 (2026-08-28/29)
- [2026-08-29.md](WSL日志/2026-08-29.md) — 真实游戏战略层联调 (Task7, 2026-08-29, forktest66 全绿)

---

> 注：原单文件 2546 行已重构为「1 总索引 + 3 稳定子文档 + 5 踩坑子文档 + N 日期日志」。3 个稳定子文档现采用各文件独立连续编号（一~N）：概述与决策 一~三 / 训练状态 一~二 / 参考速查 一~五；旧全局编号（七/八/九/十一 跳号与复用）已消除。H1 泛滥、自引用过期等问题亦随拆分消除。

---

## 待整理（收到"保存知识库"时追加于此）

> 此区为新增知识暂存区。用户定期自行归档到上方「一、稳定参考」三个子文档后，再从本区移除。新增内容请尽量带"截至日期"与"结论"。

### 09-16 P10-target-2b duel 图 move_to_force 分区分段策略（已验证通过）

**结论**（截至 2026-09-16）：T06 图 `move_to_force` 需按 duel/非 duel 区分，统一 `move_to_force=250` 会导致 duel 图 act=2 循环惩罚 190 步累积 r≈-1665。

**核心规则**：

| 图类型 | move_to_force | 原因 |
|--------|--------------|------|
| T06 duel（蓝英雄为目标）| 60 | 蓝英雄 plen=129/201 < 250 理论可达；P10 SCORE 引导前 60 步内驱动 24 MOVE_TO；与 `act_loop_from_step=60` 同步，避免 190 步循环惩罚累积 |
| T06 非 duel 1v3（蓝城为目标）| 250 | 蓝城引导天然在守卫胜后（step 38-58+），需全程 MOVE_TO；`guard_done_steps=0` 禁用 GUARD_DONE 提前终局 |

**验证数据**（重启后 5 局 duel）：

| 图 | steps | r | 对比旧 250 步全覆盖 |
|----|-------|---|------|
| 72X72_02_duel | 74 | -183 | -1665→-183，改善 89% |
| 72X72_02_duel | 158 | -123 | 改善 93% |
| 108X108_02_duel | 139 | -137 | -1671→-137，改善 92% |
| 72X72_01_duel | 62 | -174 | 改善 89% |
| 72X72_02_duel | 111 | -165 | 改善 90% |

**#238 定性更新**：108_02_duel 蓝英雄 plen=201 < 250 已可达，"结构性不可达"定性作废；duel 图 r 极差问题彻底解除。

**踩坑点**：`move_to_force` 与 `act_loop_from_step` 耦合时，若 `move_to_force = max_turns`（全覆盖），act_loop 门控 `traj["steps"] >= act_loop_from_step` 会让循环惩罚在整个 250 步局中 190 步生效，反而加剧 r 恶化。正确做法是 duel 图 `move_to_force < max_turns`（60），让 P10 引导窗口（前 60 步）与 act_loop 惩罚起点同步。

### 09-16 P10 会话沉淀：h3m2vmap B1 独立工具工程 + vmap2h3m 反向转换器（截至 2026-09-16）

**结论**：
1. **B1 完成**：`tools/h3m2vmap/main.cpp`（--selftest 两段初始化跑通 + --check-h3m 引擎级读回）+ 独立迷你 CMake 工程（只读 RPATH 链 `rel/bin/libvcmi.so`，零 lib 重编、零 rel 写入，单编译单元秒级出二进制）。独立工具 main.cpp 必须先 `#include "Global.h"`（VCMI_LIB_NAMESPACE_* 宏所在），不能赌 serverapp 传递 include（踩坑 #240）。
2. **loadMap buffer 版两事实（V1 定论）**：`cb=nullptr` 可用；`modName` 必须传 `"map"`（`CMapHeader::mapRegisterLocalizedString` 特判），传 `""` 走 `getModLanguage("")`→ModsStorage 抛异常 SIGABRT（踩坑 #242）。
3. **vmap2h3m 反向工具**：`py/vmap2h3m.py`（~490 行，SOD 谱系 0x1c）：H3M donor 模板库按 (id,subid) 匹配原样复制 raw 条目绕开 H3M 原始编号考证（缺条目 patch subid 兜底）；5 类对象特征集（hero/town/mine/resource/monster，全草地）；映射数据源 = 引擎 config json 的 index 字段（`Mods/vcmi/Content/config/creatures|heroes/*.json`，带注释需剥离）。双图（T04_36X36_02 / T03_30X30_01）strict 读回 skipped=0 + 引擎 `--check-h3m` 三图（含官方 For Sale 514obj 对照）全部 `ENGINE LOAD OK`。
4. **版本事实**：fork 版本串实为 **VCMI 1.8.0**（此前文档按 1.7.4 记述，以二进制/源码为准）；C++20；Boost 1.83 系统包。
5. **验证方法论**：H3M 写回双层 = 字节级（h3m_tool strict 读回 skipped=0 + trace 逐对象 GAP 定位）→ 引擎级（真实 loadMap）；写回字节错位三连（AB+ main_town 2B / SOD hero artifact 19 槽 / resource msg=0 分支 1B）均经 strict 对账定位（踩坑 #241）。
6. **下一步 B2**：在 h3m2vmap 骨架上加 `loadMap(buffer 版) → MapFormatJson::saveMap` 直通转换，`Knee Deep in the Dead.h3m` 零改写往返，出口判据 = 引擎读回 + ep_runner 冒烟加载；V1 已实证，B2 首日即可直接跑 loadMap 路径。详见设计稿 §6/§8。

**指针**：`docs/P10-B-h3m2vmap转换器设计稿.md`（§6 B1 完成记录 / §8 旁路工具）/ `docs/当前任务清单.md` P10 段 / `scripts/h3m_tool.py`（H3M reader/patcher 逆向资产）/ `tools/h3m2vmap/` / `py/vmap2h3m.py`。

### 09-16 P10-B B2 完成：loadMap→saveMap 直通 + Knee Deep 往返 + ep_runner 冒烟（✅ 出口判据全过）

**B2 完成记录**（`Knee Deep in the Dead.h3m`，零改写直通）：
1. **直通转换**：`h3m2vmap --save "data/Maps/Knee Deep in the Dead.h3m" out.vmap` → `ROUNDTRIP OK`，36×36 / 413 对象 / 18326B。对象类型谱系全 H3M 型集：70 山 / 35 树 / … / 16 怪 / 16 矿 / 8 资源 / 2 英雄 / 2 城。
2. **header.players 事实**（重要，避免 B3 误改）：直通产物 `header.players` 为 dict——`red(canPlay=PlayerOrAI, hero core:christian)` / `blue(canPlay=AIOnly, hero core:sandro)`。缺 7/13 个"必须"字段属**正常**：工作图 King_of_Pain 同样只有 5 个键（缺 8），引擎 loadMap 实测不强制；缺字段挂死事故（#225）根因是 players 字段形态错误，不是字段数少。
3. **ep_runner 冒烟通过（出口判据②）**：`ep_runner_one.py 6 /tmp/b2_knee_traj.json B2_adventure_knee_deep.vmap`，6 步冒烟跑满（exit=124 = timeout 300s 正常窗口）。引擎读回：`visitLobbySetMap` 成功 → `Grouped 2 heroes into p0:1 p1:1` → terrain_grid 1250 非零 OK → 战斗发生并结算（`CGCreature::battleFinished winner=0`，RED 胜）→ 英雄移动（`CHeroMovementQuery` pop 正常）。traj steps=2 时 r=-2.9（随机策略 6 步样本，仅证"引擎可玩"，不是 PPO 判据）。
4. **踩坑固化**：`strategic_env.py` L522 断言图名必须含 `s1/mini/adventure/h3m` 之一 → 直通产物命名须带 `adventure` 关键词（本次 `B2_KneeDeep.vmap` → `B2_adventure_knee_deep.vmap`，两处副本同步改名）。
5. **已知噪声（非阻断）**：smoke 日志有 `Music file "music/CstleTown" was not found` 一类报错。核查结论：`train_loop.log` 主日志与 #218 批量转换（159 张 H3M）均无此记录，判定为 rel/bin 缺 music 资源文件的**已知良性噪声**（不影响引擎功能，不处理）；入池部署时如主日志再现再复查。
6. **部署落点**：`vcmi-native/rel/bin/data/Maps/` + `maps/training/` 双份 `B2_adventure_knee_deep.vmap`（改图后跑 `sync_maps_to_runtime.py --strict` 的纪律本次在拷贝时已对齐，未走 vmap 改图路径）。

**指针**：`py/run_b2_smoke.sh`（冒烟脚本）/ `py/check_b2_knedeep.py`（vmap 内部结构检查）/ `py/rename_b2_knee.py`（改名脚本）/ `tools/h3m2vmap/main.cpp`（--save B2 逻辑）/ 设计稿 §7 B2 节。

**B2 后续（09-16 同窗收口）**：冒烟 exit=124 = timeout 300s 跑满 6 步窗口属正常（非异常退出）；`Music file "music/CstleTown" not found` 等 music 缺失报错经核查 `train_loop.log` 与 #218 批量转换链均无记录，定性为 **rel/bin 缺 music 资源的已知良性噪声**（不影响引擎功能，不阻断入池，如部署后主日志再现再复查）。traj steps=2 r=-2.9 = 随机策略 6 步样本，仅证"引擎可玩"，非 PPO 判据。

### 09-16 P10-B B4 完成：R2 玩家重配 + Knee Deep 全流程正式产出（✅ P10-B 全部收官）

**R2 实现**（`tools/h3m2vmap/main.cpp`，`--no-r2` 关闭）：8 槽位重配 — `map.players[i]`（public vector，PLAYER_LIMIT_I=8）直接写 `canHumanPlay=(i==0)` / `canComputerPlay=(i==1)`（red=human only / blue=ai only，其余 6 家双 false）+ hero 游离 owner 兜底（非 red/blue 的英雄挪 red，Knee Deep 下 0 例）。

**序列化闭环关键发现**（免写 teams 段，R2 只需 2 行核心赋值）：
- 保存侧 `serializePlayerInfo`：`canAnyonePlay()==false` 的槽位**整个不写出**（header.json 里只出现 red/blue 两家）；
- `canPlay` 枚举由 canHumanPlay/canComputerPlay 推导（PlayerOnly/AIOnly/PlayerOrAI）；
- 读取侧 `readTeams`：无 teams 段 → 按可玩玩家自动各分一队（howManyTeams=2）；保存侧 `writeTeams` 剔除单成员队 → 1v1 各自单队时 teams 段为空 → 下次读取又自动恢复。**完全闭环，R2 无需碰 team/howManyTeams**；
- heroes 段从实际对象遍历写出（`hero->getOwner()==PlayerColor(player)`）→ hero tempOwner 决定归属，无需动 PlayerInfo.heroesNames。

**Knee Deep 天然 1v1 对置**（`py/b4_recon_players.py` 调研）：hero_45=red(christian/castle)、hero_202=blue(sandro/necropolis)、town_342=red(castle 区)、town_70=blue(necropolis 区)；red allowedFactions={castle} / blue={necropolis} 与英雄类型匹配 → R2 零对象改动。

**对账 + 正式产出**（`py/run_b4_verify.sh`）：
| case | header.json 校验 | 结果 |
|------|------------------|------|
| no_r2 | red canPlay=PlayerOrAI（原状保留） | ✅ ROUNDTRIP OK |
| default 全规则 | red=**PlayerOnly** / blue=**AIOnly** / R2_players_configured=2 / R2_heroes_reassigned=0 | ✅ ROUNDTRIP OK |
| 正式产出 | `B4_adventure_knee_deep.vmap` 15630B（#246 命名） | ✅ ROUNDTRIP OK / RC=0 |

**ep_runner 冒烟**（`py/run_b4_smoke.sh`，部署 rel/bin/data/Maps + `ep_runner_one.py 6`）：**exit=0 / steps=6 / total_rew=+11.55**（B3 版 -7.2 → B4 版 +11.55，R2 后经济动作正奖励生效：`[ECON] first BUILD_2 step 2 +15` / `first RECRUIT tier=1 step 4 +12`）；`Grouped 2 heroes into p0:1 p1:1` 双方英雄分组正常；terrain_grid 旁路 1212 非零每步 OK；done 全 False（6 步未终局正常）。

**复犯提醒**：run_b4_verify.sh 首跑 RC=134（SIGABRT）= 忘 `cd /home/administrator/vcmi-native`（#248 cwd 依赖），已加 cd 修复——**任何新转换/验证脚本模板必须首行 cd**。

**指针**：`py/run_b4_build.sh`（同步+构建）/ `py/run_b4_verify.sh`（对账+产出）/ `py/run_b4_smoke.sh`（冒烟）/ `py/b4_recon_players.py`（header/objects 玩家调研，支持传参）/ `tools/h3m2vmap/main.cpp` R2 段 / 设计稿 §5 R2。**P10-B B1-B4 全部完成**，下一步 C/D/E：B4 产出入训练池。

### 09-16 P10-B B3 完成：R1-R7 改写层 + report.json 审计 + 9 case 开关对账 + ep_runner 冒烟（✅ 出口判据全过）

**B3 完成记录**（`tools/h3m2vmap/main.cpp` B3 改写层，独立 CMake 工程零 rel 写入）：

1. **R1 城镇归零**：2 城 owner→NEUTRAL（直写 public `tempOwner`，`CGTownInstance::setOwner` 是 private）+ 清建筑 23（`getBuildings()` 计数 + `removeAllBuildings()`）+ 清守军 5 stack（`CArmedInstance::clearSlots()`）；hero 部队同清。
2. **R3 守卫改写**：26 stack 遍历（16 monster + 10 randomMonsterLevel*），`--r3_scale X` 缩放（min 1，`stack->setCount`）+ `neverFlees=true` + `initialCharacter=SAVAGE`（scale=1.0 也做狂暴化，数量不变）。
3. **R4 白名单过滤**：39 类短名保守集（ML 目标 18 类 + 静态装饰 21 类）— `randomMonsterLevel*`/`randomResource`/`randomArtifact*` 运行时定型为 MONSTER/RESOURCE/ARTIFACT 后 ML 可识别故保留；山/树/岩等 21 类装饰决定 `tile.blocked()` 障碍通道必须保留。实测 Knee Deep：**保留 366 / 移除 47**（31 类杂项：shrine/witchHut/magicWell/scholar/borderGuard/sign/event 等）。
4. **R6 胜负重置**：原 4 个 triggeredEvents 清空 → standardWin(`EventCondition(STANDARD_WIN)`+VICTORY) + standardLose(`DAYS_WITHOUT_TOWN,0`+DEFEAT)。
5. **R7 文本改写**：`map.name/description = MetaString::createFromRawString(--map-name ID)`。
6. **R5 地形全草**：默认关（#94），`--terrain-flatten` 时计数 1296 cells（36×36×1 层）。
7. **report.json 审计**：写 vmap 同目录，R1-R7 计数全量输出。

**关键修复（踩坑 #247）**：R4 删对象初版用 `eraseObject`（置 null 保序）→ `CMapSaverJson::writeObjects` 用 `getObject(ObjectInstanceID(i))` 直接索引原始 vector（紧凑假设）→ 36 个尾部对象漏写 + null 槽写空壳，`ROUNDTRIP MISMATCH in=366 out=330`。改 `removeObject`（CMap.cpp:593，vector erase + id 重排 + towns/heroesOnMap/tile 引用全修正）+ **按 ID 降序删**（每次删除只重排 ≥ 该 id 的对象，待删集合中更大 id 已删完）→ ROUNDTRIP OK 366→366。

**9 case 开关对账（`py/run_b3_matrix.sh`，全 ROUNDTRIP OK）**：
| case | 对账点 | 结果 |
|------|--------|------|
| no_rules | OUT=413 + report 不写 | ✅ |
| no_r1 | R1_* 键缺失 | ✅ |
| no_r4 | OUT=413 + R4_* 缺失 | ✅ |
| no_r6 / no_r7 | 对应键缺失 | ✅ |
| r3_050 / r3_100 | R3_scale_pct=50/100 | ✅ |
| flatten | R5_flattened_cells=1296 | ✅ |
| default | 全开基线 R4 366/47 | ✅ |

**全规则组合产出**（`py/run_b3_full.sh`，r3_scale=1.5）：RULED objects=366 / 15637B / ROUNDTRIP OK / RC=0。

**ep_runner 冒烟**：`B3_adventure_knee_deep.vmap`（全规则 1.0 产物）部署 `rel/bin/data/Maps/`，`ep_runner_one.py 6` → **exit=0**（6 步跑完自然退出，无需 timeout 兜底），traj steps=6 / r=-7.2 / done 全 False；terrain_grid 旁路 1212 非零 OK；引擎加载无 error/exception。R1-R7 改写后地图在训练链路完整可玩。

**指针**：`py/run_b3_full.sh`（全规则）/ `py/run_b3_matrix.sh`（9 case 对账）/ `py/run_b3_smoke.sh`（冒烟）/ `py/inspect_b2_types.py`（70 类短名调研）/ `tools/h3m2vmap/main.cpp`（B3 改写层）/ 踩坑 #247/#248 / 设计稿 §5/§7 B3 节。**B4 待做**：Knee Deep 全流程正式产出（R2 玩家重配 red=human/blue=ai 尚未实现，属 B4 范畴）→ 交 C/D/E 步入池。

### 09-16 日志分析：D3 熵验证 + P10 duel 图持续负 r + 108_02 临界不可达实证

**训练进程**：09-16 重启段（system unit homm3-train-v5 active，PID 变更后 resume step 698978→717662+），ep 编号已重置从 1 起，至 ep=29（time=11754s），BATCH 周期 ~55min 维持。零崩溃（`[EP_TIME]` 全历史 1319 条无一条 `err=yes`；零 SIGSEGV/SIGABRT/rc=139/rc=134）。

**D3 熵 bonus 持续验证**：`entc` 行全历史 10 条（step 703791/704944/706097/707250/708403/709556/710709/711862/713015/714168），公式 `entc = 0.05 × (1+exp(-step/2M))` 逐步吻合（step 703791→0.0853 / 714168→0.0850）。`ent`（平均熵）从 1.560 → 1.492 持续下降 = warmup 衰减生效。KL 0.50→0.788（klc=3.417）= 探索策略偏离旧 policy 较大，属 D3 初期扰动正常。

**P10 target_scorer 灰度对 duel 图收益有限（关键发现）**：
- `[SCORE]` 行分布稳定：`blue_hero` score=146-183（V=100 × F=-0.32 衰减生效，#232 已上线）；`plen` 跨度 1-129（72X72_02 蓝英雄 plen=129，108_02 蓝英雄 plen=201）；`runner_up` 接近头名（差 2-8）= 候选池竞争良好，无 hard_filter 全过滤。
- **但 108_02_duel 持续 r=-1283**（ep=28 最新，200 步截断）。蓝英雄 (102,102) BFS 距离 201 步 → P10 V×0.2 衰减把 score 压到 110.9，但模型仍持续招兵（+10/+40/+120）+ 经济（16-21）+ 大量 END_TURN（2），200 步走完仍未到达 capture 点。`plen=201 > 200 步预算` = **结构性不可达**，与 WIN-3 评估"108_02_duel 临界不可达 100%"结论一致。
- **结论**：P10 经济期远目标衰减（#232）对 duel 图无效——蓝英雄太远时，模型只会"经济+东进"确定性空转，不会真正发起 capture。下一步建议：按 WIN-3 ① 把 72X72_02_duel 切单图轴观察，或将 108_02_duel 暂移出 MAPS。

**108_02_duel 临界不可达实证（与 WIN-3 评估呼应）**：
- WIN-3 评估（`py/win3_eval_difficulty_axis.py`）结论：108_02_duel 红 hero→蓝镇 曼哈顿 200 步 = 100% 截断率（200 步走满才到蓝镇门口）。
- 09-16 实测验证：`[SCORE] pick=(102,102) type=blue_hero plen=201` = 实际蓝英雄在 (102,102)，BFS 距离 201 步 > 200 步预算。`F=-0.32` 衰减已生效（V=100→score 110.9），但模型行为仍为经济+空转。
- **处理**：108_02_duel 需二选一：① 提 250 步（全局影响所有图）；② 挪蓝镇到 (98,98) 距离降至 174（69%）。当前不动，WIN-1 达标后走 WIN-3 ① 72X72_02_duel 单图轴。

**ZOMBIE 设计性现象确认**：全日志 441 次 `[ZOMBIE] hero dead (all-blocked x2)`，全部发生在 duel 图（蓝方英雄 8 向全堵卡死）= C2 红警白名单不计入，非崩溃。ep=21 时 `time=8626s`，ep=28 时 `time=11292s`，单 BATCH 时长 ~2.5h 正常。

**avg_r 段趋势（09-16 重启后）**：
| 段 | 均值 | 说明 |
|----|------|------|
| ep1-10 | -1.2 | 正常波动 |
| ep11-15 | -0.9 | 略升 |
| ep16-21 | -6.4 | duel 图 r=-1261/-1280 拉低 |
| ep22-29 | -6.4 → 0.5 | ep=28 时 -6.4（108_02 duel 负 r 主导）；ep=29 回升到 +0.5（72X72_02 非 duel r=52.1） |

**WIN-1 五判据对照（09-16 最新，ep=29 采样）**：
- ① TOWN_CAPTURE 非零：✅ 全历史 215 条；本窗 duel 图 blue_hero_killed 持续出现（capture proxy 真实击杀）
- ② GUARD ≥80%：✅ 2482 次维持
- ③ avg_r 跌幅 <20%（基线 2.34）：⚠️ 本段 duel 拉低至 -6.4（ep=29 回升 +0.5）
- ④ 自发经济 ≥80%：✅ RECRUITED 48454 次；本段 +10/+40/+120 频繁
- ⑤ 200 步局 ≤20%：⚠️ 本段 duel 图 200 步截断率 ≥30%（ep16/ep20/ep28 全 duel）

**关联**：`py/win1_five_criteria_snapshot.sh` / `py/analyze_trunc200.py` / `py/win3_eval_difficulty_axis.py` / `py/target_scorer.py`（P10 灰度）/ 踩坑 #232（P10 V×0.2 衰减）/ 踩坑 #236（D3 entc 行延迟口径）/ 知识库「WIN-3 难度轴纯评估」章。

### 250 步方案部署 (09-16, WIN-3 ②, STEPS_PER_EP 200→250)

**动机**：#238 实证 108_02_duel 蓝英雄 plen=201 > 200 步预算 = 结构性不可达。WIN-3 ② 二选一中选「提 250 步」方案（全局影响所有图，T05 小图节奏变慢 ~25% 需后续观察），另一选项「挪城到 (98,98)」暂缓。

**改动清单**：
- `train_wsl2_ppo_v2.py` L9：`STEPS_PER_EP = 250`（原 200）
- `ep_runner_one.py` T06 覆盖块：`move_to_force = 250`（原 200）+ `guard_done_steps = 0`（保留）
- `ep_runner_one.py` 三处注释口径 200→250 对齐（L1229 / L1270 / T06 覆盖块注释）
- 清 `__pycache__`（`find /mnt/d/Bigdata/hero3_fresh -name '*.pyc' -delete`）
- `wsl -u root systemctl stop/start homm3-train-v5`（PID 25924，checkpoint resume）

**验证**：新 banner 行 96902 `WSL2 PPO v2 — 1000eps×250steps batch=2048 maps=10 device=cuda`（maps=10 说明本次 checkpoint 重启后图池为 10 图）。

**关联**：踩坑 #238（108_02_duel 结构性不可达）/ WIN-3 ②（250 步方案）/ 当前任务清单 WIN-3 ② 部署标记。

### C1 B4 晋级判据实质达成 (09-16, 人工拍板, ckpt=711583)

**评估结果**：3 次 `--profile all`（ckpt=711583）avg_r = 153.2 / 133.1 / 144.6，全 ≥+15（B4 线③达标）。四项单指标全过：GUARD 首胜率 88%（≥30% 达标）/ 正局率 100%（≥70% 达标）/ avg_r 144.6（≥+15）/ 大负率 0%（≤0% 达标）。3 窗趋势稳定（均值 143.6，波动 ±10）。

**PROMO_HINT 未自动触发**：n_valid=8 < 10 护栏（`eval_history.jsonl` 同 ckpt 有效样本不足 10），故走人工拍板确认晋级条件实质满足。

**课程定位澄清**：B4 属 T7.1 历史判据（Level 3 晋级 08-29 已执行），本次是「工具链路 + 当前 ckpt 复核闭环」，**不触发** T7.5 S2 / WIN-2 / WIN-3（这些的前置 = WIN-1 五判据聚合，其中判据① TOWN_CAPTURE 非零需本次窗 40 局重新攒窗严格聚合）。

**评估明细**（`py/eval_history.jsonl`，ckpt=711583，profile=all）：
| 窗 | ts | n_valid | avg_r | GUARD | 正局率 | 大负 | 无效 |
|----|----|---------|-------|-------|--------|------|------|
| 1 | 09-16 00:21 | 6 | 153.15 | 83.3% | 100% | 0% | 4 |
| 2 | 09-16 01:13 | 8 | 133.07 | 87.5% | 100% | 0% | 2 |
| 3 | 09-16 01:55 | 8 | 144.57 | 87.5% | 100% | 0% | 2 |

**关联**：`py/eval_promo.py`（B4 五指标 + 双条件 PROMO_HINT）/ `py/eval_history.jsonl`（3 条 ckpt=711583 记录）/ 当前任务清单 C1 区 / 踩坑 #236（D3 L534 延迟口径）。

### WIN-3 难度轴纯评估 + T7.5 节奏重估 (09-15, 不改图不重启)

**WIN-3 评估结论**（`py/win3_eval_difficulty_axis.py` 读取 vmap objects.json 曼哈顿距离，零部署）：

| 候选 | 红 hero→蓝镇 | /200 步 | 结论 |
|------|-------------|---------|------|
| 72X72_02_duel | 128 | 64% | ✅ 即插即用（已在 MAPS），WIN-1 达标后直接用 |
| 108X108_02_duel | 200 | 100% | ⚠ 临界不可达，需二选一：提 250 步（全局）或挪蓝镇(98,98)→距离 174/69%（单图） |

**T7.5 节奏重估结论**（纯文档拍板，零部署）：
- S2 触发前置 = WIN-1 达标 + capture proxy 稳定 ≥2 窗（不混变量）。
- 顺序：WIN-1 → S2（1-2 窗）→ S3 → T05 换图 → S4。
- S2/S3 = 激励轴，与 WIN-3 难度轴错窗。
- S2 改 `train_wsl2_ppo_v2.py` 奖励系数，可与 D3/C2 L0 合并自然重启批次。

**vmap 结构备忘（09-15 实证）**：`.vmap` 是 ZIP 含 `header.json` + `surface_terrain.json` + `objects.json`；objects 是 dict `{key: {l, x, y, type, options:{owner,...}}}`，不是 list；hero/town 用 key 前缀 `hero_N`/`town_N` 识别，owner 在 `options.owner`。

### S2 回退决策 + WIN-1 判据①根因深挖 + 定义修正 (09-15, 踩坑 #235)

**决策背景**：原计划 D3 熵 bonus + C2 L0 崩溃插桩 + T7.5 S2 三项合批（同一 train_wsl2_ppo_v2.py + ep_runner_one.py 停启批次）。数据核查发现 S2 触发前置（WIN-1 判据① BHERO_KILL 非零）当前不满足，用户拍板"D3+C2 L0 先部署，S2 延后"。

**WIN-1 五判据快照（09-15 05:18 首版，`py/win1_five_criteria_snapshot.sh`，样本 40 局，本次窗 04:57:32 起仅 4 step）**：

| 判据 | 阈值 | 实测 | 状态 |
|------|------|------|------|
| ① TOWN_CAPTURE 非零（**修正后**） | >0 | 主日志 215 / 旁路 218 | ✅（定义修正后） |
| ② GUARD 接战 ≥80% | ≥80% | 2482 次维持 | ✅ |
| ③ avg_r 跌幅 <20%（基线 2.34） | 跌 <20% | 1.56（跌 33%）⚠ 含本次重启 + P10 灰度初期波动 | ⚠ |
| ④ 自发经济 ≥80% 局 | ≥80% | RECRUITED=48454 | ✅ |
| ⑤ 200 步截断率 ≤20% | ≤20% | 10.0%（4/40） | ✅ |

**判据① 定义修正（09-15 根因深挖）**：原"判据① BHERO_KILL 非零"是**错误定义**，改为"TOWN_CAPTURE 非零"。7 条证据链：
- (a) 代码在位：`ep_runner_one.py` L1045-1053 BHERO_KILL 埋点（`if _bnow:` 分支）
- (b) 旁路写成功：`battle_quality_events.log` 有 9 条 BHERO_KILL 记录
- (c) 9/9 全空拍：全部 `live_slots=0`（#146 空拍误报遗留）
- (d) 空拍防护生效：#146 防护上线后 BHERO_KILL 计数恒 0
- (e) 空拍仍高频：HEROSEG_EMPTY 旁路 427 次（空拍未消失，但被 BHERO_KILL 分支守卫拦下）
- (f) duel 结构性：蓝英雄死 = game_over = ep 终止，不进 BHERO_KILL 分支
- (g) 非 duel 真无行为：蓝英雄从未真被歼灭（非空拍差集恒为空）

**关键发现：主日志白名单漏网**。`train_wsl2_ppo_v2.py` L225-235 白名单仅转储含关键词的 ep_runner stdout 进 `train_loop.log`；`"[TOWN"` 是前缀通配（覆盖 `[TOWN_CAPTURE`/`[TOWN_VISIT`/`[TOWN_BLOCKED`/`[TOWNSTALL`），TOWN_CAPTURE 完整标签进主日志 215 条，而 BHERO_KILL / HEROSEG_EMPTY 不在白名单 → 主日志 grep 恒 0。**判据① 原定义"主日志 grep BHERO_KILL"从埋点架构层就不可能命中**。

**三义性判定**：BHERO_KILL 全历史 0 次属 ② 观测无效 与 ③ 真无行为 的混合——埋点工作正常，但蓝英雄真实歼灭从未发生。**这不是 S2 前置的断链，是判据定义本身错了**，capture 机制（TOWN_CAPTURE 218 条）实际一直在正常运行。

**结论（修正后）**：判据① 修正为 TOWN_CAPTURE 后已实质满足（主日志 215 条）。严格 5 判据仍需本次窗 40 局重新聚合（04:57:32 起仅 4 step），但前置断链已解除。D3/C2 L0 无前置依赖，可独立部署；S2 待本次窗 40 局严格聚合达标后启动。

### T06 Duel Reward 结构分析与修复 (09-15, 踩坑 #237)

**T06 duel 负 reward 根因（多机制耦合，定量分解）**：

| 项 | 改前（T06 duel 200 步局） | 改后（#237 修复后） |
|---|---|---|
| 位置不动 -0.5（赋值覆盖） | `r = -0.5` 每帧重置，同帧正 reward 全丢 | `r += -0.5` 累加，保留同帧奖励 |
| 横跳 8 步窗 -3.0 | `step ≥ move_to_force=200` 永假，全程不触发 | `step ≥ act_loop_from_step=60` 触发 |
| act_loop 惩罚 -1.0 | 同上，全程不触发 | 同上，step≥60 触发 |
| act=2 方向卡死 ~130 次 | 无循环惩罚 → 模型持续学错 | 循环惩罚有效 → 概率压低 |

**SCORE 远目标不可达问题（P1 待处理）**：
- 蓝英雄 plen=129~201，BFS 距离超 200 步预算 → 走不完
- `F=-0.32`（power_feasibility 负值）被 `V=100 + delta_cap×150` 主导，蓝英雄仍被选中
- 改 `py/target_scorer.py` 增加 budget-aware 降权：`plen > 剩余步数×0.8` 时 score 打 50% 折扣

**TOWN_VISIT 取兵窗冷却（P1 待处理）**：
- 英雄反复折返己方城（(2,2) 附近）取兵，每次 ~40 步
- `own_town_guide_count >= 2` 只限目标选取，不限制 TOWN_VISIT 取兵窗本身
- 改 `ep_runner_one.py` L557 增加 `town_visit_count` 限制（第 3 次后不再开取兵窗）

**S2 回退操作**：`ep_runner_one.py` 5 处 SearchReplace（RECRUIT +0.25→+0.5 / BUILD_2 +0.375→+0.75 / 兵力系数 0.03→0.02），数值与 HEAD 完全一致；保留 3 处注释改动（L1151 陈旧 `× 0.01`→`× 0.02` 修正 + L1185-1186/L1204 两处 S2 回退说明）。

**教训**：合批部署前必须核查触发前置；**并核查判据本身是否可命中**。S2 前置定义"主日志 BHERO_KILL 非零"是双重陷阱：(i) 埋点未进主日志白名单；(ii) 蓝英雄真被歼灭从未发生。若按原判据部署 S2，会污染窗口统计；若按"0 命中三义性"（#204）分类，应回到根因层面验证埋点+观测是否有效，而不是把 0 当"真无行为"接受。

**关联**：`py/win1_five_criteria_snapshot.sh`（已修正）/ `py/bhero_kill_rootcause_probe.sh`（新增，根因探针）/ `py/win1_window_split.sh`（区分本次窗 vs 历史累积）/ `ep_runner_one.py` L1045-1053（BHERO_KILL 埋点）/ `train_wsl2_ppo_v2.py` L225-235（主日志白名单）/ #146（空拍防护）/ #204（0 命中三义性）/ #231（capture proxy 双拍确认）/ #235（合批前置核查）。

### capture proxy 空拍误报修复 + T06_02 地形实证方法 (09-15, 踩坑 #231)

**事实 1：T06 _02 课程图是全草地，无静态墙（截至 09-15 解包实证）**。`maps/training/T06_adventure_72X72_02.vmap`（zip 三件套）surface_terrain = `gr24_` ×5184（72×72），无 wt/ro/rd；布局 = red hero(5,5)+town(2,2)，blue 三英雄 (66,66)/(66,5)/(5,66) + 三镇 (69,69)/(69,2)/(2,69)，5 金矿（18,18)/(54,54)/(18,54)/(54,18)/(36,36)，108_02 同构放大（蓝镇 105 系）。**以后凡"T06 走不过去/堵点"类结论，先解包 vmap 用 BFS 实证，不得只凭日志 TOWNSTALL 的 `block=(x,y)` 判断**——该 block 是引导层把"BFS 建议但引擎拒绝的首步格"拉黑的**动态障碍**诊断（多为敌方英雄/瞬态），不是地形。

**事实 2：heroes obs 空拍（截至 09-15）**。obs [128+hi*26]×8 英雄槽偶发整拍全 id=0（`[HEROSEG_EMPTY]`，全历史 412 次；形态只有"全 0 = 共享内存未填充帧"，无全 -1），多发于战斗/visit 瞬态。空拍 = 观测无效：蓝英雄集合 `_bnow` 为空集，**不能进任何差集判定**。

**事实 3：capture proxy 现行机制（09-15 修复后，ep_runner_one.py L952-979）**。蓝英雄 id 差集 → 先挂账 `_kill_pending`；**空拍帧整体跳过**（条件含 `_bnow`）；下一非空拍仍缺席才 +100/局一次（日志 `(C: hero-kill proxy, confirmed 2 frames)`）；id 回来撤账、部分仍缺滚动再挂一拍；duel 图后缀排除保持（#209）。验证真伪 proxy 一律查 `battle_quality_events.log`：真 capture 前不应有同图同步 HEROSEG_EMPTY；218/218 全配空拍 = 修复前全假。

**方法：日志局轨迹重建**。`ep_steps= r= act=[...]` 行的动作码 0-7 = 方向（dx/dy：0=(0,-1) 1=(1,-1) 2=(1,0) 3=(1,1) 4=(0,1) 5=(-1,1) 6=(-1,0) 7=(-1,-1)），16-21=经济。累计位移可还原 agent 意图轨迹（无引擎拒绝时即真实轨迹）；确定性卡死局指纹 = 多局 act 序列逐位相同。事件配对用严格键 map+step（capture 行是 `at step N`，HEROSEG_EMPTY 是 `step=N`，正则勿混）。

### T06 duel 地图生成 + check 工具 + 入池流程 (09-12)

**工具**: `py/gen_t06_duel.py`（生成 72X72_02/108X108_01/108X108_02 duel）+ `py/check_t06_maps.py`（7 维可用性检查）。

**gen_t06_duel.py 缺陷（踩坑 #212, 09-13 已证伪）**: ①缺 `terrain_0.json` 是误报——引擎 `MapFormatJson.cpp` L248-255 `getTerrainFilename(0)` 返回 `surface_terrain.json`, 不存在 terrain_0.json 这个文件名, 引擎从未读它; ②"蓝方贴镇 6 格 vs 红方 3 格不对称"描述有误——实际双方均 dist=6 完全对称, `check_t06_maps.py` L134 阈值 5 偏严触发 WARN。地图可直接入池训练, 无需补 terrain_0.json 或调坐标。

**check_t06_maps.py 7 维**: ① 文件落地三处（Maps/training/ + v13/maps/ + vcmi-native/rel/bin/data/Maps/） ② zip 完整性 + 3 文件（header/surface_terrain/objects） ③ hero/town 数 = 2 ④ identifier 白名单 ⑤ 尺寸对齐（header 与 terrain 长度一致） ⑥ 对角 duel 坐标（red 左上 / blue 对角） ⑦ 对象类型统计（44 objects: hero 2 / town 2 / mine 5 / resource 15 / monster 20）。

**入池流程**: ① `gen_t06_duel.py` 生成 → ② `check_t06_maps.py` 验证（全绿 = 结构正确，但需另验 terrain_0.json） → ③ cp 进 `v13/maps/`（训练主进程实际加载路径） → ④ cp 进 `vcmi-native/rel/bin/data/Maps/`（运行时副本） → ⑤ 改 `train_wsl2_ppo_v2.py` MAPS 列表 1 行 → ⑥ 停训 + 错窗重启。

**T7.4 HERO_DEATH 判据 1 样本池切 T06 duel 根因（踩坑 #210）**: C 方案 proxy（`blue_hero_killed`）与 zombie 全堵（`passable.any()=False`）**完全正交**。T05 守卫战 autofight 必胜 → red 几乎不战死 → 无全堵机会；T06 duel 蓝英雄一死 → game_over 当步 end → 同样无机会。VCMI 引擎 standardDefeat 未落地前 `game_over==2` 判负不生效。判据 1 样本池需切 T06 duel（blue 英雄存活 → red 进攻 → 有反杀全堵机会）。

### L877 TOWNSTALL 修复实施 + 重启验证 (09-12, 踩坑 #209 闭环)

**修复**: `ep_runner_one.py` L877 `cur_dist >= move_stall_prev` → `cur_dist > move_stall_prev`（TOWNSTALL 平台段误判根因: `>=` 把 BFS plen 持平的横移/绕岩段也计停滞）。

**重启验证**: 停 `homm3-train-v5` → 重启 resume step=659248 → 重启窗口（L76382→L78132, 66 局）TOWN_BLOCKED=0（修复前全 log 460）+ TOWNSTALL=41 全为 `move_stall==1` 瞬态诊断（pas 全 1 未升级）→ **修复生效**。

### P8-D 双机实机验证 WSL 双实例 9/9 PASS (09-14)

**背景**: T13.10 唯一剩余实机项。09-12 设计骨架 + 本机 13/13 已过，双机路径（HSK 预交换 + 跨节点 TCP + HMAC 认证握手 + 远端状态文件）缺实机验证。按既定口径**不用第二台真实机器**，WSL 内双独立节点模拟双机拓扑（node1=server 端点，node2=client 部署目标，跨 WSL 网络命名空间 `172.23.41.125` 非 localhost），双机路径另以单机双实例（`py/p8d_two_instance.py` 13/13 PASS）实跑完成。

**探针**: `py/p8d_dual_node_sim.py`——WSL 双节点模拟，6 项检查：① HSK 生成+预交换（node1→node2 `shutil.copyfile`，模拟人工 U盘/SCP 交换）+ 0o600 + VCMI 部署目录就绪；② 跨节点 TCP 可达（node1 监听 40311，node2 连接）；③ 正例 HMAC 认证握手（node2 `RemoteVCMITCPConnection(auth_enabled=True)` 发 `AuthToken` 帧，node1 `TokenVerifier` 验签回 0x01）；④ 负例错误 HSK 拒绝（新 HSK → 签名 mismatch → 0x00 → `AuthFailedError`）；⑤ 双节点状态文件（`StatusFileWriter` 写/读 OK）；⑥ HSK 权限 0o600。

**结果**: 9/9 PASS rc=0。ACK 日志正例 `ok→1`、负例 `signature mismatch→0`，HMAC 验签闭环真实生效。

**修复 1 处**: `remote_connection._auth_handshake` 认证失败路径调 `self.close()`（类中无此方法，AttributeError）→ 改 `self.disconnect()`。

**与 09-12 本机 13/13 的差异**: 本机 probe（`p8d_deploy_probe.py --local`）用真实 `VCMI_server.exe` 起服务（auth_enabled=False，仅 TCP+游戏帧透传）；双机 probe 用 `AuthProxy`（Python socket + `TokenVerifier`）模拟认证端点，因为真实 `VCMI_server` 不识别 `AuthToken` 帧（T13.10 已知边界），HMAC 正负例在此 probe 首次全链实机通过。

### P8-D 单机双实例部署验证 13/13 PASS (09-14)

**背景**: 按既定口径**不用第二台真实机器**，统一用「单机双实例」完成双机部署路径实机验证——同一台 Windows 起 2 套独立 VCMI 实例（2 真实 `VCMI_server.exe` 端口隔离 3030/3031 + 2 真实 `VCMI_client.exe` 跨实例 + HSK 跨实例预交换，共享 `D:\vcmi-fork-build\bin` 无需副本），比 WSL 双节点 sim 更贴近真实部署拓扑。回答"能同一台机器同时运行 2 个实例吗？不用 2 台电脑"——**能**，Windows 多进程可共载同一 dll，端口隔离即可并存。

**探针**: `py/p8d_two_instance.py`——同机 2 实例探针，13 项检查：
- 实例 A（node1/host）：真实 `VCMI_server.exe --port=3030` 存活 + TCP 探活
- 实例 B（node2/guest）：真实 `VCMI_server.exe --port=3031` 存活 + TCP 探活（同机 2 server 并存端口隔离）
- HSK 预交换：生成 32B → node1 侧落盘 → `shutil.copyfile` 跨实例交换到 node2 侧（模拟 U 盘/SCP）
- 真实 ModelAI client 连 3030（host 侧）与 3031（guest 侧，跨实例），`VCMI_TESTMAP_ONLYAI=1`
- 协议层认证：`AuthProxy(3031)` 收 `AuthToken` 验签 → `0x01` ACK（正例）
- 负例：错误 HSK → `signature mismatch` → `0x00` → `AuthFailedError`
- `StatusFileWriter` 双节点（node1@3030, node2@3031）状态文件

**结果**: 13/13 PASS rc=0。`ACK 日志: ['ok→1', 'signature mismatch→0']`。同机 2 真实 VCMI_server 并存（端口隔离）+ 2 真实 ModelAI client 跨实例连入 + HSK 跨实例预交换 + HMAC 正负例闭环 + 双节点状态文件全通过。

**修复 1 处（检查顺序 bug）**: 首跑 12/14——"同机 2 server 并存"判定放在 c2（起 srv_b 时 t=+7s，srv_a 尚未被 client 连入，VCMI server 无客户端会提前退出 → `srv_a.poll()` 非 None 误判）→ 判定延后到 c8（client 连入后 2 server 稳定存活）。

**边界说明**: 真实 `VCMI_server` 不识别 `AuthToken` 帧（T13.10 已知边界，server 端未实装认证逻辑），故认证走协议层验证（`AuthProxy` 补认证端点，照 `p8d_dual_node_sim.py` 范式），游戏帧走真实 VCMI。将来若 server 端实装 `AuthProxy` 同逻辑（收帧 → `TokenVerifier.verify` → 回 1B ACK），即可无缝切换（当前口径下以单机双实例为准，无第二台机器）。

**双机路径口径**: 双机部署路径已用单机双实例实跑完成（`py/p8d_two_instance.py` 13/13 PASS），`py/p8d_deploy_probe.py --remote <host> --port 3030` 路径保留但不再作为待办（无需第二台机器预交换 HSK + 部署 VCMI）。

### P8-E 人机混局验证（2 客户端拓扑）PASS (09-15)

**背景**: T13.10 目标场景"人类 GUI 客户端 + 1 外挂 AI 客户端同局"实跑验证。P8-B/C/D 全 ✅ 后，真正缺口 = 从未验证"人类 GUI 客户端 + 外挂 AI 客户端"可在同一 VCMI_server 同局并正常开局。

**拓扑**: 单机端口 3030（fork build `D:\vcmi-fork-build\bin`，隔离训练），2 客户端：
- Python host (cid=1, VCMITCPConnection，先连当 host，发 `LobbyClientConnected` + `ChangeHost(2)` 让位)
- 外挂AI (cid=2, headless, `VCMI_TESTMAP_ONLYAI=1`，guest，自动接管蓝方回合)
- 人类 GUI（仅同机共存验证，不 join lobby 不占 Twins 2 玩家 slot）

**关键踩坑（#202 衍生）**: Twins.h3m 仅 2 玩家 slot，第 3 个客户端 join lobby 会触发 server NEW_GAME 初始化 "Picking random factions for players" → "Disaster happened" 崩溃（09-15 实测：3 客户端连 Twins，`14LobbyStartGame` 广播后 server 在 NEW_GAME 崩）。故人类 GUI 若真实 join lobby（第 2 个 ClientConnected），AI（第 3 个）超出 2 槽 → 必崩。收敛为 2 客户端：人类 GUI 不连 3030，仅验证进程存活 + SDL 窗口。

**改动**: `py/p8e_human_mix_probe.py`
- 人类 GUI 不带 `--testmap`/`--serverport`（避免 `EntryPoint.cpp` L379 默认 `onlyai=true` 导致人类 GUI 也 join lobby）
- AI 等 server log 第 2 个 `ClientConnected` 后 `send_change_host(2)` 让位
- 判定从 `srv_log_cc()>=3`（3 客户端）收敛为 `>=2`（2 客户端）

**验证**（P8-E PASS）：
- server 存活 ✅
- Python host 连入 ✅
- 人类 GUI 进程存活（同机共存，不 join slot）✅
- 外挂 AI 连入（server log 第 2 个 ClientConnected）✅
- 对局开始（server log 含 "Received CPack of type 14LobbyStartGame"）✅
- server 无崩溃（tail 30 行无 "Disaster happened"/"Crash info"）✅
- 全进程存活（server / human / ai）✅
- 含 BattleStart(132) 多回合闭环（战斗实际发生，AI 正常接管蓝方回合）

**指针**：任务清单 T13.10 P8-E 行 / 踩坑 #202 (ChangeHost 时序) + Twins 2 slot 崩溃 / `py/p8e_human_mix_probe.py`。

### P8-D 跨机器部署脚手架 + 实机验证 (09-12, 设计+骨架+本机 13/13 PASS)

**架构**: 3 种拓扑 (A 本地 3 进程 / B 双机 1S+2C / C 三机 1S+3C), HMAC-SHA256 Token 认证 (client_id + timestamp + nonce 签名, ±300s 时间窗, nonce 去重防重放)。

**模块** (`py/vcmi_protocol/`):
- `auth.py`: SharedKeyManager (32B HSK 生成/校验/落盘 0o600) + AuthToken ([4B len][JSON] 帧) + TokenIssuer/Verifier
- `remote_connection.py`: RemoteVCMITCPConnection 封装 VCMITCPConnection, `_auth_handshake()` 发 token 帧读 1B ACK (0x01=OK), 指数退避重试
- `deployment.py`: NodeConfig/DeploymentConfig + ProcessManager (start/stop/health_check) + StatusFileWriter + KeyDistributor + DeploymentManager

**实机验证** (`py/p8d_deploy_probe.py`):
- `--local` 13/13 PASS: HSK 生成/落盘/轮转 + VCMI_server 启动 + TCP 探活 + RemoteVCMITCPConnection 连接 + 状态文件读写 + 2 节点部署命令构造
- `--remote <host> --port 3030`: 双机模式（保留可用，无需第二台机器——双机路径已用单机双实例 `py/p8d_two_instance.py` 13/13 PASS 实跑完成）

**修复 2 处**:
1. `remote_connection._do_connect` 原调 `VCMITCPConnection._socket_connect` (不存在) → 改用 `VCMITCPConnection.connect()`
2. `get_stats` 原依赖 `VCMITCPConnection.get_stats` (VCMITCPConnection 无此方法) → 改为仅返回 RemoteConnConfig 层字段

**Windows 兼容**: `StatusFileWriter` 用直接 open (非 atomic rename), Windows 目标已存在时 rename 报错; HSK 权限检查仅 Linux 生效 (Windows NTFS 无 POSIX 权限位)。

**与训练并行**: P8-D 探针占 1 核 + 1 端口 (3030), 与 v5 训练 (12 核) 物理资源不冲突, 可并行。

### T7.4 HERO_DEATH 0 死亡根因 (09-12, 子 agent 分析)

**现象**: step 641977, [HERO_DEATH]=0, 首窗 11 局 0 死亡样本。

**根因**:
1. **C 方案 proxy 与 HERO_DEATH 正交**: `blue_hero_killed` (blue 英雄被 red 击杀) 仅 +100 reward; HERO_DEATH 触发条件 = red 英雄 8 方向全堵 (`passable.any()=False` → `zombie=True`)。T06 duel 蓝英雄一死 → game_over 当步 end → HERO_DEATH 根本无机会触发。
2. **T05 36X36 守卫战 autofight 必胜**: [ep_runner_one.py L904](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L904) 注释"autofight 必胜", red 几乎不会战死 → 11 局首窗全守卫胜局, 无 red 死亡事件。
3. **VCMI 引擎 standardDefeat 未落地**: `game_over==2 → reward -= 50` 依赖 C++ `alive_count <= 1` 判定, 当前未实现 (方案_T74 §6 远期 C++ 课题)。

**建议**:
- 判据 1 样本池切到 T06 72X72 duel (blue 英雄存活 → red 进攻 → 有反杀全堵机会)
- ep_runner L1212 加 `[HERO_DEATH]` 诊断埋点 (passable + ah + slots), 区分"真全堵"vs"active_hero 越界 ah=-1"
- blue_hero_killed 保持不计入 HERO_DEATH (避免双罚, 激励轴错窗纪律)
- standardDefeat 落地后复核同帧双罚 (T7.4 -50 + engine -200)

**代码坐标**: [ep_runner_one.py L1212-L1223](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L1212) (HERO_DEATH 触发) / [L526](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L526) / [L899](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L899) (zombie 赋值) / [L944-L962](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L944) (C 方案 proxy) / [strategic_env.py L1117](file:///d:/Bigdata/hero3_fresh/vcmi_gym/envs/v13/strategic_env.py#L1117) (game_over==2 判负)

### Router 断言机制链与战斗 AI 真相 (R6, 截至 2026-08-31)

**症状**: `[Router] battleStart exception: Assertion failed in router.cpp: dynamic cast to V13::BAI failed — fallback to StupidAI`，训练期 15-55% 局出现；**89 局 ZOMBIE 与断言 100% 共现**。

**机制链** (代码坐标, vcmi-native-build 树):
1. battleStart (router.cpp L330+): model 来源 = baggage->modelLeft (红方 pid=0) / modelRight (蓝方 pid≠0); PATH 类型 → GetModel(modelkey) 文件加载
2. ModelType::NN/USER 分支 (L438): `bai = CreateBAI(model, ...)` → **factory.cpp L117**: `#if USING_ONNX` 块内 version==13 → make_shared\<V13::BAI\>；**USING_ONNX=0 时整个块编译掉 → return 空 shared_ptr**
3. router.cpp L442: `dynamic_cast<V13::BAI*>(bai.get())` — 空指针 cast 返回 nullptr → ASSERT throw → catch → fallback StupidAI
4. **根因**: AI/MMAI/CMakeLists L60 `add_definitions(-DUSING_ONNX=0)` 硬编码 + 构建环境无 libonnxruntime
5. 蓝方 (MMAI_RANDOM=SCRIPTED) 走 SCRIPTED 分支不受影响 → 断言恒在红方

**战略认知 (最重要)**: 红方战斗 AI 从训练第一天起恒为 StupidAI — T03 毕业 / T04 经济突破 / 96% 正局率全部在此条件下取得。**非回归，是既定环境**。比例性 (rout 15-55%) = 接战场次占比；zomb% ⊆ rout% (兵劣才死)。

**修复路径 (R6, 绑定 T8 战斗集成/T5 对抗前置)**: 部署 onnxruntime (WSL prebuilt) → USING_ONNX 0→1 → 重编 libMMAI → 三副本同步 → 验证断言消失 + 战斗强度。⚠ 启用后战斗变强 = 奖励结构非平稳，课程节点一次付。

**排查教训**: ① typeinfo/vtable grep 模式坑 (踩坑 #125)；② Release build type 触发 strip 953KB 空壳 (踩坑 #126)；③ visibility default 修复只在 ENABLE_MMAI_TEST 测试块内，正式构建从未生效 (KNOWLEDGE.md visibility 条的真相反转)。

### getUpperArmy() 取兵机制 — visit+RECRUIT=兵直上英雄 (09-02 修正: 需显式 getVisitingHero, 见文末 P1/P1b 条)

`CGTownInstance::getUpperArmy()` (CGTownInstance.cpp L879): `if(getGarrisonHero()) return getGarrisonHero(); return this;`

**关键推论**: RECRUIT 执行链 (AAI.cpp case 16-18) `dst = town->getUpperArmy()`：
- 英雄**不在城** → dst=town → 兵进 garrison (城驻军)
- 英雄 **visit 己方城** → dst **仍非英雄** (09-02 实测 visit=1/dstIsHero=0 — 本行 08-31 推论错误, 见下 P1b)

这是"回城取兵"引导的理论基础：英雄回城 + 取兵窗发 16/17/18 = 完整的兵力上英雄链路，**无需任何新动作码**（act15 SWAP_ARMY 是英雄↔英雄交换、act22 GARRISON 是反向驻守，都取不了城 garrison 存量兵）。存量兵上英雄需另外的 C++ 能力（未实现，R6 同批评估）。

### obs towns 段寻址表 (埋点/引导用, 截至 2026-08-31)

- 段起点 `obs[336]`，每城 18 字段 (`_TOWN_FIELDS=18`)，8 槽 → obs[336:480]
- 字段序: id@+0 / **owner@+1** / pos_x@+2 / pos_y@+3 / pos_z@+4 / buildings@+5 / **garrison[7]@+6..12** / gold_income@+13 / recruit_mask_lo@+14 / recruit_mask_hi@+15 / build_mask_lo@+16 / build_mask_hi@+17
- 空槽: id=-1 (C++ 初始) → Python obs 全 0；有效城判定 `id>0 且 (pos_x>0 or pos_y>0)`
- **garrison 已填充 (09-02 P3)**: strategic_state.cpp town 填充循环 memset 后追加 getUpperArmy() 7 槽 count → obs 城槽 field 6-12; ⚠ visiting 期间 upper=visiting hero 会镜像英雄兵力 (语义=城内上部军队, 非纯驻军)
- **recruit_mask 有真实填充** (fill_v3_fields, dwelling 已建位图 level*2+upgrade) — 回城取兵触发信号用它
- 注意: 城易主后槽位可能变 (填充按 players 遍历序) — 跨步跟踪城身份用 id 字段映射, 勿用槽位号

### 城格不可站的结构性定性 (TOWN 判定 bug 根因, 截至 2026-08-31)

vmap town template 实测 (六图一致): `mask=["VVVVV","VVAVV","VVVVV"]` — 中心 'A' = actionable+**blocking** (逐格移动阻挡)；`visitableFrom` 四周 '+' = 引擎语义为英雄走到**邻格**触发访问并**停在邻格**。

→ `英雄坐标==城坐标` **结构性永假** (非概率性)：修复前 1850 局 × 24% 动步占比 0 次命中即为佐证。TOWN 类判定一律用 **dist≤1** (邻格)，勿用精确坐标。判定与引导配套缺一不可 (判定让糖能发 / 引导让模型走到糖边) — 详见已完成任务.md 08-31 条目。

---

## 取兵链路三层根因与打包修复 (P1+P1b+P2+P3, 2026-09-02)

**症状**: 79 集 [TOWN_VISIT] 取兵窗 13 次 / [ECON] 招兵动作 37 次, 效果级 [RECRUITED] 0 次 — 兵力从未上英雄。

**三层根因 (逐层实证)**:
1. **招兵落点黑洞**: AAI.cpp case16-18 `dst = town->getUpperArmy()` — 英雄无法踩上城格 (城格 pas=0, visitable-not-standable) → 引擎 visit 永不发生 → getUpperArmy 返回城驻军 → 兵招进 garrison; 且 VCMI 1.8 getUpperArmy 实现**只返回 garrisonHero 或 town 本身, 不含 visiting hero** (CGTownInstance.cpp L879-884, 踩坑 #133) — 即使 visit 成功 dst 仍非英雄 (实测 visit=1/dstIsHero=0)
2. **garrison obs 恒 0**: strategic_state.cpp memset 未实现 → 招进的兵模型/runner 双盲 (P3 已修)
3. **检测器布局错误**: obs 英雄槽 army = 7 个纯 count 在 field 15-21 (无 creature_id 字段, strategic_env.py _build_obs); runner 读 11-19 混入 knowledge/max_mana (P2 已修)

**修复内容**:
- **P1** (AAI.cpp case16-18): 招兵前 visit 块 (moveHero 城锚点, 复用 case22 流程) + **邻接守卫** `distSq(standPos, cur->pos) > 2 → return noTarget` (moveHero 单格限制下远距离进城必失败, 避免白等 2s; 远距离等 TOWN_VISIT 引导回城再招)
- **P1b**: dst 显式改 `town->getVisitingHero()` (public const) — 引擎校验 hero==getVisitingHero() 通过, 兵直上英雄
- **P3** (strategic_state.cpp): town 填充循环 memset 后追加 getUpperArmy() 7 槽 count → obs 城槽 field 6-12 (原生支持零改动); 语义注意: visiting 期间 upper=visiting hero 会镜像英雄兵力
- **P2** (ep_runner_one.py): 兵力检测器改读 field 15-21, 权重 [10,40,120,350,900,1600,2500] (T6/T7 外推)

**部署**: libMMAI + libmlclient 重编 (RelWithDebInfo, -j4), 同步 4 副本: vcmi-native/rel/bin (运行时), vcmi-workspace/vcmi/rel/bin, vtest/bin, build/bin; 备份 .bak_taketroops_0902_0433; 补丁镜像 `tools/patches_20260902/`

**诊断基建**: AAI.cpp 临时 fprintf → `/tmp/rl_recruit_diag.log` ([yourTurn]/[execAdv] 动作值 + visit=/tier=/dstIsHero); stderr 被 MMAI console 重定向不可用 (踩坑 #134)。验证后可删。

**待验证**: [RECRUITED] 首触发 = TOWN_VISIT 回城集 (模型行为依赖, 引导英雄邻接己方城后招兵)。出现即全链闭环确认。

## 运行时架构实锤 (/proc maps 验证, 2026-09-02)

- VCMI server 在 **runner 进程内运行** (无独立 vcmiserver 进程): libmlclient + libMMAI 都加载于 ep_runner_one.py 进程
- libMMAI 运行时路径 = `vcmi-native/rel/bin/AI/libMMAI.so`; libmlclient = `vcmi-native/rel/bin/libmlclient.so`; **rel/ 即构建树** (CMakeCache 在 rel/), vcmi-native-build 是双目录同步副本
- 动作通道: python ctypes 写 g_rl_action → AAI yourTurn 轮询 adventure_get_action → executeAdvancedAction switch (a 11-24, try/catch 静默包裹 — 诊断必须独立文件)
- stderr 分层: 启动期通 hermes, AI 运行期被 MMAI console 重定向 (踩坑 #134)
- 多副本清单: rel/bin (运行时) / vcmi-workspace/vcmi/rel/bin / vtest/bin / build/bin — 改 .so 后全部同步

## P1c 坐标系修正 + start_home 出发前招兵 + 诊断基建 (09-02 下午)

### P1c: 邻接守卫坐标系修正 (AAI.cpp case16-18)

P1 的邻接守卫 `distSq(standPos, cur->pos) > 2` 用**锚点坐标** — 城/英雄各自经 convertFromVisitablePos 偏移, 邻接英雄对城锚点 Chebyshev 距离可达 2-3 → 守卫全误杀 (DIAG7: enter 有, afterMove 恒 0, 71/71 全弃)。

**修正**: 双方改 `visitablePos()` 口径, Chebyshev≤1 判邻接; 双路径 moveHero — 锚点不同 → 走 standPos (邻格), 已在锚点 → 走对象格 tp 触发 visit (与 a==8 同款)。坐标系双口径坑见踩坑 #137。

### start_home: 出发前招兵阶段 (ep_runner_one.py, 用户设计)

> 用户直觉: "取兵每局都应该有 — 英雄每次出发前, 先招兵、带兵、再出城探索"。确定性前置, 不再依赖模型自发回城。

- **流程**: 每局 start_home=True → obs 3203 读主英雄坐标 + towns 段 (336+ti*18, owner==0 且有城) 找首个己方城 → 未邻接: a=24 (回城引导) + move_town_bfs 引导; 已邻接: 退出阶段 (下一拍引擎 P1 visit+招兵接管); 无己方城 / >80 步: 放弃
- **前置条件**: objective_reward>0 且 red_model 非 None 且 visit_econ_steps<=0 (不与取兵窗叠加)
- **冷却 bug (自发现自修)**: 初版邻接退出时清零 visit_econ_cooldown → 取兵窗无限连发城内 spam 招 0; 修正为保持冷却 (窗结束/触发后 30 步不重触发)

### 诊断基建 (验证闭环后可删)

- **引擎侧 DIAG7** → `/tmp/rl_recruit_diag.log`: `[RL-DIAG7] enter (townFound/visited/vhero) → afterMove (pos/stand/visited/vhero) → w2 (等待循环) → w3` 五拍链路, 定位守卫误杀/visit 未遂一步到位
- **runner 侧 [START_HOME]** → `/tmp/hermes_ep_*.log`: abort (放弃) / adjacent (已邻接退出) / guide (引导中, 变更时打印) 三态
- **闭环判据链**: `[START_HOME] adjacent` → DIAG7 `afterMove visited=1` → `dstIsHero=1` → `[RECRUITED]` — 四拍全中即取兵链路全链贯通
- 一键监控: `py/monitor_recruit.sh` (服务状态 / DIAG7 visit-tier / RECRUITED / 本 run 事件统计)

## P1d 逼近走两代演进 + 坐标三实锤 (09-02 深夜)

### 坐标三实锤 (P1d 日志实锤, 一切取兵寻路的坐标系基准)

- **hero appearance offset = (1,0), 不是 (0,0)**: CGHeroInstance 无 visitablePos/getVisitableOffset override (grep 实锤), offset 来自 appearance 模板; 双数据点交叉确认 (heroPos=(3,4)/hv=(2,4) 与 heroPos=(27,29)/hv=(26,29)); 即 convertFromVisitablePos(tp) = tp+(1,0)
- **town offset = (2,0)**: 城锚点 pos=(2,3) → 真门格 `town->visitablePos()` = (0,3) — **门格在城锚点左侧 2 格同 y**; T04 六图 towns=1 恒为同一座城, tv 恒值非 bug
- **P1c 主路径自洽性**: guard 放行后 standPos=tp+heroOffset=(1,3), hero 站 (1,3) 时 hv=(0,3)=tp → moveHero(tp) 单步进格 visit ✓ — 主路径无毛病, 缺陷全在 approach 分支

### P1d-v1 手工单步逼近 (已废弃): 两缺陷

- **单轴退化 (结构性)**: approach 只试 x/y 正交 2 候选格, x 向候选 (26,30)/(25,29) 恒被城占/blocked skip → 退化成单轴 y 爬行, tv.x=0 vs hero x=27, dx=26 永不收敛
- **移动力打转 (运行时)**: 回合末移动力 <100 → `CCallback::moveHero` (void 返回, **失败静默无反馈**) 单步失败, heroPos 恒 (3,4) 8 连弃原地打转, 同回合 DIAG6 反复触发 16/17/18 次

### P1d-v2 引擎寻路直走门格 (现行, AAI.cpp case16-18)

- **方案**: 抛弃手工单步正交逼近, 直接 `cb->moveHero(cur, tp, false)` — tp = town->visitablePos() 真门格; 引擎沿路径**多格推进**, 移动力尽停半路, 下拍续走 (dxv/dyv>1 仍走 approach2), 踏上门格即触发 visit
- **moveHero 签名** (CCallback.h): `void moveHero(const CGHeroInstance*, const int3&, bool transit)` — void 无返回, 成败只能靠前后 pos 对比 (approach2 打点: `from=(...) to=(...) goal=(...)`)
- **运维坑**: `/tmp/rl_recruit_diag.log` 重启**并不会自动清空** — 09-02 实测混入前版 .so 残留 88 行, 差点据旧数据误判; **每次重启 .so 须显式 `> /tmp/rl_recruit_diag.log`**; 旧版判别法: 有 enter 无 guard=P1c / 有 `approach to`=P1d-v1 / 有 `approach2 from=`=P1d-v2
- **.so 备份**: libMMAI.so.bak_p1dv1_0902 (P1d-v1, 3 副本); AAI.cpp 备份链 .bak_p1d_0902(P1c) / .bak_p1dv1_0902(P1d-v1)

## P1e→r2→r3 approach 分支重写: CGPath 逐点推进 + 坐标双系统换算 (09-03)

### 幽灵 x-1 偏移: moveHero 锚点坐标 vs CGPathNode 格子坐标 (r2 实锤)

- **现象**: r2 部署后招兵链路端到端全通 (两局 avail 28→27, dstIsHero=1), 但 `approach2P plen=4` 只推进 2 格, 第 3 步 moveHero 目的地出图中断 → hero 停在目标左侧 1 格 (幽灵偏移), 多耗一拍才进城
- **根因 = 坐标双系统**: `CGameHandler.cpp L874 moveHero(dst)` 内部先 `convertToVisitablePos(dst)` (**锚点坐标** −offset(1,0) → 落格); 而 `CGPath.nodes[i].coord` (CGPathNode) 是**格子坐标** (真实可站格)。r2 把格子坐标直接 push 进 pathVec 喂 moveHero → server 再减 offset → 每步落点整体西移 1 格
- **换算铁律**: 喂 moveHero 的每个途经点必须 `cur->convertFromVisitablePos(node.coord)` (格子→锚点); 起点跳过比较也须同口径 — `it->coord == cur->convertToVisitablePos(cur->pos)` (两侧都格子坐标; r2 的 `it->coord == cur->pos` 格子 vs 锚点永假 → 起点节点漏跳)

### r3 修复与 plen 4→3 机制

- **r3 两刀** (AAI.cpp approach2 主刀块): ① path 节点入队前 `convertFromVisitablePos(it->coord)`; ② 起点跳过改格子口径 (见上)
- **plen 4→3**: r3 起点跳过首次真正生效 — path 2 步 (格子转锚点) + 尾补 standGoal 兜底 1 步 = plen 3, **单拍直达门格** (r2 的 plen=4 含漏跳的起点节点)
- **闭环验证判据** (/tmp/rl_recruit_diag.log): `approach2P plen=3 turns=0` → 下一拍 `DIAG6 heroPos=(1,3)` (门格) → `visited=1 vhero=1` → 同拍 `RECRUIT-DIAG tier dstIsHero=1 n=1` — 取兵四拍链压缩为 **approach→招兵两拍**
- **.so**: md5 5872b453 (4 副本一致), AAI.cpp 备份 .bak_p1e_r2; 镜像 tools/patches_20260902/AAI.cpp 已同步

### PathfinderCache 用法 (P1e 引入)

- approach 分支: PathfinderCache 取 CGPath, 门格 (`town->visitablePos()`) 8 邻可站格作中间目标 (pfCand 打点逐一验: turns=0 本回合可达 + acc 可达性 + 可站, turns=255 = 不可达弃)
- CGPath 逐点推进: `it->turns > 0` 的移动力尽段截断 (server 逐格校验必拒, 留下拍续走); CGPathNode::coord = 格子坐标, `turns` = 还需几个回合到达该节点

## R7 battle query 卡死: 根因定性 + 埋点五件套 (09-03)

### 机理链 (闭合, ep_4040 日志实锤)

- 移动踩守卫/野怪 → query 栈叠三层 movement111→visit112→battle113; moveHero/visitObject 末尾收尾 popIfTop FAIL×2 = **原版正常行为** (静默靠 onExposure 链回收)
- 战斗结束 endBattleConfirm → removeQuery(battle113) → visit112.onExposure (ENTER 打点实锤到达) → **notifyObjectAboutRemoval 内部中断** (BattleQueries.cpp:38-41) → visit112/movement111 残留 → RED 全部动作被拒 (含 endTurn, "has to answer queries") → 回合系统死等 s_turn_player → adventure_wait_for_turn 永旋 → 冻结
- 已排除: restartBattle/L86 result 清空 (RED isHuman()==false 不可达); heroGotLevel queryID=-1 (AI 自动选技能无害); Router dynamic cast 失败 = 并存独立异常 (绑 R6), 非 query 卡死成因

### 三候选根因与埋点区分法 (09-03 部署, 复发一击定位)

| 候选 | 区分打点 | 位置 |
|------|---------|------|
| ① result 空 (assert NDEBUG no-op 跳过) | `notifyObjectAboutRemoval ENTER hasResult=0` + `SKIP result-empty` | BattleQueries.cpp |
| ② visitedObject 非 CGCreature (虚调用无实现) | ENTER 行 `objType=` 非 monster | BattleQueries.cpp |
| ③ battleFinished 内部中断 (DEFENDER merge stacks 死循环/hero 死亡悬空指针) | ENTER 有而 `battleFinished RETURN` 无; movement onExposure ENTER 有而 visit-done 无 (打点在 hero 解引用前) | BattleQueries.cpp + MapQueries.cpp |

- 配套: MapObjectVisitQuery.onExposure 补 qid + `notify-done` (ENTER 有 notify-done 无 = notify 内部中断); QueriesProcessor popIfTop `OK` 成功打点与 FAIL 成对 (验证回收链闭合); 编译前验证 `result.has_value()`/`queryID.getNum()`/`getTypeName()` 全部 grep 实锤
- 验证: 部署后 popIfTop OK×86 + onExposure ENTER qid=28 带状态, 链路正常; notifyObjectAboutRemoval 链 T04 图 0 守卫未触发属正常

### fuse 机制定位 (修正"看门狗缺失"认知)

- strategic_env.py `_adventure_wait` (L854-893): 后台 daemon 线程调 `adventure_wait_for_turn()`, `t.join(min(_vcmi_timeout, 900))` 超时抛 RuntimeError → ep 自愈; **fuse 一直存在且有效** (7348 冻结 13min 死亡即触发), 本次优化 = 上限 900→300 (正常单步 <10s)
- vcmi_gym 为 /mnt/d 源码直连 (venv 无 pip 安装态), 单点改动 + 清 __pycache__ 即生效

### 编译部署归属实锤 (本次修正)

- server/queries/*.cpp → vcmiservercommon 静态库 → **实际编进 libmlclient.so** (strings 反查 'popIfTop FAIL' 只在 libmlclient.so); `cmake --build rel --target mlclient MMAI -j4` 双目标一并重编; rel/bin 原位编译即部署 (/proc maps 实锤运行时加载该路径)
- 训练 venv = `/home/administrator/vcmi-workspace/venv` (/mnt/d 下 venv 已不存在, systemd-run 必须绝对路径, 踩坑 #139)

### R7 处置状态 (09-03)

- 埋点五件套: ①埋点 ②空 result 防御 (埋点 SKIP 行覆盖诊断, 显式防御未做) ③fuse 300s ⑤AAI 六处 [AAI DBG] fprintf 清理 (保留 selectionMade) — 已执行; ④Router cast 专项绑 R6
- 部署后 10 ep × 6 图 (T04 全覆盖) 零复发; 若复发, /tmp/hermes_ep_*.log 按上表区分法定位
- 运维经验: `\\wsl.localhost\Ubuntu\home\...` UNC 路径可直接用编辑工具改 WSL 文件 (免 bash sed 转义坑); PowerShell 管道内 head/grep 会走 Windows 侧报不存在, wsl 命令内管道须整体在引号内

## R6 战斗 AI 修复: onnxruntime 部署 + USING_ONNX=1 (09-03)

### 机制与修复

- 根因: MMAI CMakeLists `add_definitions(-DUSING_ONNX=0)` → factory.cpp CreateBAI 的 `#if USING_ONNX` 块不编译 → 返回空 shared_ptr → router.cpp:438 `dynamic_cast<V13::BAI*>` 断言 → fallback StupidAI (红方战斗恒 StupidAI, 训练第一天起如此)
- 修复: onnxruntime 1.19.2 linux-x64 (与 Windows 树 onnxruntime-win-x64-1.19.2 同版) → /opt/onnxruntime (include/ + lib/), ldconfig 注册; CMakeLists: USING_ONNX=1 + `target_include_directories(MMAI PRIVATE /opt/onnxruntime/include)` + `target_link_libraries(MMAI PRIVATE /opt/onnxruntime/lib/libonnxruntime.so)`; 双树同步 (vcmi-native + vcmi-native-build); 重编 `cmake --build rel --target MMAI -j4` 一次通过; vtest 副本同步
- 版本依据: Windows 侧曾用 win-x64-1.19.2 编译成功 ( /mnt/d/vcmi_model_ai/ 实锤), C API 头跨平台通用

### 模型加载双路径 (关键认知)

- **MMAI_USER (训练自对弈)**: threadconnector.cpp L476 `leftModel = Function wrapper (f_getAction0 Python 回调)` → ModelType::USER → router case USER → CreateBAI → V13::BAI 包装; **战斗动作由 Python 策略经回调提供, 不需要 onnx 模型文件** — USING_ONNX=1 只解锁 BAI 包装层
- **PATH 模式 (C++ 内推理)**: modelLeft=PATH → CreateNNModel(path) 经 VCMI ResourceHandler (EResType::AI_MODEL) 加载 .onnx → version==13 → V13::NNModel; 需部署 bc_model_v3464b.onnx 到 VCMI AI_MODEL 资源路径 (尚未部署, 训练不需要)
- factory version 门禁: readVersion 读模型 metadata "version" 键, 非 13 抛异常 (WSL factory 仅支持 13)

### 验证方法 (对照法)

- 修复前: hermes ep 日志每战必有 `[Router] battleStart exception: dynamic cast to V13::BAI failed — fallback to StupidAI` (历史累计 748 次)
- 修复后 (ep_11638 实测): BattleProcessor::startBattle DONE + 三层 query 栈 (movement93→visit94→battle95) + **零 Router fallback** + R7 埋点全链 (`notifyObjectAboutRemoval ENTER hasResult=1 objType=town` → `battleFinished RETURN winner=0`)
- 运行时: `ldd rel/bin/AI/libMMAI.so | grep onnx` 解析到 /opt/onnxruntime/lib/libonnxruntime.so.1
- ⚠ 战斗强度变化 = 非平稳 (StupidAI→V13 BAI+Python 策略), 战略层 act 序列不变已验证, avg_r/胜率波动需后续观察

## T05 全面化: 战斗剧本确立 + map 标签造假修正 (09-04)

### 课程切换实录 (T04 → T05)

- **T05 混入 (09-03)**: 12 T04 + 4 T05, 首 ep 即 `[GUARD] +100` 落袋 (R6 后战斗奖励首次经策略模型), r=131 vs T04 剧本 15-48
- **move_to_force 60→200 实验 (09-03) 失败回滚 (09-04)**: 全程引导 13/32 挂死局 + r=-429 + a=2 占 34% + TOWNSTALL 10.4/ep — obj_best 目标长局/新图频繁失效, 引导拖着撞墙; **教训: 引导时长不是解, 目标可达性才是** (60 版 18ep avg_r 1.8 有 +131 局)
- **T05_36X36_02 移除**: 守卫过强 (swordsman8+archer10+peasant15) 6 局全负 -79~-122, 调守卫兵量后回归
- **T05 全面化 (09-04, 方案 B 全切)**: 判据①②④达标 (T05 三图高分 32/34 局近乎全胜 / 自发经济 0→54 次/40ep / 200 步局 24.4% 无大负局) + ③ avg_r 口径失真 (混合轮换被 T04 短剧本稀释) → 全切 T05 三图 (36X36_01 / 52X52_01 / 52X52_02), T04 12 图退役注释存档
- **自发经济回流确认**: 强制窗外 16-21 从 0 → 54 次/40ep (20 局有自发, 含 T05 局) — "兵力→战斗+100→招兵价值"闭环生效, 拍板"等 R6 兑现"兑现
- **T04_mir 高价值剧本泛化**: 30X30_04_mir 14 局 r≥60 / 36X36_03_mir 14 局 — 战斗/多目标路线跨图迁移 (退档前最后状态)

### map= 标签造假发现与修正 (重大, 踩坑 #143 事实 5)

- **现象**: "T04_mir" 局三连 r=141.53 声称 20X20/36X36 不同尺寸, 但 obs_nz=223 + act 逐字节相同 = 同一张图; 根因 = _mir 图未 cp 到运行时路径, **VCMI 加载失败不报错而是 fallback 复用已缓存图** → map= 标签与实际图脱钩
- **检验法**: obs_nz 特征带对照 (同图同带 / 跨尺寸必异: 20X20≈369 / 36X36≈246-309 / 52X52≈223+act 结构差); 修复 = 新图必 cp rel/bin/data/Maps/ + obs_nz 带验证
- **影响重估**: _mir 补齐前所有 "_mir 局" 数据作废 (实为 fallback 图); 补齐后 _mir 首次真实加载即高分 (36X36_03_mir 94 步 101.75 / 30X30_04_mir 200 步 90.35) — 180° 旋转变体泛化为真

### 200 步局认知 (两阶段)

- 60 版 (现行): 200 步局 ~20-25%, 浅负 (-11) 或正分 (10-31 有事件收益) — obj_best 目标可达性问题, 引导目标选择优化待立项
- 200 版 (已回滚): 全程引导放大 obj_best 失效 → 拖墙 200 步 r=-429 — **引导时长不是解**
- T05_36X36_02 特例: 守卫过强 6 局全负, 移出轮换待调守卫回归

## T06 课程: duel→1v3 分层上线 + 双根因 (09-06/07)

### 课程结构与判据
- T06 4 张原图 (72X72_01/02 + 108X108_01/02) 结构 = **1v3** (1 red 英雄+城 vs 3 blue 英雄+3 城对角) + 5 金矿 + 15 资源 + 20 野怪; 一次叠加 3 难度轴 (大图/多敌/3 城胜利) 违反"一次一轴" → **duel 变体分层** (去 hero_2/3+town_2/3 = 只加大图轴, gen_t06_duel.py 批量产出 72X72_01/02 + 108X108_01/02 四张)
- duel 站稳判据 (登记任务清单): ①≥30 局且 avg_r 无恶化 (后 1/3 ≥ 前 1/3×0.8) ②自发经济 ≥80% 局 ③200 步局 ≤20% ④守卫胜闭环 ≥70% — **实测 32 局 4/4 达标** (83.0 vs 65.1 比值 1.27 / 100% / 0% / 96.9%), 当日触发 1v3 上线
- 观察统计脚本 `py/check_duel_watch.py <尾窗>`: 自发经济 (act 序列 index≥24 的 16-21) / 200 步局 / r 分布 / T05 同口径对照 一键出表

### 双根因 (1 步空壳局的确定性形态)
1. **identifier 命名空间混淆**: alchemist 是职业名 (subtype 字段) 非英雄名 → 引擎 `Couldn't resolve hero identifier` 拒启动 → runner 1 步收 done, obs_nz=0 (空观测)。判定信号: 多局异常**形态完全一致** = 确定性配置错误。英雄实名以 `vcmi-native/config/heroes/castle.json` 顶层 key 为准 (orrin/valeska/edric/sylvia/lordHaart/sorsha/christian/tyris/rion/adela/cuthbert/adelaide/ingham/sanya/loynis/caitlin)
2. **HeroPool 对称校验**: ServerPlugin (server/ML/ServerPlugin.cpp) 非 randomHeroes + 恰好 2 owner 时强制双方同名 pool 英雄数相等 — 1v3 (1≠3) / 1v7 全拒。已放宽: 大小不等降级 stdout 警告, pool 名不同仍 throw。**mlserverplugin 是独立 SHARED 库** (add_library mlserverplugin SHARED), 重编不触 libvcmi.so 铁律; 构建 = `cmake --build ~/vcmi-native/rel --target mlserverplugin -j4`, 副本同步 vtest/bin + hero3_vcmi/build/bin
- 1v3 真实首局: **73 步守卫胜 r=82.38** (vs duel 基线 75.5 同水平) — blue 3 roaming 英雄未速攻破防

### 教训
- identifier 校验集 (VALID_*) 每一项必须引擎实测过, 校验脚本与之同步维护 — ** subtype/template 字段值与 object 命名空间同形不同义**
- duel 变体 "侥幸正常" 掩盖 hero_3 错误 (删对象绕过了坏 identifier) — 批量生成变体后**原图必须原样保留验证**, 不能只测变体

## a1ea3f4d2d 摘取 + battle-only ModelAI 链路 (09-06)

### NKAI mutex race 摘取 (上游官方 fix)
- patch: `AIStatus::removeQuery` 删锁 → `AIStatus::receivedAnswerConfirmation` 函数头加锁 (NK1/NK2 双文件, fork 无 NK1 只改 NK2); **安全性前提 = removeQuery 全树唯一调用点在 receivedAnswerConfirmation 内 (持锁后调用, std::mutex 非递归无死锁)**
- ⚠ 语义变化: removeQuery 现要求调用方自带外层锁 — 未来新增调用点必须持锁
- 已落 WSL vcmi-native + Windows vcmi/ 双树 (cp 同步防 R5); **重编部署 (libMMAI.so) 待下次停训窗** — 源码先行是摘取窗标准动作
- 价值: 该函数是 R7 battle-query-hang 同区, 裸跑访问 requestToQueryID/remainingQueries 与其他线程并发 = 真 race

### battle-only 场景 ModelAI 选择 (静态验证通过)
- **关键链路实锤**: battle-only 对局玩家全 AI → `CClient` L253-257 → red 走 g_adventure_allied_ai 注入或 settings["ai"]["adventureAlliedAI"], 其余走 aiNameForPlayer() → adventureEnemyAI → `CDynLibHandler::getNewAI(name)` → `AI/<name>.dll` — **battle-only 玩家 AI 走 adventure AI 链 (GetNewAI/CGlobalAI), 不走 getNewBattleAI (独立战斗 AI)**
- 四要素全绿: ModelAI.dll 导出 GetNewAI (战斗回调由 CGlobalAI→CBattleGameInterface 继承承接) / schema adventure*AI enum allow ModelAI (660ea59c28) / 运行时 settings 双配 "ModelAI" / DLL+onnxruntime+bc_model 部署在 D:\vcmi-fork-build\bin
- **缺口 (登记)**: schema combat*AI (combatEnemyAI/combatAlliedAI/combatNeutralAI) 的 "MMAI" 选项无对应 DLL (bin/AI 无 MMAI.dll) — auto-fight 链 (CPlayerInterface L1874 getNewBattleAI) 与中立玩家战斗选 "MMAI" 必失败; ModelAI.dll 无 GetNewBattleAI 导出不能填 combat*。修法 (待需要): ModelAI 补导出 GetNewBattleAI 工厂 + combat* enum 补 "ModelAI"
- 运行时 GUI 冒烟步骤: VCMI_client.exe → 单人游戏 → 战斗模式按钮 → 查 `Documents\My Games\vcmi\logs\VCMI_Client_log.txt` 验证 "lead by ModelAI" + battle 回调

## 1v3 首周判据数据面达标 + 训练全面后台化 (09-07)

### 1v3 (T06_adventure_72X72_01) 观察窗数据 — 判据数据面达标

- **爬坡轨迹**: 首夜窗 23 有效局 avg≈68.9 (含 r=4.0 早期战败) → 午后窗口 15 局 **avg≈80.4** (75.1~86.11), **已超 duel 基线 75.5** (+6.5%); 前 1/3 avg 80.0 → 后 1/3 81.8 上行; 早期战败局消失 (最低 75.1) — 模型在多敌图持续变强
- **健康指标**: 自发经济 100% 局 / 200 步局 0% / ZOMBIE/FUSE 0 / obs_nz=301 独立特征带稳定 — 回退线 (avg -30% 或挂死 >40%) 从未接近
- **多敌图 reward 反超 1v1 的解读**: 1v3 图 3 蓝城+5 金矿 vs duel 2 城 3 矿 — 经济事件 (MINE/RECRUITED) 目标更多, 蓝方 roaming 未形成有效压制, 红方经济剧本空间更大; 不代表战斗变强, 守卫胜闭环口径同前
- **8 图随机轮换波动认知**: 选图 = `random.choice(MAPS)` 均匀随机 (train_wsl2_ppo_v2.py), 85 局窗口 52X52_01 出现 18 次 (期望 10.6, +2.4σ) 属正常波动 — 图分布偏差不作课程异常信号, 看 r 与健康指标
- **判据口径**: 1v3 首周判据 4 项 (累计局数 ≥30 / avg_r 后 1/3 ≥ 前 1/3×0.8 / 自发 ≥80% / 200 步局 ≤20%) 数据面已达标; "守卫胜闭环 ≥70%" 与蓝英雄击杀事件随窗继续跟踪

### 训练实例归属与后台化 (09-07 午后恢复实录)

- **中断形态**: systemd unit 06:35 被外部 stop + 用户 09:43 前台终端启动 (PID 400 pts/0) → 该终端实例随后死亡, keepalive 亦丢 → 16:09 发现双 inactive (踩坑 #169 恢复序第二次实战: 补挂 keepalive → restart_train_v5.sh → grep resume 点)
- **resume 锚点**: checkpoint 555165 vs 日志残留 556410 (损失 ~1245 步 ≈10 局, 非优雅中断正常损耗); resume 后 5h+ 稳定 125 局零 ZOMBIE
- **前台跑法风险定论**: 前台终端实例**无 systemd 存档兜底**, 终端一关训练即死且 checkpoint 停在最后一次自动存档 — 训练一律走 `py/restart_train_v5.sh` 后台 transient unit (keepalive + 存档双保险)

### 多 resume 日志窗口统计套路 (踩坑 #170 配套)

- 取"最后一次启动后"窗口: `L=$(grep -n 'Loaded train state' f | tail -1 | cut -d: -f1)` + `tail -n +$L` — 写进 py/_tmp_xxx.sh 由 wsl bash 执行 (绕开 #130 $var 撕裂), 用完即删
- 窗口校验两件套: `wc -l` 看体量 + `tail -1` 应为最新 `step=... ep=...` 行 — 边界对才开统计
- `py/check_duel_watch.py` 尾窗 200ep 口径与行号窗口口径互补: 前者跨重启看趋势, 后者精确到本次运行

## a1ea3f4d2d 部署纠偏: target 归属判定法 (09-07 晚)

### 结论 — 训练栈无需重编, race 不在链路

- **归属实锤**: 摘取改动 `AI/Nullkiller2/AIGateway.cpp` → 产物 **libNullkiller2.so**; 训练栈实际加载 **libMMAI.so** (源码 = `AI/MMAI/`, 独立实现 AAI/BAI/main.cpp, 与 NK2 两套代码)
- **加载链证据**: train_wsl2_ppo_v2.py `--blue_ai MMAI_RANDOM --blue_adventure_ai MMAI` (C8.5 起替代 NK2, 见 L129 弃用注释: NK2 内存爆炸 3.7-7.5GB/局 → WSL OOM); 自弈 red/blue = MMAI_USER → 全走 libMMAI.so
- **同构扫描**: AI/MMAI/ 全目录 grep `removeQuery|receivedAnswerConfirmation` = 0 命中 — 上游 NKAI race 在 MMAI 库不存在
- **cmake 零编译行解读**: `Built target MMAI` 无 Building 行 = target 依赖未变的**正确信号** (AIGateway.cpp 非 MMAI 依赖), 不是故障
- **处置**: 改动保留 NK2 源码树 (Windows/WSL 双树已同步); 将来回用 NK2 对手时 `cmake --build ~/vcmi-native/rel --target Nullkiller2` + 同步 vtest/bin/AI 即生效; `libMMAI.so.bak_race_0907_2252` ×2 备份留档

### 登记规范 (踩坑 #171)

- "上游修复摘取 → 待重编部署"类任务, 登记前必须双确认:
  1. **改动文件 → target**: 看 `AI/<目录>/CMakeLists.txt` 确认源码归属 (AI 下多 AI 库并存: BattleAI/EmptyAI/MMAI/Nullkiller2/StupidAI)
  2. **运行时 → .so**: 看 train py `--xxx_ai` 参数推 lib<名>.so 加载链
- 同形不同源: NKAI/NK2/MMAI 三个词指三代 AI 库, 文档与任务登记中禁混用

### 开机恢复实录 (09-07 晚, #169 恢复序第三次)

- 关机前优雅 stop 存档 step=564079 → 开机 keepalive (wsl.exe sleep infinity 常驻) → restart_train_v5.sh → resume 564079 **零损失** (前两次中断均有回滚, 本次关机前主动 stop 的价值实证: 优雅停 = 零损失, 被动死 = 回滚)
- GUI battle-only 冒烟: 客户端未跑前 VCMI_Client_log.txt 为 8-29 旧会话 — 验证前先查日志 mtime 防验错文件

---

## Windows VCMI GUI 冒烟完整记录 (09-08)

### 环境总览

| 项目 | 值 |
|------|-----|
| fork 路径 | `D:\vcmi-fork-build\bin\VCMI_client.exe` |
| fork 版本 | 1.8.0.5078fe76 |
| fork 编译器 | WSL GCC 13.3.0 交叉编译 → Windows PE |
| Windows DLL 源 | MSYS2 mingw64 (gcc 16.x 主) |
| 官方 VCMI | `D:\Program Files\VCMI\` 1.7.5 MSVC |
| ModelAI.dll | `D:\vcmi-fork-build\bin\AI\ModelAI.dll` (GCC 16.2.0) |
| 数据目录 | `C:\Users\Administrator\Documents\My Games\vcmi\` |
| **隔离备份** | `C:\Users\Administrator\Documents\My Games\vcmi.bak\` (1862MB) |

### DLL 修复流程 (踩坑 #172)

```
Step 1: 备份 fork 特有文件 (非 msys64 自带)
  → VCMI_client.exe / VCMI_lib.dll / SDL2* / avcodec-63 / avformat-63 / avutil-61
  → swresample-7 / swscale-10 / libsquish.dll / lua51.dll / BattleAI.dll
  → 存 D:\vcmi-fork-build\_fork_originals\

Step 2: 清空 bin 所有 324 个 DLL
Step 3: robocopy C:\msys64\mingw64\bin\*.dll D:\vcmi-fork-build\bin\ /COPY:DAT /R:1 /W:1
Step 4: 还原 fork 特有文件
→ 最终 323 DLL, GCC 分布: 16.1→164 / 16.2→56 / 15.2→67 / 14.2→8
```

### fork GUI 功能层级 (修复后)

| 场景 | 结果 | 说明 |
|------|------|------|
| 启动 | ✅ main menu | 标题 `VCMI - Open Heroes 3 1.8.0` |
| N → 单人游戏 | ✅ lobby | 收到 LobbyUpdateState |
| lobby → 战斗模式 tab | ✅ | LobbySetBattleOnlyModeStartInfo |
| 选图 → 开始 | ✅ PlayerStartsTurn | `Server gives turn to red` |
| AI 首轮行动 | ❌ 崩 | `Attempt to read from 0x8` (NULL+8), 3 秒后触发 |
| headless + testmap | ❌ 崩 | `debugStartTest` 早期初始化路径 |

### ModelAI 加载链路验证 ✅

```
INFO - Player blue will be lead by ModelAI
INFO - Opening ModelAI
INFO - Loaded ModelAI
INFO - Player green will be lead by ModelAI
INFO - Opening ModelAI
INFO - Loaded ModelAI
```

**四要素全链贯通**: settings → aiNameForPlayer → getNewAI("ModelAI") → LoadLibrary → 导出 GetNewAI → 构造成功 → onnxruntime → bc_model_v3464b.onnx

### 崩溃根因分布

| 位置 | 条件 | 根因 |
|------|------|------|
| GUI 进 lobby 后 | DLL 24 种 GCC 混装 | STL ABI 内存损坏 → 已修复 |
| 游戏启动 AI 首轮 | DLL 统一后 | NULL+8 空指针 (StupidAI 也崩 → 非 ModelAI) |
| headless + testmap | 始终崩 | debugStartTest 初始化路径 (与 GUI 不同) |
| 官方 VCMI + ModelAI.dll | 官方 client + fork AI | MSVC vs GCC name mangling 不兼容 (踩坑 #173) |

### 08-29 能跑 68 场的条件对比

| 项目 | 08-29 当时 | 09-08 现在 |
|------|-----------|-----------|
| fork bin DLL | 应是干净的 (只复制必要 DLL) | 24 种 GCC 混装 (多次复制污染) |
| battle-only 入口 | GUI (VCMI_client.exe) | GUI 同 |
| ModelAI 加载 | 成功 (68 场) | 成功 ✅ (同一路径) |
| AI 首轮行动 | 没崩 | 崩 (需单独排查) |

### 后续行动建议

1. **AI 首轮 NULL+8 崩**: 看 fork 自定义 `ML/MLClient.cpp` init_vcmi 路径 vs GUI debugStartTest 是否差异; 用 Judgement Day (5KB 最小图) 排除图复杂度
2. **Windows 端跑 AI 冒烟**: fork GUI + DLL 已修, AI 加载 OK, 行动崩需独立 debug
3. **WSL fork 原生跑**: fork 源码 `ML/main.cpp` 是 Linux headless 入口, rel/ 目录下跑
4. **DLL 修复固化脚本**: 写 `py/fix_fork_dll.ps1` 自动执行 4 步

## v13 战斗 onnx 部署与推理验证 (09-08)

### 数据缺口定性 (推翻旧认知)

| 文件 | 实际身份 | 定性依据 |
|------|---------|---------|
| bc_model_v3464b.onnx | **战略模型** (3464 维输入) | metadata 无 version 键 → MMAI v13 factory `readVersion` 直接拒绝 |
| defender-ipnkyfqb-best3.onnx | 38 字节断链占位文本 | 非模型文件 |
| **defender-fqcbvmti-best7.onnx** | **有效 v13 战斗模型** (22.4MB) | 官方 vcmi-gym releases 成品 (v1.4), 推理验证 PASS |

- 本地重导出不可行: 战斗 checkpoint 缺失, export 管线无权重可用 → 数据缺口只能从官方渠道补
- **模型选型**: `fqcbvmti-best7` (v1.4) = 4 输入静态版, 匹配 fork C++; `tukbajrv` (v1.0) = 5 输入动态版 (nbr_flat/all_sizes) **弃用** — 与 C++ V13::NNModel 接口不符

### C++ V13::NNModel 接口 (源码实锤, 验证脚本据此构造)

- **4 输入**: `obs` float[28114] / `ei_flat` int64[2,sum_e] / `ea_flat` **float**[sum_e,1] (⚠ 不是 int64) / `lengths` int32[7]
- **6 输出**: `act0_probs`[4] / `hex1_probs`[4,165] / `hex2_probs`[165,165] + 3 masks
- `LT_COUNT = EI(V13::LinkType::_count)` = 7 (vcmi-native/AI/MMAI/BAI/v13/nn_model.cpp:30)

### 验证方法: onnxruntime 直推 (绕过 GUI 不确定性)

`py/verify_v13_inference.py` — WSL `/usr/bin/python3` 自带 onnxruntime 1.26.0, 零安装:

```bash
wsl bash -c "python3 /mnt/d/Bigdata/hero3_fresh/py/verify_v13_inference.py"
# 模型路径: ~/mmai-battle-test/config/MMAI/models/defender-fqcbvmti-best7.onnx
# PASS 判据: 6 输出 shape 全精确匹配 + act0_probs softmax 和=1.0
```

dummy 输入构造: `obs = randn(28114)*0.01 float32`, `ei_flat = zeros((2,0)) int64`, `ea_flat = zeros((0,1)) float32`, `lengths = zeros(7) int32` — 空 entity 表合法 (纯 obs 推理)。

### 部署位置 (battle-only 环境)

- 模型: `~/mmai-battle-test/config/MMAI/models/defender-fqcbvmti-best7.onnx`
- 引用: `~/mmai-battle-test/config/MMAI/CONFIG/mmai-settings.json` 四键 `models.attacker/.attacker.siege/.defender/.defender.siege` 全切此文件
- 已知妥协: side=1 时 defender 模型跑 attacker 键 (官方只有 defender 命名成品); 若运行报输入不匹配, 后备 v2.0 `attacker-pdpyqkrb-best7.onnx`

### GUI 全链路验证两次受挫教训 (为何改直推)

- run1 (timeout 180s): `Player red will be lead by MMAI` 正常 → 但 **MMAI 战斗模型加载时机 = red 自己开战时** (battleStart → BAI → 读 mmai-settings.json), Elbow Room 下 red AAI 避战 3 轮不撞怪 → 模型加载链路根本没被走到; timeout 杀进程后 core dump
- run2 (timeout 900s): 客户端 ~5min 在 NK2 tileRevealed/heroMoved 回调后自发 core dump (无 C++ 异常日志), red 仅 18 条 AAI 日志 — **与模型无关, 是客户端 GUI/NK2 层稳定性问题**
- 结论: 等 red 自主撞怪的 GUI 编排路线不可靠; **onnxruntime 直推是确定性的验证层** (接口契约级验证), GUI 全链路留待客户端修复后复验

## router bug 修复版 .so 停机窗口同步结案 (09-08)

- **同步内容**: MMAI router.cpp 资源路径 bug (assembleFromFiles 缺 `config/` 前缀 → mmai-settings.json 恒读空 → 恒 fallback) 修复版 libMMAI.so 从 `vcmi-native-build/rel/bin/AI/` 同步到训练目录
- **md5 链**: 修复版 `77840da2ae41151a4d532aac7039b4e2` ↔ 旧版 `3a28f494debc3c02497738100d560880` (Sep 3); **vtest/bin/AI/ 经 md5 确认同属旧版副本, 一并同步** — 现四副本一致 (构建树/训练目录/vtest/mmai-battle-test)
- **铁律流**: 旧版备份 `~/backup-so-sync-0908/libMMAI.so.pre-sync` → 优雅停 (journal: 08:17:53 Stopping → 08:17:56 Stopped; train_loop.log `Saved STATE_PATH (step=580111)`) → cp ×2 → `py/restart_train_v5.sh` (systemd-run) → `Loaded train state (step=580111)` 无缝 resume
- **踩坑 #168 二次复现**: stop 后 `systemctl start` 报 not found (transient unit 已收集消失); 且 **is-active 对已消失 unit 输出 `inactive` (exit 4) 不报错** — 停机确认要看 journalctl + `Saved STATE_PATH`, 勿信 is-active
- **训练影响**: 零 — 训练走 baggage 路径 (--blue_ai MMAI_RANDOM, Python 回调), 不触发 router 资源路径逻辑; 此修复只惠及 battle-only GUI 场景 (ModelAI/MMAI 独立读 mmai-settings.json)

---

## T06 capture 路径攻坚: 引导系统机理与激励包全链 (09-09)

### 引导系统机理 (本次逆向实锤, 修正历史认知)

- **五层目标优先级链** (ep_runner_one.py 引导块): 守卫 (15 格内恒优先, 守矿机制) > 矿 (obj_best, target_list type=1) > 回城取兵 (own_town_best, dist<=25 + recruit_mask) > 蓝城占城 (town_best, BFS 可达性过滤) > 资源堆 (best)
- **动作替换制 (核心机理)**: 引导块算出 move_target (tx 非 None) 即接管 — MOVE_TO 执行块把动作替换为方向动作 (优先 C++ next_dir `obs[3330+idx]` → 全图 BFS `bfs_full_dir` → 15×15 BFS → 贪心回退); **与 move_to_force 强制窗无关** — 强制窗只决定 a 的初值是 24 还是模型采样
- **MOVE_TO(24) = 中间语义**: 发送 24 → 执行块翻译为方向 → traj 记录方向 — act 序列永远无 24 (全历史 0 命中)。判定引导生效看 move_target 是否非 None, 不看 act (踩坑 #144)
- **卡死防护三件套** (城镇目标): BFS 不可达直接跳过 (不烧学费) / move_stall 6 步放弃 / town_blocked 本局禁用

### capture 激励包四件套 (全链落点)

| # | 内容 | 落点 | 语义 |
|---|------|------|------|
| 1 | TOWN_CAPTURE +100 奖励 | ep_runner L943-957 | owner 1→0 (真占领) 检测滞后 1 step (obs=上轮 nobs); 仅 T06 双图; 每城一次封顶 (logged 集合) |
| 2 | 旁路事件文件 | battle_quality_events.log | 主日志白名单改码需停训 → BHERO_KILL 同款旁路 (行带 map= 自含归属) |
| 3 | 蓝城引导直通 | ep_runner L655-656 | T06 绕过 town_best 的 mine_taken 门槛 (大图 target_list top-8 挤占 → [MINE]=0 → 门槛永假) |
| 4 | 守卫振荡黑名单 | ep_runner L331/L631-658/L912-914 | fail-count 贴脸计数 (dist<=2 每步 +1, 3 步未胜黑名单) + 梯度块联动排除 |

配套: T06 args 覆盖 (L126-132) move_to_force=200 + guard_done_steps=0 (15 步收局掐死引导 — **真死锁**; move_to_force 窗是伪死锁, 见踩坑 #144)

### 四轮死锁诊断史 (现象 → 根因 → 修复)

1. **capture 0 触发 (激励死信)** — 守卫奖能被发现是因守卫挡路; 蓝城 95 格外无引导信号模型永远发现不了 → 修 mine_taken 门槛
2. **门槛修复后仍 0** — guard_done=15 步收局, town_best 活 15 步走不到蓝城 → 修 guard_done=0 (200 truncation 兜底)
3. **200 步 truncation r=28** — 取兵震荡: [TOWN_VISIT]×4 (step 67/105/145/187, garrison 周期回满 → own_town 引导复活) 与蓝城引导打架 → 修 T06 取兵引导限次 2
4. **仍 r=30** — 守卫格振荡陷阱: hero (4,6)↔(5,7) 回跳 26/60 步 (traj_ep.json 位置序列实锤) → 修守卫黑名单 (v1 站上格失效 → v2 fail-count, 踩坑 #145)

### 验证数据 (r 递增 = 逐轮生效)

28.68 → 30.03 → 41.80 (v1 黑名单) → **93.95 (v2 fail-count, 46 步守卫胜快速闭环)** — 振荡解除, 引导奔蓝城

### 方法论沉淀

- **振荡定位法**: 解析 /tmp/traj_ep.json 的 hero 位置序列 (obs[3203] active hero → heroes 段 [128+idx*26+2/3] 的 x,y) — 回跳计数 (pos[i]==pos[i-2]) + 唯一位置数两指标, 10 分钟定位空间级振荡; act 序列逐字相同 = 确定性剧本
- **局耗时分型**: 主日志 time 字段差分 — 冻结型 (单步 >=300s, fuse 可兜) vs 慢性型 (全程 4-8s/步, fuse 雷达外, 踩坑 #147)
- **埋点甄别**: 差集检测类埋点看 live 槽形态 — 9/9 同一形态 = 埋点 bug 而非行为 (踩坑 #146)

### 遗留

- **T06 守卫战斗未触发** (引擎侧): 疑与 fix_t06_maps.py aggression=guard 补丁相关 — hero 站守卫格战斗不发生, 引导层黑名单绕行不影响 capture, 待专项
- **间歇性局级慢速** (踩坑 #147): 16% 局 4-8s/步, 根因未定位, 登记观察
- **撤梯子登记**: capture 触发率稳定后 move_to_force 200 → 常规窗 (200 全程 = 发现期模型自主性受限的必要代价)

---

## Windows GUI 死锁排查闭环 + 弹窗崩溃定性 (09-09)

### 死锁根因链 (minidump 终结证据)

```
现象: ModelAI GUI 复测, AI 行动后 ~2s 画面永久冻结 (主线程 + runNetwork 双双死等)

根因链:
  ModelAI heroMoved 回调 (网络线程)
    → 启动 detached 延迟线程调 endTurn
    → detached 线程生命周期失控, 持锁路径随线程退出失效
    → ENGINE->interfaceMutex 状态损坏 (永久失锁)
    → 全进程死等

minidump 判据: 锁 owner = 已死线程的 pthread 结构 (heap 中线程结构已 free)
```

### ModelAI 修复方案 (D:\vcmi_model_ai\model_ai.cpp)

| 路径 | 触发条件 | 处理 |
|------|---------|------|
| heroMoved | 移动完成, 无战斗 (battle_active=false) | 回调内同步 endTurn + in_my_turn=false |
| battleEnded | 战斗打完 (网络线程回调) | battle_active=false → 同步 endTurn + in_my_turn=false (防对方战斗的 battleEnded 误触发) |
| yourTurn | 正常回合开始 | 原有模式不变 |

关键语义: 同步 endTurn 非阻塞成立的前提 = `waitTillRealize=false` (与 yourTurn 回调模式一致)。**回调线程内禁开 detached 线程做续接动作** — 生命周期失控 = 锁资源泄漏定时炸弹 (踩坑 #148)。

### minidump 工具链 (py/ 五件套, 下次直接复用)

| 脚本 | 用途 | 关键点 |
|------|------|--------|
| take_dump.py | 活进程抓 full dump | ctypes 直调 MiniDumpWriteDump (MiniDumpWithFullMemory\|HandleData\|FullMemoryInfo); rundll32 路线不可靠 |
| walk_stuck_dump.py | 手动解析 Memory64ListStream | minidump 库对 full dump 支持差: type=9 流, n_ranges/base_rva/data_rva 三段式, 栈内存手动读 |
| identify_all_threads.py | 批量线程栈→函数归属 | .pdata 函数边界 (bisect) + 导出表, 无符号栈 RVA 落函数 |
| stuck4_cfbb.py | 单函数边界定位 | 疑似线程 start_routine (VCMI_lib+0xcfbb00 类) 的 .pdata 反查 |
| stuck4_heap.py | 堆/锁 owner 检查 | GAME 对象全局槽 (exe+0xa879b0 主线程 / exe+0x958920 网络) 指向对照 + owner 指针堆块上下文 |

排查流: 冻结现场抓 dump → 手解 Memory64List 读栈 → .pdata 归属函数 → 锁 owner 归属 (pthread 结构生死) → 定位持锁退出线程。

### 弹窗崩溃定性: 系统虚拟内存耗尽 (VCMI 无责)

时间线 (07:14-07:19, 2026-09-09):

```
07:14:46  Resource-Exhaustion 2004 — 3×python.exe 共 36GB commit (各 11.5-12.5GB)
07:18:52  pwsh.exe (.NET Runtime 内部错误)
07:18:53  GDEPService.exe (0xe06d7363)
07:18:55  agent-tool-host.exe (0xc0000409)
07:19:01  dwm.exe (dwmcore.dll 0xc00001ad) + LiveKernelEvent 141
07:46     cc1plus.exe RADAR_PRE_LEAK (编译链内存压力)
```

- **VCMI 排除证据**: 无 WER APPCRASH (Application Id 1000 无 VCMI_client 记录)、bin 目录无新 rpt/dmp (仅 09-08 旧档)、gui3 复测日志 endTurn after heroMoved 正常流转
- **模式识别**: 多个不相关进程短窗齐崩 + LiveKernelEvent = 资源耗尽/GPU 驱动指纹; dwm 崩 → 画面冻结, 伪装成"游戏卡死"
- **排查命令** (踩坑 #149): Application 1000/1001 (崩溃详情) + System Resource-Exhaustion-Detector 2004 (直接列元凶 PID 与字节数) + CommitUsed/Limit 对照
- 待用户确认: 3×python 来源 (进程已退); 干净环境 (5.6GB free / commit 23/55GB) 可安全复测

### 线程生命周期插桩 (09-10 重编后已生效 — 实战立功)

插桩点 (D:\Bigdata\hero3_fresh\vcmi\ 树, `[THREAD] xxx ENTER/EXIT tid=` stderr 打点; **09-10 重编落地, gui8-12 实战定位死锁链路功臣**):

| 文件 | 线程/函数 | 嫌疑背景 |
|------|----------|---------|
| client/CServerHandler.cpp | threadRunNetwork (runNetwork) | 网络线程, 回调来源 |
| client/ServerRunner.cpp | threadRunLocalServer (runServer) | 本地 server 线程 |
| server/CVCMIServer.cpp | progressTrackingThread | **短生命周期 detached 嫌疑** |
| client/Client.cpp | startPlayerBattleAction (unlockGuard 区间) | interfaceMutex 临时放锁窗口 |
| client/battle/BattleInterface.cpp | autofightingAI aiThread (detach) | **detached 嫌疑** |

⚠ ~~VCMI_client.exe 仍是 08-18 产物, 插桩未生效~~ → **09-10 三产物重编落地, 插桩已生效** (复发雷达, 常驻保留)。

### 09-10 GUI 死锁终局闭环: LoggingMutex 锁打点 → 两层根因 → 修复验证 (day=31)

**诊断方法论 (从 dump 静态分析到运行时打点的升级)**:

1. 官方 crashinfo.dmp (mini dump) 有 Exception 流 + MemoryList 但**无崩溃线程栈内存** → 只能定位崩点 RVA (exe+0x216556 类), 用 `.pdata` 函数边界 + Capstone 反汇编到指令级 (py/parse_crashinfo_mini.py / disasm_gui11_crash2.py)
2. **winpthreads Normal mutex (std::mutex) 不记录 owner** — dump 里锁结构 `{state=2(Waiting), type=0(Normal), event=0x1618, rec_lock, owner=0xffffffff}`: 0x1618 是 **auto-reset event 句柄不是 TID** (曾误判"持锁死线程"); owner 字段仅 Recursive/Errorcheck 记录 → **dump 静态分析定不出持锁者, 必须运行时打点**
3. **LoggingMutex 包装器** (client/GameEngine.h 嵌套类, 实现在 GameEngine.cpp): lock/unlock/try_lock 全打点 `[MUTEX] LOCKED/UNLOCK tid= ra=` — `ra=__builtin_return_address(0)` + .pdata 映射 = 锁点级定位; 实现放 .cpp 避免 windows.h 污染广包含头文件
4. 冻结时 stderr 末条 `LOCKED` 无配对 `UNLOCK` = 持锁者; `LOCKED` 与 `EXIT` 同线程相邻 = **该线程返回时泄漏锁**

**两层根因**:

| 层 | 机制 | 修复 |
|----|------|------|
| ① interfaceMutex 泄漏 | onPacketReceived 锁只覆盖 DISCONNECTING 检查, 包处理无锁运行; 回合切换 playerStartsTurn→waitWhileDialog (CPlayerInterface.cpp:1393) 的 makeUnlockGuard "解锁→等对话框→析构重锁" 无人配对 → **每次回合切换泄漏一锁** → runNetwork 下一包自死锁 + 主线程 USEREVENT 死等 | onPacketReceived 用 `optional<unique_lock>` 持锁覆盖整个 pack->visit, 恢复"包处理持锁"不变量 (makeUnlockGuard 配对成立) |
| ② SPECTATOR 空指针 | onlyai 观众接口 playerID=SPECTATOR(-4) 无 PlayerState → AdventureMapShortcuts::optionCanViewQuests (L647) `getPlayerState->quests.empty()` 空指针读 0x6d8 (崩溃时 rdx=0xfffffffc=-4=SPECTATOR) | 判空 (CPlayerInterface.cpp:1363 已有同类先例) |

**修复验证 (gui12, --testmap 全 AI 局)**: day=31 持续运行 (对标 09-08 headless 基准) / 62 次 INFER / 7 次 battleStarted + 1 次 battleFinished(winner=1) 战斗链闭合 / 零冻结零崩溃 / [MUTEX] 2.9 万次收支平衡 (差 -2 待观察)。heroMoved→endTurn 多轮闭环 = 09-09 ModelAI 修复验证通过。

**关键教训**:
- `makeUnlockGuard` 的隐含前提 = "调用者持锁" — 持锁不变量被上层破坏时 (锁作用域收窄), 下层 guard 的"恢复现场"变成"凭空加锁" — **锁作用域改动必须全链审查 makeUnlockGuard/makeUnlockSharedGuard 用户**
- 惰性初始化 winpthreads: `pthread_mutex_t` 本体是指针 (GENERIC_INITIALIZER=-1), 真结构体在堆上 {state,type,event,rec_lock,owner}
- 官方 crash handler 的 dmp 在对话框期间 0 字节, dismiss 后才落盘; mini dump 无栈内存, full dump (take_dump.py) 才有 — 但**冻结类问题 dump 抓晚了锁内存会被复用污染, 栈可信数据不可信**

**复测口径变更**: 新二进制 (09-10) 无 08-18 临时自动开局 hack → 用 `VCMI_client.exe --testmap Maps/Twins.h3m` 直开全 AI 局 (ModelAI×2 + 观众视角), bypass lobby 选图 UI; gui4/6 的 SelectionTab 崩溃 (lastMap 自动选图路径, 未修) 与此流程无关。观察标记: `[INFER] day=N act=X` (adventure AI) / `[BTL-AI]` (battle AI) / `[ML-battleStarted]` / `[ML-q] CGCreature::battleFinished winner=N` (战斗结算闭合) / "actGot false in applying 10MakeAction" = ModelAI 战斗出招偶发被拒 (09-08 已知非致命)。

**Windows 重编构建坑全集** (msys64 GCC 16.2 + Ninja, 详见踩坑 #156-#161): libFacade genex 泄漏 / serverapp 链接序 / facade VCMI_DLL=1+strategic_state.cpp / NK2 getDate 残留 / windows.h 宏污染 (IGNORE)。

### 09-10 第三崩溃立项闭环: 观众 SPECTATOR onTileLeftClicked 空指针 (判空修复 + 重编生效, 剩 GUI 浸泡复测)

**崩溃现场** (crashinfo.dmp 2026-09-10 18:13:24 版, gui12 浸泡 day=31 后): 主线程 TID=6028, `0xC0000005 读 0x10`, RIP=exe+0x20c09f (fn 0x20bf60, fn+0x13f), Rax=0 (null 返回值), **Rdx=R8=0xfffffffc=SPECTATOR(-4) 寄存器证据链**, 栈内存 0 bytes (mini dump 老规矩)。

**指令链译码** (py/disasm_gui12_crash3.py, 对齐扫描后精确命中崩点):

```
call 0x1a47c0            ; GAME->interface()
mov  rcx,[rax+0xd0]      ; ->localState (CPlayerInterface 字段偏移 0xd0)
call 0x1bd2b0            ; PlayerLocalState::getCurrentArmy() → 返回 null
cmp  [rax+0x10],0x22     ; ->ID != Obj::HERO(34)  ← 解引用 null 崩溃点
; 前文 cmp eax,0x22 / 0x62 = canSelect 计算的 Obj::HERO(34)/Obj::TOWN(98) 短路判断
```

**函数定位**: fn 0x20bf60 = AdventureMapInterface::onTileLeftClicked — 字符串四重锚定 ("adventure"/"showMovePath"/"gameTweaks"/"simpleObjectSelection"/"Nothing is selected..."), 函数边界 +0x20bf60..+0x20c748 (0x7e8, .pdata 提取)。

**根因链** (与第二崩溃同族 — 观众接口缺 SPECTATOR 防护, 同日双杀):

1. onlyai 观众 playerID=SPECTATOR(-4) 无 PlayerState, **永不轮到回合** → onPlayerTurnStarted 的 setSelection 三级 fallback (getCurrentHero→getOwnedTowns→getWanderingHero(0), AdventureMapInterface.cpp L446-456) 永不触发 → `PlayerLocalState::currentSelection` 恒 null
2. battleFinished 战斗结算后 UI 恢复冒险地图, 偶发输入事件触发 onTileLeftClicked → L548 `getCurrentArmy()->ID` 无判空解引用收割此雷
3. **官方防护不对称实锤**: onTileHovered L629 已有判空早退 (官方自己防护了 hover 却漏了 click); getCurrentArmy() 本身判空存在 (PlayerLocalState.cpp L154-160), 崩在调用方

**同族审计** (全客户端 `getCurrentArmy()->` 无判空 5 处): 仅 AdventureMapInterface.cpp L548 为真崩点; L693 (onTileHovered 内) 有 L629 防护安全; ClientCommandManager.cpp L506/507/511 三处为手动调试命令低风险不动。

**修复** (AdventureMapInterface.cpp L548 前): `getCurrentArmy()` 判空 return — **双覆盖**: ① 观战模式 ② 真人玩家英雄全灭 (removeWanderingHero→setSelection(nullptr), PlayerLocalState.cpp L241) 后点地图同雷。

**重编落地 (09-10 19:24, 停训窗核实后执行)**: 训练已 inactive (load 0.00) 天然窗口 → ninja 增量编译 6 步全绿 (仅 AdventureMapInterface.cpp + Version.cpp 重编 + 三链接, 未触 CMake regen 无 genex 泄漏) → VCMI_client.exe 19:24:16 版 (1.8.0.ec87c2826a, 17,988,193B) + VCMI_lib.dll 同步更新。headless 冒烟 PASS (`--headless --testmap Maps/Twins.h3m` 5 分钟: 5.2 万行日志主循环流转 / BattleEnded+MapObjectVisitQuery 战斗结算闭合 / stderr 零字节 / 无崩溃)。**剩 GUI 浸泡复测** (需用户在场): `--testmap Maps/Twins.h3m` 观众视角过战斗结算点 + 地图点击不再崩。

**方法论增量**: mini dump 无栈内存时反汇编窗口起点未对齐会出 `add byte ptr [rax-0x75], cl` 类伪影 — 对齐扫描 (枚举起始偏移找能精确命中崩点地址的解码路径) 后指令全部正确译码 (disasm_gui12_crash3.py 已内置)。

**⚠ 重编 PATH 坑 (09-10 新踩, cc1plus 静默死亡)**: 非 msys2 PATH 环境下 (PowerShell 直调 ninja) 编译全败 — c++.exe driver 正常 (`--version` OK) 但 spawn 的 **cc1plus.exe 0xC0000135 (STATUS_DLL_NOT_FOUND) 静默死亡, EXIT=1 全程零错误输出** (DLL 依赖 gmp/mpfr 等在 mingw64\bin, 靠 PATH 搜索; driver 自身静态无此依赖) — 极易误判为代码错误/资源耗尽。修复 = 编译前 `$env:PATH = "C:\msys64\mingw64\bin;C:\msys64\usr\bin;" + $env:PATH`; 诊断技巧 = 直接跑 `cc1plus.exe --version`, exit code **3221225781** 即 DLL_NOT_FOUND 实锤。

### GUI 复测环境规范 (复测前 checklist)

1. 界面语言 English; 输入法已程序化屏蔽 (09-10 ImmDisableIME 编入客户端, 不再需要手动切 ENG — 踩坑 #151 闭环)
2. settings ai.adventureAlliedAI/adventureEnemyAI = "ModelAI" (踩坑 #152, 被清空过一次)
3. 确认无大内存任务并行 (WSL 训练停机 / 无编译 / 无异常 python) — 踩坑 #149
4. 启动方式带 stderr 重定向 (gui*_stdout.log/gui*_stderr.log, 崩溃现场有最后日志)
5. 冻结时别关进程 — take_dump.py 抓现场 dump; **并立刻抓 stderr 末条 [MUTEX] (LoggingMutex 打点已常驻)**
6. AI 全自动复测口径: `--testmap Maps/Twins.h3m` (人肉点击 lobby 路径有 SelectionTab 未修崩溃, 见遗留待办)

### 遗留待办

- ~~用户确认 3×python 来源 (07:14 资源耗尽元凶)~~ / ~~干净环境 GUI 复测 (死锁修复 + battleEnded 验证)~~ / ~~插桩版客户端重编~~ — **09-10 全部闭环** (详见上章)
- v13 战斗模型 Windows 侧适配评估 (MODELAI_MODEL 指向 v13 需核实 model_infer.cpp 接口, 4 输入接口契约见上章)
- gui4/6 SelectionTab 崩溃未修 (lastMap 自动选图路径, --testmap 口径下无关)
- [MUTEX] 差值 -2 观察项 (个别 makeUnlockGuard 未持锁上下文调用)
- ~~**第三崩溃待立项 (09-10 gui12 浸泡 day=31 后)**: 主线程 `0xC0000005 读 0x10`, RIP=exe+0x20c09f...~~ — **09-10 立项当日全闭环** (崩点=onTileLeftClicked L548 getCurrentArmy() 空指针, 判空修复源码落地 + 19:24 重编生效 + headless 冒烟 PASS, 详见上章); 唯一遗留 = **GUI 浸泡复测** (需用户在场, 观众过战斗结算点 + 地图点击不再崩)

---

## VCMI 对象坐标体系: anchor↔visitable 双坐标系 (09-10, [GUARD]/[MINE] 假糖根因章)

### 语义链 (源码实锤, 修 [GUARD]/[MINE] 假糖+漏奖的理论基础)

1. **vmap objects.json 的 x,y = `setAnchorPos` = 引擎 `CGObjectInstance::pos`** (MapFormatJson.cpp L1175-1209: `pos.x=configuration["x"]; instance->setAnchorPos(pos)`)
2. **mask 字符语义** (ObjectTemplate.cpp L245-249):
   - `'V'` = VISIBLE (可通行不阻挡)
   - `'B'` = VISIBLE|BLOCKED
   - `'A'` = VISIBLE|BLOCKED|VISITABLE (**对象本体格**)
   - `'T'` = BLOCKED|VISITABLE
3. **visitable 格 = pos − getVisitableOffset()**; calculateVisitableOffset 扫 mask (y 外 x 内) 找第一个 isVisitableAt 格的 (x,y) 即 offset
4. monster/hero 标准 mask: monster 3×3 `["VVV","VAV","VVV"]` → A 中心 → **offset(1,1), 真怪位 = anchor−(1,1)**; hero 3×2 `["VVV","VAV"]` → offset(1,1), 但 CGHeroInstance::pos 特殊 (英雄 obs pos = anchor 直报, 诊断局 hero=(3,3)=anchor 零差) — **hero 判据用 anchor 口径与 obs 自洽, monster/mine 判据必须用 visitable 口径**
5. **行为推论**: hero 走上怪 visitable 格 = visit + 战斗 (autofight 秒胜后站该格); hero 站 anchor 格 = 与怪贴脸但不 visit (anchor 是 V 格 passable) → 无战斗

### 对 Python 侧的约束 (ep_runner)

- `get_guards`/`get_objectives` (mines) 必须换算 visitable 口径 — `_anchor_to_visitable()` 复刻 C++ 算法
- `towns` 保持 anchor 口径: obs towns pos = 引擎 anchor 直报, 两侧同语义 ([TOWN] dist<=1 历史自洽 241 次匹配)
- **混用禁忌**: 同一比较式两端必须同坐标系 (Python 静态表 vs obs 直报 vs C++ target_list 各有口径)
- 事件奖励检测优先 obs 直报字段 (owner 变化/对象消失 = TOWN_CAPTURE 同款), 位置重合是最后手段

### 影响面与验证

- 失真期数据: [GUARD] 1442 条 (全 T05 时期) / T04 占矿 92% 口径 / T05-T06 r 高分构成 — 全部需按"挤水分"重读
- 诊断工具: py/diag_obj_dump.py (引擎 hero/towns 实位, 单图 2s) / py/analyze_36X36_02*.py (布局+地形 ASCII)
- 新口径首命中: duel (4,6) ×2 局 / 52X52_02_mir (38,39) 均为 vis 位 (与 [EP_TIME] map 字段互证)
- 遗留专项: T06 守卫战斗触发时有时无 (ep_418 真发生 vs 0909 振荡局未触发, aggression 补丁相关)

---

## 0910 停训窗工程记录 (三树/审计/设计稿)

### NK2 三树分叉合并 (a1ea3f4d2d 结案)

- **libMMAI.so 无需重编二次实锤**: race 在 NK2 域, 训练栈 --blue_ai MMAI_RANDOM 不加载 NK2 (MMAI/ grep 0 命中 + 运行时 so 无 NK2 符号)
- **双向分叉**: 构建树独有 TBB 防 OOM fix (`max_allowed_parallelism=4`, C8.5) / 源码树独有 a1ea3f4d2d+[ML-*] 打点+battleEnded/ring6 fix → 任一侧重编都丢对方修复
- **合并**: TBB fix 摘回源码树 (构造函数开头 3 行, tab 缩进) + cp 构建树 (diff IDENTICAL); Windows vcmi/ 树精确插入 TBB 3 行
- **Windows 树 API 级分叉不可镜像**: getCalendar()/showGarrisonDialog MetaString 新签名 = 09-09 NK2 编译修复, 各树匹配各自引擎版本; 同步只做 fix 级摘取 (TBB 这类引擎无关补丁)
- 三树双标记验证: a1ea3f4d2d=2 / max_allowed_parallelism=1 全绿; NK2 运行时 so 未重编 (无消费者, 回用时重编即生效)

### R5 双树审计方法论 (py/audit_r5_trees.sh + audit_r5_filter.sh)

- diff --strip-trailing-cr 必加 (CRLF/LF 噪音); 关键词过滤 (ML-/ENGINE/打点/fix) 区分功能性差异 vs 版本演进噪音
- 审计结论: 四文件中唯一功能性缺口 = ServerPlugin HeroPool 放宽 (已同步 b1685966d1); CGameHandler/CServerHandler/Client 差异 = GUI 栈 (ENGINE null 保护+[THREAD] 插桩) vs headless 栈 (升级自动选技能+quick_exit) 各自适配, **强行对齐反破坏构建**
- ServerPlugin 退出语义差异 (std::exit vs quick_exit+VCMI_APPLE 分支) 同为各树适配

### 工程注意 (踩坑 #154-#157 详)

- PowerShell 包裹 wsl bash: $var 被吃 → 复杂逻辑写 py/ 脚本文件; pkill -f 自杀陷阱; import ep_runner_one 有副作用; hermes 日志覆盖丢样本 → [EP_TIME] 进主日志白名单

---

## Windows GUI 观众模式崩溃系列闭环 (09-09/10)

> 观众视角 (SPECTATOR/-4) 引入后连续暴露五个崩溃点，全部修复 + soak_gui15 浸泡复测 PASS (用户全流程确认：战斗结算/层切换/系统菜单/KingdomOverview 直接点击，stderr 93617 行零 THREW/零 Disaster)。

### 五崩清单与修复落点

| # | 崩溃点 | 根因 | 修复 | 验证 |
|---|--------|------|------|------|
| 一/二 | (前窗已闭环) | — | — | — |
| 第三崩① | 回合切换后整体冻结 | interfaceMutex 泄漏: onPacketReceived scoped_lock 只盖 DISCONNECTING 检查, pack->visit 无锁运行 → waitWhileDialog 的 makeUnlockGuard "析构重锁" 凭空加锁无人解锁 (踩坑 #158) | onPacketReceived 改 `optional<unique_lock>` 持锁覆盖整个包处理 | [MUTEX] 收支对账 + day=31 |
| 第三崩② | day=2 崩 0xC0000005 读 0x6d8 | SPECTATOR 无 PlayerState, optionCanViewQuests (L647) 空指针解引用 (踩坑 #159) | getPlayerState 判空 (CPlayerInterface.cpp:1363 先例) | day=31 |
| 第四崩 | 点 kingdom overview 弹窗崩 (0xC0000409 进程退出) | AdventureMapShortcuts::showOverview (L134) → CKingdomInterface L765 howManyHeroes → lib 域 throw, 观众无玩家数据 | showOverview() 加 spectator 守卫 (client 域, lib 只读) | soak_gui15 直接点击 PASS |
| 第五崩 | 点系统菜单 1.1s 后双线程 "Disaster happened" + 僵尸进程 | runServer/runNetwork 线程边界无 catch-all, 未捕获 C++ 异常 (0x20474343) 直通 SEH filter (踩坑 #165) | 两线程 catch std::exception + catch(...) 双路日志 ([THREAD] THREW 标记) | soak_gui15 零 THREW/零 Disaster |

### 第五崩取证方法论 (复发时直接复用)

- **"Disaster happened" 语义分流**: 日志行后**无 Reason** = SEH filter 路径 (onUnhandledException, CConsoleHandler.cpp L119, SetUnhandledExceptionFilter 注册于 L284); **有 Reason** = onTerminate 路径 (L146)。无 Reason 时别在日志里找异常文本 — 根本不打
- **minidump 手工解析** (`py/parse_crash_dmp.py`): header "MDMP" → stream 目录; type 6 = ExceptionStream (ThreadId@+0, Code@+8, Address@+24, nparams@+32, params@+40); type 4 = ModuleListStream (MINIDUMP_MODULE 108 字节); ASLR 换算 `runtimeVA − runtimeBase + PE_ImageBase` = addr2line 地址
- **异常码速查**: 0x20474343 = GCC C++ 未捕获异常 (非 AV, 不用怀疑野指针); 0xC0000005 = AV 解引用; 0xC0000409 = fail-fast/stack buffer; 0xC0000135 = DLL 缺失 (编译环境, 踩坑 #164)
- **默认 dmp 只 21.7MB** (MiniDumpWithDataSegs) — 堆上异常对象文本取不到; 要堆内容需 settings `general.extraDump=true` 开 FullMemory; 僵尸进程成因 = 两线程并发触发 filter 疑似 MiniDumpWriteDump 挂起
- **僵尸 vs 崩溃退出判别**: 进程存活但窗口无响应游戏逻辑死 = 线程死于 SEH filter (GUI 泵还活); 进程直接退 = MainGUI 线程死。两种模式根因域不同

### 观众模式良性刷屏判据 (勿误判崩溃前奏)

- `getPlayerStatus "No such player!"` 持续刷屏 (20-30ms 间隔) = 观战/敌回合状态轮询, 良性
- `getResource "No player info!"` ×7 = 层切换 (地表/地底) 后资源栏刷新, 良性
- 真崩溃信号 = "Disaster happened" / "THREW:" / WER APPCRASH 事件; 复测 checklist 仍以知识库既有条目为准 (英文界面 + ENG 输入法 + settings AI 双配 + stderr 重定向)

### 遗留观察项 (非阻塞)

- 第五崩原始 throw 点未知 (dmp 只能拿到异常码) — 已 instrumented, 复发时 [THREAD] THREW 直接给 e.what() 且不再僵尸化
- "Attack cannot be performed" 服务器拒绝; [MUTEX] 差值残留; gui4/6 SelectionTab 未修
- GUI 栈与 headless 栈源码分叉为各树适配 (R5 双树审计结论), 强行对齐会破坏构建

---

## VCMI 网络协议与外挂 AI 架构调研 (09-11, GitHub 深度分析)

**触发**: 调研 xsa-dev/homm3env + Issue #5586 + VCMI 网络层源码，探索"模型外挂"可行性。

### 核心发现

1. **VCMI develop 所有 AI 都是进程内直接回调 (CCallback)** — EmptyAI 的 `yourTurn` 只做 `cb->selectionMade(0); cb->endTurn()`，编译为 OBJECT 库链接进 server，完全不经过网络层。`AIFactory.h` 证实：所有 AI (BattleAI/Nullkiller2/MMAI/StupidAI/EmptyAI) 通过 `createAdventureAI(name)` / `createBattleAI(name)` 静态构造，无动态加载。

2. **VCMI 网络层是完整的命令服务器** — `lib/network/` 有 `NetworkServer`(TCP server) + `NetworkConnection`(client 连接) + `NetworkHandler`(包分发) + `NetworkDiscovery`(UDP 广播)。客户端发 `CPackForServer` 包，server 处理后发 `CPackForClient` 包。**Server 对客户端一视同仁**，不区分人类 vs AI。

3. **`PacksForServer.h` 已定义所有战略层操作** (二进制序列化协议，非 JSON)：
   - `MoveHero(path, layer, hid, transit)` — 移动英雄
   - `EndTurn()` — 结束回合
   - `RecruitCreatures(tid, dst, crid, amount, level)` — 招募
   - `BuildStructure(tid, bid)` / `RazeStructure` — 建造/拆除
   - `UpgradeCreature(pos, id, cid)` — 升级兵种
   - `HireHero(hid, tid, nhid)` / `DismissHero(hid)` — 雇佣/解散
   - `SpellResearch(tid, spellAtSlot, accepted)` — 研究法术
   - `SetFormation(hid, formation)` / `SetTactics(hid, enabled)` — 阵型/战术
   - `CastAdvSpell(hid, sid, pos)` — 战略法术
   - `MakeAction(BattleAction, battleID)` — 战斗行动 (BattleAction = MMAI 内部同结构体)
   - `QueryReply(qid, reply)` — 回复查询
   - `TradeOnMarketplace(...)` / `ExchangeArtifacts(...)` / `BuyArtifact(...)` — 经济
   - `BulkMoveArmy/BulkSplitStack/BulkMergeStacks` — 批量部队操作
   - `BuildBoat(objid)` / `SaveGame(fname)` / `SetObjectProperty(...)` — 杂项

4. **`PacksForClient.h` 客户端收到的包**:
   - `NewTurn(day, heroesMovement, heroesMana, availableCreatures, playerIncome, ...)` — 回合开始
   - `TryMoveHero(id, result, start, end, movePoints, fowRevealed, attackedFrom)` — 移动结果
   - `PackageApplied(player, requestID, packType, result)` — 执行结果
   - `PlayerStartsTurn(queryID, player)` — Query 类型，需回复
   - `HeroLevelUp/CommanderLevelUp/BlockingDialog/GarrisonDialog` — 均为 Query，必须回复 `QueryReply`

5. **`features/battle-ml` 分支是死分支** — 最后提交 2022-07-19，作者 nullkiller，从未合并。xsa-dev/homm3env 基于此分支，其 JSON over TCP 协议是私有协议，当前 develop 无对应 server 端代码。

6. **Issue #5586 (LLM Learning Game Integration) 是纯提案** — 创建者 VCMIchatbot，4 条评论无人接活。提案的"TCP 命令服务器 + JSON 序列化"其实 VCMI 已经有了，只是格式是二进制不是 JSON。

### 外挂 AI 架构

```
VCMI Server (不改代码)
  ├─ 人类客户端 (vcmiclient) ← TCP
  └─ 外部 AI (自定义客户端) ← TCP ← 模型
```

- 外挂 AI 实现 `NetworkConnection` 协议 + `CPackForServer` 序列化
- Server 不区分人类 vs AI
- `MakeAction` 里的 `BattleAction` 与 MMAI 内部同结构体 — 战斗层和战略层共用协议
- 所有 `Query` 类型必须回复 `QueryReply`，否则 server 卡住

### 外挂路径评估

| 路径 | 难度 | 说明 |
|------|------|------|
| A. 逆向二进制序列化 | 高 | 读 `Serializeable.h` + `NetworkHandler.cpp` 推字节布局 |
| B. C++ 写 VCMI headless client | 中 | 用 VCMI 头文件，类似 EmptyAI 但走网络 |
| C. 给 VCMI 加 JSON 包装层 | 中 | 改官方代码，维护成本高 |
| D. Python 实现序列化 | 高 | struct + 变长字段处理 |

**结论**: 外挂方案对终极目标 (人 vs 人 vs 模型联网) 是更好的架构，但序列化逆向是当前瓶颈。短期继续 .so 直连，长期可探索路径 B (C++ headless client)。

### 参考项目评估

| 项目 | 价值 | 说明 |
|------|------|------|
| xsa-dev/homm3env | 低 | 2021 SOC 比赛骨架，RL 环境全是 stub，JSON 协议是死分支私有协议 |
| vcmi-gym (smanolloff) | 高 | MMAI 官方训练栈，PPO-DNA + GNN + ONNX，架构可参考 |
| CleanRL (vwxyzjn) | 中 | PPO 单文件实现，超参对照参考 |
| Issue #5586 | 低 | 纯提案，无人实施 |
| agentic-factorio-ai | 中 | LLM+RL 分层架构范式参考 |

---

## C4 #7632 NK2 寻路加速 merge 执行记录 (09-10/11, 停训窗大改)

**任务**: 官方 PR #7632 (starius/optimize, NK2 寻路加速 benchmark +40%) cherry-pick 到训练栈。动 libvcmi.so 训练期禁 → 0910 停训窗执行。用户明示"大改，需要备份 + 完整验证"。

### 总体流程 (已收官)

1. **备份** (c4-2): `~/so_backup_0910_7632/` (libvcmi.so.bak_0910 336MB + libMMAI.so)
2. **cherry-pick** (c4-3): workspace 树 (~/vcmi-workspace/vcmi, 唯一真源) 落 `e28ca31af5` "Merge pull request #7632 from starius/optimize"
3. **lib 侧增量**: ISpellMechanics.h 接口尾追加 getCastsLimit/getCastsAlreadyPerformed 纯虚 + adventure 4 文件 + pathfinder 13 文件 + EntityIdentifiers 628b^ 特制版 (防 Services 蔓延) → libvcmi.so 02:18 编过
4. **NK2 适配 4 轮迭代** (c4-4b): ObjectClusterizer .h/.cpp 错配 → CSpell.h include → ArmyManager/BuildAnalyzer Calendar 断层 → 全部收口，libNullkiller2.so 02:42 编过
5. **全量 build** (32 min): 四件套 libvcmi/libNullkiller2/libMMAI/vcmiserver + 全绿，仅 mlclient-cli 挂 (MMAI::ASSERT 宏 bug, 08-01 遗留, 见踩坑 #178) → 修复后 `[100%] Built target mlclient-cli`
6. **静态验证** (c4-6): 符号导出 ✓ / ldd 解析 ✓ / StrategicEnv 冒烟 ✓
7. **git 三笔提交**: native `1c580aee3`(基础层 37 文件) + `0a44db3b9`(NK2 适配 58 文件, 含 EscapeBehavior 入库) / workspace `825a40b8e7`(ASSERT 修复 3 文件, 位于 e28ca31af5 之上)

### 双 worktree 甄别铁律 (37 DIFF 文件一次配平方法论)

vcmi-native 与 workspace 共享 .git 但 **HEAD 不同** (native=e4afa2a87 旧基线 / workspace=e28ca31af5)：
- 对 native NK2 文件取 `git status` M 状态 × 与 workspace 工作树 diff 组合判定
- **非 M + DIFF_WS** = 纯 commit 差异 (native 侧从未手改) → cp workspace 版安全 (28 文件一次配平)
- **M + DIFF_WS** = 训练手改或本会话 patch → 保留不动
- **例外**: AIGateway.h/.cpp 对配套保持旧版 (与手改保留的 AIGateway.cpp 匹配, 防新 API 断层蔓延)

### API 新旧映射表 (#7632 涉及)

| 新 API (workspace) | 旧等价 (native) | 依据 |
|---|---|---|
| `reset.weeks/days/months` 复合判断 | `reset.period == 7` | Configuration.h L57 旧 ResetInfo 单字段 period |
| `getCalendar().getCurrentDay()` | `getDate(Date::DAY)` | CGameState.cpp L126: DAY=绝对天数 |
| `getCalendar().getDayOfWeek()` | `getDate(Date::DAY_OF_WEEK)` | DAY_OF_WEEK=周几 1-7, daysPerWeek 恒 7 |
| `getCalendar().getDaysInWeek()` | 字面量 7 | engineSettings 恒 7 |
| `lib/spells/CSpell.h` (8eb0 拆分) | `lib/spells/CSpellHandler.h` | native 侧 CSpell.h 是已删除的未跟踪半新文件 |

改写落点 6 处: AIUtility (ResetInfo) / HeroManager / PriorityEvaluator ×2 / DefenceBehavior / ArmyManager / BuildAnalyzer。

### 训练运行时真身架构实锤 (c4-5 事实核查)

- **训练不启动独立 vcmiserver 进程**: `MLClient.cpp start_vcmi()` 走 `GAME->server().debugStartTest(mapname)` = libmlclient 内嵌 server 进程内线程
- Python 侧全硬编码 `/home/administrator/vcmi-native/rel/bin` (LD_LIBRARY_PATH + STRATEGIC_STATE_LIB)
- connector_v13.so (08-17) 在进程内线程调用 libmlclient, 不动
- **结论**: 副本三目录 (vcmi-native-build/vtest/hero3_vcmi/build) 不在训练链路, 不同步防污染 (踩坑 #183)

### 动态观察 (首窗纪律: 只观察吞吐与稳定性, 0911 03:5x 起)

- resume 精准对齐 step=621725 (0910 优雅停训点), 5 局全部 err=no 零崩溃
- r 基线不劣化: 52X52_mir 新 166.6/161.8 vs 旧均值 ~160
- **吞吐未兑现 +40%**: T05_52X52_mir 旧 97s×6 → 新 112s×2 (+15% 慢); T06 duel 4.96s/步 在旧区间内但样本不足 (踩坑 #184, 观察中)
- 回滚路径: so_backup_0910_7632 + `git revert` 两仓

### 遗留

- T06 duel 攒 3-4 局稳态样本后拍板: 有收益保留 / 无收益且 T05 持续慢 → 评估回滚
- libNullkiller2.so 无旧版备份 (git 源码可回退重编, 风险可接受)

## T13 外挂 AI 协议客户端与 Lobby 包 (09-11, P8 前置)

### 范围

- 目标: 外部 AI 不改 VCMI 代码, 用 VCMI 官方 TCP/CPack 协议作为客户端接入, 服务 1V7 多人对战 P8。
- 代码入口: `py/vcmi_protocol/`。
  - `serialization.py`: LVarInt / string dedup / set / pointer-present / pointer 占位读取。
  - `packs.py`: 战略包、客户端包、战斗包、Lobby 包。
  - `protocol.py`: `VCMIProtocolClient` + `QueryManager`。
  - `model_bridge.py`: obs(3464) → action(0-24) → 协议包。
  - `tests/test_e2e.py`: P8-A 实机入口 + 离线单测。
- 提交: `bdce29a` (`t13.10: lobby protocol and p8 harness`)。

### Lobby 包要点

| typeID | 包 | 用途 | 状态 |
|---:|---|---|---|
| 216 | `LobbyClientConnected` | server 通知客户端已连接 / 大厅参与者基础信息 | 可解析, 待实机校验 |
| 217 | `LobbyClientDisconnected` | 客户端断开 | 可解析, 待实机校验 |
| 218 | `LobbyChatMessage` | 大厅聊天 | 可解析, 待实机校验 |
| 226 | `LobbyUpdateState` | 大厅状态更新 | 可解析主路径, `CMapInfo` 字段暂占位 |
| 229 | `LobbySetMap` | 设置地图 | 实机 PASS (方案F, 1486B 完整 CMapInfo 由 guest client1 发送, server 接受) |
| 265 | `LobbyQueryState` | 查询大厅状态 | 无字段, 可发送 |
| 266 | `LobbyModsCheck` | 大厅兼容检查响应 | 可解析, 待实机校验 |

### 实机 P8 入口

```bash
python py/vcmi_protocol/tests/test_e2e.py --p8-1v7 --map Maps/Twins.h3m
```

实机判据:
1. TCP 连 VCMI server 成功。
2. 收到 `LobbyClientConnected` 或 `LobbyUpdateState`。
3. AI 回合收到 `PlayerStartsTurn`。
4. AI 发送 `EndTurn` 后收到 `PackageApplied`。
5. 混人+混 AI 完成至少 1 局无崩溃。

### 验证

离线验证已完成: `python py/vcmi_protocol/tests/test_e2e.py` → `144 passed, 0 failed`。
实机多人局尚未完成; 当前只完成 P8-A 入口脚本和 Lobby 协议前置, 不伪造对战结果。

### GitHub 外部项目调研 (09-11): P8 联机 + P10 转换器可用资源

#### 一、直接服务 P8/T13.10 多人联机 (高价值)

| 项目/资源 | 地址 | 价值 | 利用方式 |
|---|---|---|---|
| vcmi/proxy-server | github.com/vcmi/proxy-server | 官方联机代理 (Python), 含完整 lobby 协议文本 (login/rooms/ready/START 等) | P8-D 跨机器部署直接参考其协议章节; 人vs人vs模型联网的中转环节 |
| vcmiclient CLI 多人参数 (官方 manpage) | manpages.ubuntu.com manpage vcmiclient | 无 UI 直开多人局 | 见下方 P8-B/C CLI 方案 — P8-B/C 实机验证核心 |
| vcmi PR #4253 | github.com/vcmi/vcmi/pull/4253 | `settings["server"]["localPort"]=0` 随机端口绑定 | 并行多实例 VCMI 不抢端口; P8 并行验证/未来多人训练用 |
| 官方 Networking.md | vcmi/vcmi develop docs | 4 字节长度+payload 与 global lobby JSON 协议权威文档 | 与我们逆向的序列化规格互证, 可作 `docs/序列化协议规格.md` 官方佐证链接 |

**P8-B 实机验证方案 (09-11, 方案F 已验证 PASS, commit 407e8e5)**:

fork 1.8 无 `--loadserver/--loadplayer` 参数 (官方 develop 才有)。已验证开法:

```bash
# 1. 独立启动 server
VCMI_server.exe --port=3030

# 2. Python 先连当 host → 发 LobbyClientConnected(216)
python py/p8/p8be_host_start.py   # 自动完成后续全流程

# 3. 真实 client1 连入当 guest (脚本内自动启动):
VCMI_client.exe --testmap Maps/Twins.h3m --donotstartserver --serverport 3030 --headless
# (环境变量 VCMI_TESTMAP_ONLYAI=1)

# 4. Python(host) 发 LobbyChangeHost(225) 让 host 给 client1
# 5. client1 成为 host → 发 LobbySetMap(229) → LobbyStartGame(224)
# 6. GAMEPLAY: Python 发 EndTurn(180) → server "successfully applied" → ModelAI 对手移动 → Turn 2
```

要点:
- SetMap 是 host-only 操作; guest 发被静默拒绝 → 必须先 ChangeHost 让位
- **ChangeHost 时序 (踩坑 #202)**: 必须等目标 guest 已连入 (第 2 个 UpdateState) 再发; 对不存在的 cid 发 → server 静默拒绝 + guest 侧 SetMap 全拒 → 开局永卡。`p8be_host_start.py` L114-129 是正确时序范本。
- LobbyChangeHost(225) 手工帧: `bytes([0, 0, 0xe1, 0x01, 0x02])` (isNull+pid+tid+newHost=2)
- EndTurn(180) 帧: `isNull(0)+pid(0)+tid(180)+player(LVarInt 0)+requestID(LVarInt)`
- **PlayerStartsTurn(88) 帧 = `00 00 d800 41 00`** (isNull+pid+tid=88+queryID(-1=0x41)+player); 只在 `player==MY_COLOR` 时发 EndTurn, 对方回合 SKIP (踩坑 #200)
- 实机 PASS: 连续两回合 EndTurn "successfully applied" + ModelAI TryMoveHero + Turn 2 轮转 + server zero fishy/not-allowed

**P8-B 阶段3 (P8-C) 数据源墙 (09-11, 捕获分析, 踩坑 #203)**:

Python 外挂要发真实 MoveHero 需要 `hid`(英雄 OI) + 起始坐标。实锤发现:
- 英雄 OI+位置**只在** `LobbyStartGame(224)` 的 171KB 全状态里 (`LobbyStartGame = StartInfo + CGameState`); 之后回合窗口 server 不单独广播 GiveHero/ChangeObjPos 位置包
- `MoveHero.hid` = 引擎运行时 ObjectInstanceID, ≠ h3m 静态 heroID → P10 h3mtxt 静态 JSON 拿不到, 走不通
- server 日志只在英雄实际移动时打 "OI xxx start (x y z)", 挂机玩家无记录

三条路线 (待决策):
| 路线 | 内容 | 工程 | 收益 |
|---|---|---|---|
| 阶段4 最小 CGameState 解析器 | Python 只挖到 `CMap.heroesOnMap` + hero OI 为止, 逐字段断言校验 (width=36/day=1) | 中 | 完整 MoveHero 闭环 |
| 阶段5 降级最小闭环 | 先做 QueryReply(197)+RecruitCreatures(187) 真实决策 (城镇 OI 从 SetAvailableCreatures 拿, 不依赖地图状态), MoveHero 留后 | 小 | 战略动作 2/3 打通 |
| 阶段6 C++ headless client | 路径A 直接复用 VCMI 序列化代码 | 大 | 零逆向风险 |

离线分析入口: `python py/p8/p8c_capture_hero.py` (dump 171KB → `%LOCALAPPDATA%\Temp\p8c_startgame.bin`)。

**P8-C 首步 MoveHero 闭环 PASS (0911 晚, 踩坑 #206, 路线拍板 = SRV-DIAG 破数据源墙)**:

实际落地不走三条路线中的任何一条 171KB 解析 — **在 server 侧注入诊断行, Python 外挂读日志拿运行时状态**:
- server `CGameHandler::start` (`!resume` 分支) 注入 `[SRV-DIAG] HERO OI=.. owner=.. pos=(x y z)` 逐英雄 dump (vcmi commit bc3e124fa2); Python tail server 日志解析 → 运行时 OI 零逆向到手 (red OI=350 / blue OI=732, Twins 图实测)
- pos 口径 = `anchorPos()` (MoveHero path 用锚点坐标, 每步须与当前位置 8 邻域相邻; heroes 1x1 anchor==visitable)
- **踩坑 #206: TryMoveHero(109) 字段序 = id + result + start(int3) + end(int3) + movePoints + fowRevealed(vector) + attackedFrom**, 不是直觉的 id+start+end+result — 字段序读错会把 SUCCESS 解析成 FAILED (离线 test_e2e 两侧同错自洽通过, 实机对拍才抓出, 与 #199 同型)
- 实机验证: red (1,8,0)→(2,7,0) 实移 (后续同格 = day1 MP 耗尽非拒绝) + blue ModelAI (16,1,1)→(15,0,1) 自主移动 + 三回合轮转 + `PackageApplied(MoveHero)=True` + zero fishy/not-allowed
- 脚本: `py/p8/p8c_movehero_probe.py` (方案F流程 + 日志 OI 解析 + 决策-移动-结束回合全链)

- 剩余: 阶段3 扩展 RecruitCreatures(187)/QueryReply(197)/BuildStructure(185) (包栈已在, 缺游戏状态感知: 可招兵信息从 SetAvailableCreatures(100) 广播拿) → P8-C 混人回合 → P8-D 跨机器

#### 二、服务 P10 h3m2vmap 转换器 (中高价值)

| 项目 | 地址 | 价值 | 利用方式 |
|---|---|---|---|
| h3mtxt | github.com/alexanderbelous/h3mtxt | .h3m/.h3c ↔ JSON 双向 CLI | P10-C 改写规则: JSON 层改写 (删城/封路/挪矿) 再转回 h3m, 免手撸二进制; 第二对账工具 |
| homm3tools | github.com/potmdehex/homm3tools (155★, MIT) | h3m 解析/编辑/map_editor C 工具集 | P10-C 备选参考; hd_edition/h3complete 格式细节 |

#### 三、已覆盖/明确排除

- smanolloff/vcmi-gym + smanolloff/vcmi = 本项目主仓/fork 本体, 无新增量
- vcmi Issue #5586 (LLM 接入提案) = 已调研, 无人实施, 维持排除
- HoTSPyBot / BOT-MMORPG-AI 等像素/截图 bot = 与引擎内接口路线相反, 不用
- **HoMM3 RL 训练不用 computer_use 截图 / vision_analyze 视觉分析** (常驻约束): VCMI Client SDL2 渲染无 UIA 元素, 视觉截图拿不到可用状态; 看游戏状态一律让用户描述或写脚本采集 obs/traj 数据。此约束适用于所有训练相关分析与子 agent 派发。

## P10-C 备料: h3mtxt roundtrip 验证 PASS (09-11, 训练停机窗)

### 结论

**h3mtxt (alexanderbelous/h3mtxt) 可用, C 步改写规则管线定型**: `h3m → JSON(带注释) → Python 改写 → h3m`。4 张图 roundtrip 全 RAW-IDENTICAL PASS (gzip 解压后逐字节一致; gzip 头 mtime 差异忽略, VCMI 引擎只读解压数据)。

### 构建踩坑三连 (GCC/mingw 独有, 详见踩坑 #199)

上游只测 MSVC, mingw64 GCC 16.2 编不过, 打了 3 个源码补丁 (tools/h3mtxt 本地树):
1. `H3JsonReaderBase.h` EnumBitmask partial specialization after instantiation → `-fpermissive` 降级 (cmake/h3mtxt_common.cmake 非 MSVC 分支加)
2. `H3WriterBase.h` 基类 EnumIndexedArray writeData 与派生类 H3MWriter 同名重载在 GCC 下二义 → 删基类版 (H3MWriter.h 版保留)
3. `ObjectPropertiesVariant.h` consteval static 成员在类内 alias 默认实参 "used before its definition" → 改 Detail_NS 命名空间 `inline constexpr` 变量模板 `kObjectPropertiesIsInline<T>` (MSVC/Clang 接受原写法, GCC 不接受 complete-class context)

### Roundtrip 验证矩阵

| 图 | 格式 | 结果 |
|---|---|---|
| doc/tutorial/test_map.h3m | SoD | PASS (13.9KB raw) |
| terrain_sprites_cheatsheet.h3m | SoD | PASS (20.4KB) |
| river_sprites_cheatsheet.h3m | SoD | PASS (2.4KB) |
| A Viking We Shall Go.h3m (真实对战图 144x144) | AB | PASS (46KB gz) |

**JSON 侧二次转换稳定** (rt1.json → rt1.h3m → rt2.json, 两 JSON 逐字节一致)。

### 已知边界

- 只支持 AB/SoD 格式; **ROE 图直接拒** (`H3MReader: invalid MapFormat`) — P10 选图 "Knee Deep in the Dead.h3m" 是 ROE (format byte=0), **不可用 h3mtxt 改写**, 需换 SoD/AB 图或先用 h3m_tool 升格式
- 输出 JSON 带非标准 `//` 注释 (非严格 JSON), Python 侧解析需 `json5` 或正则剥注释
- MSYS 路径坑: exe 收 `/c/...` 路径 "Failed to open", 必须 `MSYS_NO_PATHCONV=1` + `C:/...` 原生路径
- 构建慢: 866 目标, LTO 全程 ~40min (O3+flto), 增量改 3 头文件触发大范围重编

### P10-C 管线定型

```
h3mtxt map.h3m map.json          # 1. 二进制→JSON (tool: tools/h3mtxt/build/src/h3mtxt/h3mtxt.exe)
python rewrite (删城/封路/减守卫)  # 2. JSON 层改写 (先 json5.load 或剥 // 注释)
h3mtxt map_new.json map_new.h3m  # 3. JSON→二进制
h3m2vmap --check-h3m map_new.h3m # 4. 引擎校验 (既有 B1 转换器链)
```

## PpoModelAI teal 卡死修复 + VCMI 新 API 迁移 (09-11, ppomodelai/ C++ 批)

### 背景

Windows 端 PpoModelAI 插件（`ppomodelai/src/`, 256 维 ONNX obs, 训练侧 3464 冻结面不受影响）8 人局卡死：Game B 第 6 个 AI（teal）首次 predict 挂死。本批源码级修复 6 文件 +259/-82，全部注释标 `2026-09-11`。

### ModelInference 单例化 (teal 卡死根因修复)

- **根因**: 8 人局 = 7 个 ModelAI 各自构造 `Ort::Env + Session`（7 份全核线程池），第 6 个 AI teal 首次 predict 挂死。
- **修复**: `ModelInference::instance(path)` 进程级单例（C++11 magic static，线程安全，同路径只加载一次）；`makeSessionOptions()` 限制线程池 intra=2 / inter=1（obs 仅 256 维，不需要全核池）。
- **悬垂指针修复**: 旧版 `inputNames` 存 `GetInputNameAllocated(...).get()` 临时对象的 `const char*`（行尾析构后失效）→ ORT "Invalid input name: " 全部 fallback endTurn；改 `std::string` 深拷贝，`Run` 期间用局部 c_str。
- 调用侧 `make_unique` → `&instance(...)`；加载失败置 `nullptr`（不再半构造）。

### PpoModelAI 卡死防御 + 双坐标门

- **AI_TRACE 宏**: stderr 直通打点 + `fflush`（该插件 logAi 输出在 client log 中零命中，取证据只能靠 stderr 管道）。
- **yourTurn try/catch 兜底**: 任何异常都必须 `endTurn`，防 AI 回合卡死全局；含 elapsed 计时打点。
- **moveHero 双坐标门**（gui9 实测，同 09-10 "anchor↔visitable 双坐标系" 章）: `hero->pos` 是模板锚点格，交互格 = `visitablePos()`；server `CGameHandler::moveHero` 对收到的 dst 再做 `convertToVisitablePos(dst)` → **请求参数是 anchor 语义**。本地 tile/pathfinder 判定用 visitable 语义目标，请求参数 `dest = visitableDest + getVisitableOffset()` 转回 anchor。
- **本地三重门**（全过才发 `moveHero`，任一失败 endTurn，防 server 拒绝 → client `onPacketReceived` 崩溃）:
  1. tile 拒绝：岩石地形 / `blocked && !visitable`（同 server CGameHandler:949 条件）；
  2. simultaneous-turns 拒绝：目标格有他人所属对象（client 无法预判 `isContactAllowed`，保守 endTurn）；
  3. pathfinder 拒绝：`PathfinderCache.getPathsInfo(hero)` 目标不可达 / `turns > 0`（本回合 MP 不够）。
- **API 签名变化**: `cb->moveHero(moveHero, dest, false, LAND)`（英雄指针 + 无 playerID 参数）；`showGarrisonDialog` 第二参 `CArmedInstance*` → `CGHeroInstance*`（对齐新 CAdventureAI 虚函数）。
- **DLL 导出补齐**: `GetAiName`/`GetNewAI` 在源码缺失（exports.def 要求）导致链接失败，参照 `AI/MMAI/main.cpp` 约定补在 PpoModelAI.cpp 尾部（含 `__GNUC__` 下 `strcpy_s` 兼容宏）。

### ObsBuilder VCMI 新 API 迁移（obs 语义不变，纯 API 适配）

| 旧 API | 新 API |
|---|---|
| `cb->getDate(Date::DAYOFWEEK/WEEK/MONTH)` | `cb->getCalendar().getDayOfWeek()/getWeek()/getMonth()` |
| `cb->getPlayerStates()`（复数） | `cb->getPlayerState(PlayerColor, false)`（单数逐个查） |
| `pState->heroes.size() / towns.size()` | `pState->getHeroes().size() / getTowns().size()` |
| `hero->getHeroType()` | `hero->getHeroTypeID().getNum()` |
| `hero->experience()` | `hero->exp` |
| `getPrimSkillLevel(static_cast<...>(0..3))` | `getPrimSkillLevel(PrimarySkill::ATTACK/DEFENSE/SPELL_POWER/KNOWLEDGE)` |
| include `callback/CPlayerState.h` | `CPlayerState.h`（新路径）+ 新增 `callback/Calendar.h` |

### 构建与可观测性

- **StdInc.h**: 删除自写 `boost::noncopyable` stub —— 其 guard 名与真实 boost guard（`BOOST_CORE_NONCOPYABLE_HPP`）不符导致重定义冲突，连带 `makeDefend` 等类型转换报错；改 `#include "Global.h"`（与 `lib/StdInc.h` 口径一致）直接用系统 boost。
- **现状**: 源码已 commit (`0aa2047`); **DLL 重编 + 部署已确证 (09-11)**: `ppomodelai/build/ModelAI.dll` mtime 04:39:17 晚于全部源文件 (03:15~04:20), 二进制标记 4/4 命中 (`ONNX singleton session created` / `yourTurn enter` / `dest rejected by tile check` / `GetNewAI`); 部署副本 `D:/vcmi-fork-build/bin/AI/ModelAI.dll` 同大小 4647678 B + 同时间戳; 旧版备份 `backup_0911_lib/ModelAI_v4_552350.dll`。
- **与训练 v5 关系**: 零。训练栈走 `vcmi_gym` strategic_env + `libmlclient.so`（WSL），不链接 PpoModelAI.dll（Windows 客户端插件），本批不影响在训进程。

## T06 duel 蓝英雄死亡 = capture proxy（C 方案，09-11 停训窗上线，首局 PASS）

### 背景与根因

09-08 上线的 capture +100 激励（仅 T06 双图）采用原始口径 = 蓝城 owner 翻转（TOWN_CAPTURE 事件）。但 duel 图（`T06_adventure_72X72_01_duel.vmap`）上蓝英雄唯一且一死即 game_over 终局 → 蓝英雄不可能再到达蓝城 (69,69) → **owner 翻转式 capture 在 duel 图结构性死信**：红方消灭蓝英雄（duel 上实际的"等效占城"事件）拿不到 +100 capture 激励。1v3 图（72X72_01，3 蓝英雄 / 3 蓝城）无此结构问题，原始口径天然可用（c2 确认）。

### C 方案设计（用户拍板 09-11，A/B/C/D 四方向选 C）

- **激励**: duel 图上"消灭蓝英雄" = capture proxy，+100（与原始 TOWN_CAPTURE 同额），限定 T06 `_duel` 图，每局最多一次。
- **实现（ep_runner_one.py 两处）**:
  - L410: `_t06_hero_kill_capture` 标志（开局置位复位，触发后置位保证"每局一次"）。
  - L940-958: proxy 块插入点 = 空拍诊断与 `if _bnow:` BHERO_KILL 分支之间 — `_killed = bhero_ids_prev - _bnow`（蓝英雄 id 差集，**在 prev 更新前计算**），非空且 duel 限定 → +100 + `battle_quality_events.log` 落 `[TOWN_CAPTURE] ...(C: hero-kill proxy)` 记录。
- **无双记**: 蓝英雄全灭时 `_bnow` 为空走空拍分支，击杀事件只落 TOWN_CAPTURE(proxy) 标签，不再双记 BHERO_KILL。
- **零扰动**: 1v3 图不进 proxy 分支；监控脚本 `py/check_duel_watch.py` 零改动；OBS(3464)/动作空间零触碰（纯 ep_runner 注释层）。

### 部署过程（09-11 停训窗）

> ⚠️ 下述 1-2 步为 **09-11 白天旧 user 级 transient unit 的历史过程**；当晚已重构为 system 级 enabled unit（见本文 "#201 WSL 发行版容器空闲关停" 节）。**现行停启 = `wsl -u root systemctl stop|start homm3-train-v5`，禁用 `systemctl --user`**。

1. `systemctl --user stop homm3-train-v5` 优雅停（尾部 `Saved STATE_PATH step=629167`）→ 清 `__pycache__`。
2. **重启踩坑**: v5 为 transient unit（`--collect`），stop 后单元定义被清除，`systemctl start` 报 "Unit not found"（踩坑 #195，#168 三次复现）→ 改走 `py/restart_train_v5.sh`（systemd-run 重建，venv 必须绝对路径 `/home/administrator/vcmi-workspace/venv/bin/python`）→ `active`。
3. 在位验证: `grep -c '_t06_hero_kill_capture' ep_runner_one.py` = 3（C 方案代码在位）。

### 首局验证数据（PASS）

- `battle_quality_events.log` 首条: `[TOWN_CAPTURE] map=T06_adventure_72X72_01_duel.vmap blue_hero_killed=[1] at step 95 +100 (C: hero-kill proxy)`。
- BHERO_KILL 分布（同期）: T05_52X52_01 ×4 / T06 1v3 ×3 / T05_52X52_02 ×1 / T05_36X36_01 ×1；TOWN_CAPTURE 当前仅 duel proxy 1 条（1v3 原始 owner 翻转 capture 尚未发生，正常）。
- 训练健康: `Loaded train state (model+optimizer, step=629167)` 无缝续训 → 已跑 step 629638 avg_r=2.1；T06 1v3 局 r=156.53 steps=114、T05_mir r=157.38；`monitor_alerts.log` 不存在 = 零告警；`[ZOMBIE] hero dead (all-blocked x2)` 高频出现为红英雄全灭熔断既有行为（非新问题）。

### 后续动作

攒 ~40 局（C 方案上线后）聚合活跃任务 1 观察五判据（[TOWN_CAPTURE] 非零 / 守卫胜 ≥80% / avg_r 跌幅 <20% / 自发经济 ≥80% / 200 步局 ≤20%，r 基线 141.3）；达标后按错窗纪律走 72X72_02_duel 地图轴。

### 关联

踩坑 #189-#192 / 知识库 "VCMI 对象坐标体系: anchor↔visitable 双坐标系 (09-10)" 章 / 任务清单 P7。

## mq 模型部署线闭环：v5 全模型 C++ 实机对战底座 (09-11, ppomodelai/ + onnx 部署链)

### 部署链架构（全链路通）

checkpoint 体检 → `rl_model_v5_0911.onnx` 导出 + Python/C++ 探针对拍（maxdiff 1.4e-6）→ ModelAI C++ v5 适配全量落盘 → MinGW 直编部署 → 实机 1v7 验证 PASS。四层：

1. **模型层**: opset 17，双输入接口 `Net.forward(obs[1,3464], terrain[1,4,21,21]) → actor_logits[1,25] + critic[1,1]`；模型路径 `ModelInference` 按名定位输入（"terrain" 子串匹配 + 其余为 obs）与 "actor" 输出，shape 防御（obs 3464 / terrain 4×21×21 不符即 fallback）。
2. **推理层**: `ModelInference::instance()` 进程级单例（7 AI 共享，#189）+ intra 2/inter 1 线程池 + 输入名 std::string 深拷贝防悬垂（#190）+ **softmax 采样决策**（#196，temperature=1.0 与训练一致；argmax 因 logits 平坦已证伪）。
3. **决策层**: `PpoModelAI` AAI 模式移植 — 25 动作（0-7 移动 N-start CW + 8 INTERACT + 9 NEXT_HERO + 10 END_TURN + 11-24 高层）+ 单步决策模式（无 query 堆积，yourTurn → 本地三重门 → move 或延迟 endTurn）+ anchor↔visitable 双坐标转换（#191）。
4. **部署层**: `py/build_modelai.ps1` MinGW 直编（-std=gnu++20，3 源文件 + exports.def）→ `D:\vcmi-fork-build\bin\AI\ModelAI.dll`；dll 被运行中游戏锁定，部署前须先关游戏。

### 关键诊断案例：action 恒定的三层排查（mq-4）

- **表象**: 实机三 AI 动作恒 5/6，疑似"旧 dll 未替换"（logAi 行格式相同实为巧合性遗产——新代码保留了同格式 logAi 输出）。
- **定位链**: Grep 源码确认新逻辑在跑 → 误判排除 → **onnx 直探**（`py/probe_onnx_action5.py`：绕过 C++ 直接喂 onnx，全输入域 argmax 恒 6 + top1-top2 差 0.1~0.3 + logit_std≈0.19）→ 实锤模型 logits 平坦，与部署链无关 → 修法：predict 尾部 argmax 改 softmax 采样（用户拍板 C 方案：采样+重启训练双管齐下）。
- **方法论**: "换 dll 无效"不等于"dll 没换上"；**onnx 探针是切断 C++ 链路嫌疑的最快实锤手段**。

### 日志观测通道矩阵（实机监控口径）

| 通道 | 载体 | 实机可见性 | 用途 |
| --- | --- | --- | --- |
| logAi（logAiLogger） | `VCMI_Client_log.txt`（`C:\Users\Administrator\Documents\My Games\vcmi\logs\`） | **全量可靠** | 实机监控唯一主通道（`PpoModelAI: yourTurn/action` 行） |
| AI_TRACE（fprintf stderr） | stderr 管道 | **运行期不可见**（仅启动期 MUTEX 噪音） | 弃用于实机（#197，修正 #192 坑③） |
| server 侧 | client 日志 `[runServer]` 标签 | 单进程模式内嵌线程 | moveHero 拒绝/异常取证 |

### 实机验证证据（二次验证 PASS）

- 7 AI 玩家 "v5 model loaded successfully"；day1→4 连续推进无卡死。
- 动作多样化: turn1=[5,7,5,7,5,5,7] turn2=[7,7,5,5,5,7,5] turn3=[5,5,7,7,7,5,5]（argmax 版恒 5/6 对比）。
- moveHero 真实执行且方向语义严格吻合（#198）: P1 hero1932 (10,65)→(9,66)→(8,67)、P2 hero1931 (105,100)→(104,101)、P6 hero1927 (67,34)→(66,35)，action=5=SW=(-1,+1) 三方一致；action=7 不可达被 server 正确拒绝。

### 训练侧联动与后续

- 训练侧采样动作本就多样（act=[0,17,18,16...3,3,3]），平坦 logits 主要是部署 argmax 模式暴露的问题；C 方案（softmax 采样部署 + 续训观察 logits 拉开）双管齐下。
- 训练 logits 拉开差距后重新导出 onnx 替换即可，部署代码零改动；训练状态 step=629830 续训中（restart_train_v5.sh 重建，#195）。

### 关联

踩坑 #189-#191 / #195-#198 / `ppomodelai/src/ModelInference.{h,cpp}`、`PpoModelAI.cpp` / `py/probe_onnx_action5.py`、`py/build_modelai.ps1` / 任务清单 P7/P8 头部 mq 增量。

## 09-11 训练存活机制重构: 容器空闲关停根修 (Hermes 侧驱动)

### 问题定性
- Hermes/脚本侧 `wsl` 命令驱动训练时, 训练活不过单个命令周期 (~17-45s): **发行版容器空闲关停** — 最后一个 wsl 会话退出, WSL 终止整个 Ubuntu+systemd (VM boot_id 恒定不动)。user 级 transient unit (旧 restart_train_v5.sh) 与 system 级 unit 都随容器一起死, 挂法无关。
- 与 #195 transient unit 坑的关系: #195 是表层 (unit 随会话消失), 本坑是底层 (容器整体终止)。#195 的 "三次复现" 真凶即此。

### 双层修复 (09-11 实装, 验证 PASS)
1. **Windows keepalive**: `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList '--exec','sleep','infinity'` — 常驻隐藏会话, 容器不空闲关停。Windows 重启后需重起此进程。
2. **system 级 enabled unit** `homm3-train-v5`: /etc/systemd/system/homm3-train-v5.service, User=administrator, WorkingDirectory=/mnt/d/Bigdata/hero3_fresh, 双 append 到 train_loop.log。容器冷启动时 multi-user.target 自动拉训练。`wsl -u root` 免密安装 (WSL root 通道, 不需要 sudo 密码)。
- 附带: `.wslconfig` 加 `vmIdleTimeout=2147483647` (VM 层保险; 原尝试 -1 是非法值)。旧 `py/restart_train_v5.sh` 废弃, 备用脚本 `py/restart_train_v5_sys.sh` 留档。

### 运维与验证纪律
- 重启/状态: `wsl -u root systemctl restart homm3-train-v5` (status 同理); 日志 tail train_loop.log。
- **验证存活三件套**: `ps -o lstart,etime -C python` (PID 存活时长) + 日志 mtime 推进 + step 行出现。`systemctl is-active` 不可信 — 容器冷启动自动拉起也显示 active。首局 ~6-10min 才出第一条 step 行, banner 反复出现 = 进程被杀循环重启。
- 0911 实证: checkpoint step=629830 干净续训 → step630016+ 连跑多局 (T05 r=164.0 首局, [GUARD]/[MINE] 正常)。

### 关联

踩坑 #201 / #195 / 任务清单 L9 (训练存活机制重构段) / `py/restart_train_v5_sys.sh` / `.wslconfig`。

## T7.4 死亡惩罚上线：zombie 确认点 -50 归档（09-11 晚，停训窗 patch + checkpoint 续训）

### 背景（为什么修）
- 引擎判负不可达实锤：死亡局 game_over 恒 0（zombie 现象本身即证明 — 英雄死后 yourTurn 仍被调 = 引擎未判 standardDefeat），strategic_env L1117 的 "game_over==2 → -200" 永远轮不到。
- 定量证据（方案_T74 §1）：首胜后战死 7/7 局；死亡局 r=+50~+93 vs 超时局 r=-18~-107 — **死比活着结算更赚**（步数惩罚烧穿）；capture +100 可被"送死碰运气"套利；死亡点 GAE bootstrap 污染 vloss。

### 设计（ep_runner 层纯 Python，零 C++ 改动）
- 落点 = zombie 确认点（zombie_streak>=2 块，L1213-1222）："r += args.death_penalty; traj[rewards][-1] += args.death_penalty; traj[done][-1]=True" → GAE 经 done=True 截断 bootstrap，惩罚不污染后续。
- "--death_penalty" argparse 默认 -50（试探档），上限 -100（对称守卫），0=关闭；全局生效不按图分支（T04/T05/T06 统一，无死亡局零扰动）。
- 与 C 方案正交：capture proxy +100（蓝英雄死）与 death_penalty -50（红英雄死）落在不同帧/不同事件，不存在同帧双罚（方案_T74 §6 复核：红英雄全灭后蓝英雄已无 target，不会再触发 capture）。
- 主日志白名单补 "[HERO_DEATH]"（train_wsl2_ppo_v2.py L194 highlights 表），死亡事件进主日志可 grep。

### 参数定档依据
| 档 | 值 | 依据 |
|----|-----|------|
| 试探 | **-50**（当前） | 守卫战 +100 / 死亡 -50：打赢净 +50 仍正 → 不劝退接战（T05 守卫战是核心战斗信号源，过强惩罚=避战退化风险） |
| 加深 | -100 | 仅当 -50 档送死剧本未消失且接战率不塌 |
| 回退 | 0 | 接战率塌 >30% 或 avg_r 跌 >20% |

### 部署（09-11 晚停训窗）
1. "systemctl stop homm3-train-v5" → checkpoint 存 step=637994（日志实锤："Saved STATE_PATH (step=637994) and MODEL_PATH"）。
2. patch 两处文件语法验证通过：ep_runner_one.py（--death_penalty argparse L127 / zombie 块 L1213-1222 / 日志改 "[HERO_DEATH] penalty -50 [ZOMBIE] ..." 格式）+ train_wsl2_ppo_v2.py（白名单 L194）。
3. restart："Loaded train state (model+optimizer, step=637994)" 干净续训，KL adaptive 恢复（target=0.5 coef=0.3 kl_ref frozen from BC）；重启后配置 = batch=2048 maps=8（C4 #7632 新栈参数沿用），C 方案标志 grep=3 在位。

### 首窗观察（09-11 晚 11 局，T05 52X52）
- "[HERO_DEATH]" 触发 0 次 — 11 局全守卫胜局（ep_steps=71~73，GUARD won +100，r=153~166），无英雄死亡事件 → **判据 1（死亡局 r 转负）暂不可验，待实际死亡局出现**。
- avg_r=2.20 vs 重启前基线 2.34 — 跌 6%，远低于 20% 回退线（判据 3 通过）。
- [GUARD] 接战正常（ep=10 guard won step 48 / ep=11 guard won step 54），接战率未塌（判据 2 暂通过，样本 11 局需再攒 1 窗）。
- 结论：无需干预，继续跑；~100 局（1-2 窗）后复核三判据。

### 关联
方案 "docs/方案_T74_死亡惩罚_20260910.md"（设计稿，实装=本次）/ 踩坑 #195（C 方案 capture proxy，正交关系）/ #201（system 级 unit 运维）/ #204（T7.4 上线验证方法论）/ 任务清单「活跃任务 3」→ 转观察期 / 引擎侧 standardDefeat 判负根修 = 独立 C++ 课题（T7.4 落地后紧接立项，落地时复核 done 双路同帧双罚）。

## T7.4 死亡惩罚 09-13 方向纠正 + 02_duel 引擎 reset 冷启动竞态

### 09-13 用户提问 + 实证定判
- 用户问："死亡惩罚一次都没发生，是学会了生存、敌方太弱、还是根本不会遇见？"
- **实证定判 = 根本没遇见（地形让卡死结构性不可达）**。三层叠加：
  1. **ZOMBIE 触发条件 = 红英雄 8 方向全堵 ×2**（`passable.any()=False` 保险终止，非"被敌方击杀"）。duel 图全草地开阔 → 103 局 duel ZOMBIE=0 → 死亡惩罚触发条件永远不满足。
  2. **duel 图红方 BFS 绕路取兵/攻城**，几乎不会走到会卡死的位置。
  3. **历史 441 局 ZOMBIE 全部来自 T03/T04 小图**（20X20-36X36 地形复杂、死路多），T05/T06 大图 0 局。
- **T7.4 判据 1 "sample 池切 duel" 方向错误** — duel 图产不出死亡事件。需"高障碍图"（死路/障碍墙密集，T03/T04 级别）或引擎 standardDefeat 判负落地。T7.4 的 -50 试探档对 duel 图结构性无效。
- **机制澄清（读代码确认）**：T7.4 死亡惩罚的触发条件 = 红英雄卡死（zombie_streak>=2），不是"蓝英雄被击杀"。C 方案（蓝英雄消失 = capture proxy +100，[L948](file:///d:/Bigdata/hero3_fresh/ep_runner_one.py#L948)）与 T7.4 是两条独立轴。duel 图蓝英雄是"伪英雄"（静态，不交战），蓝英雄 obs 不会真的消失 → capture proxy 在 duel 中也结构性不触发（#213 已修 duel 跳过 C 方案）。

### 02_duel 引擎 reset 冷启动竞态（#214）
- **现象**：`72X72_02_duel` 4 局 `steps=1 secs=603 obs_nz=0`（`no_own_town` + `hero=(0,0) towns=[NONE]`），同图其余 103 局正常（obs_nz=301）。`01_duel`/`108X108 duel` 0 局命中，异常仅 02_duel。
- **定判**：①地图文件正常（objects.json 蓝方 hero_1(66,66)/红方 hero_0(5,5)/town_0/1 全在）→ 非地图缺陷；②`secs=603`（≈600 秒）= 首拍 `env.reset()` 阻塞 600 秒后正常返回全零 obs（引擎冷启动竞态，obs 段填充线程未就绪）；③全零 obs → `_own=None`（8 城段全 0）→ `start_home=False` 打印 `abort(no_own_town)`（[L596](file:///d:/Bigdata/hero3_fresh/ep_runner_one.py#L596)）→ 软放弃不终止 → 但 `act=16` 无效动作 + 引擎 `done=True` → 单步即终局 `steps=1`。
- **修复 — 方案 A 脏样本过滤（最稳，1 行，零引擎改动）**：[train_wsl2_ppo_v2.py L220-225](file:///d:/Bigdata/hero3_fresh/train_wsl2_ppo_v2.py#L220-L225) `obs_nz==0 → return None`，调用方 L377 `if traj is None: continue` → 全零 obs 局不进 PPO buffer。停训窗 `systemctl stop` → 清 `__pycache__` → `systemctl start` resume step=675915。
- **教训**：①`obs_nz=0` 是引擎冷启动竞态的信号（`secs≈600` 首拍阻塞 + obs 全零 + `no_own_town`），非地图缺陷 — 排查顺序先查地图文件，再查 reset 时序；②全零 obs 局对 PPO 价值网是纯噪声（无学习价值），训练端一行过滤即可消除污染；③方案 B（引擎 reset 重试 1-2 次）留作后续 — 需改 ep_runner + 清缓存 + 单独开引擎轴。

### 关联
踩坑 #214（02_duel 引擎 reset 竞态 + 方案 A 过滤）/ #213（duel C 方案误报）/ #212（02_duel 地图缺陷证伪）/ #210（HERO_DEATH 与 C 方案 proxy 正交）/ 任务清单「活跃任务 3」T7.4 方向纠正段 / `train_wsl2_ppo_v2.py` L220-225 过滤 / `ep_runner_one.py` L590-596 `no_own_town` 软放弃段。

## 09-12 T13.10 P8-C 协议栈+双探针闭环（离线 Query/MoveHero + 在线 Query/MoveHero 全 PASS）

### 阶段背景
- 主线（T7 城镇经济 + T13.10 多人对战底座）在跑，P8-C 阶段补齐 **MoveHero 实战闭环 + QueryReply 实战闭环**。全部离线+实机验证，不干扰训练。
- P8-B 方案 F 已交付：Python 先连当 host → 真实 guest client → Python 发 LobbyChangeHost 让位 → guest 发 SetMap → StartGame（离线 lobby 全通、实机 vcmiserver 握手通过）。

### 四探针结果矩阵
| 探针 | 载体 | 结果 | 关键指标 |
|---|---|---|---|
| **离线 Query** (`py/p8/p8c_query_probe.py`) | 127.0.0.1:0 mock server | 6/6 PASS | 覆盖 HeroLevelUp / BlockingDialog / GarrisonDialog / qid=-1 skip |
| **离线 MoveHero** (`py/p8/p8c_movehero_offline_probe.py`) | 127.0.0.1:0 mock server | 6/6 PASS | 单/多点路径 + fow 条目数 + 拒绝包 + EndTurn + request_id 回显 |
| **在线 Query** (`py/p8/p8c_query_probe_real.py`) | 实机 vcmiserver 3030 | PASS (qid=-1 only) | turns_act=14 turn_ends(102)=27 |
| **在线 MoveHero** (`py/p8c_movehero_probe_real.py`) | 实机 vcmiserver 3030 | PASS | turns_act=4 move_accepted=9 move_failed=0 try_moves_total=12 bad_keywords=0 |

**实机首解证据**：`oid=350 result=1 start=(1,8,0) end=(2,7,0) mp=1760 fow=14` — TryMoveHero 全字段实机首次完整解出。

### 协议栈四层隐性缺陷（#207 记录）
1. **QueryManager 层**：用 `type_id` 代替真实 `query_id`（首字段）派回复 → 错包。修复：`protocol.py` 在 `handle_query` 前从包首字段提取真实 qid。
2. **三个 Query 派生类字段序错位**（HeroLevelUp / BlockingDialog / GarrisonDialog）：packs.py 原字段序与 VCMI `PacksForClient.h` 不匹配。修复：逐个按 wire 顺序覆写 `serialize/deserialize`。
3. **parse_client_pack 扁平 vs 嵌套不一致**：单测手写 dict 掩盖了 wire 层 bug；生产返回 `{type_id, class_name, data:{...}, raw}` 嵌套结构，测试却直接读顶层字段 → 假绿。修复：测试用例改为读 `.data`，且新增 7 项 TryMoveHero wire 断言。
4. **TryMoveHero 字段序**：从"占位 2 字段（source/destination/reason）"改为真 wire 字段序：`oid + result(0..5) + start(int3) + end(int3) + movePoints + fowRevealed(vector<int3>) + attackedFrom(int3)`。

### Query 分支控制流教训（#208 记录）
- **现象**：只收到 1 条 `PlayerStartsTurn qid=-1 (INVALID, 跳过回复)` 后 server 断开。
- **根因**：`if tid in QueryManager.QUERY_TYPES: ... continue` 分支吞掉 tid=88，后续 `elif tid == 88: act_turn()` 兜底永不触发 → EndTurn 永不下发 → server 等回合结束超时踢连接。
- **修复**：在 Query 分支内对 tid=88 做特殊处理，无论 qid 是否 -1 都触发 `act_turn`。
- **教训**：①Query 分支不能只写"回复/跳过"两义；②实机是终极仲裁（离线全绿不代表实机跑通）；③qid=-1 语义 ≠ 整包可忽略（"非实际 query"≠"不需要动作响应"）。

### 关键 wire 契约（PacksForClient.h 权威）
- **顶层包帧**：`isNull(1B) + pid(LVarInt) + tid(LVarInt) + 数据`
- **TCP 帧**：`uint32 length (little-endian) + payload`
- **Query 派生类首字段恒为 queryID**：`struct DLL_LINKAGE Query : public CPackForClient { QueryID queryID; }` — 所有 Query 派生类首字段都是 queryID
- **QueryID == -1**：NetPacksBase.h L47-50 明确"非实际 query, 不应回复"
- **TryMoveHero result 枚举**：0=FAILED 1=SUCCESS 2=TELEPORT 3=BLOCKING_VISIT 4=EMBARK 5=DISEMBARK

### 关键产物
- `py/vcmi_protocol/packs.py` — TryMoveHero 真字段序 + 三 Query 派生类序列化覆写
- `py/vcmi_protocol/protocol.py` — parse_client_pack/parse_server_pack 嵌套返回 + QueryManager 真 qid 提取 + qid=-1 skip
- `py/vcmi_protocol/tests/test_e2e.py` — TryMoveHero 7 项 wire 断言（e2e 167/167 通过）
- `py/p8c_movehero_offline_probe.py` — 新建，6/6 PASS
- `py/p8c_movehero_probe_real.py` — 新建，实机 PASS
- `py/p8/p8c_query_probe_real.py` — Query 分支特判 tid=88

### 训练冲突纪律
- **离线探针**（127.0.0.1:0 系统端口 + 纯 mock）：零冲突
- **在线探针**（taskkill + 3030 端口）：必须停训练再跑
- 本轮训练状态：`homm3-train-v5` systemd 单元当前未启（本轮探针执行时零冲突）

### 关联
踩坑 #207（协议栈四层隐性缺陷）/ #208（Query 分支吞 PlayerStartsTurn）/ #201（system 级 unit 运维）/ 任务清单 T13.10 P8-C 完成回写 / `py/vcmi_protocol/` 包。

---

## 09-12 TOWNSTALL 平台段误判 + 训练日志健康度快照

### 结论（截至 2026-09-12，日志分析实锤）

**TOWNSTALL 误判根因**
- `ep_runner_one.py` L877 `if cur_dist >= move_stall_prev:` 把路径平台段（BFS `plen` 横向移动时步数持平）误判为"停滞"，6 步累积后触发 `TOWN_BLOCKED` 禁用城镇引导
- L887 副作用：`move_stall == 1` 时 `dyn_blocked.add((bx, by))` 把**可通行格**加入黑名单（passability mask 全 1 仍判 stall），放大误判
- 全 log 统计：`TOWNSTALL` 3817 次 / `TOWN_BLOCKED` 460 次；局仍正常完成，仅损失 `town_visited` 约 +30/局
- 修复方案：L877 `>=` 改 `>`，只惩罚"进度变差"，允许"进度持平"；**需 stop/restart 重启窗实施，与 checkpoint 同窗**
- 详见踩坑 #209

**训练日志健康度快照（step=641793，09-12）**
- 服务 active，step 640489→641793 正常推进
- T05/T06 局 r=142~255，全 err=no
- 出现 TOWN_CAPTURE 击杀蓝英雄 3 个（1v7 优势扩大信号）
- 大额负奖励属 T04 历史遗留（86%），非新增故障
- 明细日志无 ZOMBIE/ENDTURN_FUSE，训练健康，无需干预

### 关联
踩坑 #209（TOWNSTALL `>=` 误判根因）/ 任务清单 L107「TOWNSTALL 引导可达性」行 / `ep_runner_one.py` L872-898。

### T06 duel C 方案 hero-kill proxy +100 全误报修复 (09-13, #213)

**背景**: C 方案 (09-11 上线, 同日扩展全图) 定义"蓝英雄死亡 = capture proxy +100"，duel(1v1) 蓝英雄一死 → game_over → 原 TOWN_CAPTURE(owner 翻转) 结构性死信 → 蓝英雄击杀事件替代。09-12 日志分析时发现 duel 的 49 条 `[TOWN_CAPTURE] blue_hero_killed=[1]` 全部可疑（同期 `BHERO_KILL` = 0），启动单独核查。

**核查结论 — 49/49 全部误报，无真击杀**:

三重证据链：

1. **`BHERO_KILL = 0`** — obs 正常状态下蓝英雄从未消失（集合差恒为 0），英雄一直活着
2. **`HEROSEG_EMPTY = 0`** — 全空拍诊断未触发，因为战斗瞬态期间 `_bnow` **非全空**（有部分英雄但少了 id=1），走不到 `if not _bnow` 的全空拍分支
3. **ep 继续运行** — TOWN_CAPTURE step 95 后 ep 正常到 step 96 才 end（`err=no`）；若真击杀 duel 应当步 game_over，不该多跑 1 步

**根因 — 两条路径不对称 (ep_runner_one.py L948 vs L963)**:

C 方案 L948 无 `_bnow` 非空守卫：
```python
if (bhero_ids_prev is not None and not _t06_hero_kill_capture):
    _killed = bhero_ids_prev - _bnow  # obs 部分少报 → 误判"消失"
```

`BHERO_KILL` L963 有守卫：
```python
if _bnow:  # ← 空拍时跳过，防止 prev 被清空
```

duel 战斗瞬态（蓝英雄进战斗 → C++ obs 线程清 heroes 段 id=-1 → 填充循环短暂 0 行）造成 `_bnow` 部分少读但不全空，C 方案路径**无守卫**直接误判。

**修复 — 方案 B: duel 删除 C 方案**:

在 L948 加 `and not args.mapname.endswith('_duel.vmap')`。duel 蓝英雄死 = game_over = ep 终止，无需 C 方案 proxy；+100 纯属污染价值学习。

```python
if (bhero_ids_prev is not None and not _t06_hero_kill_capture
    and not args.mapname.endswith('_duel.vmap')):
```

**影响评估**:
- 49 次 × +100 = **4900 虚假 reward 已注入 PPO 价值网络**
- 集中在 duel 早期 step（28-99 占 33/49 = 67%），让 agent 学到"进战斗 = +100"的错误价值关联
- 当前 duel 局 r 基线被抬高约 +100/局（49 局 × 100 / 总 ep 数）

**教训**:
- 两条相似代码路径（C 方案 + BHERO_KILL）的守卫条件必须对齐 — 一处有 `if _bnow` 另一处没有 = 隐蔽缺陷
- 战斗瞬态的 obs 部分少报（非全空）是比全空拍更隐蔽的误报源，全空拍防护（L934 `if not _bnow`）拦不住部分少报
- duel 中蓝英雄死 = game_over = ep 终止，游戏引擎已处理终止信号，**不需要额外 reward proxy** — proxy 只在"蓝英雄死但 ep 不终止"的 1v3/1v7 场景才有必要

**关联**: 踩坑 #213 / #210（HERO_DEATH 与 C 方案 proxy 正交）/ 任务清单 T13.10 专区 / `ep_runner_one.py` L944-962。

### 09-13 地图轴: King of Pain H3M 官方图入池 + T04 回池 + T05 MIR 3 张移除

**背景**: 用户指令"King of Pain.h3m.vmap，把这个地图加进来训练" + "只去 T05 三个 MIR，加 T04 1-2 张"。本轮 09-13 地图轴变更三连：①去除 T05 MIR 镜像 3 张（36X36_01_mir / 52X52_01_mir / 52X52_02_mir），T05 难度上移；②T04 死路密集图 2 张（36X36_01 + 30X30_01）加回 MAPS，作为 T7.4 判据 1（ZOMBIE 死亡局 r 转负）唯一可行样本源；③King of Pain（H3M 官方 72X72 死路图）入池，提供高障碍大图维度。

**King of Pain 入池技术细节**:
- **来源**: H3M 官方图（SoD, 72X72, 3p），经 `py/vcmi_full_to_slim.py` 转 VMAP（1657→173 对象：hero_0 + town_5 + mine_38 + resource_68 + monster_61）
- **文件**: `maps/training/King_of_Pain_h3m.vmap`（gzip 压缩，含 header.json / surface_terrain.json / objects.json）
- **命名约束**: 文件名带 `_h3m` 后缀，因 `strategic_env.py` L150-154 强制要求 mapname 含 s1/mini/adventure/h3m 之一标识。King 不带 T 前缀（非 T04/T05/T06 课程图），**不走 T04/T05/T06 引导分支**，潜在引导缺失需首局观察（obs 初始化 / NK2 寻路 / 引擎 reset）。
- **地形**: gr57_ 系列（gr24_ 变体），无 rc/wa 前缀 → passable_grid 全通（单层无桥无船一致），has_underground=0。
- **MAPS 位置**: L69 `"King_of_Pain_h3m.vmap"`，MAPS[6]（修复截断后）。`random.choice(MAPS)` 抽样 9 图，King 占 1/9，需时间才抽中。

**L69 语法截断 bug（踩坑 #215）**: 上一轮改 MAPS 时 L69 写入 `"King_of_Pain_h3` 但漏了后续 `m.vmap",`，引号未闭合。Python 解析器静默 drop 该条（`py_compile` 不报错，因文件其余部分合法），King 从未真正入池。本轮修复：SearchReplace 补全为 `"King_of_Pain_h3m.vmap",`，AST 解析确认 MAPS=9。

**T04 回池（T7.4 判据 1 样本源）**: 09-04 T04 12 图退役存档（原版 6 + _mir 6），本轮加回 2 张死路密集图（`T04_adventure_36X36_01` + `T04_adventure_30X30_01`），作为 T7.4 判据 1（死亡局 r 转负）样本源。T7.4 09-13 方向纠正实证 duel 图产不出 ZOMBIE（全草地开阔，8 方向全堵结构性不可达），需"高障碍图"（死路/障碍墙密集，T03/T04 级别）。T04 -50 试探档在死路局可触发 ZOMBIE → 死亡局 r 转负首验。

**MAPS 现状（修复后 9 条）**:
```
[0] T05_adventure_36X36_01.vmap
[1] T05_adventure_52X52_01.vmap
[2] T05_adventure_52X52_02.vmap
[3] T06_adventure_72X72_01_duel.vmap
[4] T06_adventure_72X72_01.vmap
[5] T06_adventure_72X72_02_duel.vmap
[6] King_of_Pain_h3m.vmap       ← 修复截断后入池
[7] T04_adventure_36X36_01.vmap
[8] T04_adventure_30X30_01.vmap
```

**runtime 完整性**: `/home/administrator/vcmi-workspace/vcmi_gym/envs/v13/maps/` 本轮 `cp` 补齐 5 张缺失（T05 36X36_01 / 52X52_01 / 52X52_02 + T06_72X72_01_duel / 72X72_01），源自 `/mnt/d/Bigdata/hero3_fresh/maps/training/`。runtime 现含 10 图（含 King），训练加载不报错。

**MIR 清除确认**: `_mir.vmap` 6 处 grep 命中全在 L37-42 注释区（`#` 开头 T04 旧池存档），MAPS 主列表无有效 MIR 条目。新进程（PID 14345, 08:50:42 启动）`maps=9`，不再产 MIR episode。

**部署**: 优雅停 `wsl -u root systemctl stop homm3-train-v5` → 清 `__pycache__` → `systemctl start homm3-train-v5` → active（step=676490 正常推进）。

**观察项**: ①King of Pain 首局（obs 初始化 / NK2 寻路 / 引擎 reset；不带 T 前缀不走 T04/T05/T06 引导分支，潜在引导缺失）；②T04 是否产 ZOMBIE 事件 → T7.4 判据 1 首验；③9 图全部正常加载无报错。

**关联**: 踩坑 #215（King L69 语法截断）/ #214（02_duel 引擎 reset 竞态 + 方案 A 脏样本过滤）/ #213（duel C 方案误报）/ 任务清单 09-13 地图轴增量 / 活跃任务 3（T7.4 判据 1 样本源落实 T04 回池）/ `train_wsl2_ppo_v2.py` L48-73 MAPS 段 / `strategic_env.py` L150-154 T04/T05/T06 引导分支 / `py/vcmi_full_to_slim.py` H3M 转换工具。

### 09-13 训练日志分析: King of Pain 首局脏样本 + T04 负 r 首现 + T7.4 死亡惩罚已启用确认

**背景**: 地图轴变更后（MAPS=9）step=680112 训练日志分析，发现 3 个关键事实。

**1. King of Pain 首局全部脏样本（无有效训练数据）**:
- 日志中 3 局 King of Pain，全部 `steps=1, secs=603, r=12.5, obs_nz=0`
- 根因：引擎 reset 603s（全地图最大）后 obs 仍为空（冷启动竞态）→ `no_own_town` abort → 单步终局
- 方案 A（#214）全捕获：3 条 `[FILTER] obs_nz=0 脏样本丢弃`，0 条进入 PPO buffer
- 结论：King of Pain 在 9 图池里**暂无有效训练贡献**，需持续观察后续局是否仍 1 步 abort（若是 = VMAP 初始化异常，需排查 `vcmi_full_to_slim.py` 转换质量）
- 同 02_duel 引擎 reset 竞态（#214），H3M 72x72 大图与 duel 图共性：reset 耗时 ~600s，obs 段填充线程未就绪

**2. T04 首现负 r 局（T7.4 判据 1 首验数据）**:
- T04_30X30_01 4 局负 r：-32.0 / -69.7 / -38.7（200 步超时，死路密集 → 拿不到足够奖励）
- T04_36X36_01 2 局负 r：-32.0 / -69.7（同上）
- 同时 T04 也有正 r 局（160.9 GUARD 胜 / 151.9 169 步正常结束 / 146.3 55 步 GUARD 胜）
- 判据 1（死亡局 r 转负）**部分达成**：T04 确实能产出负 r，但 ZOMBIE 触发（`[HERO_DEATH]` 标签）尚未在 T04 回池后首次出现（`grep -c 'HERO_DEATH' train_loop.log` = 0）

**3. T7.4 死亡惩罚已启用确认（用户问"死亡惩罚，要启用吗？"）**:
- **不需要启用，-50 已在线生效**
- 代码路径：`ep_runner_one.py` L127 `--death_penalty` argparse `default=-50.0`；`train_wsl2_ppo_v2.py` L139-141 未显式传，依赖默认值
- 触发条件：红英雄 8 方向全堵 ×2（`passable.any()=False` 连续 2 步）→ L1214-1226 `r += death_penalty` + `done=True`
- 当前状态：`[HERO_DEATH]` 0 命中（T04 回池后样本未攒够），判据 1 挂起
- 历史 441 条 ZOMBIE 全来自 T03/T04 小图（09-04 前），T05/T06 大图结构性不可达
- T04 回池后 2 张死路图占 MAPS 2/9，按 `random.choice` 频率攒 ~100 局 T04 需时间

**4. MIR 残留确认**:
- `_mir` 在日志中 1539 次命中 = 旧进程（08:50 前）残留日志，新进程 MAPS=9 无 MIR 条目
- `_mir.vmap` grep 6 处全在 L37-42 注释区（T04 旧池存档），无有效代码命中
- 新进程不再产 MIR episode，日志追加模式保留旧行

**5. King of Pain 潜在引导缺失**:
- King 不带 T 前缀（非 T04/T05/T06 课程图），`strategic_env.py` L150-154 引导分支不命中
- 需观察：obs 初始化 / NK2 寻路 / 引擎 reset 是否因引导缺失导致异常

**关联**: 踩坑 #214（02_duel 引擎 reset 竞态 + 方案 A）/ #215（King L69 语法截断）/ 知识库 09-13 地图轴章 / 任务清单 活跃任务 3（T7.4 判据 1 样本源落实）/ `ep_runner_one.py` L127/L1214-1226 / `train_wsl2_ppo_v2.py` L48-73 MAPS / `strategic_env.py` L150-154 引导分支。

### 09-13 地图轴二次扩展: T04 移除 + T06 三张大图入池 (MAPS=9→10)

**背景**: 用户判断 T7.4 死亡惩罚"英雄打不死就永远不触发"，决定砍掉 T04 死路密集图的 T7.4 样本源定位，改走大图轴扩展（1v7 多敌轴 + 108X108 最大图）。

**变更**（`train_wsl2_ppo_v2.py` L48-73 MAPS 段）:
- 移除: `T04_adventure_36X36_01` / `T04_adventure_30X30_01`（2 张）
- 加入: `T06_adventure_72X72_02` / `T06_adventure_108X108_02_duel` / `T06_adventure_108X108_02`（3 张）
- MAPS: 9 → 10

**新增图 identifier 检查（zip 解析）**:
- `hero_subtypes=['core:alchemist']` — 合法
- `town_subtypes=['core:conflux','core:dungeon']` — 合法（SoD 城）
- `108X108_02_duel`: 2 hero + 2 town（1v1 duel 结构）
- `72X72_02` / `108X108_02`: 4 hero + 4 town（header 只注册 1 blue hero，objects 4 个，同 01 口径）
- 三图均无 identifier 风险

**T04 移除对 T7.4 判据 1 的影响**:
- T7.4 -50 全局生效（不按图分支），但 T7.4 判据 1（"死亡局 r 转负"）的样本源失去 T04 死路密集图
- T06 全开阔大图 ZOMBIE 结构性不可达（09-12 定判），King of Pain 在修（dragon identifier）
- 判据 1 挂起 → 若 T06/108X108 局也 0 次 ZOMBIE，则 T7.4 需引擎 `standardDefeat` 判负落地才有样本

**King of Pain 死因补充（09-13 二次排查）**:
- 除 #221 reset 竞态外，引擎日志新增错误：
  ```
  [%p/runServer][global] ERROR Failed to find object of type monster::core:dragon
  [%p/runServer][global] ERROR Failed to launch game: Failed to resolve identifier monster::core:dragon
  ```
- `monster::core:dragon` 不在当前 `libvcmi.so` 注册表 → `NEW_GAME` 失败 → 引擎挂起/反复重启
- King of Pain（H3M SoD 官方图）引用了 SoD 龙单位，当前部署的 libvcmi.so 缺少该 identifier
- 处置：King 正在单独修改（用户确认），暂不干预训练

**当前 MAPS 10 张**:
| 课程 | 图 |
|------|-----|
| T05 | 36X36_01 / 52X52_01 / 52X52_02 |
| T06_01 | 72X72_01_duel / 72X72_01 |
| T06_02 | 72X72_02_duel / 72X72_02 |
| 108X108_02 | duel / 原版 |
| King | King_of_Pain_h3m（修复中） |

**关联**: 踩坑 #221（King reset 竞态）+ dragon identifier 缺失 / 任务清单 09-13 地图轴二次扩展 / `train_wsl2_ppo_v2.py` L48-73 MAPS / `py/_check_108_ids.py`（108X108 identifier 检查工具）。

## VMAP header.players 系统性缺陷 + 批量修补（09-13 停训窗）

**背景**: King of Pain 入池后 3 局全部 `steps=1 obs_nz=0 no_own_town abort`，#221 初判为"引擎 reset 竞态"。逐层排查（`py/_check_king.py` / `_deep_king.py` / `_check_king_players.py` / `_compare_town_fields.py` / `_king_all_owners.py`）证实真实根因 = **VMAP `header.players = []` 空数组**（地图初始化异常，非引擎时序竞态）；同病扫描发现 4 张 T06 `_02(_duel)` 系列 VMAP 也有相同缺陷（其中 `T06_adventure_72X72_02_duel.vmap` 就在训练 MAPS 名单 L64）。**5 张全部 patch 完成，扫描 60 张 VMAP 全部 players OK**。

### 根因链路

- **VCMI 引擎玩家创建**：`header.players` 决定引擎创建多少玩家槽位（player 0..N-1）。空数组 → 无玩家索引 → obs 8 城段 `owner` 字段全为 0。
- **obs 城段语义**：`obs[336:480]` = 8 城 × 18 字段，owner 位置 `_tb2+1`，coords `_tb2+2/+3`。
- **`no_own_town` abort 判定**（`ep_runner_one.py` L584-596）：`owner=0 且 coords 有值 → 己方城`；无己方城则 abort。
- **结论**：`header.players=[]` → obs 全零 → `no_own_town` 是**必然触发**（非竞态偶发）。#221 的"reset 竞态"假设已被证伪。

### header.players 两种格式

| 格式 | 示例 | 来源 |
|------|------|------|
| dict-of-players（T01 标准）| `{blue:{canPlay:'PlayerOrAI',heroes:{...}}, red:{...}}` | 手工制作 VMAP |
| list-of-dicts（L1 老格式）| `[{canComputerPlay:true,canHumanPlay:true,mainHero:null}, ...]` | L1 系列老图（8 张）|
| 空数组（缺陷）| `[]` | h3m2vmap 转换产物 + T06 _02 生成脚本产物 |

### 对象分布结构

- `objects.json` = **dict-of-dicts**（`name → obj`），非 list，遍历 `for k, v in objs.items()`。
- `owner` 位置 = `obj.options.owner`（不是 `obj.owner`）。
- `owner` 值 = **颜色字符串**（"blue"/"red"/"orange"/"teal"/"green"/"yellow"）不是玩家索引。
- 训练 AI 主控方 = player 0 = blue（`vcmi_gym/envs/v13/strategic_env.py` L93 `p0 = state.players[0]`）。

### 5 张图修补明细

| # | 文件 | players 前 | 后 | 对象变更 | 尺寸 |
|---|------|-----------|------|---------|------|
| 1 | King_of_Pain_h3m | `[]` | `{blue,red}` | town_1 owner red→blue + hero_0 owner red→blue | 10713→10781 |
| 2 | T06_adventure_72X72_02_duel | `[]` | `{blue,red}` | 无（对象已正确）| 1723→1804 |
| 3 | T06_adventure_72X72_02 | `[]` | `{blue,red}` | 无（对象已正确）| 1787→1868 |
| 4 | T06_adventure_108X108_02_duel | `[]` | `{blue,red}` | 无（对象已正确）| 1895→1976 |
| 5 | T06_adventure_108X108_02 | `[]` | `{blue,red}` | 无（对象已正确）| 1959→2038 |

**共同修改**：`header.mods: [] → {}`（对齐 T01 格式）。

**King 特殊性**：H3M 官方 5 玩家图，原 town/hero owner 分 5 色（orange/red/blue/None/None），hero_0 原本归属 red；修补时必须同时改 `town_1 + hero_0 owner → blue` 让蓝方 = player 0 主控逻辑一致。修补后 Blue 2 town + 1 hero，Neutral 3 town。

**T06 _02 系列特点**：标准 1v1/1v3 生成图，town/hero owner 已正确（town_0/hero_0=red @ 左上，town_1/hero_1=blue @ 右下），只改 header 不动 objects。

### 工具链

- `py/patch_king_players.py` — King 单图 patch（v2，改 header + objects）
- `py/patch_t06_02_players.py` — T06 _02 批量 patch（只改 header）
- `py/_scan_players.py` — 60 张 VMAP 全量扫描工具（新增 VMAP 入 MAPS 前必检）
- 备份后缀：`.vmap.bak_players_patch`（5 张均有备份）

### 系统性缺陷定性

**缺陷 #4**（h3m2vmap 系列 + T06 生成脚本共同缺陷）：转换/生成脚本导出 VMAP 时未注入默认 `header.players` 字段。**其他未入池 H3M 转换产物同样有此缺陷**，未来入池前必扫。

**长期治本**：改 `tools/h3m2vmap/main.cpp` + `py/vcmi_full_to_slim.py` + `fix_t06_maps.py` 生成管线，导出时注入默认 `header.players={blue,red}`。

### 回归验证

- `py/_scan_players.py` 60 张 VMAP：**52 张 dict-of-players OK**（含 King + T06 _02 系 4 张修补产物）+ **8 张 L1 老 list 格式**（非空数组，引擎兼容识别）+ **`players=[]` 空数组 0 张** ✓
- 训练 MAPS 名单 10 图全部 `players OK`（无脏图）
- 训练当前 `inactive`（未擅自启动）

**关联**: 踩坑 #222（King 真实根因 + 单图 patch）+ #223（T06 _02 批量 patch）+ #221（reset 竞态假设已被证伪）+ #214（方案 A 过滤兜底仍生效）/ 任务清单 09-13 地图轴 patch 增量 / `train_wsl2_ppo_v2.py` L64（T06 72X72_01_duel 入池历史）/ `ep_runner_one.py` L584-596（`no_own_town` 判定）。

## VMAP 运行时部署拓扑 + sync 同步固化 + King 1v3 重建（09-14）

### 运行时地图加载链路（踩坑 #224，拓扑实锤）

```
权威源  d:\Bigdata\hero3_fresh\maps\training\<name>.vmap   (git 仓库, 改图只改这里)
                          │  py/sync_maps_to_runtime.py (原子写+校验)
                          ▼
运行时真实目录  vcmi/data/Maps/<name>.vmap
                          ▲ readlink 软链（同一目录, 不是双副本）
        ┌─────────────────┴──────────────────┐
  vcmi-native/rel/bin/data/Maps     vcmi-native-build/rel/bin/data/Maps
                          ▲
  ep_runner ctypes libmlclient.so: chdir(VCMI_BIN_DIR) → userDataPath()/Maps
  代码: ML/MLClient.cpp L307-308 validateFile, L421 "Maps/"+mapname, L489 chdir
```

- 地图名强制含 `s1/mini/adventure/h3m`（strategic_env.py L522）。
- 反查运行进程实际读图：`pgrep -f ep_runner_one` → `ls -la /proc/<pid>/cwd`；对比版本用 sha256/mtime。
- 探针与训练并发安全（进程内连接器、无端口无锁），但 traj/ep_log 必须用独立文件（训练占用 `/tmp/traj_ep.json`）。

### 权威同步工具 py/sync_maps_to_runtime.py

| 用法 | 作用 |
|---|---|
| `python py/sync_maps_to_runtime.py --strict` | **改图后必跑**：预检→同步→写后校验，rc=0 才可训 |
| `--check` | 只校验不同步，不一致 rc=1（重启前门禁/可接 CI） |
| `--dry-run` | 报告不写盘 |
| `--check --strict` | 纯校验 + identifier 注册表检查 |
| `<name>.vmap ...` | 只同步指定图（仍须在 MAPS 清单内） |
| `--purge` | 删除运行时非 MAPS 退役图（默认只汇总不删） |

要点：① 同步范围 = AST 解析 train_wsl2_ppo_v2.py 顶层 MAPS（唯一清单，退役图自动排除）；② resolve() 软链去重只写一次；③ 源侧预检=zip 三条目/header.players 含 red+blue/owner∈{red,blue,null}/双方至少各一城/（strict）monster·town identifier 在 VCMI config 注册表；④ 原子写（tmp+fsync+rename）+ 写后 sha256 复验；⑤ 运行中 ep 不受影响，新局自动加载新版。负向回归脚本 `py/_test_sync_negative_0914.sh`。

### VCMI core 注册表位置（identifier 合法性核查）

- `/home/administrator/vcmi-native/config/creatures/<城镇>.json`（11 个城镇文件，**JSONC 带 // /* */ 注释**，解析前需 strip；顶层 key 即生物 id 如 redDragon/blackDragon/greenDragon，**无泛指 dragon**）。
- `config/heroes/`（144 英雄）、`config/towns/`、`config/resources.json`。
- `rel/bin/config` 是指向 `vcmi-native/config` 的软链；core mod 本体在 `rel/bin/Mods/vcmi`（只有 Content 资源，json 注册表在 config/）。

### vmap 结构与 1v3 阵营模板（踩坑 #225/#226）

- vmap = zip 三条目：`header.json` / `surface_terrain.json` / `objects.json`；objects 是 **dict-of-dicts**（key→obj）。
- 合格 header = **13 字段**（5 基础 + allowedArtifacts/defeatIconIndex/difficulty/victoryConditions=[standardDefeat,specialVictory]/triggeredEvents/versionMajor/versionMinor/victoryIconIndex=2）；players 为 `{blue:{...}, red:{...}}`，mods 为 `{}`。
- owner 在 **`obj.options.owner`**（颜色串 red/blue/None；orange/teal 等未在 players 声明 = 引擎 SIGSEGV）。
- T06 1v3 英雄 schema：`subtype=core:alchemist`（职业），`options.type`=具体英雄（edric/iona/christian/piquedram），army 第 4 槽 peasant；英雄驻守在城旁切比雪夫距离 3 的对角格；header 每方只声明一个主角类型。
- King 1v3 终态：red=town_1(10,8)+hero_0(13,11)；blue=town_0(4,62)+town_2(65,64)+town_4(54,28) + hero_1/2/3(7,65)/(62,61)/(57,31)；town_3(40,52) 中立；173→176 对象。
- 完整局验收口径：**rc=0 且 traj 无 error 字段（EP_TIME err=no）**；err=yes 局 train 侧静默不进 buffer（train L240）。

### 09-14 事故修复时间线（假局污染收尾）

1. 残留 traj 假局三道拦截已在 09-14 凌晨上线（run 开头删 traj / 记录 ep_rc / rc≠0+身份不符 [FILTER]），checkpoint 683620 续训。
2. T06 _02 4 图 header 补 8 字段（#225）→ 发现未部署（#224）→ 部署后 max_turns=1 + 200 步完整局全过 → MAPS 6→10 回池（resume 685402）。
3. 日志分析发现 King 仍 603s 脏局 → 部署后剥三层（dragon/orange/red 无城，#226）+ ep_runner passable bug（#227）→ 完整局 120 步 r=183.1 err=no。
4. sync 工具固化 + project_rules 硬约束。

### 生产回池首批验证（09-14，resume 685402 起 36 局，进程 04:59 启动至 step≈689300）

#224-#227 修复 + sync 部署后，MAPS=10 全图池首批生产局（口径 = `[EP_TIME] err=no`，代码+日志实锤，非训练效果结论）：

| 图 | 局数 | steps 区间 | r 区间 | err=yes |
|---|---|---|---|---|
| King_of_Pain_h3m | 2 | 1 / 149 | 12.5 / 157.2 | 0 |
| T06 108X108_02（1v3） | 3 | 57-200 | 162.5-178.8 | 0 |
| T06 108X108_02_duel | 6 | 34-200 | 15.9-261.7 | 0 |
| T06 72X72_02（1v3） | 5 | 40-200 | 89.8-281.4 | 0 |
| T06 72X72_02_duel | 5 | 84-200 | 172.6-221.4 | 0 |
| T06 72X72_01 / _01_duel | 4 | 73-100 | 126.1-235.1 | 0 |
| T05 三图 | 11 | 66-74 | 138.9-156.7 | 0 |

- **零 SIGSEGV / 零 err=yes / 零挂死**：三张原致命图（72_02 系 header 挂死、108_02 系 SIGSEGV、King 三层连环）全部产出完整有效局。
- **King 生产首效**：1 局脏（steps=1/603s/obs_nz=0，方案 A `[FILTER]` 拦截不进 buffer）→ 随后 149 步/259s/r=157.2/obs_nz=348，`[GUARD_DONE]` 正常早停，#226 修复生产闭环（探针局 120 步 r=183.1 之外的首个生产局）。
- **TOWN_CAPTURE=4，全在 1v3 图**：108_02 step56、72_02 step39/step128、72_01 step92，均 `blue_hero_killed=[1,2,3]` +100（C 方案 proxy 在新 1v3 大图生效）；duel 图 0 次符合 #213 跳过逻辑。
- **HERO_DEATH=0**：T06 大图池 36 局继续 0 触发，T7.4 判据 1"全草地大图 ZOMBIE 结构性不可达"再添生产证据（#210/#226 方向），判据 1 仍挂起待 standardDefeat。
- **观察项（不断言）**：108_02_duel 2 局短终局（34 步/320s/r=15.9、41 步/335s/r=19.6，8-9.4s/步偏慢，无 GUARD_DONE/TOWN_CAPTURE/HERO_DEATH 任何终局标记，err=no），终局原因待攒样本定性（疑长战斗/卡顿后自然终局，非脏局）。

**关联**: 踩坑 #224（部署拓扑）/ #225（header 13 字段）/ #226（King 四层）/ #227（passable）；工具 `py/sync_maps_to_runtime.py`、`py/patch_t06_02_header_0914.py`、`py/patch_king_dragon_0914.py`、`py/patch_king_rebuild_0914.py`；治本 `py/vcmi_full_to_slim.py`、`regenerate_t06_108.py`、`regenerate_level5.py`。

## H3 双编译树判定 + vcmiserver/mlclient 构建部署拓扑 (2026-09-14, 踩坑 #228 闭环)

### 两棵源码树同名，改码前必须先判生产树（最大坑）
WSL 侧存在两棵同名近似树，极易改错：

| 树 | 构建目录 | CMAKE_HOME_DIRECTORY | 二进制时间 | 是否生产 |
|----|----------|----------------------|-----------|---------|
| `/home/administrator/vcmi-native` | `vcmi-native/rel` | `/home/administrator/vcmi-native` | rel/bin/vcmiserver = **09-11→09-14 11:45** | ✅ **生产/训练实际加载** |
| `/home/administrator/vcmi-native-build` | `vcmi-native-build/rel` | `/home/administrator/vcmi-native-build` | rel/bin/vcmiserver = 08-02（陈旧） | ❌ 不参与生产/训练 |

**判定生产编译树三件套（交叉验证，缺一易误判）**:
1. `strings /home/administrator/vcmi-native/rel/bin/vcmiserver | grep -c 'vcmi-native/server'` → 168；对 native-build 树同名产物 grep `vcmi-native-build/server` → 时间戳陈旧（内嵌的是**编译时**源码根路径，最硬证据）。
2. `grep CMAKE_HOME_DIRECTORY /home/administrator/vcmi-native/rel/CMakeCache.txt` → 指向哪棵源码树。
3. `ls -l --time-style=full-iso rel/bin/vcmiserver rel/bin/libmlclient.so` 看产物 mtime（对照最近一次重编时刻）。

> 教训：在陈旧的 vcmi-native-build 树分析会看到 `removeQuery` 游离实现 + `BattleResultProcessor` 用 `popIfTop`（header 声明还是注释、全树无调用点），从而误判"补丁没接线"；而生产 vcmi-native 树里 08-17 补丁本就完整自洽（header L37 有声明 + brp L404 调 removeQuery），只残留 `removalDone` 守卫这一处缺陷。**两树源码可能不同步，源码级改动前先在生产树 grep 确认。**

### 构建命令（不碰 libvcmi.so）
```bash
cmake --build /home/administrator/vcmi-native/rel --target vcmiserver mlclient -j8
# Unix Makefiles / RelWithDebInfo / ENABLE_ML=ON
```
- 产物：`rel/bin/vcmiserver`（可执行，仅此一份生产位）+ `rel/bin/libmlclient.so`。
- `libmlclient.so` 需**双副本**（Python 侧 `strategic_env.py` 4 处硬编码 `rel/bin/libmlclient.so`；历史 build/bin 也有副本）：
  `cp rel/bin/libmlclient.so /home/administrator/vcmi-native/build/bin/`，cp 后 `md5sum` 两处对齐，`chown administrator:administrator`。
- 改后清 `vcmi_gym/**/__pycache__`（ep 逐局加载，无需停训即生效，但本次改了 C++ 必须重启训练让新 vcmiserver 被拉起）。
- 备份后缀统一 `.bak.H3.20260914`（vcmiserver / libmlclient.so / 4 个 C++/py 源文件）。

### vcmiserver 与训练的进程关系
- 训练 `train_wsl2_ppo_v2.py`（systemd `homm3-train-v5.service`，system 级 enabled）→ 每局 fork `ep_runner_one.py`（一子进程一局）→ ep 内拉起/承载 VCMI（vcmiserver/libmlclient）。**局间 pgrep -x vcmiserver 可能为空**（reset/启动间隙），不代表卡死；判活看 `pstree -p <train_pid>` 有 ep_runner + `/tmp/hermes_ep_<trainpid>.log` 持续增长。
- 大图（T06 108X108_02 1v3，200 步）单局 400-600s 正常，勿把慢启动误判挂死。
- ep 收尾生产侧本就无条件 `os._exit(0)`（ep_runner_one.py L1261），规避真终局后 NK2 后台 makingTurn 线程与 connector shutdown 的析构竞态 SIGSEGV（rc=139）；**任何探针/独立脚本跑到真终局也必须 os._exit，不能 env.close()**。

### H3 败北信号终局通道（本次新增代码契约）
- `ML/strategic_state.cpp`: `adventure_process_turn` 入口 `if(userData) g_ml_player_cb=userData`（全局回调必须在此持久化）；`adventure_wait_for_turn` 每 25 拍（≈250ms）`shared_lock(CGameState::mutex)` 轮询 `gs.players`（**跳过 PlayerColor::NEUTRAL**，否则打野也算减员误触发），存活玩家≤1 → `fill_strategic_state(g_ml_player_cb)` 刷终局快照 → 返回 **-2**。
- Python `strategic_env.py`: `_adventure_wait` 识别 -2 静默 return（step 继续 `_read_state→game_over=2→reward→terminated`）；**reward 必须在实际生效的 shaping 分支核对**：NK2 分支曾提前 `return clip(r,-10,300)` 吞掉 -200（终局 state_value 退化为有界值），需在 return 前补 `game_over==1 +200 / ==2 -200`，clip 下限放宽到 -300。
- server 侧 `removeQuery()` 去 `removalDone` 守卫后每玩家各调一次 `onRemoval`；二次/重入安全由 `battleFinalize` 的 `finishingBattles.count(battleID)==0 return` 兜底，gdb 实机二次 onRemoval 无段错误。

**关联**: 踩坑 #228（完整根因/修复/验证）/ R7「编译部署归属实锤」(09-03)；探针 `py/probe_t06_gameover.py`（`--idle --blue_adventure_ai Nullkiller2`，红败秒回 go=2 r≈-226 rc=0）；补丁 `py/patch_h3_server_0914.py`、`py/patch_h3_souser_0914.py`。

---

## 2026-09-15：WIN-1 ⑤专项 + C2/P10 方案备料 + fog 语义核查 + systemd 口径统一

### ⑤ 200 步截断局专项（直接服务 WIN-1 达标判定）
- 只读工具 `py/analyze_trunc200.py`（口径对齐 check_win1_watch.py；`--last/--all/--map`；A 胜后空转/B 推进未竟/C 未打出去三分类 + 末 20 拍动作画像 + 同图截断/非截断对照）。
- 结论（全历史 1124 有效局 / 1v3 133 局）：截断 33/133=25%，**100% 为 B 类**（守卫胜+占矿后未 capture），零 A 零 C（无 ZOMBIE/ENDTURN_FUSE/END_TURN）→ 非策略退化。
- 结构卡点 = **T06_adventure_72X72_02.vmap 1v3：7/12=58%**，跨 6k 步指纹一致（r≈89.8-93.8，末拍方向2 占 76-80%，H=1.47）。决定性证据：同图成功局（127 步 r=274.6）与失败局（200 步 r=92.9）**前 51 步事件完全同构**（同矿 step43 + 同守卫 (23,20) step51 + 同一 TOWNSTALL block=(40,5)）；分叉在 stall 后：成功绕行遇蓝英雄 capture，失败 step108 起朝东撞墙 ~90 拍（蓝城 (69,2) 在东缘）。
- **提 250 步对此型无效（撞墙型非步数临界型）**；有效干预 = ①改图（蓝城挪离东缘/清 BFS 堵点，72_02 优先）或 ②修订判据（B 类 r≥150 非病态 / ⑤只数 C 类，当前 C=0）。⑤在改图/修订前结构性不可达 ≤20%，但不阻塞 WIN-1 聚合（①②③④已达标）。
- 附带关键事实：ep_runner T06 无条件覆盖 `move_to_force=200 + guard_done_steps=0`（ep_runner_one.py L134-136，命令行传 60/15 对 T06 无效）；capture proxy +100 不 break，胜后继续走到 200。

### C2 崩溃根因插桩（方案，零部署）
- `docs/方案_C2_崩溃插桩_20260915.md`：8 个历史崩溃点台账（启动期/地图数据/断言/工具/关闭期）→ 运行期崩溃几乎都是引擎断言（SIGABRT 有文本栈）或空指针（SIGSEGV 无栈），随机内存腐败型至今无实证；09-14 干净图池后零 SIGSEGV。
- 四缺口：rc 裸数字不翻译信号名 / ep_log 逐局覆盖 / core 被 WSL pipe 接管且 ulimit -c=0 / server 内 stderr 重定向（fprintf 不可见，#134）。
- 三级方案：L0 纯 Python（rc→信号名、崩溃局 ep_log 归档 crashlog/、词表补 Segmentation fault、监控计数，建议随 D3 同窗口）；L1 复发时临时 core/gdb（core_pattern 改 `/tmp/core.%p.%e` + ulimit，排查完恢复 wsl-capture-crash pipe）；L2 C++ 信号 handler backtrace 写显式 fd（最后手段，走 .so 铁律）。

### P10 target_list 加权排序（纯设计，零部署）+ 现状机制存档
- `docs/方案_P10_target加权排序_20260915.md`。
- **现状机制（代码实证，存档防再查）**：
  - C++ `ML/strategic_state.cpp` fill_target_list（L197-246）：候选仅未占矿/资源/篝火/宝箱/宝物 5 类，**纯曼哈顿距离 sort top-8**，写 `target_list[8][8]`（type,idx,x,y,z,dist,log2(guard+1),flags=0）；不含城镇/蓝英雄；guard 只记录不参与排序。obs 映射 `obs[3251:3315]`（strategic_env.py L411）。
  - Python ep_runner_one.py 动作 24 段是**五层硬编码 if/else**：守卫（get_guards 静态 vmap，15 格，L654-686，blacklist 状态机）＞ 矿（type=1 最近，L688-699）＞ 回城取兵（obs 城镇段 recruit_mask，≤25+BFS，T06 限次 2）＞ 蓝城（get_objectives 静态，全图 BFS plen，mine_taken 门控，T06 `_t06_direct` 绕过）＞ target_list 全局最近兜底；护栏 = 粘滞/move_stall 6 步/BFS 不可达跳过/dyn_blocked。
  - 蓝英雄动态信息**在 obs 全知可读**：英雄段 `obs[128:336]` = 8×26（owner/pos xyz/movement/level/total_power/is_garrisoned…，StrategicHero 字段）；城镇 `obs[336:480]` = 8×18。
  - 已实锤缺陷：大图 top-8 被近资源挤占致矿引导断链（0909 `_t06_direct` 补丁）、近资源压矿（0829 硬优先级补丁）、guard_power 填而不用、**蓝英雄不在目标池（72_02 stall 后撞墙 90 步的承接缺失）**。
- 设计要点：Python 旁路统一打分器（候选全量化 vmap 缓存 + 蓝英雄动态入池 + BFS plen + 战力 logistic 可打性 + 阶段调制），硬约束层沿用现有黑名单/stall；**零 obs 变更零重编**，`--target_chain {legacy,scorer}` 开关，离线单测→探针局→T04/T05→T06 灰度；真实 H3 部署时蓝英雄位置须降为 explored/可见集。

### fogOfWarMap 语义（T5.4 遗留核查，已消项）
- **TeamState.fogOfWarMap = explored 累积语义，非"当前可见"**：枚举 ETileVisibility 仅 HIDDEN/REVEALED；英雄移动 `TryMoveHero.fowRevealed` 只收 fow==0 新格、apply 置 1（GameStatePackVisitor.cpp L543-545），只增不清；清 0 仅 ViewWorld/ViewAir 法术失效（CGameHandler.cpp L752-754）与网络回滚。
- obs[1155:3203] global_explored 命名正确；local_tiles 以 explored 为黑雾门控、门内对象/守卫实时直读；引擎头注释 "true-visible" 系误导。要"当前帧可见"需按 sightRadius 另算，引擎无现成 per-tick 图。详见 `docs/源码分析地图.md` 待确认第 4 条。

### D3 开局熵 bonus 补丁（备料，等自然重启窗）
- `py/d3_entropy_bonus.patch`（train_wsl2_ppo_v2.py 5 hunk）：熵系数从常数 0.05 改 `0.05*(1+exp(-total_steps/2e6))`（0 步 0.10 / 200 万 0.068 / ∞0.05），warmup 200 万步；日志行尾在 `time=...s` 之后追加 entc/ent（analyze 脚本正则无尾锚，位置不能错）。
- 应用：`wsl -u root systemctl stop homm3-train-v5` → cp .bak_d3_日期 → `patch -p1 < py/d3_entropy_bonus.patch` → py_compile → start；回滚 `patch -R`。当前 step 应用瞬间系数 ≈0.085。可与 C2-L0 合并为同一停启批次。

### 运维
- systemd 口径 09-15 全面统一（system 级 enabled unit，禁 --user），详见踩坑 #229；存活判据沿用 #201 三件套。
- C1 工具 `py/eval_promo.py` 已加固（独立进程组+看门狗 SIGKILL+实时事件），全 profile 待训练低峰跑。

---

## 2026-09-15：P10 target_scorer 实施 + 灰度启用（零重编 Python 旁路打分器）

### 背景与定位

P10 方案（`docs/方案_P10_target加权排序_20260915.md`）解决 72_02 卡点（58% 截断）+ WIN-1⑤ 联动：target_list 排序纯曼哈顿 top-8 无价值/威胁加权，蓝英雄完全不在目标池（D4），蓝城 stall 后无目标承接 → 失败局东向撞墙 ~90 步。设计形态 = Python 旁路统一打分器（`py/target_scorer.py`），OBS 3464/动作空间零变更（铁律），零 .so 重编，`--target_chain {legacy,scorer}` 灰度开关。

### 核心产物 `py/target_scorer.py`

**候选池 5 类**（相对 C++ target_list 的 D4 补全）：

| 候选类 | 来源 | 基础价值 V |
|--------|------|-----------|
| 矿/资源/篝火/宝箱/宝物 | C++ target_list obs[3251:3315] 8×8 | 30/10/12/20/25 |
| 蓝英雄 | obs[128:336] 8×26（total_power 直读） | 100 |
| 蓝城 | obs[336:480] 8×18 | 80 |
| 己方取兵城 | obs[336:480] 8×18（recruit_mask 非 0） | 35 |
| 静态守卫 | vmap 注入（get_guards） | 45 |

**打分公式**：

```
score = w_type*V + w_win*Δcap*V + w_pow*F*(V+20) - w_dist*g + w_stick*stick - p_phase - budget_pen
```

- `Δcap`：蓝英雄=1.0 / 蓝城=0.8 / 其他=0.0
- `F`（可打性）：logistic 战力差，`power_feasibility(power_self, power_c, w)` ∈ [-1,1]；资源类恒 +1；蓝英雄直读 total_power；守卫/蓝城 half-self 近似
- `g`：BFS 真实路径长度（`bfs_full_dir` 非 None 时），不可达剔除；守卫格/蓝英雄格 passable=0 不入 BFS（贴脸）
- **经济期远目标衰减（#232 修复）**：`phase=="economy" and g>50` 且蓝英雄/蓝城 → `V *= 0.2`，防止 `w_win` 无条件下拉远目标开局锁死
- `p_phase`：阶段惩罚（economy 罚蓝英雄/蓝城，capture 拉满）
- `budget_pen`：步预算惩罚（远候选 plen > step_budget×0.5 加罚）
- `stick`：粘滞 bonus（当前目标未 stall → 强化保持）

**硬约束打分侧过滤**：
- BFS 不可达剔除（方案 §3.3 硬约束）
- 守卫/蓝英雄贴脸不走 BFS
- `man > 30` 跨图剔除
- 取兵 `man ≤ 25`；`own_town_limit`（T06 超限整类剔除）
- `guard_blacklist` / `dyn_blocked` 透传

**obs 段偏移常量**（冻结 3464）：

```python
OBS_TL_OFF   = 3251   # target_list 8×8
OBS_HERO_OFF = 128    # 英雄段 8×26
OBS_TOWN_OFF = 336    # 城镇段 8×18
OBS_ND_OFF   = 3330   # C++ 全图 BFS next_dir[8]
OBS_PAS_OFF  = 3211   # 8 方向 passable
H_F_ID, H_F_OWNER, H_F_X, H_F_Y, H_F_Z, H_F_LEVEL, H_F_POW = 0, 1, 2, 3, 4, 5, 10
T_F_ID, T_F_OWNER, T_F_X, T_F_Y = 0, 1, 2, 3
```

### ep_runner_one.py 集成（L675-717 新增 scorer 分支）

- **argparse 7 参数**（L133-144）：`--target_chain {legacy,scorer}` + `--ts_w_type/--ts_w_win/--ts_w_pow/--ts_w_dist/--ts_w_stick/--ts_margin/--ts_temp`
- **lazy import**：`_target_scorer = None`，scorer 分支首次调用时 `importlib.import_module("target_scorer")`，`sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")`
- **scorer 分支**（L675-717）：
  1. `power_self = int(obs[base + 10])`（active hero total_power，H_F_POW=10）
  2. 构造 `_phase`（T06 图直接 capture，否则 mine_taken→capture 否则 economy）
  3. `score_candidates(...)` → `pick_from_scored(...)` → 赋值 `move_target/move_stall/next_dir_idx/move_guard_target/move_town_target/move_town_bfs`
  4. `[SCORE]` 诊断日志（pick 坐标/类型/分值/路径长/V/F/runner_up 分值）
  5. `pick is None` → tx 保持 None → L916 zombie a=10（无候选兜底）
- **legacy 段**（L718-874）：原五层 if/else 整体缩进 +1，零行为变化

### 训练脚本透传（#234）

`train_wsl2_ppo_v2.py`：
- L196：`cmd.extend(["--target_chain", "scorer"])`（P10 灰度启用，默认 legacy 零行为变化）
- L222：`[SCORE]` 加入 `highlights` 主日志转储词表（否则 ep_runner 子进程日志对主日志不可见）

### 灰度启用与验证（09-15）

**离线 7 项测试全过**（`py/test_target_scorer.py`）：
1. 候选完整性（5 类全部入池）
2. 打分单调性（蓝英雄>蓝城>守卫>矿>资源堆）
3. 72_02 卡点（蓝英雄入池且打分最高，legacy 完全不在池）
4. 硬约束过滤（BFS 不可达/黑名单/取兵限次整类剔除）
5. 步预算惩罚（远候选加罚）
6. 粘滞 bonus（当前目标未 stall → 强化保持）
7. 阶段调制（economy 罚蓝英雄/蓝城，capture 拉满）

**灰度首日首局（#232 修复后）**：
- King_of_Pain_h3m step 28 选 `own_town`（plen=1 近距离取兵）而非远蓝英雄（plen=64，修复前会被锁定），守卫战斗 +100，115 步正常终局，`r=119.3` 正收益。
- T05_adventure_36X36_01 经济期远目标不再碾压，正常节奏恢复。

**灰度纪律**：
- 默认 `--target_chain legacy` 零行为变化，scorer 启用需训练脚本显式透传
- 灰度观察期 ~40 局，重点指标：72_02 截断率（目标 ≤20%）、蓝英雄/蓝城进目标池频率、`[SCORE]` 日志 pick 坐标分布
- 回退：`train_wsl2_ppo_v2.py` L196 改 `["--target_chain", "legacy"]` + 清 `__pycache__` + 重启

### 关联

踩坑 #232（经济期远目标碾压）/ #233（坐标变量混用）/ #234（训练脚本透传）/ WIN-1⑤（72_02 卡点拍板转 P10）/ `py/target_scorer.py` / `py/test_target_scorer.py` / `ep_runner_one.py` L133-144/L675-717 / `train_wsl2_ppo_v2.py` L196/L222。


## P8-C 收尾: QueryReply 197 组包 + green headless null-ENGINE 段错误根治 (09-16)

**背景**: T13.10 P8-C 决策接入已闭环 (09-11, MoveHero/Build/Recruit 实机 PASS), 剩余 = QueryReply(197) 实战样本。本轮一次做完 2.1-4.2 + 遗留 green 段错误根治。

### 1. QueryReply(197) 双布局 + 8B/9B 回退 (纯协议工作)

**C++ 权威**: `lib/networkPacks/PacksForServer.h` `QueryReply = QueryID(qid LVarInt) + std::optional<int32>(reply)`. `BinarySerializer::save(std::optional<T>)` present = 1B(0x01)+int32; **absent = `save(static_cast<uint32_t>(0))` 写 4B** (非 1B 0x00). Python 侧 8B absent / 9B present 为两种 candidate 布局, 实机 197 无 fishy = 受理.

**脚本** `py/p8/p8c_query_reply.py`:
- 双数据源拿真实 qid: ① server tail `[QUERY-DIAG] qid=N player=X type=...` (VCMI_QUERY_DIAG=1 编译宏+运行时双控, fork 1.8 `server/queries/QueriesProcessor.cpp` 注入) 为主 ② client 88/154-160 query 包体首字段 qid 为辅
- 组包: 8B absent 首发; 197 鱼线 ("applying 10QueryReply...fishy") 或 10s 无 PackageApplied 回流 → 9B present 回退一次
- 判据: ① bad keyword 只数 197 鱼线 (Build/Recruit 占位 OI 的 fishy 记录不计入) ② 客户端 88 PlayerStartsTurn 包体 queryID = 上一回合 qid 残值, 真实 qid 一律以 QUERY-DIAG 为准 ③ 仅我方 (MY_COLOR) qid≠-1 才回送, 他方只记录 ④ 断线后仍 tail 5s 抢 197 组包窗口

**两次 clean run (达标)**:
- run10: DIAG 抓到 qid=2/red (MapObjectVisitQuery) → 8B 帧发出 → 197 zero fishy = **PASS(replied)** (唯一抓到真实 qid 回送的 run)
- run12: qid=-1 only + server 16PST广播=3≥2 + 197 zero fishy = **PASS(qid=-1 only)**

**8B absent vs C++ uint32 路径字节不匹配疑点** (遗留): 实机 8B 帧 server 无 197 fishy = 受理 (run10 实证), C++ absent 走 uint32(0) 4B vs Python 1B 0x00 理论不匹配, 9B present 为回退候选, 待 197 fishy 实锤时验证.

### 2. green(NK2 client) runNetwork 段错误根治 (踩坑 #215, vcmi-native commit 65515ef24)

**现象**: 每次 clean run 复现 green(NK2 client, headless/testmap-onlyai) 在 server 广播 16PlayerStartsTurn #2 时 runNetwork 线程 `segfault at 80` (dmesg `mov r13,[rax+0x80]` rax=null), 进程消失 → server SHUTDOWN (host=python 仍在但 activeConnections 减少触发) → Python 连接 RST → 对局推进中断.

**根因 (gdb core 实锤, 非 dmesg 符号化误导)**:
- 首崩点 `client/CServerHandler.cpp:697` `startGameplay → ENGINE->discord()`: headless 模式下全局 `ENGINE`(unique_ptr<GameEngine>) 为 **null** (`clientapp/EntryPoint.cpp` L297 `if(!headless) ENGINE=make_unique`), `unique_ptr<Discord>::operator*` this=null → null+0x80 (GameEngine 类内 Discord 成员偏移) = `segfault at 80`
- 二次崩点 `client/Client.cpp:536` `removeGUI → ENGINE->windows()` (断线回收路径, 同样 null-ENGINE)
- dmesg 符号化坑: "segfault at 80" 的 80 = 解引用偏移非函数偏移, 直接 addr2line 落在 inlined 的 `__Vector_base<char>` 是误导, **必须 gdb core 拿真实调用栈**

**修复**: `client/CServerHandler.cpp` + `client/Client.cpp` 全部裸 `ENGINE->` 解引用 (discord/windows/interfaceMutex) 加 `if (ENGINE)` 守卫 (共 14 处), sendRestartGame/sendStartGame 的 CLoadingScreen 双分支收进 `if (ENGINE) {}` 消 dangling-else, 重编 vcmiclient.

**验证 (修后 clean run)**: 16PST 广播 3→**4** (green 活到第 3 回合), 无 "Connection lost", dmesg 无新 runNetwork segfault, 无新 core 落地. BuildStructure 占位 OI 的 fishy 仍存 (不计入 197 判定).

### 3. RecruitCreatures(187) 签名坑 (踩坑 #214)

`RecruitCreatures(tid=1, bid=30, count=1)` → `TypeError: got an unexpected keyword argument 'bid'`. 正确签名 = `RecruitCreatures(tid, dst, crid, amount, level=0, player, request_id)`, 字段序 = tid(ObjectInstanceID 源建筑) + dst(ObjectInstanceID 英雄) + crid(string jsonKey) + amount(ui32) + level(si32), 与 185 Build(tid+bid LVarInt) 完全不同. 参考 `py/p8/p8c2_town_chain_probe.py` L110.

### 4. 交付物

- `py/p8/p8c_query_reply.py` (主仓 commit 1eb664b)
- `openspec/specs/vcmi-protocol/spec.md` QueryReply 8B/9B 双布局 + "双布局回退" Requirement + 2 Scenario + Notes (commit 1eb664b)
- 踩坑 #213 (green 段错误+8B/9B 布局疑点, 主仓 commit 7ae9ae7 补充) / #214 (RecruitCreatures 签名) / #215 (null-ENGINE 根治, 主仓 commit dfdc532)
- vcmi-native commit 65515ef24 (client/CServerHandler.cpp + client/Client.cpp, 未推送 mmai-ml 分支)
- 当前任务清单第七章 剩余工作②③标完成 + 遗留①标 ✅已修复 (commit dfdc532)

### 关联

踩坑 #213/#214/#215 / spec `openspec/specs/vcmi-protocol/spec.md` / `py/p8/p8c_query_reply.py` / vcmi-native 65515ef24 / 上游 P8-E 人机混局 (09-15) / P8-D 双机部署 (09-14).

## WIN-1 capture 观察窗 40 局临界复核 + P8-C green null-ENGINE 根治 (09-16)

**背景**: P8-C 收尾 2.1-4.2 完成 (commit 1eb664b/7ae9ae7) + green 段错误根治 (踩坑 #215, vcmi-native 65515ef24) 后, WIN-1 capture+100 观察窗继续攒局。

### WIN-1 攒局: 40 局临界越过, 判据①仍 0 = 实质卡点
- **40 局临界**: 09-16 白天 ep=40 (step=725195) 本窗已攒满 40 局严格聚合 (切窗锚点 L=97434 'Loaded train state' step=719852 起)。
- **判据① TOWN_CAPTURE 在 40 局大样本下仍=0** (主日志本窗 0 + runner 0), 三义性=生效但本窗 0 触发 (capture proxy 双拍确认修复在位, duel 图 blue_hero_killed 非空拍持续出现, 但真实全灭+占城从未走到"占城+双拍确认"那一步)。**40 局临界已过仍 0 = 实质卡点, 非挂起**——无脑续攒大概率还 0。
- **判据② GUARD**: 本窗仅 2 次接战全 won +100 (比率 2/2=100% 但样本极小, 分母守卫局数不足), 需下窗攒厚。
- **判据④ 经济 RECRUITED=758 维持; ⑤ duel 截断全 B 类 C 类=0**。
- **下一步方向**: 深挖 blue_hero_killed 后占城链路为何未触发 (双拍确认被空拍吞 / 占城 OI 未易主 / 击杀后英雄未走到蓝城), 再决定继续攒 vs 切 WIN-3 ① 72X72_02_duel 单图轴。子 agent 判据对齐分析 (18:13 派发) 被用户"取消所有任务"中断, 占城链路深挖未出报告, 待重启。

### P8-C green null-ENGINE 根治 (踩坑 #215, 已 commit)
- **根因 (gdb core 实锤)**: client 框架 headless 路径 null-ENGINE 解引用——首崩点 `client/CServerHandler.cpp:697 startGameplay → ENGINE->discord()` (headless 下 EntryPoint L297 `if(!headless) ENGINE=make_unique` 使 ENGINE 恒 null), 二次崩点 `Client.cpp:536 removeGUI → ENGINE->windows()`。dmesg "segfault at 80" 的 80=解引用偏移非函数偏移, 直接 addr2line 落在 inlined `__Vector_base<char>` 是误导, 必须 gdb core 拿真实调用栈。
- **修复**: 14 处裸 `ENGINE->` 加 `if(ENGINE)` 守卫 + 重编 vcmiclient。验证: 16PST 广播 3→4 (green 活到第3回合), 无 Connection lost, dmesg 无新 segfault。
- **状态**: vcmi-native commit `65515ef24` (mmai-ml 分支, 本地未推, ahead 11 / behind 8); 主仓归档 commit `dfdc532`/`c7f7ba8`。

### 踩坑沉淀
- #215 green null-ENGINE 根治 / #216 8B absent vs C++ uint32 字节不匹配 (实机 8B 无 197 fishy=受理, 9B 回退候选待 197 fishy 触发) / #217 reasonix-cli WSL 跑 Windows .exe 不通 + --dir 指 WSL 路径无效 (09-16 实测 15s run_done ok=false, WSL C++ 仓一律主会话手动 gdb+patch)

### 关联
踩坑 #215/#216/#217 / 任务清单 WIN-1 进度核查 (09-16 深夜 ep=103) / vcmi-native 65515ef24 / 知识库「P8-C 收尾」章 / WIN-3 ① 72X72_02_duel 单图轴 (待 WIN-1 达标)。

## WIN-1 capture 归零定谳（没杀到）+ 击杀激励重设计批次A开窗 (09-16)

### 归因核查（零干扰，三层证据链）
- **问题**：最后 `[TOWN_CAPTURE]` L89715 (step 695056) 后跨 4 run 段 0 触发，与 5c2f2b8（#231 双帧确认，step 695099 上线）时间线重合 → 假设 A（修复消除假阳性暴露真实能力缺口）vs 假设 B（双帧过严把真击杀也挡了）。
- **证据1**：commit 5c2f2b8 实勘 218/218 TOWN_CAPTURE 严格战斗配对 100% 空拍误报；L89715 恰为上线前最后一次误报，归零起点与上线严格对齐。
- **证据2（决定性）**：battle_quality_events.log（持久 append-only，834 行）全部 9 条 BHERO_KILL 集中文件头 L1-9 且 **live_slots=0** —— 按修复后打点条件 `if _bnow:`（非空拍才打点），只能是修复前旧代码空拍期痕迹；修复后 **0 单拍差集 / 0 confirmed** —— 双帧确认从未收到过需要裁决的挂账，"过严挡真"无从谈起。
- **证据3**：修复后 HEROSEG_EMPTY 空拍仍持续出现且被正确冻结无一误发 —— 空拍现象还在，是 proxy 在挡。
- **结论**：**"没杀到"（真实击杀基线=0），历史 218 次 capture 基线全部为假**。残余盲区仅"击杀发生在 ep 最后一个非空拍"（BHERO_KILL 首非空拍即留痕，几十局 0 条，概率趋零）。
- **方法论沉淀**：proxy 归零归因要**分层取证** —— 发奖层（双帧 confirmed）与打点层（单拍 observe-only BHERO_KILL）分开看；持久旁路日志的单拍差集是"真击杀是否发生过"的下界证据，双帧发奖归零本身不能区分 A/B。

### 击杀激励重设计（方案 docs/方案_WIN1_击杀激励重设计_20260916.md）
- **行为链**：接近（P-H1 蓝英雄接近梯度，新低制 max(0)+cap 25）→ 接战（P-H2 坐标重合=走上敌英雄格必触发战斗，每局每敌幂等 +15）→ 击杀（P-H3 逐 id 双帧确认阶梯，首杀+40/后续+30）→ 全歼（proxy +100 不动）→ 占城（capture reward 不动）；击杀轴满贯 ≈+215 防通胀。
- **护栏**：空拍冻结（#231 口径 `_bnow` 前提）/ duel 图排除（与 proxy 同口径）/ 新低制防往返刷分 / 步罚 -0.1 + death_penalty -50 不变（送死换 +15 接战奖净亏）。
- **实装**：ep_runner_one.py 5 参数默认全 0 零行为（argparse + ep 级状态 + proxy 块内 P-H3 + 独立 P-H1/H2 块 + `[BHERO_GRAD]` ep 末汇总）；train_wsl2_ppo_v2.py `WIN1_ENV_ARGS` 环境变量注入（HOMM3_BLUE_HERO_GRAD/CAP + 批次B 三个预留，run_episode cmd 透传，启动打 `[WIN1_BATCH]` 行）。
- **启动脚本**：py/restart_train_v5_win1_batchA.sh —— 与原版唯一差异 = unit 注入 `Environment=HOMM3_BLUE_HERO_GRAD=0.2 / HOMM3_BLUE_HERO_GRAD_CAP=25`；回退 = 原版 restart_train_v5_sys.sh（无注入）。
- **开窗记录（09-16 20:17）**：优雅停 `Saved (step=736372)` → 主日志 `[WIN1_BATCH] env-injected runner args: --blue_hero_grad=0.2 --blue_hero_grad_cap=25` → `Loaded train state (step=736372)` 接续 → 首局 ep_runner 存活（VCMI 查询链正常）。
- **批次A攒窗判据（~40 局）**：蓝英雄最小距离 p50 128→<64（`grep BHERO_GRAD` 取 final_min_d）/ avg_r 跌幅 <20% / WIN-1 ②④⑤ 不塌；回退线 = 判据塌跑原版脚本。
- **踩坑**：#249（PowerShell `$var` 插值致 grep 静默空结果，本次多排查 2 轮）。

### 关联
踩坑 #231/#249 / 方案_WIN1_击杀激励重设计_20260916.md / 任务清单 WIN-1（09-16 晚开窗条目）/ T7.5 S2 前置（WIN-1 达标后才轮到）/ WIN-3 难度轴（错窗互斥）。

## 批次A 收口 + 批次B/A3 同窗部署 + A4 证伪重定性 (09-17)

### 批次A 结算（生效窗 44 局, step 739253→745008+, 三判据全绿）

- **窗口语义**：L101674 首开窗段（22 局）ep_runner 旧代码零 BHERO_GRAD = P-H1 未生效（踩坑 #252），判污染段不计；**生效窗 = L102375 resume 起新代码**。
- ① 贴近 p50=47.0 <64（基线128）✅ ② 滚动 avg_r 0.6→0.8 持平 ✅（duel 对照组 P-H1 关闭 avg -157~-168 实锤大负值与本轴无关）③ 护栏不塌（RECRUITED 877 / 局长 mean=131 / 截断 20%）✅ KL 2/2<1.0。
- 工具：`py/win1_batchA_agg.py`（窗口定位修复版，自动取最后 WIN1_BATCH 行 = 生效窗起点）/ `py/win1_guardrail_probe.py`（护栏计数）。

### 双定谳（当日两大归因）

- **A2（P-H2 判据）**：`_d1==0` 同格结构性不可达（#143 事实3 误读，踩坑 #250）→ contact_d 参数化，批次B 注 2（曼哈顿≤2 = 8 方向世界真 8 邻；注意 ≤1 只是 4 邻）。
- **A4（"卡死段"证伪）**：act 长同向段 = MOVE_TO(24) 执行时被改写为方向动作（L906-957），是直线奔袭非卡死（踩坑 #251）；T05 全负唯一根因 = **own_town 贴脸 89.5 恒定霸屏回城循环**（38-59 段 pick 100% own_town，TOWN_VISIT 节律 ~33 步/次 = 冷却30+窗4，局均 3.0 次 vs T06 1.0）→ 根治转 A3。

### 批次B + A3 同窗配置（09-17 部署, `py/restart_train_v5_win1_batchB.sh`, 8 Environment）

| 参数 | 值 | 语义 |
|---|---|---|
| blue_hero_grad / cap | 0.2 / 25 | P-H1 保留（行为链完整） |
| blue_hero_contact_r / **contact_d** | 15 / **2** | P-H2 接战塑形（邻域判据修复） |
| kill_r_first / kill_r_next | 40 / 30 | P-H3 击杀阶梯（双帧确认） |
| **own_town_decay / max_visits** | **0.5 / 4** | A3：V×0.5^min(visits,3) 封底3次 + 空撞拉黑（[TOWN_EMPTY]） |

- **A3 机制**：窗开启记 tid+兵力快照 → 窗完成 visits+1 → army power 段延迟一帧复核（零增量 → 拉黑本局）；scorer 候选4 加 blocked/max_visits 过滤 + visits/decay 注入。离线自测 `py/a3_selftest.py`。
- **首局实证**：[TOWN_EMPTY] town=13（开局取兵窗空撞当场识别）→ own_town 剔除 → pick 转矿(74.5) → **r=+98.4**（基线 -165~-337），74 步收局。
- **双轨判据可分**（同窗纪律依据）：批次B 看 BHERO_CONTACT/BHERO_KILL/TOWN_CAPTURE；A3 看 own_town pick 行数（基线 589→<100）/ TOWN_VISIT 次数 / TOWN_EMPTY / T05 avg_r 回升。
- **回退链**：批次B 塌 → batchA 脚本（仅 P-H1）；A3 异常 → 删 HOMM3_OWN_TOWN_DECAY/MAX_VISITS 两行；全关 → restart_train_v5_sys.sh。

### 残余观察（不立项）

- duel 自由期 22/22 停滞（疑贴脸僵局：min_d=2 机械下限 + 敌格 blocked 无路可走）→ 批次B contact_d=2 改变激励面后自然复验。
- 自由期碎片化移动被 econ 每 40 步 4 步提醒插穿 act_loop 检测窗 → A3 斩断目标回流后复查。
- [ECON] first BUILD_2 全窗 0 条（T05/T06 act20 强制轮换零触发）→ BUILD 动作无效嫌疑待查。

关联：踩坑 #250/#251/#252 / `docs/方案_own_town重复访问衰减_20260917.md` / `docs/备料_T05引导期卡死熔断_20260917.md`（证伪归档）/ `py/a4_stall_analyze.py`（名义轨迹审计工具） / `docs/已完成任务.md` 09-17 两条 / 方案_WIN1 §4（contact_d 增补行）。

---

### 09-17 OBS-3 登记改述 + A2 攻击步旁路方案（截至 2026-09-17）

**OBS-3 旧描述"aggression 遗留"方向已证伪，改述如下**：

- 原登记：OBS-3 T06 守卫战斗未触发（aggression 遗留）
- 09-17 预研定谳（`docs/预研_OBS3英雄战斗触发链与BUILD链_20260917.md`）：引擎 `CGameHandler::moveHero → blockingVisit() → objectVisited → CGHeroInstance::onHeroVisit → gameEvents.startBattle` 链**无条件触发战斗，无 aggression 开关**；真闸门 = Python 侧 passable 掩码封锁敌格（三方结构性不可达）+ 引导层 MOVE_TO 贪心只走 `pas[d]==1`，蓝英雄格 `passable=0` 被完全堵死。
- 改述为：**"Python mask/引导层缺攻击步"**——passable 掩码 + MOVE_TO 贪心两处堵点，非引擎 aggression 问题。

**A2 攻击步旁路实现（Python 零重编，复用守卫特判同族模式）**：

- 改动文件：`ep_runner_one.py`（argparse 新增 `--blue_hero_attack_bypass` int 默认 0 / `--attack_f_min` float 默认 0.0；状态变量 `move_blue_hero_target`/`blue_hero_id_target`/`_attack_tried`；MOVE_TO 执行段蓝英雄攻击步分支）+ `py/target_scorer.py`（蓝英雄候选 dict 加 `hero_id`；`pick_from_scored` 返回 dict 加 `blue_hero_id`）+ `train_wsl2_ppo_v2.py`（`WIN1_ENV_ARGS` 映射补 `HOMM3_BLUE_HERO_ATTACK_BYPASS`→`--blue_hero_attack_bypass` / `HOMM3_ATTACK_F_MIN`→`--attack_f_min` 两条）
- 护栏：① 旁路总开关默认 0 零行为；② 战力 logistic F 阈值（`attack_f_min`，打不过不进入）；③ `_attack_tried` 幂等集合（本局已下发的蓝英雄不重复）；④ 送死 −50/−200 兜底（BHERO_KILL 双帧确认 + BHERO_CONTACT 已有时序）
- 触发条件：`move_blue_hero_target=True`（scorer 链选中蓝英雄候选）且 `d ≤ blue_hero_contact_d`（默认 2）且 `F ≥ attack_f_min`
- 方向码：绕 over passable 强制下发朝蓝英雄格方向（与守卫特判 `pas[d] or move_guard_target` 同族，扩展为 `pas[d] or move_guard_target or move_blue_hero_target`）
- 日志：`[BHERO_ATTACK]` 双写（stdout + `bhero_events.log`）
- 冒烟前注意：两次文档反转教训（#250 d==0 不可达 / #252 子进程输出落窗）→ 以引擎实机行为为最终准，部署前必须先做 72_01 单局手动冒烟（`--blue_hero_attack_bypass=1`，验 `[BHERO_ATTACK]` 埋点 + CBattleQuery + R6 onnx 结算 `state.battle_result` 非 0）
- 方案文档：`docs/方案_攻击步旁路_20260917.md`
- 踩坑：#254（`WIN1_ENV_ARGS` 缺 A2 参数映射致 ep_runner 收不到 `--blue_hero_attack_bypass`，scorer 链选中蓝英雄后贪心回退全 blocked → 引擎拒绝；`Cannot move hero, destination tile is blocked!` 反复出现）

**指针**：`docs/方案_攻击步旁路_20260917.md` / `docs/预研_OBS3英雄战斗触发链与BUILD链_20260917.md` / 踩坑 #254 / `ep_runner_one.py`（argparse L85-168 / MOVE_TO L947-1021）/ `py/target_scorer.py` / `train_wsl2_ppo_v2.py`（`WIN1_ENV_ARGS`）
