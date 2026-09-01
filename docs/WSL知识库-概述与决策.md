# WSL知识库 — 概述与决策

> 本文件是 `WSL知识库.md` 总索引下的稳定参考子文档（项目概述与关键技术决策）。
> 结论性内容，按需就地修订；内容截至 2026-08-29。

---

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



### 3.3 为什么放弃 ARM64 训练



**根因：** headless=true 下 VCMI 的 `networkHandler->createTimer()` 不触发，游戏不进首回合。

**尝试过：** ctypes→connector 迁移、DummyVecEnv 短路、MLClient 注入 mainLoop、Xvfb —— 全部失败。

**结论：** 根源在 VCMI 服务线程网络层事件循环，涉及 `lib/client/GameEngine.cpp`、`lib/server/CVCMIServer.cpp`、`lib/network/` 源码改造，不确定性大。

**决定：** ARM64 留作推理端，训练全部移到 WSL2。



### 3.4 为什么选 Nullkiller2 而非 MMAI



- MMAI (Mini AI) 模块在 WSL2 上初始化阶段 core dump

- MMAI 含 broken `g_cached_game_state` 代码，清理后依然不稳定

- Nullkiller2 是 VCMI 内置冒险 AI，稳定且已有 AIGateway.cpp 回调钩子

- 切换方式：`ENABLE_MMAI=OFF`, `ENABLE_NULLKILLER2_AI=ON`



### 3.5 训练地图: 课程学习 VMAP 体系 (2026-08-23 起全量使用)



**现状：** 训练 MAPS 全部走课程学习 vmap (Phase I.4)。31 张 Level 0-5 地图 (T01-T06 系列) 已生成并实跑验证，Level 0 (T01×5) 已接入训练。

**历史教训：** 早期 vmap 全部不可用 — train_v1.vmap 从未真正加载成功 (blue hero core:inham 不存在 + wt/ro 地形崩)，gen_v3.py 的 players 数组格式直接 core dump。**"VMAP 兼容性待解决, 暂用 H3M" 的真相 = 生成格式错误, 不是 VCMI 不支持 vmap。**

**vmap 格式要点（VCMI 1.7.4）:**

- header players 必须 dict 格式 {red:{heroes,mainHero,team}, blue:{...}}, 数组格式崩

- terrain 代码: 只用 gr24_ (草地) — wt00_/rc00_ 加载 segfault (待查, 踩坑 #87); rock shortIdentifier=rc 非 ro; 无 road 类型

- town mask 5x3 anchor 居中 → town_x∈[2,w-3], town_y∈[1,h-2], 越界左崩

- hero/资源/野怪: 标识符必须真实存在 (core:edric/iona/gold/wood/crystal/swordsman), resource 需 options.amount

- 验证必须 ep_runner 实跑 20 步, 不能只查 zip 结构 (test_vcmi_load.py 是假验证)

- 生成脚本: maps/training/gen_curriculum_all.py (T01-T04, 坐标规则化+界内校验)



### 3.6 观测与动作



- 观测 ~256 维：英雄位置/兵力/移动力、城镇/资源、敌方可见信息、日期

- 动作：移动(8方向) + 交互 + 城镇操作 + 结束回合

- AI 对手使用 Nullkiller2（不耗 ML 推理）



### 3.7 step() 通信机制（C7 最终架构 + B 修复 + #45 修复）



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



### 3.8 C7 动作映射架构



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



### 3.9 战斗处理



英雄踩怪物：

1. startBattleHook(hero1, hero2=null) → return（跳过 ML 随机初始化）

2. VCMI autofight 自动裁决

3. endBattleHook(heroDefender=null) → return（跳过 stats 记录）

4. 战斗完成，继续 turn 循环



---



