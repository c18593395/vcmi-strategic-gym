# WSL踩坑点 — 引擎-VCMI-API

> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。

---

### 12. DATA/LCDESC 缺失 → VCMI 初始化崩溃

- **现象**: `Resource with name DATA/LCDESC and type TEXT wasn't found`

- **原因**: libvcmi.so 从 data 目录找不到游戏资源

- **解决**: data 必须指向 HoMM3 安装目录 (含 Data/H3bitmap.lod 等)



### 13. CONFIG/FILESYSTEM 缺失

- **现象**: `Resource with name CONFIG/FILESYSTEM and type JSON wasn't found`

- **原因**: config 目录为空或缺失

- **解决**: config/ 下至少放 modSettings.json、settings.json（可空{}）



### 14. g_adventure_cb lambda 导致 crash

- **现象**: 在 MLClient.cpp 的 init_vcmi() 中加 `g_adventure_cb = [](int,void*){}` 后 env.reset() crash

- **原因**: extern "C" 函数指针与 C++ lambda 的 ABI 不兼容

- **解决**: 删除 lambda，回调注册放别处



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



### 21. dlsym 找到旧版 strategic_state_update

- **现象**: `dlsym(RTLD_DEFAULT)` 在 libvcmi.so 里先找到旧版 strategic_state_update（无 P0 自分配），新版在 libmlclient.so 里不被执行

- **解决**: 改 extern "C" 直调，不用 dlsym。链接器保证找到 libmlclient.so 的正确版本



### 22. struct 尺寸不可改

- **现象**: 在 `StrategicState` 中加 `int32_t action` 字段后全量编译失败

- **根因**: strategic_state.cpp 被编进 mlclient.dir 和 vcmiservercommon.dir，两处 sizeof 不一致

- **解决**: action 放独立全局变量 `g_rl_action`，不碰 struct



### 24. moveHero 在回调链中 segfault

- **现象**: yourTurn 内直接调 cb->moveHero() 段错误

- **根因**: VCMI 在 query 回调上下文中禁止 game action

- **解决**: 先 cb->selectionMade(queryID) 回答 query（释放上下文），再调 moveHero。2026-07-27 验证直接调在 WSL2 不再 segfault——直接 moveHero 成功



### 25. "Player is not allowed to perform this action!"

- **现象**: 后台线程 asyncTasks->run(moveHero) 被服务器拒绝

- **根因**: selectionMade 在 moveHero 前调用，服务器认为玩家已非 active

- **解决**: 不要在 moveHero 前答 selectionMade。**最终架构**：yourTurn 单次 action → 直接 moveHero → selectionMade → endTurn。不需要 asyncTasks



### 26. waitTillRealize=false 对 endTurn 必要

- **现象**: endTurn 不返回，下一步超时

- **解决**: endTurn 前设 `cb->waitTillRealize = false`，发请求不等待服务器确认



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



### 30. EmptyAI 不在 AIS 列表

- **现象**: 设 adventureEnemyAI="EmptyAI" 后启动报 "Unsupported scripted AI name: EmptyAI"

- **解决**: MLClient.h 的 AIS 列表加 "EmptyAI"



### 31. canMoveBetween 不足够精确

- **现象**: cb->canMoveBetween(hero->pos, target) 返回 true 但服务器仍拒绝 moveHero

- **根因**: canMoveBetween 只做地形层面检查，服务器有额外游戏规则检查（visitable objects 等）





### 33. VCMI 内部重定向 stdout/stderr

- **现象**: 即使子进程 stdout 指向日志文件，MMAI 的 fprintf 仍不出现

- **根因**: VCMI 启动后 CBasicLogConfigurator 可能重定向 fd 1/2

- **解决**: 用 fopen("/tmp/mmai_diag.txt", "a") 直接写文件，完全绕过 VCMI 日志层



### 33. TerrainTile::blocked() 是函数不是成员变量

- **现象**: `tile.blocked` 编译报错 `cannot convert from type bool () const to type bool`

- **解决**: 使用 `tile.blocked()` 加上括号调用



### 34. TerrainTile::terType 不存在

- **现象**: `tile.terType != 5` 编译报错 `no member named terType`

- **解决**: 使用 `tile.getTerrain()->isWater()` 判断是否为水域



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



### 2. canMoveBetween 太宽松 → passability 全1

- **现象**：`obs[-8:] = [1,1,1,1,1,1,1,1]` 永远全可通

- **根因**：`CCallback::canMoveBetween()` 只查 `isBlockedVisitable()`，不查 `terrain.isPassable()` 和障碍物。且客户端 CGameState 在 yourTurn 时数据不完整

- **修复**：改用 `CGameInfoCallback::getTile(target, false)->isClear(heroTile)`，检查实际地形+障碍物



### 3. waitTillRealize=true → moveHero/endTurn 卡死

- **现象**：`cb->moveHero()` 和 `cb->endTurn()` 永远不返回

- **根因**：`cb->waitTillRealize = true` 时，moveHero 同步等待服务器确认。被拒绝的 move 不返回确认 → 线程卡

- **修复**：调用前 `cb->waitTillRealize = false`，调用完恢复



### 4. Non-red 玩家不处理 → step 超时

- **现象**：step() 等待 30s 后 timeout

- **根因**：red endTurn 后 game 调 blue/tan 的 yourTurn，但旧代码用 asyncTasks 异步处理且不 endTurn → 卡住

- **修复**：`AAI::yourTurn` 对非红方立即 selectionMade + doEndTurn（设 waitTillRealize=false）



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



### 3. adventureAlliedAI/EnemyAI 全被改成 Nullkiller2 → red 失联

- **现象**: env reset 后 adventure_wait 超时；日志显示 `NK2AI::AIGateway::makingTurn` 处理 red 的回合（"Player 0 (red) ended turn"）

- **根因**: MLClient.cpp 把 `adventureAlliedAI` 和 `adventureEnemyAI` 都写成 "Nullkiller2"（C8.1 改的）→ **所有玩家**冒险 AI 都是 NK2 → MMAI 的 AAI::yourTurn（模型注入）永不触发

- **修复**: `adventureAlliedAI="MMAI"`（red 注入路径），`adventureEnemyAI="Nullkiller2"`（blue/tan 真 AI 对手）



### 4. build 目录 ServerPlugin 缺野怪保护 → NK2 打野 abort

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



### 12. TerrainTile::isClear() 无 from 参数 → segfault (2026-08-01)

- **现象**: 采集/训练 reset 后静默 segfault（无 traceback, 进程 Aborted）

- **根因**: `tile.isClear()` 默认 from=nullptr → VCMI 内部 `from->getTerrain()` 解引用 null → 崩

- **定位**: gdb --batch -ex run -ex "bt" --args python collect_bc.py（拿 C++ 栈: fill_exploration → isClear → entrableTerrain → getTerrain this=0x0）

- **修复**: `tile.isClear(&from_tile)`（传英雄所在格, 对齐 passability 写法）

- **教训**: VCMI 的 isClear(from) 的 from 必须有效; 新代码调用前查 API 默认参数



### 14. VCMI settings 写读层不一致 → AI 分配失效 (2026-08-01)

- **现象**: red_adventure_ai="Nullkiller2" 但 Opening 全是 MMAI, act=-1（MMAI 的 send_action(-1)）

- **根因**: `Settings(settings.write({"ai",...}))` 写 session 层, Client.cpp `settings["ai"][...]` 读配置层 → 写入不生效（读默认 MMAI）。C8.5 训练没暴露（默认 MMAI 恰好正确）

- **修复**: 跨 .so 全局 `extern "C" char g_adventure_allied_ai[64]`（MLClient strncpy 写 / Client.cpp 读, g_ml_player_cb 同模式）

- **教训**: 验证 settings 写入生效用运行时日志（friendlyAI/playerAI 打印的是 combat/冒险 AI 别混淆）; 写入非默认值才暴露层问题



### 17. 动作 8 INTERACT 从未实现 — 文档与代码脱节 (2026-08-15)

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





### 21. bulkSplitStack 是军队内部平铺, 不能跨英雄转移 (2026-08-15 H.6)

- 现象: 设计文档写 SPLIT_ALL 用 bulkSplitStack, reasonix 调研 CGameHandler.cpp:1705 发现实现是 srcArmy==dstArmy 军队内部平铺

- 根因: bulkSplitStack 语义是"把某个槽位的兵平铺到军队内其他空槽", 参数没有跨英雄的 dst 概念

- 修复: SPLIT_ALL 改用 bulkMoveArmy(currentHero->id, nearestHero->id, srcSlot)（有 isAllowedExchange 相邻检查, 失败静默, 符合 v1 简化）

- 教训: 动作设计文档的引擎接口名未核实实现就写死; 委派外部 agent 前先核实关键 API 语义, 或让 agent 调研阶段就核对 CGameHandler 实现



### 24. passable mask 与 moveHero 目标格不一致 — 英雄模板 visitableOffset 偏移 (2026-08-16 H.8 根因)

- 现象: PPO 训练 40 局英雄位置永远不变 (107 步全在 (16,15,1)), 服务器持续报 "Cannot move hero, destination tile is blocked!"; obs passable 段标方向 5(SW) 可通行但服务器拒, 方向 4(S) 标不可通行但 NK2 实际走通

- 根因链:

  1. obs passable fill (strategic_state.cpp) 用 heroes[active_hero].pos (对象锚点) + dir 作为目标格做 isClear

  2. 服务器 CGameHandler::moveHero 检查 convertToVisitablePos(dst) = dst - getVisitableOffset() — 英雄模板 ["VVV","VAV"] offset=(1,0), 锚点与可站格差 1 格

  3. fill 用锚点+dir 算出的"可通行方向" = 服务器实际检查格 + offset → passable=1 的方向被服务器以 blocked 拒绝, 真可走的方向标 0

- 修复 (commit acc1a7f92): fill 的 hpos 改用 hero->visitablePos() (pos - getVisitableOffset()) — 站立格 + dir == 服务器检查的 convertToVisitablePos(pos+dir)

- 附加修复: fill_exploration active_hero 强制 owner==0 (防 g_active_hero 越界到 blue 槽位), 无 red 英雄时 -1

- 验证: 修复后 passable=[0,0,0,0,1,0,0,0] (方向 4=(16,16) 正确), 模型按 mask 选方向 4 moveHero 成功 (16,15)↔(16,16)

- 教训: **obs 任何位置/格子相关字段必须与服务器 CGameHandler 的目标格语义对齐** (visitablePos vs anchorPos); 验证训练环境健康的第一信号是英雄位置是否变化, 不是 vloss/avg_r



### 26. NK2 卡死根因 — Router battleStart 战斗模型加载失败 (2026-08-16 全面分析)



- 现象: NK2 无论作为 red (采集) 还是 blue (训练/复现), 每局 7-42 pairs 就 stuck; 日志刷屏 [ML-wait] battle=3 q=0 obj=1 mov=1; adventure_wait 90-120s 超时

- 根因链 (3 环):

  1. threadconnector.cpp 481/491: `Scripted(red/blue)` — blue=Nullkiller2 时 battle 模型名 = "Nullkiller2" (NK2 是冒险 AI 非战斗模型名)

  2. Router::battleStart SCRIPTED 分支只认 StupidAI/BattleAI/MMAI_BATTLEAI, 未知名 THROW → catch fallback StupidAI → 战斗仍挂 (battle 无人正确指挥)

  3. **打野 (red 攻中立) 时 neutral 无 playerID → C8.5 fix 用 baggage->modelRight (blue 模型)** → Nullkiller2 → 加载失败; 且 fallback BattleAI 在 headless 无头服务器下等待回调卡死 (MLClient.cpp 400 行注释早有记录)

- [ML-wait] 真相: NK2 的 AIStatus::waitTillFree 等 battle!=NO_BATTLE + queries 空 + 对象访问完 + 移动完 — battle=3 挂着 = NK2 在等战斗结束, 战斗永不结束 → 超时

- 修复 (router.cpp 两处): neutral 无 playerID → 直接 CDynLibHandler::getNewBattleAI("StupidAI") 自动裁决 early return; SCRIPTED else fallback BattleAI → StupidAI (BattleAI headless 卡死勿用)

- 教训: **battle 模型名 ≠ 冒险 AI 名**; neutral 战斗不能复用 blue 模型; BattleAI 无头模式不可用, 自动裁决统一 StupidAI



### 29. NK2 卡死 6 环修复链 — 6 环全闭环 ✅ (2026-08-16 晚, 死锁链另见 #30)



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

### 30. 战斗后客户端收包静默 + NK2 EndTurn 死循环 — 4 层死锁修复链 (2026-08-16 晚, gdb 实证)



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

### 31. NK2 英雄交换查询死锁 — q=1 obj=1 mov=1 永久卡死 (2026-08-17)

- **现象**: BC 采集长跑 (max_pairs>=1000) 英雄位置不变 (唯一值=2), 动作分布 90% 单一方向 (缓存假动作), 日志 [ML-wait] battle=0 q=1 obj=1 mov=1 永久 (2s/次贯穿整局, qdesc=Exchange between heroes)

- **根因链**: NK2 收到 showGarrisonDialog (英雄交换) → heroExchangeStarted 异步任务 (AIGateway.cpp:1419 executeActionAsync) 持 CGameState 共享锁 → pickBestCreatures/answerQuery 与服务器写锁竞争 → **死锁** (showBlockingDialog 已有同款 ML fix CGameHandler.cpp:1164, showGarrisonDialog 漏加) → QueryReply 永不发 → Exchange 查询永不关闭 → AIStatus remainingQueries=1 永久 → waitTillFree 卡死 → NK2 决策线程死 → 英雄不动

- **次根因**: CGarrisonDialogQuery 同阵营两英雄 addPlayer 两次无去重 → players={RED,RED} → addQuery 双重 push → popQuery FAIL 796 次 (查询栈污染)

- **修复**: 1) CQuery::addPlayer 加 vstd::contains 去重 (WSL 编译树旧版缺, D 盘已有) 2) showGarrisonDialog AI 玩家自动应答 (setReply(0)+popQuery, 同 showBlockingDialog 模式, 仅无头服务器模式)

- **验证**: All for One 图红方英雄 15-17 位置真实移动 (16,12→4,6), 动作 10 种 8 方向, 升级/移动力消耗正常; ML-wait 永久卡 120+→短暂等待; popQuery FAIL 796→0

- **后续修复 (同日)**: 战斗查询残留 (has to answer 刷屏 8867-18202 次/局) → ① expGiven 升级 AI 自动选技能 ② QueriesProcessor::removeQuery 任意位置强制移除 (onRemoval 只调一次防段错误 + 移除后触发暴露链否则 visitQuery 永不 onExposure) ③ battleResultAccepted 改用 removeQuery; env.close() embedded 卡死 (58% CPU, close 线程 5s 超时实测无效) → SAVED 后直接 os._exit 跳过, 局间 1 行间隔

- **地图坑**: Dungeon Keeper.h3m 红方 954 出生地被围 (passable 8 方向全 0, isClear=false), 卡死修复后仍动不了 → 换 All for One.h3m

- **诊断教训**: obs 大数值字段有 log1p 归一化 (H.8: movement 1560→log1p=7.353, gold→8.61), 排查 float 异常先查 obs 构建归一化段; 探针 (临时打印 state.heroes[0].movement type) 直接区分 int 结构 vs float 垃圾





## 踩坑 #32: 有头 GUI (embedded 非 headless) 与标准 client-server 的地图加载链 (2026-08-17)



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



### 34. 有头验证 08-18: WSLg 虚拟显卡无 GPU 合成 (显示无解) / 官方 Windows NK2 0x618 崩溃 / spectate 官方也崩 (2026-08-18)

- **WSLg 显示**: 本机无真实 GPU (仅 OrayIddDriver 向日葵 + MuMu 虚拟显卡) → WSLg 窗口 (X11 + wayland/SDL_VIDEODRIVER 都试) 任务栏有图标桌面无画面; EGL/MESA/ZINK 失败 + [WARN:COPY MODE]; **环境无解** → 有头验证走 Windows 原生 VCMI

- **官方 Windows VCMI (1.6/1.7.5) NK2 0x618 空指针**: All for One/Arrogance 都崩 (回合 1 NK2 初始化后, "Attempt to read from 0x618"); 我们 fork 1.8 的 NK2 修复链已修 (WSL 4 方跑到回合 4) → Windows 需源码构建 fork

- **spectate 官方也崩**: 官方 1.7.5 Linux AppImage 在 "Initializing the interface for player invalid" SIGSEGV — 官方渲染链脆弱, spectate 弃用; 玩家视角 (VCMI_TESTMAP_ONLYAI=0) 是部署形态

- **github.com 443 间歇不通** → ghproxy.net 镜像下载成功

- **AppImage**: WSL 无 FUSE → --appimage-extract 解压运行

- **~/.local/share/vcmi/Maps 的 .vmap** 使官方 VCMI 扫描卡死 (s1.vmap 解析) → 移走

- **Windows VCMI 地图源**: Documents\My Games\vcmi\Maps (158 张); 安装: D:\Program Files\VCMI (1.6) / D:\GAMES\VCMI (1.7.5 用户自装)

- **Windows 侧控制 WSLg 窗口**: user32 ShowWindow/SetWindowPos (win_force_maximize_vcmi.py); 窗口可能被移到屏幕外 (-21333)



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



## 踩坑 #72: ModelAI 战斗后回合挂死 — yourTurn 线性执行 (2026-08-19, fork+1.7.5 双验证)

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

### 167. ServerPlugin HeroPool 对称校验拒多敌课程: 1v3 及 1v7 全部无法启动 (2026-09-06)
- **现象**: alchemist 修复后 1v3 仍拒启动: `Added pool 0 of owner 0/1: default` → `ERROR Failed to launch game: Owners have differently sized pools`
- **真因**: fork 训练栈 `server/ML/ServerPlugin.cpp` pool matching — 非 randomHeroes 模式且恰好 2 owner 时, 强制双方同名 pool 英雄数相等 (T04/T05/duel 全 1v1 天然通过, 1v3 red1 vs blue3 → 1≠3 throw)
- **修复**: 大小不等降级 stdout 警告 (`pool size mismatch ... skip`), pool **名**不同仍 throw (真配错图仍可发现); **libmlserverplugin.so 是独立 SHARED 库不触"勿重编 libvcmi.so"铁律** (server/ML/CMakeLists add_library mlserverplugin SHARED; 单文件重编 -j4, cmake --build rel/ --target mlserverplugin)
- **运维**: 备份链 .bak_pool_0906 (.so+源码); 副本同步 vtest/bin + hero3_vcmi/build/bin (route-backups/vcmi-gym 为历史备份不同步); **1v7 课程前置障碍已扫除**
- 状态: ✅ 已修复部署 (1v3 真实首局 73 步 r=82.38 闭环)

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

