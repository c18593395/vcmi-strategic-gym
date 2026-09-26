# WSL踩坑点 — 引擎-VCMI-API

> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。

---

### 修复链

| 问题 | 症状 | 修复 | 文件 |

|------|------|------|------|

| #46 installNewBattleInterface segfault | neutral 玩家初始化崩溃 | 重建三件套 (2026-07-29) | `client/Client.cpp` |

| Discord null reference segfault | post-init segfault | `if(ENGINE->hasDiscord())` guard | `client/GameEngine.h`, `client/CServerHandler.cpp` |

| 信号量通信 (`adventure_wait_for_turn` 永远不返回) | obs_nz=0 | `AAI::yourTurn` 调 `adventure_process_turn()` | `AI/MMAI/AAI/AAI.cpp` |

### 当前工作组合（已验证通过 env.reset()）

- `libmlclient.so` = 最新重建（含 Discord fix + 信号量）

- `libMMAI.so` = 最新重建（含 `adventure_process_turn` 调用）

- `vcmiserver` = 最新重建

- `connector_v13.so` = 最新重建

### 已知剩余问题

- `obs_nz=8/264` — 低但非零。`random_heroes=0`、地图初始状态淡、`fill_state_from_cb` 可能还有缺失数据

- `step()` 未验证

- 新版 libmlclient.so 有新增的 try-catch + before/after 日志（无影响）

---

### 待归档新增

### 2. canMoveBetween 太宽松 → passability 全1

- **现象**：`obs[-8:] = [1,1,1,1,1,1,1,1]` 永远全可通

- **根因**：`CCallback::canMoveBetween()` 只查 `isBlockedVisitable()`，不查 `terrain.isPassable()` 和障碍物。且客户端 CGameState 在 yourTurn 时数据不完整

- **修复**：改用 `CGameInfoCallback::getTile(target, false)->isClear(heroTile)`，检查实际地形+障碍物

### 3. waitTillRealize=true → moveHero/endTurn 卡死

- **现象**：`cb->moveHero()` 和 `cb->endTurn()` 永远不返回

- **根因**：`cb->waitTillRealize = true` 时，moveHero 同步等待服务器确认。被拒绝的 move 不返回确认 → 线程卡

- **修复**：调用前 `cb->waitTillRealize = false`，调用完恢复

### 3b. adventureAlliedAI/EnemyAI 全被改成 Nullkiller2 → red 失联

- **现象**: env reset 后 adventure_wait 超时；日志显示 `NK2AI::AIGateway::makingTurn` 处理 red 的回合（"Player 0 (red) ended turn"）

- **根因**: MLClient.cpp 把 `adventureAlliedAI` 和 `adventureEnemyAI` 都写成 "Nullkiller2"（C8.1 改的）→ **所有玩家**冒险 AI 都是 NK2 → MMAI 的 AAI::yourTurn（模型注入）永不触发

- **修复**: `adventureAlliedAI="MMAI"`（red 注入路径），`adventureEnemyAI="Nullkiller2"`（blue/tan 真 AI 对手）

### 4. Non-red 玩家不处理 → step 超时

- **现象**：step() 等待 30s 后 timeout

- **根因**：red endTurn 后 game 调 blue/tan 的 yourTurn，但旧代码用 asyncTasks 异步处理且不 endTurn → 卡住

- **修复**：`AAI::yourTurn` 对非红方立即 selectionMade + doEndTurn（设 waitTillRealize=false）

### 4b. build 目录 ServerPlugin 缺野怪保护 → NK2 打野 abort

- **现象**: `Exception: Both hero1 and hero2 are required` + std::unexpected abort（BattleProcessor::startBattle）

- **根因**: build 目录 ServerPlugin.cpp 是旧版（startBattleHook 强制双英雄）；项目源新版已有 `if (!(hero1 && hero2)) return` 保护

- **修复**: build 旧版补齐 startBattleHook/endBattleHook 野怪保护（battlecounter++ 保留）

- **教训**: 项目源（git）与 build 目录长期分叉，编译真理在 build 目录，但新修复往往只在项目源。改 build 前先 diff

### 5. onlyai 下无 human → 所有玩家走 adventureEnemyAI

- **现象**: 即使 AlliedAI=MMAI，red 仍被 NK2 接管

- **根因**: Client.cpp `initPlayerInterfaces`：`onlyai=true` 时 debugStartTest 主动把 host 从玩家颜色移除 → 无 human 玩家 → `alliedToHuman` 恒 false → 全部 `adventureEnemyAI`

- **修复**: Client.cpp 强制 `color == PlayerColor(0)` 用 `adventureAlliedAI`（MMAI），其他玩家走原逻辑（NK2）

- **机制**: VCMI AI 名选择 = `aiNameForPlayer(ps)`：ps.name（仅识别 Nullkiller2/EmptyAI）> alliedToHuman ? adventureAlliedAI : adventureEnemyAI

- **构建链坑**: Client.cpp 编进 `vcmiclientcommon` → **链接进 libmlclient.so**（不是 vcmiserver！）。改 Client.cpp 后必须 `make vcmiclientcommon && make mlclient`，vcmiserver md5 不变是正常（它不含 client 代码）

### 7. 战斗 AI 三选一全废 (C8.5 训练卡死根因链)

- **现象**: NK2(blue) 打野怪 → 战斗开始 → 卡死或崩溃, ep_steps=1~2

- **根因链** (逐层定位):

  1. `combatEnemyAI/NeutralAI` 设置在 **"server" 路径** (无效) → 实际用 schema 默认 **BattleAI** → headless 下等待回调卡死

  2. 换 **StupidAI** → `libStupidAI.so does not export GetNewAI` (ABI 不匹配, 只有 GetNewBattleAI 无 GetNewAI) → 冒险 AI 加载崩

  3. 换 **MMAI** → battleStarted → Router::battleStart → `ASSERT(cb->getPlayerID()->hasValue())` — **neutral 玩家无 playerID → 抛异常 → 穿过 noexcept 边界 → std::unexpected 崩溃**

- **修复**: ① 战斗 AI 键改 `{"ai", ...}` 路径 + 全用 MMAI (leftModel/rightModel=Scripted("StupidAI") 自动裁决) ② Router::battleStart neutral 无 playerID 时用 modelRight + 整体 try-catch fallback StupidAI ③ 战斗结果对话框 `IFML(true,false)` 禁用 (ML 模式 AI 不回答 CBattleDialogQuery → 永久卡) — **server 代码链接进 libmlclient.so, 改 BattleResultProcessor 必须 make mlclient 而非 vcmiserver**

- **教训**: 进程内 server (useProcess=false) — server 代码在 libmlclient.so; 改 server 逻辑后验证二进制归属 (grep -acl "消息文本" rel/bin/*)

### 11. 无 playerID 的玩家 (neutral) 触发 MMAI ASSERT 崩溃 (C8.5)

- **现象**: NK2 打野怪 → battleStarted → std::unexpected 崩溃 (VCMI 死)

- **根因**: Router::battleStart `ASSERT(cb->getPlayerID()->hasValue())` — neutral 玩家无 playerID → throw → 穿 noexcept → unexpected

- **修复**: neutral 无 playerID 时用 modelRight + 整体 try-catch fallback StupidAI

- **教训**: MMAI 代码假定"无 neutral 玩家参战" (注释 XXX: dev mode assumes there are no neutral players in battle) — 训练打野怪必然触发

### 12. DATA/LCDESC 缺失 → VCMI 初始化崩溃

- **现象**: `Resource with name DATA/LCDESC and type TEXT wasn't found`

- **原因**: libvcmi.so 从 data 目录找不到游戏资源

- **解决**: data 必须指向 HoMM3 安装目录 (含 Data/H3bitmap.lod 等)

### 12b. TerrainTile::isClear() 无 from 参数 → segfault (2026-08-01)

- **现象**: 采集/训练 reset 后静默 segfault（无 traceback, 进程 Aborted）

- **根因**: `tile.isClear()` 默认 from=nullptr → VCMI 内部 `from->getTerrain()` 解引用 null → 崩

- **定位**: gdb --batch -ex run -ex "bt" --args python collect_bc.py（拿 C++ 栈: fill_exploration → isClear → entrableTerrain → getTerrain this=0x0）

- **修复**: `tile.isClear(&from_tile)`（传英雄所在格, 对齐 passability 写法）

- **教训**: VCMI 的 isClear(from) 的 from 必须有效; 新代码调用前查 API 默认参数

### 13. CONFIG/FILESYSTEM 缺失

- **现象**: `Resource with name CONFIG/FILESYSTEM and type JSON wasn't found`

- **原因**: config 目录为空或缺失

- **解决**: config/ 下至少放 modSettings.json、settings.json（可空{}）

### 14. g_adventure_cb lambda 导致 crash

- **现象**: 在 MLClient.cpp 的 init_vcmi() 中加 `g_adventure_cb = [](int,void*){}` 后 env.reset() crash

- **原因**: extern "C" 函数指针与 C++ lambda 的 ABI 不兼容

- **解决**: 删除 lambda，回调注册放别处

### 14b. VCMI settings 写读层不一致 → AI 分配失效 (2026-08-01)

- **现象**: red_adventure_ai="Nullkiller2" 但 Opening 全是 MMAI, act=-1（MMAI 的 send_action(-1)）

- **根因**: `Settings(settings.write({"ai",...}))` 写 session 层, Client.cpp `settings["ai"][...]` 读配置层 → 写入不生效（读默认 MMAI）。C8.5 训练没暴露（默认 MMAI 恰好正确）

- **修复**: 跨 .so 全局 `extern "C" char g_adventure_allied_ai[64]`（MLClient strncpy 写 / Client.cpp 读, g_ml_player_cb 同模式）

- **教训**: 验证 settings 写入生效用运行时日志（friendlyAI/playerAI 打印的是 combat/冒险 AI 别混淆）; 写入非默认值才暴露层问题

### 15. env.reset() 阻塞 (战斗模式)

- **现象**: opponent='BattleAI' 时，reset() 永远不会返回

- **原因**: VCMI 进入战斗后等待 Python 侧发送动作 (MMAI_USER)

- **解决**: 用 MMAI_RANDOM 或 StupidAI 作为双方避免阻塞

### 16. VCMI 关闭时 SIGSEGV

- **现象**: 训练完成或 env.close() 时 random segfault

- **原因**: VCMI 内部关闭流程有 bug，非我们代码导致

- **解决**: 训练脚本已处理 (os._exit(0))

### 17. train_anchor.py 的 capture_output 问题

- **现象**: subprocess.run(capture_output=True) 时子进程卡死

- **原因**: VCMI 输出大量日志，管道缓冲区满

- **解决**: 改为 capture_output=False，或增大缓冲区

---

### 17b. 动作 8 INTERACT 从未实现 — 文档与代码脱节 (2026-08-15)

- 现象: 冒烟测试 RECRUIT/GARRISON/RECRUIT_HERO 全失败, 英雄永远进不了城

- 根因: 设计文档标 INTERACT(8) "✅ 已实现", 但 AAI.cpp yourTurn 无 a==8 分支（历史遗留）→ 动作 8 实际是 no-op 直接 endTurn

- 修复: interactTarget 优先最近己方城镇（3 格内）→ 其次最近可交互对象; standPos==heroPos 时 moveHero 到对象格触发交互, 相邻走 standPos, 远则逐格逼近

- 教训: 文档状态不可信, 冒烟测试逐动作实机验证是唯一真相; 历史"动作 8 可用"的验证可能也是 NK2 假象

### 18. swapGarrisonHero 未进城挂起 120s (2026-08-15)

- 现象: GARRISON 动作后 adventure_wait timed out after 120s（query 无人应答）

- 根因: 英雄未 visiting 城镇时 swapGarrisonHero 触发服务器 query 等待, 无应答挂起

- 修复: 先 cb->moveHero(cur, standPos, false) 进城, 轮询 cur->getVisitedTown() == town 确认后再 swapGarrisonHero; 未进城则放弃

- 教训: 动作实现必须带前置条件检查（NK2 DefenceBehavior 同款: 先移动英雄进城再交换）; 挂起类 bug 的检测靠 120s 超时

### 19. moveHero 单格版只允许相邻格 + 目标必须是可站格 (2026-08-15)

- 现象: MOVE_TO/INTERACT 直接 moveHero 到远处对象, movement 扣了但位置不变（引擎静默拒绝）

- 根因1: CGameHandler::moveHero STANDARD 模式检查 !h->pos.areNeighbours(dst) → "Tiles are not neighboring" → 远处目标直接 FAILED

- 根因2: moveHero 目标是可站格, 直接传对象 visitablePos 会被 BLOCK（城镇格 terrain 不可站）

- 修复: moveOneStepToward 8 方向夹角最小逐格逼近; 目标用 hero->convertFromVisitablePos(obj->visitablePos())

- 教训: NK2 用 calculatePaths + 完整路径数组, 我们 v1 简化逐格; 引擎 API 的"看起来能传任意坐标"都是假象

### 20. 冒烟测试必须 MMAI 模式 — Nullkiller2 是假象源 (2026-08-15)

- 现象: smoke_h7.py 用 Nullkiller2 模式, SPLIT 显示兵力转移"PASS"（31→1/37→67）, 但其实是 NK2 自己的分兵行为

- 根因: red_adventure_ai=Nullkiller2 时你的 Python 动作根本不进 AAI::yourTurn（NK2 自己决策执行）→ 所有 PASS 与动作实现无关

- 修复: 动作测试用 red_adventure_ai=MMAI（AAI::yourTurn 消费 Python action）; collect_bc.py 用 NK2 是采集 NK2 行为, 用途不同

- 证据: 加 fprintf(stderr, "[H7-DBG] yourTurn action=%d") 后 Nullkiller2 模式零输出, MMAI 模式正常打印

- 教训: 验证动作执行必须先确认执行链真的走了你的代码（诊断打印是最快确认）; 数据驱动的 PASS 可能是对手行为

### 21. dlsym 找到旧版 strategic_state_update

- **现象**: `dlsym(RTLD_DEFAULT)` 在 libvcmi.so 里先找到旧版 strategic_state_update（无 P0 自分配），新版在 libmlclient.so 里不被执行

- **解决**: 改 extern "C" 直调，不用 dlsym。链接器保证找到 libmlclient.so 的正确版本

### 21b. bulkSplitStack 是军队内部平铺, 不能跨英雄转移 (2026-08-15 H.6)

- 现象: 设计文档写 SPLIT_ALL 用 bulkSplitStack, reasonix 调研 CGameHandler.cpp:1705 发现实现是 srcArmy==dstArmy 军队内部平铺

- 根因: bulkSplitStack 语义是"把某个槽位的兵平铺到军队内其他空槽", 参数没有跨英雄的 dst 概念

- 修复: SPLIT_ALL 改用 bulkMoveArmy(currentHero->id, nearestHero->id, srcSlot)（有 isAllowedExchange 相邻检查, 失败静默, 符合 v1 简化）

- 教训: 动作设计文档的引擎接口名未核实实现就写死; 委派外部 agent 前先核实关键 API 语义, 或让 agent 调研阶段就核对 CGameHandler 实现

### 22. struct 尺寸不可改

- **现象**: 在 `StrategicState` 中加 `int32_t action` 字段后全量编译失败

- **根因**: strategic_state.cpp 被编进 mlclient.dir 和 vcmiservercommon.dir，两处 sizeof 不一致

- **解决**: action 放独立全局变量 `g_rl_action`，不碰 struct

### 24. moveHero 在回调链中 segfault

- **现象**: yourTurn 内直接调 cb->moveHero() 段错误

- **根因**: VCMI 在 query 回调上下文中禁止 game action

- **解决**: 先 cb->selectionMade(queryID) 回答 query（释放上下文），再调 moveHero。2026-07-27 验证直接调在 WSL2 不再 segfault——直接 moveHero 成功

### 24b. passable mask 与 moveHero 目标格不一致 — 英雄模板 visitableOffset 偏移 (2026-08-16 H.8 根因)

- 现象: PPO 训练 40 局英雄位置永远不变 (107 步全在 (16,15,1)), 服务器持续报 "Cannot move hero, destination tile is blocked!"; obs passable 段标方向 5(SW) 可通行但服务器拒, 方向 4(S) 标不可通行但 NK2 实际走通

- 根因链:

  1. obs passable fill (strategic_state.cpp) 用 heroes[active_hero].pos (对象锚点) + dir 作为目标格做 isClear

  2. 服务器 CGameHandler::moveHero 检查 convertToVisitablePos(dst) = dst - getVisitableOffset() — 英雄模板 ["VVV","VAV"] offset=(1,0), 锚点与可站格差 1 格

  3. fill 用锚点+dir 算出的"可通行方向" = 服务器实际检查格 + offset → passable=1 的方向被服务器以 blocked 拒绝, 真可走的方向标 0

- 修复 (commit acc1a7f92): fill 的 hpos 改用 hero->visitablePos() (pos - getVisitableOffset()) — 站立格 + dir == 服务器检查的 convertToVisitablePos(pos+dir)

- 附加修复: fill_exploration active_hero 强制 owner==0 (防 g_active_hero 越界到 blue 槽位), 无 red 英雄时 -1

- 验证: 修复后 passable=[0,0,0,0,1,0,0,0] (方向 4=(16,16) 正确), 模型按 mask 选方向 4 moveHero 成功 (16,15)↔(16,16)

- 教训: **obs 任何位置/格子相关字段必须与服务器 CGameHandler 的目标格语义对齐** (visitablePos vs anchorPos); 验证训练环境健康的第一信号是英雄位置是否变化, 不是 vloss/avg_r

### 25. "Player is not allowed to perform this action!"

- **现象**: 后台线程 asyncTasks->run(moveHero) 被服务器拒绝

- **根因**: selectionMade 在 moveHero 前调用，服务器认为玩家已非 active

- **解决**: 不要在 moveHero 前答 selectionMade。**最终架构**：yourTurn 单次 action → 直接 moveHero → selectionMade → endTurn。不需要 asyncTasks

### 26. waitTillRealize=false 对 endTurn 必要

- **现象**: endTurn 不返回，下一步超时

- **解决**: endTurn 前设 `cb->waitTillRealize = false`，发请求不等待服务器确认

### 26b. NK2 卡死根因 — Router battleStart 战斗模型加载失败 (2026-08-16 全面分析)

- 现象: NK2 无论作为 red (采集) 还是 blue (训练/复现), 每局 7-42 pairs 就 stuck; 日志刷屏 [ML-wait] battle=3 q=0 obj=1 mov=1; adventure_wait 90-120s 超时

- 根因链 (3 环):

  1. threadconnector.cpp 481/491: `Scripted(red/blue)` — blue=Nullkiller2 时 battle 模型名 = "Nullkiller2" (NK2 是冒险 AI 非战斗模型名)

  2. Router::battleStart SCRIPTED 分支只认 StupidAI/BattleAI/MMAI_BATTLEAI, 未知名 THROW → catch fallback StupidAI → 战斗仍挂 (battle 无人正确指挥)

  3. **打野 (red 攻中立) 时 neutral 无 playerID → C8.5 fix 用 baggage->modelRight (blue 模型)** → Nullkiller2 → 加载失败; 且 fallback BattleAI 在 headless 无头服务器下等待回调卡死 (MLClient.cpp 400 行注释早有记录)

- [ML-wait] 真相: NK2 的 AIStatus::waitTillFree 等 battle!=NO_BATTLE + queries 空 + 对象访问完 + 移动完 — battle=3 挂着 = NK2 在等战斗结束, 战斗永不结束 → 超时

- 修复 (router.cpp 两处): neutral 无 playerID → 直接 CDynLibHandler::getNewBattleAI("StupidAI") 自动裁决 early return; SCRIPTED else fallback BattleAI → StupidAI (BattleAI headless 卡死勿用)

- 教训: **battle 模型名 ≠ 冒险 AI 名**; neutral 战斗不能复用 blue 模型; BattleAI 无头模式不可用, 自动裁决统一 StupidAI

### 27. SEND→WAIT→READ 顺序防 race

- **现象**: WAIT→SEND 顺序下 _read_state() 读到 action 执行前的旧状态

- **解决**: step() 先 _send_action(action)，再 _adventure_wait() 等下一轮 process_turn，最后 _read_state()。此时 state_update 已在 C++ 侧执行完毕

### 28. 两处 battle hook 防护

- **现象**: 英雄踩怪物时 BattleProcessor::startBattle 抛 "Both hero1 and hero2 are required"

- **根因**: ServerPlugin.cpp 的 startBattleHook 和 endBattleHook 假设两方都是英雄，怪物战 hero2=null 时崩

- **解决**: startBattleHook 加 `if (!(hero1 && hero2)) return;`，endBattleHook 加 `if (!heroDefender) return;`。VCMI autofight 自动裁决战斗

### 29. 非红方 guard（pc!=0 直接 endTurn）

- **现象**: 蓝方也用 MMAI（adventureEnemyAI="MMAI"），yourTurn 进入 while 循环后因不对 Python 交互而永远不结束

- **解决**: AAI::yourTurn 顶部加 `if (pc != 0) { selectionMade + endTurn; return; }`

### 29b. NK2 卡死 6 环修复链 — 6 环全闭环 ✅ (2026-08-16 晚, 死锁链另见 #30)

**卡死根因链 (6 环)**:

1. Router SCRIPTED else THROW → fallback StupidAI (ebba48afd, 第 1 轮)

2. neutral 打野 StupidAI early return + fallback BattleAI→StupidAI (ebba48afd, 第 2 轮)

3. config 缺失 fallback BattleAI→StupidAI (router.cpp:90, 第 3 轮; mmai-settings.json 一直缺失, C8.5 不触发战斗未暴露)

4. battleEnded 服务器侧补调 (AIGateway::battleEnd 同步 battleEnded(); 官方由 NetPacksClient.cpp:897-899 调 BattleEnd 包, 无头服务器无客户端 → NK2 状态卡 ENDING_BATTLE(3) → waitTillFree 死等; 第 4 轮) — 验证 battle=0 ✓

5. dialog 自动应答 (CGameHandler::showBlockingDialog 对 AI 玩家 setReply(0)+popQuery 不发送; NK2 answerQuery 任务拿 CGameState::mutex shared_lock (AIGateway:1403) 与服务器写锁竞争死锁 → query 永不答 → 对象访问卡; 第 5 轮) — 验证 Blocking dialog=0 ✓

6. **守卫战斗收尾卡 (✅ 2026-08-16 闭环)**: 根因 = **IFML 宏漂移** — `onlyOnePlayerHuman || IFML(true,false)` 在 ENABLE_ML 下恒 true → CBattleDialogQuery 永不 pop → MapObjectVisitQuery::onExposure 全链断。修复: `if(onlyOnePlayerHuman)` (BattleResultProcessor.cpp:303)。验证: endBattleConfirm → popIfTop → onExposure → battleFinished winner=0 → removeObject → heroVisit/playerBlocked 清空 → 战斗闭环。

**部署教训 (严重)**: 训练环境是 embedded 模式 (python 进程直接加载 libmlclient.so → vcmiservercommon 静态库), **不是独立 vcmiserver 进程** — 改 server 代码必须重编 libmlclient.so, 只重编 vcmiserver 二进制无效 (运行时不用)。全量 `cmake --build rel -j4` 可对齐; target 名大小写敏感 (Nullkiller2)。

**版本漂移 (系统性隐患)**: 项目源 vcmi/ 与编译树 vcmi-native/ 长期不同步 (queryAs 新 API 只在项目源; BattleProcessor.cpp 整体 cp 覆盖编译失败) — 单文件同步碰巧兼容, 需全面 diff 对齐基准。

**验证证据**: 修复后非战斗场景 steps=8 完整跑局 (无 timeout, (16,15)→(16,16)→(15,17) 多格移动, act 混合 8/4/10/5/1); 守卫战斗场景 100% 复现卡死。ML-wait 打点已加 obj 详情 (对象名)。

**下次开机起点**: QueriesProcessor popIfTop 失败打点 + query 栈内容打印 (守卫战斗 battle query 之上是什么) → 自动答/移除 → 验证守卫战斗收尾链 (onExposure→battleFinished→objectVisitEnded→NK2 obj/mov 清)。

**打点清单 (已部署, 调试用保留)**: AIGateway heroVisit/playerBlocked/battleStart/battleEnd ([ML-obj]/[ML-mov]/[ML-battle]); BattleProcessor::startBattle DONE; VisitQueries.cpp onExposure; CGCreature::battleFinished; CGameHandler::removeObject ([ML-q])。

### 30. EmptyAI 不在 AIS 列表

- **现象**: 设 adventureEnemyAI="EmptyAI" 后启动报 "Unsupported scripted AI name: EmptyAI"

- **解决**: MLClient.h 的 AIS 列表加 "EmptyAI"

### 30b. 战斗后客户端收包静默 + NK2 EndTurn 死循环 — 4 层死锁修复链 (2026-08-16 晚, gdb 实证)

**现象**: 战斗闭环后 red 回合起不来 (PlayerStartsTurn 未达 handlePack) + NK2 EndTurn 死循环刷屏 (acting:0 被拒) → Python adventure_wait 超时 → 整局报废。早期错误诊断: 以为是"客户端收包线程卡死" — 实际是 **CGameState::mutex 死锁 + wtr 状态残留**, 层层剥离 (4 层修复):

**层 1 (gdb 现场 A)**: runNetwork 线程 (持 interfaceMutex) 在 handlePack 等 CGameState::mutex **写锁**, NK2 决策线程持**读锁** (makeTurn gsLock) 等 PackageApplied 确认 (确认需 runNetwork 处理) → 互等死锁。~官方设计~: sendRequest 的 makeUnlockSharedGuard (Client.cpp:407) 等待时解锁读锁 → 理论不死锁, 但 embedded 高频触发 (NK2 决策长 + 广播多)。

**层 2 (修复走弯路, 记录教训)**: 

- gsLock.unlock() 手动解锁 → 与 makeUnlockSharedGuard 构成**双重解锁 UB** (shared_mutex 计数 -1 → 永久损坏, runNetwork 等写锁无持有者) — gdb 现场 B 证实

- scope-lock (endTurn 移出锁作用域) → makeUnlockSharedGuard 解锁**空锁** UB (官方契约 = 调用 sendRequest 必须持读锁) — gdb 现场 C 证实

- **正解**: 恢复官方锁结构 (endTurn 持锁调用, sendRequest 内部解锁/重锁平衡) + turnCounter

**层 3 (turnCounter, AIGateway.h/cpp)**: 旧 makingTurn 线程残留 do-while (确认包迟到), 新回合 startedTurn 重置 haveTurn=true 被旧线程读到 → 死循环刷屏。修复: AIStatus 加 turnCounter (startedTurn 递增), do-while 条件加 `status.getTurnCounter() == myTurn` (回合变更即退出)。验证: r_openK 3 个完整回合正常流转 (此前从未达到)。

**层 4 (MMAI wtr 自锁 + 战斗 AI wtr 残留, 关键)**:

- **MMAI 自锁**: red 的 yourTurn 在 runNetwork 线程执行, a<0 / a==9 路径 cb->endTurn() 用 wtr=true → waitWhileContains 等确认 → 确认需 runNetwork 自己处理 → **自锁死锁**。修复: 这两路径 endTurn 用 wtr=false (AAI.cpp, 与 a==8/0-7 路径一致)。

- **战斗 AI wtr 残留 (最终根因, r_openR 实证)**: BattleAI/StupidAI 的 initBattleInterface (BattleAI.cpp:71-72) 把**共享 cb** 的 waitTillRealize 设 false, 恢复在**析构** (46-51) — embedded 模式战斗界面对象长期存活 (battleints 残留) → **析构不触发 → wtr=false 残留** → NK2 下个回合 endTurn wtr=0 → do-while 不等确认立即重发 → livelock 刷屏 (138857 次 wtr=0 EndTurn)。修复: AIGateway::endTurn 显式 `cc->waitTillRealize = true;` (不依赖战斗 AI 恢复)。

**验证证据**: 修复后 3/3 局完整跑通 (r_openU/V/W: steps=10, acts 各 10 个, err=None, 0 次 EndTurn 拒绝, 日志 7-10K 行); 清理打点后冒烟 1/1 (r_openX, 日志 2499 行)。

**gdb 抓死锁流程 (可复用)**: 复现卡死 → `ps aux | grep ep_runner_one | grep -v timeout | awk '{print $2}'` 取 PID → `wsl -u root gdb -p PID -batch -ex 'set pagination off' -ex 'thread apply all bt 12'` → 找 runNetwork (handlePack 等锁) / NK2 线程 (sendRequest/waitWhileContains/序列化) / runServer (epoll 空闲=不持锁) → 判锁持有者。注意: gdb attach 后 WSL 可能卡死 (ptrace 冻结), 抓完立即 detach (batch 模式自动); 连续 attach 多次后 WSL 服务可能崩 (0x8007274c), 用 wsl --shutdown 恢复。

**打点清理教训**: 正则删 fprintf 时多行 fprintf 的参数残留行会留下 (AIGateway.cpp:384 / TurnOrderProcessor.cpp:344 编译错误 'expected ; before )') — 清理后必须全量编译验证, 不能只信删除计数。

### 31. canMoveBetween 不足够精确

- **现象**: cb->canMoveBetween(hero->pos, target) 返回 true 但服务器仍拒绝 moveHero

- **根因**: canMoveBetween 只做地形层面检查，服务器有额外游戏规则检查（visitable objects 等）

### 31b. NK2 英雄交换查询死锁 — q=1 obj=1 mov=1 永久卡死 (2026-08-17)

- **现象**: BC 采集长跑 (max_pairs>=1000) 英雄位置不变 (唯一值=2), 动作分布 90% 单一方向 (缓存假动作), 日志 [ML-wait] battle=0 q=1 obj=1 mov=1 永久 (2s/次贯穿整局, qdesc=Exchange between heroes)

- **根因链**: NK2 收到 showGarrisonDialog (英雄交换) → heroExchangeStarted 异步任务 (AIGateway.cpp:1419 executeActionAsync) 持 CGameState 共享锁 → pickBestCreatures/answerQuery 与服务器写锁竞争 → **死锁** (showBlockingDialog 已有同款 ML fix CGameHandler.cpp:1164, showGarrisonDialog 漏加) → QueryReply 永不发 → Exchange 查询永不关闭 → AIStatus remainingQueries=1 永久 → waitTillFree 卡死 → NK2 决策线程死 → 英雄不动

- **次根因**: CGarrisonDialogQuery 同阵营两英雄 addPlayer 两次无去重 → players={RED,RED} → addQuery 双重 push → popQuery FAIL 796 次 (查询栈污染)

- **修复**: 1) CQuery::addPlayer 加 vstd::contains 去重 (WSL 编译树旧版缺, D 盘已有) 2) showGarrisonDialog AI 玩家自动应答 (setReply(0)+popQuery, 同 showBlockingDialog 模式, 仅无头服务器模式)

- **验证**: All for One 图红方英雄 15-17 位置真实移动 (16,12→4,6), 动作 10 种 8 方向, 升级/移动力消耗正常; ML-wait 永久卡 120+→短暂等待; popQuery FAIL 796→0

- **后续修复 (同日)**: 战斗查询残留 (has to answer 刷屏 8867-18202 次/局) → ① expGiven 升级 AI 自动选技能 ② QueriesProcessor::removeQuery 任意位置强制移除 (onRemoval 只调一次防段错误 + 移除后触发暴露链否则 visitQuery 永不 onExposure) ③ battleResultAccepted 改用 removeQuery; env.close() embedded 卡死 (58% CPU, close 线程 5s 超时实测无效) → SAVED 后直接 os._exit 跳过, 局间 1 行间隔

- **地图坑**: Dungeon Keeper.h3m 红方 954 出生地被围 (passable 8 方向全 0, isClear=false), 卡死修复后仍动不了 → 换 All for One.h3m

- **诊断教训**: obs 大数值字段有 log1p 归一化 (H.8: movement 1560→log1p=7.353, gold→8.61), 排查 float 异常先查 obs 构建归一化段; 探针 (临时打印 state.heroes[0].movement type) 直接区分 int 结构 vs float 垃圾

### 32. 有头 GUI (embedded 非 headless) 与标准 client-server 的地图加载链 (2026-08-17)

**场景**: 战略层模型要"有头"跑局 (VCMI 窗口显示对局)。embedded 模式 headless 硬编码 true;

标准 client-server (vcmiclient) 编译 + 启动流程踩坑链。

**坑 32.1 embedded headless 硬编码**: connectors/v13/threadconnector.cpp InitArgs 构造 `true // headless`

→ 改环境变量 `STRATEGIC_HEADLESS=0` 启用 GUI (默认 true 训练/采集零影响)。connector 重编:

`cd vcmi_gym/connectors/rel && cmake --build . --target connector_v13 -j 8`

(注意: `cmake --build .` 全量会因 exporter.cpp GA::BATTLE_SIDE 旧代码失败, 只编 connector_v13 target)

**坑 32.2 GYM symlink 地图扫描递归**: data/Maps/GYM 是 symlink → vcmi-workspace/maps/gym (vmap 训练图)。

GUI 客户端初始化扫描 MAPS/ 资源 (getFilteredFiles) 跟随 symlink 递归扫 vmap → 虚拟地图名前缀叠加

(MAPS/MAPS/MAPS/.../GYM/ML-MINI) → "Failed to resolve identifier ml:hero_0" 刷屏 → 段错误 (exit 139)。

headless 不扫描 (直接加载指定地图) 所以无头正常。修复: 移除 data/Maps/GYM symlink + 移走 data/Maps 顶层 *.vmap

(s1.vmap 会被大厅当默认地图加载 → 解析失败段错误)。

**坑 32.3 地图名大写化**: VCMI 资源系统把请求资源名转大写 (HoMM3 约定) → Linux 大小写敏感文件系统找不到

"ALL FOR ONE"。--testmap 必须带 "Maps/" 前缀: `--testmap "Maps/All for One.h3m"`

(纯文件名 "All for One.h3m" 会崩在 CMapInfo::mapInit "Resource ALL FOR ONE wasn't found"; 绝对路径也被转大写失败)。

**坑 32.4 debugStartTest 死循环 setMapInfo**: `while(!mi || mapInfo->fileURI != mi->fileURI)` —

mapInit 用小写原名 (Maps/All for One.h3m) vs 服务器回显 mi->fileURI 大写 (MAPS/ALL FOR ONE) → 死循环刷

LobbySetMap (639 次/10min)。修复①: boost::iequals 大小写不敏感比较; 修复② (关键): 服务器广播链路 mi 仍不更新

(mi=NULL 死循环) → 加 10s 超时兜底继续流程 (setPlayer + sendStartGame) → 流程推进到 bonus 界面构建。

**坑 32.5 g_adventure_allied_ai 未定义**: MLClient.cpp 定义 (libmlclient.so) 但 vcmiclient 不链接 ML →

链接错误。修复: Client.cpp 改 weak 定义 (`extern "C" __attribute__((weak)) char g_adventure_allied_ai[64]=""`),

ML 强定义优先, 客户端默认空走 settings。

**坑 32.6 pkill -f 自杀**: `pkill -f vcmiclient` 在命令行含 vcmiclient 字符串时匹配自身 (exit 15, 后续命令不执行)。

先 pkill 再单独跑测试命令, 或 pkill 模式用 "bin/vcmiclient" 避开。

**坑 32.7 embedded GUI 分支不稳**: STRATEGIC_HEADLESS=0 (embedded 非 headless) 多次段错误

(地图扫描递归 → 修复后 start_vcmi 后立即崩 debugStartTest 地图加载层, 无日志)。embedded+GUI 组合坑多,

标准 client-server (vcmiclient 独立) 是正路 (vcmiserver 标准 AI + 模型 AI 封装 = 部署路线预演)。

**验证状态**: vcmiclient 编译成功; --testmap --onlyAI 流程推进到 bonus 界面构建 (NK2 vs MMAI 无模型);

模型 AI 封装 (Phase 2) 未开始。libtorch 可用 (venv torch/lib/libtorch_cpu.so — C++ 推理路径确认)。

### 33. VCMI 内部重定向 stdout/stderr

- **现象**: 即使子进程 stdout 指向日志文件，MMAI 的 fprintf 仍不出现

- **根因**: VCMI 启动后 CBasicLogConfigurator 可能重定向 fd 1/2

- **解决**: 用 fopen("/tmp/mmai_diag.txt", "a") 直接写文件，完全绕过 VCMI 日志层

### 33b. TerrainTile::blocked() 是函数不是成员变量

- **现象**: `tile.blocked` 编译报错 `cannot convert from type bool () const to type bool`

- **解决**: 使用 `tile.blocked()` 加上括号调用

### 34. TerrainTile::terType 不存在

- **现象**: `tile.terType != 5` 编译报错 `no member named terType`

- **解决**: 使用 `tile.getTerrain()->isWater()` 判断是否为水域

### 34b. 有头验证 08-18: WSLg 虚拟显卡无 GPU 合成 (显示无解) / 官方 Windows NK2 0x618 崩溃 / spectate 官方也崩 (2026-08-18)

- **WSLg 显示**: 本机无真实 GPU (仅 OrayIddDriver 向日葵 + MuMu 虚拟显卡) → WSLg 窗口 (X11 + wayland/SDL_VIDEODRIVER 都试) 任务栏有图标桌面无画面; EGL/MESA/ZINK 失败 + [WARN:COPY MODE]; **环境无解** → 有头验证走 Windows 原生 VCMI

- **官方 Windows VCMI (1.6/1.7.5) NK2 0x618 空指针**: All for One/Arrogance 都崩 (回合 1 NK2 初始化后, "Attempt to read from 0x618"); 我们 fork 1.8 的 NK2 修复链已修 (WSL 4 方跑到回合 4) → Windows 需源码构建 fork

- **spectate 官方也崩**: 官方 1.7.5 Linux AppImage 在 "Initializing the interface for player invalid" SIGSEGV — 官方渲染链脆弱, spectate 弃用; 玩家视角 (VCMI_TESTMAP_ONLYAI=0) 是部署形态

- **github.com 443 间歇不通** → ghproxy.net 镜像下载成功

- **AppImage**: WSL 无 FUSE → --appimage-extract 解压运行

- **~/.local/share/vcmi/Maps 的 .vmap** 使官方 VCMI 扫描卡死 (s1.vmap 解析) → 移走

- **Windows VCMI 地图源**: Documents\My Games\vcmi\Maps (158 张); 安装: D:\Program Files\VCMI (1.6) / D:\GAMES\VCMI (1.7.5 用户自装)

- **Windows 侧控制 WSLg 窗口**: user32 ShowWindow/SetWindowPos (win_force_maximize_vcmi.py); 窗口可能被移到屏幕外 (-21333)

### 36. passability mask 全堵时应回退 END_TURN 而非抛异常

- **现象**: Categorical(logits=-inf) 抛 "invalid probability distribution"

- **解决**: 采样前加 `if passable.any():` 判断，全堵直接 `a = 10`

### 41. strategic_state_update 从未被调用

- **现象**: passability 全部堵死，obs 全零，模型无有效训练数据

- **根因**: `strategic_state_update()` 定义了、编译了，但没任何代码调用它

- **解决**: 在 `AAI::yourTurn()` 中通过 dlsym 调用 `strategic_state_update`，传入 CGameState 指针

  ```

  static auto st_update = reinterpret_cast<void(*)(void*)>(dlsym(RTLD_DEFAULT, "strategic_state_update"));

  st_update(&cb->gameState());

  ```

### 42. strategic_state.h ABI 不匹配（Windows vs WSL）

- **现象**: Python ctypes 读到的 passable 数据错位，struct 字段偏移不一致

- **根因**: Windows 版 `strategic_state.h` 缺 `action` 字段，C++ struct 比 Python struct 多 4 字节

  - WSL C++: `game_over(4) | action(4) | _version(4) | passable(8*4=32)`

  - Windows Python: `game_over(4) | _version(4) | passable(8*4=32)`

  - passable 在 Python 侧整体偏移 4 字节，第 8 个方向读越界

- **解决**: 两边同步——C++ 加 `int32_t action;`，Python ctypes 加 `("action", ctypes.c_int32)`

### 45. CCallback::gameState() 在 yourTurn 回调时返回空 CGameState

- **现象**: `strategic_state_update(&igic->gameState())` 在所有字段上产生 0

- **根因**: VCMI 客服端 CGameState 在 `yourTurn()` 时尚未与服务端同步（通过 `gamestate` shared_ptr 访问到的状态是空的）

- **尝试的方案**:

  - 通过 dlsym 调 `strategic_state_update` → 空

  - 从 `cb->getHeroesInfo()` 直填 → 空

  - 等 `moveHero/endTurn` 后再调 `strategic_state_update` → 还是空

- **结论**: 尚未找到能读到真实游戏数据的方法。可能需要在 VCMI 启动完成后多等几轮

### 46. g_strategic_state->action 不被 adventure_send_action 更新

- **现象**: C++ 读 `g_strategic_state->action` 永远是 memset 后的 0

- **根因**: Python 的 `_send_action` 写的是 `g_rl_action` 全局变量 + `adventure_send_action`(原子变量 `s_turn_action`)，不是 struct 字段

- **解决**: 改为读 `adventure_get_action()`（从 `s_turn_action` 原子变量读）

### 48. selectionMade 在 moveHero 前导致服务器拒绝+segfault

- **现象**: moveHero 失败后 segfault，passability mask 无效（全 1），模型选非法方向

- **根因链**:

  1. `AAI::yourTurn` 顺序为 `selectionMade→moveHero→endTurn`

  2. `selectionMade` 回答 query 后，服务器认为玩家已非活跃

  3. `moveHero` 被服务器拒绝（"Player not allowed"）

  4. 第 48 行 `passable[d]=1` 暴力覆盖完全废掉 mask，模型无有效阻塞信息

  5. CGameState 在 yourTurn 时为空（#45），strategic_state_update 填充零

  6. 模型反复选非法方向 + 服务器拒绝 + 状态不一致 → segfault

- **修复**:

  1. 调换顺序：`moveHero→selectionMade→endTurn`（#24 确认 WSL2 不再 segfault）

  2. 移除 `passable[d]=1` 暴力替身，改为 `cb->canMoveBetween(hpos, target)` 计算

  3. fallback 路径也从 `g_rl_action` 改为 `adventure_get_action()`（与 callback 路径一致）

  4. CGameState 访问加 try/catch，失败时走 cb 路径的 passability

- **涉及文件**: `vcmi/AI/MMAI/AAI/AAI.cpp`

- **部署**: libMMAI.so 重编部署到 vcmi-native/rel/bin/AI/

- **状态**: ✅ 已部署，训练重启中

---

### 49. strategic_state_update / fill_state_from_cb 都无法填充数据（#45 持续）

- **现象**: obs_nz=0 持续，`fill_state_from_cb` 中 fprintf(stdout) 不输出（函数从未被执行）

- **根因**（2026-07-28 更新诊断）:

  - `fill_state_from_cb` 的 stdout fprintf 完全没出现在训练日志中 → **函数没被调用**

  - 无论是 callback 路径(`if (g_adventure_cb)`)还是 fallback 路径，都不进入 fill_state_from_cb

  - 初步判断: 训练进程启动时加载了旧的 libMMAI.so（多次 kill/restart 后仍有残留进程加载旧 .so）

  - 即便 .so 已更新，运行中的 VCMI 进程持有旧文件句柄

- **之前尝试的方案**（全部失败）:

  - 用 `igic->gameState()` 读 → 空（CGameState 未同步）

  - 从 `cb->getHeroesInfo()` 直填 → 空（getHeroesInfo 也读的同一个 CGameState!）

  - 从 `cb->getGameStatePtr().getMap().objects` 迭代找英雄 → 编译成功但 `fill_state_from_cb` 从未被执行

  - 等 moveHero/endTurn 后再读 → 还是空

- **关键发现**:

  - `cb->getHeroesInfo()` 的实现: `gameState().getPlayerState(*getPlayerID())->getHeroes()` — **跟 igic->gameState() 走的是同一个 CGameState!** 不是不同路径

  - moveHero 能成功是因为它发送网络包到服务器，不读取客户端 CGameState

  - `memset(g_strategic_state->passable, 1, 32)` 错误: 设的是每字节=1，int32_t 值=0x01010101=16843009，作为 NN 输入会完全支配激活值

- **当前状态**: 未解决。`fill_state_from_cb` 的调用路径需要进一步追查

---

### 50. installNewBattleInterface 中性玩家 crash

- **现象**: env.reset() 在 "Initializing the battle interface for player neutral" 后 segfault

- **根因**: 

  - 不是 installNewBattleInterface 函数本身的 bug（加 fprintf 确认四色全部通过）

  - 是 VCMI 重建后自然消失的时序/ABI 问题

  - 新版 libmlclient.so（今日构建）仍有 crash，旧版（Jul 28 备份）+ 新版 MMAI 正常

- **修复**: 重建 vcmiserver + libmlclient.so + libMMAI.so 后消失

- **验证方法**: 在 `CClient::installNewBattleInterface()` 加 fprintf 日志确认 neutral 玩家 initBattleInterface 返回 OK

- **当前稳定工作组合**:

  - `libmlclient.so` = `bak.20260728`

  - `libMMAI.so` = 最新构建（含 `__attribute__((used))` 构造器导出）

  - `vcmiserver` = 最新重建

  - `libmlserverplugin.so` = 最新重建（含 hero pool pop_back）

  - `connector_v13.so` = 现有（712KB, Jul 29 03:03）

- **注意**: 新版 libmlclient.so 编译通过且含 try-catch + before/after 日志，但在 `initBattleInterface` 处 crash，原因待查

### 52. MMAI callback throw 导致进程 abort

- **现象**: 游戏启动后 crase 为 RuntimeError，非 segfault

- **根因**: MMAI `AAI` 类的 `heroGotLevel`、`showBlockingDialog`、`showGarrisonDialog`、`showTeleportDialog`、`showMapObjectSelectDialog`、`commanderGotLevel` 等回调直接 `throw std::runtime_error("not implemented by AAI")`

- **解决**: 改为 `cb->selectionMade(0, queryID)` 自动应答 + null check

- **涉及文件**: `/home/administrator/vcmi-native-build/AI/MMAI/AAI/AAI.cpp`

### 53. Hero pool even number 检查 kill 游戏

- **现象**: `random_heroes=N` 时 "An even number of heroes is required in each hero pool"

- **根因**: `ServerPlugin::ServerPlugin()` 中遍历 heropools，要求每个 pool 英雄数为偶数

- **解决**: 改为 `pool.heroes.pop_back()` + fprintf 通知，不 throw

- **涉及文件**: `/home/administrator/vcmi-native-build/server/ML/ServerPlugin.cpp`

### 54. ServerPlugin artifact loop 空 hero 指针

- **现象**: 偶现 segfault 在 artifact 赋值循环

- **修复**: 加 `if (!h) continue` 空指针检查

- **涉及文件**: `/home/administrator/vcmi-native-build/server/ML/ServerPlugin.cpp`

### 56. Post-init segfault — Discord null reference ✅ 已修复（2026-07-29）

- **现象**: env.reset() 在 installNewBattleInterface 全部完成后 segfault

- **输出特征**: installNewBattleInterface 四色全部 EXIT OK 后立刻崩，无 MMAI callback 触发

- **根因**: `GameEngine(headless=true)` 不调 `init()` → `discordInstance` 是 nullptr → `ENGINE->discord()` 返回 null reference → `CServerHandler::startGameplay()` 调用 `discord.setPlayingStatus(this=0x0)` 崩

- **修复**:

  1. `GameEngine.h` 加 `bool hasDiscord() const { return discordInstance != nullptr; }`

  2. `CServerHandler.cpp` 调用前检查 `if (ENGINE->hasDiscord())`

- **涉及文件**: `client/GameEngine.h`, `client/CServerHandler.cpp`

- **状态**: ✅ 已修复。gdb backtrace 确认

### 57. 信号量通信修复 — AAI::yourTurn 阻塞等 Python action ✅ 已修复（2026-07-29）

- **现象**: `adventure_wait_for_turn()` 无限等待 → obs_nz=0

- **根因**: `register_adventure_delegate` 空实现，`AAI::yourTurn` 不设原子变量 `s_turn_player`

- **修复**: `AAI::yourTurn` 调 `adventure_process_turn()` 阻塞等 Python action

- **涉及文件**: `AI/MMAI/AAI/AAI.cpp`

---

### 58. VCMIGYM_DEBUG=1 导致 importerror

- **现象**:  报 

- **根因**:  导入 v14，v14 的 pyconnector 在  时从  导入 exporter_v14，但 build/ 目录只有 connector .so 没有 exporter .so

- **解决**: 不要设 ，默认从  导入（有完整 exporter_v13/14/15.so）

- **涉及文件**: 

### 59. getHeroesInfo() 在 selectionMade 前返回空

- **现象**:  内  返回空（size=0）

- **根因**: 部署版  结构： 同步调用（selectionMade 前）→ async task 中  后才可访问英雄

- **影响**: StrategicState 全零（obs_nz=8 仅 passability），英雄/资源/日期数据缺失

- **候选方案**:

  1. 改用  的  — 可能绕过 query 限制，且是 public 接口

  2. 加全局 CGameState* 指针，async task 中设置

  3. 在 async task（selectionMade 后）调用 strategic_state_update

### 60. g_ml_player_cb — 全局 CCallback 指针传参

- **现象**:  收到  即使  传了 

- **根因**: 部署版 MMAI AAIs 的  成员在  时可能为空（shared_ptr 未初始化或已移动）

- **解决**: 在  定义 ， 中先  再调 

-  中  双保险

- **涉及文件**: , 

### 61. CGameInfoCallback 比 getHeroesInfo 更可靠

- **现象**:  在  前返回空

- **根因**:  在 query 未回答时返回空列表

- **解决方案**: 用  的  替代，这些 public 方法绕过 query 限制，直接从 game state 读取

- **可用 public 方法**: , , 

- **局限性**: ,  在部署版不可用或 protected

### 62. VCMI stdout 重定向吞掉 Python print

- **现象**: Python  输出在 timeout: failed to run command ‘python’: No such file or directory 中不显示

- **根因**: VCMI 的  +  可能重定向 fd 1

- **诊断方法**: 重定向到文件  后检查文件内容

- **已知影响**: 临时文件路径下跑测试 stdout 不可见；直接 WSL 终端下正常

### 63. adventure_process_turn 缺日历/地图填充

- **现象**: `StrategicState.day/week/month/map_width/map_height/has_underground` 全0

- **根因**: `adventure_process_turn()` 只填 player/hero/passability/game_over，没写日历和地图字段。`strategic_state_update()`（dlsym 路径）有填，但 connector 路径不走那个函数。

- **影响**: 训练缺时间感知；地图尺寸缺失导致 passability 方向验越界不完整

- **修复**: 在 `adventure_process_turn()` 加：

  1. `gicb->gameState().day` → day/week/month（不用 `getCalendar()`，部署版没有）

  2. `gicb->getMapSize()` → map_width/map_height/has_underground

- **注意事项**: 改的是 `vcmi/ML/strategic_state.cpp`，须同步到 WSL2 所有副本（`hero3_vcmi`/`vcmi-native`/`vcmi-native-build`/`vcmi-build-latest`）

### 67. fork 战斗链从未可用 — 任意战斗触发即崩 0x98, 双根因 (2026-08-18 晚, gdb 实证)

- 现象: 第一次战斗 (BattleSetActiveStack applied) 后 "Attempt to read from 0x98" Disaster。此前 6 AI 测试 580+ 回合

  0 崩是假象 — NK2 在 A Viking 图上没相遇任何人, 战斗链从未被触发过。ModelAI 走进守卫区才暴露。

- gdb 栈: Thread 7 SIGSEGV → CClient::startPlayerBattleAction (client/Client.cpp) → handlePack → NetworkHandler。

- 根因 ①: 原代码一行内 `gameState().getBattle(battleID)->battleGetStackByID(gameState().getBattle(battleID)->activeStack, false)`

  **getBattle 调两次** — AI 线程在两次调用间解锁 interfaceMutex, 第二次返回 null → 0x98。

  修复: 单次 `auto * battle = gameState().getBattle(battleID);` + 判空 (BTL-DBG 防御打印)。

- 根因 ② (修完①仍崩): `vstd::makeUnlockGuard(ENGINE->interfaceMutex)` — **headless 下 ENGINE 是 null**

  (P22 规则: headless = ENGINE null, 所有 ENGINE-> 必须判空), mutex guard 构造即解引用 null+0x98。

  修复: `if (ENGINE)` 包住 unlock guard, else 直接 activeStack。

- 验证: A Viking 5 场战斗 0 崩 (forktest52/55 + hermes-verify)。commit 5078fe762 (fork) + 09b6efd (submodule)。

### 72. ModelAI 战斗后回合挂死 — yourTurn 线性执行 (2026-08-19, fork+1.7.5 双验证)

- 现象: 模型移动触发战斗, 战斗打完但该 AI 回合永久挂起 ("Player X has to answer queries" 后无活动)

- 根因链: yourTurn 线性 (moveHero 异步 → sleep 300ms → endTurn); 战斗触发时 endTurn 被拒 (CBattleQuery 挂着) → yourTurn 返回 → 战斗结束查询清空 → 引擎不重调 yourTurn → 挂死

- 线程模型 (关键): activeStack/battleEnded/heroMoved 在 runNetwork 线程 (Client.cpp startPlayerBattleAction 直接调), yourTurn 在 AI 线程 — AI 线程阻塞等待 (cv/mutex 观察窗口) 必失败 (战斗事件在别的线程处理, fork Windows 战斗初始化可能 >15s)

- heroMoved 陷阱: 移动完成即回调 (在战斗 pack 之前) — 立即 endTurn 会被战斗查询拒绝

- 修复 (P46, commit 537e3ae): 事件驱动 — yourTurn 移动后返回不等待; heroMoved 启动 detach 延迟线程 (2s 等战斗初始化 + 轮询 atomic battle_active 最多 30s + endTurn); activeStack 置位 / battleEnded 复位; 无战斗回合代价 +2s

- 验证: fork61 (2战0拒0崩, 战后 gives turn 继续) + 1.7.5 GUI 5AI 维京风暴 (7战0拒0崩145轮转)

- 计数口径: grep BattleEnded 全文含 apply 行虚高 (每场 3-4 行) — 真实场数看 "Received CPack of type struct BattleEnded" (每场 1 次)

### 90. VCMI 生物标识符: footman 不存在, 是 swordsman

- castle.json 生物: pikeman/halberdier/archer/marksman/griffin/royalGriffin/swordsman/crusader/...

- 地图 monster 对象或 hero army 写 core:footman → "Failed to resolve identifier core:footman"

- **修**: core:swordsman

### 95. 杀训练 worker 认准 python3 PID, bash 包装不是 worker

- `ps aux | grep "[t]train_wsl2_ppo_v2.py"` 会同时匹配 bash 包装 (RSS ~3MB) 和 python worker

- kill bash 包装 → python 孤儿也退, state 可能没保存 (22:08 事件: 杀 362 bash, state 停在旧时间戳)

- 正确: `ps aux | grep "[t]rain_wsl2_ppo_v2.py" | grep python3 | awk '{print $2}'` 再 kill

- 重启训练命令见 WSL知识库.md "训练进程启动方式 (2026-08-23 变更)"

### 97. Level 3 经济动作引导失败 → 模型毒化 (2026-08-24)

- 16-21 (RECRUIT/BUILD) 采样强制 → noTarget 惩罚 → END_TURN 刷步 → klc 触顶 → 策略锁死

- 处理: poisoned checkpoint 存档 + ep_runner_one.py logits[16:24]=-inf 屏蔽回滚; 等 reward 解决 noTarget 再试

### 98. L1/L2 checkpoint 丢失 (2026-08-24)

- L3 失败回滚 BC 时, Level 1/2 学习全部丢失 — 晋级/切图前必须备份模型

- 修复: backup_on_promotion() 按 .maps_fingerprint 检测 MAPS 变更自动备份

### 99. entropy=-0.01 正r率 15%, -0.05 → 27% (2026-08-24)

- 熵惩罚过低策略收敛太快探索不足; -0.05 在 Level 2 表现最好

### 102. 守卫被访问消失无战斗 = takenAction 评估 JOIN/FLEE (2026-08-26)
- 现象: 英雄进入守卫格, 守卫消失 (passable 全 1), 无 battle_result 无战斗奖励; NK2 采集同格战斗正常
- 根因: CGCreature::onHeroVisit → takenAction: relStrength = 英雄战力/守卫战力 → random_armies 3000-5000 使英雄远强于 peasant 守卫 → charisma >> agression → 守卫 JOIN/FLEE (消失) 而非 FIGHT; NK2 采集无 random_armies → FIGHT
- 处理: 关闭 random_armies (恢复地图初始军队) + 守卫清除检测 (进守卫格 → +100) 作为战斗等价信号
- 教训: "守卫战斗不触发"先查守卫行为评估 (战力对比/agression), 不是只查路径/访问链; random_armies 会改变守卫对英雄的战力评估

### 103. 守卫格 passable=0 → 模型绕开守卫 (2026-08-26)
- 现象: 训练 40+ 局英雄从不走向守卫; 守卫格 isClear=false 被 passability 通道标 blocked
- 根因: 守卫格可进入 (模板无 blocked 格) 但 isClear=false → passable[d]=0 → 模型/MOVE_TO 按 passable 选方向永远绕开; NK2 不走 passable 自有寻路 → 直接走到守卫格
- 处理: MOVE_TO 守卫目标跳过 passable 检查 + 守卫格一步可达优先
- 教训: passability 通道对"可战斗格"是误导信号; 战斗/守卫目标不能依赖 passable

### 104. 先占矿守卫消失 → 战斗永不触发 (2026-08-26)
- 现象: 守卫目标贪心路径途经矿 → 先占矿 → 守卫消失 (守矿机制)
- 根因: VCMI 守矿机制 — 矿被占后守卫清除; 英雄先占矿守卫即消失, 战斗永远不发生
- 处理: 守卫恒优先于矿 (15 格内有守卫一律先打守卫) + 守卫一步可达优先 (避免途经矿/资源)
- 教训: 守矿/守资源机制 — 目标优先级必须"守卫 > 矿", 否则战斗目标被矿截胡

### 105. C++ 重编环境崩 (纯 8-23 源码重编也 core dump, 未解) (2026-08-26)
- 现象: strategic_state.cpp/.h 改守卫目标后 make mlclient → VCMI 启动崩 (timeout: dumped core); gdb 崩在 shutdown_vcmi (GAME null); start_vcmi 从未被调; init_vcmi 正常 (VCMI 日志到 mod 加载)
- 根因: 未定位 — 两 .so ABI 布局一致 (gdb ptype), 纯 8-23 源码重编也崩; 编译环境问题与改动无关 (候选: MLClient.cpp 工作区 610 行 vs committed 689 行? 编译 flags?); 已回退工作 .so (backup-t03-target-20260825_233554, md5 5d2b9e9d)
- 处理: 回退 + 全 Python 侧修复; C++ 侧改动 (local_tiles 类型通道/守卫战力通道) 待编译环境修复
- 教训: 编译环境崩 (与改动无关) 时不要死磕, 回退 + Python 侧等价实现优先

### 106. local_tiles[1] 填实例 ID 非类型 + 守卫战力通道边界噪声 (2026-08-26)
- 现象: obs 物体类型通道恒 1 (守卫/矿/资源类型不可见); 守卫战力通道 (local_tiles[2]) 地图边缘整行 =1
- 根因: C++ fill local_tiles[1] 用 top->ID.getNum() (实例 ID 恒 1) 非 MapObjectID 类型; 战力通道无出界检查 (边界格 guardingCreatures 返回全守卫)
- 处理: Python get_guards() 读 vmap 补偿 (守卫坐标直接来自地图文件); C++ 修复待编译环境
- 教训: obs 通道不可信时先验证 C++ 填充语义 (实例 ID vs 类型), 用 vmap 源数据补偿

### 107. 守卫清除检测 = 战斗机制的 Python 等价 (2026-08-26)
- 现象: MMAI 环境守卫被访问即消失 (无战斗); 战斗奖励 (battle_result +100) 永远拿不到
- 根因: 守卫评估 JOIN/FLEE 消失, 无 battle_result 帧
- 处理: ep_runner 检测英雄进入守卫格 (pos == 守卫坐标) → 守卫清除 → +100 首胜奖励 (每局一次); 训练验证正奖励率 83%
- 教训: 环境机制缺失 (真战斗) 可用确定性等价事件替代 — 进守卫格 = 守卫被清除 = 战斗的等价结果; 先打通学习信号, 真战斗待编译环境修复

### 111. MMAI yourTurn 轮询阻塞事件循环 → 战斗回调死锁 (2026-08-27)
- 现象: battleStart/battleEnd 回调永不触发 (in_battle 标志不更新), 提前 endTurn 被 CBattleQuery 拒
- 根因: yourTurn 在 runNetwork 线程, 轮询 sleep 阻塞事件循环 → 同线程回调无法处理
- 处理: 轮询缩短 0.3s + 回合挂起 (pending_endturn) + battleEnd 回调收尾 (async 0.5s) + 兜底 CAS
- 教训: 同线程阻塞与回调互斥 — 轮询等待"回调设置的标志"无效 (回调被阻塞)

### 112. garrison dialog AI 应答后查询栈卡 (2026-08-27)
- 现象: 战斗后守卫残余 (autofight 未全灭) → 英雄访问 → showGarrisonDialog → AI 答 0/1 都卡
- 根因: 残余对象未移除 (AI 不合并), 访问流程未完成, 查询栈残留
- 处理: CGameHandler::showGarrisonDialog AI vs AI 自动合并残余 (moveStack) + removeAfterVisit, 不建 dialog
- 教训: AI 环境的交互对话框应服务器侧跳过 (AI 无法正确应答); 与 blocking dialog 自动答同模式

### 113. make POST_BUILD 生成坏 data 符号链接 → EEXIST (2026-08-27)
- 现象: make mlclient 后训练启动报 boost::filesystem create_directories: File exists "./data"
- 根因: POST_BUILD ln -sf 生成 rel/bin/data → vcmi-native-build/../data (错误路径, 不存在)
- 处理: rm -f rel/bin/data && ln -s /home/administrator/vcmi-native-build/data rel/bin/data (绝对路径)
- 教训: 每次 make mlclient 后必须重修 data 链接; 用绝对路径 (相对路径解析错)

### 115. QueryID=-1 断言雷 (AAI.cpp) 引爆训练空转 (2026-08-29, 45+ 局 ep_steps=1)
- 现象: 02:48 续训后 100% 局数 ep_steps=1, r=恒 1.7, act=[3] (MOVE_TO 直冲守卫开战), 无 [ZOMBIE] 标记; ep_runner 明细日志见 `AAI.cpp: QueryID is -1, but we are ATTACKER` 断言 + 调用栈 (libMMAI.so ← callOnlyThatBattleInterface ← visitBattleResult)
- 根因链: ① 08-27 深夜做 queryID=-1 守卫实验 (构建树产出 libmlclient=77967cde + libMMAI=13c0f041; 实验版 libmlclient 会导致全动作被拒/EndTurn 不允许 — 从未同步到运行时, 但 libMMAI 13c0f041 自带守卫); ② 08-29 插桩诊断时诊断版覆盖运行时 .so, "恢复"回 08-23 版对 (5d2b9e9d+b20199c1, 与 ep386 时代一致); ③ 该版 libMMAI 无 queryID 守卫 = 既有随机雷; ④ 续训后模型 (step=194848 权重) MOVE_TO 一步直冲守卫走 MapObjectVisitQuery 开战 → 攻方 battleEnd queryID=-1 → ASSERT 崩引擎 → env 第 1 步 done。真正的雷 = 断言本身, 版本考古是弯路 (start_vcmi 未调→GAME null 假设也不成立)
- 为何 ep1-71 没炸: 旧段模型开战路径 queryID 正常; 续训权重行为变化直冲守卫, 精确踩中 queryID=-1 路径 (推断, 未逐步复现)
- 修复: libmlclient 保持 5d2b9e9d (移动正常), libMMAI 单独换构建树 13c0f041 (08-27 单文件重编产物, 内含 `if(queryID.getNum() != -1)` 守卫 + battleEnd 补 endTurn); 只动 AAI.cpp 不碰 .h (避开 08-26 strategic_state.h 连带重编坑)
- 验证: 冒烟 (训练同款参数+MOVE_TO 强制) 2 场战斗 winner=0、0 断言、引擎存活; 续训 ep 156/200 步满局 r=43/19.75 ✅
- 教训: ① 恢复 .so 必须用 md5 对照"实际跑过验证期"的那对, 不能凭 mtime/目录名猜版本 (backup-mlclient-brp-0827 里的 5d2b9e9d 是修复前快照不是好版本); ② 构建树 rel/bin 可能是未验证的实验构建, 整对部署前先单独核对 libmlclient 可用性; ③ 诊断备份要用独立文件名, 别让诊断版覆盖备份; ④ 冒烟必须带训练同款 env (LD_LIBRARY_PATH/STRATEGIC_STATE_LIB/裸地图名/MOVE_TO 强制), 否则动作全被拒造成假象

### 133. VCMI 1.8 getUpperArmy() 不含 visiting hero: 与 HoMM3 直觉相反 (2026-09-02)
- **现象**: CGTownInstance.cpp L879-884 `if(getGarrisonHero()) return getGarrisonHero(); return this;` — 只返回 garrisonHero 或 town 本身; 英雄 visit 后 dst 仍非英雄 (实测 visit=1 但 dstIsHero=0)
- **危害**: "getUpperArmy 优先 visiting hero" 的直觉假设使 P1 visit 修复后兵仍进 garrison 黑洞; 知识库 08-31 条目关键推论因此错误 (已修正)
- **正确姿势**: 招兵给 visiting hero 时显式 `dst = town->getVisitingHero()` (public const, CGTownInstance.h L132)
- 状态: 🔴 认知坑, 已修复 (P1b)

### 134. fprintf(stderr) 在 MMAI server 内不可见: console 重定向 (2026-09-02)
- **现象**: AAI.cpp 内 fprintf(stderr,...) 诊断在 hermes/主日志均不出现 ([MMAI-DIAG] init 行证明启动期 stderr 通 hermes, 但 AI 运行期输出被吞)
- **正确姿势**: C++ 侧诊断写独立文件 `{FILE* dg = fopen("/tmp/xxx.log","a"); if(dg){fprintf(dg,...); fclose(dg);} }`; 基建: /tmp/rl_recruit_diag.log (取兵链路诊断, 验证后可删)
- 状态: 🔴 排查坑, 基建可用

### 137. VCMI 坐标系双口径坑: 锚点 pos vs visitablePos, 邻接判定必错 (2026-09-02)
- **现象**: P1 邻接守卫用锚点坐标 `distSq(standPos, cur->pos) > 2` → 邻接英雄被误判"远", 71/71 全部误弃 (DIAG7: enter 有动作, afterMove 恒 0); 改 visitablePos() Chebyshev≤1 口径后同场景放行
- **机制**: `cur->pos` 与 `visitablePos()` 差 convertFromVisitablePos 对象相关偏移; 城锚点在 3x3 mask 中心 (mask=["VVVVV","VVAVV","VVVVV"]), 英雄 visit 停在邻格 — 锚点坐标系下"邻接"对城锚点距离可达 2-3, 守卫阈值 2 必误杀
- **正确姿势**: 邻接/距离/守卫判定一律 **visitable 口径** (`visitablePos()` 双方 Chebyshev≤1); 锚点坐标仅作 moveHero 目的地; 已在锚点时改走对象格本身触发 visit (与 a==8 双路径同款)
- **关联**: 知识库"城格不可站"条 (TOWN 判定 dist≤1 同源); 踩坑 #133 (getUpperArmy)
- 状态: 🔴 认知坑, 已修复 (P1c)

### 140. C++ API 假设编译前必 grep 验证: typeName() 不存在实为 getTypeName() (2026-09-03)
- **现象**: R7 埋点凭直觉写 `visitedObject->typeName()` — CGObjectInstance 实际 API 是 `getTypeName()` (CGObjectInstance.h L54), 编译期才暴露; 若在停训练窗口内编译失败则窗口拉长
- **正确姿势**: 停训练窗口前先在源码 grep 验证所有新用 API (类成员名/方法签名); 本次因编译前验证流程 (queryID/result 虚成员 grep) 已验两项, 漏了 typeName — 流程执行不彻底
- 状态: 🟡 流程坑, 规范先行

### 148. GUI 死锁根因: detached 线程持锁路径退出 → interfaceMutex 永久失锁 (2026-09-09)
- **现象**: ModelAI GUI 复测, AI 行动后 ~2s 画面永久冻结; minidump 实锁 owner = 已死线程的 pthread 结构, 主线程 + runNetwork 双双死等 ENGINE->interfaceMutex
- **根因**: ModelAI `heroMoved` 回调 (网络线程) 启动 detached 延迟线程调 `endTurn` — detached 线程生命周期失控, 持锁路径随线程退出失效 → interfaceMutex 状态损坏 (永久失锁), 全进程死等
- **修复 (D:\vcmi_model_ai\model_ai.cpp)**: 移除 detached 线程 → `heroMoved` (无战斗) / `battleEnded` (有战斗) 回调内**同步调用 endTurn** (waitTillRealize=false 非阻塞, 与 yourTurn 回调模式一致) + battle_active 原子变量区分两条路径 + in_my_turn 及时重置防 battleEnded 误触发
- **教训**: ①回调线程里禁开 detached 线程做续接动作 — 生命周期失控 = 锁资源泄漏定时炸弹 ②GUI 锁问题的终结证据是 minidump 的锁 owner 归属, 不是猜测 ③同步 endTurn 的前提是非阻塞语义, 先确认 waitTillRealize=false 再同步
- 状态: ✅ 修复部署 (旧版备份 ModelAI.dll.bak_0908_deadlock), gui3 复测 endTurn after heroMoved 正常流转

### 158. interfaceMutex 泄漏: onPacketReceived 锁作用域收窄破坏 makeUnlockGuard 不变量 (2026-09-10, GUI 死锁根因①)
- **现象**: --testmap 全 AI 局每次回合切换后整体冻结 (Resp=False); dump 显示 runNetwork 卡在 onPacketReceived 的 pthread_mutex_lock + 主线程卡在 USEREVENT 同一把锁; [MUTEX] 打点实锤 LOCKED 后无配对 UNLOCK 即 onPacketReceived EXIT = 锁泄漏
- **根因**: onPacketReceived (CServerHandler.cpp:1061) 的 scoped_lock 只覆盖 DISCONNECTING 检查 (源码级作用域即如此), 包处理 (pack->visit) 无锁运行; 而深层 handler CPlayerInterface::waitWhileDialog (CPlayerInterface.cpp:1393) 的 `makeUnlockGuard` 语义 = "析构时重锁恢复现场" — 无锁调用时析构重锁**凭空加锁且无人配对解锁** → 每次回合切换泄漏一锁
- **修复**: onPacketReceived 用 `optional<unique_lock<GameEngine::LoggingMutex>>` 持锁覆盖整个 pack->visit, 恢复"包处理持锁"不变量
- **教训**: ①makeUnlockGuard/makeUnlockSharedGuard 隐含前提 = "调用者持锁" — **任何锁作用域改动必须全链审查所有 guard 用户** ②guard 是 RAII 但"恢复现场"型 guard 的不变量靠调用约定, 编译器/RAII 救不了 ③LeakSanitizer 类工具不覆盖 std::mutex, 只能靠打点收支对账 ([MUTEX] LOCKED vs UNLOCK 计数)
- 状态: ✅ 修复 + day=31 验证

### 159. SPECTATOR 无 PlayerState: getPlayerState(-4) 返回 null 无判空崩溃 (2026-09-10, 死锁修复后第二层)
- **现象**: 死锁修复后跑到 day=2 崩溃 `0xC0000005 读 0x6d8`, 前奏是 "getResource: No player info!" ×N 刷屏; dump 崩点 `mov rdi,[rax+0x6d8]` 前一条是 `call CGameInfoCallback::getPlayerState(PlayerColor, bool)` (IAT 0xa9e5b8)
- **根因**: testmap-onlyai 的观众视角接口 playerID=**SPECTATOR(-4)** (崩溃时 rdx=0xfffffffc 实锤), 游戏状态里 SPECTATOR 无 PlayerState → getPlayerState 返回 null → AdventureMapShortcuts::optionCanViewQuests (L647) `->quests.empty()` 无判空解引用 (+0x6d8/+0x6e0 = vector begin/end 对)
- **修复**: optionCanViewQuests 判空 (CPlayerInterface.cpp:1363 已有同类先例 "PS NULL GUARD: spectator has no PlayerState")
- **教训**: ①onlyai/观战模式引入后, 所有 `getPlayerState(interface->playerID)` 调用点都要假设 SPECTATOR; 上游无此模式所以上游代码天然不防 ②崩溃前奏的 verbose 警告刷屏 ("No player info!") 就是同源查询失败信号, 看到 spam 就该想到同族调用里有没有漏判空的
- 状态: ✅ 修复 + day=31 验证

### 160. winpthreads Normal mutex 不记录 owner: dump 静态分析定不出持锁者 (2026-09-10)
- **现象**: 冻结 dump 里读 interfaceMutex (ENGINE+0x98) 的 pthread_mutex_t, 值 {state=2, type=0, +0x08=0x1618, owner=0xffffffff} — 曾把 0x1618 误判为持锁死线程 TID
- **根因**: ①winpthreads `pthread_mutex_t` 本体是**指针** (GENERIC_INITIALIZER=-1 惰性初始化), 真结构体在堆上; ②内部布局 `{state(Unlocked/Locked/Waiting), type(Normal/Errorcheck/Recursive), event(auto-reset HANDLE!), rec_lock, owner}` — **仅 Recursive/Errorcheck 记录 owner, Normal 恒 0xffffffff**; 0x1618 = event 句柄 (内核 HANDLE 数值巧合性地小)
- **规避**: ①std::mutex 死锁的持锁者定位**必须运行时打点** (LoggingMutex: LOCKED/UNLOCK + tid + `__builtin_return_address(0)` → .pdata 映射锁点), dump 只能证明"锁被持有"不能证明"谁持有" ②冻结 dump 抓晚了锁内存会被复用污染 (gui8 教训), 抓现场要快
- 状态: ✅ LoggingMutex 已常驻 GameEngine (复发雷达)
- 关联: 知识库 "09-10 GUI 死锁终局闭环" 章

### 165. GUI 线程边界无 catch-all: 未捕获 C++ 异常直通 SEH filter → "Disaster happened" + 僵尸进程 (2026-09-10, 第五崩)
- **现象**: 浸泡测试 (soak_gui14) 用户点系统菜单 (SettingsMainWindow 正常打开) 1.1s 后，runServer (tid=42544) 与 runNetwork (tid=45960) 双双 "Disaster happened" 但**进程存活成僵尸** (Responding=True / 802MB / 游戏逻辑死 / GUI 消息泵空转) — 与第四崩 (MainGUI 死 → 0xC0000409 → 进程退出) 模式不同
- **取证链**: ①日志 Disaster 行后无异常文本 — CConsoleHandler.cpp `onUnhandledException` (L119-140, SEH filter) 只打 "Disaster happened." + Thread ID, **不打 Reason** (Reason 只在 `onTerminate` L146 打) → 无文本即 SEH filter 路径实锤 ②21.7MB dmp = `MiniDumpWithDataSegs` 非 FullMemory (`extraDump` 设置未开), 堆上异常对象文本取不到 ③`py/parse_crash_dmp.py` 手解 minidump: 异常流 (type 6) `Code=0x20474343` = GCC/MinGW SEH 模式 C++ 异常标记 (ASCII "GCC ") → **未捕获 C++ 异常实锤, 非 AV**
- **根因**: `ServerRunner.cpp` runServer lambda 完全裸奔无 try/catch; `CServerHandler.cpp` threadRunNetwork 只 catch `TerminationRequestedException` — 两线程边界抛出的 C++ 异常绕过 std::terminate 直达 OS unhandled filter; 两线程先后触发 filter, 疑似并发 MiniDumpWriteDump 挂起 → 僵尸
- **修复**: ①runServer 只包 `server->run()` (**不包 prepare/promise.set_value** — prepare 抛异常时主线程会永久挂在 `promise.get_future().get()`) ②threadRunNetwork 追加 catch std::exception + catch(...), 双路日志 (logGlobal 进 VCMI_Client_log.txt + `fprintf [THREAD] xxx THREW` 进 stderr 便于 grep)
- **工具沉淀**: `py/parse_crash_dmp.py` — minidump 异常流 (ThreadId/Code/Address/nparams) + 模块表 (type 4, MINIDUMP_MODULE 108 字节) + ASLR 换算 (runtimeVA − runtimeBase + PE_ImageBase = addr2line 地址, ImageBase 在 e_lfanew+4+20+24) → 实测定位到 KERNELBASE.dll RaiseException 内部
- **教训**: ①**线程入口 = 异常边界, catch-all 必须兜底** — GCC SEH 下未捕获 C++ 异常不走 terminate handler 直达 OS filter ②"Disaster happened" 无 Reason = SEH filter 路径; 有 Reason = onTerminate 路径 — 两者排查方向完全不同 ③日志无文本时转 dmp 拿异常码, 0x20474343 一眼定性 ④良性刷屏别淹没: getPlayerStatus "No such player!" (观战敌回合轮询) / getResource "No player info!" (层切换资源栏刷新) 均良性
- 状态: ✅ 修复部署 + soak_gui15 复测 PASS (93617 行 stderr 零 THREW/零 Disaster, 含 KingdomOverview 直接点击); 异常原始 throw 点未闭合 (已 instrumented, 复发即给出 e.what() 且不再僵尸化)

### 166. NK2 死锁修复链 (08-16/17, 详见 vcmi-ml-module refs/deadlock-chain)
- **close 卡死**: env.close() 嵌入模式卡死 (58% CPU, close 线程 5s 超时无效) → SAVED 后直接 os._exit(0) 跳过
- **battle query 卡顶**: 三层 query 栈 + notifyObjectAboutRemoval 中断 → QueriesProcessor::removeQuery 任意位置强制移除
- **battleResultAccepted**: 改用 removeQuery (onRemoval 只调一次防段错误 + 移除后触发暴露链)
- **采集 bash wrapper**: 逐局独立 (防跨局状态泄漏)
- **训练前必验**: npz 英雄位置 + 动作分布 (防模型输出全空/全非法)

### 167. ServerPlugin HeroPool 对称校验拒多敌课程: 1v3 及 1v7 全部无法启动 (2026-09-06)
- **现象**: alchemist 修复后 1v3 仍拒启动: `Added pool 0 of owner 0/1: default` → `ERROR Failed to launch game: Owners have differently sized pools`
- **真因**: fork 训练栈 `server/ML/ServerPlugin.cpp` pool matching — 非 randomHeroes 模式且恰好 2 owner 时, 强制双方同名 pool 英雄数相等 (T04/T05/duel 全 1v1 天然通过, 1v3 red1 vs blue3 → 1≠3 throw)
- **修复**: 大小不等降级 stdout 警告 (`pool size mismatch ... skip`), pool **名**不同仍 throw (真配错图仍可发现); **libmlserverplugin.so 是独立 SHARED 库不触"勿重编 libvcmi.so"铁律** (server/ML/CMakeLists add_library mlserverplugin SHARED; 单文件重编 -j4, cmake --build rel/ --target mlserverplugin)
- **运维**: 备份链 .bak_pool_0906 (.so+源码); 副本同步 vtest/bin + hero3_vcmi/build/bin (route-backups/vcmi-gym 为历史备份不同步); **1v7 课程前置障碍已扫除**
- 状态: ✅ 已修复部署 (1v3 真实首局 73 步 r=82.38 闭环)

### 175. VCMI 网络协议是二进制序列化，非 JSON (09-11)

**现象**: 调研 xsa-dev/homm3env 时发现其 JSON over TCP 协议基于 `features/battle-ml` 分支 (2022 年死分支)，当前 VCMI develop 无此协议。VCMI 官方网络协议使用 `Serializeable` 模板 + `h & field` 做二进制序列化。

**根因**: VCMI 的网络包系统 (`lib/networkPacks/`) 从 HoMM3 原版协议继承而来，使用自定义二进制格式 (非 JSON/protobuf/msgpack)。`CPack` 基类的 `serialize(Handler &h)` 通过 `h & field` 逐字段序列化，变长字段 (std::vector, std::string) 有自定义编码。

**处理**: 外挂 AI 方案需逆向 `Serializeable.h` 的字节布局。短期不影响 (继续 .so 直连)，长期需路径 B (C++ headless client 复用 VCMI 头文件)。

**教训**: 不要假设 VCMI 有 JSON 协议 — 第三方项目 (homm3env) 的 JSON 格式是基于已废弃分支的私有协议。官方协议始终在 `lib/networkPacks/` 定义。

---

### 176. EmptyAI 不走网络 — VCMI 内置 AI 全是进程内直接回调 (09-11)

**现象**: 误以为 EmptyAI 或 MMAI 通过网络与 server 通信，实际读源码发现全部用 `CCallback` (C++ 直接函数调用)，编译为 OBJECT 库链接进 server 进程。

**根因**: `AIFactory.h` 定义 `createAdventureAI(name)` / `createBattleAI(name)` 静态工厂，所有 AI 在 server 进程内构造。`CEmptyAI::yourTurn` 直接调 `cb->selectionMade(0); cb->endTurn()`。无动态加载、无插件系统。

**处理**: 外挂 AI 必须走网络协议 (作为客户端连接 server)，不能模仿内置 AI 的 `CCallback` 路径。`--onlyAI` 标志是告诉 server 内部构造 AI，不是启动网络桥。

**教训**: VCMI 有两条 AI 路径 — 内部回调 (CCallback, 所有内置 AI) vs 网络协议 (CPackForServer, 客户端)。外挂只能用网络协议。混淆这两条路径会导致错误的架构设计。

---

### 177. features/battle-ml 分支是死分支 — 基于它的 JSON 协议不可用 (09-11)

**现象**: xsa-dev/homm3env 的 README 指向 `vcmi/vcmi/tree/battle-ml` 分支，其 TCP JSON 协议在当前 develop 无对应 server 端代码。

**根因**: `features/battle-ml` 分支最后提交 2022-07-19 (作者 nullkiller)，从未合并到 develop。当前 VCMI develop 完全没有 BattleML TCP/JSON 协议代码。

**处理**: 不要基于 battle-ml 分支做架构决策。如果要外挂 AI，走官方 `lib/network/` + `lib/networkPacks/` 协议。

**教训**: 调研第三方项目时，必须确认其依赖的上游分支是否仍然活跃。homm3env 是 2021 SOC 比赛产物，代码是骨架/存根 (step() 返回 None, update_game_state() 是 pass)，其架构参考价值仅限于"JSON over TCP 概念"，不能直接用。

---

### 178. `MMAI::ASSERT` 宏带 namespace 前缀非法展开 → mlclient-cli 编译失败 (09-11)

**状态**: ✅ 已解决

**现象**: C4 #7632 全量 build 时 `mlclient-cli` 报 `AI/MMAI/common.h:23:9: error: expected unqualified-id before 'if'`。agent-v13/14/15.cpp 各 1 处 `MMAI::ASSERT(err.empty(), ...)` 编译不过。

**根因**: `ASSERT` 宏定义在 `namespace MMAI` 内（common.h L20-23：`#define ASSERT(cond, msg) if(!(cond)) throw std::runtime_error(...)`），但 **C/C++ 宏替换不受命名空间限定**——`MMAI::ASSERT(...)` 被展开成 `MMAI::if(!(cond))`，`MMAI::if` 非法。历史遗留 bug（08-01 起 mlclient-cli target 从未编过，暴露即首编），非 C4 引入。

**处理**: 三处 sed 去 `MMAI::` 前缀（agent-v13.cpp L35 / agent-v14.cpp L35 / agent-v15.cpp L42），vcmi-native 与 vcmi-workspace/vcmi 双仓同步修复，全量 build 后 `[100%] Built target mlclient-cli`。

**教训**: 宏永远不带 `NS::` 前缀调用；凡宏定义在 namespace 内，使用处直接裸名。验证旧项目时注意"从未编译过的 target"可能藏着历史语法债。

---

### 179. std::views 传递 include 断裂 — BuildAnalyzer 需显式 `#include <ranges>` (09-11)

**状态**: ✅ 已解决

**现象**: C4 cherry-pick 后部分文件编译报 `std::views::` 未声明，即使已间接包含其他 C++20 头文件。

**根因**: `<bits/range_to.h>` 等传递 include 链在本工具链版本下不稳定，`std::views` 不能依赖传递引入。

**处理**: 在直接使用 `std::views` 的 TU 显式 `#include <ranges>`。

**教训**: 涉及 C++20 新特性（ranges/coroutines/concepts）必须显式 include，不赌传递引入；不同 GCC/clang 版本传递链差异大。

---

### 180. ResetInfo 周判断新旧 API 映射 — 复合判断 ≡ `period==7` (09-11)

**状态**: ✅ 已解决

**现象**: cherry-pick #7632 引入的 `ResetInfo` 新字段与旧代码 `weeks/days/months` 复合判断（`weeks*7 + days` 之类）语义不一致，NK2 代码按新 API 写。

**根因**: 新版把"第 N 周"判断简化为 `ResetInfo::period == 7`（周期=7 即每周）。

**处理**: 旧复合判断统一改写成 `period==7` 判周；`getDate(DAY)` 取绝对天数、`getDate(DAY_OF_WEEK)` 取 1-7。完整新旧映射表见知识库「C4 #7632 执行记录」章。

**教训**: merge 上游重构性 commit 时，先 grep 出所有旧 API 调用点，逐一按新 API 语义改写，不能只改编译报错处。

---

### 181. getCalendar → getDate 等价改写要点 (09-11)

**状态**: ✅ 已解决

**现象**: #7632 删除 `getCalendar()` 返回结构，日历读取改 `getDate(UNIT)`。

**根因**: 上游 API 重构；`getCalendar` 的 week/month 字段由 `getDate(DAY)`（绝对天数）与 `getDate(DAY_OF_WEEK)`（1-7，周一=1）组合等价替代。

**处理**: `CSpellHandler.h` 等调用点逐处改写；周恒 7 天的语义保持不变。

**教训**: 等价改写前先用小样例算一遍天数/星期对应关系，防止 off-by-one（DAY_OF_WEEK 是 1-based）。

---

### 182. `sed -n` 输出隐藏行首 tab — patch 锚点必须 `cat -A` 实测缩进 (09-11)

**状态**: ✅ 已解决

**现象**: 用 `sed -n 'Xp' file` 取出的行做 SearchReplace 锚点时反复失败；`grep -n` 找到的行与文件实际缩进对不上。

**根因**: 文件内混用 tab 缩进，sed/Read 输出把 tab 渲染成空格（或吞掉前导空白），锚点字符串实际是空格开头而非 tab 开头。

**处理**: 关键锚点先 `cat -A`（或 `sed -n 'Xp' file | cat -A`）实测真实字符再写入 patch；本会话 C4 知识库 SearchReplace 首败（anchor 多算 1 行）也用重读文件末尾确认的方式避免。

**教训**: patch 失败先怀疑"看不见的字符"，`cat -A` 显示 tab(`^I`) 与行尾(`$`)，比反复对照肉眼输出可靠。

---

### 183. .so 副本三目录不在训练链路 — 不同步防污染 (09-11)

**状态**: ✅ 已解决（实锤，无需同步）

**现象**: C4 c4-5 "多副本同步" 步骤要求把新 libvcmi.so 等同步到 vcmi-native-build / vtest / hero3_vcmi/build 三处旧副本；事实核查发现三处均为旧版 .so 且**不在训练运行时链路**，同步反而污染基线。

**根因**: 训练真身架构（0911 实锤链）：`train_wsl2_ppo_v5.sh`（transient unit, systemd-run --collect）→ `train_wsl2_ppo_v2.py`（`LD_LIBRARY_PATH` 硬编码 `rel/bin`，`STRATEGIC_STATE_LIB`=`rel/bin/libmlclient.so`）→ `ep_runner_one.py` → `strategic_env.py`（CDLL 加载 rel/bin/libmlclient.so）→ `threadconnector.cpp` → `MLClient.cpp` `GAME->server().debugStartTest(mapname)` = **libmlclient 内嵌 server，进程内线程运行，不启动独立 vcmiserver 进程**。三副本目录是历史构建产物，无人引用。

**处理**: 新栈 .so 全部留在 rel/bin 原位即生效，三副本不动；备份安全网 `~/so_backup_0910_7632/`（libvcmi.so.bak_0910 + libMMAI.so）保留用于回滚。

**教训**: "改 .so 后同步全部副本"的旧纪律建立在多副本被引用的假设上；动副本前先 grep 运行时实际加载路径（LD_LIBRARY_PATH / STRATEGIC_STATE_LIB / CDLL 路径）确认真身，副本同步改为"确认真身后再议"。

---

### 184. #7632 后 T05 小图 +15% 变慢 — NK2 收益与图规模相关 (09-11, 闭环)

**状态**: ✅ 已解决（观察闭环, 假设坐实, 用户拍板保留新栈）

**现象**: 新栈 5 局实测：T05_52X52_mir 旧 97s×6 局极稳 → 新 112s×2 局极稳 = **+15% 慢**（双方极稳，非噪音）；T06_duel 新 4.96s/步落在旧区间 3.67-6.23s/步内（仅 1 局样本）；reward 不劣化（T05 r=166.6/161.8 vs 旧 ~160；T06 r=135.4/137.7 正常）。

**根因（假设）**: 官方 #7632 的 +40% 吞吐 benchmark 是大规模寻路场景；T05 小图 NK2 寻路回合占比低，优化不敏感，且 PathfinderCache 在小图上的维护成本可能是净负。

**处理**: 首窗只观察吞吐与稳定性（纪律：不与其他变更同窗）；T06 duel 需攒 3-4 局稳态样本再判定；T05 若持续 112s 级则判定"本负载无收益"，评估回滚（git revert native 两笔 + workspace 一笔，或换回 `~/so_backup_0910_7632/` 的 libvcmi.so）。

**教训**: 上游 benchmark 收益数字（+40%）不能外推到本项目负载；落地后必须用**同图 EP_TIME 严格对比法**（新旧栈同 map 对比消除地图难度变量）判定，且要等稳态样本（≥3 局）再下结论。

### 185. T13.10 Lobby/P8 前置完成但实机多人局未完成 (2026-09-11) — ✅ 已解决 (阶段1+2 实机 PASS)
- **状态**: ✅ 已解决 — P8-B 阶段1 (lobby join, efb5b6b) + 阶段2 (完整对局 EndTurn 轮转, 407e8e5 + 9cc08b9) 均实机 PASS
- **背景**: T13 外挂 AI 协议客户端完成 `py/vcmi_protocol/`, 新增 Lobby 包解析与 P8-A 实机入口; 离线单测 `144 passed, 0 failed`。
- **坑**: 离线解析通过 ≠ 真实 VCMI server 接受。Lobby 握手、玩家槽位、StartInfo/CMapInfo、跨客户端同步仍需实机抓包验证; 不能把 `LobbyUpdateState` 部分字段占位解析当作完成多人局。
- **正确口径**: 完成的是 P8 前置: TCP/CPack/Query/ModelBridge/Lobby 基础包。未完成的是 P8-B/C: 实机启动 VCMI server/client, AI 与人类同局完成至少 1 局。
- **解决**: 阶段1 假服务器捕获法对拍 BYTE-IDENTICAL 56B; 阶段2 方案F (Python host + LobbyChangeHost 让位 + guest SetMap + StartGame + EndTurn 轮转)。阶段2 首轮虽表面 game_started=True，但 server 日志实锤 "not allowed/fishy" 拒绝（见 #200），真正 zero-fishy 全绿由 9cc08b9 达成。
- **复现/验证**: `python py/p8/p8be_host_start.py` (阶段2 完整对局, 跑完 grep server 日志 `not allowed|fishy` 应 = 0); `python py/p8/p8b_lobby_probe.py` (阶段1 握手)。
- **关联**: T13.10 / P8 / `docs/序列化协议规格.md` / 提交 `bdce29a` → `efb5b6b` → `407e8e5` → `9cc08b9` / 踩坑 #200。

### 186. vcmienv ERROR 日志级下 T06 终局双重失明：超时 forcing 零痕迹，9/10 判真实 game_over (2026-09-11) — ✅ 实锤（只读）
- **状态**: ✅ 实锤（只读取证），探针已写待错窗执行
- **背景**: 排查 [GUARD_DONE] 早停 + TOWNSTALL 可达性 + target_list 排序链时，需定判 T06 历史 10 局终局来源。
- **坑**: ep_runner L330 传 `vcmienv_loglevel="ERROR"` → strategic_env L883 WARNING "timed out after 300s" 与 L766 INFO "Episode done" 双双被抑制；进 ep 日志的超时痕迹只有 L725 ERROR "adventure_wait timed out: … — forcing episode end"，而 9/10 历史 T06 局该 ERROR 缺失 ⇒ 判为真实 game_over（纠正此前"旁证指向超时 forcing"的推断）。但 L1182 步尾静默 break + 训练高亮词表无超时词 ⇒ 超时 forcing 路径依旧双重失明，是隐藏的终止源。
- **正确口径**: 判 T06 终局来源不靠日志推，用 obs[19]/[34] alive 判别器（见 #188）或探针 `vcmienv_loglevel="INFO"` 实跑（`py/probe_t06_gameover.py`，错窗执行：停 v5 → 跑 → 重启）。
- **关联**: #187 / #188 / `py/probe_t06_gameover.py` / 当前任务清单 g3b 事实块 / ep_runner L330-L332 / strategic_env L724-L736、L766、L883、L1182。

### 187. NK2 模式无末步 ±200：末局 reward 无终局方向判别力 (2026-09-11) — ✅ 实锤
- **状态**: ✅ 实锤（只读取证）
- **背景**: 曾试图从 EP_TRAJ 末局 r 定判胜负（预设 NK2 末步注入胜负 ±200 reward）。
- **坑**: `--use_nk2_shaping` 下 `_calc_reward` L1057 提前 return，胜负 ±200 不进管道；r=135.4 级数值在 timeout/go=1/go=2 三场景均可凑出，末 r 无判别力。
- **正确口径**: 终局方向只信 obs alive 判别器（#188）或探针终局 4-tuple dump，不用末 r。
- **关联**: #186 / #188 / 当前任务清单 g3b 事实块 / strategic_env `_calc_reward` L1057。

### 188. obs 无 game_over 通道：players 段 alive 作只读判别器，battle_quality_events 死路封档 (2026-09-11) — ✅ 实锤
- **状态**: ✅ 实锤（只读取证）
- **背景**: EP_TRAJ 无 terminal 字段 + 9/11 T06 traj 被 52X52 并发跑 (pid 45100) 覆盖丢失，只剩 1/11 样本；需另找只读判别路径。
- **坑①**: obs 3464 冻结（铁律）无 game_over 通道 → 用 players 段（base=8、每玩家 15 字段、alive 为第 12 个）：红 p0 alive=obs[19]、蓝 p1 alive=obs[34]；配合 C++ alive_count≤1 → game_over=last_alive+1 规则：双 0 = timeout forcing（全零 obs）；obs[19]=1 & obs[34]=0 = go=1 红胜；obs[19]=0 & obs[34]=1 = go=2 蓝胜；双 1 + 200 步到顶 = 截断无 terminal。
- **坑②**: `battle_quality_events.log` 40 条 T06 HEROSEG_EMPTY 全 `go=0 slots=0/0 ah=0 cur_p=0` = 观测瞬态空拍，非终局事件，死路封档。
- **正确口径**: 只读定判用 alive 判别器四场景表；实跑定判用探针终局 4-tuple + players obs[8:43] sanity dump。
- **复现/验证**: `python -c` 读 traj 末帧 obs[19]/obs[34]，或探针 `--out py/probe_t06_traj.json` 后看 terminal block。
- **关联**: #186 / #187 / `py/probe_t06_gameover.py` / 当前任务清单 g3b 事实块。

### 189. 8 人局 7 份 ONNX 实例：teal AI 首次 predict 挂死 (2026-09-11) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（Game B teal 卡死现场），源码修复已落 `ppomodelai/src/` 未 commit
- **背景**: PpoModelAI 插件 8 人局（7 个 ModelAI 玩家）teal 首次 predict 挂死。
- **坑**: 每个 ModelAI 各自构造 `Ort::Env + Session` → 7 份全核 ONNX 线程池，第 6 个 AI 起资源放大导致挂死；Game A 单实例正常掩盖问题。
- **正确口径**: 多 AI 插件推理走进程级单例 `ModelInference::instance()`（C++11 magic static 线程安全，同路径只加载一次）+ 线程池限制（intra 2 / inter 1，obs 仅 256 维够用）；加载失败置 `nullptr` 而非半构造。
- **关联**: #190 / 知识库 "PpoModelAI teal 卡死修复" 章 / `ppomodelai/src/ModelInference.{h,cpp}`。

### 190. GetInputNameAllocated 悬垂指针：ORT "Invalid input name: " 全 fallback endTurn (2026-09-11) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（源码审查），修复已落未 commit
- **背景**: 排查 predict 异常 / 动作全 endTurn 现象。
- **坑**: 旧版 `inputNames` 存 `session.GetInputNameAllocated(...).get()` —— 返回的 allocator 对象行尾析构，`const char*` 悬垂；ORT 报 "Invalid input name: " 后 inference 全部走 fallback endTurn，表面像"模型不动作"。
- **正确口径**: ORT C++ API 返回"持有分配的包装器"时，用 `std::string` 深拷贝持有名字，`Run` 调用期间才取局部 c_str；勿存临时对象指针。
- **关联**: #189 / `ppomodelai/src/ModelInference.cpp`。

### 191. moveHero 双坐标 anchor↔visitable：server 判 blocked → client 崩溃 (2026-09-11, gui9 实测) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（gui9 卡死/崩溃现场），修复已落未 commit
- **背景**: PpoModelAI 发出 move 后 server 拒绝或 client `onPacketReceived` 崩溃。
- **坑**: `hero->pos` 是**模板锚点格**，英雄实际交互格 = `visitablePos()` = `pos - getVisitableOffset()`（英雄模板 1x2，offset 非 0）；server `CGameHandler::moveHero` 对收到的 dst 再做 `convertToVisitablePos(dst)` 且成功后 `setAnchorPos(pack.end)` → **请求参数是 anchor 语义**。本地用 anchor 格直接当目标发 → 双方判的格子错位一格 → server 判 blocked 拒绝。
- **正确口径**: 本地 tile/pathfinder 判定用 visitable 语义目标；请求参数 `dest = visitableDest + getVisitableOffset()` 转回 anchor。再叠本地三重门（全过才发 move，任一失败 endTurn）：① tile 拒绝（岩石 / `blocked && !visitable`）② simultaneous-turns 目标格有他人对象（保守 endTurn）③ pathfinder `turns>0`/不可达（本回合 MP 不够）。与 09-10 "anchor↔visitable 双坐标系" 章（[GUARD]/[MINE] 假糖根因）同源。
- **关联**: #189 / 知识库同章 / `ppomodelai/src/PpoModelAI.cpp`。

### 192. 构建/链接/可观测性三坑：boost stub guard 失配 + DLL 导出缺失 + 插件 logAi 失明 (2026-09-11) — ✅ 已修
- **状态**: ✅ 源码修复已落未 commit
- **背景**: PpoModelAI 插件重编 + 卡死取证过程。
- **坑①**: 自写 `boost::noncopyable` stub 的 guard 名与真实 boost guard（`BOOST_CORE_NONCOPYABLE_HPP`）不符 → 重定义冲突 + `makeDefend` 等类型转换连锁报错；修法：删 stub，`StdInc.h` 改 `#include "Global.h"`（与 `lib/StdInc.h` 口径）直接用系统 boost。
- **坑②**: `exports.def` 要求 `GetAiName`/`GetNewAI` 但源码缺失 → 链接失败；参照 `AI/MMAI/main.cpp` 约定在 `PpoModelAI.cpp` 尾部补齐（`__GNUC__` 下需 `strcpy_s` 兼容宏）。
- **坑③**: 插件 `logAi` 输出在 client log 中**零命中**（teal 卡死时无 from-turn 内进度可观测）；取证只能靠 stderr 直出（`AI_TRACE` 宏：`fprintf(stderr)` + `fflush`，配合客户端 stderr 管道）。
- **关联**: #189-#191 / 知识库 "PpoModelAI teal 卡死修复" 章。

### 193. 构建树 ninja 静默失败：终端 PATH 缺 mingw64\bin → cc1plus DLL_NOT_FOUND 零输出 (2026-09-11) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（gui12 修复重编期），规避法已固化
- **背景**: 修 `client/CPlayerInterface.cpp` 后在 Trae 终端跑 `ninja`，`Building CXX object` 步 `FAILED: [code=1]` 但 **c++ 编译器零 diagnostic 输出**，稳定复现。
- **坑**: 新开终端 PATH 无 `C:\msys64\mingw64\bin` → g++ 驱动 spawn `cc1plus.exe` 时其依赖 DLL（libgmp/libmpfr/libisl/libzstd 等）找不到 → `0xC0000135 (STATUS_DLL_NOT_FOUND)` → 驱动**不打印任何错误**直接 exit 1。表现为"编译失败但无错误信息"，极易误判成源码/编码问题。链接期另一表现：`ld.exe: cannot open output file bin\VCMI_client.exe: Permission denied` = 游戏进程未退占用 exe（先杀 VCMI_client 再编）。
- **正确口径**: 编构建树前先 `$env:Path = 'C:\msys64\mingw64\bin;' + $env:Path`；ninja 用绝对路径 `C:\msys64\mingw64\bin\ninja.exe`（不在 PATH）。排查口诀：编译 FAILED 无输出 → 手动跑 `cc1plus.exe --version` 看 exit 是否 `-1073741515`。**另**: 任何 CMake re-run 会重新生成 build.ninja 并复活 `$<LINK_ONLY>` 转义坑（PowerShell 正则替换 9 处 → `-l` 形式），改 cpp 不触发、改 CMakeLists 必触发。
- **关联**: #192 / `D:\vcmi-fork-build\build.ninja`。

### 194. VCMI fork settings 键路径错：combatAlliedAI 读 server 段 → 空 dll 名 → runNetwork 线程死亡全局卡死 (2026-09-11, gui11 实测) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（client 日志铁证），修复已落未 commit
- **背景**: 用户开 quickCombat 攻击野怪守卫 → 战斗开始瞬间全局冻结（AI 无新回合、client 进程存活、无 crash dump）。
- **坑**: `client/CPlayerInterface.cpp:1874` 写 `settings["server"]["combatAlliedAI"]`，但 schema（`config/schemas/settings.json`）定义在 **`ai` 段**（默认 "BattleAI"，全库其余 6 处引用均为 `settings["ai"][...]`）→ 恒返回空串。用户 `adventure.quickCombat=true` 时 `battleStart` → `prepareAutoFightingAI` → `getNewBattleAI("")` → 尝试加载 `.\AI\.dll`（**空库名**）→ throw → 异常沿包 apply 链传播到 **runNetwork 收包线程 → 线程终止** → client 不再收发任何包 → 全局卡死（runServer 线程还活着等 query 回复，永不超时）。
- **正确口径**: 键路径改 `settings["ai"]["combatAlliedAI"]`。取证口诀：**战斗开始后冻结，先查 client 日志 `Cannot open dynamic library` / `thread terminated by exception`**（`VCMI_Client_log.txt`，比 stderr 关键行更直接）；`[runServer]` 标签说明单进程模式（server 为内嵌线程，无独立 VCMI_server.exe 进程可查）。
- **关联**: #193 / `vcmi/config/schemas/settings.json` ai 段 / gui13 实测战斗 7s 闭环 + 多轮推进正常。

### 195. transient unit 第三次复现：v5 停止后 `systemctl start` 报 "Unit not found"，重启必须 `py/restart_train_v5.sh` systemd-run 重建 (2026-09-11) — ⚠️ 三次复现 + 口径固化
- **状态**: ⚠️ 三次复现（09-06 首踩 / 09-08 二次 / 09-11 本条），规避口径已固化
- **背景**: 09-11 C 方案部署停训窗，优雅停 `systemctl --user stop homm3-train-v5` 后直接 `systemctl --user start` 想重启 → exit 5 "Unit not found"；排查确认 WSL systemd user manager 无持久单元目录（`/home/administrator/.config/systemd/user` 与 `/etc/systemd/user` 均不存在，仅单一用户 administrator uid 1000）。
- **坑**: v5 由 `systemd-run --user --collect --unit=homm3-train-v5` 创建，`--collect` 使 stop 后单元定义被自动清除，单元即消失；且 `is-active` 对已消失单元照样输出 `inactive`（exit 4）→ **不能作为单元存在性判据**，极易误判为"服务停了 start 一下即可"。
- **正确口径**: 重启 v5 一律 `py/restart_train_v5.sh`（内部 systemd-run 重建；venv 必须绝对路径 `/home/administrator/vcmi-workspace/venv/bin/python` — hero3_fresh 目录下无 venv）；重启前用 `train_loop.log` 尾部 `Saved STATE_PATH` + journalctl 确认停机完成，勿靠 `is-active`。Windows 侧 keepalive（`wsl.exe sleep infinity`，09-11 实查 4 进程常驻）防 idle shutdown 需同时保住。
- **复现/验证**: 本条执行链 — 重建后 unit `active`、主进程+ep_runner 双进程在位、`Loaded train state (model+optimizer, step=629167)` 无缝续训、`grep -c '_t06_hero_kill_capture' ep_runner_one.py` = 3 确认 C 方案代码在位。
- **关联**: #168（transient unit 二次复现）/ #114（Windows keepalive）/ `py/restart_train_v5.sh` / `py/check_v5_state.sh`、`py/verify_v5_restart.sh`。

### 196. policy logits 平坦 → argmax 恒定单动作：部署推理必须 softmax 采样与训练一致 (2026-09-11, mq-4 实测) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（onnx 探针 + 实机两局验证），采样版 dll 已部署
- **背景**: mq-4 首次实机 1v7 验证，ModelAI v5 全链路通但三个 AI 动作恒 5/6 不动；最初误判旧 dll 未替换（logAi 格式相同是巧合），Grep 源码确认新代码在跑后转向模型本身。
- **坑**: checkpoint 导出的 `rl_model_v5_0911.onnx` policy 头 logits 高度平坦 — `py/probe_onnx_action5.py` 全输入域（零 obs / 结构化 obs / 随机噪声×5 / 0~5 量级随机×3）argmax 恒 6，top1-top2 差仅 0.1~0.3，logit_std≈0.19 → **argmax 退化为常数函数**；而训练侧采样动作多样（act=[0,17,18,16...3,3,3]）。对比实锤：训练采样多样 ≠ argmax 单峰，同一权重两种决策模式行为天差地别。
- **正确口径**: PPO 部署推理必须按 softmax 概率采样（temperature=1.0）与训练一致，argmax 只适合评估/对拍。实现（`ModelInference.cpp` predict 尾部）：maxLogit 减去防 exp 溢出 → double probs 累加 → `static std::mt19937 rng{std::random_device{}()}` + uniform_real_distribution 轮盘减法采样；sum≤0 或输出异常兜底 return 10（END_TURN）。
- **复现/验证**: 采样版 dll 二次实机 PASS — turn1=[5,7,5,7,5,5,7] turn2=[7,7,5,5,5,7,5] turn3=[5,5,7,7,7,5,5]，moveHero 真实执行且方向语义吻合（见 #198），day1→4 无卡死。训练 logits 拉开差距后换新 onnx，部署侧零改码。
- **关联**: #189（单例推理）/ 知识库 "mq 模型部署线闭环" 章 / `py/probe_onnx_action5.py` / `ppomodelai/src/ModelInference.cpp`。

### 197. AI_TRACE stderr 在 Windows GUI 子系统实机不可见：实机观测一律走 VCMI_Client_log.txt 的 logAi 通道 (2026-09-11, mq-4 实测) — ✅ 实锤
- **状态**: ✅ 实锤（三次日志捕获空 + 对照组实锤）
- **背景**: mq-4 取证尝试用 `AI_TRACE`（`fprintf(stderr)` + fflush，`[ModelAI p%d]` 前缀）经 stderr 管道捕获 AI 决策明细，filter 三次全空。
- **坑**: `fprintf(stderr)` 在 Windows GUI 子系统（VCMI_client.exe）运行期**实机不可见**（仅启动阶段 MUTEX 噪音偶见）——与 #192 坑③"stderr 直出取证"结论冲突，实际那是 teal 卡死期 logAi 失明的特例，**正常期 logAi 通道可靠**，#192 坑③适用范围就此修正。
- **正确口径**: 实机监控一律读 `C:\Users\Administrator\Documents\My Games\vcmi\logs\VCMI_Client_log.txt` 中 `PpoModelAI: ...` 行（logAiLogger 通道，`PpoModelAI.cpp` 403/447/578 行 yourTurn/action/obs 输出全量可靠可见）；stderr 管道只当启动期诊断用。
- **复现/验证**: 采样版验证全程走 VCMI_Client_log.txt，7 AI "v5 model loaded successfully" + 动作流 + moveHero 请求坐标全部取到。
- **关联**: #192（坑③修正）/ 知识库 "PpoModelAI teal 卡死修复" 章 / 知识库 "mq 模型部署线闭环" 章。

### 198. v5 动作方向表 N-start CW（0=N..7=NW）：5=SW=(-1,+1)，AAI.cpp E-start 旧表弃用 (2026-09-11, 实机坐标验证) — ✅ 实锤
- **状态**: ✅ 实锤（moveHero 请求坐标三方吻合）
- **背景**: 实机动作流验证方向语义，需确认 action→(dx,dy) 映射真实口径。
- **坑**: AAI.cpp 52-55 行留有 E-start 顺时针旧方向表遗产，易误导映射排查；文档若写"5=W"之类旧语义会与实机行为矛盾。
- **正确口径**: v5 动作 0-7 移动为 **N-start CW**：0=N..7=NW，`DIR_DX={0,1,1,1,0,-1,-1,-1}` / `DIR_DY={-1,-1,0,1,1,1,0,-1}`。实机铁证：action=5 → moveHero 请求 (10,65)→(9,66) 即 dx=-1,dy=+1 = SW，严格吻合；P2 (105,100)→(104,101)、P6 (67,34)→(66,35) 同向验证。action=7(NW) 对不可达目标被 server 正确拒绝（非 bug）。
- **复现/验证**: 任何实机 action 流对照该表逐一验坐标即可；PPoModelAI.cpp 本地 tile 判定同表。
- **关联**: #191（anchor↔visitable 双坐标）/ 知识库 "mq 模型部署线闭环" 章 / `ppomodelai/src/PpoModelAI.cpp`。

### 199. h3mtxt (alexanderbelous/h3mtxt) mingw GCC 编译三连坑 (2026-09-11) — ✅ 已解决 (3 源码补丁)
- **状态**: ✅ 已解决; roundtrip 4 图全 PASS
- **背景**: P10-C 备料, Windows mingw64 (GCC 16.2, Ninja, O3+flto) 构建 h3mtxt, 上游只测 MSVC → 编不过, 逐个修。
- **坑 1 - partial specialization after instantiation**: `H3JsonReaderBase.h` EnumBitmask 模板特化在某些 TU 内晚于隐式实例化 → GCC 硬错误 (MSVC -fpermissive 档)。修: 非 MSVC 分支加 `-fpermissive` (`cmake/h3mtxt_common.cmake`)。
- **坑 2 - 基类/派生类同名模板重载二义**: `H3WriterBase::writeData(EnumIndexedArray<...>)` 与 `H3MWriter::writeData(EnumIndexedArray<...>)` — GCC 派生类名字查找把 base 版与 derived 版判二义 (MSVC/Clang 选精确匹配)。修: 删基类版, 保留 H3MWriter 版。
- **坑 3 - consteval 静态成员类内前向使用**: `ObjectPropertiesVariant::isInline<T>()` 在类内 `std::conditional_t<isInline<T>(),...>` — GCC "used before its definition" (complete-class context 不覆盖 alias 默认实参)。修: 改命名空间级 `inline constexpr` 变量模板 (`Detail_NS::kObjectPropertiesIsInline<T>`), 类内 static_assert 同步换。
- **口径**: 三坑共同模式 = **GCC 对类内模板实参推导中的成员模板/consteval 前向引用比 MSVC 严**, 上游 MSVC-only 项目跨编译器先预期此类错误; 修复优先级 = 命名空间变量模板 > -fpermissive > 删冗余重载。
- **附带坑**: ① exe 不吃 `/c/...` MSYS 路径 → `MSYS_NO_PATHCONV=1` + `C:/...` ② ROE 图拒读 (仅 AB/SoD) ③ 输出 JSON 带 `//` 注释非严格 JSON, Python 解析需 json5 或剥注释 ④ 构建慢 (866 目标 LTO ~40min)。
- **复现/验证**: `tools/h3mtxt/build/src/h3mtxt/h3mtxt.exe`; roundtrip 判据 = gzip 解压后 raw 逐字节一致 (gzip 头 mtime 差异忽略)。
- **关联**: 知识库 "P10-C 备料" 章 / #193 (mingw PATH 前置) / P10。

### 200. P8-B 阶段2 PlayerStartsTurn 字段序错 + 盲发 EndTurn 抢对方回合 → server fishy 拒绝 (2026-09-11) — ✅ 实锤修复
- **状态**: ✅ 已修复 (commit 9cc08b9)
- **背景**: P8-B 阶段2 首轮 `p8be_host_start.py` 表面 `RESULT: game_started=True`，但用户指出"没完成对局，运行就报错"。查 server 日志抓到实锤。
- **坑① 字段序错**: `PlayerStartsTurn(88)` 的 Python 定义写成 `player + time_limit`，与 C++ `Query{queryID} + PlayerColor player` 字段序不符。C++ 权威结构 (PacksForClient.h): `serialize: h & queryID; h & player;`。实机字节 `88帧 = 00 00 d800 41 00` 逐字对上：isNull(00) + pid(00) + tid(88→d800) + queryID(-1→41) + player(0)。
- **坑② 盲发抢回合**: 旧脚本在**每个** PlayerStartsTurn 都无条件发 EndTurn(player=0)，包括蓝方 (p1, ModelAI 客户端的回合)。蓝方回合被 Python 抢发 EndTurn → server 拒 "Player is not allowed to perform this action!" + "Got false in applying 7EndTurn... fishy!" + 2 条 SystemMessage。虽然 ModelAI 自己那轮正常走完、Turn 2 也轮转了，但日志里的 fishy 拒绝是真实错误信号，不算完成。
- **正确口径**: PlayerStartsTurn 包体 = `queryID(LVarInt, 无 timer 时 -1) + player(LVarInt)`。只在 `pack.player == MY_COLOR`（自己的回合）才发 EndTurn；对方回合 SKIP，交给对方客户端（ModelAI）自主管理。EndTurn 绝不替对方回合发。
- **修复**: `py/vcmi_protocol/packs.py` 重写 PlayerStartsTurn（queryID+player 字段序 + 覆写 deserialize）; `py/p8/p8be_host_start.py` 解析 88 包体 player，加 `MY_COLOR=0` 门控; `tests/test_e2e.py` 断言 player/query_id。实机 grep `not allowed|fishy` = 0，Turn1→Turn2 两次 "successfully applied"，ModelAI 蓝方自主 TryMoveHero(40B)。离线 145/145 PASS。
- **关联**: T13.10 / P8-B 阶段2 / 踩坑 #185 / `docs/序列化协议规格.md` / 提交 `9cc08b9` / 技能 `vcmi-network-protocol`。

### 201. WSL 发行版容器空闲关停杀训练 — systemctl is-active 也会骗人 (2026-09-11) — ✅ 已修 (双层)
- **状态**: ✅ 已修复; 训练 PID 存活 14min+ 连跑多局验证
- **现象**: Hermes 侧 `wsl bash restart_train_v5.sh` 拉起训练后无日志输出; unit 每次只活 17-45s (14:07/14:27 两次 44s/49s, 14:38 起 system 级 unit 仍 17s 一停)。当时误判两层: 先怪 user-level transient unit (改 system 级无效), 再怪 vmIdleTimeout=-1 非法值 (方向也错)。
- **根因**: **发行版容器空闲关停** — 最后一个 wsl 会话退出 → WSL 终止整个 Ubuntu+systemd 容器 (非 VM!) → 下条 wsl 命令冷启动容器 → 训练 unit 随命令会话死亡。VM 层 boot_id 恒定 + uptime 连续, journal 里 15:05:07 出现整套 `Stopped multi-user.target` 关停序列但 VM 没重启 = 容器级关停实锤。vmIdleTimeout 只管 VM, 管不到发行版容器。**任何挂法 (user/system 级 unit) 都逃不掉**, 因为死的是整个 systemd。
- **处理**: 双层修复 ① Windows 侧常驻 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList '--exec','sleep','infinity'` (有活跃会话 → 容器不关停; Windows 重启后需重起) ② system 级 enabled unit `homm3-train-v5` (/etc/systemd/system, User=administrator, StandardOutput=append 到 train_loop.log; `wsl -u root` 免密装, 容器冷启动时自动拉训练)。旧 `py/restart_train_v5.sh` (user 级 transient, 坑 #195/#168) **已废弃**。
- **教训**: ① 验证训练存活 = `ps -o lstart,etime -C python` (PID 存活时长) + 日志 mtime 推进 + step 行出现, **`systemctl is-active` 会骗人** — 容器冷启动后 unit 自动拉起也显示 active, 但下一会话结束就死 ② 首局需 ~6-10min 才出第一条 step 行, "没日志"≠"没在跑", 要先分清 "进程被杀循环重启" (banner 反复出现) vs "首局未完" ③ container idle shutdown 与 VM idle shutdown 是两层, journal 关停序列 + boot_id + uptime 三件套联合定位 ④ git-bash 调 powershell 时 `$_` 会被 bash 吞掉 (Where-Object 全炸), 用 `tasklist /FI` 替代。
- **关联**: #195 (transient unit 坑, 本坑为其真解) / #168 / 知识库 09-11 训练存活机制重构章 / 任务清单 L9 运维命令 / `.wslconfig` vmIdleTimeout=2147483647 (VM 层保险, 非本坑根修)。

### 202. P8-B ChangeHost 时序：必须在 guest 连入后才发，否则静默拒绝开局永卡 (2026-09-11, 捕获脚本首跑踩) — ✅ 实锤
- **状态**: ✅ 已修 (p8c_capture_hero.py 同步 p8be 时序)
- **现象**: `p8c_capture_hero.py` 首跑 60s 全空捕获——server 日志尾部 client1 反复发 `11LobbySetMap`(10+) + `14LobbySetPlayer`, 最后 "Connection lost", 游戏从未开局。
- **根因**: 脚本在 `VCMI_client.exe` 刚 Popen 就发 LobbyChangeHost(225)→cid=2；但 client1 此时还没连上，cid=2 不存在 → server 静默拒绝。client1 随后以 guest 身份加入 → 其 host 侧 SetMap/SetPlayer 被 host-only 检查全部拒掉 (SetMap 静默丢, 见 #185 解法) → mi_loop 10s 超时空转 → 永不开局。
- **正确口径**: ChangeHost 前必须确认目标 guest 已 join = 等到**第 2 个 LobbyUpdateState(226)** (p8be 的 `client2_seen`) 才发。同坑变体: 目标 cid 必须是实际存在的 connection ID。
- **复现**: `python py/p8/p8c_capture_hero.py` (已修, 正常开局); 旧症状 = 捕获脚本报 "捕获结束" 但零 [DUMP] 行 + server 日志 SetMap 刷屏。
- **关联**: #185 (SetMap host-only) / T13.10 P8-B 阶段2 方案F / `py/p8/p8be_host_start.py` 第 114-129 行时序范本。

### 203. P8-B 阶段3 (P8-C) 数据源墙：我的英雄 OI+位置只在 StartGame 171KB 全状态, 回合窗口无独立位置包 (2026-09-11, 捕获分析) — 🟡 已分析, 待决策
- **状态**: 🟡 分析完成, 3 条路线待用户拍板
- **实锤**: ① turn 窗口 server 只广播 88/102/116/86/84/91/109 等, **不**单独发 GiveHero/ChangeObjPos/NewObject 位置包 (171KB 之后的 8s 内零 hero 位置包) ② `MoveHero.hid` = 引擎运行时 ObjectInstanceID, ≠ h3m 静态 heroID → P10 h3mtxt 静态 JSON 拿不到 OI, 走不通 ③ server 日志只在英雄实际移动时打 "OI xxx start (x y z)", 挂机玩家无记录。
- **结论**: Python 外挂要发真实 MoveHero, 必须从 StartGame(224) 的 `LobbyStartGame = StartInfo + CGameState(171KB)` 解析出 `CMap.heroesOnMap` / `CPlayerState.hero` OI + 坐标。CGameState 全量 Python 解析工程量大 (map 对象数组几百个 CGObjectInstance 模板 + 版本门控字段, 见 CGameState.h L196-225)。
- **三条路线 (改编号为阶段4/5/6)**: **阶段4 最小 CGameState 解析器** — 只挖到 heroesOnMap + hero OI 为止, 每包校验断言 (width=36/day=1), 工程中等, 收益=完整 MoveHero 闭环 **阶段5 降级最小闭环** — 阶段3 先做 QueryReply(197)+RecruitCreatures(187) 真实决策 (不依赖地图状态, 城镇 OI 可从 SetAvailableCreatures 拿), MoveHero 留阶段4 **阶段6 C++ headless client** — 直接复用 VCMI 序列化代码 (路径A), 工程量最大但零逆向风险。
- **复现**: `python py/p8/p8c_capture_hero.py` (dump 171KB → %LOCALAPPDATA%/Temp/p8c_startgame.bin, 离线分析入口)。
- **关联**: T13.10 P8-B 阶段3 / 技能 vcmi-network-protocol 路径A/B/C / #185 / `docs/序列化协议规格.md` / C++ 结构: `PacksForLobby.h LobbyStartGame` + `CGameState.h L196` + `CMap.h heroesOnMap` + `StartInfo.h L169`。

### 204. 新惩罚/事件标签上线验证陷阱：0 次触发 ≠ 未生效 + 全 log 计数跨重启污染 (09-11, T7.4 死亡惩罚首窗) — ⚠️ 方法论坑

- **状态**: ⚠️ 方法论坑 (已纠正认知, 验证套路固化)
- **现象**: T7.4 死亡惩罚 (death_penalty=-50) 上线后验证, 初查主日志 `grep -c HERO_DEATH` = 0, 险些判 "patch 未生效/白名单没进"; 同时全 log grep ZOMBIE 得 441 条, 误读为 "死亡事件在发生只是没打 HERO_DEATH 标签"。
- **根因 (三层)**:
  - **层1 日志通道矩阵**: ep_runner stdout 重定向到 `/tmp/hermes_ep_{pid}.log` (见 #122/#129), 主日志只进白名单行。`[HERO_DEATH]` 已入白名单 (train_wsl2_ppo_v2.py L194), 理论上主日志可 grep — 但**白名单在 = 触发时能进, 不保证已触发**。0 命中只说明 "当前窗口 0 次死亡事件", 不是 "patch 失效"。
  - **层2 跨重启污染**: 全 log 的 ZOMBIE 441 条是历史多轮累计 (log 经多次 resume 追加, 见 #170), 不代表当前窗口。必须按最后一次 `Loaded train state` 行号切窗 (`L=$(grep -n 'Loaded train state' f | tail -1 | cut -d: -f1); tail -n +$L f > /tmp/cur_win.log`) 再统计。
  - **层3 首窗样本性质**: 重启后 11 局全跑 T05 52X52 守卫胜局 (ep_steps=71~73, GUARD won +100), 该负载段**本就不产英雄死亡事件** — 0 触发是地图/剧本决定的, 与 patch 无关。
- **正确验证姿势 (三件套, 缺一不可)**:
  1. **代码在位** (静态): `grep -n "death_penalty\|HERO_DEATH" ep_runner_one.py train_wsl2_ppo_v2.py` — 确认 argparse L127 / zombie 块 L1213-1222 / 白名单 L194 三处全在;
  2. **窗口内触发计数** (动态): 切窗后 `grep -c "HERO_DEATH" /tmp/cur_win.log` = 当前窗口真实触发数; 0 触发且全局为守卫胜局 → 判据 1 (死亡局 r 转负) **暂不可验**, 不是失败;
  3. **判据可验性声明**: 每个观察判据标注 "当前窗口是否有触发样本", 无样本的判据挂起等下一窗口, 不得用 0 命中反推 "未生效"。
- **教训**: ① 新增事件标签上线, 验证第一步是查 "当前窗口是否存在该事件的触发条件" (本例 = 有英雄死亡局吗), 再谈 grep 计数 ② 0 命中三义性: 未生效 / 生效但0触发 / 窗口错 — 必须用代码在位 + 窗口样本性质区分 ③ 全 log 统计必切窗 (#170 行号法), 跨 resume 计数无效 ④ 回退线 (接战率/avg_r) 有样本先验证, 事件判据无样本则挂起, 两者不混。
- **关联**: #122/#129 (日志通道矩阵) / #170 (多 resume 切窗行号法) / #195 (C 方案 capture proxy, 本条正交) / 知识库 T7.4 章 / 方案 `docs/方案_T74_死亡惩罚_20260910.md` §5 观察判据。

### 205. 外部客户端发非法 entity 字符串可炸服 — retrievePack 未捕获 IdentifierResolutionException (2026-09-11, P8-C Recruit 测试踩出) — ✅ 已修
- **状态**: ✅ 已修 (vcmi 1c3be8d030): `CVCMIServer::onPacketReceived` 对 `retrievePack` try/catch (`IdentifierResolutionException` + `std::exception`) → 丢弃恶意包并 log, 不再 Disaster。
- **现象**: Python 外挂发 `RecruitCreatures(187)` 带 placeholder `crid="<ref510>"` → server "Disaster happened" 全服崩溃 (dump 落盘)。
- **根因**: `EntityIdentifierWithEnum::serialize`(!saving) → `CreatureID::decode("<ref510>")` → `resolveIdentifier` 尾部 `throw IdentifierResolutionException` → 异常穿透 `GameConnection::retrievePack` 直达顶栈。任何 wire 内 entity-string 字段 (CreatureID/HeroTypeID/SpellID/BuildingID? BuildingID 是 StaticIdentifier LVarInt 除外) 都可被外部客户端用于炸服 — **联网对战安全漏洞**。
- **坑中坑**: `SetAvailableCreatures(112)` 的 CreatureID 字符串带跨包去重 (负数 ref 引用 171KB StartGame 里首次写入的字面量), 外挂侧单包解析无法还原 → 招兵 crid 来源 = 新增 `[SRV-DIAG] TOWNAVAIL` (build 成功后 dump `town->creatures` 各级 jsonKey)。
- **字段序修正 (同窗)**: `BuildingID` = `StaticIdentifierWithEnum` → wire LVarInt 数字 (非 string); `HeroTypeID` = `EntityIdentifier` → wire string jsonKey; `SetAvailableCreatures(112)` = tid + `vector<pair<ui32, vector<CreatureID>>>`。
- **关联**: #206 (SRV-DIAG 路线) / `CVCMIServer.cpp onPacketReceived` / `EntityIdentifiers.cpp resolveIdentifier L171` / 脚本 `py/p8/p8c2_town_chain_probe.py`。

### 206. P8-C 数据源墙第四路线 = SRV-DIAG server 侧注入, 免解析 171KB (2026-09-11, MoveHero 闭环实机 PASS) — ✅ 已实施
- **状态**: ✅ 落地并实机验证 (vcmi commit bc3e124fa2 + 主仓 7967511)
- **方案**: 不解析 StartGame blob, 改在 `CGameHandler::start` (`!resume` 分支) `fprintf(stderr, "[SRV-DIAG] HERO OI=%d owner=%d pos=%s", ..., hero->anchorPos().toString())` 逐英雄 dump → Python 外挂 tail server 日志拿运行时 OI+owner+锚点坐标。零逆向、零包解析、跨图通用。
- **坑中坑 (字段序)**: `TryMoveHero(109)` wire 序 = **id + result + start(int3) + end(int3) + movePoints + fowRevealed(vector) + attackedFrom**, 非直觉 id+start+end+result; 读错会把 SUCCESS(1) 当 FAILED(0) (离线 test_e2e 两侧同错自洽通过, 实机 server trace 对拍才抓出, 与 #199 同型坑)。
- **MoveHero 语义**: path = 锚点坐标序列, 每步须与英雄当前位置 8 邻域相邻 (`areNeighbours` 检查), layer=0(LAND), transit=false; day1 MP 耗尽后同格移动也回 SUCCESS(=原地 no-op), 不是拒绝。
- **实锤**: red OI=350 (1,8,0)→(2,7,0) 实移 + blue ModelAI OI=732 (16,1,1)→(15,0,1) + 3 回合轮转 + PackageApplied=True + zero fishy。
- **脚本**: `py/p8/p8c_movehero_probe.py`。
- **关联**: #203 (数据源墙分析, 本条=第四路线闭环) / #202 (ChangeHost 时序) / #200 (PlayerStartsTurn 字段序) / `CGameHandler.cpp CGameHandler::start`。

### 207. Query 协议栈四层隐性缺陷 — 离线单测通过实机不可用 (2026-09-12, P8-C QueryReply 探针首跑抓出) — ✅ 已修 (全协议栈返正)
- **背景**: `test_e2e.py` 162 项 PASS, 但首跑 `p8c_query_probe.py` 6/6 全 FAIL, 且失败现象一致 (`[QUERY] X: qid=-1 (INVALID, 跳过回复)`, 但 mock server 明明下发 qid=7/12/15/42)。逐层排查后暴露 4 处协议栈隐性缺陷, 均在 `test_e2e` 覆盖盲区。
- **层 1 — QueryManager 用 type_id 代替 query_id**: `handle_query` 原实现 `qid = query_data.get("type_id")`, 把包类型号 (154/156/157/88) 当 qid 回复; VCMI 官方 `Query{queryID}` 是**所有 Query 派生包的首字段**, 与 type_id 无关。→ 改为 `qid = data.get("query_id", -1)`。
- **层 2 — 三个 Query 派生类字段序错位**: `HeroLevelUp(154)` / `BlockingDialog(156)` / `GarrisonDialog(157)` 原走基类默认序列化 (player 首字段), 但 `PacksForClient.h` 明确它们首字段是 `queryID` (`HeroLevelUp` L1308: queryID+player+heroId+primskill+skills; `BlockingDialog` L1349: queryID+text+components+player+flags+soundID; `GarrisonDialog` L1392: queryID+objid+hid+removableUnits+customTitle 版本门控)。→ 三处全部覆写 `serialize/deserialize`, 首字段改回 queryID, 与 `PlayerStartsTurn(88)` (#200 已修) 一致。
- **层 3 — parse_client_pack 扁平 vs 嵌套不一致**: 原 `parse_client_pack/parse_server_pack` 返回**扁平 dict** (`{type_id, class_name, 字段全平铺}`), 但 `QueryManager.handle_query` 和 `VCMIProtocolClient._handle_packet` 都在读 `result.get("data", {})`。→ 单测 `test_query_manager` 手写了带 `data` 键的 dict 所以 PASS, **实际 wire 层不可用**。已统一改为返回 `{type_id, class_name, data: {字段...}, raw}` 嵌套结构; `test_e2e.py::test_client_packs` 同步把 15+ 处 `result.get(field)` 改为 `result["data"].get(field)`。
- **层 4 — TryMoveHero 字段序错位**: 原占位 `source/destination/reason`, 实机 wire 是 `oid + result + start(int3) + end(int3) + movePoints + fowRevealed(vector<int3>) + attackedFrom(int3)` (PacksForClient.h; 与 #206 记录的字段序一致)。→ 覆写 serialize/deserialize, test_e2e 断言从 2 → 7 (oid/result/start/end/move_points/fow_len)。
- **qid=-1 语义补全**: `handle_query` 增加 `qid==-1 → skip 回复 + history 记 skipped=True` (VCMI 官方 `NetPacksBase.h L47-50` 明确"非实际 query, 不应回复"; PlayerStartsTurn 无回合计时器时即为 -1)。
- **回归**: e2e **167/167 PASS** (断言数从 162 → 167, TryMoveHero 覆盖加深) / `p8c_query_probe.py` 离线 **6/6 PASS** / `p8c_query_probe_real.py` 实机 **PASS(qid=-1 only, 14 回合 27 次 PlayerEndsTurn, zero fishy)** / `p8c_movehero_probe_real.py` 实机 **PASS (turns_act=4 move_accepted=9 move_failed=0)**。
- **教训**: ①单测手写 dict 会掩盖 wire 结构不一致 (与 #178/#204 同型"两侧同错自洽"坑); ②字段序 bug 必须实机对拍才抓出, 离线 mock 双方自洽通过无诊断力; ③`Query` 派生类首字段全为 queryID, 覆写基类序列化不是可选项。
- **关联**: #200 (PlayerStartsTurn 字段序) / #206 (TryMoveHero 字段序, 本条重述 packs.py 落地) / #178 (ASSERT namespace) / #204 (0 命中三义性) / 脚本 `py/p8/p8c_query_probe.py` + `py/p8c_movehero_offline_probe.py` / `py/p8/p8c_query_probe_real.py` + `py/p8c_movehero_probe_real.py`。

### 208. Query 分支 `continue` 吞 PlayerStartsTurn — server 等回合结束超时踢连接 (2026-09-12, `p8c_query_probe_real.py` 首跑实机 FAIL 抓出) — ✅ 已修 (分支内补特判)
- **背景**: 协议栈四层修复 (#207) 后, `p8c_query_probe_real.py` 实机首跑仍 FAIL — 只收到 1 条 `PlayerStartsTurn qid=-1 (INVALID, 跳过回复)` 后 `[RECV] 断开`。查代码发现 recv_loop 里 `if tid in QueryManager.QUERY_TYPES: ... continue` 分支把 `PlayerStartsTurn(88)` 吞掉, 后面的 `elif tid == 88: act_turn()` 兜底永不触发, EndTurn 永不下发, server 等我方回合结束超时踢连接。
- **修复**: 在 Query 分支里对 `tid == 88` 做特殊处理 — 无论 qid 是否 -1, 只要 player == MY_COLOR 且 not end_turn_sent, 立即 `turn_count++` + `act_turn()` + `end_turn_sent=True`。这与 #200 记录的 "PlayerStartsTurn 是 Query 派生" 语义一致, 但业务逻辑与 Query 回复正交。
- **实机复验**: turns_act=14 turn_ends(102)=27 query_received=28 (全部 qid=-1) query_reply_sent=0 bad_keywords=0 → **VERDICT: PASS(qid=-1 only)** — 无计时器场景下的官方预期行为 (NetPacksBase.h L47-50)。
- **教训**: ①Query 分支不能只写"回复/跳过"两义 — 业务事件 (回合切换) 也要消费; ②实机是协议栈的终极仲裁 — 离线 6/6 PASS 的 probe 不能覆盖"分支优先级"这类控制流 bug; ③`qid=-1` 语义 = "非实际 query, 不应回复", 不等于 "整包可忽略" — 包本身可能携带业务事件。
- **关联**: #200 (PlayerStartsTurn 是 Query 派生) / #207 (Query 协议栈四层修复) / `py/p8/p8c_query_probe_real.py` L141-151 (修复位置)。

### 209. TOWNSTALL 卡住检测 `>=` 把路径平台段（BFS plen 持平）误判停滞 → 提前 TOWN_BLOCKED 禁用城镇引导 (2026-09-12, 日志分析实锤) — ✅ 已修 (09-12 实施, 重启窗验证)
- **状态**: ✅ 已修 (09-12 L877 `>=` 改 `>` 实施 + 重启 `homm3-train-v5` 验证; 重启窗口 TOWN_BLOCKED=0 全绿)
- **背景**: 日志分析发现 `[TOWNSTALL]` 假阻塞实例 — passability mask 8 邻全 1 仍判 stall（典型 L73327：`hero=(8,7) tgt=(2,1) plen=6 block=(7,6) pas=[1,1,1,1,1,1,1,1]`）；全 log 统计 TOWNSTALL 3817 次 / TOWN_BLOCKED 460 次。排查 `ep_runner_one.py` L872-898 卡住检测核心后定位根因。
- **坑① `>=` 把"进度持平"也计停滞（主根因）**: L877 `if cur_dist >= move_stall_prev: move_stall += 1`。BFS plen 在横向移动/绕岩路径的平台段**不变**（绕岩前段曼哈顿不降反升已注明 L868，但 plen 横向移动时仍会持平），`>=` 把这种合法持平也累积进 `move_stall`，攒满 6 步即 L892 `move_stall >= 6` 触发 TOWN_BLOCKED → L893-894 `town_blocked=True` 本局禁用城优先引导。8 邻全通（pas 全 1）却判 stall 即此症状：英雄在绕岩/横移平台段被误杀。
- **坑② `dyn_blocked.add` 副作用把可通行格入黑名单**: L881-887 在 `move_stall==1` 时取 BFS 首步格 `(_bx,_by)` 加入 `dyn_blocked`（设计意图=敌方英雄等动态障碍），但平台段首步格实际是**可通行格**（pas 全 1 实证）→ 后续 BFS 重规划绕行该格，进一步拉偏路径，放大误判。
- **影响面**: 局仍正常完成（招兵/打守卫/拿分不中断），仅损失 town_visited 约 +30/局 的奖励；TOWN_BLOCKED 460 次为误判占比大头。
- **正确口径 / 修复方案**: L877 `>=` 改 `>` — 只惩罚"进度变差"（plen 增加），允许"进度持平"（平台段不再累积 `move_stall`）；代价是真卡死（原地打转）累积变慢（6 步 → 8~10 步触发），可接受。修复需 stop/restart 训练（`systemctl --user stop homm3-train-v5` 优雅停 → `py/restart_train_v5.sh` 重建，见 #195/#201），待自然 checkpoint 重启窗实施，不与其他变更同窗。
- **复现/验证**: `grep -n "TOWNSTALL\|TOWN_BLOCKED" /mnt/d/Bigdata/hero3_fresh/train_loop.log`（3817/460 量级）；修复后同 grep 预期 TOWN_BLOCKED 频次显著下降，且 pas 全 1 的 TOWNSTALL 实例不再出现。
- **关联**: #204 (0 命中三义性 / 全 log 切窗法) / #195/#201 (重启窗口径: systemd transient unit + keepalive) / 任务清单"活跃任务 6 长期观察集 TOWNSTALL 引导可达性"行 / `ep_runner_one.py` L872-898。

### 210. T7.4 HERO_DEATH 判据 1 在 T05 负载段恒 0 触发 — C 方案 proxy 与 zombie 全堵正交 (2026-09-12, 子 agent 分析) — ✅ 根因定位
- **状态**: ✅ 根因已定位（代码 + 日志双向对照），无需修复代码，需切观察窗样本池
- **背景**: T7.4 死亡惩罚三判据观察，首窗 11 局 T05 36X36/52X52 全部 `[HERO_DEATH]=0`，判据 1 (死亡局 r 转负) 无法验证。子 agent 排查 `ep_runner_one.py` L1212-L1223 + `strategic_env.py` L1117 后定判。
- **坑**: HERO_DEATH 触发条件 = `zombie_streak >= 2` (8 方向全堵, `passable.any()=False`)，与 C 方案 proxy 的 `blue_hero_killed` (blue 英雄被 red 击杀)**完全正交**（L1216 注释明确"正交"）。T05 守卫战 autofight 必胜 ([ep_runner_one.py L904](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L904))，red 英雄几乎不战死 → 无全堵机会；T06 duel 蓝英雄一死 → game_over 当步 end → 同样无机会。
- **正确口径**: 判据 1 样本池应切到 T06 72X72 duel (blue 英雄存活 → red 进攻 → 有反杀全堵机会)；blue_hero_killed 保持不计入 HERO_DEATH (避免双罚, 激励轴错窗纪律)；VCMI 引擎 standardDefeat 未落地前 `game_over==2` 判负不生效 (方案_T74 §6 远期 C++ 课题)。
- **复现/验证**: `grep -c "HERO_DEATH" /mnt/d/Bigdata/hero3_fresh/train_loop.log` 当前 = 0；切到 T06 duel 图池后观察 1-2 窗 (~100 局) 复核。
- **关联**: 任务清单"活跃任务 3 T7.4 死亡惩罚" / #204 (0 命中三义性) / `ep_runner_one.py` L1212-L1223 / `strategic_env.py` L1117。

### 211. P8-D 远程连接 `_do_connect` 调不存在的 `_socket_connect` + Windows atomic rename 失败 (2026-09-12, 实机验证抓出) — ✅ 已修
- **状态**: ✅ 已修 (commit 待 git 提交)
- **背景**: P8-D 跨机器部署脚手架 (auth + remote_connection + deployment) 本机实机验证 13/13 PASS 前需修复 2 处。
- **坑①**: `RemoteVCMITCPConnection._do_connect` 原调 `self._vcmi._socket_connect()` (VCMITCPConnection 无此方法) → 改为 `ok = self._vcmi.connect(); self._sock = self._vcmi.sock`。
- **坑②**: `StatusFileWriter._write` 用 atomic rename (先写 `.tmp` 再 rename 到 `.json`)，Windows NTFS 目标已存在时 `tmp.rename` 抛 `FileExistsError` → 改为直接 `with open(self._path, 'w') as f: json.dump(data, f)`。
- **坑③**: HSK 权限 0o600 检查在 Windows 下 `os.chmod` 不生效 (NTFS 无 POSIX 权限位) → 放宽为仅 Linux/macOS 检查，Windows 打印"跳过 POSIX 权限检查"。
- **正确口径**: 跨机器脚手架本机验证 = 启动真实 VCMI_server + TCP 探活 + RemoteVCMITCPConnection 连接 + 状态文件读写 + 部署命令构造；双机部署路径按既定口径**不用第二台真实机器**，统一用「单机双实例」实跑完成（`py/p8d_two_instance.py` 13/13 PASS：2 真实 VCMI_server 端口隔离 3030/3031 + 2 真实 ModelAI client 跨实例 + HSK 跨实例预交换 + HMAC 正负例 + 双节点状态文件，共享 fork build 无需副本）。
- **复现/验证**: `python py/p8d_deploy_probe.py --local` 13/13 PASS；双机路径用 `python py/p8d_two_instance.py` 13/13 PASS（单机双实例）；`python py/p8d_deploy_probe.py --remote <host> --port 3030` 保留可用但不再作为待办。
- **关联**: P8-D / `py/vcmi_protocol/remote_connection.py` / `py/vcmi_protocol/deployment.py` / `py/p8d_deploy_probe.py`。

### 213. P8-C 收尾 QueryReply 197 实机验证: green(NK2) runNetwork 段错误 + 8B/9B 布局疑点 (09-16, fork/1.8)
- **现象**: `py/p8/p8c_query_reply.py` 两次 clean run 均复现: green(NK2 client, cid=3) 在 server 广播 16PlayerStartsTurn #2 时 runNetwork 线程段错误 (dmesg `runNetwork[pid]: segfault at 80 ip ... in vcmiclient`), 进程消失 → server 走 SHUTDOWN (host=python 仍在但 activeConnections 减少触发) → Python 连接被 RST → 对局推进中断
- **崩溃点定位** (09-16 dmesg Code 段符号化): Code 段 `<4c> 8b a8 80 00 00 00` = `mov r13,[rax+0x80]`，rax 非 null 但 +0x80 处无效内存。`segfault at 80` = 访问偏移 0x80 字段。结合 `server/CGameHandler.h` L74 `std::unique_ptr<QueriesProcessor> queries` 与 `CGameHandler` 在 SHUTDOWN 路径析构时序 → 疑似 **QueriesProcessor use-after-free**: green 的 runNetwork 线程在第二轮 16PlayerStartsTurn 回调 `QueriesProcessor::popIfTop/addQuery` 时，server 侧 CGameHandler 已因 green 自身上一回合崩溃触发的 SHUTDOWN 释放了 queries 指针。属 fork/1.8 引擎生命周期 bug。
- **影响**: ①3.2 "对局 >=2 回合" 判据只能以 server 侧 16PST 广播次数为准 (green 存活无关) ②green 崩前最后一波 [QUERY-DIAG] 行 (qid=2/red MapObjectVisitQuery) 在 Python 连接 RST 后才被 tail 到, 197 组包回送窗口极窄 (run10 抓住 1 次, run11/12 窗口错过, DIAG 行出现时 Python 已断)
- **8B/9B 布局实测**: ①离线: 8B absent = `0000c50100010200` (isNull+pid+tid+player+req+qid+0x00), 9B present = `0000c5010001020100` (+0x01+reply LVarInt), 与 QueryReply 类字节级一致 ②实机: 8B 帧发出后 server **无 197 fishy** = 受理 (run10); C++ `BinarySerializer::save(std::optional<T>)` absent 路径 = `save(static_cast<uint32_t>(0))` 写 4B, 与 Python 1B 0x00 存在字节级不匹配疑点, 9B present 为回退候选 (回退判据 = 197 fishy 行 "applying 10QueryReply...fishy")
- **判定口径** (09-16 固化): ① bad keyword 只数 197 QueryReply 鱼线, Build/Recruit 占位 OI 的 fishy 记录不计入 ② 客户端 88 PlayerStartsTurn 包体 queryID 字段 = 上一回合 qid 残值, 真实 qid 一律以 [QUERY-DIAG] 行为准 ③ green 崩前 5s 断线后仍 tail, 抢 197 组包窗口
- **根因未闭合** (09-16 已由 #215 根治): green runNetwork 段错误原疑似 CGameHandler use-after-free, 实为 **client 框架 headless 路径 null-ENGINE 解引用** (gdb core 实锤), 非 use-after-free。修复 = 14 处 `if(ENGINE)` 守卫, 见 #215。
- 状态: ✅ 2.1/2.2 离线+实机验证 PASS; ✅ green 段错误已由 #215 根治 (vcmi-native 65515ef24); ⚠ 8B absent 与 C++ uint32 路径字节不匹配疑点 → 实机 8B 帧无 197 fishy = 受理, 9B present 为回退候选, 见 #216

### 214. RecruitCreatures(187) 构造签名: 无 bid/count 参数 (09-16)
- **现象**: `RecruitCreatures(tid=1, bid=30, count=1)` 报 `TypeError: __init__() got an unexpected keyword argument 'bid'`
- **正确签名**: `RecruitCreatures(tid, dst, crid, amount, level=0, player, request_id)` — dst=目标英雄 OI, crid=CreatureID (string jsonKey), amount=数量
- **教训**: 187 的字段序 = tid(ObjectInstanceID 源建筑) + dst(ObjectInstanceID 英雄) + crid(string) + amount(ui32) + level(si32), 与 185 Build(tid+bid LVarInt) 完全不同; 参考 py/p8/p8c2_town_chain_probe.py L110 正确用法
- 状态: ✅ 已修正 p8c_query_reply.py act_turn

### 215. green(NK2) runNetwork 段错误根因 = CServerHandler headless 路径 null-ENGINE 解引用 (09-16 修复)
- **现象**: 每次 clean run 复现 green(NK2 client, headless/testmap-onlyai) 在 server 广播 16PlayerStartsTurn #2 时 runNetwork 线程 `segfault at 80` (dmesg `mov r13,[rax+0x80]`), 进程消失 → server SHUTDOWN + Python RST
- **根因 (gdb core 实锤, 非 dmesg 符号化的 `__Vector_base<char>` 误导)**: 真实调用链 = `NetworkConnection::onHeaderReceived → CServerHandler::onPacketReceived → visitLobbyStartGame → startGameplay:697 → ENGINE->discord()`，headless 模式下全局 `ENGINE`(unique_ptr<GameEngine>) 为 **null** (clientapp/EntryPoint.cpp L297 `if(!headless) ENGINE=make_unique`)，`*discordInstance` this=null → null+0x80 (GameEngine 类内 Discord 成员偏移) = `segfault at 80`。二次崩点在 `onDisconnected → endGameplay → CClient::endGame → removeGUI → ENGINE->windows()` (Client.cpp:536, 同样 null-ENGINE)
- **修复**: `client/CServerHandler.cpp` + `client/Client.cpp` 全部裸 `ENGINE->` 解引用 (discord/windows/interfaceMutex) 加 `if (ENGINE)` 守卫 (共 13+1 处), sendRestartGame/sendStartGame 的 CLoadingScreen 双分支收进 `if (ENGINE) {}` 消除 dangling-else。重编 vcmiclient
- **验证**: 修后 16PlayerStartsTurn 广播=4 (修前=3, green 活到第3回合), 无 "Connection lost", dmesg 无新 runNetwork segfault, 无新 core。BuildStructure fishy 仍存 (占位 OI 正常, 不计入 197 判定)
- **教训**: ① dmesg `segfault at 80` 的 `80` = 解引用偏移而非函数偏移, 直接符号化 ip 会被 inlined 调用者误导, **必须 gdb core 拿调用栈** ② headless/testmap-onlyai 路径在 fork 1.8 下未做 null-ENGINE 守卫 (上游无此模式), 任何 `ENGINE->` 裸调用在此路径都是定时炸弹 ③ `startGameplay`/`endGameplay` 是 green 收 171KB LobbyStartGame 广播时必经路径, 崩点不在 NK2 AI 侧而在 client 框架侧
- 状态: ✅ 修复部署 (vcmi-native working tree, client/CServerHandler.cpp + client/Client.cpp), 已 commit 65515ef24 (mmai-ml, 本地未推)

### 216. 8B absent vs C++ save(optional) 字节不匹配: 实机 8B 无 197 fishy = 受理 (09-16)
- **现象**: C++ `BinarySerializer::save(std::optional<int32>)` absent 路径 = `save(static_cast<uint32_t>(0))` 写 **4B** uint32, 但 Python `p8c_query_reply.py` 8B absent 帧只写 **1B `0x00`** → 理论字节级不匹配
- **实机结论**: run10 发 8B absent 帧, server **无 197 fishy 行** = 受理 (197 fishy = "applying 10QueryReply...fishy")。说明 server 侧对 8B 帧的解析路径在 absent 场景下未触发拒绝 (要么 C++ actual 路径在 wire 上也是 1B, 要么 server 宽容解析)
- **未实锤**: 9B present 回退候选尚未被 197 fishy 实际触发过验证 (对局无 player timer → qid=-1 → 无 197 帧, 无 reject)。待某次对局出现 197 fishy 时回退 9B 再验证
- **教训**: ① byte-level wire 验证须跑实机 (离线字节对齐 ≠ server 实际解析行为) ② 回退判据 = 197 fishy 行, 不是 "server 没回 PackageApplied" (PackageApplied 回流时序宽, 别拿它当 reject 信号)
- 状态: 8B 已实机受理; 9B 回退候选保留, 待 197 fishy 触发验证

### 217. reasonix-cli 在 WSL 跑 Windows .exe 不通 + --dir 指 WSL 路径无效 (09-16)
- **现象**: `wsl -u root ... /mnt/d/Bigdata/Reasonix/reasonix-cli.exe run --dir /home/administrator/vcmi-native` 15s 内 `run_done ok=false num_turns=0` 退出
- **根因**: ① reasonix 是 Windows .exe (C#/.NET), 虽能从 WSL 走 /mnt/d 执行, 但其内部工作目录逻辑期望 **Windows 路径**, `--dir /home/administrator/vcmi-native` 对 .exe 无效 (Windows 文件系统看不到 WSL rootfs 路径) ② 任务文本 `$(cat file)` shell 展开在 `sh -c` 引号里被吞, 路径被转义破坏
- **结论**: 修 WSL 侧 C++ 仓 (vcmi-native), reasonix **不适用**, 走主会话手动 gdb + patch。reasonix 只适用于 `--dir` 指 Windows 路径 (如 `D:/Bigdata/hero3_fresh` 主仓 Python 侧)
- **关联**: 主仓 (Python) 侧 reasonix 可用; WSL vcmi-native (C++) 侧一律主会话手动
- 状态: 知识归档

### 228. 08-17 removeQuery 补丁的多玩家计数欠减：PvP 战斗结算永久挂起 → currentBattles 残留 → simturns 占城全拒 + 判负检查永不跑 (2026-09-14) — ✅ 已修复（H3 窗口当晚闭环）
- **现象（红败定向探针 RedLossProbe_20X20，修复前基线）**: 蓝 NK2 day1 战斗击杀红英雄 Edric 后，占红城 (0,2,0) 被引擎永久拒绝：`You cannot move your hero there...engaged in battle and simultaneous turns are still active`（`server/CGameHandler.cpp` L944，判定=`gs->getBattle(owner) != nullptr`）；探针 200 步/31s C 类截断、双方存活，**连预期的 300s A 类超时都没走到**——引擎层游戏本身就卡死了。
- **根因链（全部代码实证）**:
  1. `BattleResultProcessor::endBattle()` 按 `queriedPlayers = boost::count(queries->allQueries(), battleQuery)` 建 `FinishingBattleHelper.remainingBattleQueriesCount`：**CBattleQuery 是蓝+红共享的同一对象，PvP=2，PvE 中立战=1**（NEUTRAL 不 addPlayer）。
  2. `battleFinalize()` 每次被 `CBattleQuery::onRemoval()`（BattleQueries.cpp L70-76）调用就 `remainingBattleQueriesCount--`，**减到 0 才发 BattleResultsApplied / RemoveObject / BattleEnded（GameStatePackVisitor.cpp L1443 从 gs.currentBattles erase）/ checkVictoryLossConditions（判负！）**。
  3. 08-17 为治"嵌套查询（升级/战利品）压住 CBattleQuery → popIfTop 永久 FAIL → 查询残留"（见 BattleResultProcessor.cpp L401-405 注释），把 `endBattleConfirm()` 末尾的 popIfTop 改为 `QueriesProcessor::removeQuery()`（QueriesProcessor.cpp L68-94，任意位置强制 erase），但加了 `removalDone` 守卫 **onRemoval 只对第一个命中玩家调一次**（当时理由："多玩家查询二次触发 battleFinalize → 段错误"）。
  4. PvP 局 query 从蓝、红两栈都被 erase，onRemoval 只 1 次 → 计数 2→1 永久挂住：**BattleEnded 永不发 → gs.currentBattles 残留 → simturns 一切对红方对象的移动全拒；checkVictoryLossConditions 永不跑 → 没人会被判 LOSER**。第二方 endBattleConfirm 进来 topQuery 已空，L312 "No battle query, battle end was confirmed by another player" 返回，无人再触发 finalize。
- **为什么潜伏到现在**: PvE（打野/守城中立）queriedPlayers=1，减 1 即归零，完全正常——88015 行日志普通战斗无异常；只有 ML红 vs NK2蓝 的 **PvP 英雄交战**触发，而这恰好是 T7.4 判据 1「死亡局」的唯一样本路径：红蓝一接战引擎就半残，[HERO_DEATH]=0、败北局 300s 超时、TOWN_CAPTURE 后段卡住全部同源。战后期望的"无将无城判负"在引擎层根本没机会执行。
- **修法（不碰 libvcmi.so；改 server 源码重编 vcmiserver 可执行文件）**: `server/queries/QueriesProcessor.cpp` `removeQuery()` 恢复"每个实际持有该 query 的玩家各调一次 onRemoval"（对齐上游 popIfTop 语义；二次/重入安全性由 BattleResultProcessor.cpp L413-415 `if(finishingBattles.count(battleID)==0) return;` 兜底；removeQuery 全树唯一调用点 = BattleResultProcessor L404 battleQuery）。配套仍需 H3 .so 补丁（败北后 wait 无终局通道，见当前任务清单 09-14 晚 banner 根因 B）。
- **验证**: 修复后红败探针预期——蓝杀 Edric 后可占红城、无 simturns 报错、wait 秒回 -2、game_over=2、r 含 -200；回归 duel 红胜 go=1 / PvE 打野战正常 / 200 步 C 类截断正常。
- **教训**: ①修查询残留时改了"弹出次数"语义却没核对下游按玩家计数的 finalize——治一个卡死引入一个更隐蔽的半残；②多玩家共享 CQuery 的 onRemoval 契约 = 每玩家一次，去重只能靠被调方幂等兜底；③探针出现"和预期不同的失败类别（C 而非 A）"往往是更上游根因的礼物，必须顺着引擎报错字符串 grep 到判定条件，不能先写补丁。
- **关联**: H3 立项根因 B（wait 断链，同窗双改）/ T7.4 判据 1 回退线 / 08-17 原补丁（QueriesProcessor.cpp L68-94 + BattleResultProcessor.cpp L401-405）/ `py/gen_redloss_probe_0914.py` / `py/probe_t06_gameover.py --idle`。
- **修复闭环 (2026-09-14 当晚 H3 窗口, 先证后改一次过)**:
  - **⚠ 编译树纠正（本窗最大坑，差点改错树）**: 两棵源码树同名 `vcmi-native` / `vcmi-native-build`。先在 `vcmi-native-build` 分析，看到的是 `popIfTop` 未接线 + `removeQuery` 游离实现（header 声明注释、无调用点），据此误判"banner 描述有偏差"。最终用 **`strings <vcmiserver> | grep 'vcmi-native/server'`（168 vs 0）+ `CMakeCache.txt CMAKE_HOME_DIRECTORY` + 产物 mtime** 三者交叉实锤：**生产 vcmiserver (rel/bin, 09-11) 编译自 `vcmi-native/rel`（CMAKE_HOME=vcmi-native）；`vcmi-native-build/rel/bin/vcmiserver` 是 08-02 陈旧产物、不参与生产/训练**。`vcmi-native` 树里 08-17 补丁其实**完整自洽**（header L37 有 removeQuery 声明 + BattleResultProcessor L404 已调 removeQuery），唯一缺陷就是 removeQuery 体内残留 `removalDone` 守卫。教训：双树改码前必先判定生产编译树，看陈旧树会得出相反结论。
  - **实际改动（生产树 vcmi-native，编译目录 vcmi-native/rel，target=vcmiserver+mlclient，不碰 libvcmi）**:
    1. `server/queries/QueriesProcessor.cpp` `removeQuery()`: 删 `removalDone` 守卫 → 每个实际持有 query 的玩家各调一次 `onRemoval`（二次/重入安全由 `battleFinalize` 的 `finishingBattles.count(battleID)==0 return` 兜底；gdb 实机 PvP 二次 onRemoval 无段错误）。
    2. `ML/strategic_state.cpp`（根因 B 原计划）: `adventure_process_turn` 入口持久化 `g_ml_player_cb=userData`（原 L54 全局量从不赋值）；`adventure_wait_for_turn` spin 内每 25 拍 `shared_lock(CGameState::mutex)` 轮询 `gs.players`（跳过 NEUTRAL），存活≤1 → `fill_strategic_state` 刷终局快照 → 返回新码 **-2**。
    3. `vcmi_gym/envs/v13/strategic_env.py` `_adventure_wait`: 识别 r==-2 静默 return，让 step 走 `_read_state→game_over=2→terminated`（旧路径 -2 落入 unexpected raise → 被当 300s timeout forcing，r=0/全零 obs）。
    4. **第二处 Python 配套（修复后首验 r=-10 才暴露，非事前预判）**: NK2 shaping 分支（生产/探针都用 `use_nk2_shaping=True`）在 `_calc_reward` 提前 `return clip(reward,-10,300)`，**永远到不了非 NK2 分支的 ±200 块**；红灭瞬间 NK2 state_value 退化为有界值（实测 nk2_val=10、delta 仅 -26），-200 不可达且 -26 被 clip -10 压成 **-10**。修法：NK2 分支 return 前补显式 `game_over==1 +reward_win / ==2 -reward_win`（对齐非 NK2 分支），clip 下限 -10→-300。
    5. `py/probe_t06_gameover.py` 收尾改 `os._exit(0)`（不调 env.close()）: 真终局后 NK2 后台线程仍 makingTurn，`close()->connector.shutdown()` 的 join 触发 VCMI client 线程析构竞态 SIGSEGV（rc=139，gdb 确认崩在 close 后、非战斗/fill 期）。生产 `ep_runner_one.py` L1261 本就无条件 os._exit(0)，故**生产红败局 rc=0 不受影响**，仅探针正常解释器退出会崩，对齐之。
  - **验证矩阵（全部新二进制，rc=0 零 SIGSEGV/assert）**: ①红败 20X20 `--idle` wait **0.3s**（原 300s/卡死）、go=2、alive19=0/34=1、**r=-226.2（含 -200）**、terminated；②72X72 1v3 step16 被 NK2 推平 go=2 r=-226；③72X72 duel 带 ckpt689498 greedy step19 go=2 r=-232（当前模型仍弱于 NK2）；④PvE：日志 `CBattleQuery objType=monster → CGCreature::battleFinished RETURN` 单玩家链路正常，恢复训练后 108X108_02 首局 PvE 同样 0 assert（错误仅 MMAI 非法移动 fishy/音频资源缺失等良性历史噪音）；⑤A Viking We Shall Go.h3m（官方 144X144）headless 8 回合 10.3s 加载+存活 go=0 VERDICT=C，覆盖官方图加载与存活/截断路径。
  - **未自然覆盖（降级为生产首批观察，不阻塞）**: 红胜 go=1（三次对阵模型/无模型皆败，无法触发红灭蓝活）；但 go==1 与 go==2 共用同一 -2/READ/reward 代码路径、`==1 +200` 与成熟非 NK2 分支逐字一致，且红存活时 yourTurn 照常走 generation break（轮询仅在 alive≤1 返回 -2）；200 步满截断由 A Viking 存活路径 + 历史大量生产局佐证（alive=2 不触发 -2，wait 行为不变）。
  - **部署**: 备份统一后缀 `.bak.H3.20260914`（vcmiserver/libmlclient.so/4 个源文件/strategic_env.py）；构建 `cmake --build /home/administrator/vcmi-native/rel --target vcmiserver mlclient -j8`（产物 09-14 11:45/11:46）；vcmiserver 仅 rel/bin 一份，libmlclient.so 同步 rel/bin+build/bin 两副本（md5 一致），chown administrator:administrator；清 `vcmi_gym/**/__pycache__`；恢复训练 resume step=689938 maps=10。补丁脚本: `py/patch_h3_server_0914.py`（去守卫）/ `py/patch_h3_souser_0914.py`（.so 两处）/ `py/patch_h3_wire_0914.py`（仅陈旧 build 树接线，非生产所需）。
  - **新增教训**: ①双树/多副本环境改码前先定生产编译树（strings 内嵌路径 + CMAKE_HOME + mtime 交叉验证），陈旧树会误导；②终局信号不能只验 game_over，必须沿**实际生效的 reward 分支**核对终值（提前 return + clip 下限会静默吞信号）；③一子进程一局的 ep 模型用 os._exit 收尾是规避 VCMI client 关闭竞态的既定手段，探针/工具要对齐，否则 rc=139 假性失败。

### 230. P8-E 人机混局探针 3 客户端连 Twins 触发 server NEW_GAME 崩溃 (09-15, P8-E 实跑踩) — ✅ 已收敛为 2 客户端

- **状态**: ✅ 已修（收敛为 2 客户端拓扑，P8-E PASS）
- **现象**: P8-E 初版 4 客户端（Python host + 人类 GUI×2 + 外挂 AI）→ server "Picking random factions for players" → "Disaster happened" 崩溃。二版 3 客户端（Python host + 人类 GUI + 外挂 AI）→ 同样崩溃。`14LobbyStartGame` 广播成功但 server 随后在 NEW_GAME 初始化阶段崩溃。
- **根因**: Twins.h3m 仅 2 玩家 slot。VCMI server 的 NEW_GAME 初始化在 "Picking random factions for players" 阶段为每个 join lobby 的客户端分配玩家 slot，超出地图 max players（2）时触发 "Disaster happened"。3 客户端 = 3 个 join lobby 的客户端 → 超出 2 slot → 崩。
- **收敛**: 改为 2 客户端拓扑（P8-B 范式）：Python host + 外挂 AI（AI 是第 2 个 join 的客户端，占 Twins 第 2 slot）。人类 GUI 不 join lobby（不带 `--testmap`/`--serverport`，避免 `EntryPoint.cpp` L379 默认 `onlyai=true` 导致人类 GUI 也 join lobby），仅验证"人类 GUI 进程与 AI 同机共存"。判定 `srv_log_cc()>=3` → `>=2`。
- **复现**: `python py/p8e_human_mix_probe.py`（已修，PASS）；旧症状 = server log 末尾 "Player 0/1 is controlled by human" + "Picking random factions" → "Disaster happened" + crashinfo.dmp。
- **关联**: #202（ChangeHost 时序，本条是其 2 客户端拓扑的前置约束）/ Twins.h3m 仅 2 玩家 slot / `EntryPoint.cpp` L379 `VCMI_TESTMAP_ONLYAI` 默认 true / `py/p8e_human_mix_probe.py` / 知识库 P8-E 人机混局章。

### 298. batch1 三图开局随机失败静默吞局：query -1 / segfault 概率性发作，阻塞 h3m 池混合轴 (09-22 深挖) — 🔄 挂起待专项（C++ 侧 #296 族深挖）

- **状态**: 🔄 挂起（batch1 混合轴 MIX=0 回滚，纯课程图训练继续；BATCH=1 开关保留随时可启）
- **现象**: batch1 剩余 3 张（good_to_go/judgement_day/elbow_room）上线后 **100+ 局零出现**（期望 ~8 次，概率 0.9^100 级不可能）。深挖真相：**mix 分支选中它们时每局都开局失败**——`query -1` 刷屏卡 300s 或直接 segfault（同图两次测试两种死法，**概率性发作**），训练主进程 traj=None 静默 `continue`，不写 EP_TIME → 观测面表现为"零出现"。
- **排查链**: ① 数据/代码/进程 env/时序四层验证全对（_POOL_MAPS=3 张 ✓）→ 排除配置层；② 停训单跑仍卡 → 排除资源竞争；③ triggeredEvents 置空实验 → 原本就是空的，dialog 假设证伪；④ 同图重打包后从 query -1 变 segfault → **不稳定失败，非确定性 bug**。
- **定性**: #296 同族（mlclient 网络层开局状态注册缺陷），**概率性发作**。管线验收时 3 试重试掩盖了它（某次成功即 PASS）→ 137 张池图里其他图也可能带此雷。viking 能跑属幸存者。
- **影响**: h3m 池混合轴阻塞——batch1 无图可混；batch2/3 推进前必须先过此关。
- **处理**: ① 混合轴挂起 MIX=0（unit 注释留档，BATCH=1 保留）；② 纯课程图训练继续；③ 专项方向 = C++ 侧 mlclient 开局 query 注册（对比 viking[能跑] vs good_to_go[必挂] 的图差异定位触发条件——图尺寸/对象数/玩家配置三轴），或引擎侧 query -1 容错重试。
- **预研产出（09-22 深夜，零成本文件对比，专项方向已收窄）**: 4 图对比（能跑 viking 144x144/2488 obj vs 必挂 3 张全 36x36/222-366 obj）发现**英雄来源三通道，必挂 3 张命中其中两条脆弱路径**：① good_to_go = **`randomHero` 占位对象 ×2**（subtype="object" 未展开，h3m2vmap 直译 H3M 随机英雄标志，训练环境无 RMG 展开 → 引擎注册悬空）；② elbow = **`randomTown` ×8** 同类占位；③ judgement = mainTown generateHero 双方锚点 (4,34)/(34,33)——需验证锚点处是否有本方城（warm 型同族嫌疑）。viking 能跑 = 英雄走 **predefinedHeroes 显式定义**（sanitize 曾清洗其 50 处 availableFor）+ 无任何 random 占位依赖。**sanitize v3 方向明确**：randomHero 对象替换为具体英雄 subtype（core:heroId）/ randomTown 替换为具体城 / mainTown 锚点无本方城造城（v2 已有）。judgement/elbow 具体死法待引擎日志验证（各跑 1 局取证）。
- **教训**: ① **采样命中期望与实际偏差超数量级时，先怀疑"选中后静默失败"**——训练循环 `traj=None continue` 是无痕吞局点，观测脚本只看 EP_TIME 会完全失明；② 概率性失败被"重试机制"掩盖后进入生产，爆雷时已是多层下游（管线 3 试 → 池 → 训练混合 → 零出现），根因定位要跨 4 层回溯；③ 同输入两次运行不同死法（query -1 vs segfault）= 非确定性问题，单次复现无意义，须统计成功率。
- **关联**: #296（同族定性）/ #294（sanitize v2）/ `py/_watch_b1_rest.sh`（捕获脚本暴露零出现）/ `py/_strip_te_test.py`（dialog 证伪实验）/ 知识库 **09-23 #298 定谳章**（机制链全文+复现表+修复方向）
- **09-23 专项复现定谳（`py/_298_repro.sh`/`_298_repro2.sh`，停训窗 5 局取证）**: red=StupidAI+蓝 MMAI_RANDOM 配置下 **4/4 图全挂 300s**（good_to_go×2: 5-17 步/313-327s；judgement: 3 步/311s popFAIL×7；elbow: 1 步/310s 开局即卡；**viking 对照也挂**——Exchange dialog q=1 恒挂 88 次）。**"viking 幸存"认知被推翻：幸存与图无关，与 red=ML 模型配置相关**（训练配置下 viking 实跑过 250 步两局）。
- **机制链（源码+日志双实锤）**: 蓝方（MMAI_RANDOM 底层 = NK2 AIGateway）英雄相遇/visit 城 → 引擎发 Exchange/Garrison blocking query（`CGarrisonDialogQuery` 挂 BLUE 栈顶，run1 栈 dump: HeroMovement qid=21 + MapObjectVisit qid=22 + **GarrisonDialog qid=23** 三层叠压）→ NK2 应答走 `executeActionAsync` **异步**（AIGateway.cpp:587/635），主循环卡住时 `selectionMade` 永不下发 → `[ML-wait] q=1` 恒挂（AIGateway.cpp:1583）→ 蓝方回合永不推进 → adventure_wait 300s 强停 → traj=None 静默吞局。同形态死锁 08-17 已有前科（CGameHandler.cpp:3512 ML fix 注释："写锁竞争 → 死锁 → Exchange 查询永不关闭 → AIStatus q=1 永久"）。`Cannot answer the query -1`（#299 降噪对象）= MMAI AAI.cpp:694 对通知型 dialog（askID=-1）直接 selectionMade 的伴随症状，非病因。
- **修复方向（下窗拍板，按侵入度排序）**: ① Python 旁路防静默——ep_runner 对 adventure 300s 吞局加 `[EP298_SWALLOW]` 打点进白名单（低成本立即可做）；② 转换层——sanitize v3 清城 garrison 驻军/定型 randomTown+randomHero（消除 dialog 触发源，零 C++）；③ 引擎 C++（mlclient 不违铁律）——NK2 showGarrisonDialog/showBlockingDialog 应答同步化（对齐 AAI 同步 selectionMade 模式）或查询栈看门狗强制 removeQuery（QueriesProcessor 已有 ML fix 通道）。
- **残留未知**: 训练配置（red=ML 模型）下 viking 能跑通 dialog 而三图挂——ML connector/模型路径参与查询结算的具体机制未定位（ML-wait 打点在 NK2 AIGateway，connector 侧 query 管理逻辑参与方式待下窗带模型复现分离变量）。
- **09-23 S 精准修复部署（用户拍板 T+S 组合）**: **第二创建点实锤**——`CGarrisonDialogQuery` 有两处创建：makeGarrisonDialog:3507（已有双层 AI 自动应答 fix）+ **heroExchange:1582 英雄相遇（无任何保护）**。NK2 应答链：`heroExchangeStarted` 回调 → executeActionAsync 异步 → pickBestCreatures + answerQuery(0)（AIGateway.cpp:263-283），主循环卡住时永不下发。**patch**（`py/patch_298_heroexchange.py`，备份 .bak_298_0923）：heroExchange 加 bothAI 判断——AI 间相遇不弹 dialog 不建查询直接 return（保留 useScholarSkill；放弃 NK2 pickBestCreatures 军队合并，训练语义影响小）。重编 vcmiservercommon+mlclient（libmlclient.so md5 c7547f90→36b9769f，rel/bin 原位部署，build 树无副本）。
- **S 修复验证（s300×4 + s600×2）**: ① good_to_go **卡死→推进收局**（修复前 17 步/327s 卡死吞局 → 修复后 28 步/340s rc=0 自然收局 r=-6.1，qid 23→795 局面大幅推进）✅；② elbow 1 步即卡→31286 行活跃推进 ✅ 改善；③ **[EP298_SWALLOW] 打点首次实战触发** ✅（E 路线验证通过）；④ 残留慢速 ~12s/步（比间歇性慢速前科 4-8s/步更慢）= 独立轴非本次 dialog 卡死；⑤ **judgement boot hang 2/2**（5121 行卡 TERRAIN 段，adventure 未进，boot_timeout=120 未触发）——与 patch 无关（patch 只在运行期相遇路径），疑似 #212 reset 竞态同族，下窗单独定位。
- **结论**: S patch 保留（实证改善 + 课程图不受影响：训练 9000+ 局 exchange 从未卡死，patch 仅去掉蓝蓝相遇的军队合并机会）；**T（sanitize v3 定型随机对象/清驻军）视混合轴复活后实测决定是否追加**；混合轴 MIX=0 恢复时点 = 下窗观察首局 batch1 图是否出现 EP_TIME。
- **09-23 看门狗兜底上线（judgement boot hang 专项）**: **根因定位**——`bootTimeout=120` 在 threadconnector 只包 **cond2**（client 等 server 启动完成，L567），#296 实锤的 **cond1.wait 无超时**在管辖外 → boot hang 时子进程不死（600s+），主进程 `proc.wait(15300s)` 停摆 4.25h 风险。**修复**（`ep_runner_one.py`，即时生效无需停训）：daemon 线程滚动看门狗——400s 无 kick → `os._exit(43)`（任意线程直接系统调用退出，绕 GIL/C++ 栈——SIGALRM handler 在 C++ 调用栈中不执行不可靠）；400s = adventure_wait 300s 正常内部超时 + 100s 余量（C8.5 蓝方回合 15-60s / OBS-1 战斗 300s fuse 均覆盖）；kick 链 = 启动 + reset 后 + 每步后（唯一 env.step 调用点 L1378）；rc=43 → 主进程 `ep_rc!=0` → 崩溃局归档 + return None（吞局有痕，接入现有崩溃处理零新增）。
- **看门狗冒烟（judgement 单局 04:18）**: **30 步/26s rc=0 正常跑完**（r=-85.0，61210 行活跃日志）——boot hang 未复现（确认概率性竞态）+ 看门狗零误杀 + **四图全部恢复运行能力**（S patch 后 good_to_go/elbow/judgement/viking 均可完整跑局）。残留 = 慢速轴（12s/步独立轴）+ boot hang 概率性发作（看门狗兜底，CRASHLOG 取证积累样本）。
- **⚠️ libvcmi.so 重编归因勘误（09-23 事实核查）**: L1545 条目初判"并行会话重编 libvcmi.so"——**经 mtime/构建日志核查实为本会话 cmake 连带**：`cmake --build rel --target vcmiserver mlclient` 构建窗 03:09-03:10 与 libvcmi.so mtime=03:09 吻合，构建日志含 `Built target vcmi`（依赖链连带重链）；L1545 引用的 `py/patch_298_heroexchange.py` 亦为本会话文件。**无并行会话操作引擎**。铁律影响评估：libvcmi.so 虽连带重链，但本会话源码改动仅在 `server/CGameHandler.cpp`（vcmiservercommon，链进 vcmiserver/libmlclient），**libvcmi.so 源码集未动**，产物内容变化仅为构建时间戳/链接元数据级，功能等价；md5 7a2b906e（重编后）已登记。教训：**cmake target 的依赖链边界要先 `cmake --build --target help` 或看 dependency graph 确认，"target 未含 X"不等于"X 产物不动"**。
- **09-23 冻结源定谳（gdb 全线程栈，根因不是 dialog）**: 用 `py/_298_freezedump.sh`（字节增长检测冻结 → 冻结窗内 `/proc` 线程态 + `gdb -p <engine_pid> -batch -ex 'thread apply all bt'`，17 线程）拿到铁证——**红方 MMAI(AAI) 与蓝方 NK2 两条 AI 线程同形卡在 `CClient::sendRequest(item=1414/1415)` 的 `ThreadSafeVector::waitWhileContains`**（← `CCallback::endTurn` CCallback.cpp:93 ← `yourTurn` ← `visitPlayerStartsTurn` NetPacksClient.cpp:952 / ← `AIGateway::endTurn` ← `makeTurn` AIGateway.cpp:802），而 **`runServer` 空转在 `do_epoll_wait`** → **死锁：两条 AI 的 EndTurn 永不被 realize、服务器不推进**，主线程卡 ctypes `adventure_wait` → 300s 超时。**前兆**：`[ML-q] popIfTop FAIL ... 19MapObjectVisitQuery qid=2662 affecting player BLUE, top=null`（服务器侧查询栈不一致 → 等一个永不到来的应答）。**结论：与 `CGarrisonDialogQuery`/heroExchange 无关**（解释了修复②对冻结无效）。**修复方向**：① 服务器侧查询栈看门狗（`top=null`/`popIfTop FAIL` 时强制清理推进）② 根因查 MapObjectVisitQuery 为何在 top=null 被 pop（同族：08-17 `removeQuery` PvP 计数欠减）③ AI 侧 `endTurn` 走 `waitTillRealize=false`（解死锁但放松回合序）。**工具坑**：`timeout $PY ... &` 的 `$!` 是 **timeout 进程**，须 `pgrep -P $!` 取引擎进程（首轮抓错只有 13 行栈）。
- **09-23 收官（4/4 全绿，两个故障全定性）**: **勘误上条的"前兆"**——`popIfTop FAIL top=null` 经 `patch_298_stacktrace.py` 栈打点定谳为**无害的重复 pop**（`objectVisited` 尾部又 pop 一次已被暴露链出栈的查询），**不是冻结原因**；冻结前查询栈是干净且 depth=0。真正两个独立故障：① **网络线程自锁**（如上条 gdb 铁证）→ 方案1 `patch_298_netthread_fix.py`（`CClient::onNetworkThread` + 网络线程内跳过 `waitWhileContains`）；② **upgrade 死循环**（被冻结掩盖）：`AIGateway::makePossibleUpgrades` 的 `do{...upgradeCreature()}while(hasUpgrades())` × `CGameHandler::upgradeCreature:2578` 拒绝 → 客户端/服务器状态分歧永久重试（10 万+/20MB、2.4GB 日志、仅 1 步；前提 = 共享标志 `cc->waitTillRealize=false`）→ `patch_298_upgrade_probe.py`（打点 + **熔断 cap 8**）。**验证 4/4 全绿**（30 步 / 24-39s / rc=0 / swallow=0 / timeout=0，此前 4/4 rc=124）。**⚠ 漂移疑点**：方案1 跳过路径健康局 0 次触发 → 冻结消失精确归因待对照实验。**开 MIX 后盯 `[ML-upg] BREAK`**。细节见知识库 09-23「冻结源修复 + 4/4 全绿」节。
- **09-23 漂移取证（收官窗口，归因未钉死的根因找到一半）**: WSL `~/vcmi-native` 工作区相对 HEAD 有 **3028 文件 / 79959+ / 73473- / 5074 hunk** 未提交（含整个 `ML/` 目录、`MLBot.cpp` 639、`AINodeStorage.cpp` 641 等）→ **`.so` ≠ 已提交源码**——"重编带入未知改动"不是猜想而是**事实**。**⚠ 勘误**：先前记的"6 文件 / 508+/214-"是误报（`git diff --stat` 带了 6 文件 pathspec，只统计子集）。**入库纪律**：只提已分类的 6 文件、显式标注两处 08-17 回退；~3000 文件另起专项，勿 `git add -A` 全提。另：`BattleResultProcessor.cpp` 的 08-17 `removeQuery` 修复在工作区被回退成 `popIfTop`，但 `.bak_stk298`（09-19）已是 `popIfTop` → 该回退**早于本次重编**，不能直接当修复源（`patch_298_stacktrace.py:81` 锚点即 `popIfTop`，打点不产生回退）。**对照实验设计 + 去留倾向**见知识库 09-23 节。
- **09-23 排查"本地修复有没有被冲掉"的可靠方法（可复用）**: 本地 ML 修复以工作区改动形式存在，上游同步会静默覆盖。**两道交叉判据**：① **标记计数差**——`git grep -c '<标记>' <原HEAD>` vs 工作区逐文件对齐（标记取 `ML fix`/`C8.5`/`ring6`），出现净减即可疑；② **中文注释扫描**——`git diff` 删行中筛 CJK（上游注释是英文，中文注释≈本地修复），逐行核是否只是重构/搬家。**坑**：`git grep -c` 计数会因「同文件新增一条、删掉一条」互相抵消（CGameHandler 3→4 掩盖了 182 行丢失），**必须配 `git show <HEAD>:<file> | grep -n` 看具体行号**，不能只看计数。**另一坑**：判"丢失"要区分「注释丢」与「逻辑丢」——`CQuery.cpp` 的 08-17 去重修复注释被删，但上游自己加了 `// prevent duplicates`，**行为保留**，只看 grep 会误报。**⚠ 该判据的盲区（当日即踩到）**：它只认标记/注释，**"纯代码改动、注释不变"的修复查不出**——`QueriesProcessor::removeQuery` 的 09-14「删 `removalDone` 守卫」正是此类（注释原样保留，只删了代码），两道判据都漏过，后经逐函数比对才抓到。**修正结论：真丢失 = 三处**（`CGameHandler` levelUpHero、`BattleResultProcessor` 调用点、`QueriesProcessor` 守卫），均已登记 `py/ml_patch_check.py`（第三项用**反向判据** `expect=absent`）。
- **09-23 竞态类修复的验证纪律（血泪）**: 「单样本 4 图全绿」**毫无判别力**——A/B 实测 `elbow_room` **基线（未做任何新修复）就 4/6 异常**（2×rc=139 SIGSEGV + 2×rc=124 300s 超时），而 07:28 那次单样本 4/4 绿被当成"冻结消失"的铁证，**结论直接错**。**正确姿势**：① N≥4 重复跑 + 记逐图复现率（工具 `py/_298_repeat.sh`）；② 任何"修好了竞态"的结论必须有**基线对照**（回退修复重编再跑同 N 局）；③ 崩溃栈用 `py/_298_crash_gdb.sh`（gdb 前台跑，命中 SIGSEGV 自动 `bt`+全线程栈）——注意崩溃可能**只在非 gdb 下复现**（gdb 下 6 局全过），故 gdb 单跑不能反证"没问题"。
- **09-23 夜间定谳三条（用户拍板登记，#298 收官口径）**: ① **冻结仍需真修**——07:28「4/4 全绿 = 冻结消失」**已被 A/B 证伪**（`elbow_room` 基线即 4/6 异常），**AI EndTurn realize 死锁仍在**（红 MMAI/AAI 与蓝 NK2 两条 AI 线程同形卡 `CClient::sendRequest` 的 `ThreadSafeVector::waitWhileContains`，`runServer` 空转 `do_epoll_wait`）。修复方向三档见知识库 09-23 章：① 服务器侧查询栈看门狗（`top=null`/`popIfTop FAIL` 强制清理推进，治标直接解死锁）② 根因查 `MapObjectVisitQuery` 为何在 `top=null` 被 pop（08-17 `removeQuery` PvP 计数欠减同族）③ AI `endTurn` 走 `waitTillRealize=false`（解死锁但放松回合序）。三套补丁的**对照实验**（只回退补丁、重编、同 4 图 N≥4 轮）排下个自然停训窗，**不打断观测窗**。② **偶发图登记**——`elbow_room` / `a_viking` 约 **33% 概率 rc=124（300s 超时）/rc=139（SIGSEGV）**，**与本次改动无关**（A/B 基线同量级：基线 4/6 vs 恢复后 3/6）。是否暂移出 MIX 池待拍板（`a_viking`×2 已于 09-22 摘除 `batch:1→99`；`elbow_room` 仍在 `batch:1`，`elbow_room_allies` 在 `batch:2`）。③ **验证纪律升级为硬规则**——竞态类结论**强制 N≥4 重复 + 基线对照**，单样本通过不算数（同上条）。
- **09-23 数据核查勘误（`a_viking` ×2 的归属）**: 任务清单/知识库 09-23 收官条记「重启后实采到池图 `a_viking` ×2（MIX 生效实证）」——**归属错误**。日志逐局解析实锤：该两局位于 **step=889517 / 905401**，而 09-23 重启 resume 起点是 **step=948241** → 属 **09-22 窗**（MIX 首次上线、`a_viking` 尚未摘除）。**09-23 重启后实际只跑 17 局（948241→951689），池图 0 局**（MIX=0.10 期望 ~1.7 局，`0.9^17≈0.17`，样本不足以判异常，也**不能**算"零出现复发"）。→ **MIX 是否真在按 `BATCH=1` 采样仍无实证**；下窗开 MIX 后先验「池图 EP_TIME 出现率 ≈ MIX 值」，再评估偶发图的实际吞局成本。工具：日志解析 `grep '\[EP_TIME\]' + 'stepNNN avg_r'` 配对定位所属窗。
- **09-23 `shutil.copy2` 保留旧 mtime → rollback 后重编是空操作（差点污染 A/B）**: 补丁脚本用 `copy2` 做 `.bak`/回滚，`copy2` **连 mtime 一起复制**，回滚后源文件 mtime 比 `.o` 还旧 → `make` 判定无需重编 → **`.so` 与源码不一致而 md5 不变**（本次实测：回滚后重编 md5 仍是补丁版，`touch` 后才变）。**修法**：回滚路径加 `os.utime(p, None)`；推而广之，**任何"改源码→重编→验"的流程，改完必须确认构建日志出现 `Building CXX object <目标文件>`**，只看 `Built target` 不算数。

### 299. 'Cannot answer the query -1!' 实锤: lib CCallback 非 mlclient + Popen 层 grep 降噪 (09-23)

> 编号说明: 本条原编 #298, 与 WSL踩坑点.md 既有 #298 (batch1 三图开局随机失败, 09-22) 冲突, 09-23 改号 #299。
- **现象**: hermes 日志每局 ~498 行 `ERROR Cannot answer the query -1!` 刷屏 (0.5 行/秒, TBB worker N + runNetwork 线程标签交替), 无连锁报错 (Can not end turn / fishy / Disaster / THREW 全 0), 训练链路不受影响 (主日志 EP_TIME 全 err=no)
- **#296 勘误**: 原记录归因为 "mlclient 网络层 runNetwork 开局查询注册" — **实际报错点在 `lib/callback/CCallback.cpp:53`** (`CCallback::sendQueryReply` 收到 `QueryID(-1)` 时 `logGlobal->error`)。`runNetwork`/`TBB worker` 只是调用线程标签, 不是报错位置。`CServerHandler.cpp` 的 runNetwork 是 mlclient 网络线程, 但 `CCallback` 在 **libvcmi.so** 内 (lib/callback/), 重编 libmlclient 不影响该报错
- **方案A 降噪 (Popen 层 grep -v 管道, 零 C++ 重编)**: `train_wsl2_ppo_v2.py` 的 `Popen(cmd, stdout=open(ep_log,"w"))` 改为 `Popen(cmd, stdout=PIPE)` + `Popen(["sh","-c","grep -vE 'Cannot answer the query -1' || true"], stdin=proc.stdout, stdout=open(ep_log,"w"))`。C++ `std::cerr` 经 Popen `stderr=STDOUT` 合入 stdout → 底层 pipe → grep 按行过滤 → 写 ep_log。验证: fd 1/2 由 `hermes_ep.log 文件` 变 `pipe:[inode]`, 日志 Cannot answer 0 行, 其他 14488 行全保留, EP_TIME err=no
- **为什么不用 Python 层过滤**: VCMI `logGlobal->error` 走 C++ `std::cerr` (CLogger.cpp L412), 不经过 Python `sys.stdout`; ep_runner 内 `sys.stdout = _FilteredStdout()` 无效 (C++ 底层 fd 绕过 Python 对象)。必须 shell 管道层过滤
- **铁律兼容**: 改 Python 侧 Popen 管道配置, 零 C++ 重编, 零 .so 改动
- **回退**: 把 train_wsl2_ppo_v2.py 的 grep 管道换回 `stdout=open(ep_log,"w"), stderr=subprocess.STDOUT` (2 行)
- **扩展**: 后续发现其他刷屏良性噪声 → 追加 grep -vE 模式 (正则 `|` 分隔或多次 -v)
- 状态: ✅ 降噪部署 (Popen 管道, 09-23), 训练正常推进 ep=2 主日志全 err=no

### 300. (已证伪) ~~池图开局故障的**误判条目**：「#297 同族概率性并发竞态」（09-24）— ❌ 已证伪（真根因见 **#308**）〔原编 #300，与下方 keepalive 条目 #300 重号；本条已作废，**保留仅为记录误判历程**〕~~

- **状态**: ❌ **已证伪**——真根因 = **#308 XDG 用户数据目录缺失导致 SIGABRT**（服务非 root 身份 VFS 打开失败）。本条结论「并发竞态 / 单进程复现不了」完全错误。
- **被证伪的论据（备查，避免重走）**:
  - ✗ 「单进程 250 步 good_to_go/judgement_day 全 rc=0 成功 ⇒ 非图缺陷、是并发竞态」——**实验身份不对**：那些单进程实验是 **root** 跑的，而训练服务是 `User=administrator`。以 administrator 身份跑 → rc=134 + `Failed to open .../good_to_go_h3m.vmap`。**身份不一致的实验无判别力**。
  - ✗ 「训练 10-env 并发才暴露 ⇒ 竞态」——**Python 侧实为串行**（同一时刻仅 1 个 `ep_runner`），根本不存在池图并发。课程图/`King_of_Pain` 正常只是恰好未触发该路径。
  - ✗ `[ML-q] popIfTop FAIL ... top=null`（数千行）被当作 #297 前兆——实为 09-23 三套补丁的**正常打点**，与本故障无关。
- **仍有效的部分**：MIX 采样机制本身正常（`[MIX_TRACE]` 实证 roll/mix/pool 全对，见知识库 09-24 章）；`trade BREAK` strings 命中法可查 .so 修复是否编入（`py/_check_tradecap.sh` 保留）。
- **教训（新增，最重要）**: **排查"服务里才崩"的问题，第一件事是对齐身份**——任何单进程复现必须以 `sudo -u <服务用户>` 跑；root 跑通毫无证明力。此误判的代价 = 一个引擎窗口的并发取证（方向完全跑偏）。
- **关联**: **#308（真根因，以此为准）** / #296 / #297（地下城图 mainTown 去层 → HEROSEG_EMPTY，与本故障**无关**，当时"同族"说法也是错的）/ 知识库 09-24「池图故障根因修正」章（已同步改为以 #308 为准）

### 308. 池图在训练中 SIGABRT 的真根因：服务非 root 身份下 VCMI 的 XDG 用户数据目录缺失 → VFS 打开失败（报误导性 "Permission denied"）→ `std::terminate` (09-24 定谳) — ✅ 已修（预建 XDG 链 + Maps 软链）

- **状态**: ✅ 已修（`py/setup_vcmi_runtime.sh` 预建 + `restart_train_v5_sys.sh` 调用）；同进程内 A→B 实测通过
- **现象**: `h3m_pool` 池图（`good_to_go_h3m.vmap` / `judgement_day_h3m.vmap`）进入训练后**必崩**：父进程报 `[WARN] traj 读取/解析失败 ... rc=-6`，子进程日志尾是 C++ 栈回溯。**课程图与 `King_of_Pain_h3m.vmap` 完全正常**。
- **误判历程（备查，避免重走）**: ①「并发竞态」错——Python 侧实为**串行**（同一时刻仅 1 个 `ep_runner`）；②「无 `[FILTER]` ⇒ rc=0」错——`if ep_rc != 0: FILTER` 代码位于 `open(EP_TRAJ)` **之后**，文件缺失时先抛 `FileNotFoundError` 直接落 WARN，**FILTER 分支不可达**（crashlog 也因此长期为空）；③「地图内容/saveMap 格式/无 hero 对象」错——结构差异真实存在但不是崩溃原因；④「terrain_grid.bin 被 root 占」是真实隐患但非充分原因。
- **真根因（用户身份 A/B 铁证）**: 训练服务 `User=administrator`，而 **VCMI 的 XDG 用户数据目录 `$HOME/.local/share/vcmi/` 从未存在**（`/home/administrator/.local` 不存在；`/root` 侧路径恰可用）→ `CFilesystemLoader::load` 打开 `.vmap` 失败（VCMI 把路径无效**误报成 "Permission denied"**）→ C++ 抛 `Exception` → 未捕获 → `std::terminate` → **SIGABRT (rc=-6/-134)**。
  - 栈：`CFilesystemLoader::load ← CFilesystemList::load ← CMapService::getStreamFromFS ← CMapService::loadMapHeader ← CMapInfo::mapInit ← CServerHandler::debugStartTest`
  - A/B：administrator → `ERROR Exception: Failed to open file './data/Maps/good_to_go_h3m.vmap'. Reason: Permission denied` + rc=134；root → `rc=0` + traj 写出 + `[EP_TIME] err=no`
  - 同进程内转变：修复前后同一训练进程，`rc=-6` 立即转为 `[EP_TIME] map=good_to_go_h3m.vmap steps=84 r=-189.5 err=no`
- **修复**: 预建 `~/.local/share/vcmi/{data,config}`（administrator 属主）+ 把 `$XDG_DATA_HOME/vcmi/data/Maps` **软链到运行时 Maps 目录**（`/home/administrator/vcmi-native/rel/bin/data/Maps`）+ unit 显式 `XDG_DATA_HOME`。
- **教训**: ① **守护进程以非 root 运行时，engine 依赖的 XDG/HOME 派生路径必须显式预建并 chown**——"root 能跑"不等于"服务能跑"；② VCMI 的 `Failed to open ... Reason: Permission denied` **不可当权限问题直读**（路径无效/缺失也这么报），要结合 strace/身份 A/B 判定；③ 排查"文件读不到"要分三态：**不存在 / 存在但权限不对 / 路径解析失败**，本窗前两轮只查了前两态；④ `rc=-6` 这类 C++ abort 必须**先看 C++ 栈**（`CFilesystemLoader` 段直接指向 VFS），比在 Python 侧猜快得多；⑤ 同一运行内的"修复前后"对比是最强的单样本证据（不必另建对照）。
- **关联**: #307（共享 /tmp + 粘滞位，同属"身份/权限"类）/ #306（unit 双副本漂移）/ #296（h3m 图开局）/ **~~#300~~（本故障的误判条目，已作废）** / `py/setup_vcmi_runtime.sh` / `py/sync_unit_env.sh` / `py/train_wsl2_ppo_v2.py`（EP_TRAJ PID 隔离）
- **附带修复（09-24 同窗）**: `py/sync_maps_to_runtime.py --purge` 原按"不在 MAPS 清单"删运行时图，会把 `h3m_pool` 池图当退役图**误删** → 已改为「保护集 = MAPS ∪ `maps/training/h3m_pool/*.vmap`」（池图只保护不删，不参与预检/同步循环，避免 135 张 strict 预检拖慢或误判挡住训练启动）。

---

### 309. 服务器评测农场跨地图并发 worker_crashed：多 worker 同时加载不同地图 → 共享资源路径并发读 → 堆损坏 → glibc abort（09-24 对照矩阵定谳）— 🔄 根因定谳，flock 修复待落

- **状态**: 🔄 根因已定谳（对照矩阵 + core 栈）；修复（boot flock 串行化）待落，验收 = 12 图并发崩率 → 0
- **现象**: `172.16.2.40` 的 `batch_eval_pool.py` 12 worker 各开**不同地图**时 ~42% 局 `worker_crashed`（turn=0 早死，VCMI worker 进程死掉，python 侧 recv 超时记 `worker_crashed`）。
- **对照矩阵（KTV × StupidAI，max_turns=2000，09-24 全部实跑）**:

  | 条件 | 崩率 |
  |---|---|
  | 串行 4 局 / 串行 12 局 | 0/4、0/12 |
  | 并发 4 worker（全 KTV） | 0/4 |
  | 并发 12 worker（全 KTV） | 0/12 |
  | 并发 12 worker（12 张不同图） | 10/24（~42%） |

- **根因**: **跨地图资源竞态，非并发本身、非段错误**。core（3842659 SIGABRT）栈（`eu-stack --core`）：python worker 线程 → `ML::start_vcmi()` → VCMI 资源加载（CAnimation 帧指针已花 `File name: c??\x00`）→ `malloc(): unsorted double linked list corrupted` → glibc 主动 abort。机制：VCMI 资源缓存为进程内全局单例，多 worker 同时加载**不同地图**时并发读共享资源路径（`vcmi-build/bin/data` 软链 + `Maps/`）→ 堆越界。不同图 = 不同资源集 = 触发条件；同图并发（12 worker 全 KTV）无竞态故 0 崩。
- **与 #308 的区分**: #308 是 WSL 训练侧单服务 XDG 目录缺失（已修）；本条是服务器评测农场多 worker 跨图 boot 竞态，机制不同、位置不同，独立问题。旧 #300"并发竞态"误判已被 #308 证伪，本条是**服务器侧真·并发竞态**（对照矩阵坐实，非推定）。
- **修复方向（harness 层，不动引擎）**: ① worker boot 阶段 flock 串行化（`flock` 锁 `vcmi-build/bin/data/.lock`，只锁资源加载、不锁局内运行，32 worker 并行不受影响，仅 boot ~10-20s 排队）；② 或降并发 + 每 worker 固定同图轮转。验收 = 12 图并发复测崩率 → 0。
- **附带坑（09-24 同窗，见 `docs/服务器踩坑点.md` §2.5）**: ① 服务器 `/usr/lib64/libpython3.11.so.1.0` 软链指向静态库 `.a`，gdb 读 core 报 invalid ELF header → 一律走 `eu-stack --core=`（不依赖 libpython）；② 并发评测收尾必清孤儿 `strategic_worker`（99% CPU 可烧 27min+）。
- **关联**: #308（WSL XDG 缺失，区分项）/ 踩坑 服务器 §2.4/§2.5 / `batch_eval_pool.py`（harness）/ 任务清单 S-5

### 310. 第 3 连接观战 client `--testmap` 内置「摘自己」→ 0x98 空指针崩；`--spectate` 零重编修复 (09-27, T13.11 M3 实跑踩) — ✅ 已修（--spectate 参数）

- **现象**: T13.11 M3 观战位——3 连接（Python 红 / client1 蓝NK2 / client3 观战）连 `:3030`，client3 装图后 `Disaster happened. Attempt to read from 0x98` 崩（fork client）。dmp 落盘 0 字节（fork crash handler 没写成），无 cdb 可用。
- **真因（源码静态推演 + server log 时序实锤）**: fork `--testmap` 走 `debugStartTest`（`client/CServerHandler.cpp` L875-919），装图后内置**「摘自己」** `setPlayer(myFirstColor())`（L904，注释 "Click on color to remove us from it"）→ 第 3 个 client 被摘成「未分配玩家」→ 发一条 `L14 LobbySetPlayer` 把蓝方槽**抢占**改绑自己（server log 实锤：`Player color 1 will be controlled from connection 2` 之后紧跟 `L14 LobbySetPlayer` → `controlled from connection 3`，client1 被挤成 neutral）→ client3 走默认非 slot 路径装界面读 **0x98 空指针**（与 09-10 已修的 `getPlayerState()->quests` 0x6d8 同族，fork SPECTATOR 路径又一处未判空）。
- **修复（零重编，走 fork 原生参数）**: 观战位 client 加 `--spectate`（`clientapp/EntryPoint.cpp` L171 "enable spectator interface for AI-only games"）→ 显式走 spectate 分支装 `PlayerColor::SPECTATOR` interface（`client/Client.cpp` 无 human slot 自动 spectate 段 L238-249/L289-292）绕开 0x98 未判空路径。**注意这是绕开非源码判空修**；治本=fork 那条默认非 slot 路径的 `getPlayerState()` 直链加判空再重编 client（留后续）。
- **人类 GUI 观战即用**（去 headless）: `D:\vcmi-fork-build\bin\VCMI_client.exe --testmap Maps/Twins.h3m --donotstartserver --serverport 3030 --spectate`。
- **附带勘误（#230 旧结论作废）**: P8-E（09-15）「3 客户端 join Twins → server NEW_GAME 崩」在当前 server 已**不复现**（09-16 #205 robustness 后）；M3 v2/v3 三连接对局正常开始。#230「已收敛为 2 客户端」的约束对 server 侧不再成立，client 侧观战位需 `--spectate`。
- **M3 实跑（`py/p11_m3_spectate_probe.py` v3 PASS）**: 三进程全存活 + 对局照常（红蓝交替 4 轮 + 蓝方 server 侧受控=cid2）+ 观战位日志净。
- **铁律兼容**: 零 C++ 重编、零 .so 改动、零训练面影响（fork build 隔离）；蓝方身份以 server log `controlled from connection 2` 为准（client 摘 slot 后自身 log 可能无 `will be lead by` 行）。
- **关联**: #230（P8-E 3 客户端 server 崩，本条勘误其旧结论）/ 09-10 `getPlayerState()->quests` 0x6d8 同族 / 任务清单 T13.11 M3 / `py/p11_m3_spectate_probe.py` / 知识库 09-27 M3 章
