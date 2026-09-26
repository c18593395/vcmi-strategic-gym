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
- [2026-09-02.md](WSL日志/2026-09-02.md) — getUpperArmy() 取兵机制 — visit+RECRUIT=兵直上英雄 (09-02 修正: 需显式 getVisitingHero, 见文末 P1/P1b 条)
- [2026-09-03.md](WSL日志/2026-09-03.md) — P1e→r2→r3 approach 分支重写: CGPath 逐点推进 + 坐标双系统换算 (09-03)
- [2026-09-04.md](WSL日志/2026-09-04.md) — T05 全面化: 战斗剧本确立 + map 标签造假修正 (09-04)
- [2026-09-06.md](WSL日志/2026-09-06.md) — T06 课程: duel→1v3 分层上线 + 双根因 (09-06/07)
- [2026-09-07.md](WSL日志/2026-09-07.md) — 1v3 首周判据数据面达标 + 训练全面后台化 (09-07)
- [2026-09-08.md](WSL日志/2026-09-08.md) — Windows VCMI GUI 冒烟完整记录 (09-08)
- [2026-09-09.md](WSL日志/2026-09-09.md) — T06 capture 路径攻坚: 引导系统机理与激励包全链 (09-09)
- [2026-09-10.md](WSL日志/2026-09-10.md) — 线程生命周期插桩 (09-10 重编后已生效 — 实战立功)
- [2026-09-11.md](WSL日志/2026-09-11.md) — VCMI 网络协议与外挂 AI 架构调研 (09-11, GitHub 深度分析)
- [2026-09-12.md](WSL日志/2026-09-12.md) — T06 duel 地图生成 + check 工具 + 入池流程 (09-12)
- [2026-09-13.md](WSL日志/2026-09-13.md) — T7.4 死亡惩罚 09-13 方向纠正 + 02_duel 引擎 reset 冷启动竞态
- [2026-09-14.md](WSL日志/2026-09-14.md) — P8-D 双机实机验证 WSL 双实例 9/9 PASS (09-14)
- [2026-09-15.md](WSL日志/2026-09-15.md) — WIN-3 难度轴纯评估 + T7.5 节奏重估 (09-15, 不改图不重启)
- [2026-09-16.md](WSL日志/2026-09-16.md) — 09-16 P10-target-2b duel 图 move_to_force 分区分段策略（已验证通过）
- [2026-09-17.md](WSL日志/2026-09-17.md) — 09-17 批次B 首窗（07:42）归因增量沉淀（A2 归因报告完整版补录）
- [2026-09-18.md](WSL日志/2026-09-18.md) — 09-18 晚 B+C 窗：红蓝英雄真实战斗链路首次全线打通（OBS-3 历史性闭环）
- [2026-09-19.md](WSL日志/2026-09-19.md) — 09-19 官方 H3M 全量转换批跑（159 图 + 类型普查器 + 串行停训/批跑/重启脚本）
- [2026-09-20.md](WSL日志/2026-09-20.md) — 09-20/21 JEV 决策模型运维工具链全量上线（OPS-JEV-01~04：告警分诊 / FAIL 归因 / 池排序 / 金标回归）+ jegrep + h3m2vmap 重链与段错误发现
- [2026-09-21.md](WSL日志/2026-09-21.md) — 09-21 a_warm_and_familiar_place 地下城 skip 机制 + 批转 4 张新 PASS（blue_ai 标记体系成型）
- [2026-09-22.md](WSL日志/2026-09-22.md) — 终版护栏新窗首批信号（09-22 晚，ep42 窗 14 局——duel 首批转正）
- [2026-09-23.md](WSL日志/2026-09-23.md) — 09-23 #296 勘误 + 日志降噪 (Popen 层 grep 管道, 零 C++ 重编)
- [2026-09-24.md](WSL日志/2026-09-24.md) — 09-24 服务器 172.16.2.40 SSH 登录凭据 + 免交互通道 + pam_faillock 踩坑（结论）

---

> 注：原单文件 2546 行已重构为「1 总索引 + 3 稳定子文档 + 5 踩坑子文档 + N 日期日志」。3 个稳定子文档现采用各文件独立连续编号（一~N）：概述与决策 一~三 / 训练状态 一~二 / 参考速查 一~五；旧全局编号（七/八/九/十一 跳号与复用）已消除。H1 泛滥、自引用过期等问题亦随拆分消除。
> **2026-09-25 二次瘦身**：原本混在本文件的日期工作日志（09-02 ~ 09-24，3184 行）已全部拆出到 `WSL日志/` 下按日期命名的文件，本文件回归为纯索引。

---

## 附：稳定结论（标注截至日期，待归入上方「一、稳定参考」子文档）

> 以下条目为结论性内容而非日程记录，故不随日志归档；待归入 `WSL知识库-参考速查.md` 等稳定子文档后可从本区移除。

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


### 09-26 服务器训练日志判据分析 + 池图/课程图三档治理（elbow/King/T05）

> 状态：✅ 已落。触发 = 用户"分析下训练日志" → 判据对齐 S-10 + 09-25 续窗口径 → 三张大负图归因 → 用户追问 52_01 → A/B 双臂定谳 → "做" × 2 落地。证据 `train_full.log`（切窗法 10354 行=resume 1156385）+ `/DATA/hero3/ab5201_20260926/`（8 traj + 8 log + done.flag）。

**判据分析（当前窗 1156385→1553239，2135 局）**
- duel 108_02 难度轴有效：meanR +50.6 / 79% 正（09-25 基线 +78.7，未回退）；崩率 0/2135；战死 3/1584（09-25 的 58.6% → ~0.2%）
- H3M 池分化：judgement +392（94% 正）/ King -716 / too_many -603 / elbow -461；课程 T05 三张 -102~-113（0 正局）
- KL 整窗 192/192 批 >1.0（1.35→1.5 慢上漂），来源=H3M 池图 + T05 的"大常数负无结构"样本灌 PPO
- 09-25 要求的每局 R=（total_rew）已落地 [SLOT] 行

**三档治理（#326/#327 配套）**
- **elbow_room_allies**（池图，batch 2→99，热生效）：双窗证伪（迁移日段 14/14 全大负 + 当前窗分桶恶化 -440→-474→-497 + 0 正局 + 竞态 rc=124 史）。根因=09-25 入池依据是 30 步冒烟（rew=-62.75 看着正常），30 步进不了 250 步满步负区，整局实为 -461。
- **King_of_Pain**（课程 MAPS，摘除，重启生效）：非环境因素（地图 md5 两侧 9d21416f 相同）；= duel focus 挤压（只占 ~4% 局没被复习）+ 策略对旧课程图回归。WSL 尾段（迁前）已 -212~-263，迁移日段 -514，当前 -716 持续恶化。
- **T05 三张**（课程 MAPS，摘除，重启生效）：档位级能力真空。52_01 全历史 606 局 77% 正（449k-695k 弱蓝方环境 +128~+200）→ 696k 拐点（#283 蓝方变更）后 4 个月 0 回正。**A/B 双臂（N=4/臂，#298 纪律）：B1=T05 现行配置 vs B2=T06-duel 同款（gd=0），meanR -77.5 vs -78.5 等效 → 非机械问题，能力真空定谳**。回池条件写死：新 ckpt 评测 4 局 meanR≥0 且正局≥50%。
- **too_many_monsters**：保留留观 1 窗（分桶改善中 -616→-585），~50 局复核：改善 >20% 或正局 ≥5% 留，否则摘。

**方法论沉淀（三条，影响后续所有池/课程图决策）**
1. **图池准入禁止 30 步冒烟判**（#326）：verify 字段 steps=30 只看"能开局不崩"，满步大负图 30 步看不出来 → 必须满 250 步整局 N≥4。
2. **判留/摘看时间桶趋势非瞬时值**（#326）：对照 judgement_day -612→+391 证明"大负≠学不会"；判据=每 25 局桶均值改善 >10% 或出正局=留，平/恶化 + 0 正局 + 满步率>80% 跨 2 窗=摘。
3. **档位退化整档处置 + A/B 先诊断再摘除**（#327）：T05 三张一起治不逐图；机械 vs 能力分叉用双臂对照坐实，摘/留都有证据不是拍脑袋。

**重启记录**：本日 3 次优雅停起（20:47 King 生效 / 21:3x T05 生效 / 中间无），均 `Saved STATE_PATH` 零损失；末态 MainPID 2834236，maps=6（T06 六张），池=3（good_to_go/judgement_day/too_many），resume step=1600910。

**duel 概率悬案（本轮不动）**：DUEL_FOCUS_P=0.6 写死在 trainer L104，建议攒 ~500 局看"课程塌陷是否随 T05/池图负源清除而恢复 + duel 单图过拟合信号 + KL 回落"三件事后再定 40-60%；A/B 证明正收益不靠机械引导撑着（gd=0 救不动 52_01），duel 的 +51 靠目标可达+模型推进。

**delegation 401 事故（同日附带）**：delegation provider=agnes（api.agnes-ai.cn key sk-v0I...）401 无效令牌致子 agent 双挂 → 切 custom:apihub-5（apihub.agnes-ai.com 同模型），config.yaml delegation 段 3 行外科改（新会话生效），fact_store #66。

## 待整理（收到保存知识库指令时追加于此）

---

### 09-26 P1 引擎窗口三项收口（298 对照定谳 + #215 守卫重写 + connector 重编）

**结论**：P1 三项全闭环，本地仓 commit `11be8ba34d`（vcmi-native，4 文件）+ `87df8cc`（vcmi_gym，2 文件），均未推。证据目录 `/home/administrator/_298_p1_20260926/`（rootfs 持久）。

**P1-2 298 三套 A/B 对照实验（P0-2 销项）**：
- 纪律按 #298：同 4 图 × 4 轮 30 步，with-patches 臂（09-24 .so 原态）vs baseline 臂（`py/revert_298.py` 手术式逆向三套 298 → 重编，保留 09-24 的 [ML-time]/force/tradecap）
- 结果：A 臂 16/16 全 rc=0 零冻结；B 臂 4/16 rc=0 + **12×rc=124 冻结**（judgement_day 4/4、a_viking 4/4、elbow 3/4、g2g 2/4）
- 定谳：**三套全留**（栈打点当哨兵不撤 / 方案1 网络线程跳过等待 / upgrade 熔断 cap 8），09-23「去留倾向」三选三全留实锤
- 边界：压制非根治——冻结死锁根因（AI EndTurn realize 死锁 / Mode B 架构级）仍在，根治方向另排（09-23 章三档：服务器查询栈看门狗 / MapObjectVisitQuery 根因 / endTurn waitTillRealize=false）
- 基线工具关键决策：`.so.bak_*298` 是 09-23 快照，直接 rollback 会误伤 09-24 独立提交 → `revert_298.py` 基于三套 patch 脚本的 EDITS 常量做 `new→anchor` 精确逆向（踩坑 #321）

**P1-3 #215 headless 守卫重写**：
- 原 commit 65515ef24（09-16，14 处）被 09-19 上游 1160 文件重同步冲掉 + 对象随 09-18 rootfs 事故永久丢失（WSL 仓/D 盘镜像/09-19 备份 tar .git 三处 `cat-file -t` 全灭，踩坑 #320）→ 按 fact_store #215 记录重写为 P8 终局热路径最小 6 处：`py/patch_215_engine_guard.py`（CSH sendRestartGame/sendStartGame CLoadingScreen 双分支 + showHighScores + endGameplay discord + showServerError；Client.cpp removeGUI 二次崩点；备份 .bak_215）
- 同 commit 修 **vcmiclient 链接失败**（7/26 起欠账）：上游重同步冲掉 mlclient 链接行，`clientapp/CMakeLists.txt` 补 `if(ENABLE_ML) target_link_libraries(vcmiclient PRIVATE mlclient)`——根因 = NetPacksClient.cpp visitPlayerEndsGame 硬引用 `strategic_state_force_game_over` + `g_adventure_allied_ai`（MLClient.cpp L31 定义）
- 环境件：`data/config/settings.json` 写 `server.ML.statsMode=disabled` + `rel/bin/-`（sqlite）建 stats/stats_md 表 + seed 行 (side=0, n_pools=1, pool_size=2)（踩坑 #323）
- 验证：P8 p8c_query_reply **VERDICT: PASS**（171KB LobbyStartGame 广播不崩、zero 197 fishy、MY TURN #1 轮转、`grep -c "not allowed|fishy"` = 0）；冻结复验 g2g 重跑 4/4 rc=0（初跑 1×rc=124 定性 flake，N≥4 口径）

**P1-4 connector 重编（开源周 C++ 改动首次生效）**：
- vcmi_gym/connectors 3 个 .so（v13/14/15）+ 3 exporter 重编：`VCMI_DIR` CACHE PATH（`-DVCMI_DIR` 可覆盖）+ threadconnector XDG_DATA_HOME 取 `$HOME/.local/share`（已设不覆盖，根治 root 侧跑静默拿 /root 地形全零）
- 验证：cmake 全目标绿 + dlopen OK + trainer 冒烟链路正常；commit `87df8cc`（master，本地仓）

**遗留/下窗**：① 冻结 Mode B 根修（三档方向，见 P1-2 边界）② T13 §六 遗留①「#215 待 commit」销项（本次即销，守卫 6 处已入 11be8ba34d）③ p8c 脚本 exit 语义统一（踩坑 #325，开源周顺路）④ `py/ep_runner_one.py` 横跳 P0 修正仍挂账（奖励面改动，引擎窗口验证后再提）

---

### 09-25 PPO-DNA 并行化（N_SUBPROC=4 灰度上线）

**动机**：串行 1 局 5-600s + GPU 利用率近 0（更新 <1s vs 子进程 500s），24/7 训练日吞吐仅 15-180 局。

**架构**：
- 子进程池化（路线 A）：`train_wsl2_ppo_v2.py` 主循环分叉——`N_SUBPROC=1` 走原串行路径（零行为变化），`N_SUBPROC>1` 走 slot 池化路径（N 个 ep_runner 并行 Popen）
- Popen 非阻塞：`_spawn_slots` Popen 已启动 slot，`_harvest_slots` 每 2s poll 收割已完成 traj 入 buffer，buffer≥BATCH 后阻塞跳出进 PPO 更新
- 模型下发：每 PPO 更新后下一轮 `_spawn_slots` Popen 新版 ep_ckpt（1 个 PPO 更新延迟，PPO 容忍度高）
- 路径隔离：traj/ep_ckpt/ep_log 按 `_{slot}` 后缀（防 N 子进程撞同名文件，踩坑 #302 同款 EPERM 防护）

**内存预算**：
- 单 ep_runner RSS ~0.9GB（实测，NK2 修复后稳定），N=4 峰值 ~4.5GB
- WSL 默认 50% 上限（实测 7.6Gi）→ `.wslconfig` memory=12GB + swap=4GB → N=4 占 38%，留 ~6GB 安全垫

**吞吐提升**：
- 串行：攒 BATCH=2048 step 需 ~9 局 × 300s = 2700s/PPO 周期
- 并行 N=4：4 局并行 ~300s 攒满 → **~300s/PPO 周期**，GPU 利用率提升 ~9x

**并行路径 cmd 对齐**：`_spawn_slots` 的 cmd 构造与 `run_episode` L254-318 逐条对齐（HERMES env 化 + move_to_bias/force 按 map 前缀分支 + T06 act_loop_from_step + WIN1_ENV_ARGS 注入 + #296 grep 降噪管道），确保 N=4 时策略输入与 N=1 完全一致

**全崩兜底**：4 slot 全崩（rc≠0 / traj 缺失）时 while 死循环风险 → 连续 3 轮无新 traj 强制跳出进 PPO 更新（用现有样本，不卡死）

**SIGTERM 清理**：`save_shutdown` 清理 N 个 ep_runner + grep 管道（防关机残留），`if "slots" in globals()` 防御（slots 定义前 SIGTERM 不 NameError）

**灰度切换**：
- 当前：`HOMM3_N_SUBPROC=4`（已生效，4 ep_runner 同时跑）
- 回退：`HOMM3_N_SUBPROC=1` + `systemctl daemon-reload` + 重启训练 = 完全恢复串行
- 晋级判据适配：`curriculum_manager.record_episode` / `eval_promo` 的「最近 100 局窗口」统计需确认无交叉污染（`_harvest_slots` 按完成顺序 append，时间戳乱序但 100 局窗口内 avg_r 统计不受影响）

**待观察（1 周）**：
- 晋级判据 5 指标 vs 串行基线（avg_r / vloss / 正局率 / 大负率 / GUARD 首胜率）
- 全崩兜底触发频率
- 内存 available 维持 > 6GB
- 对手池 70/20/10 并行多样性爆炸（可固定 N slot 同对手）

**关键文件**：
- `py/train_wsl2_ppo_v2.py` L31-36（N_SUBPROC 常量）/ L226-419（run_episode slot 参数）/ L582-728（Popen 池化辅助函数）/ L777-815（主循环分叉）/ L546-557（SIGTERM 清理）
- `C:/Users/Administrator/.wslconfig`（memory=12GB + swap=4GB）
- `py/homm3-train-v5.service` + `/etc/systemd/system/homm3-train-v5.service`（HOMM3_N_SUBPROC=4）

**日志口径说明（09-25 补，防误判）**：
- 并行 `[SLOT]` 行打印 `avg_r=`（= `np.mean(traj["rew"])`，逐帧均值），串行打印 `r=`（= `total_rew`，整局累积）——两者口径不同但都是奖励指标，**`avg_r` 是更细的逐帧均值**，不是数据丢失
- `rc=0` = ep_runner 子进程**正常退出码**（跑完 250 步或自然 done，traj 正常写出）；`rc≠0`（-6/SIGABRT、-11/SIGSEGV、-15/SIGTERM）= 崩溃/被杀，traj 被 `[FILTER]` 丢弃。4 个 slot 全 `rc=0` = 全健康
- 全崩兜底日志措辞 09-25 已改：原「全崩兜底: buffer=X/2048」在 N 个 slot 正常并行完成时必然触发（4 slot 同时 poll 完成 = 设计内 batch 满跳出），易误读为崩溃 → 改后 L815 `[SLOT] batch 满...跳出进 PPO 更新`、L420/L719 `[FILTER] obs_nz=0 首拍全零丢弃 (reset 冷启动竞态/地图 header.players 缺陷)`（踩坑 #314）

**H3M 池图 obs 全零三层根因（09-25 排查，非单一竞态）**：
- **L1 地图 `header.players=[]` 空数组（确定性，已修 #222/#223）**：H3M 池图（King/good_to_go/judgement_day）`h3m2vmap` 工具链导出时漏注入 `header.players` → 引擎不建玩家槽位 → obs 城段 owner 全 0 → runner `no_own_town` abort → 首拍全零。**这是确定性缺陷非偶发竞态**，修 players 后脏样本归零
- **L2 引擎 reset 冷启动竞态（偶发 ~4%，#214 残余）**：`strategic_env.py` L690 `_adventure_wait()` 300s 内未收到 yourTurn 回调 / obs 填充线程未就绪 → `return np.zeros(OBS_DIM)`；H3M 72×72/108×108 大图 reset ~600s 竞争窗口大
- **L3 XDG 目录缺失（已修 #308，独立故障线）**：`$HOME/.local/share/vcmi/` 不存在 → `.vmap` 加载失败误报 Permission denied → SIGABRT rc=-6 丢 traj（走 `[WARN] traj 读取失败`，**不是 obs_nz=0 分支**）
- **#228「obs 3464 修复」与此不同源**：#228 = 败北信号断链根修（局末 PvP 战斗结算挂起 → game_over=2 刷新），与局首 reset obs 全零无因果
- **排查工具**：`py/_scan_h3m_players2.py`（raw 字节级读 .vmap players 段，临时脚本，查完即删）；权威预检走 `py/sync_maps_to_runtime.py --strict`（自带 header.players 预检）


### T14.2b t14-handicap 对称 handicap 纯 JSON mod（09-25 闭环，09-26 归档）

**结论（边界）**：对称经济加速（mod 双通道 start resources + weekly income 均确认流入进程内引擎）**未单独治好 KTV 单图 DRAW**——A/B 两组 250 步 go 仍全 0（全截断），B 组总战力末帧 B>A 但 NK2 把钱吃进战力不收割。治 DRAW 根因 = T14.3 VictoryPursuer（无胜利条件解析层），对称加金只是加速双方攒钱。详见 fact_store #61 / 任务清单 T14.2b 段。

**mod 结构**（`vcmi/Mods/t14-handicap/`）：`Content/config/difficulty.json` ai 段（通道 A=开局资源，官方 core king 档 ×1.5）+ `mod.json` `settings.resources.weeklyBonusesAI`（通道 B=周收益，king gold=525）+ `keepDisabled=true` 零干扰；引擎侧 `assembleFromFiles` 自动并入 config，`initDifficulty` 按 `p.human?human:ai` 分发。

**双通道确认真流入进程内引擎（ridiculous 值铁证）**：king gold 临时拉 500000 → obs 开局 gold raw=500000 原样进引擎（log1p 反算 `exp(obs)-1`）；通道 B weekly_income s29 8.16→10.24 也在工作。跑完已还原 ×1.5 定稿 + preset 默认关，零残留。

**对称根因修正**：headless `onlyai=true` 红蓝两侧 `isHuman=false` → handicap 对称加给双方=对症 S-7 全池 DRAW（双方经济加速→更早自然终局，baseline 同享→WR 公平不变）；Track2 真实游戏（human 红 / model 蓝）同一 mod 自动变不对称蓝方强化。一个 mod 两用。

**三条稳定参考**：
- **进程内引擎读 `rel/bin` 树而非源根**：`ep_runner` 走 `libmlclient.so` 内嵌引擎（非独立 vcmiserver），mod/preset 生效路径 = `rel/bin/data/` + `rel/bin/Mods/`；`vcmi-native/`（源根）与 `rel/bin/` 双树独立，**mod 部署需双写**（`rel/bin/data` 软链到 `vcmi-native/data`，但 Mods 是两份）
- **settings key = `weeklyBonusesAI`（带 "es"）**：schema + 官方 gameConfig.json + `GameSettings.cpp` L120 三元组 + mod.json 四方一致；C++ 枚举名 `RESOURCES_WEEKLY_BONUPS_AI` 无 es 是历史 typo，JSON 层以带 es 为准。`additionalProperties:false` 下错一个字母 = 通道 B 静默 0 效果（不报错，见踩坑 #319）
- **obs 资源槽 log1p 压缩**（详见踩坑 #316）：`_LOG1P_COLS` 槽位（strategic_env.py L454-462：players gold/total_power/weekly_income）读 raw 必须 `np.exp(obs)-1`，int() 直比 = 假曲线重合误判

**部署态**：preset 默认关（`keepDisabled=true`，零干扰）；启用 = `modSettings.json` `default.mods` 加 `"t14-handicap"` 一行；数值定稿 = core king 档 ×1.5（gold 全档 7500/11250/15000/15000/15000，weekly king gold=525）。仓内 `vcmi/Mods/t14-handicap/{mod.json,Content/config/difficulty.json}`。commit 主仓 f21c192c + vcmi 仓 27f2c9714。
