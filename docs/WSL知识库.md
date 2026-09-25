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

## 待整理（收到保存知识库指令时追加于此）

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

---

> ✅ **归档完成 (2026-09-25)**：原混在本文件的日期工作日志（共 290 块 / 3184 行）已全部拆分归档到 `WSL日志/` 下按日期命名的文件（2026-09-02 ~ 09-24），上方「三、日期工作日志」链接表已补全。本区清空，收到保存知识库指令时仍追加于此。
