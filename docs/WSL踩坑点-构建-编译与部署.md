# WSL踩坑点 — 构建-编译与部署

> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。

---

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



### 7. connector 和 libmlclient 必须 API 匹配

- **现象**: connector 含 adventure 代码但加载旧 libmlclient → `undefined symbol: g_adventure_cb`

- **解决**: 训练用旧版(无adventure)，冒险测试用新版(有adventure)，完全隔离部署



### 8. 训练和冒险测试用不同的 connector/libmlclient 组合

- **训练**: workspace/vcmi/rel/bin/ (旧 libmlclient + 旧 connector，无 adventure 符号)

- **冒险测试**: vcmi-native/rel/bin/ (新 libmlclient + 新 connector，含 adventure 符号)

- **教训**: 不要混用，每次切换必须显式指定 LD_LIBRARY_PATH



### 32. subprocess stderr=DEVNULL 吞掉 MMAI 诊断

- **现象**: `fprintf(stdout, "FILL: enter\n")` 从未在任何日志中出现

- **根因**: `train_wsl2_ppo_v2.py` 第 59 行 `stderr=subprocess.DEVNULL`，ep_runner 所有 stdout/stderr 进黑洞

- **解决**: 改为 `stdout=open(ep_log, "w"), stderr=subprocess.STDOUT` 捕获到文件



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



### 35. 两个 libmlclient.so 实例导致 g_strategic_state 不共享

- **现象**: passability 值在 C++ 侧设置了但 Python 读不到（虽然 heroes 位置能读到）

- **根因**: 实际不是双实例问题，是 ctypes 结构体偏移不匹配（已修，同 #32）

- **解决**: 确认 sizeof/offsetof 匹配 + 强制写 passable 到固定位置



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



### 43. CMake /DEF: 标志导致 MinGW ld 链接失败

- **现象**: `make mlclient` 报 `/usr/bin/ld: cannot find /DEF:path/mlclient_exports.def`

- **根因**: CMakeLists.txt 包含 `target_link_options(mlclient PRIVATE /DEF:...)`——/DEF: 是 MSVC 标志，MinGW ld 不识别

- **解决**: 去掉 `mlclient_exports.def` 源文件引用和 `target_link_options /DEF:` 行



### 44. vcmi-native 和 vcmi-native-build 两份源码不一致

- **现象**: 改了 vcmi-native/ML/ 的代码，编译的却是 vcmi-native-build/ML/ 的老代码

- **根因**: cmake 的 `CMAKE_HOME_DIRECTORY=/home/administrator/vcmi-native-build`，源文件从那里读

- **解决**: 两份都改，或 rsync 同步后再编译



### 47. `extern "C"` 不允许嵌套

- **现象**: 在 `extern "C" { ... }` 块内又加了 `extern "C" int adventure_get_action()`

- **解决**: 去掉内层的 `extern "C"`，只保留函数声明



### 40. 部署新 connector .so 需备份旧文件

- **现象**: 覆盖 rel/ 的 .so 后无法回滚

- **解决**: 部署前 `cp *.so *.so.bak.20260727`，再从 build/ 复制新 .so 到 rel/

- **当前版本**: v13=8.3MB, v14=7.0MB, v15=6.3MB（均为新 1-param API 链接）



---



### 51. MMAI constructor symbols 需强制导出

- **现象**: `nm -D libMMAI.so | grep AAIC1Ev` 显示 `U`（undefined）而非 `T`（defined text）

- **后果**: 新版 libMMAI.so 加载时 `symbol lookup error: undefined symbol: _ZN4MMAI3AAI3AAIC1Ev`

- **根因**: GCC 链接器因某些原因未将 `AAI.cpp.o` 中定义的 `AAI::AAI()` 构造器导出到最终 .so

- **解决**: 在定义处加 `__attribute__((used, visibility("default")))` 强制导出

- **涉及文件**: `/home/administrator/vcmi-native-build/AI/MMAI/AAI/AAI.cpp` line 38



### 55. libmlclient RUNPATH 指向 build 目录

- **现象**: 新版 libmlclient.so 的 RUNPATH 包含 `/home/administrator/vcmi-native-build/rel/bin/AI`

- **后果**: 运行时从 build 目录加载 libMMAI.so 和 libvcmi.so，不是从 rel 目录

- **注意**: vcmiserver 也有类似问题——生成用`/home/administrator/vcmi-native-build/rel/bin/libmlserverplugin.so`

- **修复**: 部署时 cp 文件到 rel/ 即可（ld 优先从 rel/ 加载，build 目录作为兜底）

- **更好的修复**: 改 cmake 的 `-DVCMI_BIN_DIR` 编译参数指向 `rel/` 而非 `build/`



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



### 10. 进程内 server 代码在 libmlclient.so (C8.5)

- **现象**: 改 BattleResultProcessor (server 逻辑) 后 make vcmiserver 部署无效

- **根因**: useProcess=false → server 代码链接进 libmlclient.so (vcmiservercommon → libmlclient)

- **修复**: make mlclient 部署 libmlclient.so

- **教训**: 改 server 逻辑先验证二进制归属: grep -acl "代码内字符串" rel/bin/*



### 15. extern "C" 语法两坑 (2026-08-01)

- **坑1**: `extern "C" extern char x[64];` → "invalid use of 'extern' in linkage specification"

- **坑2**: 函数内 `extern "C"` → 非法（只能命名空间作用域）

- **正确**: 文件作用域 `extern "C" { extern char x[64]; }`（块形式）



### 16. 编译树 MMAI 旧版陷阱 (2026-08-01)

- **现象**: 战斗崩溃（neutral ASSERT, 踩坑 #11 的修复在项目源但编译树没有）

- **根因**: vcmi-native（编译树）AI/MMAI 只有 v13 结构, 项目源是 fork tip（含 v14/v15 Graphmind draft）→ 全量同步 MMAI 有编译风险; router.cpp 等关键修复文件没同步

- **修复**: 只同步关键修复文件（router.cpp neutral guard）→ 重编 MMAI

- **教训**: 编译树与项目源版本漂移是常态（AI/ML 目录: AIGateway hook、MLClient、router 都可能旧）; 编译前 diff 关键文件, 按需同步





### 25. C++ 修复写了但未同步编译树/未重编/未部署/未提交 = 修复从未生效 (2026-08-16 工作流教训)

- 现象: visitablePos 修复 2026-08-15 已写入项目源 vcmi/ML/strategic_state.cpp (git 未提交), 但编译树 ~/vcmi-native/ML/ 是旧版, 部署的 libmlclient.so (14:49) 无修复 → 8-16 训练仍全 blocked

- 原因: 改代码后只改项目源, 没有走完: 同步编译树 (cp) → 重编 (cmake --build rel --target mlclient) → 部署 (rel/bin/libmlclient.so) → 实测 → git commit

- 教训: **C++ 改动四步闭环: 项目源 → 编译树 → 编译部署 → 实测, 全部完成后才 commit**; 排查"改了没生效"先对比项目源 vs 编译树 vs .so 时间戳 (diff 三处)



### 66. 模型 AI DLL (Windows VCMI) 编译与部署坑 (2026-08-18)

- **TBB 头**: include CGHeroInstance.h 头链需 tbb/concurrent_hash_map.h (CBonusSystemNode) — oneTBB v2021.13.0 下载解压加 /I

- **tbb12.lib**: 链接缺 tbb12.lib — 安装目录 tbb12.dll (95 导出) 用 pefile+def+lib.exe 生成导入库 (同 VCMI_lib 法)

- **movementPointsRemaining 未导出**: CGHeroInstance::movementPointsRemaining 不在 VCMI_lib.dll 导出表 (__imp_ 链接失败) — 去掉移动力检查 (直接 moveHero, 失败无害); hero->pos 内联可用

- **0x618 3+AI 限制**: 官方 1.7.5/1.6 第 3+ 个 AI 玩家界面初始化崩 (0x618) — 人类模式最多 2 个 AI 玩家; 2v2 (人+ModelAI vs 2 电脑 = 3 AI) 不可行, 需 Windows 源码构建 fork 修复; 2v1 可行

- **launcher schema**: VCMI_launcher 的 AI 下拉读安装目录 config/schemas/settings.json 的 ai.enum — 加自定义 AI 名需改 enum (两个安装: D:\GAMES\VCMI 1.7.5 + D:\Program Files\VCMI 1.6); launcher 改设置写入共享 My Games\vcmi\config\settings.json

- **AI DLL 接口 (1.7.5)**: GetGlobalAiVersion/GetAiName/GetNewAI 3 C 导出; GetNewAI 返回 shared_ptr<CGlobalAI>; 纯虚: showBlockingDialog/showGarrisonDialog/showTeleportDialog/showMapObjectSelectDialog/makeSurrenderRetreatDecision/heroGotLevel/commanderGotLevel/activeStack/yourTacticPhase; 带 QueryID 的 dialog 回调必须应答 selectionMade(0,qid) 否则 "Cannot wait for dialogs" 死锁

- **回合卡死时序**: yourTurn 应答后立即 endTurn 卡死 (服务器未就绪) — 加 300ms sleep 后 endTurn 正常



#28 fork 1.8.0 Windows 构建/移动链(08-18, 见知识库 fork 构建节)

- 运行时需 PATH 含 C:\msys64\mingw64\bin(DLL 递归依赖; ldd 在 git-bash 下可能误报 0 not found)

- 重链 VCMI_lib/VCMI_client 时 POST_BUILD 删 bin/config+Mods(create_link.cmake 的 mklink /J 失败)→ 已改 file(COPY) 复制, 治本

- 用户 modSettings.json(1.7.5 旧格式)缺 vcmi 激活 → 1.8 核心 mod 不加载 → 'Built-in font/mod was not found'

- 地图必须放 bin/Maps(filesystem.json MAPS 挂载 non-initial 才索引 .h3m; 用户目录 Maps 被 initialTypes 过滤)

- --testmap 传 'Maps/图名.h3m'(资源键带 MAPS/ 前缀)

- ModelAI 移动: 1.8 moveHero(path 版) layer 参数无默认必须传 AUTO; STANDARD 模式逐格必须相邻; CGPath::getPath nodes 倒序(目标→起点), 第一步=末尾第二; 寻路 entrableTerrain 忽略非 visitable blocking(树)而 server blocked()&&!visitable() 拒绝 → AI 侧同款过滤

- AI 迷雾: AI cb 带 player → getTile 不可见崩寻路; 特权 nullopt cb 方案不可行(CBattleCallback::sendRequest 用 *getPlayerID() UB); 正确=CGameState::isVisibleFor 对 AI 返回 true(全知)

- A Warm (12,15,0) lava: client passable=1 vs server 拒绝 'destination tile is blocked' — ✅ 已解 (08-18 晚, forktest41):

  根因 = **moveHero 坐标系错配**: CPathfinder 起点是 hero->visitablePos() (NodeStorage), 而 ModelAI 用 hero->pos

  跳过起点 → 永远把自己面前格当目标发; 且 moveHero 期望 anchor 系, path 节点是 visitablePos 系, 需

  convertFromVisitablePos (NK2 同款, AIGateway.cpp:1098)。修复后 fishy 1100→0, 英雄真实移动。见技能 P30。

- obs 3464 + onnx 移植 ✅ (08-18 晚, forktest45): obs_fill.cpp (fill from CGameState, 全知直读) + obs_build.cpp (展平) +

  model_infer.cpp (onnxruntime); onnx 导出需 dynamo=False (legacy, onnxscript 装不上); **System32 有 onnxruntime 1.17.1

  会抢加载** — ModelAI.dll 编译头 1.19.2 时运行报 'requested API version [19] only [1,17]' → 必须把匹配的 onnxruntime.dll

  放 bin/AI/ (ModelAI.dll 同目录, 依赖 DLL 优先搜 AI/ 目录)。端到端: 模型驱动英雄移动 128 次, 0 崩。见技能 P31。



### 68. BattleAI.dll 手动链接必须 9 obj + stale obj ABI 漂移 (2026-08-18 晚)

- fork CMakeLists: BattleAI 是 OBJECT 库 (9 源), main.cpp 被 fork 删 → 手动 g++ -shared 重链。

- **坑 ①**: 旧 build_battleai.sh 用 `ls *.obj` 链接 — 当时目录缺 StackWithBonuses/ThreatMap 的 obj (ninja 没编),

  但旧 obj (16:19) 碰巧不引用 HypotheticBattle::makeWait, 链接过了但**运行战斗即崩** (ABI/符号不全)。

  重编全部 obj 后暴露 `undefined reference to HypotheticBattle::makeWait` → 补 StackWithBonuses.cpp.obj 即过。

  教训: 手动链接前对照 CMakeLists 源列表数 obj (9+main=10), 缺一个都要查。

- **坑 ②**: BattleAI obj (16:19) vs VCMI_lib.dll (19:27 重链) 头文件漂移 → CBattleAI::activeStack 内崩。

  任何 lib 头改动后必须 `rm AI/BattleAI/CMakeFiles/BattleAI.dir/*.obj && ninja .../*.obj` 全量重编再链。

- 验证: 9 obj 完整链接后 A Viking 5 战斗 0 崩。commit 26c4d1d (build_battleai.sh 注释)。



### 69. AI DLL static 变量跨实例共享 — red/green 同 DLL 串状态 (2026-08-18 晚)

- 现象: red/green 都是 ModelAI 时 (A Warm 2 人图), green 地下英雄 285 次 fishy — 用了 **red 视角的 passable**。

- 根因: `static StrategicState s_state` 是进程级 — 两个 CGlobalAI 实例 (red/green) 共享同一份;

  且 fill 硬编码 owner==0 (red) → green 的 yourTurn 用 red 的地形判断自己的移动。

- 修复: StrategicState 改为**类成员** + `fill_strategic_state_win(state, cb, my_color)`,

  my_color = `cc->getPlayerID()->getNum()` 在 initGameInterface 里取。obs fill 的 active_hero/team/

  relations/build-mask/enemy_threat 全部参数化 playerColor。

- 验证: red/green 均 0 拒绝 (forktest50 vs 53: fishy 460→0)。

- 通用教训: AI DLL 内任何跨回合状态必须是实例成员, static 只留给真正进程级的东西 (如 onnx session)。



### 70. 1.7.5 官方版部署 — MSVC 编译 + 缺失符号替代 (2026-08-18 晚, B 方案)

- **MinGW 无法链接 1.7.5**: VCMI_lib.dll 导出是 MSVC 修饰名 (??0CGlobalAI@@QEAA@XZ), MinGW g++ 生成 Itanium 修饰

  (_ZN9CGlobalAIC2Ev) → undefined reference (即使导出表有)。必须用 MSVC cl + VCMI_lib.lib (build_modelai_175.bat)。

- **/utf-8 必须**: 无它 MSVC 按 GBK (936) 读 UTF-8 源码, 中文注释解码出反斜杠吞掉下一行代码

  (症状: obs_build.cpp "s 未声明" / Ort 命名空间不可用 — 全是注释吞行假象)。

- **虚函数免导出**: moveHero/selectionMade/isVisibleFor 走 vtable, 无需导出符号; 只要非虚符号 (getAllVisitableObjs

  等全部导出)。

- **1.7.5 不导出的符号及替代**: movementPointsRemaining/Limit/manaLimit → 数据成员 movement/mana (protected,

  friend class hack 见 CGHeroInstance.h); CGameState::mutex → 删 shared_lock (单线程安全); map.levels() → MAX_LEVELS

  (obs 固定 2 层); ResourceSet 非 const operator[] 调 resizeContainer (不导出) → 用 const 引用; TerrainTile

  blocked()/visitable() 标 dllimport 未导出 → visitableObjects/blockingObjects 数据成员。

- **接口差异**: initGameInterface/initBattleInterface 2 参, moveHero 3 参 (无 EPathfindingLayer) — #ifdef MODELAI_175。

- 部署: AI/ModelAI.dll + AI/onnxruntime.dll (同目录优先) + 安装目录 onnx (CWD); 1.7.5 schema settings.json enum 加 ModelAI。

- 实测: 人类 vs 3 模型电脑 day=9 0 崩, 用户亲眼看到模型移动 (guitest175b)。



## 踩坑 #80: libmlclient.so 多路径加载 + BFS 目标格 blocked 豁免 (2026-08-23, Phase I.2)



### 现象

- C++ fill_next_dir 编译成功, strings 确认新代码在 .so 里, 但 reserved[0..7] 全 -1 (BFS 不命中)

- reserved[8..15] 诊断全 0 (旧代码的 for i<8 初始化), 说明 VCMI server 加载的是旧 .so



### 根因链 (6 层)

1. **.so 加载路径**: build/bin/libmlclient.so 是软链接到 vcmi-workspace/vcmi/rel/bin/ (Aug 15 旧版), 不是我们编译的 vcmi-native/rel/bin/ (Aug 23 新版)。VCMI server 通过 build/bin 加载旧 .so

2. **gicb 作用域**: fill_exploration(StrategicState*, CGameState&) 里 line 111 用了 gicb->gameState(), 但 gicb 不在该函数作用域。全局 sed 替换误伤了 line 111 (原本用 gs.)

3. **hero pos 坐标系**: heroes[ah].pos 是锚点坐标, 不是站立格。与 passable[8] 的 visitablePos() 坐标系不一致, BFS 起点错位

4. **BFS passability**: isClear(srcTile) 太严格 (terrain transition), entrableTerrain() 全 false, !blocked() 太宽松 (含水/岩浆)。正确: isLand() && isPassable() && !blocked()

5. **目标格 blocked**: 矿/资源物体让 blocked()=true, BFS 把目标格也跳过了。需豁免目标格的 blocked 检查

6. **z-level**: hero 在 z=1 (地下) 但 target 在 z=0 (地面), BFS 在地下搜永远找不到地面目标



### 修复

- .so: 复制到 4 个路径 (rel/bin, build/bin, workspace/vcmi/rel/bin, vcmi-native-build/rel/bin)

- gicb: fill_exploration L111 恢复 gs.getObjInstance(), fill_next_dir 用 gicb->gameState()

- pos: 改用 hero->visitablePos() (通过 gs.getObjInstance 获取 CGHeroInstance)

- passability: !dstTile.getTerrain()->isLand() || !dstTile.getTerrain()->isPassable() || dstTile.blocked()

- 目标格: bool isTarget = (nx==tx && ny==ty); if (!isTarget) { blocked check }

- z-level: if (tz != hz) continue;



### 验证

- 冒烟测试: 18/18 = 100% BFS 命中率 (i2_v12.json)

- 训练 ep3: 59 步 r=-2.3 avg_r=-0.0 (Phase I.1 最好 -0.4)



### 同类教训

- .so 多路径: 编译产物必须同步到所有加载路径 (build/bin 软链接不可信, 要物理复制)

- BFS passability 必须对齐引擎的 canMoveFrom: isLand + isPassable + !blocked

- visitable 对象的 tile blocked()=true 但英雄可以走到上面 -- BFS 需豁免目标格

- z-level: HoMM3 地图有地面/地下两层, BFS 必须按层搜索

- 不要用全局 sed 替换 -- 会破坏不同作用域的同名变量





### 110. BattleResultProcessor.cpp.o 旧缓存 → IFML bug 从未进部署 .so (2026-08-27)
- 现象: 源码已修复 (onlyOnePlayerHuman) 但战斗后 CBattleQuery 卡顶 (AI vs AI 也建 dialog)
- 根因: .o 是 8-2 旧缓存, 后续所有链接都用旧 .o — 源码修复 ≠ 部署修复
- 处理: rm .o + make mlclient (单文件重编成功, 不碰 strategic_state.h 就安全)
- 教训: 改 server 代码后必须确认 .o 实际重编 (ls mtime); 部署验证用行为 (CBattleQuery 卡顶)

