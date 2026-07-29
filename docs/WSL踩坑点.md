# HoMM3 战略 AI — 踩坑记录

---

## 一、编译与构建

### 1. 9p 文件系统不可用于编译
- **现象**: cmake 在 `/mnt/d/` (9p挂载) 上编译超时或极慢
- **原因**: 9p 是网络文件系统，每次头文件 include 都要走网络，预编译头(PCH)尤其慢
- **解决**: 编译必须在ext4上 (`/home/administrator/...`)
- **教训**: cp 源码到 ext4，编译完再 cp 产物回来

### 2. cmake -S/-B 比 cd+cmake 可靠
- **现象**: `cd rel && cmake ..` 偶尔找不到 CMakeLists.txt
- **解决**: 用 `cmake -S /path/to/src -B /path/to/build` 绝对路径

### 3. ENABLE_LAUNCHER/EDITOR/LOBBY 必须 OFF
- **现象**: cmake configure 报 "add_subdirectory" 错误
- **解决**: 加 `-D ENABLE_LAUNCHER=OFF -D ENABLE_EDITOR=OFF -D ENABLE_LOBBY=OFF`

### 4. RPATH 陷阱
- **现象**: 新编译的 libmlclient.so 的 RUNPATH 指向 ext4 构建目录
- **后果**: 部署到 workspace 后，ld 从 ext4 加载 libvcmi.so（该处 data 目录为空），导致 DATA/LCDESC 找不到
- **解决**: 用 `patchelf --set-rpath` 或统一从 ext4 加载所有 .so

### 5. cmake 自动覆盖 data symlink
- **现象**: 每次 cmake build 后 `rel/bin/data` 被重置为 `<build>/data`
- **解决**: 编译后必须重新 `ln -sf /mnt/d/GAMES/Heroes3 data`

### 6. PCH 导致重编译巨慢
- **现象**: 第一次编译 gch 耗时 90 秒+
- **解决**: `-D ENABLE_PCH=OFF`

---

## 二、连接器与运行环境

### 7. connector 和 libmlclient 必须 API 匹配
- **现象**: connector 含 adventure 代码但加载旧 libmlclient → `undefined symbol: g_adventure_cb`
- **解决**: 训练用旧版(无adventure)，冒险测试用新版(有adventure)，完全隔离部署

### 8. 训练和冒险测试用不同的 connector/libmlclient 组合
- **训练**: workspace/vcmi/rel/bin/ (旧 libmlclient + 旧 connector，无 adventure 符号)
- **冒险测试**: vcmi-native/rel/bin/ (新 libmlclient + 新 connector，含 adventure 符号)
- **教训**: 不要混用，每次切换必须显式指定 LD_LIBRARY_PATH

### 9. MSYS_NO_PATHCONV=1 必备
- **现象**: `$PWD/vcmi/rel/bin` 被 MSYS 转成 `C:/Program Files/Git/...`
- **解决**: 所有 wsl 命令前加 `MSYS_NO_PATHCONV=1`

### 10. LD_LIBRARY_PATH 含空格路径会截断
- **现象**: `export LD_LIBRARY_PATH=$PWD/vcmi/rel/bin:...` 因 MSYS 路径转换引入空格而截断
- **解决**: 用绝对路径，如 `/home/administrator/vcmi-workspace/vcmi/rel/bin`

### 11. 子进程环境继承
- **现象**: train_anchor.py 的 subprocess.run 继承的 LD_LIBRARY_PATH 可能不对
- **解决**: train_anchor 中显式设置 env 变量

---

## 三、VCMI 运行

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

## 四、地图

### 18. A1/A5 地图频繁崩溃或超时
- **现象**: R2 A1 1分钟 crash (exit=-7)，R3 A5 20分钟超时
- **可能原因**: 地图文件本身问题，或 VCMI 对这些地图初始化不稳定
- **现状**: A2/A6 相对稳定，A4/A7 已用 A1 模板重建修复

### 19. ml-mini.vmap 的 hero 类型问题
- **现象**: 用 core:knight 等标准英雄类型加载失败
- **原因**: vmap 需要 ML mod 的英雄类型 (ML:hero_X)
- **解决**: s1.vmap 用 ML:hero_0 等

### 20. s1.vmap 战斗模式 vs 冒险模式
- **现象**: s1.vmap 在战斗 Gym 中加载 crash
- **原因**: 战斗 Gym 期望 battle map，s1 是冒险地图

---

## 五、C7 动作映射（2026-07-27）

### 21. dlsym 找到旧版 strategic_state_update
- **现象**: `dlsym(RTLD_DEFAULT)` 在 libvcmi.so 里先找到旧版 strategic_state_update（无 P0 自分配），新版在 libmlclient.so 里不被执行
- **解决**: 改 extern "C" 直调，不用 dlsym。链接器保证找到 libmlclient.so 的正确版本

### 22. struct 尺寸不可改
- **现象**: 在 `StrategicState` 中加 `int32_t action` 字段后全量编译失败
- **根因**: strategic_state.cpp 被编进 mlclient.dir 和 vcmiservercommon.dir，两处 sizeof 不一致
- **解决**: action 放独立全局变量 `g_rl_action`，不碰 struct

### 23. try/catch 吞异常导致观测全零
- **现象**: strategic_state_update 内 try/catch 包裹所有逻辑，异常被吞，观测全零
- **解决**: 去掉 try/catch，让异常暴露；或在 catch 里输错 e.what()

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


## 五、Python 与环境

### 21. PWD 在不同 shell 上下文中的差异
- **现象**: `bash -c` 中 `$PWD` 可能是 Windows 路径
- **解决**: 所有关键路径用绝对路径，不依赖 $PWD

### 22. python3 -c 中的引号嵌套
- **现象**: `python3 -c "print(f'{x}')"` 在 bash -c 中引号冲突
- **解决**: 复杂 Python 写文件再用 `python3 file.py`，或用 heredoc `<< 'PYEOF'`

### 23. 多个 train 进程并存
- **现象**: pgrep -f train 匹配到自身 grep 和旧残留
- **解决**: `for p in $(pgrep -f "python.*train"); do kill -9 $p; done`

### 24. ctypes 跨进程访问全局变量
- **现象**: Python 脚本 A 设了 g_strategic_state，Python 脚本 B 读出来是 NULL
- **原因**: 两个 python3 调用是不同进程，内存不共享
- **解决**: 必须在同一个 Python 进程中 init 和 read

---

## 六、GitHub 与网络

### 25. GitHub 直连超时
- **现象**: git clone https://github.com/... 超时
- **原因**: 网络不通
- **解决**: 本地已有副本 D:\Bigdata\hero3\vcmi-gym\

### 26. opencode 连不上服务器
- **现象**: opencode run 报 "Unexpected server error"
- **原因**: 网络问题或 API key 未配置
- **解决**: 用本地的 deepseek-v4-pro/flash 子 Agent

---

## 八、connector/libmlclient/MMAI 三件套匹配（2026-07-28）

### 32. subprocess stderr=DEVNULL 吞掉 MMAI 诊断
- **现象**: `fprintf(stdout, "FILL: enter\n")` 从未在任何日志中出现
- **根因**: `train_wsl2_ppo_v2.py` 第 59 行 `stderr=subprocess.DEVNULL`，ep_runner 所有 stdout/stderr 进黑洞
- **解决**: 改为 `stdout=open(ep_log, "w"), stderr=subprocess.STDOUT` 捕获到文件

### 33. VCMI 内部重定向 stdout/stderr
- **现象**: 即使子进程 stdout 指向日志文件，MMAI 的 fprintf 仍不出现
- **根因**: VCMI 启动后 CBasicLogConfigurator 可能重定向 fd 1/2
- **解决**: 用 fopen("/tmp/mmai_diag.txt", "a") 直接写文件，完全绕过 VCMI 日志层

### 34. __declspec(dllexport) 在 GCC 下不识别
- **现象**: WSL 编译 MLClient.cpp 报 `expected constructor, destructor, or type conversion before '(' token`
- **根因**: `__declspec(dllexport)` 是 MSVC 扩展，GCC on Linux 不认
- **解决**: 加跨平台宏 `#ifdef _MSC_VER` / `#else DLL_EXPORT __attribute__((visibility("default")))`

### 35. init_vcmi ABI 不匹配（3-arg vs 1-arg）
- **现象**: 新编译的 connector_v13.so import 时报 `undefined symbol: _ZN2ML9init_vcmiEPN4MMAI6Schema6IModelES3_RKNS_8InitArgsE`（3-arg）但 libmlclient.so 只有 1-arg 版本
- **根因**: connector 代码(v13/threadconnector.cpp:573) 调用 `ML::init_vcmi((void*)initargs)` 1-arg，但链接到旧 libmlclient 的 3-arg 版本；或 connector 编译时找的是新 libmlclient(1-arg) 但代码还是旧 3-arg 签名
- **解决**: 统一 connector 使用 `ML::init_vcmi((void*)initargs.get())` 1-arg 签名，且 connector 与 libmlclient 编译自同一份 headers

### 36. CMakeLists.txt 硬编码 VCMI_DIR 覆盖 -D 参数
- **现象**: 即使传 `-DVCMI_DIR=/mnt/d/Bigdata/hero3_fresh/vcmi`，编译 Include 路径还是 `/home/administrator/vcmi-native`
- **根因**: CMakeLists.txt 第 11 行 `set(VCMI_DIR "/home/administrator/vcmi-native")` 无条件覆盖命令行传入的缓存变量
- **解决**: 改为 `if(NOT VCMI_DIR) set(...)` 条件设置

### 37. Schema 版本冲突（BATTLE_SIDE vs BATTLE_ROUND）
- **现象**: connector_v13 编译时 constants.h static_assert 报错
- **根因**: 
  - 项目源码(D:\Bigdata\hero3_fresh\vcmi) 的 v13 schema 有 `BATTLE_SIDE` + `LINK_SIZES`（新版）
  - vcmi-native-build 的 v13 schema 有 `BATTLE_ROUND`（旧版）
  - connector 代码引用 LINK_SIZES，vcmi-native-build 头文件没有
  - types.h 和 constants.h 两处不一致导致编译或运行时崩溃（core dump）
- **教训**: 项目源码和 vcmi-native/vcmi-native-build 三份 VCMI 源码已严重分歧。connector、libmlclient、MMAI 必须编译自同一 schema 版本

### 38. 三份 VCMI 源码各自不同步
- **现象**: 
  - `D:\Bigdata\hero3_fresh\vcmi\` — 项目源（BATTLE_SIDE + LINK_SIZES，新版 schema）
  - `/home/administrator/vcmi-native/` — 部署目录（BATTLE_ROUND，旧版 schema）
  - `/home/administrator/vcmi-native-build/` — 编译目录（BATTLE_ROUND，旧版 schema）
- **后果**: 修一个就要同步三份，否则 connector 和 libmlclient 不兼容
- **教训**: 项目源码是权威，改代码后必须 `cp` 到 `vcmi-native/` 和 `vcmi-native-build/` 两份。编译用 `vcmi-native-build` (ext4, 速度快)，部署从 build 复制到 `vcmi-native`

### 27. deepseek-v4-flash 有 45 次工具调用上限
- **现象**: 子 Agent 分析到一半戛然而止
- **解决**: 大任务用 deepseek-v4-pro (同样 45 次但能力更强)，或拆成多个小任务

### 28. 子 Agent 用 patch 写文件频繁失败
- **现象**: NTFS 路径 `C:\d\Bigdata\...` 拼写错误，patch 失败
- **解决**: 让子 Agent 用 write_file 而不是 patch

### 29. 子 Agent 杀死后台进程
- **现象**: pkill -f train 副作用杀了父进程的 bash
- **解决**: `for p in $(pgrep -f "python.*train"); do kill -9 $p; done`

### 30. 子 Agent 改 symlink 后不通知
- **现象**: 子 Agent 改了 vcmi symlink 导致训练失败，父 Agent 不知道
- **解决**: 审计 Agent 检查 symlink 完整性

### 31. WSL terminate 丢失未写入文件的更改
- **现象**: `wsl --terminate Ubuntu` 后，WSL 内文件未写入的更改丢失
- **解决**: 修改 WSL 内文件后立即 flush/写入，不要在 Python heredoc 中留待后续处理

### 32. 观测维度和 ctypes 结构体偏移必须严格同步
- **现象**: passable[8] 加入 C++ struct 后 obs[-8:] 全零，C 和 Python 的 sizeof 一致但读取位置不对
- **根因**: 英雄字段 8×23=184 超过 OBS_DIM=264 的剩余空间，passable 被写到 idx=242 而非 idx=256
- **解决**: obs 构建器强制写 passable 到 OBS_DIM-8 位置，不从当前 idx 继续

### 33. TerrainTile::blocked() 是函数不是成员变量
- **现象**: `tile.blocked` 编译报错 `cannot convert from type bool () const to type bool`
- **解决**: 使用 `tile.blocked()` 加上括号调用

### 34. TerrainTile::terType 不存在
- **现象**: `tile.terType != 5` 编译报错 `no member named terType`
- **解决**: 使用 `tile.getTerrain()->isWater()` 判断是否为水域

### 35. 两个 libmlclient.so 实例导致 g_strategic_state 不共享
- **现象**: passability 值在 C++ 侧设置了但 Python 读不到（虽然 heroes 位置能读到）
- **根因**: 实际不是双实例问题，是 ctypes 结构体偏移不匹配（已修，同 #32）
- **解决**: 确认 sizeof/offsetof 匹配 + 强制写 passable 到固定位置

### 36. passability mask 全堵时应回退 END_TURN 而非抛异常
- **现象**: Categorical(logits=-inf) 抛 "invalid probability distribution"
- **解决**: 采样前加 `if passable.any():` 判断，全堵直接 `a = 10`

### 37. vcmi-native 缺 v14/v15/v13 constants.h 的 LINK_SIZES
- **现象**: v14/v15 connector 编译报 `schema/v14/types.h: No such file or directory`，v13 报 `LINK_SIZES was not declared`
- **根因**: vcmi-native 的 schema 版本落后于本地 vcmi
- **解决**: 从本地 vcmi 复制 schema 目录到 vcmi-native：
  ```bash
  cp -r /mnt/d/Bigdata/hero3_fresh/vcmi/AI/MMAI/schema/v14 /home/administrator/vcmi-native/AI/MMAI/schema/v14
  cp -r /mnt/d/Bigdata/hero3_fresh/vcmi/AI/MMAI/schema/v15 /home/administrator/vcmi-native/AI/MMAI/schema/v15
  cp /mnt/d/Bigdata/hero3/hero3_fresh/vcmi/AI/MMAI/schema/v13/constants.h /home/administrator/vcmi-native/AI/MMAI/schema/v13/constants.h
  ```

### 38. v15 预存 header/impl 返回类型不匹配
- **现象**: v15 connector 编译报 `no declaration matches` for connect/reset/step/render/getLogs
- **根因**: header 声明 `const std::tuple<int, P_State>` 而 cpp 实现 `std::tuple<int, const py::dict>`（去掉了 const 且换了类型）
- **连带**: v15 header 缺 `buildObsDict` 声明
- **解决**: 统一为 `std::tuple<int, py::dict>` + 补 `py::dict buildObsDict()` 声明 + 删不存在的 `convertState`

### 39. Connector 适配新 1-param init_vcmi(void*) API
- **现象**: 新版 libmlclient 改用 `ML::init_vcmi(void*)`，旧 connector 调 `init_vcmi(leftModel, rightModel, initargs)` 算不链接
- **解决**: 三个版本 v13/v14/v15 统一改：
  - header: `const ML::InitArgs initargs;` → `std::unique_ptr<ML::InitArgs> initargs;`
  - header: 移除 `initargs(ML::InitArgs{...})` 初始化列表，加 25 个 `_` 前缀成员变量存储构造参数
  - start(): 模型分配后 `initargs = make_unique<InitArgs>(_mapname, leftModel, rightModel, ...)`
  - 调用: `init_vcmi(leftModel, rightModel, initargs)` → `ML::init_vcmi((void*)initargs.get())`
  - v14/v15 的 `randomArmies`(bool) → `randomStackChance`(int) 映射: `randomArmies ? 100 : 0`
  - `maxBattles=0`, `statsTimeout=60000`, `headless=true` 硬编码保持旧行为

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

### 43. CMake /DEF: 标志导致 MinGW ld 链接失败
- **现象**: `make mlclient` 报 `/usr/bin/ld: cannot find /DEF:path/mlclient_exports.def`
- **根因**: CMakeLists.txt 包含 `target_link_options(mlclient PRIVATE /DEF:...)`——/DEF: 是 MSVC 标志，MinGW ld 不识别
- **解决**: 去掉 `mlclient_exports.def` 源文件引用和 `target_link_options /DEF:` 行

### 44. vcmi-native 和 vcmi-native-build 两份源码不一致
- **现象**: 改了 vcmi-native/ML/ 的代码，编译的却是 vcmi-native-build/ML/ 的老代码
- **根因**: cmake 的 `CMAKE_HOME_DIRECTORY=/home/administrator/vcmi-native-build`，源文件从那里读
- **解决**: 两份都改，或 rsync 同步后再编译

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

### 47. `extern "C"` 不允许嵌套
- **现象**: 在 `extern "C" { ... }` 块内又加了 `extern "C" int adventure_get_action()`
- **解决**: 去掉内层的 `extern "C"`，只保留函数声明

### 40. 部署新 connector .so 需备份旧文件
- **现象**: 覆盖 rel/ 的 .so 后无法回滚
- **解决**: 部署前 `cp *.so *.so.bak.20260727`，再从 build/ 复制新 .so 到 rel/
- **当前版本**: v13=8.3MB, v14=7.0MB, v15=6.3MB（均为新 1-param API 链接）

---

## 八、AAI::yourTurn 执行顺序与 passability（2026-07-28）

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

## 九、CGameState 空问题修复（2026-07-28）

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

## 十、#46 ~ #57 修复（2026-07-29）

**当前状态：全部修复 ✅ env.reset() 返回 obs_nz=8/264**

关键修复记录已归纳到踩坑点 #50-#59。以下为最终总结：

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

## 十一、#46 installNewBattleInterface segfault（2026-07-29）

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

### 51. MMAI constructor symbols 需强制导出
- **现象**: `nm -D libMMAI.so | grep AAIC1Ev` 显示 `U`（undefined）而非 `T`（defined text）
- **后果**: 新版 libMMAI.so 加载时 `symbol lookup error: undefined symbol: _ZN4MMAI3AAI3AAIC1Ev`
- **根因**: GCC 链接器因某些原因未将 `AAI.cpp.o` 中定义的 `AAI::AAI()` 构造器导出到最终 .so
- **解决**: 在定义处加 `__attribute__((used, visibility("default")))` 强制导出
- **涉及文件**: `/home/administrator/vcmi-native-build/AI/MMAI/AAI/AAI.cpp` line 38

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

### 55. libmlclient RUNPATH 指向 build 目录
- **现象**: 新版 libmlclient.so 的 RUNPATH 包含 `/home/administrator/vcmi-native-build/rel/bin/AI`
- **后果**: 运行时从 build 目录加载 libMMAI.so 和 libvcmi.so，不是从 rel 目录
- **注意**: vcmiserver 也有类似问题——生成用`/home/administrator/vcmi-native-build/rel/bin/libmlserverplugin.so`
- **修复**: 部署时 cp 文件到 rel/ 即可（ld 优先从 rel/ 加载，build 目录作为兜底）
- **更好的修复**: 改 cmake 的 `-DVCMI_BIN_DIR` 编译参数指向 `rel/` 而非 `build/`

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

## 九、CGameState 空问题修复（2026-07-28）【已移到上方】


### 57. MMAI_USER battle hang — env 无 battle step 回调
- **现象**: env.reset() 后 installNewBattleInterface 四色全部 EXIT OK，然后  静等 15s 超时
- **特征**: 战斗接口全部初始化 OK，但游戏再也进不了冒险回合
- **根因**:  时 leftModel=Function(f_getAction0)，战斗需要 python 调  才能返回 action。但 strategic_env 不驱动战斗（只调 adventure_wait/act），战斗永远挂起
- **解决**: 改为 （或 Nullkiller/BattleAI），战斗自动解析不通过 connector 回调
- **影响**: 冒险测试不能用 MMAI_USER，只能用 auto-battle AI
- **副作用**:  和  参数当前无用（blue 也固定 StupidAI）

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
