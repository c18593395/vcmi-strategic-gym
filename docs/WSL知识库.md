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

- **中断形态**: systemd unit 06:35 被外部 stop + 用户 09:43 前台终端启动 (PID 400 pts/0) → 该终端实例随后死亡, keepalive 亦丢 → 16:09 发现双 inactive (踩坑 #135 恢复序第二次实战: 补挂 keepalive → restart_train_v5.sh → grep resume 点)
- **resume 锚点**: checkpoint 555165 vs 日志残留 556410 (损失 ~1245 步 ≈10 局, 非优雅中断正常损耗); resume 后 5h+ 稳定 125 局零 ZOMBIE
- **前台跑法风险定论**: 前台终端实例**无 systemd 存档兜底**, 终端一关训练即死且 checkpoint 停在最后一次自动存档 — 训练一律走 `py/restart_train_v5.sh` 后台 transient unit (keepalive + 存档双保险)

### 多 resume 日志窗口统计套路 (踩坑 #136 配套)

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

### 登记规范 (踩坑 #137)

- "上游修复摘取 → 待重编部署"类任务, 登记前必须双确认:
  1. **改动文件 → target**: 看 `AI/<目录>/CMakeLists.txt` 确认源码归属 (AI 下多 AI 库并存: BattleAI/EmptyAI/MMAI/Nullkiller2/StupidAI)
  2. **运行时 → .so**: 看 train py `--xxx_ai` 参数推 lib<名>.so 加载链
- 同形不同源: NKAI/NK2/MMAI 三个词指三代 AI 库, 文档与任务登记中禁混用

### 开机恢复实录 (09-07 晚, #135 恢复序第三次)

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

### DLL 修复流程 (踩坑 #138)

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
| 官方 VCMI + ModelAI.dll | 官方 client + fork AI | MSVC vs GCC name mangling 不兼容 (踩坑 #139) |

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
- **踩坑 #134 二次复现**: stop 后 `systemctl start` 报 not found (transient unit 已收集消失); 且 **is-active 对已消失 unit 输出 `inactive` (exit 4) 不报错** — 停机确认要看 journalctl + `Saved STATE_PATH`, 勿信 is-active
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
- **第三崩溃待立项 (09-10 gui12 浸泡 day=31 后)**: 主线程 `0xC0000005 读 0x10`, RIP=exe+0x20c09f (fn 0x20bf60) — `getter(0x1a47c0)->fieldD0->call(0x1bd2b0)` 返回 null → `cmp [rax+0x10], 0x22`; 崩溃时 Rdx=R8=**SPECTATOR(-4)** — 观众视角战斗结算 UI 同族空指针 (battleFinished 后触发); crashinfo.dmp 18:13 版已存, parse_crashinfo_mini.py + resolve_ra.py 可续查

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
