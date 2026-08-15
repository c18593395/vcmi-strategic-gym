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

### 3.4 战略训练只用 H3M，不用 vmap

**历史教训：** 早期用 vmap（战斗模型训练图）跑战略训练，大部分 vmap 不是 2-player 布局，导致 adventure 回调不来或崩溃。
**原则：** 战略训练只用 H3M 经典图。
**现状：** scan_maps.py 从 158 张中筛出 110 张可用 2-player H3M。

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

### 4.8 用 vmap 跑战略训练（已修复）

| 项目 | 内容 |
|---|---|
| 根因 | 战略图误用战斗 vmap，assert 检查不过 |
| 修复 | 只使用 H3M 经典图，scan_maps.py 验证可用性 |

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
