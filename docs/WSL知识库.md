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

### getUpperArmy() 取兵机制 — visit+RECRUIT=兵直上英雄 (截至 2026-08-31)

`CGTownInstance::getUpperArmy()` (CGTownInstance.cpp L879): `if(getGarrisonHero()) return getGarrisonHero(); return this;`

**关键推论**: RECRUIT 执行链 (AAI.cpp case 16-18) `dst = town->getUpperArmy()`：
- 英雄**不在城** → dst=town → 兵进 garrison (城驻军)
- 英雄 **visit 己方城** → dst=visiting hero → **新招兵直接进英雄 5 槽** → 兵力增量奖励 (0.01×dp) 立即生效

这是"回城取兵"引导的理论基础：英雄回城 + 取兵窗发 16/17/18 = 完整的兵力上英雄链路，**无需任何新动作码**（act15 SWAP_ARMY 是英雄↔英雄交换、act22 GARRISON 是反向驻守，都取不了城 garrison 存量兵）。存量兵上英雄需另外的 C++ 能力（未实现，R6 同批评估）。

### obs towns 段寻址表 (埋点/引导用, 截至 2026-08-31)

- 段起点 `obs[336]`，每城 18 字段 (`_TOWN_FIELDS=18`)，8 槽 → obs[336:480]
- 字段序: id@+0 / **owner@+1** / pos_x@+2 / pos_y@+3 / pos_z@+4 / buildings@+5 / **garrison[7]@+6..12** / gold_income@+13 / recruit_mask_lo@+14 / recruit_mask_hi@+15 / build_mask_lo@+16 / build_mask_hi@+17
- 空槽: id=-1 (C++ 初始) → Python obs 全 0；有效城判定 `id>0 且 (pos_x>0 or pos_y>0)`
- **garrison 恒 0**: strategic_state.cpp L724 全知填充段 memset 未实现 — 使用前必知 (R6/garrison 前置见当前任务清单)
- **recruit_mask 有真实填充** (fill_v3_fields, dwelling 已建位图 level*2+upgrade) — 回城取兵触发信号用它
- 注意: 城易主后槽位可能变 (填充按 players 遍历序) — 跨步跟踪城身份用 id 字段映射, 勿用槽位号

### 城格不可站的结构性定性 (TOWN 判定 bug 根因, 截至 2026-08-31)

vmap town template 实测 (六图一致): `mask=["VVVVV","VVAVV","VVVVV"]` — 中心 'A' = actionable+**blocking** (逐格移动阻挡)；`visitableFrom` 四周 '+' = 引擎语义为英雄走到**邻格**触发访问并**停在邻格**。

→ `英雄坐标==城坐标` **结构性永假** (非概率性)：修复前 1850 局 × 24% 动步占比 0 次命中即为佐证。TOWN 类判定一律用 **dist≤1** (邻格)，勿用精确坐标。判定与引导配套缺一不可 (判定让糖能发 / 引导让模型走到糖边) — 详见已完成任务.md 08-31 条目。
