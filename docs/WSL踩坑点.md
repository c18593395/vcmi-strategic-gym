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

## 十一、Passability 修复总结（2026-07-29）

### 1. 方向映射不统一 → 模型坍缩
- **现象**：200步全选同一方向，r=-89.5/ep，vloss→0
- **根因**：`strategic_state.cpp` passability 用的 E-start 方向，`AAI.cpp` moveHero 用的 N-start。passable[0] 检查 East，action=0 移动 North → 模型认为"方向0可通"但"选方向0走不通"
- **修复**：全系统统一 `dx={0,1,1,1,0,-1,-1,-1} dy={-1,-1,0,1,1,1,0,-1}`（N-start CW）
- **三处必须一致**：`strategic_state.cpp` passability、`AAI.cpp` moveHero、Python 侧

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

### 63. adventure_process_turn 缺日历/地图填充
- **现象**: `StrategicState.day/week/month/map_width/map_height/has_underground` 全0
- **根因**: `adventure_process_turn()` 只填 player/hero/passability/game_over，没写日历和地图字段。`strategic_state_update()`（dlsym 路径）有填，但 connector 路径不走那个函数。
- **影响**: 训练缺时间感知；地图尺寸缺失导致 passability 方向验越界不完整
- **修复**: 在 `adventure_process_turn()` 加：
  1. `gicb->gameState().day` → day/week/month（不用 `getCalendar()`，部署版没有）
  2. `gicb->getMapSize()` → map_width/map_height/has_underground
- **注意事项**: 改的是 `vcmi/ML/strategic_state.cpp`，须同步到 WSL2 所有副本（`hero3_vcmi`/`vcmi-native`/`vcmi-native-build`/`vcmi-build-latest`）

### 64. EEXIST — boost::create_directories 对符号链接失败
- **现象**: `boost::filesystem::create_directories: File exists [system:17]: "./data"`
- **根因**: `rel/bin/data` 是 cmake POST_BUILD 创建的符号链接（`data -> ../../data`），指向 `/home/administrator/data` 不存在。boost::create_directories 先 stat（跟符号链接 → ENOENT）后 mkdir（发现已有 symlink 条目 → EEXIST）
- **影响**: 阻塞 v15 connector 初始化，无法使用 v15 架构
- **修复**: 删符号链接，建真实目录，内部 ln -sf 具体文件：
  ```bash
  rm -rf rel/bin/data && mkdir -p rel/bin/data && cd rel/bin/data
  ln -sf /home/administrator/vcmi-native-build/data/H3bitmap.lod .
  # 同理其他文件...
  ```
- **cmake 陷阱**: 每次 `cmake --build` 重建 mlclient 时 POST_BUILD 重新创建符号链接。必须重建后重新修复
- **同时修复**: 所有 config 目录写入有效 JSON + 删除递归 config 符号链接

### 65. 旧模型权重编码旧 obs 模式 — 清权重才能受益于新 obs
- **现象**: 修好 passability/day/map_size 填充后，旧模型仍然 act=[10,10,...]（END_TURN），不探索
- **根因**: 旧模型在 obs_nz=29（缺数据）上训练了 73000+ step，权重编码了"obs 大部分为零 → 无用信息 → 执行 END_TURN"
- **修复**: `rm wsl2_model.pt wsl2_model_state.pt; rm checkpoints/*.pt`，重启训练
- **验证**: 新随机模型首次 ep 就 obs_nz=61（数据完整），avg_r 从随机水平开始正常学习

---

## 2026-07-31 — C8.2 Nullkiller2 验证修复链（5 个阻塞）

### 1. MLClient.h InitArgs 头文件与 .so 布局漂移
- **现象**: connector_v13 编译报 `cannot convert string to bool`（_mapname → bool leftAllowMlBot）
- **根因**: 某会话把 MLClient.h InitArgs 重构成 33 字段 string 版（git a15789690），但 libmlclient.so 实际是 28 字段 IModel* 版（MLClient.cpp 引用 `a.leftModel`，.o 未重编）→ 头文件与 .so ABI 分裂
- **诊断**: `gdb -batch -ex 'ptype ML::InitArgs' libmlclient.so` 直接读出 .so 内部真实布局（298MB .so 含 debug info）
- **修复**: 头文件恢复 28 字段 IModel* 布局 + `init_vcmi(void*)` 单参声明。三副本（vcmi-native / vcmi-native-build / 项目源）同步
- **教训**: 改 MLClient.h 布局必须同步重建 libmlclient.so + connector，否则静默 ABI 分裂。头文件与 .so 的真理以 gdb ptype 为准

### 2. connector_v13.so 本体丢失
- **现象**: `rel/connector_v13.so` 不存在（只剩 .current/.bak/.new），strategic_env.py `from ...connectors.rel import connector_v13` 必 ImportError
- **根因**: 23:35 cmake 重配后 v13 target 未被构建（只建了 v14/v15），旧产物被清
- **修复**: 恢复头文件后 `cmake --build rel --target connector_v13` 重建

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

### 6. 采集子进程无 watchdog → NK2 启动阶段卡死挂起整条采集
- **现象**: collect_bc.py 主进程 `subprocess.run(cmd)` 无限等待；ep1 (Key to Victory.h3m) 子进程卡 `futex_do_wait` 1h27m，CPU 仅 19s，无 npz 产出，输出进 pipe 无人读（日志全丢）
- **根因**: NK2 chain 重试死循环（已知 ~50% 概率）可发生在 **reset 启动阶段**——`connector.init()`/首个 yourTurn 等待无超时兜底（boot_timeout/vcmi_timeout/wait_timeout 只覆盖采集循环），子进程永久挂起，主进程 `subprocess.run` 无 timeout 跟着无限等
- **修复**: 主进程 `subprocess.run(..., timeout=900)` 整局硬超时，`TimeoutExpired` → kill 跳局 continue；重启采集并 `> collect.log 2>&1` 落盘日志
- **验证**: 修复后 ep0 正常落盘 44KB，ep1（之前卡死图）reset OK 正常采集
- **教训**: 所有子进程隔离式脚本必须有**整局级** watchdog（覆盖启动+运行全程），不能只依赖 env 内部各阶段 timeout；后台进程 stdout 必须重定向到日志文件

### 7. 战斗 AI 三选一全废 (C8.5 训练卡死根因链)
- **现象**: NK2(blue) 打野怪 → 战斗开始 → 卡死或崩溃, ep_steps=1~2
- **根因链** (逐层定位):
  1. `combatEnemyAI/NeutralAI` 设置在 **"server" 路径** (无效) → 实际用 schema 默认 **BattleAI** → headless 下等待回调卡死
  2. 换 **StupidAI** → `libStupidAI.so does not export GetNewAI` (ABI 不匹配, 只有 GetNewBattleAI 无 GetNewAI) → 冒险 AI 加载崩
  3. 换 **MMAI** → battleStarted → Router::battleStart → `ASSERT(cb->getPlayerID()->hasValue())` — **neutral 玩家无 playerID → 抛异常 → 穿过 noexcept 边界 → std::unexpected 崩溃**
- **修复**: ① 战斗 AI 键改 `{"ai", ...}` 路径 + 全用 MMAI (leftModel/rightModel=Scripted("StupidAI") 自动裁决) ② Router::battleStart neutral 无 playerID 时用 modelRight + 整体 try-catch fallback StupidAI ③ 战斗结果对话框 `IFML(true,false)` 禁用 (ML 模式 AI 不回答 CBattleDialogQuery → 永久卡) — **server 代码链接进 libmlclient.so, 改 BattleResultProcessor 必须 make mlclient 而非 vcmiserver**
- **教训**: 进程内 server (useProcess=false) — server 代码在 libmlclient.so; 改 server 逻辑后验证二进制归属 (grep -acl "消息文本" rel/bin/*)

### 8. WSL 内存崩溃 (E_UNEXPECTED)
- **现象**: 训练/diag 跑一段时间后 `wsl bash` 全部返回 `Wsl/Service/E_UNEXPECTED` 乱码 — WSL 服务崩溃
- **根因**: 主机 16GB 内存仅剩 3.9GB 空闲 → WSL2 默认 50% 配额吃满 → VCMI+Python 重负载 OOM → WSL 整体崩
- **修复**: `C:\Users\Administrator\.wslconfig` 限制 `memory=6GB swap=4GB processors=8`
- **教训**: 训练机内存紧张, 监控 free -h; 训练进程死亡先查 WSL 是否崩溃 (watchdog 检测进程消失 + WSL 探测)

### 9. 被动资源收入做 per-step 奖励 → 模型坚守 END_TURN (C8.5)
- **现象**: 训练 200 步全 act=10 (END_TURN), r=2000/局 (每步 +10)
- **根因**: reward_gold_mult=0.01 → END_TURN → day 推进 → 城镇被动 gold 收入 → 每步 +5~10 白拿 → 坚守 END_TURN 最优
- **修复**: reward_gold_mult=0.0 (被动收入只做终局奖励)
- **教训**: 任何被动收入 (gold/town/资源产出) 都不能做 per-step 奖励; 主动行为驱动必须用事件奖励 (占矿/杀敌/占城) + 态势感知

### 10. 进程内 server 代码在 libmlclient.so (C8.5)
- **现象**: 改 BattleResultProcessor (server 逻辑) 后 make vcmiserver 部署无效
- **根因**: useProcess=false → server 代码链接进 libmlclient.so (vcmiservercommon → libmlclient)
- **修复**: make mlclient 部署 libmlclient.so
- **教训**: 改 server 逻辑先验证二进制归属: grep -acl "代码内字符串" rel/bin/*

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

### 13. fill 无锁直读 CGameState → NK2 决策损坏 (2026-08-01)
- **现象**: NK2 所有 moveHero 被服务器拒 ("destination tile is blocked" 死循环), 非崩溃
- **根因**: fill_exploration/fill_mines 在 NK2 后台线程直读 gs.getMap()/fogOfWarMap（无锁）→ 与 NK2 规划线程数据竞争 → NK2 决策数据损坏
- **定位**: H2 隔离实验（注释 fill 调用 → NK2 恢复 100 pairs 正常）
- **修复**: fill_exploration/fill_mines 内部 `std::shared_lock gsLock(CGameState::mutex)`（AAI.cpp 同模式）
- **教训**: 回调里直读 CGameState 必须加锁; callback API（getTile 等）内部有锁, 直读 gs 没有

### 14. VCMI settings 写读层不一致 → AI 分配失效 (2026-08-01)
- **现象**: red_adventure_ai="Nullkiller2" 但 Opening 全是 MMAI, act=-1（MMAI 的 send_action(-1)）
- **根因**: `Settings(settings.write({"ai",...}))` 写 session 层, Client.cpp `settings["ai"][...]` 读配置层 → 写入不生效（读默认 MMAI）。C8.5 训练没暴露（默认 MMAI 恰好正确）
- **修复**: 跨 .so 全局 `extern "C" char g_adventure_allied_ai[64]`（MLClient strncpy 写 / Client.cpp 读, g_ml_player_cb 同模式）
- **教训**: 验证 settings 写入生效用运行时日志（friendlyAI/playerAI 打印的是 combat/冒险 AI 别混淆）; 写入非默认值才暴露层问题

### 15. extern "C" 语法两坑 (2026-08-01)
- **坑1**: `extern "C" extern char x[64];` → "invalid use of 'extern' in linkage specification"
- **坑2**: 函数内 `extern "C"` → 非法（只能命名空间作用域）
- **正确**: 文件作用域 `extern "C" { extern char x[64]; }`（块形式）

### 16. 编译树 MMAI 旧版陷阱 (2026-08-01)
- **现象**: 战斗崩溃（neutral ASSERT, 踩坑 #11 的修复在项目源但编译树没有）
- **根因**: vcmi-native（编译树）AI/MMAI 只有 v13 结构, 项目源是 fork tip（含 v14/v15 Graphmind draft）→ 全量同步 MMAI 有编译风险; router.cpp 等关键修复文件没同步
- **修复**: 只同步关键修复文件（router.cpp neutral guard）→ 重编 MMAI
- **教训**: 编译树与项目源版本漂移是常态（AI/ML 目录: AIGateway hook、MLClient、router 都可能旧）; 编译前 diff 关键文件, 按需同步


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

### 22. NK2 采集后期卡死 — adventure_wait 90s 超时兜底 (2026-08-15 H.7 #15)
- 现象: 24 局稳定性采集 (collect_bc.py, NK2 对手) 跑到 ep23 时 adventure_wait timed out after 90s, 该局只采到 11 pairs
- 根因: NK2 后期陷入死循环 (反复 Unable to complete chain / Exchange between heroes 队列刷屏), 服务器端一直有 query 待应答, Python 侧等不到自己的回合
- 处理: collect_bc.py 的 90s 超时兜底生效 — 超时后按已采 pairs 正常保存 (ep23 SAVED 11 pairs), 不崩不挂, 整条采集继续下一局
- 教训: 长采集必须有 per-episode 超时兜底 + 部分保存; NK2 卡死是已知行为 (早期 C8 采集也有), 单局掉数据不影响全局; 采集日志看 [epN] SAVED 行数即可判断局质量

### 23. OBS v3 大数值字段未归一化 → 训练数值爆炸 (2026-08-16 H.8 根因)
- 现象: PPO 重启后 vloss=2.6e12, KL=1.4e6, 动作坍缩恒 23; BC 训练 loss=92934, val_acc=0.19, 预测分布只出 {1:255, 5:426}
- 根因链: 2689 时代 obs max=6410 (C8.5 vloss=1349 正常) → v3 新增未归一化大字段:
  1. **build_mask_lo/hi** (31-bit bitmask, 全置位=0x7FFFFFFF≈2.1e9) — 最极端, 单列即炸
  2. gold 74万 / total_power 7.8万 / weekly_income 1.7万 / enemy_threat 11万
  → 直接喂 Linear(3464→128) → logits 300-1700 爆炸 → softmax 饱和单点 → 训练失效
- 修复 (strategic_env._build_obs + bc_train.load_data 双端同变换):
  1. build_mask 16 列 ÷2^31 → [-1,1), 保留 bit 语义 (float32 存 2e9 精度本就丢低 8 位)
  2. players.gold/total_power/weekly_income + heroes.movement/max_movement/exp/total_power + enemy_threat + battle_pred 共 67 列 log1p 压缩 (0→0, 1e6→13.8)
- 效果: vloss 2.6e12→153→1, kl 1.4e6→0.048, BC loss 92934→0.83, val_acc 0.19→0.475
- 教训: **新增 obs 字段必须检查数值尺度** (bitmask/资源量/战力都是高危), 不能原样进网络; 训练前跑一次 obs max 统计 (2689 时代 6410 是安全参考线)
- 附加坑: strategic_env.py 里曾引用不存在的 TOWNS_OFF 变量 (写归一化时代码错误) → ep_runner 每局崩 "name 'TOWNS_OFF' is not defined", 排查要直接看 traj_ep.json 的 error 字段
- 附加坑: train_wsl2_ppo_v2.py 模块级代码在 import 时执行 — 诊断脚本 import 它会触发训练 (超时被杀), 用 bc_train.Net 代替

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

### 25. C++ 修复写了但未同步编译树/未重编/未部署/未提交 = 修复从未生效 (2026-08-16 工作流教训)
- 现象: visitablePos 修复 2026-08-15 已写入项目源 vcmi/ML/strategic_state.cpp (git 未提交), 但编译树 ~/vcmi-native/ML/ 是旧版, 部署的 libmlclient.so (14:49) 无修复 → 8-16 训练仍全 blocked
- 原因: 改代码后只改项目源, 没有走完: 同步编译树 (cp) → 重编 (cmake --build rel --target mlclient) → 部署 (rel/bin/libmlclient.so) → 实测 → git commit
- 教训: **C++ 改动四步闭环: 项目源 → 编译树 → 编译部署 → 实测, 全部完成后才 commit**; 排查"改了没生效"先对比项目源 vs 编译树 vs .so 时间戳 (diff 三处)

### 26. NK2 卡死根因 — Router battleStart 战斗模型加载失败 (2026-08-16 全面分析)

- 现象: NK2 无论作为 red (采集) 还是 blue (训练/复现), 每局 7-42 pairs 就 stuck; 日志刷屏 [ML-wait] battle=3 q=0 obj=1 mov=1; adventure_wait 90-120s 超时
- 根因链 (3 环):
  1. threadconnector.cpp 481/491: `Scripted(red/blue)` — blue=Nullkiller2 时 battle 模型名 = "Nullkiller2" (NK2 是冒险 AI 非战斗模型名)
  2. Router::battleStart SCRIPTED 分支只认 StupidAI/BattleAI/MMAI_BATTLEAI, 未知名 THROW → catch fallback StupidAI → 战斗仍挂 (battle 无人正确指挥)
  3. **打野 (red 攻中立) 时 neutral 无 playerID → C8.5 fix 用 baggage->modelRight (blue 模型)** → Nullkiller2 → 加载失败; 且 fallback BattleAI 在 headless 无头服务器下等待回调卡死 (MLClient.cpp 400 行注释早有记录)
- [ML-wait] 真相: NK2 的 AIStatus::waitTillFree 等 battle!=NO_BATTLE + queries 空 + 对象访问完 + 移动完 — battle=3 挂着 = NK2 在等战斗结束, 战斗永不结束 → 超时
- 修复 (router.cpp 两处): neutral 无 playerID → 直接 CDynLibHandler::getNewBattleAI("StupidAI") 自动裁决 early return; SCRIPTED else fallback BattleAI → StupidAI (BattleAI headless 卡死勿用)
- 教训: **battle 模型名 ≠ 冒险 AI 名**; neutral 战斗不能复用 blue 模型; BattleAI 无头模式不可用, 自动裁决统一 StupidAI

### 27. pkill/pgrep -f 匹配到自己 — bash -c 命令行含模式字符串自杀 (2026-08-16)

- 现象: `pkill -9 -f train_wsl2_ppo` 在 bash -c 包装里执行 → exit 9, 后续命令全没跑; pgrep -f 采样到 bash 包装进程 (rss=3MB) 而非目标 python
- 根因: bash -c "pkill -f XXX ..." 的命令行本身含 XXX → pkill -f 匹配到自己的 bash → SIGKILL
- 修复: 用精确 PID (ps aux | grep | awk 取列) 或 pgrep -f '^/绝对路径' (锚定开头, 排除 bash -c 包装)
- 教训: WSL 里 pkill -f 高危, 先 pgrep 看 PID 再 kill; 采样脚本的 pgrep 模式必须锚定可执行文件绝对路径

### 28. WSL /tmp 频繁清空 — 观测日志/轨迹丢失 (2026-08-16)

- 现象: /tmp/nk2_mem_watch.log /tmp/router_fix.log /tmp/traj_ep.json 多次消失 (复现实验日志还没分析就没了)
- 根因: WSL2 /tmp 是 tmpfs, 系统内存压力/重启时自动清理 (多次出现)
- 修复: 实验日志写项目目录 (bc_data/ 或 logs/), 不用 /tmp; 轨迹文件同样
- 教训: 长观测/实验数据必须落盘项目目录, /tmp 只放一次性临时文件

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
