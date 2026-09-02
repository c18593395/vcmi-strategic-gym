# 知识库 — HoMM3 全盘操盘 AI（体系总索引）

> 本文件是项目文档体系的**总索引**（2026-08-31 重构）。知识库内容分三层，请按需取读，勿在单文件内堆砌。
> - **稳定参考**：结论性内容，就地修订，标注截至日期。
> - **问题登记册**：踩坑点，每条带状态字段（✅/⚠️/❌/🔄）。
> - **日期工作日志**：每轮会话一份，append-only，永不回编。
>
> **约定（AI 必读）**：收到“保存知识库”→ 追加到本文件末尾「待整理」区（不自动分发到子文档，由用户定期自行归档）；收到“保存踩坑点”→ 追加到 `WSL踩坑点.md` 末尾「待归档新增」区（不自动分发）；收到“记日志/今天进展”→ 写 `WSL日志/YYYY-MM-DD.md`（新日期新建一份）。模型读取本索引后应**自动取读下方子文档与日志目录**获取完整内容。

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

## 待整理（收到“保存知识库”时追加于此）

> 此区为新增知识暂存区。用户定期自行归档到上方「一、稳定参考」三个子文档后，再从本区移除。新增内容请尽量带“截至日期”与“结论”。

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
