# 当前任务清单

> 父文档: `总任务.md` | 踩坑: `step2分析.md` | 技能: `skill vcmi-gym`, `skill homm3`

---

## 双轨并行架构

```
┌──────────────────────┐   ┌──────────────────────────┐
│  Track 1: 训练 🟢    │   │  Track 2: 真实游戏对齐 ⬜ │
│  持续提升模型强度      │   │  模型落地到真实 HoMM3    │
│  WSL2 GPU 后台跑      │   │  Windows 内存读取验证    │
│  不占交互注意力        │   │  需主动执行              │
└──────────────────────┘   └──────────────────────────┘
```

**使用方式：**
- 说 **"按当前任务清单去训练"** → 执行 Track 1 任务
- 说 **"按当前任务清单去测试实际游戏"** → 执行 Track 2 任务

**训练进程在 WSL 长期运行（不依赖任何 Hermes 会话）。V1 稳定后才考虑切 V2，否则一直用 V1。**

---

## Track 1: 训练 🟢（GPU 24/7 后台跑）

### 📋 下次开机启动（快速恢复训练）

```bash
# 1. 恢复干净 checkpoint
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash -c '\
  cp /mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_16390.pt \
     /mnt/d/Bigdata/hero3_fresh/wsl2_model.pt'

# 2. 启动训练（V1 脚本）
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/train_loop.sh &

# 3. 确认运行
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- ps aux | grep train_wsl2_ppo
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- tail -5 /mnt/d/Bigdata/hero3_fresh/train_loop.log
```

**或说 "按当前任务清单去训练"**

### 训练状态（2026-07-23）

```
V1 总计: Round 1 ✅ + Round 2 ✅ = ~32h, best_vloss=12
V2 总计: 3 轮全部 NaN crash，已弃用
当前: V1 训练（从干净 checkpoint step 16390 续训，1000ep）

总训练时长: ~50h
```

### ⚠️ 关键规则
- **使用 V1 训练脚本**（train_wsl2_ppo.py），不用 V2（有 NaN bug）
- 只有 V1 达到 avg_r 中枢 ≥1.0 且连续 300ep 无下滑，才考虑切 V2
- 脚本已加 NaN 防护：加载时检测 NaN → 自动回退干净 checkpoint；保存前检测 NaN → 跳过保存
- 训练步数 N_EPISODES = **1000**（~10h/轮）

### 训练参数

| 参数 | 值 |
|---|---|
| N_EPISODES | 1000 |
| STEPS_PER_EP | 50 |
| BATCH | 128 |
| device | cuda (RTX3060) |
| 地图 | 110 张 H3M 轮换 |
| 对手 | Nullkiller2 (king 难度: maxPass=40, maxRoamingHeroes=4) |
| 对手池 | 70%当前 / 20%早期 / 10%随机 |
| Checkpoint | 每 200 step, 保留 10 个 |
| 监控 | cron `training-report` 每 20min |
| Round 3+ | **V1 稳定后再切 V2**: avg_r≥1.0 中枢且 300ep 无下滑 |

### ⏳ C5: 训练升级（待办）

| # | 任务 | 说明 | 难度 | 状态 |
|---|------|------|------|------|
| C5.1 | 扫描多玩家地图 | 从 maps 目录筛 3p/4p/6p/8p 地图 | 🟡 中 | ✅ 已完成 |
| C5.2 | 升级 AI 对手 | Nullkiller2 queen→king (lastDifficulty=4) | 🟢 低 | ✅ 已完成 |
| C5.3 | 多玩家 StrategicEnv | 环境支持 3+ 玩家 (1v2, 1v3) | 🟡 中 | ⬜ |
| C5.4 | 多英雄管理 | StrategicEnv 支持多英雄控制 | 🟡 中 | ⬜ |
| C5.5 | ELO 固定基线评估 | eval_elo.py 新增 --baseline_type=stupidai | 🟢 低 | ✅ 已完成 |
| C5.6 | **跑一次基线评估** | 已测三次：R2最终50% / 当前最佳50% / vs King NK = 0% | 🟢 低 | ✅ 已完成 |

### ✅ 已完成

- C1: 扩规模训练 (500ep×20步)
- C2: GPU 加速 (cuda)
- C3.1: Checkpoint 保存
- C3.2: 对手池
- C3.3: ELO 评估脚本
- C4.1: 全地图扫描 (110/158)
- C4.2: 参数升级 (2000ep×50步×128batch)
- C4.3: 长程训练启动
- C5.1: 多玩家地图扫描 (158张, 2-8p分布)
- C5.2: AI 对手升级 queen→king (lastDifficulty=4, libmlclient.so 重编)
- C5.5: ELO 基线评估脚本
- C5.6: 基线评估 ×3（R2模型50% / 当前最佳50% / vs King NK 0%）
- **E1: ONNX 模型导出 ✅** — wsl2_model.pt → wsl2_model.onnx (205KB)
- **Checkpoint 趋势分析** — 模型 51K 参数，v2 训练参数开始偏移

---

## Track 2: 真实游戏对齐 🟡（已延期 — 等模型强了再搞）

> **路线变更（2026-07-22）：** 放弃 HD Mod 内存对齐方案，改为直接写 VCMI Windows AI DLL，加载 ONNX 模型控制玩家。
> **2026-07-22 决策：** 暂停部署，继续训练等模型变强后再回来看。

### ✅ E1: ONNX 模型导出 [已完成]

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | 选 best checkpoint `wsl2_model.pt` | ✅ |
| 2 | `torch.onnx.export()` 导出为 `wsl2_model.onnx` | ✅ |
| 3 | ONNX Runtime 验证推理结果一致（diff=0.000000） | ✅ |
| 4 | 推理速度 CPU <5ms | ✅ 已验证 |

**输出：** `wsl2_model.onnx` (205KB)

### ✅ E1.5: WSL 模型验证 [已完成]

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1 | WSL 运行 test_model_game.py 加载模型推理 | ✅ 模型加载+推理正常 |
| 2 | 动作在 VCMI 游戏中生效 | ✅ 英雄从(1,1)移动到(2,1) |
| 3 | 模型行为评估 | ⚠️ 早期阶段，只会选 ↖（训练不足140回合） |
| 4 | WSL 战斗触发 crash | ❌ "Both hero1 and hero2 required" |

### 🟡 E6: PPO Model AI DLL [开发中]

**进展（2026-07-22）：**
- ✅ VCMI Windows 动态 AI DLL 加载机制确认（CDynLibHandler）
- ✅ VCMI_lib.lib 生成成功（4.2MB）
- ✅ ONNX Runtime C++ SDK 下载就绪
- ⬜ 8 个源文件待写（PpoModelAI.h/.cpp, ModelInference.h/.cpp, ObsBuilder.h/.cpp + CMakeLists + exports.def）
- ⬜ 编译 + 部署到 D:\Program Files\VCMI\AI\PpoModelAI.dll
- ⬜ VCMI 开一局选 PpoModelAI 对手验证

**项目目录:** D:\Bigdata\hero3_fresh\ppomodelai\

| # | 问题 | 说明 |
|---|------|------|
| 1 | **VCMI Windows 动态加载 AI DLL** | 非 STATIC_AI 构建下，CDynLibHandler 用 LoadLibraryExW 加载 AI/ 下的 DLL，需导出 GetAiName + GetNewAI |
| 2 | **MMAI vs ENABLE_ML 互斥** | CMake 中 ENABLE_ML 时自动关闭 ENABLE_MMAI。Windows 发行版有 MMAI 无 ML |
| 3 | **strategic_state 符号不在 VCMI_lib.dll** | strategic_state_update、g_adventure_cb 仅在 libmlclient.so（WSL ML 构建）中，Windows 无此符号 |
| 4 | **WSL 训练 NaN crash** | 加载已损坏的 checkpoint 会导致 logits 全 NaN。使用 v2 脚本（GAE λ=0.95 + grad_clip=1.0）缓解 |
| 5 | **WSL VCMI ML 构建战斗崩溃** | "Both hero1 and hero2 are required" — ML 构建的战斗处理有 bug |
| 6 | **动作编码** | StrategicEnv 的 step(action) 控制红方。动作: 0-7=8方向移动, 8=交互, 9=换英雄, 10=结束回合 |
| 7 | **观测 256 维格式** | [0-7]全局(日/周/月/当前玩家/地图宽高/地下/玩家数) [8-103]8玩家×12字段 [104-241]最多6英雄×23字段 [242-255]最多1城镇×14字段 |
| 8 | **VCMI_lib.lib 生成** | 用 lib /name:VCMI_lib.dll /machine:x64 /out:VCMI_lib.lib 从 VCMI_lib.dll 生成 |
| 9 | **ONNX Runtime C++ 下载** | GitHub release onnxruntime-win-x64-1.20.1.zip，放在 C:\Users\Administrator\onnxruntime\extracted\ |
| 10 | **AI DLL 不依赖 GPU** | ONNX Runtime CPU 推理即可，~5ms/步 |

### ⬜ E2: 真实游戏内存读取 [已弃用 — 改为 VCMI AI DLL]

需要确认 HoMM3 HD Mod 的内存结构：

| 字段 | VCMI 观测索引 | 真实游戏内存地址 |
|---|---|---|
| hero_x, hero_y | 0-1 | ? |
| hero_army_count | 2-? | ? |
| gold | ? | ? |
| wood/ore | ? | ? |
| day_of_week | ? | ? |

**验证方法：**
1. 启动 HoMM3 HD Mod，开一局同地图（如 Key to Victory.h3m）
2. 用 Python `ctypes` / `ReadProcessMemory` 读 HoMM3 进程
3. 从已知 HoMM3 内存基址偏移读资源/坐标
4. 跟 VCMI 同图同条件的观测向量逐字段比对

**输出：** `memory_map.json`（字段→地址偏移映射表）

**风险：** HoMM3 内存基址随版本变化。HD Mod 可能改内存布局。需要先用 Cheat Engine / 已知偏移表验证可读性。

### ⬜ E3: 状态注入验证

| 步骤 | 内容 |
|---|---|
| 1 | VCMI 开 Key to Victory，reset 后 dump 观测向量 |
| 2 | 真实游戏开同图同条件，读对应内存字段 |
| 3 | 比对数值（允许 ±10% 误差 = VCMI vs HD 结算差异） |
| 4 | 记录对不齐的字段，分析根因 |

**验收标准：** 80% 字段对齐，关键字段（资源、兵力、英雄位置）全部对齐

### ⬜ E4: 模型推理 + 动作注入 [可行性待验]

| 步骤 | 内容 |
|---|---|
| 1 | 加载 ONNX 模型，读真实游戏状态 → 推理 |
| 2 | 模型输出动作（8方向/交互/结束回合等） |
| 3 | 用 PostMessage 向 HD Mod 窗口发送按键/鼠标 |
| 4 | 验证动作在真实游戏中生效 |

**风险：** 动作空间映射可能对不上（VCMI 的动作编号 ≠ 真实游戏的按键/鼠标）。PostMessage 在 HD Mod 上可能被屏蔽。

### ⬜ E5: 端到端验证

| 步骤 | 内容 |
|---|---|
| 1 | 0 操作跑 10 回合：读状态→推理→发动作→循环 |
| 2 | 记录回放：每步截图 + 模型输出 |
| 3 | 手动回放检查：动作是否合理、状态是否变化 |

**验收标准：** 连续 10 回合无 crash，模型动作在真实游戏中生效

---

## 快速启动

### 查看训练状态
```bash
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/check_training.sh
```

### 启动训练（已运行，不需要再启动）
```bash
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/train_loop.sh 2>&1 &
```

### 启动真实游戏对齐
（待补充——启动 HD Mod 的命令、查看 Cheat Engine 偏移的命令等）

---

## 关键踩坑点

1. **step() 必须是 WAIT→SEND 顺序**
2. **AI 引擎必须是 Nullkiller2**（不 MMAI）
3. **改 Python 源码后必须清 pyc 缓存**
4. **ep_runner 必须用 os._exit(0)**
5. **MLClient headless 用 cond_shutdown**
6. **三件套 .so 必须同源编译**
7. **子 agent 已修复**（不再 401），可派发编码任务，但 WSL 编译/执行需主 agent 跑

详见 `step2分析.md`。

---

## 关键文件

| 文件 | 用途 |
|------|------|
| `train_wsl2_ppo.py` | PPO 训练主脚本 |
| `train_wsl2_ppo_v2.py` | v2 训练脚本（GAE + 梯度裁剪） |
| `ep_runner_one.py` | 单 episode 执行器（支持 --blue_model） |
| `strategic_env.py` | 战略 Gym 环境 |
| `train_loop.sh` | 24/7 循环脚本 |
| `eval_elo.py` | ELO 评估脚本 |
| `scan_maps.py` | 全地图扫描工具 |
| `available_maps.json` | 110 张可用地图列表 |
| `check_training.sh` | 训练状态查询脚本 |
| `wsl2_model.pt` | 最佳模型（PyTorch） |
| `wsl2_model.onnx` | ONNX 导出模型（205KB，脱离 PyTorch） |
| `总任务.md` | 项目全貌 |
| `step2分析.md` | step2 问题分析全记录 |
| `知识库.md` | 单页知识总汇 |
| `问题解答_H3M训练与Xvfb.md` | 外部问题解答（踩坑总结） |
| `checkpoints/` | 模型 checkpoint 目录（保留 10 个） |
| `route-backups/base/` | 基线备份 |
