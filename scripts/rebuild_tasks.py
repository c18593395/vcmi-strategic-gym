# -*- coding: utf-8 -*-
"""重构三份任务清单：统一 T 编号、与知识库/踩坑点脱钩、进度流水迁出日志。
用法: python rebuild_tasks.py            # dry-run 预览
      python rebuild_tasks.py --write     # 实际执行
"""
import re, os, shutil, sys

DOCS = r'D:\Bigdata\hero3_fresh\docs'
LOG = os.path.join(DOCS, 'WSL日志')
WRITE = '--write' in sys.argv

# ---------- 编号映射 ----------
# 子任务级 旧->新
SUB = {
    'A1':'T1.1','A2':'T1.2','A3':'T1.3','A4':'T1.4',
    'B1':'T2.1','B2':'T2.2','B3':'T2.3','B4':'T2.4','B5':'T2.5','B6':'T2.6',
    'C1':'T3.1','C2':'T3.2','C3':'T3.3','C4':'T3.4','C5':'T3.5','C6':'T3.6',
    'C8.1':'T4.2','C8.2':'T4.3','C8.3':'T4.4','C8.4':'T4.5','C8.5':'T4.6',
    'H.1':'T5.1','H.2':'T5.2','H.3':'T5.3','H.4':'T5.4','H.5':'T5.5','H.6':'T5.6','H.7':'T5.7','H.8':'T5.8','H.9':'T5.9',
    'I.1':'T6.1','I.2':'T6.2','I.3':'T6.3','I.4':'T6.4',
    'II.1':'T7.1','II.2':'T7.2','II.3':'T7.3','II.4':'T7.4',
    'D1':'T8.1','D2':'T8.2','D3':'T8.3','D4':'T8.4',
    'E0':'T9.1','E1':'T9.2','E2':'T9.3','E3':'T9.4','E4':'T9.5','E5':'T9.6',
    'v15.1':'T12.1','v15.2':'T12.2','v15.3':'T12.3','v15.4':'T12.4',
}
# Phase 级 旧->新
PHASE = {'Phase A':'T1','Phase B':'T2','Phase C1-C6':'T3','Phase C7':'T4.1',
         'Phase C8':'T4','Phase H':'T5','Phase I':'T6','Phase II':'T7',
         'Phase D':'T8','Phase E':'T9','Phase F':'T10','Phase G':'T11','v15':'T12'}

def renumber(t):
    # 先子任务级（含 C8.5/I.4 等），再 Phase 级，避免 Phase C8 误吞 C8.5
    for k, v in sorted(SUB.items(), key=lambda x: -len(x[0])):
        t = t.replace(k, v)
    for k, v in PHASE.items():
        t = t.replace(k, v)
    t = t.replace('#45', 'T4.1 修复链').replace('#46', 'T4.1 修复链')
    return t

def decouple(t):
    """移除指向知识库/踩坑点的引用（任务清单只写任务）。"""
    for kw in ['WSL知识库', 'WSL踩坑点', '踩坑记录']:
        t = re.sub(re.escape(kw) + r'\.md', '', t)
        t = re.sub(re.escape(kw), '', t)
    t = re.sub(r'（详见知识库[^）]*）', '', t)
    t = re.sub(r'详见知识库[^\s。\n]*', '', t)
    t = re.sub(r'见知识库[^\s。\n]*', '', t)
    t = re.sub(r'过程踩坑见[^\n]*', '', t)
    t = re.sub(r'见踩坑 #\d+(?:/#\d+)*', '', t)
    t = re.sub(r'（踩坑[^）]*）', '', t)
    t = re.sub(r',?\s*踩坑 #\d+(?:/#\d+)*', '', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    return t

# ---------- 模板：总任务.md（整体脉络） ----------
TOTAL = '''# HoMM3 全盘操盘 AI — 总任务（整体脉络）

> 最终目标：AI 完整操控真实 HoMM3，与你对战（1v7），并战胜你。
> 演进路线：1v7 高级电脑 → 2-3 真人 → 人vs人vs模型联网（VCMI Windows 引擎内部接口）。
> 策略：VCMI 沙盒训练战略模型 → 真实游戏内存操控 → 自对弈持续进化。
> 任务清单体系（三层）：本文件 = 整体脉络（大项 + 重要里程碑）；`当前任务清单.md` = 当下窗口要完成/解决的任务清单；`已完成任务.md` = 对应编号的详细归档（追加型）。
> 设计依据：`源码分析地图.md` + `动作空间设计文档.md`（技术参考，非任务体系）。

> 编号规则（AI 必读）：大项用 T1~T12，子任务 T.n（如 T6.2）。插入中间任务用小数（T6.5）；任务变更（取消/合并）保留原号打 ❌ 并注明去向，不重用编号，避免引用断裂。新增大项顺延 T13+。当前训练参数快照见 `当前任务清单.md` 当前主线。

---

## 总进度

| 大项 | 目标 | 状态 |
|------|------|------|
| T1 | VCMI 冒险地图 API | ✅ 完成 |
| T2 | 战略 Gym 环境 (obs 264→2689→3464) | ✅ 完成 |
| T3 | 基础 PPO 训练 | ✅ 完成 |
| T4 | Connector 适配 + BC 采集微调 (事件奖励 + KL) | ✅ 完成 |
| T5 | 动作空间宪法冻结 (64 码 + obs 3464) | 🔶 T5.1-T5.7 ✅ / T5.8 训练中 / T5.9 ⬜ |
| T6 | NK2 逻辑融合 (1 估值→2 寻路→3 决策) | 🔶 T6.1✅ / T6.2✅(毕业) / T6.4🔄 |
| T7 | 城镇经济（当前主线） | 🔶 T7.1-T7.3 ✅ / T7.4 ⬜ |
| T8 | 战斗集成 | ⬜ 待办 (v15 合并后评估) |
| T9 | 真实游戏对齐 (Track 2) | ✅ 战斗链+战后恢复闭环 (08-19) |
| T10 | 你 vs AI (1v1) | ⬜ 待办 |
| T11 | 1v7 战胜你 | ⬜ 目标 |
| T12 | v15 架构迁移 (GNN + py::dict) | ⬜ Phase G 前 |

---

## 大项总览（整体脉络）

### T1 VCMI 冒险地图 API
目标：VCMI 冒险地图层原子通信，供战略 Gym 读取。
子任务：T1.1 adventure_process_turn / T1.2 strategic_state_update / T1.3 adventure_get/send_action / T1.4 g_strategic_state 全局指针。状态：✅ 全部完成（详见 `已完成任务.md`）。

### T2 战略 Gym 环境
目标：gymnasium.Env 战略环境，obs 264→2689→3464。
子任务：T2.1 StrategicEnv / T2.2 obs 构建器 / T2.3 奖励函数 / T2.4 ep_runner_one / T2.5 passability mask / T2.6 态势感知扩展 (obs 264→2689)。状态：✅ 全部完成。

### T3 基础 PPO 训练
目标：PPO 自对弈基础能力。
子任务：T3.1 500ep×20步 / T3.2 GPU 加速 / T3.3 Checkpoint+对手池+ELO / T3.4 1000ep×50步×128batch, 110 张 H3M / T3.5 多玩家+AI 对手 / T3.6 STEPS_PER_EP 50→200。状态：✅ 全部完成。

### T4 Connector 适配 + BC 采集微调
目标：Connector 适配修复链 + BC 行为克隆采集微调（事件奖励 + KL）。
子任务：T4.1 Connector 适配+修复链 (N2-N11, EEXIST 解锁, 全线打通) ✅ / T4.2 事件奖励 ✅ / T4.3 KL 约束 ✅ / T4.4 BC 采集→PPO 重启 ✅ 链路通 / T4.5 采集排障 4 连 ✅ / T4.6 训练重启 (用户关机解除) ✅。BC→PPO 链路打通后演进归入 T5.8 / T6.2。

### T5 动作空间宪法冻结
目标：动作码 64 位 + obs 3464 维 长期宪法，一次设计冻结。
子任务：T5.1 源码 9 面枚举 / T5.2 动作空间 v2 冻结 (64 码) / T5.3 OBS schema v3 冻结 (2689→3464) / T5.4 敌方可见性验证 / T5.5 obs v3 实现 / T5.6 C++ 动作 11-24 / T5.7 冒烟测试 16 项 / T5.8 BC 重采集→PPO 重启 (训练验证中) / T5.9 v2 MultiDiscrete 三维参数化 (远期, 与 T6.3 合并)。
状态：T5.1-T5.7 ✅；T5.8 🔶 训练中；T5.9 ⬜ 远期。

### T6 NK2 逻辑融合（主线之一）
目标：1v7 正道——NK2 专家骨架 + 学习组件渐进替换（1 估值→奖励, 2 执行→寻路, 3 决策→分层）。
子任务：T6.1 NK2 估值→奖励塑形 ✅ 冻结 (08-22) / T6.2 执行层 C++ BFS 全图寻路 ✅ 代码完成+T03 段毕业 (08-29) / T6.3 决策结构分层 ⬜ 远期 (与 T5.9 合并) / T6.4 训练地图体系 (VMAP 课程 T01-T06) 🔄 Level 3 训练中 (v5)。
当前训练 v5 = T6.1 估值 + T6.2 寻路 实跑中。

### T7 城镇经济（当前主线）
目标：1v7 必经之路（经济招兵）。纪律：晋级与开经济不同时做，一次只加一个难度轴。
子任务：T7.1 Level 3 晋级 ✅ (08-29) / T7.2 切 T04 地图 (不开经济) ✅ (08-29) / T7.3 开经济 (一次一轴) ✅ (08-29 深夜) / T7.4 存活塑形评估 ⬜ 待经济稳定 / T7.5 经济奖励撤梯子策略 (渐进半价) 📋 已登记。
详见 `当前任务清单.md` 当前主线详述。

### T8 战斗集成
目标：英雄战斗进观测/奖励，战斗结果建模。
子任务：T8.1 英雄踩怪→autofight ✅ / T8.2 英雄 VS 英雄战斗 ⬜ / T8.3 战斗结果进观测/奖励 ⬜ / T8.4 战斗状态追踪 (obs.in_battle) ⬜。
注：MMAI v15 未合并官方，2-4x 慢；战斗层版本锁定不追。

### T9 真实游戏对齐（Track 2）
目标：模型落地真实 HoMM3（路线 C：原版 SoD 3.2 + H3API DLL 最终目标）。
子任务：T9.1 H3API 编译验证+注入 demo ⬜ (前置 T5.8 成熟) / T9.2 状态读取层 (obs↔H3API) ⬜ / T9.3 动作执行层 (hook 原版函数) ⬜ / T9.4 推理层 ONNX+DLL ⬜ / T9.5 稳定性 24 局 ⬜ / T9.6 VCMI Windows 路线验证 ⬜。
状态：战斗链+战后恢复闭环 ✅ (08-19, 1.7.5 GUI 5AI 7 战 0 拒 0 崩)；路线 C 待 T5.8 成熟。

### T10 你 vs AI 1v1
目标：人机 1v1 对战底座。⬜ 待办（T9 铺路）。

### T11 1v7 战胜你
目标：最终目标。⬜ 需 T12 前完成 v15 迁移。

### T12 v15 架构迁移
目标：图状态取代平面向量 + GNN + py::dict 通信 + 训练体系重写。
子任务：T12.1 图状态 (nodes+links) / T12.2 GNN 取代 MLP / T12.3 py::dict 取代 struct / T12.4 训练体系重写。⬜ 全部待办（Phase G 前）。

---

## 重要里程碑时间线

- 2026-07-29：T4.1 Connector 适配+修复链完成；EEXIST 解锁 / 全线打通。
- 2026-08-01：T4.6 训练停止（用户关机）；T2.6 态势感知扩展 obs 264→2689；T4 事件奖励+KL 合并。
- 2026-08-14：T5 动作空间宪法冻结（T5.1-T5.4）。
- 2026-08-15：T5.5 obs v3 实现 (2689→3464)；T5.6 C++ 动作 11-24；T5.7 冒烟 16 项。
- 2026-08-16：NK2 卡死修复全闭环（T8 前置）。
- 2026-08-18：有头 GUI 验证（T9 前置）。
- 2026-08-19：MOVE_TO 训练端落地；真实游戏战略层联调（T6 / T9）。
- 2026-08-22：T6.1 NK2 估值→奖励塑形冻结。
- 2026-08-23：T6.4 训练地图体系生成完成 (T01-T06)；T6.2 BFS 代码完成。
- 2026-08-24：T6.2 超参调优链冻结。
- 2026-08-26：守卫战斗根因闭环（Level 2 正奖励率 83%）。
- 2026-08-27：守卫真战斗全链打通。
- 2026-08-28：END_TURN zombie 三层防御 + v4 段交付；v5 训练运维根治。
- 2026-08-29：首胜-战死关联分析；T7 阶段②经济前置准备 ✅；Task7 真实游戏联调 ✅；断言修复部署+训练重启 ✅；T03 毕业 + T7.1/T7.2 Level 3 晋级 ✅；T04 三件套修复；T7.3 开经济 ✅；B 方案自主通道修复 → 课程突破 ✅。

---

## 架构

### 双轨并行

```
┌──────────────────────┐   ┌──────────────────────────┐
│  Track 1: 训练 🟢    │   │  Track 2: 真实游戏对齐 ⬜ │
│  持续提升模型强度      │   │  模型落地到真实 HoMM3    │
│  WSL2 GPU 后台跑      │   │  Windows 内存读取验证    │
│  不占交互注意力        │   └──────────────────────────┘
└──────────────────────┘
```

- Track 1：PPO 自对弈，WSL2 RTX3060 24/7
- Track 2：ONNX 导出 → 真实游戏内存读取 → PostMessage 操控

### 战略层 vs 战斗层

```
战略层 RL (PPO) → 决定移动/探索/占矿/攻城/分兵/合兵/招兵
  ↓ 遇敌
战斗裁决 → VCMI autofight 自动裁决（当前）
         → v15 战斗模型（后续 T8，需官方合并+重采集）
```

### 两段式设计

| 端 | 位置 | 用途 |
|----|------|------|
| 训练端 | WSL2, RTX3060 | PPO 自对弈训练，出 ONNX |
| 推理端 | ARM64 服务器 (172.16.2.40) | ONNX 推理，ctypes 读状态 |
| 部署端 | 本机 HD Mod | 内存读取 + PostMessage 操控 |

---

## 关键原则

1. **训练地图用 VMAP** (ZIP+JSON, T01-T06 课程体系)；H3M 经典图已停用。
2. **改代码 → `wsl -u root systemctl stop homm3-train-v5` 优雅停止 → `start` 重启 (checkpoint resume)**（0911 起 system 级 enabled unit；旧 `systemctl --user` transient 已废弃）；WSL keepalive 常驻防 idle shutdown（v5 训练运维根治）。
3. **VCMI 铁律**：不重编 libvcmi.so，只编 libmlclient.so + libMMAI.so + connector。
4. **vcmi-native vs vcmi-native-build** 双目录须 cp 同步。
5. **改 Python 后清 `__pycache__`**。
6. **动构建树前备份** .so + 源码 (backups/ + *.bak)。
7. **OBS/动作空间冻结铁律**：禁增删维度/改语义/重排段序；扩展只启用预留位。
8. **不追官方更新**：锁战斗层版本；NK2 寻路加速 (40% 吞吐) 是红利，训练稳定后择机 merge（T6.2 关联）。
9. **奖励原则**：被动收入不做 per-step 奖励（导致 END_TURN 塌缩）；只做终局/事件奖励。
10. **晋级纪律**：晋级与开经济不同时做，一次只加一个难度轴（T7 铁律）。

---

## 关键资产索引

| 资产 | 位置 |
|------|------|
| 训练脚本 (V2) | `train_wsl2_ppo_v2.py` |
| StrategicEnv | `vcmi_gym/envs/v13/strategic_env.py` |
| ep 执行器 | `ep_runner_one.py` |
| strategic_state (C++) | `vcmi/ML/strategic_state.h/cpp` |
| 训练启动 | WSL systemd system 级 enabled unit `homm3-train-v5`（/etc/systemd/system，0911 起）；停/启 `wsl -u root systemctl stop\\|start homm3-train-v5` |
| 训练日志 | `D:\\Bigdata\\hero3_fresh\\train_loop.log` |
| Checkpoints | `checkpoints/` |
| VMAP 训练地图 | `maps/training/` (T01-T06 共 31 张；运行时 3 副本同步) |
| H3M 地图 (已停用) | `maps/` (158 张, h3m_tool.py 保留逆向参考) |
| 可用地图索引 | `available_maps.json` (110 张) |
| 动作空间设计 (宪法) | `docs/动作空间设计文档.md` |
| 源码分析地图 (依据) | `docs/源码分析地图.md` |
| 任务三件套 | `总任务.md`, `当前任务清单.md`, `已完成任务.md` |
| 健康监控 | `py/train_health_monitor.ps1` + `monitor_alerts.log` |
'''

# ---------- 模板：当前任务清单.md（当下要解决） ----------
CURRENT = '''# 当前任务清单（当下窗口要完成/解决的任务）

> 父文档：`总任务.md`（整体脉络，大项 T1-T12）。本文件 = 当下要完成/解决的任务清单：① 当前主线大项详细任务；② 待办工作台 A/B/C/D 档；③ 训练期并行 P；④ 风险登记 R。完成即移入 `已完成任务.md` 并回写总任务状态。
> 编号：与总任务 T 体系一致；A/B/C/D/P/R 为本文件工作台视图分类标签（非大项编号），明确归属某大项的标注 T 编号。
> 脱钩：本文件只写任务，不引用知识库/踩坑点（技术细节见对应设计文档）。

---

## 当前主线：T7 城镇经济（当前主线，T7.1-T7.3 ✅）

### T7.1 Level 3 晋级 ✅ 完成 (08-29)
晋级线：近 100 局胜率 ≥30~50% 或 avg_r 持续为正。三判据全过：eval 10/10 全胜 avg_r=99 / 近 100 局首胜率 64% / 30X30_01 A/B 44 局 0% 大负率。决策：跳过 30X30_02（同构边际低），直接晋级。

### T7.2 切 T04 地图（不开经济）✅ 完成 (08-29)
MAPS=T04×6 + Level 3 超参 (BATCH=2048/EPOCHS=6/ADV_CLIP=6.0)；step=205345 resume；配套 clip±300 对称修复 + objective_reward 30 (首占矿/首进城镇 +30) + 目标优先层 (矿 > 资源堆) + move_to_force 60 常驻。

### T7.3 开经济（一次一轴）✅ 完成 (08-29 深夜)
economy_force 24 (50→24 修复空转) + explore 0.3 + nk2 0.45；RECRUIT first+12/每次+2, BUILD_2 first+15/每次+3（自主通道修复）；兵力增量 0.001→0.01；周期提醒每 40 步 4 步经济窗；城镇引导降级。[ECON] 全链验证；avg_r 段高 +0.8；80+ 分局 3/15 常态化；历史新高达 +105.9；自主 16-21 0.6→2.0/局 爬升中。

### T7.4 存活塑形评估 ⬜ 待经济稳定
首胜-战死 100% 关联 (7/7)；T04 有城镇后评估是否加死亡惩罚/存活奖励。

### T7.5 经济奖励撤梯子策略 📋 已登记
渐进半价不跳崖：① 现在不动 (自主 2.0/局未固化) → ② 自主 3+/局 连续 2 窗稳定后每次奖励半价 (+2/+3→+1/+1.5), first 不动 → ③ 大调 (兵力 0.01/explore) 打包到换图节点一次付非平稳成本。每步观察 1~2 窗确认无行为退化。

**T04 当前态势**：修复前 19 局乱逛 r=-80~-110 (0 胜负局)；三件套修复后 [MINE] 首占矿验证生效。观察点：占矿率上升 / ±200 胜负局出现 / [TOWN_BLOCKED] 卡死率。

**前置准备（08-29 完成，零干扰）**：s2a 经济奖励编码 / s2b 动作合法性掩码 / s2c 超参注释包 / s2d T04 地图池注释块 / s2e economy_force 切换点——全部条件开关设计（详见 `已完成任务.md`）。

---

## 并行主线：T6 NK2 逻辑融合（训练验证中）

- T6.1 NK2 估值→奖励塑形 ✅ 冻结 (08-22)，v5 实跑中。
- T6.2 C++ BFS 全图寻路 ✅ 代码完成 + T03 段毕业 (08-29)，v5 实跑 (step≈212k, MAPS=T04×6)。
- T6.4 训练地图体系 (VMAP T01-T06) 🔄 Level 3 训练中。
- T6.3 决策结构分层 ⬜ 远期（与 T5.9 合并）。
- 注：v5 = T6.1 + T6.2 + T7.3 三者叠加训练中。

---

## 待办任务总表（A/B/C/D 档，标注是否影响训练）

> 影响训练判定：是否触碰 WSL 侧 rel/ 运行时 .so、训练进程/日志、GPU/显存、vcmi-native 工作源码。

### A. 立即可做（零影响：Windows 侧 / 纯只读）
| # | 任务 | 归属 | 影响训练? |
|---|------|------|-----------|
| A1 | S5 健康复核补跑（grep 重启点后 ZOMBIE/FUSE/ASSERT/GUARD 计数）| T6.2 | ❌ 纯只读 |
| A2 | A Viking 战斗验证（fork 1.8 headless 跑 RL 模型，看战斗链闭环）| T9 | ❌ Windows 侧 |
| A3 | 1.7.5 MSVC DLL 重编（同步 4 文件到官方 GUI 部署）| T9.3 | ❌ Windows MSVC |
| A4 | MOVE_TO(act24) DLL 执行器（补齐真实游戏闭环）| T9.3 | ❌ Windows 侧 |

### B. 设计文档类（零影响：只写方案）
| # | 任务 | 归属 | 影响训练? |
|---|------|------|-----------|
| B1 | 30x30/36x36 解封方案 | T7 | ❌ 纯文档 |
| B2 | 经济动作上线参数方案 | T7.3 | ❌ 纯文档 |
| B3 | 开局熵 bonus 方案 | T3 | ❌ 纯文档 |
| B4 | 晋级判据量化校准 | T7.1 | ❌ 纯文档 |

### C. 谨慎（需隔离设计，有资源/文件重叠）
| # | 任务 | 归属 | 影响训练? |
|---|------|------|-----------|
| C1 | 晋级判据自动化 eval | T7.1 | ⚠ 会抢 GPU/CPU；CPU-only + 低频 (≥2h) + 限 batch |
| C2 | 重编崩溃根因插桩 | T6.2 | ⚠ 分析可，部署禁止 |
| C3 | CGameHandler garrison 自动合并 | T8.1 | ⚠ 触碰铁律；除非断言复发否则搁置 |
| C4 | NK2 寻路加速 merge (+40% 吞吐) | T6.2 | ⚠ 动 libvcmi.so，训练期禁 |

### D. 等待条件触发（不在当前窗口做）
| # | 任务 | 归属 | 影响训练? |
|---|------|------|-----------|
| D1 | 经济动作实际上线 | T7.3 | 🔴 改 ep_runner，须停训窗口 |
| D2 | 30x30/36x36 实际解封 | T7 | 🔴 需重启训练 |
| D3 | 开局熵 bonus 实装 | T3 | 🔴 改训练脚本 |
| D4 | 2v2/多人对局验证 | T10 | ❌/⚠ fork headless 不影响，GUI 验证需用户在场 |

**建议顺序**：A1 → A2 → A3 → B1/B2 → 其余等窗口。

---

## 训练期并行任务（P，不碰运行中 v5 进程）

| # | 任务 | 类型 | 状态 / 依赖 |
|---|------|------|------------|
| P1 | 训练空转根因 (断言雷) 已修复 | 解锁型 | ✅ 完成 (08-29) — libMMAI.so 换 13c0f041, libmlclient 保持 5d2b9e9d；冒烟 2 战斗 0 断言 |
| P2 | 晋级判据自动化 eval 脚本 (py/eval_promo.py) | 备料型 | ✅ 完成 (08-29) — CPU-only，不抢训练资源 |
| P3 | 30x30/36x36 守卫距离解封（代码就绪待激活）| 解锁型 | 🔧 待激活 — `--guard_grad_scale_by_map` |
| P4 | ZOMBIE/GUARD all-blocked 事件聚合分析 (py/analyze_deadlock.py) | 备料型 | ✅ 完成 (08-29) |
| P5 | 开局确定性对策 (entropy 调度) | 备料型 | ⏸ 等自然重启窗 |
| P6 | 对手池 self-play/NK2 混合 | 备料型 | ⏸ 等 20x20 首胜稳定 |
| P7 | 真实游戏战略层联调 (fork 1.8 DLL) | 铺路型 | ⬜ 低强度并行 |
| P8 | 人机对战底座 (大厅 1V7 配置) | 铺路型 | ⬜ 远期 |
| P9 | done 信号接线 — 核实已存在无需开发 | 备料型 | ✅ 误报排除 |
| P10 | H3M 官方图 → VMAP 转换 (h3m2vmap) | 备料型 | 🔧 A 步实测 (08-29) |

### P10 H3M 官方图 → VMAP 转换（A 步实测结论）
需求：用官方 H3M 图真实复杂度做地形骨架，降低守卫强度，按官方复杂度渐进。定位：备料型，不碰在跑的 v5 训练。
- A 步实测：① 72~144 尺寸可塞进 21×21 obs（fill_terrain_grid 以英雄为中心 10 格局部窗）；② 官方图物体密度不爆槽（白名单 45 vs 自研 48 同量级）；③ H3M 属性需自建转换入口（无命令行）；④ 水域/船已规避。
- ⚠ 真瓶颈：fill_target_list 排序 = 纯曼哈顿距离 top-8，无价值/威胁加权 → 最近 8 目标大概率全是被强守卫堵住的资源 → 模型看不到可行路径。"减少守卫"真实作用 = 释放 top-8 槽位让可行目标可见（守卫系数 = 天然课程轴）。
- 选图：`Knee Deep in the Dead.h3m`（36×36 无地下, ROE, 2 玩家, 城需删/封）。
- 实施序：A ✅ / B 转换器 ⬜ / C 改写规则 ⬜ / D 验证链 ⬜ / E 入池 ⬜。B 步编译须独立构建目录，禁覆盖 rel/ 下 .so。

---

## 风险登记（R，引擎侧）

| 风险 | 机制 | 状态 / 对策 |
|------|------|------------|
| R1 动作拒绝不可感知 | server 拒绝只 complain，AI 侧无回调 | 🟡 已缓解未审计 — Python action mask 在用 |
| R2 done 信号 — 核实轮询链已通 | 终止靠轮询链非事件回调 | ✅ 误报排除 |
| R3 异步时序竞态 | 动作靠 waitTillRealize 同步化 | 🟢 约束型 — 新增动作走 waitTillRealize |
| R4 queryID=-1 断言雷 | 战斗结束攻方 queryID=-1 触发 ASSERT | ✅ 已修 — libMMAI.so 13c0f041 部署 |
| R5 双源码树不同步 | Windows vcmi/ 与 WSL vcmi-native 不同步 | 🟡 长期隐患 — 源码级改动前 WSL grep 确认 |

---

## 远期 / 阻塞集

- T5.9 v2 MultiDiscrete 三维参数化（与 T6.3 合并）⬜ 远期
- NK2 寻路加速 merge（官方 #7632, +40% 吞吐）— 训练稳定后评估（→ C4）
- MMAI v15（PR #7654）— 未合并官方，2-4x 慢；合并后需重采集（→ T8）
- 动作码 16-23 内政启用 — Level 3 切入时先解决 noTarget 惩罚
- fogOfWarMap 语义确认（visible vs explored）— T5.4 顺带
'''

def backup(fname):
    src = os.path.join(DOCS, fname)
    bak = src + '.split_bak'
    if not os.path.exists(bak):
        shutil.copy2(src, bak)
        return f'备份 {fname} -> {fname}.split_bak'
    return f'{fname}.split_bak 已存在，跳过'

def main():
    print('=== dry-run ===' if not WRITE else '=== WRITE ===')
    for f in ['总任务.md', '当前任务清单.md', '已完成任务.md']:
        print(backup(f))

    # 总任务 / 当前清单：直接写模板
    print(f'总任务.md 将写 {len(TOTAL.splitlines())} 行')
    print(f'当前任务清单.md 将写 {len(CURRENT.splitlines())} 行')

    # 已完成任务：读原 -> renumber + decouple
    src_done = os.path.join(DOCS, '已完成任务.md')
    raw = open(src_done, encoding='utf-8').read()
    n_kb = raw.count('WSL知识库') + raw.count('WSL踩坑点') + raw.count('踩坑记录') + len(re.findall(r'坑 #\d+', raw))
    done_lines = raw.splitlines()
    out = ['# 已完成任务（对应编号详细归档）', '',
           '> 追加型文档：记录已闭环任务的详细过程，按总任务 T 编号归档。新完成任务时在此追加，保留日期与结论。', '',
           '---', '']
    skip_head = True
    for l in done_lines:
        if skip_head and l.startswith('>'):
            if ('父文档' in l) or ('归档从' in l) or ('规范' in l):
                continue
            skip_head = False
        out.append(decouple(renumber(l)))
    done_text = '\n'.join(out) + '\n'
    print(f'已完成任务.md 将写 {len(out)} 行（脱钩引用 {n_kb} 处）')

    # 日志迁出：优先从备份(.split_bak)读旧当前清单的进度记录段（当前清单已被重写）
    cur_src = os.path.join(DOCS, '当前任务清单.md.split_bak')
    if not os.path.exists(cur_src):
        cur_src = os.path.join(DOCS, '当前任务清单.md')
    cur = open(cur_src, encoding='utf-8').readlines()
    idx = [i for i, l in enumerate(cur) if l.startswith('## 进度记录')]
    if idx:
        log_body = ''.join(cur[idx[0]:])
        log_body = decouple(log_body)
        log_head = '# 进度记录 2026-08-29（从 当前任务清单.md 迁出）\n\n> 本文件为日期工作日志，记录 2026-08-29 当日进度流水。任务状态变更见 总任务.md / 当前任务清单.md / 已完成任务.md。\n\n---\n\n'
        os.makedirs(LOG, exist_ok=True)
        print(f'日志将写 WSL日志/2026-08-29-进度.md ({len(log_body.splitlines())} 行)')
    else:
        log_head = log_body = None
        print('未找到 进度记录 段')

    # 废弃踩坑记录.md
    junk = os.path.join(DOCS, '踩坑记录.md')
    junk_bak = junk + '.bak'
    if os.path.exists(junk):
        print(f'废弃 踩坑记录.md 存在：将备份为 .bak 后删除')
    else:
        print('踩坑记录.md 不存在（可能已删）')

    if not WRITE:
        print('\n[dry-run] 未写入任何文件。加 --write 执行。')
        return

    # ---- 实际写入 ----
    open(os.path.join(DOCS, '总任务.md'), 'w', encoding='utf-8', newline='').write(TOTAL)
    open(os.path.join(DOCS, '当前任务清单.md'), 'w', encoding='utf-8', newline='').write(CURRENT)
    open(src_done, 'w', encoding='utf-8', newline='').write(done_text)
    if log_head:
        open(os.path.join(LOG, '2026-08-29-进度.md'), 'w', encoding='utf-8', newline='').write(log_head + log_body)
    if os.path.exists(junk):
        shutil.copy2(junk, junk_bak)
        os.remove(junk)
        print('已删除 踩坑记录.md（备份 .bak）')
    print('\n[write] 完成。')

if __name__ == '__main__':
    main()
