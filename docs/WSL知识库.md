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

