# 知识库 — HoMM3 全盘操盘 AI

> 单文件知识总汇：项目概述、架构决策、踩坑记录、环境搭建、参数索引
> 最后更新：2026-07-27
|
|---
|
## 一、项目概述

**目标：** AI 完整操控 HoMM3 真实游戏，与你对战（1v7），并战胜你。

**策略：** VCMI 沙盒训练战略模型 → 真实游戏内存操控 → 自对弈持续进化。

**当前阶段：** Phase C7 完成 + passability mask 落地 + Connector 适配完成(N2)，4 张开放 H3M 地图训练中（WSL2, RTX3060, PPO 自对弈）

---

## 二、双轨并行架构

```
┌──────────────────────┐   ┌──────────────────────────┐
│  Track 1: 训练 🟢    │   │  Track 2: 真实游戏对齐 ⬜ │
│  持续提升模型强度      │   │  模型落地到真实 HoMM3    │
│  WSL2 GPU 后台跑      │   │  Windows 内存读取验证    │
│  不占交互注意力        │   │  需主动执行              │
└──────────────────────┘   └──────────────────────────┘
```

**使用方式：**
- 说 **"按当前任务清单去训练"** → 执行 Track 1
- 说 **"按当前任务清单去测试实际游戏"** → 执行 Track 2

**训练进程 `proc_3af048736066` 一直后台跑，任何操作不中断它。**

---

## 三、关键技术决策

### 3.1 Passability（通行性）系统 (2026-07-29)

**方向映射规则**：全系统统一 N-start 顺时针
```
dx = {0, 1, 1, 1, 0, -1, -1, -1}
dy = {-1, -1, 0, 1, 1, 1, 0, -1}
```
0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW。三处 must match：`strategic_state.cpp` passability、`AAI.cpp` moveHero、Python。不一致则模型坍缩。

**计算方法**：`tile.isClear(heroTile)` 通过 `CGameInfoCallback::getTile()` 获取，替代 `CCallback::canMoveBetween()`（太宽松，只查 `isBlockedVisitable`，漏地形/障碍）。

**waitTillRealize 陷阱**：`cb->waitTillRealize = true` 下 `moveHero()`/`endTurn()` 同步等服务器确认，失败时不返回→线程卡死。修复：调用前设 false，调用后恢复。

**Non-red 处理**：MMAI 为三方注册实例。blue/tan 的 yourTurn 必须立即 `selectionMade` + `endTurn`（设 false），否则卡死循环。`AAI.cpp` `AAI::yourTurn()` 实现。

### 3.2 两段式设计

```
训练端 (WSL2):  /home/administrator/vcmi-workspace/, MMAI ON, RTX 3060
推理端 (ARM64): root@172.16.2.40, 不需要 callback, ctypes 直读状态 + ONNX 推理
部署端 (真实游戏): 本机 HD Mod, 内存读取 + PostMessage, 模型推理
```

### 3.2 为什么放弃 ARM64 训练

**根因：** headless=true 下 VCMI 的 `networkHandler->createTimer()` 不触发，游戏不进首回合。
**尝试过：** ctypes→connector 迁移、DummyVecEnv 短路、MLClient 注入 mainLoop、Xvfb —— 全部失败。
**结论：** 根源在 VCMI 服务线程网络层事件循环，涉及 `lib/client/GameEngine.cpp`、`lib/server/CVCMIServer.cpp`、`lib/network/` 源码改造，不确定性大。
**决定：** ARM64 留作推理端，训练全部移到 WSL2。

### 3.3 为什么选 Nullkiller2 而非 MMAI

- MMAI (Mini AI) 模块在 WSL2 上初始化阶段 core dump
- MMAI 含 broken `g_cached_game_state` 代码，清理后依然不稳定
- Nullkiller2 是 VCMI 内置冒险 AI，稳定且已有 AIGateway.cpp 回调钩子
- 切换方式：`ENABLE_MMAI=OFF`, `ENABLE_NULLKILLER2_AI=ON`

### 3.4 训练地图: 课程学习 VMAP 体系 (2026-08-23 起全量使用)

**现状：** 训练 MAPS 全部走课程学习 vmap (Phase I.4)。31 张 Level 0-5 地图 (T01-T06 系列) 已生成并实跑验证，Level 0 (T01×5) 已接入训练。
**历史教训：** 早期 vmap 全部不可用 — train_v1.vmap 从未真正加载成功 (blue hero core:inham 不存在 + wt/ro 地形崩)，gen_v3.py 的 players 数组格式直接 core dump。**"VMAP 兼容性待解决, 暂用 H3M" 的真相 = 生成格式错误, 不是 VCMI 不支持 vmap。**
**vmap 格式要点（VCMI 1.7.4）:**
- header players 必须 dict 格式 {red:{heroes,mainHero,team}, blue:{...}}, 数组格式崩
- terrain 代码: 只用 gr24_ (草地) — wt00_/rc00_ 加载 segfault (待查, 踩坑 #87); rock shortIdentifier=rc 非 ro; 无 road 类型
- town mask 5x3 anchor 居中 → town_x∈[2,w-3], town_y∈[1,h-2], 越界左崩
- hero/资源/野怪: 标识符必须真实存在 (core:edric/iona/gold/wood/crystal/swordsman), resource 需 options.amount
- 验证必须 ep_runner 实跑 20 步, 不能只查 zip 结构 (test_vcmi_load.py 是假验证)
- 生成脚本: maps/training/gen_curriculum_all.py (T01-T04, 坐标规则化+界内校验)

### 3.5 观测与动作

- 观测 ~256 维：英雄位置/兵力/移动力、城镇/资源、敌方可见信息、日期
- 动作：移动(8方向) + 交互 + 城镇操作 + 结束回合
- AI 对手使用 Nullkiller2（不耗 ML 推理）

### 3.6 step() 通信机制（C7 最终架构 + B 修复 + #45 修复）

```
Python step(action):
  ① _send_action(action)        // 发 action 给 VCMI（写 atomic s_turn_action）
  ② _adventure_wait()           // 等 VCMI 处理完在下一轮 process_turn 阻塞
  ③ _read_state()               // 读状态（从 cb 方法填充，非 CGameState）

C++ yourTurn() → 单次 action:
  ① adventure_process_turn()    // 阻塞等 Python 发 action（spin-loop）
  ② adventure_get_action()      // 从 atomic 读 action
  ③ switch(action): moveHero    // 直接 cb->moveHero（selectionMade 之前）
  ④ cb->selectionMade(queryID)  // 回答 query
  ⑤ fill_state_from_cb(cb)      // 用 cb 方法填充 state（绕过 CGameState!）
  ⑥ compute_passability_cb(cb)  // 用 cb->canMoveBetween 算 passability
  ⑦ cb->endTurn()
```

**修复 #45 的关键（2026-07-28）：**
- `strategic_state_update(&igic->gameState())` → **空**，因为客户端 CGameState 在 yourTurn 时未同步
- 替换为 `fill_state_from_cb(cb)`，使用 `cb->getHeroesInfo()`、`cb->getPlayerState()`、`cb->getResource()` 等方法直接填充
- `cb->getHeroesInfo()` 一直有数据（moveHero 用它成功了 5000+ ep），但之前 strategic_state_update 走错了数据源

**#45 实际阻塞点（2026-07-28 发现）：**
- ep_runner 子进程 `stderr=subprocess.DEVNULL` → MMAI 的所有 `fprintf` 诊断全丢弃
- VCMI 内部重定向 stdout/stderr（CBasicLogConfigurator），MMAIA DIAG 输出不可见
- 改用写文件 `/tmp/mmai_diag.txt`（fopen+fprintf+fclose 绕过 VCMI 日志层）可见诊断
- **更深层问题**：connector_v13 与 libmlclient 的 `init_vcmi` ABI 不一致（3-arg vs 1-arg）
- connector 代码用旧 3-arg API，libmlclient 已改为 1-arg void* → 运行时 core dump
- connector 编译时 CMakeLists.txt 第 11 行 `set(VCMI_DIR /home/administrator/vcmi-native)` 硬编码覆盖 `-DVCMI_DIR`
- connector 必须与 libmlclient/MMAI 编译自同一 schema 版本（BATTLE_ROUND vs BATTLE_SIDE 冲突）

**关键不变：** SEND→WAIT→READ 顺序，无 race condition。state_update 在 process_turn 阻塞后执行，Python 在 _adventure_wait 返回后才读状态。

### 3.7 C7 动作映射架构

```
Python PPO policy (model)
    ↓ action
strategic_env.py step()
    ↓ ctypes 写 g_rl_action + adventure_send_action
C++ adventure_process_turn spin 退出
    ↓ read g_rl_action
AAI.cpp yourTurn → cb->moveHero() 直接执行
    ↓
cb->endTurn() → VCMI 推进到下一玩家
```

| 组件 | 位置 | 作用 |
|------|------|------|
| g_rl_action | strategic_state.h/cpp | 全局变量，Python ctypes 写入，C++ 读取 |
| adventure_process_turn | strategic_state.cpp | spin-loop 等 Python action |
| adventure_get_action | strategic_state.cpp | 读 g_rl_action |
| strategic_state_update | strategic_state.cpp | 从 CGameState 填充 256 维观测 |
| AAI::yourTurn | AI/MMAI/AAI/AAI.cpp | 红方控制枢纽：state_update → process_turn → moveHero → endTurn |
| ServerPlugin start/endBattleHook | server/ML/ServerPlugin.cpp | 战斗钩子，hero2=null 时跳过（防崩） |

**非红方（蓝方）**：AAI.cpp 的 pc!=0 guard 直接 endTurn，不进 while 循环。蓝方由 VCMI 内置 AI（MMAI）控制，但拦截后直接结束，不会和 Python 交互。

### 3.8 战斗处理

英雄踩怪物：
1. startBattleHook(hero1, hero2=null) → return（跳过 ML 随机初始化）
2. VCMI autofight 自动裁决
3. endBattleHook(heroDefender=null) → return（跳过 stats 记录）
4. 战斗完成，继续 turn 循环

---

## 四、踩坑大全

### 4.1 step2 挂死（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | SEND→WAIT 顺序导致 `s_turn_player` 被提前消费 |
| 修复 | WAIT→SEND + 切 Nullkiller2（回调后 fall through，不手动 endTurn） |
| 验证 | 5 步全通，vloss 769→45 |

### 4.2 MMAI core dump（已绕过）

| 项目 | 内容 |
|---|---|
| 根因 | 旧 MLClient 含 broken `g_cached_game_state` 代码 |
| 修复 | 清理，切 Nullkiller2，用 cond_shutdown 版本 |

### 4.3 ABI 不兼容（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | vcmi-native/workspace 两套源码混搭 .so |
| 修复 | 从 vcmi-native 全量重编三件套：libvcmi.so + libmlclient.so + connector_v13 |

### 4.4 .pyc 缓存问题（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | NTFS 文件系统 pyc 过期检测不可靠 |
| 修复 | 部署后 `find ... -name __pycache__ -exec rm -rf {} +` |

### 4.5 subprocess 僵尸（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | VCMI 线程阻止 Python 退出 |
| 修复 | `os._exit(0)` 硬退出 |

### 4.6 DummyVecEnv 短路（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | PPO 构造时 DummyVecEnv 调 reset，导致 adventure_wait 阻塞 |
| 修复 | reset() 加 `_vcmi_just_started` 标志，跳过一次 |

### 4.7 子 agent 401（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | delegation.provider=custom，硬编码 api_key 过期 |
| 修复 | provider 改为 deepseek，api_key 留空走 DEEPSEEK_API_KEY 环境变量 |

### 4.8 用 vmap 跑战略训练（2026-08-23 已解决）

| 项目 | 内容 |
|---|---|
| 根因 | 早期 vmap 生成格式全错 (players 数组/inham/wt-ro 地形/town 越界) |
| 修复 | 统一生成脚本 gen_curriculum_all.py + dict players + 全草地 + 坐标规则化; T01-T04 实跑验证通过 (20 步全满正奖励) |
| 现状 | 训练 MAPS = T01×5 (Level 0), 后续 Level 1-5 按课程晋级切换 |
| 参考 | 踩坑 #84-90 |

---

## 五、训练参数

### 当前训练（C4）

| 参数 | 值 |
|---|---|
| 算法 | PPO |
| 网络 | MLP: 256→128→128→11(actor)/1(critic) |
| Episodes | 2000 |
| Steps/ep | 50 |
| Batch | 128 |
| 学习率 | 3e-4 |
| Clip | 0.2 |
| Epochs | 4 |
| 设备 | cuda (RTX3060) |
| 地图 | 110 张 H3M |
| 对手池 | 70%当前 / 20%早期 / 10%随机 |
| Checkpoint | 每 200 step, 保留 10 个 |
| 模型 | ~203KB (.pt) |

### 观测向量结构 (256 维)

| 索引 | 内容 | 长度 |
|------|------|------|
| 0-7 | Global (day/week/month/player/map) | 8 |
| 8-103 | Players (8 × 12字段) | 96 |
| 104-241 | Heroes (6 × 23字段) | 138 |
| 242-255 | 填充零 | 14 |

### 动作空间 (11)

| ID | 动作 |
|----|------|
| 0-7 | 8 方向移动 |
| 8 | 交互（拾取/对话/攻击） |
| 9 | 下一英雄 |
| 10 | 结束回合 |

---

## 六、环境搭建

### WSL2 VCMI 编译

```bash
# 三件套同源编译（必须！）
cd ~/vcmi-native
cmake .. -DENABLE_ML=ON -DENABLE_MMAI=ON -DENABLE_NULLKILLER2_AI=ON
cmake --build . --target vcmi -j4
cmake --build . --target mlclient -j4

# Connector 编译（需 schema 同步：v14/v15 从本地 vcmi 复制）
# 新版 libmlclient 用 1-param init_vcmi(void*)，connector 适配
cp -r /mnt/d/.../vcmi/AI/MMAI/schema/v{14,15} ~/vcmi-native/AI/MMAI/schema/
cd /mnt/d/Bigdata/hero3_fresh/vcmi_gym/connectors/build
cmake .. && cmake --build . --target connector_v13 -j4
cmake --build . --target connector_v14 -j4
cmake --build . --target connector_v15 -j4

# 部署（备份旧 .so + 复制新 .so）
cp rel/*.so rel/*.so.bak.$(date +%Y%m%d)
cp build/connector_v*.so rel/

# 环境变量
export LD_LIBRARY_PATH=~/vcmi-native/rel/bin:~/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=~/vcmi-native/rel/bin/libmlclient.so
```

### Connector 版本说明

| 版本 | 观测编码 | 返回类型 | adventure | 当前使用 |
|------|---------|---------|-----------|---------|
| v13 | 固定 264 维数组 | P_State | ✅ | **当前训练** |
| v14 | 同 v13（参数更细） | P_State | ❌ | 未使用 |
| v15 | 图结构（nodes+links） | py::dict | ❌ | Phase G 前迁移 |

### 启动训练

```bash
# 清 pyc
find /mnt/d/Bigdata/hero3_fresh -path "*/__pycache__" -type d -exec rm -rf {} +

# 24/7 循环
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/train_loop.sh 2>&1 &

# 查看状态
MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/check_training.sh
```

---

## 七、内存偏移表（快速索引）

### CN 3.1 (Heroes3.exe) — 固定地址

**玩家结构体：** `pb = *0x0082B0BC`

| 字段 | 偏移 | 已验证 |
|------|------|--------|
| gold | pb+0xB4 | ✅ |
| wood | pb+0x9C | ✅ |
| ore | pb+0xA4 | ✅ |
| mercury | pb+0xA0 | ✅ |
| sulfur | pb+0xA8 | ✅ |
| crystal | pb+0xAC | ✅ |
| gems | pb+0xB0 | ✅ |
| hero_count | pb+0x01 | ✅ |
| town_count | pb+0x3E | ✅ |

**英雄结构体：** `hero_addr = gd + 1170*hid + 136736`, `gd = 0x00826D40`

| 字段 | 偏移 | 已验证 |
|------|------|--------|
| pos_x | hero+0x00 | ✅ |
| pos_y | hero+0x02 | ✅ |
| pos_z | hero+0x04 | ✅ |
| cur_movement | hero+0x4D | ✅ |
| max_movement | hero+0x49 | ✅ |
| level | hero+0x55 | ✅ |
| attack | hero+0x476 | ✅ |
| defense | hero+0x477 | ✅ |
| power | hero+0x478 | ✅ |
| knowledge | hero+0x479 | ✅ |
| exp | hero+0x51 | ✅ |
| army_count[0..6] | hero+0xAD + i*4 | ✅ |
| army_type[0..6] | hero+0x91 + i*4 | ✅ |
| in_battle | 0x00825BF8 (3=战斗) | ✅ |

### HD Mod 5 RC94 + HOTA 1.6.1 — AOB 动态扫描

**玩家指针：** `base + 0x29CCFC` → pb

**英雄地址：** `pb + 0x278E0`（CN31 的 gameData 数组完全不一样）

已验证偏移同 CN31：pos_x/y, movement, max_movement
推断同 CN31（待验证）：资源, 属性, 兵力

> 详见 `对齐清单_CN31.md` 和 `对齐清单_HD.md`

---

## 八、关键文件索引

| 文件 | 用途 |
|------|------|
| `docs/总任务.md` | 全局架构、Phase A~G 进度 |
| `docs/当前任务清单.md` | 双轨可执行任务表 |
| `对齐清单_CN31.md` | CN 3.1 完整内存偏移 |
| `对齐清单_HD.md` | HD Mod 内存偏移 |
| `train_wsl2_ppo.py` | PPO 训练主脚本 |
| `ep_runner_one.py` | 单 episode 执行器（支持 --blue_model） |
| `train_loop.sh` | 24/7 循环脚本 |
| `eval_elo.py` | ELO 评估脚本 |
| `scan_maps.py` | 全地图扫描 |
| `strategic_reader.py` | Python ctypes 直读游戏状态 |
| `check_training.sh` | 训练状态查询 |
| `docs/知识库.md` | **本文件 — 单页知识总汇** |
| `docs/踩坑记录.md` | 踩坑详细记录 |
| `docs/step2分析.md` | step2 问题分析全记录 |
| `checkpoints/` | 模型 checkpoint 目录 |
| `maps/` | 158 张 H3M 地图 |
| `available_maps.json` | 110 张可用地图列表 |
| `scripts/` | 历史测试/一次性脚本 |
| `_archive/` | 已完成/废弃旧文件 |

---

## 十一、StrategicState 结构体布局（C++ ↔ Python ABI）

```cpp
// C++ struct (WSL, libmlclient.so)
int32_t day, week, month, current_player;     //  16 字节
int32_t map_width, map_height;                 //   8
int32_t has_underground, player_count;         //   8
StrategicPlayer players[8];                    // 384 (8×48)
StrategicHero   heroes[8];                     //1216 (8×152)
StrategicTown   towns[8];                      // 704 (8×88)
int32_t game_over;                             //   4
int32_t action;                                //   4  ← Python 写入的 RL 动作
int32_t _version;                              //   4
int32_t passable[8];                           //  32
// Total: ~2380 字节
```

**关键字段偏移**（Python ctypes 必须匹配）：
- `game_over` @ 2336
- `action`    @ 2340  ← 之前漏了这个字段！
- `_version`  @ 2344
- `passable`  @ 2348  ← 没 action 时会前移 4 字节，数据全错位

## 十二、数据流（修复后）

```
VCMI server → AI::yourTurn()
  → strategic_state_update(CGameState*)   // dlsym 调用，填充所有字段
  → g_adventure_cb ? callback : fallback   // g_adventure_cb 通常为 null
  → fallback: 读 action → moveHero → endTurn
  ↓
Python → 读 g_strategic_state (ctypes)
  → obs = non-zero (真实英雄位置、资源、passability)
  → 模型输出 action
  → adventure_send_action(action)  // 写入原子变量
  → 等待下一轮
```

## 十三、WSL 双目录构建陷阱

| 目录 | 用途 |
|------|------|
| `/home/administrator/vcmi-native/` | 源码（可编辑） |
| `/home/administrator/vcmi-native-build/` | cmake 源目录（`CMAKE_HOME_DIRECTORY`）|
| `/home/administrator/vcmi-native-build/rel/` | 构建目录（编译产物） |
| `/home/administrator/vcmi-native/rel/` | 部署目录（训练时加载的 .so）|

**改代码后必须同步两份**：`cp vcni-native/* vcmi-native-build/*`。不然改了 vcmi-native 的 .cpp，编译的还是 vcmi-native-build 的旧代码。

**RUNPATH 陷阱**：`libmlclient.so` 和 `vcmiserver` 的 RUNPATH 指向 `/home/administrator/vcmi-native-build/rel/bin/`，运行时优先从 build 目录加载 `.so`。部署到 `rel/` 后靠 `LD_LIBRARY_PATH` 覆盖。

**#46 修复关键**：重建三件套（vcmiserver + libmlclient.so + libMMAI.so）后 segfault 消失。installNewBattleInterface 全流程通过（加 fprintf 确认）。工作组合见 `WSL踩坑点.md` 第50项。

**当前阻塞（2026-07-29）**：installNewBattleInterface 修复后通，但 game main loop 启动时 segfault。非代码改动导致，WSL 重启后稳定复现，所有组件版本组合均崩。需 gdb backtrace 定位。另 `adventure_wait_for_turn()` 信号量机制不工作（`AAI::yourTurn` 不设原子变量），`obs_nz=0` 的根本原因。

===

✅ **2026-07-29 全线打通**：env.reset() 返回 obs_nz=8/264！全部修复：
- Discord null dereference（`GameEngine::hasDiscord()` guard）
- 信号量通信（`AAI::yourTurn` 调 `adventure_process_turn()`）
- Hero pool even 检查（`pop_back` 替代 throw）
- step() 5 步无崩溃
- 工作组合全部用最新重建产物（见 `WSL踩坑点.md` 第十~十一节）

**当前剩余：** obs_nz=8 仅 passable。`getHeroesInfo()` 返回空（地图无初始英雄），`fill_state_from_cb` 需迭代。
```


## 十四、StrategicEnv 循环打通 (2026-07-29)

**env.reset() + step() 循环完整可跑通**，战斗自动解析。

### 关键修复

| 问题 | 修复 |
|------|------|
| battle 卡死 (MMAI_USER 等待 step 回调) |  战斗自动解析，不通过 connector 回调 |
| obs_nz=8 (状态数据空) | 根因已定位： 在  前调  → 空 |

### 验证结果


### 待修：obs_nz=8 根因

 结构：


 在 async task 之前同步执行，此时 query 未答 →  空。

### 修复路线

**方案 A（推荐）**:  中  改用  public 方法：
-  → day/week/month
-  → player + heroes via 
-  → resources
- 不需要 CGameState 访问权限，可能绕过 query 限制

**方案 B**: 加全局 CGameState* 指针， 的 async task 设置， 读取。

**方案 C**: Python 侧 fallback。


## 十五、obs_nz 修复 — CGameInfoCallback 方案 (2026-07-29)

**obs_nz: 8 → 34，奖励: -0.1 → +6.15**

### 根因

部署版  结构：


 中  → 空（query 未答）。
 的  是 public 方法，绕过 query 限制。

### 修复

1.  —  改用  public 方法：
   -  → player + heroes
   -  → hero 数据
   -  → 资源

2.  — 全局  指针：
   -  中 
   -  读取该指针

3. 重编 2 个 .so： + 

### 局限性
- `player_lib` 模式只能看到红方自己，看不到蓝方（callback 权限限制）
- 修复前 `map_size`/`day` 未填充（`adventure_process_turn` 缺失日历和地图信息）
- `passability` 在 Python 侧计算（`obs[-8:]`，不受 C++ 影响）

### 验证

---

## 七、connector 日历/地图填充（2026-07-29）

**问题：** `adventure_process_turn()`（connector 路径）不填 `day`/`week`/`month`/`map_width`/`map_height`/`has_underground`，只有 `strategic_state_update()`（dlsym 路径）会填。

**影响：** 训练缺时间感知（周/月信息），可通行性方向计算缺地图边界验证。

**修复：**
- `strategic_state.cpp:adventure_process_turn()` 加两个填充块：
  1. 日历：`gicb->gameState().day` → `state.day/week/month`（匹配 `strategic_state_update` 的 `(gs.day-1)/7+1` 算法）
  2. 地图尺寸：`gicb->getMapSize()` → `state.map_width/height/has_underground`
- 同步到 WSL2 4 个副本（`hero3_vcmi`/`vcmi-native`/`vcmi-native-build`/`vcmi-build-latest`）

**原则：** 避免用 `getCalendar()`（部署版不可用），改用 `gameState().day` 直接访问 `CGameState::day`。

---

## 八、#45 EEXIST 解锁 + v15 connector 重建（2026-07-29）

**问题：** `boost::filesystem::create_directories: File exists [system:17]: "./data"` 在 v15 connector 初始化时抛异常。

**根因：** `vcmi-native-build/rel/bin/data` 是 cmake POST_BUILD 创建的坏符号链接（`data -> ../../data` 指向 `/home/administrator/data` 不存在）。`boost::create_directories` 对已存在的符号链接抛 EEXIST。

**修复：**
- 删符号链接，建真实目录 `rel/bin/data/`，内部用 `ln -sf` 链接具体文件
- 同时修复：所有 config 目录的所有大小写变体写入有效 JSON
- 删除递归 config 符号链接（`config/config -> ../../config`）

**v15 connector 重建：** 清 CMakeCache 后 `cmake .. -DVCMI_DIR=/home/administrator/vcmi-native` 重建成功（681KB）

**已知问题：** v15 VcmiEnv init 后在中立玩家 `installNewBattleInterface` 后 segfault（独立问题，不阻塞 #45）

**训练重启：** 清旧模型（wsl2_model.pt + checkpoints）后重启 train_loop.sh，`obs_nz=61`（含 day/map_size 填充），V2 PPO 在跑。

---

## 九、C8 行为克隆计划（2026-07-29 讨论）

### 动机
自对弈（red=MMAI_USER, blue=MMAI_USER）双方只会 act=10（END_TURN），模型塌缩。根因不是奖励函数，而是对手死了。

### 新路径
行为克隆（BC）预训练 → PPO 微调。

**Step 1:** Nullkiller2 双开采集数据（red=Nullkiller2, blue=Nullkiller2）
**Step 2:** 从 Nullkiller2 的移动推断 action（dx/dy → 方向映射表）
**Step 3:** 行为克隆训练（CrossEntropyLoss, 只训 actor）
**Step 4:** PPO 微调（加载 BC 权重, blue=Nullkiller2 作为对手）

### 优点
- Nullkiller2 能探索、占矿、攻城、城镇管理
- 模型从真实行为学习策略，不是从零随机探索
- 零训练时间浪费在"学 END_TURN 不动"

### Nullkiller2 城镇管理评估
- 建筑顺序：保守但合理（城堡→兵营），不够优但不影响 BC
- 招兵策略：全招满，不挑
- 多英雄控制：会招第二个但分配一般
- 对 BC 阶段：**足够产生有意义数据**

### 1v7 最终需求分析（讨论总结）
当前架构受限的三个根本问题：
1. **模型是瞎子**—obs 缺地图探索、敌方位置、已探索区域、战争迷雾
2. **PPO 无记忆**—MLP 不记得上周做了什么
3. **单 Agent 限制**—多英雄协调/分工超出当前 PPO 能力

需要扩展的维度：探索格点地图、敌方感知、切英雄动作、记忆网络（LSTM/RNN）。
详见 `总任务.md` 的 1v7 需求清单。


---

## C8.2 验证结论 — Nullkiller2 对手链路打通 (2026-07-31)

### VCMI 玩家 AI 分配机制（关键架构认知）

```
CClient::initPlayerInterfaces (client/Client.cpp)
  └─ onlyai=true → 所有玩家都创建 AI 接口
     └─ aiNameForPlayer(ps, battleAI=false, alliedToHuman)
        ├─ ps.name 非空且 isAvailableAdventureAI(ps.name)  → 用 ps.name（仅 "Nullkiller2"/"EmptyAI"）
        └─ 否则: alliedToHuman ? adventureAlliedAI : adventureEnemyAI
           ├─ alliedToHuman = 玩家与某个 human 玩家同队
           └─ onlyai 时 debugStartTest 把 host 从玩家颜色移除 → 无 human → 全走 adventureEnemyAI
```

**当前部署配置**（MLClient.cpp processArguments）:
- `adventureAlliedAI = "MMAI"` → 玩家0（red）= 模型注入（AAI::yourTurn）
- `adventureEnemyAI = "Nullkiller2"` → 其他玩家 = 真 AI 对手
- `combatAlliedAI = "MMAI"`（战斗自动解析）

**构建依赖链**: Client.cpp → libvcmiclientcommon.a → **libmlclient.so**（ML/CMakeLists line 30: mlclient PUBLIC vcmi vcmiclientcommon MMAI）。vcmiserver 不含 client 代码，改 Client.cpp 后重链 libmlclient.so 即可，vcmiserver 无需动

### InitArgs ABI 真理来源

- 头文件布局 ≠ .so 实际布局（33 字段 string 版 vs 28 字段 IModel* 版）
- 真理 = `gdb -batch -ex 'ptype ML::InitArgs' <libmlclient.so>`（debug build 含 DWARF）
- 部署 .so 是 28 字段（MLClient.cpp 引用 a.leftModel 证实），connector 调用也按 28 字段

### 战斗集成状态

- **英雄 vs 英雄**: ServerPlugin startBattleHook 完整逻辑（random heroes/vips/armies/mana/swap）
- **英雄 vs 野怪**: 跳过双英雄逻辑，VCMI autofight 处理（startBattleHook/endBattleHook 保护）
- **已知未解决**: v15 VcmiEnv 中立玩家 installNewBattleInterface segfault（Phase D）

### NK2 对手特征（For Sale.h3m 实测）

- 单回合耗时: 数十秒级（多线程 TBB 规划，HeroMoved/tileRevealed 高频）
- 活动: 移动/探索/城镇建设/买兵/招募英雄全链条
- **3 人图问题**: tan 玩家也是 NK2（adventureEnemyAI）→ 额外拖慢。C8.3 需确定 2 人训练图集（For Sale 有 tan；Elbow Room 6 人不可用；h3m 2 人图待扫描）
- obs 限制: StrategicState 只含己方（player_count=1），敌方英雄位置不可见（1v7 需求项 #2 待解决）

### C8.3-C8.5 BC 预训练链路（2026-08-01 推进）

**采集管道（C8.3）**
- 架构: red=Nullkiller2 自主玩（学习对象），blue=MMAI 自动 endTurn；NK2 每个决策点（moveHeroToTile/endTurn）阻塞采集 (obs, action)
- C++: `adventure_capture_turn()`（填 obs + 记录 NK2 action + 阻塞等 Python）；MLClient.h InitArgs 末尾加 red/blue 冒险 AI 字符串（带默认值保持 28 位置参数兼容）；AIGateway.cpp moveHeroToTile + endTurn 采集 hook；makeTurn catch-all 补 endTurn()（NK2 异常防卡死）
- NK2 卡死特征: `Unable to complete chain. Expected hero X to arrive to (y z w) in 0 turns` 循环 → chain 重试死循环（~50% 概率）→ 子进程永久挂起
- 2 人图集: Dungeon Keeper / Key to Victory / Good Witch, Bad Witch / Fort Noxis（scan_players_v2.py 158 张全解析，slots=[0,1]）

**Watchdog 机制（2026-08-01 修复）**
- 子进程隔离 + 整局硬超时: `subprocess.run(timeout=900)`，TimeoutExpired → kill 跳局
- 关键: NK2 卡死可发生在 reset 启动阶段（env 内部 boot_timeout/vcmi_timeout 只覆盖采集循环），必须有子进程级兜底
- 后台进程 stdout 必须重定向日志文件（否则输出进 pipe 无人读，排查全靠猜）

**BC 训练（C8.4）**
- bc_train.py: CrossEntropy 11 分类，网络与 PPO Net 一致（fc 264→128→128, actor 11, critic 1），critic 随机保留
- 24 局 435 pairs 出 bc_model.pt（best_val=5.4），预测分布覆盖 9 类动作（不塌缩）
- 数据少（<500 pairs）只 WARNING 不阻断；类权重 1/count 加权少数类

**PPO 微调（C8.5）**
- train_wsl2_ppo_v2.py: BC_PATH 存在则 fc+actor 用 BC 权重，critic 随机（`sd.pop("critic.*")` + strict=False）
- 关键坑: 旧 wsl2_model_state.pt 存在会抢占加载路径（resume_step>0 跳过 BC）→ 启动前必须删/挪 state 文件
- 配置: MAPS=4 张 2 人图（无 tan 拖慢），blue_adventure_ai=Nullkiller2 真对手，reward_explore=1.0（新格子 +1），1000eps×200steps
- 奖励原则落地: 探索奖励用 env 内 _visited 集合（每局 reset），reward_explore>0 才启用

**C8.5 战斗系统修复链（2026-08-01 夜~晨）**
- **进程内 server**: useProcess=false → server 代码链接进 **libmlclient.so**（改 BattleResultProcessor 等 server 逻辑必须 make mlclient，不是 vcmiserver！验证: grep -acl "消息文本" rel/bin/*）
- **战斗 AI 三选一全废**: ① settings 键在 `"ai"` 路径（`{"server",...}` 无效路径 → 用 schema 默认 BattleAI → headless 等待回调卡死）② libStupidAI.so 只有 GetNewBattleAI 无 GetNewAI（冒险 AI 加载崩）③ MMAI battleStarted 崩（Router::battleStart `ASSERT(cb->getPlayerID()->hasValue())` — neutral 无 playerID → throw 穿 noexcept → std::unexpected）
- **修复**: 战斗 AI 全走 MMAI 体系（leftModel/rightModel=Scripted("StupidAI") 自动裁决，即 #46 机制）；Router neutral 无 playerID 用 modelRight + 整体 try-catch fallback StupidAI；战斗结果对话框 `IFML(true,false)` 禁用（ML 模式 AI 不回答 CBattleDialogQuery → 永久卡）
- **moveHero 等待**: AAI::yourTurn moveHero 后轮询位置（最多 2s）再 endTurn（异步未实现就切回合 → 卡死）；NK2 用 waitTillFree（等 heroMoved）正常

**NK2 内存炸弹（2026-08-01 09:22）**
- NK2 单局内存 3.7-7.5GB（1 分钟 430MB→3.7GB 膨胀）→ WSL 8GB OOM 崩溃；EmptyAI 430MB / MMAI_RANDOM 493MB 正常 → NK2 确凿
- nk2ai-settings.json（config/ai/nk2ai/）openMap 已全关、bucket 小 → settings 无解；TBB global_control 限 4 线程无效 → 根因未明（Phase D 深挖：疑似 Nullkiller analyze/memory 累积）
- **替代对手**: MMAI_RANDOM（自动随机行动，内存 493MB，每步 2s）— ep_runner `--blue_ai MMAI_RANDOM --blue_adventure_ai MMAI`

**C8.5 奖励结构教训（2026-08-01 10:00）**
- **被动 gold 收入不能做 per-step 奖励**: reward_gold_mult=0.01 → END_TURN 后 day 推进被动 gold +500~1000 → 每步 +5~10 → 模型坚守 END_TURN（r=2000/200 步全是 act=10）→ 改 0.0
- 交互（act=8）含英雄升级经验奖励（exp×0.001）→ 免费正奖励（+2.9）→ 模型"交互一次→END_TURN 刷到底"
- 对局 200 步固定、END_TURN 不结束 → -0.1/步是最低损耗 → 无事件奖励（占矿/杀敌）时模型无主动做事动力
- **结论**: PPO 微调无 KL 约束会偏离 BC 塌缩；事件奖励（占矿+10/杀敌+100/占城+50）是主动行为驱动（需 strategic_state 矿归属/战斗结果扩展）；态势感知（#1-4/#8/#13）是 1v7 最小阻塞集

**VCMI 上游研究（2026-08-01, GitHub 实查）**
- 官方 vcmi/vcmi: 最新 release 1.7.4（2026-05），develop=1.8.0 开发线；本地仓库 remote 即 smanolloff/vcmi fork `develop+v15+ml` tip（+37 本地提交），已对齐无需升级基线
- **fmt 依赖**: 只在 `client/CMakeLists.txt` 的 `if(ENABLE_DISCORD)` 块内 find_package（与 glaze 一起，供 discord-presence）→ 训练构建 `-DENABLE_DISCORD=OFF` 直接跳过，无需装 libfmt-dev
- **MMAI v15 "Graphmind" PR #7654**（2026-07-31 draft）: 图节点观察（Global/Player/Unit/Hex/Action）+ GNN，vs BattleAI 镜像 89%（v13 80%）；无施法/无 tactics；v15 模型由 vcmi-mods/mmai mod 发布。官方 develop 只合入 v13（onnxruntime 后端）；#7654 合入后官方原生支持 v15 → Phase D 战斗集成对齐此方向
- **vcmi-gym 官方 RL 项目**（smanolloff/vcmi-gym, 2026-07-31 活跃）: v13/v14/v15 环境 + MPPO/MPPG/PPO-DNA/MQRDQN/MuZero 全家桶，PBT+W&B；**官方经验: flat CNN+FCN 效果最好，self-attention/residual/LSTM 反而更差，Transformer 不适用（观察近 Markovian）**——⚠️ 挑战我们 1v7 阻塞集 #13（RNN/LSTM 记忆），但注意这是**战斗层**结论（回合内局部观察），战略层（地图探索/长期规划）记忆需求可能不同，需验证
- **战略层 RL 是空白**: 官方/社区无现成战略层方案 → 我们的 strategic_state + 战略 PPO 是独有资产；1.8 Lua scripting（modding API TODO）未来可能提供更干净集成接口
- **NK2 修复**: #7504 Dimension Door（07-01 合入）、#7413 传送门探索（06-06）、#7352 守卫拾取物绕行（07-04）、**#7613 路线失败循环（open 07-20）— 合入后 BC 采集 ~50% deadloop 概率应显著下降**、#7632 寻路提速（open）
- 行动项: 跟踪 #7654 合入后评估本地 37 提交从 fork 迁官方 develop；NK2 对手升级等 #7613 合入后 rebase

**B 态势感知实现要点（2026-08-01）**
- StrategicState 扩展字段放**结构体末尾**（现有字段偏移不动 → 旧 ctypes 定义仍对齐，ABI 安全）；_version 从 1→2
- fill_exploration() 读 `team->fogOfWarMap[int3(x,y,z)]`（TeamState per-player，非全知）⚠️ 待验证：VCMI 注释 visible vs 累计 explored，影响"走过又离开视野"的格子
- local_tiles 15×15 编码 0=未知/1=可通行/2=障碍（物体与 1 合并，宁简勿错）；global_explored 32×32×2 下采样 ceil 块，块内任一探索=1
- active_hero 跨 .so 共享走 extern "C" 全局（g_ml_player_cb 同模式）；AAI.cpp act==9 切换 g_active_hero=(g_active_hero+1)%n，移动用 heroes[g_active_hero]
- cmake POST_BUILD create_symlink 对**已存在目录**失败（目录 ≠ symlink）→ data 是真目录时需先移走再 build，build 后手动 ln -s 指向游戏数据
- CMakeCache 损坏重配后，vcmi-native 编译目录必须与项目源逐文件 diff 对齐（user_agents/、MLClient.cpp 都可能旧版）

**采集排障新陷阱（2026-08-01）**
- **VCMI settings 写读层不一致**: `Settings(settings.write({"ai", ...}))` 写 session 层, Client.cpp `settings["ai"][...]` 读配置层 → 写入不生效（读默认值）。训练没暴露（red 默认 MMAI 恰好正确），采集（NK2）暴露。**跨 .so 直传方案**: `extern "C" char g_adventure_allied_ai[64]`（MLClient 定义+strncpy / Client.cpp 读）——g_ml_player_cb 同模式
- **extern "C" 语法**: `extern "C" extern char x[64];` 非法（invalid use of 'extern' in linkage specification）；函数内 `extern "C"` 也非法（只能命名空间作用域）。正确: 文件作用域 `extern "C" { extern char x[64]; }`
- **TerrainTile::isClear(from) 的 from 不能为 nullptr**: VCMI 实现里 from->getTerrain() 解引用 → segfault。必须传有效 tile（英雄所在格）
- **fill 无锁直读 CGameState = 数据竞争**: fill 在 NK2/MMAI 后台线程执行, 直读 gs.getMap()/fogOfWarMap 与 AI 规划线程竞争 → NK2 决策损坏（症状: moveHero 全被服务器拒的死循环, 非崩溃）。必须 `std::shared_lock gsLock(CGameState::mutex)`（AAI.cpp 同模式）
- **编译树 vs 项目源版本漂移**: vcmi-native（编译树）AI/MMAI 只有 v13, 项目源是 fork tip（v14/v15 Graphmind draft）→ 不能全量同步 MMAI（编译风险）；router.cpp 等关键修复文件单独同步。AIGateway.cpp 采集 hook 在项目源但编译树没有 → 重编 libNullkiller2.so 前必须同步
- **NK2 卡死（chain retry）是固有的**: ~50% 概率, day 4+ 后常见（moveHero blocked 死循环）。采集用 watchdog 900s + 子进程隔离跳局, 属正常流程（C8.3 同）
- **collect close 阶段 segfault**: SAVED 之后 close() 崩溃（dumped core）——数据已落盘, 不影响采集（C8.3 已知, 子进程隔离处理）

## H.6-H.7 动作空间落地（2026-08-15 完成）

**H.6 动作 11-24 实现（reasonix CLI 代写 + Hermes 验证）**
- 位置: vcmi/AI/MMAI/AAI/AAI.cpp（战略层动作执行点，非 strategic_state.cpp）
- 11-13 SPLIT×3: splitStack 分 1/3、1/2 给最近友方英雄; SPLIT_ALL 用 bulkMoveArmy（bulkSplitStack 是军队内部平铺不能跨英雄）
- 14 MERGE_FROM: mergeStacks; 15 SWAP_ARMY: bulkMoveArmy/swapCreatures
- 16-18 RECRUIT×3: recruitCreatures 目标最近己方城镇（town->getUpperArmy() 作 dst）
- 19-21 BUILD×3: buildBuilding（buildMask 位 → BuildingID，仅己方城镇）
- 22 GARRISON: swapGarrisonHero; 23 RECRUIT_HERO: getAvailableHeroes+recruitHero
- 24 MOVE_TO: 高层移动（逐格逼近）
- strategic_env.py N_ACTIONS 11→25
- reasonix CLI 用法: reasonix-cli.exe run --permission-mode bypassPermissions --preset delivery --max-steps 150 --events-jsonl --dir <项目> "任务"（MCP 版只调研不写码已弃用; 详见 docs/H6_reasonix_task.md）

**H.7 冒烟测试（16/16 全过, smoke_h7.py）**
- 必须 MMAI 模式测动作: red_adventure_ai=Nullkiller2 时 yourTurn 不执行（NK2 自己决策，Python 动作全被忽略，PASS 是假象）；collect_bc.py 用 NK2 是采集行为，测试动作执行必须 red_adventure_ai=MMAI
- 冒烟 4 bug 修复: INTERACT(8) 从未实现（设计文档标✅但代码无分支）; GARRISON 未进城 swapGarrisonHero 挂起 120s; MOVE_TO 直接 moveHero 远处被 BLOCK; smoke 配置错 Nullkiller2
- 单英雄图上 SPLIT/MERGE/SWAP 目标缺失 = 静默跳过 = 合法无崩溃（v1 引擎侧最近目标解析固有行为）

**动作执行关键 API 知识**
- CCallback::moveHero 单格版只允许相邻格（CGameHandler STANDARD 检查 "Tiles are not neighboring"）→ 高层移动必须逐格逼近或传 vector<int3> 路径
- moveHero 目标是 hero->convertFromVisitablePos(obj->visitablePos())（可站格），直接传对象 visitablePos 会被 BLOCK（城镇格 terrain 不可站）
- 英雄 visiting 判断: cur->getVisitedTown()（visitedTown 是 ObjectInstanceID 成员）; is_garrisoned 仅表示驻守（swapGarrisonHero 后），visiting 不等于 is_garrisoned
- INTERACT 目标选择: interactTarget 优先最近己方城镇（3 格内），其次最近可交互对象; standPos==heroPos 时 moveHero 到对象格触发交互（进城），相邻走 standPos，远则逐格逼近

**H.7 #15 24 局稳定性 ✅ (2026-08-15, bc_collect_v3464.log)**
- 4 图轮换 (Dungeon Keeper/Good Witch Bad Witch/Fort Noxis/Key to Victory) × 6 = 24 局, NK2 对手
- TOTAL 463 pairs, 无崩溃无死锁; ep16 最多 57 pairs, Good Witch 图稳定 8-12 pairs
- ep23 尾部 NK2 卡死 (adventure_wait 90s 超时兜底, 只采 11 pairs 正常保存) — 长采集必须有 per-episode 超时+部分保存, 见踩坑点 #22
- H.8 重采集已开跑: 463/771 pairs (8月15 22:46)


## H.8 obs 归一化规范 (2026-08-16 数值爆炸根因修复)

**背景**: 2689 时代 obs max=6410 可训 (C8.5 vloss=1349 正常); OBS v3 新增未归一化大字段 (build_mask 2.1e9 / gold 74万 / total_power 7.8万 / enemy_threat 11万) 直接喂 Linear → logits 爆炸 → 训练失效。

**归一化规则 (strategic_env._build_obs 与 bc_train.load_data 必须双端一致)**:
- build_mask_lo/hi (towns 段 f16/f17, 8×2=16 列): ÷2^31 → [-1,1), 保留 bit 语义
- players.gold/total_power/weekly_income + heroes.movement/max_movement/exp/total_power + enemy_threat + battle_pred (67 列): log1p 压缩
- heroes/towns 的 id 标识符 (≤2831) 不处理 (与 C8.5 的 6410 同量级)
- 新采集数据走 _build_obs 自动归一化; 旧 npz 在 bc_train.load_data 里做同变换

**安全参考线**: 新增 obs 字段前先跑 obs max 统计, 超过 ~1e4 必须设计变换 (bitmask→÷2^31, 资源/战力→log1p, 计数→原样)。

## NK2 AI 结构与内存分析 (2026-08-16)

**NK2 (Nullkiller2) 架构**: Goals 24 + Behaviors 11 + AIPathfinder/ObjectGraph (Pathfinding) + Analyzers。决策循环 = 目标估值 → 选最高价值目标 → Behavior 执行。源码: vcmi/AI/Nullkiller2/ (Windows 版 Nullkiller2.dll / Linux libNullkiller2.so)。

**移动**: AIPathfinder (A* 8 方向, 代价=移动力+地形+危险度) → ObjectGraph (全图对象可达性) → 多格路径一次 moveHero。不走逐格。

**内存结构 (泄漏嫌疑点)**: PathfinderCache (lib/pathfinder/, key=英雄指针缓存全图 CPathsInfo, invalidatePaths 才清); ObjectGraph (unique_ptr 只建一次, removeObject 增量维护, 遗漏则累积); memory 对象记忆 (removeInvisibleOrDeletedObjects 依赖可见性)。

**NK2 卡死根因 (2026-08-16 全面分析, 见踩坑 #29)**: 6 环链 — Router battleStart 战斗模型名 (3 处修复) → battleEnded 服务器补调 → dialog 自动应答 → 守卫战斗收尾卡 (第 6 环定位未闭环)。**NK2 卡死 = 战斗集成 bug, 非 NK2 本身**。战斗全链 (startBattle→battleStart→battleEnd) 已通; 剩守卫战斗 battle query 移除后 onExposure 未触发 (objectVisitEnded 不发 → obj/mov 卡)。

**内存爆炸 (C8.5 记录 3.7-7.5GB/局) — 2026-08-18 定性修正**: 长时验证 (nk2_mem_long_watch.sh, 5 局采样) 结论: (1) 无跨局泄漏 — 每局独立进程基线稳定回归 200-300MB; (2) 局内爆发仅发生在 ML hook 采集环境的卡死前刻 (pairs_lines 停滞、查询栈残留、popIfTop FAIL 循环时, 实测 4.2/6.5GB), 正常局仅几百 MB (214→318MB); (3) **Windows 原生 GUI 对战 NK2 无此问题** (用户实测 2v1 对局回合正常) — NK2 纯净运行时无 ML hook 干扰查询栈, 不触发。定性: 是 ML hook 采集环境的异常态, 非 NK2 本身缺陷。处置: 采集侧独立进程 wrapper + watchdog 已规避; **内存问题不再阻塞任何路线** (Track 2 部署无影响, Phase I 移植精简版即可); 1v7 真正阻塞是 0x618 (≥3 AI 玩家, 官方 bug, 需 Windows 构建 fork)。

**战斗处理链路 (Phase D 领域)**: 服务器 BattleFlowProcessor 驱动 → CBattleGameInterface::activeStack (无 yourTurn, AI 决策入口是 activeStack) → MMAI Router 转发 bai。Router 是 battle interface (installNewBattleInterface 安装)。**BattleAI 在 headless 无头模式等待回调卡死, 自动裁决统一用 StupidAI**。MMAI 的 Scripted 模型 (ML::ModelWrappers::Scripted) 是 dummy (getVersion=-666, CreateBAI 不支持), 名字只用于 Router SCRIPTED 分支分派。

**MMAI 配置**: mmai-settings.json (MMAI/CONFIG/) 缺失 → "Could not load MMAI config" → fallback=BattleAI (ScriptedModel)。config 是模型注册表 (models.attacker/defender 路径)。

**训练环境部署模式 (embedded, 2026-08-16 实测确认)**: python 进程直接加载 libmlclient.so (链接 vcmiclientcommon → vcmiservercommon 静态库, 含 server 代码) — **不是独立 vcmiserver 进程**。改 server 代码 (CGameHandler/BattleProcessor 等) 必须重编 libmlclient.so (vcmiservercommon 是中间静态库, 自动重编), 只重编 vcmiserver 二进制无效。全量对齐用 `cmake --build rel -j4`。target 名大小写敏感 (Nullkiller2)。**这是"正常游戏 (AI 在客户端进程) vs 训练环境 (AI 在服务器进程内)"架构差异的直接后果**: battleEnded 回调 (NetPacksClient) 缺失、dialog answerQuery 锁竞争死锁 — 修复策略 = 服务器侧补齐 AI 自动处理 (条件化, 部署客户端模式需关闭, 见踩坑 #29)。
## 死锁链知识: CGameState::mutex + waitTillRealize (2026-08-16 晚, 踩坑 #30 配套)

**CGameState::mutex 是 shared_mutex, 四类持有者**:
- runNetwork 线程 (处理包): handlePack 里 unique_lock (写锁, 短暂)
- NK2 决策线程: makeTurn 的 shared_lock (读锁, 整个决策期)
- MMAI fill: 局部 shared_lock (读锁, 段内)
- sendRequest 的 makeUnlockSharedGuard: 调用者持读锁时 解锁→等待→重锁 (官方契约)

**官方契约**: 调 CCallback::sendRequest (waitTillRealize=true) 必须**持读锁** (makeUnlockSharedGuard 配对解锁/重锁)。破坏契约 = shared_mutex 计数损坏 → 后续 lock 永久阻塞 (无持有者但拿不到锁)。修复必须保持官方锁结构, 不能手动解锁/移出作用域。

**waitTillRealize 是共享 cb 的易变状态**: BattleAI/StupidAI initBattleInterface 设 false, 析构才恢复 — embedded 模式战斗界面对象长期存活 → 残留 false → NK2 endTurn 不等确认 → livelock。防御: AIGateway::endTurn 显式设 true。

**embedded 模式 AI 线程模型**: runNetwork (asio, 收包+handlePack) / runServer (asio, 处理请求) / NK2 makingTurn (TBB worker, 决策) / MMAI yourTurn (在 runNetwork 线程!) — MMAI 的 endTurn 在 runNetwork 线程执行, 不能 wtr=true (自锁)。NK2 的 endTurn 在 TBB 线程, 可以 wtr=true (等待时解锁)。

**gdb 抓死锁**: runNetwork 卡 handlePack 等锁 + NK2 在 sendRequest/waitWhileContains/序列化 + runServer epoll 空闲 (不持锁) = 锁状态坏或互等。抓完立即 detach (batch), 多次 attach 后 WSL 服务易崩 (0x8007274c), wsl --shutdown 恢复。


## 有头验证结论 (2026-08-18)
- **部署形态 = Windows 原生 VCMI + 玩家视角**: WSLg 无 GPU 合成显示无解 (虚拟显卡); 官方 Windows 显示正常但 NK2 0x618 崩 (fork 已修) → 最终: **Windows 构建 fork** (显示+稳定+ML 一步到位)
- **spectate 观战模式不可用** (官方也崩, 渲染链脆弱) — 用玩家视角 (VCMI_TESTMAP_ONLYAI=0, red 人类位 = 模型 AI 落点)
- 官方 1.7.5 Linux AppImage: squashfs-root/usr/bin/vcmiclient, 用户数据 ~/.local/share/vcmi (与 fork 共享)
- 1.7.5 下载: ghproxy.net 镜像 (github 间歇不通); Windows 安装 D:\GAMES\VCMI
- vcmi_source (C:\Users\Administrator\vcmi_source): ML Windows 移植树雏形 (Linux preset, 无 fork NK2 修复, 未构建) — Windows 构建起点

## 模型 AI DLL 封装 (2026-08-18 里程碑)
- **目标**: 模型 AI 进真实 Windows VCMI 对局 (AI DLL 方案 — 部署形态)
- **接口** (1.7.5 AI DLL): extern "C" 3 导出 — GetGlobalAiVersion()→AI_INTERFACE_VER(1), GetAiName(char*), GetNewAI(shared_ptr<CGlobalAI>&); AI 继承 CGlobalAI (CGameInterface + IGameEventsReceiver); 纯虚: showBlockingDialog/showGarrisonDialog/showTeleportDialog/showMapObjectSelectDialog/makeSurrenderRetreatDecision/heroGotLevel/commanderGotLevel/activeStack/yourTacticPhase
- **编译** (免完整构建): VCMI_lib.def 从安装 DLL 导出表自动生成 (pefile, 8192 符号) + lib.exe 生成导入库; boost 头 (1.83) + boost.filesystem 手编静态库 (vc143 名匹配, /DBOOST_FILESYSTEM_NO_CXX20_ATOMIC_REF 修 MSVC atomic_ref 误报); cl /LD 编 DLL; vcvars64.bat 环境
- **AI 名选择**: --ai 参数 1.7.5 未实现 (定义了没用); 由 PlayerSettings.name 决定 → 改 settings.json ai.adventureEnemyAI/AlliedAI + 安装目录 schema enum 加名
- **回合卡死时序坑**: yourTurn 应答(selectionMade 0) 后立即 endTurn → 服务器未就绪卡死; 加 300ms sleep 后 endTurn → 正常 (NK2 对照: 有行动+状态跟踪所以无此问题)
- **对话框死锁**: 所有带 QueryID 的 dialog 回调必须应答 (selectionMade(0, qid)) 否则 "Cannot wait for dialogs in gui thread" 卡死
- **0x618**: 仅 --onlyAI 全 AI 模式 (第 3+ 玩家界面初始化) 崩; 人类模式 (1 人类 + AI 对手) 无; 官方 bug (我们 fork 修过同类 PlayerState 判空)
- 工程: D:\vcmi_model_ai\ (model_ai.cpp, build_model_ai.bat, gen_implib.py 等); 部署: AI\ModelAI.dll
- **v1 行动 (08-18)**: simpleAct — 英雄 4 方向轮换移动 3 格 (路径自动采集); yourTurn: 应答 query → simpleAct → 300ms → endTurn; 编译链: CGHeroInstance.h 需 TBB 头 (oneTBB-2021.13.0) + tbb12.lib (dll 生成导入库); movementPointsRemaining 未导出 (去掉检查)
- **2v2 阻塞**: 0x618 = 官方 1.7.5 第 3+ AI 玩家界面初始化崩 (PlayerState 类, fork 修过同类); 人类模式最多 2 AI; 目标 2v2 (人+ModelAI vs 2 电脑) 需 Windows 源码构建 fork (vcpkg 或手工, ~半天)

■ fork 1.8.0 Windows 构建(08-18 完成, commit 873dbe78a)
- 环境: MSYS2 MinGW64(C:\msys64), CMake 4.4.2, Ninja; 构建目录 D:\vcmi-fork-build; 部署 bin/ 即完整环境
- 选项: -DENABLE_ML=OFF(ML 模块 Linux-only #error) -DENABLE_MMAI=OFF -DENABLE_DISCORD=OFF -DENABLE_LAUNCHER=OFF -DENABLE_PCH=OFF -DENABLE_EDITOR=OFF
- 每次 cmake configure 后必须 sed 修 build.ninja: $<LINK_ONLY:ws2_32/mswsock/dbghelp> → -l; libVCMI_lib.dll.a 移到 vcmiservercommon.a 之后(MinGW ld 从左到右)
- 半重构残留修复集: CDynLibHandler.h 恢复(9b9a77032^)/CreatureCostBox.h 恢复(b5b599fee^)/VCMIDirs fullLibraryPath 恢复/QueriesProcessor 对齐 AllQueriesView/lobby visitor 补实现(visitLobbyQueryState x3 + visitLobbyClientConnected + visitLobbyModsCheck)/hasRemoteClientInLobby 恢复/孤儿 logger/eventBus/reinitScripting 删除/headless ENGINE 判空 9 处/mapInstance 无条件创建/g_adventure_allied_ai 非ML本地定义
- BattleAI: fork 删 main.cpp(GetNewBattleAI 导出)但运行时仍 LoadLibrary → 恢复 main.cpp + 手动链接(OBJECT obj + libVCMI_lib.dll.a + -ltbb12), 不碰 CMake(OBJECT 传播会带 vcmiMain obj 循环)
- ModelAI 重编: g++ -shared model_ai.cpp + libVCMI_lib.dll.a(fork ABI, AICombatOptions 签名)
- 0x618 验证: A Viking We Shall Go 6 AI 全 ModelAI 稳定 0 崩(EndTurn 数百次)
- AI 全知: CGameState::isVisibleFor(int3/obj 版)对 !isHuman 玩家返回 true(寻路+obs 需要); NK2 AIGateway getPlayerID 加 value_or
- 移动链: 寻路 SingleHeroPathfinderConfig(out, cc, hero) + options.turnLimit=1 + CPathfinder.calculatePaths + CPathsInfo::getPath(倒序!)


## 十六、Windows ModelAI 战斗链 (2026-08-18 晚打通)

### 战斗链路 (fork headless 首次可用)
- 触发: 模型英雄走进守卫/敌人 → server 发 BattleStart → BattleSetActiveStack → client 分发 activeStack 给 BattleAI.dll
- 参与者: 冒险 AI (ModelAI.dll) + 战斗 AI (BattleAI.dll) 独立加载; 战斗决策在 BattleAI
- 历史: 6 AI 测试 580+ 回合 0 崩是假象 (NK2 没相遇), 战斗链从未验证 — ModelAI 主动探索才暴露
- 双根因 (踩坑 #67): ① Client.cpp startPlayerBattleAction getBattle() 双调用竞态 → 单次取指针 ② ENGINE null
  (headless) 的 unlock guard 解引用 → if(ENGINE)
- BattleAI.dll 手动链接 (踩坑 #68): CMake OBJECT 库 9 源 + 恢复的 main.cpp = 10 obj 全链;
  StackWithBonuses/ThreatMap 漏链 → HypotheticBattle::makeWait 未定义; lib 头改动后 obj 必须全量重编

### 动作执行层 (模型 → 游戏)
- 0-7 移动: dx/dy 表 (N-start CW) + passable[8] masking (不可走 → 环形最近可走方向), fishy 460→0
- 8 INTERACT: 移植训练端 interactTarget (最近己方城镇 3 格内优先, 否则最近友好/中立对象; 相邻一步到位,
  远则点积选向单步逼近) — 实测 147 次城镇访问 + 146 宝箱拾取
- 10 END_TURN; 其余码 fallback simpleAct 探索
- 每实例状态: StrategicState 是类成员 (static 跨 red/green 实例共享 → 285 fishy, 踩坑 #69),
  fill 按 my_color 视角 (active_hero/team/relations/build-mask/enemy_threat 全参数化)

## 十七、奖励塑形与训练配置 (2026-08-19 记忆迁移)
### 奖励设计
- 被动 gold/town 收入不能 per-step 给 (模型会坚守 END_TURN 刷奖励) — 只能终局结算
- 探索 +1 / 占矿 +10 / 杀敌 +100 / 占城 +50
- step_fixed = -1 ~ -2 (每步小惩罚)
### 训练 MAPS (6 张 2 人图, 出生点近/训练验证过)
- Twins / A Warm and Familiar Place / Unholy Quest / When Dragons Clash / Gorlam's Tentacle Swampland / Unexpected Inheritance
- passable 段在 obs[3211:3219] (非末尾段)
- 训练 1000ep ≈ 5 天/轮
### 训练监控 (首信号)
- 英雄位置变化: traj_ep.json 里 ah=obs[3203], base=128+ah*26, pos=2,3,4
- 单动作连发 + 全负奖励 ≠ 正常训练; 两格横跳 = 出生点被围 (查 MAPS)

## 十八、训练塌缩诊断与防坍缩机制 (2026-08-19)
### 诊断方法 (可复用)
1. 训练日志动作序列: 纯交替对 (3/7, 0/4) = 横跳; 80%+ END_TURN = 刷步
2. bc_model vs 训练模型同图对比诊断局 (ep_runner --model): bc 能探索 = PPO 训练伤害 (policy collapse); 都困 = 地图/环境问题
3. passable 段 obs[3211:3219] 每步检查: 可走方向充足却打转 = 策略问题非 mask 强制
### 防坍缩机制清单 (ep_runner_one.py + train_wsl2_ppo_v2.py)
- 横跳惩罚: 回两格前位置 r-=2.0 (比较 nobs 与两格前 obs 同英雄位置)
- 探索奖励: 新格子 +2.5 (net +1 vs step_fixed -1.5, 走出去净赚)
- END_TURN 冷却: 连续 3 次屏蔽 logits[10] (防跳过游戏刷步, C8.5 老问题复发)
- 熵奖励 0.05 (0.01 拉不住确定性坍缩)
- 11-24 mask: logits[11:25]=-inf (训练端未实现码)
- KL 0.05 拉向 BC (注意: BC 本身有横跳倾向 P45, 弱约束对抗)
### 教训
- 惩罚必须配逃生通道: 横跳罚 → 模型躲 END_TURN → 需冷却; 否则只是换一个局部最优
- 奖励结构环环相扣: 探索弱 → 横跳; 横跳罚 → END_TURN; 调整需一次到位 + 从干净权重重启 (resume 塌缩态会被旧策略污染)
- **第 5 轮判死 → 行为级修补有边界, 见二十**
## 十九、MOVE_TO 动作 24 落地 (2026-08-19)
### C++ 侧 (vcmi-native/ML/strategic_state.cpp)
- fill_target_list 填充 obs[3251:3315]: 最近 8 个可采集目标, 每目标 8 字段 (type,idx,x,y,z,dist,power,flags)
- 候选: 未占矿 / 资源堆 / 篝火 / 宝箱 / 宝物; 同层曼哈顿距离; 守卫战力 log2 (power)
- libmlclient.so 重编部署 (旧 .so 先备份)
### Python 侧 (ep_runner_one.py)
- 24 开放 (11-23 屏蔽: logits=-inf); --move_to_test 强制全 24 (验证用); --move_to_bias 训练引导
- 展开逻辑: target_list 取最近目标 → 8 方向候选 (passable obs[3211:3219]) 朝目标贪心走一格
- 粘滞 (move_target): 上次目标未到达继续用, 到达才重新选 — 防目标漂移来回走
- stall 检测: 连续 6 步距离不减小 → 放弃换目标 (被堵/绕路兜底); 无目标 → END_TURN (动作 10)
### 训练引导
- logits[24] 偏置 = 2.0 × (1 - ep/200) 线性衰减 (train_wsl2_ppo_v2.py:68), 帮模型发现 24
- 第 4 轮训练: BC 干净重启 (fc+actor 载 BC 权重, critic 随机), KL_COEF=0.05
### 验证与局限
- Twins --move_to_test 60 步: target_list 填充正确 (type/坐标/距离), 英雄目标导向移动, 粘滞生效
- 局限: 贪心不绕路 (地形挡会卡住, stall 兜底换目标) — 完整寻路 = Phase I.2 (NK2 AIPathfinder 移植)


## 二十、第 5 轮判死: 行为级修补的边界 (2026-08-19)
### 结论
- 第 5 轮 (三件套: 采样强制 24 + 状态级循环检测 + KL 0.3) 25 ep 判死 — 与第 4 轮同构: avg_r 无转正 (-0.7~-3.2), 9/25 ep 动作循环复发 (3/7, 2/6, 6/2), vloss 4~142 震荡, kl 0.1~1.79
- 判死四项标准 (可复用): ① avg_r 无转正斜率 ② 循环复发 ③ 引导动作自发率≈0 ④ vloss/kl 不收敛
### 新实锤: 强制引导 = 空转假动作
- 强制 MOVE_TO (24) 期间英雄原地 27 步不动 (traj pos 连续重复) — 出生点 target_list 空/无可走目标, 24 展开无效果仍消耗 step_fixed
- 模型学到 "24=无奖励" 关联 → 自发率 0 的真正原因 (比 #77 偏置无效更深一层: 采样强制也无效, 因为动作本身不产生状态变化)
- 教训: 引导动作必须保证执行效果; 无目标时应直接映射 END_TURN 或回退最近可达点, 否则引导成为纯噪声
### 循环检测的边界 (打地鼠失效)
- 8 步窗口同 (hero,pos) >=5 次 → -3 + 强制随机方向: 134 窗口触发 23 次, 仍挡不住 3/7 横跳
- 原因: 4/8 图出生点区域状态空间太小, 随机方向被模型拉回横跳; 行为级惩罚追不上策略演化
- 教训: 行为级修补 (惩罚/强制/冷却) 只能拖延, 不能根除 — 无正奖励信号时模型必然收敛到局部最优循环; 正道 = 结构级 (NK2 骨架/势函数奖励, Phase I)
### 下一步 (见任务清单第 6 步)
- A: MOVE_TO 空转修复 (target_list 空 → END_TURN/最近可达点)
- B: 奖励结构重构 (探索 2.5 太弱, NK2 估值势函数 Phase I.1)
- C: 直接上 Phase I NK2 骨架 (1v7 正道)

## 二十一、动作级循环惩罚与逃生码投机 (2026-08-19 第7轮)

### 起因: 第 6 轮 klc 触顶仍压不住 kl
- 第 6 轮 v2 (KL_TARGET 0.3, KL_COEF_MAX 10): 实际 kl 0.6~1.2, klc 升至 8.477 接近上限仍压不住 — 目标定太低, 系数追着打
- 第 7 轮调参: KL_TARGET 0.3→0.4 (放宽约束) + CLIP 0.1→0.08 (收紧 policy 更新步幅); 其余不变 (EPOCHS 2 / KL_COEF_INIT 0.3 / ADAPT 1.5/0.7 / MIN 0.01 / MAX 10 / LR 5e-5 / GAE 0.9 / grad_clip 1.0 / gamma 0.99 / batch 128)

### 动作级循环惩罚 (--act_loop_penalty)
- 动机: 日志 [3,7,3,7] 交替死循环单局上百步, [2,6,2,6]/[4,0,4,0]/[24,5,24,5] 变体, [2,2,2,2]/[10,10,10] 连发 — 状态级检测 (8 步窗口同 (hero,pos)≥5) 与横跳惩罚 (prev2) 只抓位置往返, 抓不住推进型动作循环 (位置持续变化但动作模式固定)
- 规则: 连续 4 步同动作 → -N; 8 步两两交替 (a,b×4) → -N; 强制阶段 (move_to_force 内) 不检测
- 参数: --act_loop_penalty (0=关) / --act_loop_repeat (默认 4) / --act_loop_alt (默认 8); 训练端传 1.8

### 3.0 → END_TURN 投机 (数据)
- ROUND1 (改前) 10 占 6.2% avg 9.1/ep; ROUND2 3.8% avg 6.8/ep; ROUND3 (penalty=3.0) 17.8% avg 27.8/ep 全场第一 (362 次), 10-run≥3 从 11-18 → 77 次
- 根因: ① 10 前 2 次免费 (strategic_env 连续 END_TURN ≥3 才 -5), "走2步→10" 节奏永不触发 ② 10 插入检测窗口打断交替/重复模式 → 循环惩罚永不触发 ③ 纯循环 -3/步 vs 穿插 10 = 0, 投机必赢
- 修复 (v2): 降 1.8 + 检测窗口剔除 10 (if a != 10: act_hist.append(a)) — 10 无法再打断检测, [3,10,7,3,10,7...] 剔除后原形毕露照样触发, 投机失去收益

### 验证
- 单测: 长穿插 [3,10,7]x6 第 11 步起持续 alternate 触发; [2,10]x4 触发 repeat; 纯 10 不触发 (交给冷却+-5); 正常序列不误判
- ROUND4 (1.8+剔除): ep5 kl 0.324 klc 1.012 (从 8.477 触顶回落), avg_r -0.8

### 教训
- 任何 >0 的惩罚都会诱发穿插逃生码; 降强度只是缩小激励差 (10 免费 → 依然最优), 根治 = 检测窗口对逃生码免疫
- 新增惩罚前先检查动作空间里有没有"免费打断检测"的码 (END_TURN/无操作类), 有就剔除

## Phase I.2 C++ BFS 全图寻路 (2026-08-23)

### 实现
- fill_next_dir() 在 fill_strategic_state 后调用, 全图 BFS 从 hero visitablePos 出发搜索8个 target_list 目标
- 结果写 reserved[0..7] (next_dir[8], 方向 0-7 或 -1=不可达)
- reserved[8..15] 诊断: hx,hy,hz,W,H,next_dir[0],explored_count,-1

### BFS passability (对齐引擎 canMoveFrom)
- isLand() + isPassable() + !blocked() -- 三条件缺一不可
- 目标格豁免 blocked 检查 (矿/资源物体让 blocked=true 但英雄可走上去)
- z-level 过滤: 跳过不同层的 target

### Python 侧
- strategic_env.py: obs[3330:3338] = next_dir[8], obs[3338:3346] = diagnostics
- ep_runner_one.py: MOVE_TO 三层回退: C++ BFS -> Python 15x15 BFS -> 贪心方向

### .so 部署
- 编译: cd /home/administrator/vcmi-native/rel && make mlclient -j4
- 同步 4 处: rel/bin, build/bin, workspace/vcmi/rel/bin, vcmi-native-build/rel/bin
- build/bin 是软链接不可信, 必须物理复制

### 性能
- BFS 开销 ~0.36s/step (72x72 地图, 8 目标)
- 冒烟: 18/18 = 100% 命中率
- 训练: avg_r 从 -1.0~-1.6 改善到 -0.0~-0.7

## Phase I.2 训练验证 — KL 调参 (2026-08-23)

### BFS 训练效果
- 冒烟: 18/18 = 100% 命中率
- 训练 71 ep (KL=0.15): 正奖励率 27% (19/71), 最高 r=+74, 最高 avg_r=+1.2
- 好 ep 特征: 纯方向探索 (无 24 强制), 动作多样 (1,3,4,5,7 混用)
- 差 ep 特征: 6,2 循环 或 END_TURN 投机

### KL 调参链
- KL=0.08: klc 触顶 10, avg_r -1.0~-1.6
- KL=0.15: klc 仍触顶 10 占 80%+, 正奖励率 27%
- KL=0.30: 全新启动 (从 BC 模型), 待观察

### 关键指标
- klc 触顶 10.0 占比: 80%+ (KL=0.15 时)
- 正奖励 ep 集中在 ep50+: 最近 20 ep 正奖励率 40%
- 好 ep 的 KL 范围: 0.07~0.30
- 差 ep 的 KL 范围: 0.30~2.77

### 决策
- 全新启动优于续训: checkpoint 被 KL=0.08→0.15 锚定, 续训需挣脱旧约束
- KL=0.30 从 BC 模型出发: 策略自由度从第一步释放


## Phase I.4 地形栅格实现 (2026-08-23)

### 数据格式
- 21x21x4 = 1764 uint8, HWC 行优先
- C0: terrain_type (0-13)
- C1: blocked (0/1)
- C2: object_type (0-10, 优先级: hero>town>monster>artifact>chest>resource>mine>dwelling>teleport>other)
- C3: visibility (训练期全 1)

### 实现架构
- C++: fill_terrain_grid() 在 fill_strategic_state() 末尾调用
- 数据通道: C++ fwrite -> /home/administrator/vcmi-workspace/terrain_grid.bin -> Python np.fromfile
- Python: _build_terrain_grid() 读文件, 返回 (4,21,21) float32 CHW
- info["terrain_grid"] 随 obs 一起返回
- ENABLE_TERRAIN_GRID 开关在 strategic_state.cpp 第 333 行

### 关键坑
- .so 双实例: ctypes 和 connector 各加载一份 libmlclient.so, 全局变量不共享
- _init_baselines 覆盖: 在 _build_terrain_grid 之后调用, 把 terrain_grid 重置为 0
- 越界处理: 超出地图范围的格子 C1=1 (不可通行)

### 文件传递是 .so 隔离的可靠绕过
- 后续如需从 struct 直接读, 需要统一 .so 加载源 (让 connector 导出指针)

### 设计文档
- docs/地形栅格数据格式设计.md v1.1

## Phase I.4 C: CNN 地形编码器实现 (2026-08-23)

### 架构
- Net() 双输入: obs(3464) + terrain(4,21,21)
- CNN: Conv2d(4→16→32→64) + MaxPool2d(2) + Linear(1600→128)
- Merge: concat(obs_128, cnn_128) → Linear(256→128) → actor/critic
- CNN params: 228k, total: 724k
- terrain=None 时兼容 (零填充, 不改旧网络行为)

### 数据链路
- C++ fill_terrain_grid() → fwrite terrain_grid.bin
- strategic_env: _build_terrain_grid() → info["terrain_grid"]
- ep_runner: terrain_grid 保存到 trajectory JSON
- 训练循环: buffer["terrain_grid"] → terrain_t → model(obs, terrain)

### 关键修复
- step() info 缺 terrain_grid: 加 info["terrain_grid"] = self._terrain_grid
- ep_runner strict=False: 3处 load_state_dict
- 训练循环 strict=False: 6处 load_state_dict

## H3M 对象表逆向 (2026-08-23) — h3m_tool.py parse_objects

**工具**: scripts/h3m_tool.py — H3M 解析 (header/terrain/对象表) + terrain 修改 (加水/岩/草)
**验证**: gdb 断 readObject 从 VCMI 引擎拿真值 — A Warm 730/730, For Sale 514/514, Twins 803/803 全量匹配

### H3M 文件结构 (gzip 压缩)
header (玩家/victory/loss/teams/heroes/artifacts/rumors/自定义英雄) → terrain (w×w×7B×levels) → objectTemplates → objects → events

### 对象段格式
- readObjectTemplates: u32 count; 每个 = lstr anim + 6B blockMask + 6B visitMask + u16 + u16 terrMask + u32 id + u32 subid + u8 type + u8 printPriority + skip16
- readObjects: u32 count; 每个 = int3 pos (u8×3, 允许 ±8 越界) + u32 defIndex + skip5 + payload (按模板 id 分派)

### 对象类型 id = VCMI Obj 枚举 (H3M 原始 id == remapped id, gdb 实测)
**≠ MapObjectBaseID 枚举** (ptype libvcmi.so 拿到的是另一套)! 实测值:
- HERO=62, RANDOM_HERO=70; TOWN=98, RANDOM_TOWN=77; MINE=53 (subid<7 矿, ≥7 abandoned)
- RANDOM_MONSTER=54, L1=72, L2=73, L3=74, L4=75, L6=162, L7=163 (L5 未实测, 161 实测 generic)
- RANDOM_RESOURCE=76, RESOURCE=79; TREASURE_CHEST=101; ARTIFACT=5, RANDOM_ART=65-69
- EVENT=26, CAMPFIRE=12, SIGN=91, SEER_HUT=83, SCHOLAR=81, WITCH_HUT=113, SHRINE=88/89/90
- CREATURE_BANK=16, DERELICT_SHIP=24, SHIPWRECK=85; GARRISON=33; QUEST_GUARD=215
- CREATURE_GENERATOR1-4=17-20; RANDOM_DWELLING=216/217/218; SHIPYARD=87
- 实测 generic (勿设分派): 9 BORDERGUARD, 14, 37, 41, 57, 58, 61, 161, 199, 207-211

### payload 要点
- readBoxContent 开头 = readMessageAndGuards (bool msg + [lstr + bool guards + creatureSet + skip4]), 不是直接 lstr
- readEvent 对象: readBoxContent + bitmaskPlayers(1) + computerActivate + removeAfterVisit + skip4
- readHero (AB): identifier u32 + owner u8 + heroType u8 + hasName + exp u32(无条件) + portrait + secSkills + garrison + formation + loadArtifactsOfHero + patrol + bio + gender + spell + skip16
- readCreatureSet: 7 × (creature u8/u16 + count u16); readCreature/readArtifact: ROE=u8, AB+=u16
- Twin 脏数据 hero: bag 巨大 → 容错搜索恢复 (双头校验 + 回溯 before+20~300)

### 工具命令
python scripts/h3m_tool.py scan <h3m> / terrain <in> <out> <edits.json> / objects <h3m>
## vmap 水/岩障碍启用 + 非草地 segfault 误判纠正 (2026-08-23 晚)

### 背景
课程地图曾因 "vmap 非草地 (wt00_/rc00_) 加载 segfault" 转 H3M 路线 (对象表解析已完成)。
本晚实证推翻该结论, vmap 水/岩直接可用, H3M 路线停用 (工具 h3m_tool.py 保留作逆向参考)。

### 真根因: NK2 守卫战斗断言 (与 terrain 无关)
- 断言: `vcmi/AI/MMAI/AAI/AAI.cpp:435` `ASSERT(queryID != -1, "QueryID is -1, but we are ATTACKER")`
- 触发链: 守卫战斗 (打野怪) → 无 CBattleDialogQuery (onlyOnePlayerHuman=false) → queryID=-1
  → MMAI battleEnd 断言崩。ep_runner 默认 blue_adventure_ai=Nullkiller2 必触发。
- 证据: T01 全草地 + NK2 配置 3/3 崩同一断言; T01 + MMAI 配置 3/3 不崩;
  1 格水/34 水+8 岩 + MMAI 3/3 不崩 → 与 terrain 完全无关。
- 训练配置 (blue=MMAI_RANDOM --blue_adventure_ai MMAI) 永不触发, 训练不受影响。
- 教训: **验证地图必须用训练同款配置** (--blue_ai MMAI_RANDOM --blue_adventure_ai MMAI);
  用 ep_runner 默认 NK2 会把守卫战斗断言误归因到地图格式。

### vmap 水/岩障碍生成 (已启用)
- `maps/training/gen_curriculum_all.py` make_obstacles(): 岩柱 rc00_ (单格) + 2x2 水湖 wt00_,
  避开对象±3 + hero 出生±4 + 边界 1 格, 4 邻检查防封路, 确定性 seed。
- Level 1 (T02): 岩5+水4-8; Level 2 (T03): 岩9+水12; Level 3 (T04): 岩13。
- 验证: T02/T03/T04 带障碍版 20 步全满无 error, hero 唯一位置 7-9 (绕障碍不卡死)。
- 31 张课程图部署: Windows vcmi/data/Maps/ + WSL rel/bin/data/Maps/。

### optimizer.load_state_dict(strict=False) TypeError — state 永远加载失败 (严重)
- `train_wsl2_ppo_v2.py` 曾 `opt.load_state_dict(sd["optimizer"], strict=False)` —
  PyTorch Optimizer.load_state_dict 无 strict 参数 → TypeError → except → fallback BC 权重。
  **每次重启都丢训练进度** (resume_step 恒 0), 日志 "Failed to load STATE_PATH" 静默降级。
- 修复: 去掉 strict=False。验证: 重启后 "Loaded train state (model+optimizer, step=3834)" 恢复续训。
- 教训: state 加载失败时先隔离测试 (单独 torch.load + load_state_dict), 不要直接 trust except 分支。

### 训练进程启动方式 (2026-08-23 变更)
- 原 train_loop.sh 守护 (tee train_loop.log) 已不用于当前训练; 现用 Hermes background 直接跑:
  `wsl bash -c 'cd /home/administrator/vcmi-workspace && export LD_LIBRARY_PATH=... && export STRATEGIC_STATE_LIB=... && export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh && python3 -u train_wsl2_ppo_v2.py 2>&1 | stdbuf -oL sed "s/\x1b\[[0-9;]*m//g" | tee train.log'`
- 杀 worker: 认准 `grep "[t]rain_wsl2_ppo_v2.py" | grep python3` 的 PID (bash 包装 3MB 不是 worker)。
- 日志: train.log (用户看, Get-Content -Wait); 重启前 cp train.log train.log_L0_<tag>.log 存档。

### Phase I.2 超参调优链 + Level 3 实验失败 (2026-08-24)

**PPO 大调参 (stuck → working)**:
- Before: BATCH=128, LR=5e-5, CLIP=0.08, EPOCHS=2, KL_TARGET=0.30, KL_COEF_MIN=0.15, entropy=-0.05, NK2 scale=1.0, explore=0.5, act_loop=1.8 — 33ep 无改进
- After (冻结): BATCH=1024, LR=3e-4, CLIP=0.2, EPOCHS=4, KL_TARGET=0.50, KL_COEF_MIN=0.05, entropy=-0.05, NK2 scale=0.3, explore=0.2, act_loop=1.0, move_to_force=15, random_armies=3000-5000, return normalization
- 关键链: KL_TARGET 放宽 (0.3→0.5) 让策略离开 BC 邻域; BATCH 128→1024 梯度 8x 稳定; entropy -0.05 正r率 27% (-0.01 只有 15%)

**NK2 移除实验失败 (critic 爆炸)**:
- 现象: 禁用 NK2 后 vloss 4-30→159-164, loss 2-15→80-82, 策略无法学习
- 根因: 原始 env reward 幅度 -100~-300/ep, BC 初始化的 critic 无法预测; NK2 势函数此前在掩盖幅度
- 修复 (必须同时): NK2 恢复 scale 1.0→0.3 + 训练循环加 return normalization (returns 标准化)
- 验证: vloss 159→1, kl 0.06→0.28 恢复学习

**Level 3 经济动作实验失败 (毒化)**:
- 动作: 16-21 (RECRUIT/BUILD) 采样强制引导 (train_wsl2_ppo_v2.py:97 注释)
- 失败链: noTarget 惩罚 → 模型学 END_TURN 刷步 → klc 触顶 10 → 策略锁死 → 模型毒化
- 处理: poisoned checkpoint 存档 (wsl2_model_L3_poisoned.pt), 回滚 Level 2, ep_runner_one.py logits[16:24]=-inf 屏蔽
- 教训: 经济动作必须等 reward 侧 noTarget 惩罚问题解决后再启用; 11-15 (SPLIT/MERGE/SWAP) 保留启用

**晋级规则 (2026-08-24 设计, 未集成)**:
- 80ep 检查点, ep_r (总奖励, 非 avg_r), 80% 达标率, ep_steps>10 过滤
- backup_on_promotion(): MAPS 变更自动备份模型 (L1/L2 checkpoint 丢失教训)

### 多 run 日志结构 + 训练意外停止恢复 (2026-08-25)

- train.log 由多次 `Loaded train state` 分段; 不同段可能是不同地图/超参, 统计必须按段
- 实例: Run1 正r率 64% → 切 L2 后 Run2 0% → Run5 26%; 混算 29% 会误判
- analyze_train.py 自动探测路径 + 分段统计 (见 refs/train-log-multirun-20260825.md)
- 09:51 训练意外停止: 无 Shutdown 日志 (正常停止有 "Shutdown signal received, saving") → 硬杀/WSL 终止; checkpoint 自动保存完好 (step=32083), 直接重启续训即可

### Hermes voice 自动启动排查 (2026-08-25)
- hermes 配置只在进程启动时读入内存; 修改 config.yaml 后不重启进程就不生效 (wake word/STT 监听按启动时内存态运行)
- 排查链: 配置里 stt.enabled=false + wake_word.enabled=false 却仍触发 "Wake word detected" → 对比 hermes 进程 CreationDate 与 config.yaml mtime, 进程早于配置修改 = 旧进程
- 排查命令: wmic process where "name like '%python%'" get ProcessId,CreationDate,CommandLine; stat config.yaml 看修改时间
- 永久禁用 voice 三件套 (15:03 会话执行, 15:23 写入): stt.enabled=false + wake_word.enabled=false + hermes tools disable tts
## 守卫战斗根因链 (2026-08-26 闭环)

**现象**: T03 训练 40+ 局守卫战斗永不触发, 正奖励率 11%, vloss 0.9 停滞。NK2 采集同图守卫战斗正常。

**根因链 (4 层, 逐层击破)**:
1. **守卫格 passable=0**: 守卫格 isClear=false (blocked) → strategic_state passable 通道标记不可通行 → 模型/MOVE_TO 按 passable 选方向永远绕开守卫 (NK2 不走 passable, 自有寻路直接走到守卫格 → 战斗)。**passability 通道对"可战斗格"是误导信号** — 守卫格可进入 (模板无 B 格) 但被标 blocked。
2. **先占矿守卫消失**: 守矿机制 — 矿被占后守卫清除。英雄绕开守卫先占矿 → 守卫消失 → 战斗永不触发。守卫目标必须优先于矿。
3. **守卫战力/行为评估 (takenAction)**: CGCreature::onHeroVisit → takenAction: relStrength = 英雄战力/守卫战力, powerFactor = relStrength>=1 ? 2×(relStrength-1) : -1; charisma = powerFactor + diplomacy + sympathy。**random_armies 3000-5000 (英雄) vs peasant 8+archer 6 (守卫) → relStrength ~4 → charisma >> agression → 守卫 JOIN/FLEE (消失无战斗)!** NK2 采集无 random_armies (swordsman 8) → relStrength ~2.3 → charisma 2.5 < agression 10 → FIGHT ✓。
4. **守卫"消失" ≠ 战斗**: MMAI 环境英雄进守卫格 → 守卫被清除 (JOIN/FLEE) → 无 battle_result 无战斗奖励。

**Python 侧等价修复 (零编译风险)**:
- 守卫目标: get_guards(mapname) 读 vmap objects.json 守卫坐标; 守卫恒优先于矿 (15 格内先打守卫); 守卫目标跳过 passable 检查 (守卫格 passable=0); 一步可达守卫优先 (避免途经矿/资源触发守矿机制)
- **守卫清除检测: 英雄进入守卫格 = 守卫被清除 → +100 首胜奖励** — 战斗机制的等价信号, 模型学"直奔守卫"
- random_armies 关闭 (恢复地图初始军队, NK2 同款, 守卫评估 FIGHT)

**验证**: 12 局正奖励率 83.3%, r mean 37.0 — 双超晋级判据。守卫清除奖励 (进格即得) 是确定性信号, 模型快速学会。

**遗留**: 真战斗 (battle_result) 仍未验证 — 守卫在 MMAI 环境评估 JOIN/FLEE 而非 FIGHT。若需真战斗: 提高守卫 agression (死守不逃) 或降低英雄军队 (但打不赢) — 课程设计取舍。

### 守卫真战斗 (2026-08-27, 从"守卫恒FLEE"到"autofight全链")
- vmap monster options 的字段名是 **character** (CGCreature.cpp serializeEnum), 不是 aggression — aggression:"guard" 无效被忽略 → 性格默认 → agression=0 → charisma>0 → takenAction 恒 FLEE (守卫逃跑=removeObject 无战斗)
- 08-26"守卫清除检测 +100"实为守卫逃跑误判 (假任务); 修复 = character:"savage" (agression=10 恒 FIGHT) + neverFlees:true
- 守卫战力: relStrength ∈ (1,1.5) 守卫才 FIGHT (charisma=powerFactor+diplomacy+sympathy < agression); 英雄 8 swordsman (1960, getValueForDiplomacy=sqrt((1+0.05A)(1+0.05D))×AI value) vs 守卫 swordsman×3/2堆 (1470) = 1.33; >1.5 守卫 JOIN/FLEE (强兵种双刃剑, random_armies 坑同机制)
- 运行时地图目录 = /home/administrator/vcmi-native/data/Maps (rel/bin/data → vcmi-native/data); patch 须同步 3 副本 (项目 Maps/training + vcmi-native/data/Maps + vcmi/data/Maps)
- 编译经验: 全量重编 mlclient 崩 (shutdown_vcmi GAME null, 未解); 但单个 .cpp 的 .o 重编+链接成功 (BattleResultProcessor/CGameHandler/AAI) — 不碰 strategic_state.h 就安全
- 战斗收尾: BattleResultProcessor.cpp.o 8-2 旧缓存 (IFML bug 从未重编进 .so) — 源码修了 .o 没重编 = 部署恒旧; 判定用行为 (CBattleQuery 卡顶)
- MMAI yourTurn 轮询阻塞 runNetwork 事件循环 (battleStart/battleEnd 回调同线程无法处理) → 轮询必须短 (0.3s); 战斗收尾用 async 任务 (battleEnd 回调 0.5s 延迟 + 兜底 CAS)
- garrison dialog: 战斗后守卫残余 (autofight 未全灭) → 英雄访问 → dialog → AI 应答后查询栈卡; 治本 = CGameHandler::showGarrisonDialog AI vs AI 自动合并残余 + 移除对象, 不建 dialog
- data 符号链接: make POST_BUILD 每次生成坏链接 (rel/bin/data → ../data 错误) → EEXIST; 每次 make 后 ln -s 绝对路径重修
- 详见 vcmi-gym refs/guard-battle-autofight-20260827.md

## v5 训练运维 + Phase II 经济前置准备 (2026-08-28/29)

### v5 复活 (WSL2 idle shutdown 根治, 2026-08-28)
- v4 死因: Windows 侧会话全关 → WSL2 VM auto-shutdown → SIGTERM 杀训练 (setsid/nohup 挡不住 VM 级死亡)
- v5 启动: `systemd-run --user --collect --unit=homm3-train-v5 --working-directory=/mnt/d/Bigdata/hero3_fresh /bin/bash -c 'exec venv/bin/python train_wsl2_ppo_v2.py >> train_loop.log 2>&1'` + Windows keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList 'sleep infinity'`
- 停止: `systemctl --user stop homm3-train-v5` (优雅保存); 续训验证: 日志 "Loaded train state (step=...)"
- zombie 修复 2a 生效后: ep1-71 首胜率 7.0% (v4 段 ~2%), 正 r 峰值 85-101

### 首胜-战死关联分析 (2026-08-29)
- 全部 7 场首胜 (v4×2, v5×5) 100% 以英雄战死收尾: 模型最后一击 → 守卫清除 (+100) + 英雄同战死 → 引擎封锁动作 → 强制 [10,10] ZOMBIE 2 步确认 → done
- 死亡不扣 +100 (无英雄存活项), 当前奖励结构下属理性行为; zombie 熔断把僵尸段从 121 步压到 ≤2 步, 无害化
- T04 阶段 (有城镇复活/征兵) 再评估是否加存活塑形

### Phase II 阶段② 经济前置准备落地 (2026-08-29, 零干扰设计)
- 原则: 条件开关 `mapname.startswith("T04")` + 注释块 — 当前 Level 2 (T03×2) 行为 100% 不变
- ep_runner_one.py:
  - get_resource_points() 解析 vmap 资源点 (L136-155), 供经济闭环奖励
  - 经济跟踪变量一局生命周期 (L203-215): econ_recruit_first 等 5 变量
  - 经济成型奖励段 (L434-475): 兵力增量差分 / 资源点访问 / 首 RECRUIT+BUILD_2 / 资源-招兵闭环
  - 动作掩码 (L242-296): 非 T04 → logits[16:24]=-inf (等价旧行为); T04 → 位域解码 (recruit_mask@640, build_mask) + 资源阈值 (gold/wood/ore) 逐动作置 -inf
- train_wsl2_ppo_v2.py: Level 3 超参注释包 (BATCH=2048 / EPOCHS=6 / EXTREME_ADV_CLIP=6.0), T04 地图池注释块 (6 张), run_episode 内 explore/nk2_scale/economy_force 切换点注释 (economy_force 前 N 步强制采样 16-21 轮换, 解经济冷启动)
- py_compile 双文件通过 (WSL venv)
- 晋级决策 (2026-08-29): 现在不晋 Level 3 — ① Level 2 未打穿 (真赢 1~2%) ② 学习爬坡无平台 ③ 守卫修复+首胜+100 上线才 1 天样本不足; 晋级线 = 最近 100 局胜率 ≥30~50% 或 avg_r 持续为正; 晋级后先只切 T04 地图不开经济, 稳定后一次一轴开经济 (奖励塑形先行 + 掩码源头做 + NK2/explore 临时上调 + BATCH 加大)

## 真实游戏战略层联调 (Task7, 2026-08-29, forktest66 全绿)

### DLL 端 RL 模型部署 (BC 单输入 → RL 双输入)
- 模型: rl_model_v3464t_0829.onnx = wsl2_ckpt_193821.pt 导出 (fc3464 + CNN 4×21×21 双分支, merge 256→128, actor 25)
- 导出: scripts/export_rl_onnx.py (WSL 跑, dynamo=False; checkpoint=裸 state_dict strict 加载; 对拍 maxdiff 1.9e-06)
- 双输入: obs[1,3464] + terrain[1,4,21,21]; uint8 HWC → float CHW/255 (推理时归一化, 与 strategic_env._build_terrain_grid 一致)
- 模型路径 env 可覆盖: MODELAI_MODEL (默认 rl_model_v3464t_0829.onnx); dump 钩子 MODELAI_DUMP_OBS=1 (stderr 输出 obs+terrain)

### DLL obs 对齐 08-23 语义 (分布差异根因修复)
- DLL obs_fill.cpp 是 08-18 移植版, 缺 08-23 三块: fill_terrain_grid (I.4) / fill_target_list (H.8) / fill_next_dir (I.2 写 reserved[0..7])
- obs_build.cpp reserved 段直接跳过 (idx += RESERVED_SIZE 注释"已 memset 0") 而训练端真实拷贝 — 结构性分布差异的第二根因
- 修复后 14 obs 逻辑段 DLL vs WSL 分布对照全 OK (reserved 两侧 11.2% nz); 判定"数值不同=进程/地图差异, 结构差异=移植缺口"
- towns.recruit_mask_hi 等位掩码字段值可达 2^24 (25,469,088) — 非脏数据

### 验证链与判据
- headless 验证判据沿用: INFER 增长 / 0 Disaster / 0 fishy / MASK 正常; 战斗看 11BattleEnded + 战后 EndTurn 增长
- forktest66: 64 INFER / 244 EndTurn / 0 Disaster / MASK 43 / heroMoved 正常; 战斗未触发 (A Warm 双 AI 不接战, 验战斗换 A Viking)
- 启动姿势: VCMI_client.exe --testmap=Maps/xxx.h3m --onlyAI --headless (client 承载 server; 直接起 VCMI_server 会 Listening 挂等)

### settings.json ai 节点丢失坑
- 用户 settings.json 无 ai 节点 → 回落 Nullkiller2 → bin/AI 无该 DLL → LoadLibrary 126 → 启动即 Disaster
- 修复: ai 节点 5 字段全给 (adventureAlliedAI/EnemyAI=ModelAI + combat×3=BattleAI); schema enum 需含 ModelAI (bin/config/schemas/settings.json 2 处); 已留 .bak_0829

### 未竟
- 1.7.5 官方版 MSVC DLL 未同步本次 4 文件改动 (GUI 人机对战前要重编, build_modelai_175.bat)
- MOVE_TO(act24) 无 DLL 执行器 (模型输出 24 走 fallback)
- AAI 断言崩溃修复 (5b83ace6f) 未同步 WSL .so (P0, 见分析报告)

## A 档四项 + B 档方案 (2026-08-29 晚)

### A2 RL 模型战斗链验证 (forktest67, A Viking 6 人图)
- **判定成立**: 14 场战斗 (20BattleResultsApplied) 全部结算, 0 Disaster, 战后回合持续轮转 → RL 模型战斗链闭环
- 战斗计数口径再确认: 真实场数看 20BattleResultsApplied (结算包) 或 Received CPack BattleEnded; 11BattleEnded 出现≈2×场数 (发送+应用双计数)
- fishy 39 = WALK_AND_ATTACK 偶发 "Two destinations" 类拒绝 (P46/P47 已知残留), 战斗仍能打完, 不阻塞回合 — 新增日志勿惊慌
- RL 模型 (vs BC) 战斗更积极: A Viking 双 AI 8 场 battleStarted vs BC 时代 A Warm 5 分钟 0 接战

### A3 1.7.5 MSVC 重编部署 (RL 模型上 GUI)
- 构建命令坑: git-bash 里 `cmd //c xxx.bat` 弹交互壳**不执行** bat (输出 Windows 版本横幅即中招); 正确姿势 = `powershell -Command "& { cmd /c 'D:\path\xxx.bat' }"`
- 产物验证 (防假构建): python 检查 dll 字节串 — `b'rl_model_v3464t_0829'` (新模型路径) / `b'MODELAI_MODEL'` / `b'OBS_DUMP'` 全 True 才算新 DLL
- 部署三件套: AI/ModelAI.dll + 根目录 rl_model_v3464t_0829.onnx (CWD) + AI/onnxruntime.dll (1.19.2, 防 System32 老版抢加载)
- BND 提醒: 1.7.5 的 settings.json ai 节点 5 字段缺一整节点被 schema 丢弃 → 回落 Nullkiller2 → 启动 Disaster (与 fork 同坑, #115)

### A4 MOVE_TO (act24) 执行器
- 语义对齐训练端: 方向 = reserved[0] (fill_next_dir BFS 首步), 目标 = target_list[0] (最近可采集); reserved[0]∉[0,7] 或空槽 → 返回 false 走 simpleAct fallback
- moveHero 单步 convertFromVisitablePos (P30 坐标系), MODELAI_175 二参 / fork 四参 (EPathfindingLayer::AUTO) 双 #ifdef
- fork + 1.7.5 双端编译部署; forktest68 0 Disaster 链路健康
- 现状: RL 模型极少输出 act24 (训练数据零出现), 执行器先就位, 经济动作上线 (B2/D1) 后才有实战价值

### B1-B4 方案要点 (全文见 docs/方案_B1-B4_20260829.md)
- B1 解封: `--guard_grad_scale_by_map` 代码已存在 (0.5×max(1, w/20)); 方案 A = MAPS 渐进 2→3→4→6 张每步 100 局观察; 方案 B (vmap 移近) 备选
- B2 经济: 代码 s2a-s2e 已备齐; 定值 economy_force=24 步轮换, T04 6 图先开 2, BATCH 2048/EPOCHS 6, explore 0.25; 次序 = 先晋级 T04 地图后开经济 (一次一轴)
- B3 熵 bonus: ent_coef 前期×2 指数衰减 200 万步 (训练侧一行); 拒绝开局强制随机 (采样污染); 监控 3/7+10 占比 >85% 告警
- B4 晋级判据: 双条件 = GUARD 首胜率≥30% 且 avg_r≥+15 连续 3 窗 (T03 阶段 GUARD 首胜作"胜" proxy); 5 指标 grep 规格定稿, 实装随 C1

## 上游差异报告落地 (2026-08-29 晚, 报告=docs/upstream_diff_report_20260829.md)

### 差异全景
- 本地 vcmi submodule (5b83ace6f, fix_action_mapping) vs upstream/develop 8229b274 (08-28): 落后 662 提交 / 本地领先 59
- 变更量: server 38 文件 / AI 84 (NK2 寻路为主) / lib 706 (MetaString 翻译重构为主)
- **真实冲突面 = 71 文件** (本地 59 提交的 328 文件与上游 1809 文件的交集), 之前整包合并的 22 冲突全落在这
- 冲突分两类: ①机械漂移 (命名空间宏删除 662c819065 波及 1004 文件, 解法=删两行宏, 零风险) ②真实语义分歧 (moveHero passableFor ← seer_rework, 需整包评估)

### 摘取清单 (已 merge-tree 真实预演验证, 按执行序)
| 序 | 目标 | 预演 | 备注 |
|---|---|---|---|
| 1 | PR #7744 地图加载加速 (8 提交) | 7 CLEAN / 1 冲突=测试文件丢弃 | **训练吞吐最直接** (ep_runner 逐局加载), 优先落地 |
| 2 | PR #7632 NK2 寻路性能 (11 提交) | 9 CLEAN / 2 冲突=单头文件命名空间宏 | 两冲突文件本地从未改过 (已核实), 解冲突=删宏 |
| 3 | f4c622c842 神器即胜 / 0981f48837 移动层传播 / 15034e38c9 下船落水 | 全 CLEAN | 直接摘 |
| 缓 | TurnOrderProcessor AI/人类分流 | 需评估本地是否复刻人类分支修正 | 第四步 |
| 拒 | seer_rework (PR #7535) 整包 | 依赖大重构 | 边境守卫 c9023e74c1 依赖它, 放弃或整包 |
| 拒 | MetaString/翻译重构 ×5 | 纯重构噪音, MMAI 零收益 | 跳过 |

### 执行约束 (C4 档)
- 摘取编译产物进 **libvcmi.so** (训练端在用) — 训练期禁止, 必须停训窗口
- 前置: Windows submodule ML/ 三文件未提交改动先清; vcmi-native 侧同步核对
- 摘后必须: 重编 libvcmi + 重链 libmlclient + 冒烟 + 重启训练 — 本身就是一次停训窗口动作
- 复核方法 (报告§9): `git merge-tree --write-tree --merge-base=<c>^ <tree> <c>` 返回 0 无 CONFLICT = CLEAN; 链式预演每次取输出首行作下次输入

## 二十四、T04 课程引导体系 (2026-08-29 晋级后落地)

> 背景: Level 3 晋级 (T03 毕业 → T04 六图) 后模型乱逛 r=-80~-110。三层诊断锁定根因 → 目标优先层 + 事件奖励 + 强制期延长三件套修复。

### 1. T04 地图与引擎胜利条件

- T04 六图由 `maps/training/gen_curriculum_all.py` 生成, **cfg 无 monsters 键 = 显式 0 守卫** (课程重心从战斗转向城镇/经济)
- owner 分配: hero_0/town_0 = red (我方), hero_1/town_1 = blue (对手), 各 1 英雄 1 城 1 矿 3~5 资源堆
- victoryConditions = `standardDefeat` = 消灭对方全部英雄+城镇。red 赢 = 杀 blue 英雄 (iona) + 占 blue 城 (对角)
- game_over 信号链 (P9 已核): strategic_state.cpp 轮询 `players[p].alive (status==INGAME)` → `game_over=last_alive+1` → env reward ±200 (reward_win) + NK2 势函数 ±50 → `_check_done` terminated

### 2. 三种"视野/目标"语义辨析 (易混, 坑 #118)

| 尺寸 | 通道 | 内容 | 用途 |
|------|------|------|------|
| 15×15 | obs[480:705] local_tiles | 通行性 (0未知/1可走/2障碍), hero 恒 (7,7) | Python BFS 寻路 (±7 格有效) |
| 21×21 | terrain_grid.bin CNN 分支 | 纯地形 4 通道, **无对象位置** | 网络地貌感知 |
| 8×8 | obs[3251:3315] target_list | C++ 填的目标表 [type,idx,x,y,z,dist,power,flags] | MOVE_TO 目标源 |

### 3. target_list 实测 (check_target_list.py, T04_30X30_01)

- **矿在**: type=1 (mine_0); **资源堆在**: type=2 ×5; **城镇不在** (C++ 白名单不填 town)
- C++ next_dir (obs[3330:3338]) 全图 BFS 对**任意距离**目标有效 (dist=41 远矿也给方向, check_next_dir.py 验证 33/33 步有效)
- 引擎实际加载地图路径 = 进程 cwd 相对 `data/Maps` = `vcmi-native/rel/bin/data/Maps` (部署副本, 改图后须同步, 与项目 maps/training 已核对一致)

### 4. 乱逛根因 (r=-80~-110, 19 局 0 胜负局)

1. **近目标吸住**: runner 24 展开 = 选 dist 最小 target → 资源堆 dist 5~21 恒压过矿 dist 41 → 200 步在资源堆间游走, 矿永不可达
2. **强制期覆盖不了闭环**: move_to_force≈28 步, T03 守卫 d≤6 强制期内完成"走到→+100"闭环; T04 dist 41 → 强化信号断在半路
3. **失败信号被剪**: strategic_env `np.clip(reward,-10,300)` 下限把 blue 胜利 -200 剪成 -10 → 输赢差 10 分, 模型"输也无所谓" (坑 #116)

### 5. 修复三件套 (2026-08-29, 全纯 Python)

| 修复 | 位置 | 内容 |
|------|------|------|
| clip 对称 | strategic_env.py L1122 | `np.clip(reward, -300, 300)` — ±200 胜负信号真实传递 |
| 事件奖励 | ep_runner_one `--objective_reward N` (默认 0=关) | 首占矿 [MINE] / 首进城镇 [TOWN] 各 +30, 复用守卫 +100 位置重合法 (get_objectives 读 vmap) |
| 目标优先层 | ep_runner_one obj_best (24 展开处) | 矿 (target_list type=1, 带 slot idx→C++ next_dir) / 城镇 (Python 注入) 恒优先于最近资源堆; 占领后 (mine_taken/town_visited) 排除防粘死; 城镇贪心卡死 → move_stall≥6 → town_blocked 本局禁用 |
| 强制期延长 | train_wsl2_ppo_v2 (T04 分支) | `--move_to_force 60` 常驻 (T03 保持 30×scale); eval_promo 按图名自适应 60/15 |

### 6. 撤销策略 (可逆性分析结论)

- 注入只改"动作 24 的目标选择实现" (env 语义), 不碰 OBS/动作空间冻结面 → 完全可逆 (一行开关)
- 推荐常驻 (T03 守卫注入先例, 毕业时从未撤销); 可选降级路径: 占矿率>80% 后从"优先"降为"兜底" (C++ 池空才用)
- 训练/eval/部署三处同口径 = 注入是环境定义的一部分而非作弊

### 7. 观察指标

- [MINE] 触发频率 (占矿率): 模型学会奔矿的标志; [TOWN_BLOCKED] 频率 (城镇贪心卡死率)
- ±200 胜负局是否出现 (clip 修复后应可见); T04 分层: `py/analyze_ab.py`

## 二十六、经济动作 (16-21) 真实语义与 II.3 开经济调优 (2026-08-29 夜)

### 1. 动作语义澄清 (重要 — 早期"三档资源档位"理解有误)

C++ 实现: `AAI::executeAdvancedAction` (AAI.cpp L170+, libMMAI 13c0f041):

| 动作 | **真实语义** (策略变体/建筑链, 非档位) | C++ 调用 |
|------|----------------------------------------|----------|
| 16 RECRUIT_1 | 最近己方城镇**招最低级兵 ×1** | recruitCreatures |
| 17 RECRUIT_2 | 最近己方城镇**招最高级兵 ×1** | recruitCreatures |
| 18 RECRUIT_3 | 最近己方城镇**全部可招兵各 ×1** | recruitCreatures 循环 |
| 19 BUILD_1 | 大厅链第一个未建 (村→镇→城→首都) | buildBuilding |
| 20 BUILD_2 | 兵种链第一个未建 (1~7 级巢穴) | buildBuilding |
| 21 BUILD_3 | 防御链第一个未建 (堡垒→要塞→城堡) | buildBuilding |

- 19-21 的"档位"实为**三条建筑链**选择; 16-18 为**三种招兵策略**
- 唯一失败条件: 无己方城镇 → return noTarget; 本周无兵 → recruitCreatures 招 0 个 (引擎 clamp, 不报错)
- 掩码 (recruit_mask/build_mask @ obs[640:704]) = 城镇可招募/可建造状态位域, 与英雄位置无关

### 2. 远程性实证与执行链路

```
runner (a=16-21) → strategic_env.step → adventure_send_action (atomic)
  → AAI::yourTurn (阻塞) → adventure_get_action → executeAdvancedAction
  → nearestOwnTown(cb, cur) → cb->recruitCreatures/buildBuilding  ← 玩家级操作, 与英雄位置无关
```

- 实证: [ECON] first RECRUIT/BUILD_2 在 step 0-4 触发 (英雄在地图角落)
- **结论: 模型不需要任何位置提示**; obs 已含位域 (640:704) + 资源字段 (304:311), 掩码保证只从合法集选

### 3. II.3 开经济配置与调优链 (08-29 夜)

| 配置 | 值 | 教训/依据 |
|------|-----|----------|
| economy_force | **24 步** | 50 步实测学费过重: 50 步原地空转 (16-21 不移动) = -25 步罚 + 延误奔矿 50 步, r 均值 -93; 改 24 后 -4.5 (B2 方案原值) |
| explore | 0.3 (0.2→) | 经济动作初期防 entropy 塌 |
| nk2_shaping_scale | 0.45 (0.3→) | 经济长程行为需更强势函数 |
| RECRUIT 奖励 | **+12/档** (+5→) | 自主经济卡 0.6/局平台, 提高相对占矿+30 的吸引力 |
| BUILD_2 奖励 | **+15** (+8→) | 同上 |
| 城镇引导 | **降级移除** | RECRUIT/BUILD 玩家级远程无需到城; 城镇贪心远距必卡死 (每局烧 6 步 + [TOWN_BLOCKED] 常态); [TOWN] +30 保留为路过事件 |

单局经济收益上限: RECRUIT×3 (+36) + BUILD_2 (+15) + 闭环 (+15) = **+66**, 与占矿 +30 同量级。

### 4. 效果时序 (启动段 ep1-55)

| 阶段 | avg_r | 特征 |
|------|-------|------|
| 50 步版 | -0.6 | 强制期空转学费深负 -134 |
| 24 步版 | -0.2 | 自主 MOVE_TO 涌现, r 均值 -4.5 |
| 奖励上调后 | 0.0→-0.5 震荡 | **正局质量新高 +75.3/+62.3** (占矿+经济+势函数叠加), 正局率 53%; 深负偶发 (-90.7, 接战战损型) |

- 自主 16-21: 0 → 0.6 → 1.0 → 0.8/局 (破零但未爆发, 奖励梯度传播中)
- [ECON] 事件稳定 1.2 次/局 (RECRUIT 首访 + BUILD_2)
- ⚠ [ECON] 不在主日志转储词表 — 观察 grep `/tmp/hermes_ep_*.log` (待办: 词表补 [ECON])

### 5. T04 战局结构认知 (用户判断核验的方法论沉淀)

- T04 **零守卫** — "打不过的守卫"不存在; 深负主因 = vs blue NK2 英雄接战战损 (red 战斗 Router 回退 StupidAI 接战必弱)
- Router 回退只在接战时触发 — 模型学会避战后频率自然下降 (最近窗口 0 条); 根治需 C++ 重编 (跨 .so RTTI cast 问题, 留停训窗口)
- r<-150 局从未出现 = blue 从未推平我方 (blue 胜利 -200 clip±300 真实传递的判定标志)
- 深负 -45~-90 窄带 = 战损势函数 + 200 步游荡步罚累积, 非团灭定局

## 二十五、训练日志数据管道 (2026-08-29, P4 死锁聚合产出)

> 三层日志的分工、生命周期与已知陷阱。分析工具: analyze_deadlock.py (纪元聚合) / analyze_ab.py (A/B+晋级)。

### 1. 三层日志分工与生命周期

| 层 | 文件 | 生命周期 | 内容 |
|----|------|----------|------|
| 主日志 | `train_loop.log` | 追加, 永久 | ep 汇总行 (ep_steps/r/act/obs_nz/map=) + PPO 点 (avg_r/vloss/kl/klc) + 事件转储 |
| 明细日志 | `/tmp/hermes_ep_<pid>.log` | **逐局覆盖** (同 PID 一个文件) + **/tmp 重启即清** | ep_runner 子进程 stdout 全量 ([ZOMBIE]/[GUARD]/[ERROR]/断言栈) |
| 轨迹 | `/tmp/traj_ep.json` | 逐局覆盖 | obs/act/rew/done 数组 (训练进程消费) |

⚠ **历史明细不存在**: 明细日志只反映"当前局"。历史统计一律以主日志为准 — 主日志的事件行靠转储机制留存, 词表外的行永久丢失。

### 2. 主日志转储词表 (train_wsl2_ppo_v2.py)

- 机制: 局末训练进程按词表过滤子进程输出, 命中行转储主日志
- 词表 (08-29 增补后): `[ZOMBIE]` / `[ENDTURN_FUSE]` / `[ERROR]` / **`[GUARD]`** (守卫首胜, 此前从不进主日志) / **`Assertion`** (引擎断言崩溃行不带 [ERROR] 方括号, 此前漏网) / `end ep at step` / `fuse-break` / `cycle_detect triggered` / `penalty END_TURN`
- 生效方式: train_wsl2_ppo_v2.py 进程启动时加载 → 改词表需重启才生效 (ep_runner_one 是逐局重载, 改它即时生效)

### 3. 空转局污染与过滤口径

- 空转局特征: `steps==1 且 r≈1.7` (引擎断言雷段产物, 坑 #115)
- 危害实例: analyze_ab 晋级窗口曾虚报 87/100 (含 60 空转局), 过滤后真值 26/100; A/B 正局率 97.3%→90.9%
- 过滤规则 (analyze_ab.py 两处解析均已加): `steps==1 且 r<5 → 剔除`; analyze_deadlock.py 的"空转"列即此口径

### 4. analyze_deadlock.py 纪元切分法

- 以 `Loaded train state (model+optimizer, step=N)` 横幅为纪元边界 (每次重启一段), 按段统计局数/首胜/空转/ZOMBIE/熔断/大负/avg_r + ZOMBIE 步位分布 + 最后纪元分图统计
- 口径: 首胜 = r≥80 且 steps<60; 大负 = r<-100 (clip±300 修复后 T04 需重审此阈值, -100 不再是大负天花板)

### 5. 短窗口抽样错觉 (map= 字段)

- MAPS 轮换 = `random.choice(MAPS)` 均匀抽样, 3 图连续 7 局同图概率 (2/3)⁷≈5.9% — tail 看不到某图≠池里没有
- 验证进程真实配置: `ls -l /proc/<train_pid>/cwd` + grep 该目录下的 train_wsl2_ppo_v2.py (systemd ExecStart 用相对路径, cwd 才是真相); 全程分布核对用 `grep "map=" train_loop.log | grep -o "map=\S*" | sort | uniq -c`

