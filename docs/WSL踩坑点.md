# 踩坑点文档索引（AI 必读）

> 本文件 `docs/WSL踩坑点.md` 是踩坑点总索引，长期保留。
> 收到"保存踩坑点"指令时，模型写入本文件末尾「待归档新增」区（唯一方式，不自动分发到下方子文档；由用户定期自行归档）。
> 不论哪种方式，模型读取本文件后，应**自动读取下方 5 个子文档**获取完整内容。

> 内容已拆分为以下 5 个主题文档（相当于 5 个分区）：
> 1. **环境-WSL与进程** —— `WSL踩坑点-环境-WSL与进程.md`
> 2. **构建-编译与部署** —— `WSL踩坑点-构建-编译与部署.md`
> 3. **引擎-VCMI-API** —— `WSL踩坑点-引擎-VCMI-API.md`
> 4. **训练-奖励与策略** —— `WSL踩坑点-训练-奖励与策略.md`
> 5. **地图-vmap生成** —— `WSL踩坑点-地图-vmap生成.md`
>
> 每条踩坑点必须带状态字段（四选一）：✅ 已解决 / ⚠️ 待查 / ❌ 已证伪(见 #X) / 🔄 绕过中
> 引用其他条目统一用 `见 #X` 形式。

---

## 条目归属速查（按编号升序）

| 条目 | 归属文档 |
| --- | --- |
| 1a. 9p 文件系统不可用于编译 | 构建-编译与部署 |
| 1b. 方向映射不统一 → 模型坍缩 | 训练-奖励与策略 |
| 1c. MLClient.h InitArgs 头文件与 .so 布局漂移 | 构建-编译与部署 |
| 2a. cmake -S/-B 比 cd+cmake 可靠 | 构建-编译与部署 |
| 2b. canMoveBetween 太宽松 → passability 全1 | 引擎-VCMI-API |
| 2c. connector_v13.so 本体丢失 | 构建-编译与部署 |
| 3a. ENABLE_LAUNCHER/EDITOR/LOBBY 必须 OFF | 构建-编译与部署 |
| 3b. waitTillRealize=true → moveHero/endTurn 卡死 | 引擎-VCMI-API |
| 3c. adventureAlliedAI/EnemyAI 全被改成 Nullkiller2 | 引擎-VCMI-API |
| 4a. RPATH 陷阱 | 构建-编译与部署 |
| 4b. Non-red 玩家不处理 → step 超时 | 引擎-VCMI-API |
| 4c. build 目录 ServerPlugin 缺野怪保护 → NK2 打野 abort | 引擎-VCMI-API |
| 5a. cmake 自动覆盖 data symlink | 构建-编译与部署 |
| 5b. onlyai 下无 human → 所有玩家走 adventureEnemyAI | 引擎-VCMI-API |
| 6a. PCH 导致重编译巨慢 | 构建-编译与部署 |
| 6b. 采集子进程无 watchdog → NK2 启动阶段卡死挂起整条采集 | 训练-奖励与策略 |
| 7a. connector 和 libmlclient 必须 API 匹配 | 构建-编译与部署 |
| 7b. 战斗 AI 三选一全废 (C8.5 训练卡死根因链) | 引擎-VCMI-API |
| 8a. 训练和冒险测试用不同的 connector/libmlclient 组合 | 构建-编译与部署 |
| 8b. WSL 内存崩溃 (E_UNEXPECTED) | 环境-WSL与进程 |
| 9a. MSYS_NO_PATHCONV=1 必备 | 环境-WSL与进程 |
| 9b. 被动资源收入做 per-step 奖励 → 模型坚守 END_TURN (C8.5) | 训练-奖励与策略 |
| 10a. LD_LIBRARY_PATH 含空格路径会截断 | 环境-WSL与进程 |
| 10b. 进程内 server 代码在 libmlclient.so (C8.5) | 构建-编译与部署 |
| 11a. 子进程环境继承 | 环境-WSL与进程 |
| 11b. 无 playerID 的玩家 (neutral) 触发 MMAI ASSERT 崩溃 | 引擎-VCMI-API |
| 12a. DATA/LCDESC 缺失 → VCMI 初始化崩溃 | 引擎-VCMI-API |
| 12b. TerrainTile::isClear() 无 from 参数 → segfault | 引擎-VCMI-API |
| 13a. CONFIG/FILESYSTEM 缺失 | 引擎-VCMI-API |
| 13b. fill 无锁直读 CGameState → NK2 决策损坏 (2026-08-01) | 训练-奖励与策略 |
| 14a. g_adventure_cb lambda 导致 crash | 引擎-VCMI-API |
| 14b. VCMI settings 写读层不一致 → AI 分配失效 (2026-08-01) | 引擎-VCMI-API |
| 15a. env.reset() 阻塞 (战斗模式) | 引擎-VCMI-API |
| 15b. extern "C" 语法两坑 (2026-08-01) | 构建-编译与部署 |
| 16a. VCMI 关闭时 SIGSEGV | 引擎-VCMI-API |
| 16b. 编译树 MMAI 旧版陷阱 (2026-08-01) | 构建-编译与部署 |
| 17a. train_anchor.py 的 capture_output 问题 | 引擎-VCMI-API |
| 17b. 动作 8 INTERACT 从未实现 — 文档与代码脱节 (2026-08-15) | 引擎-VCMI-API |
| 18a. A1/A5 地图频繁崩溃或超时 | 地图-vmap生成 |
| 18b. swapGarrisonHero 未进城挂起 120s (2026-08-15) | 引擎-VCMI-API |
| 19a. ml-mini.vmap 的 hero 类型问题 | 地图-vmap生成 |
| 19b. moveHero 单格版只允许相邻格 + 目标必须是可站格 (2026-08-15) | 引擎-VCMI-API |
| 20a. s1.vmap 战斗模式 vs 冒险模式 | 地图-vmap生成 |
| 20b. 冒烟测试必须 MMAI 模式 — Nullkiller2 是假象源 (2026-08-1… | 引擎-VCMI-API |
| 21a. dlsym 找到旧版 strategic_state_update | 引擎-VCMI-API |
| 21b. PWD 在不同 shell 上下文中的差异 | 环境-WSL与进程 |
| 21c. bulkSplitStack 是军队内部平铺, 不能跨英雄转移 (2026-08-15 … | 引擎-VCMI-API |
| 22a. struct 尺寸不可改 | 引擎-VCMI-API |
| 22b. python3 -c 中的引号嵌套 | 环境-WSL与进程 |
| 22c. NK2 采集后期卡死 — adventure_wait 90s 超时兜底 (2026-0… | 训练-奖励与策略 |
| 23a. try/catch 吞异常导致观测全零 | 训练-奖励与策略 |
| 23b. 多个 train 进程并存 | 环境-WSL与进程 |
| 23c. OBS v3 大数值字段未归一化 → 训练数值爆炸 (2026-08-16 H.8 根因) | 训练-奖励与策略 |
| 24a. moveHero 在回调链中 segfault | 引擎-VCMI-API |
| 24b. ctypes 跨进程访问全局变量 | 训练-奖励与策略 |
| 24c. passable mask 与 moveHero 目标格不一致 — 英雄模板 visit… | 引擎-VCMI-API |
| 25a. "Player is not allowed to perform this actio… | 引擎-VCMI-API |
| 25b. GitHub 直连超时 | 环境-WSL与进程 |
| 25c. C++ 修复写了但未同步编译树/未重编/未部署/未提交 = 修复从未生效 (2026-0… | 构建-编译与部署 |
| 26a. waitTillRealize=false 对 endTurn 必要 | 引擎-VCMI-API |
| 26b. opencode 连不上服务器 | 环境-WSL与进程 |
| 26c. NK2 卡死根因 — Router battleStart 战斗模型加载失败 (2026… | 引擎-VCMI-API |
| 27a. SEND→WAIT→READ 顺序防 race | 引擎-VCMI-API |
| 27b. deepseek-v4-flash 有 45 次工具调用上限 | 环境-WSL与进程 |
| 27c. pkill/pgrep -f 匹配到自己 — bash -c 命令行含模式字符串自杀 (… | 环境-WSL与进程 |
| 28a. 两处 battle hook 防护 | 引擎-VCMI-API |
| 28b. 子 Agent 用 patch 写文件频繁失败 | 环境-WSL与进程 |
| 28c. WSL /tmp 频繁清空 — 观测日志/轨迹丢失 (2026-08-16) | 环境-WSL与进程 |
| 29a. 非红方 guard（pc!=0 直接 endTurn） | 引擎-VCMI-API |
| 29b. 子 Agent 杀死后台进程 | 环境-WSL与进程 |
| 29c. NK2 卡死 6 环修复链 — 6 环全闭环 ✅ (2026-08-16 晚, 死锁链另… | 引擎-VCMI-API |
| 30a. EmptyAI 不在 AIS 列表 | 引擎-VCMI-API |
| 30b. 子 Agent 改 symlink 后不通知 | 环境-WSL与进程 |
| 30c. 战斗后客户端收包静默 + NK2 EndTurn 死循环 — 4 层死锁修复链 (202… | 引擎-VCMI-API |
| 31a. canMoveBetween 不足够精确 | 引擎-VCMI-API |
| 31b. WSL terminate 丢失未写入文件的更改 | 环境-WSL与进程 |
| 31c. NK2 英雄交换查询死锁 — q=1 obj=1 mov=1 永久卡死 (2026-08… | 引擎-VCMI-API |
| 32. 观测维度和 ctypes 结构体偏移必须严格同步 | 训练-奖励与策略 |
| 33a. subprocess stderr=DEVNULL 吞掉 MMAI 诊断 | 构建-编译与部署 |
| 33b. TerrainTile::blocked() 是函数不是成员变量 | 引擎-VCMI-API |
| 34a. VCMI 内部重定向 stdout/stderr | 引擎-VCMI-API |
| 34b. TerrainTile::terType 不存在 | 引擎-VCMI-API |
| 34c. 有头验证 08-18: WSLg 虚拟显卡无 GPU 合成 (显示无解) / 官方 Wi… | 引擎-VCMI-API |
| 35a. init_vcmi ABI 不匹配（3-arg vs 1-arg） | 构建-编译与部署 |
| 35b. 两个 libmlclient.so 实例导致 g_strategic_state 不共享 | 构建-编译与部署 |
| 36a. CMakeLists.txt 硬编码 VCMI_DIR 覆盖 -D 参数 | 构建-编译与部署 |
| 36b. passability mask 全堵时应回退 END_TURN 而非抛异常 | 引擎-VCMI-API |
| 37a. Schema 版本冲突（BATTLE_SIDE vs BATTLE_ROUND） | 构建-编译与部署 |
| 37b. vcmi-native 缺 v14/v15/v13 constants.h 的 LINK… | 构建-编译与部署 |
| 38a. 三份 VCMI 源码各自不同步 | 构建-编译与部署 |
| 38b. v15 预存 header/impl 返回类型不匹配 | 构建-编译与部署 |
| 39. Connector 适配新 1-param init_vcmi(void*) API | 构建-编译与部署 |
| 40. 部署新 connector .so 需备份旧文件 | 构建-编译与部署 |
| 41. strategic_state_update 从未被调用 | 引擎-VCMI-API |
| 42. strategic_state.h ABI 不匹配（Windows vs WSL） | 引擎-VCMI-API |
| 43. CMake /DEF: 标志导致 MinGW ld 链接失败 | 构建-编译与部署 |
| 44. vcmi-native 和 vcmi-native-build 两份源码不一致 | 构建-编译与部署 |
| 45. CCallback::gameState() 在 yourTurn 回调时返回空 CGa… | 引擎-VCMI-API |
| 46. g_strategic_state->action 不被 adventure_send_… | 引擎-VCMI-API |
| 47. `extern "C"` 不允许嵌套 | 构建-编译与部署 |
| 48. selectionMade 在 moveHero 前导致服务器拒绝+segfault | 引擎-VCMI-API |
| 49. strategic_state_update / fill_state_from_cb … | 引擎-VCMI-API |
| 50. installNewBattleInterface 中性玩家 crash | 引擎-VCMI-API |
| 51. MMAI constructor symbols 需强制导出 | 构建-编译与部署 |
| 52. MMAI callback throw 导致进程 abort | 引擎-VCMI-API |
| 53. Hero pool even number 检查 kill 游戏 | 引擎-VCMI-API |
| 54. ServerPlugin artifact loop 空 hero 指针 | 引擎-VCMI-API |
| 55. libmlclient RUNPATH 指向 build 目录 | 构建-编译与部署 |
| 56. Post-init segfault — Discord null reference … | 引擎-VCMI-API |
| 57. 信号量通信修复 — AAI::yourTurn 阻塞等 Python action ✅ … | 引擎-VCMI-API |
| 58. VCMIGYM_DEBUG=1 导致 importerror | 引擎-VCMI-API |
| 59. getHeroesInfo() 在 selectionMade 前返回空 | 引擎-VCMI-API |
| 60. g_ml_player_cb — 全局 CCallback 指针传参 | 引擎-VCMI-API |
| 61. CGameInfoCallback 比 getHeroesInfo 更可靠 | 引擎-VCMI-API |
| 62. VCMI stdout 重定向吞掉 Python print | 引擎-VCMI-API |
| 63. adventure_process_turn 缺日历/地图填充 | 引擎-VCMI-API |
| 64. EEXIST — boost::create_directories 对符号链接失败 | 构建-编译与部署 |
| 65. 旧模型权重编码旧 obs 模式 — 清权重才能受益于新 obs | 训练-奖励与策略 |
| 66. 模型 AI DLL (Windows VCMI) 编译与部署坑 (2026-08-18) | 构建-编译与部署 |
| 67. fork 战斗链从未可用 — 任意战斗触发即崩 0x98, 双根因 (2026-08-1… | 引擎-VCMI-API |
| 68. BattleAI.dll 手动链接必须 9 obj + stale obj ABI 漂移… | 构建-编译与部署 |
| 69. AI DLL static 变量跨实例共享 — red/green 同 DLL 串状态 … | 构建-编译与部署 |
| 70. 1.7.5 官方版部署 — MSVC 编译 + 缺失符号替代 (2026-08-18 晚… | 构建-编译与部署 |
| 71. WSL 与 git-bash 环境坑 (2026-08-19 记忆迁移) | 环境-WSL与进程 |
| 72. ModelAI 战斗后回合挂死 — yourTurn 线性执行 (2026-08… | 引擎-VCMI-API |
| 73. PPO 策略坍缩链 — 横跳 → END_TURN 刷步 (2026-08-19) | 训练-奖励与策略 |
| 74. MOVE_TO 目标漂移 — 每步重选最近目标 → 来回走 (2026-08-1… | 训练-奖励与策略 |
| 75. python 补丁脚本残留中文注释拼接 — U+2014 SyntaxError… | 环境-WSL与进程 |
| 76. ep_runner 缺 import numpy — 被动作… | 训练-奖励与策略 |
| 77. logits 偏置对模型从未见过的动作码无效 — 引导用采样… | 训练-奖励与策略 |
| 78. 强制引导动作空转 — MOVE_TO 无目标时原地 27 步 (2026-08-… | 训练-奖励与策略 |
| 79. 动作循环惩罚诱发 END_TURN 穿插投机 (2026-08-19, 第 7 … | 训练-奖励与策略 |
| 80. libmlclient.so 多路径加载 + BFS 目标格 blocked 豁… | 构建-编译与部署 |
| 82. 地形栅格 — _init_baselines 覆盖 + 双 .so 内存隔离 (… | 训练-奖励与策略 |
| 83. ep_runner load_state_dict 缺 strict=False… | 训练-奖励与策略 |
| 84. vmap players 数组格式 → 引擎加载即 core dump | 地图-vmap生成 |
| 85. vmap hero 标识符 core:inham 不存在 | 地图-vmap生成 |
| 86. vmap terrain shortIdentifier: rock=rc 非 ro; … | 地图-vmap生成 |
| 87. vmap 非草地地形 (wt00_/rc00_) 加载 segfault (⚠️ 待查) | 地图-vmap生成 |
| 88. vmap town mask 5x3 越界 → segfault (根因链核心) | 地图-vmap生成 |
| 89. vmap resource 对象 options 需 amount | 地图-vmap生成 |
| 90. VCMI 生物标识符: footman 不存在, 是 swordsman | 引擎-VCMI-API |
| 91. vmap 非草地地形崩溃是 VCMI 1.7.x 共有 bug (1.7.5 也崩), … | 地图-vmap生成 |
| 92. T05/T06 旧 dict 版也含崩溃地形 (rd/ro/wt/sa) + T05 t… | 地图-vmap生成 |
| 93. optimizer.load_state_dict(strict=False) Type… | 训练-奖励与策略 |
| 94. "vmap 非草地 segfault" 是误判 — 真因是 NK2 守卫战斗断言 (AA… | 地图-vmap生成 |
| 95. 杀训练 worker 认准 python3 PID, bash 包装不是 worker | 引擎-VCMI-API |
| 96. NK2 移除 → critic 爆炸 (vloss 159-164) (2026-08-… | 训练-奖励与策略 |
| 97. Level 3 经济动作引导失败 → 模型毒化 (2026-08-24) | 引擎-VCMI-API |
| 98. L1/L2 checkpoint 丢失 (2026-08-24) | 引擎-VCMI-API |
| 99. entropy=-0.01 正r率 15%, -0.05 → 27% (2026-08-… | 引擎-VCMI-API |
| 100. 训练意外停止无保存日志 (2026-08-25 09:51) | 训练-奖励与策略 |
| 101. hermes voice 禁用了还自动触发 wake word = 旧进程未重启 (2… | 环境-WSL与进程 |
| 102. 守卫被访问消失无战斗 = takenAction 评估 JOIN/FLEE (2026… | 引擎-VCMI-API |
| 103. 守卫格 passable=0 → 模型绕开守卫 (2026-08-26) | 引擎-VCMI-API |
| 104. 先占矿守卫消失 → 战斗永不触发 (2026-08-26) | 引擎-VCMI-API |
| 105. C++ 重编环境崩 (纯 8-23 源码重编也 core dump, 未解) (202… | 引擎-VCMI-API |
| 106. local_tiles[1] 填实例 ID 非类型 + 守卫战力通道边界噪声 (202… | 引擎-VCMI-API |
| 107. 守卫清除检测 = 战斗机制的 Python 等价 (2026-08-26) | 引擎-VCMI-API |
| 108. vmap aggression 字段无效 → 守卫恒 FLEE (2026-08-27) | 地图-vmap生成 |
| 109. 运行时地图目录 ≠ 项目 Maps/training (2026-08-27) | 地图-vmap生成 |
| 110. BattleResultProcessor.cpp.o 旧缓存 → IFML bug … | 构建-编译与部署 |
| 111. MMAI yourTurn 轮询阻塞事件循环 → 战斗回调死锁 (2026-08-27) | 引擎-VCMI-API |
| 112. garrison dialog AI 应答后查询栈卡 (2026-08-27) | 引擎-VCMI-API |
| 113. make POST_BUILD 生成坏 data 符号链接 → EEXIST (202… | 引擎-VCMI-API |
| 114. WSL2 idle shutdown 杀训练进程 (2026-08-28, v4 段 … | 环境-WSL与进程 |
| 115. QueryID=-1 断言雷 (AAI.cpp) 引爆训练空转 (2026-08-29… | 引擎-VCMI-API |
| 116. reward clip 下限 -10 把失败 -200 剪没 → T04 输赢信号失真… | 训练-奖励与策略 |
| 117. T04"有目标却乱逛"三连环: 近目标吸住 + 强制期不够长 + 城镇不在 targe… | 训练-奖励与策略 |
| 118. 21×21 CNN 地形栅格 ≠ 对象视野 (语义混淆) (2026-08-29) | 训练-奖励与策略 |
| 119. 引擎实际加载地图 = cwd/data/Maps 部署副本 (2026-08-29) | 地图-vmap生成 |
| 120. PowerShell 传 wsl bash -c 复杂命令的引号/$ 展开坑 (202… | 环境-WSL与进程 |
| 121. economy_force 50 步空转学费过重 → 24 步定版 (2026-08-… | 训练-奖励与策略 |
| 122. [ECON] 事件不进主日志转储词表 → 观察盲区 (2026-08-29) | 训练-奖励与策略 |
| 123. T04 分层误读三连: 无守卫/深负来源/win_rate 失真 (2026-08-2… | 训练-奖励与策略 |
| 124. first 奖励被强制期截胡 → 自主动作零信号 (2026-08-29, 自主 16… | 训练-奖励与策略 |
| 125. C++ 符号排查 grep 模式坑: typeinfo/vtable 是 mangled 名 (08-31) | 构建-编译与部署 |
| 126. cmake 重编 build type 覆盖坑: Release 触发 strip → 953KB 空壳 .so (08-31) | 构建-编译与部署 |
| 127. cmake 增量操作顺序坑: set_target_properties 需重 configure / rm 须在 cmake 前 (08-31) | 构建-编译与部署 |
| 128. ep_runner_one.py 无 __main__ 保护: import 即跑主流程 (08-31, ≈#156) | 训练-奖励与策略 |
| 129. 日志方括号事件词前缀匹配坑: grep '\[TOWN' 把 [TOWN_BLOCKED] 一起算 (08-31) | 训练-奖励与策略 |
| 130. PowerShell 双引号内 $(...)/$var 子表达式展开: wsl 复杂命令被撕裂 (09-02, ≈#154) | 环境-WSL与进程 |
| 131. 编译 -j8 与训练并发压死 WSL: 0x8007274c 连接失败 (09-02) | 环境-WSL与进程 |
| 132. 主日志选择性转储白名单: [ECON]/[RECRUITED] 不进 | 训练-奖励与策略 |
| 133. VCMI 1.8 getUpperArmy() 不含 visiting hero | 引擎-VCMI-API |
| 134. fprintf(stderr) 在 MMAI server 内不可见: console 重定向 | 引擎-VCMI-API |
| 135. Python 补丁脚本三连坑: % 格式化 / 锚点缩进 / while 不前进死循环 | 环境-WSL与进程 |
| 136. C++ 诊断代码远程生成三连坑: 引号拼接 / 尾杂引号 / 作用域外引用 | 环境-WSL与进程 |
| 137. VCMI 坐标系双口径坑: 锚点 pos vs visitablePos | 引擎-VCMI-API |
| 138. SearchReplace 模糊匹配残片: old_str 微差致插入错位 | 环境-WSL与进程 |
| 139. /mnt/d venv 已不存在: systemd-run 相对路径启动失败 | 环境-WSL与进程 |
| 140. C++ API 假设编译前必 grep 验证: typeName() 实为 getTypeName() | 引擎-VCMI-API |
| 141. WSL 断网 + Windows 有网: 双机协作下载方案 (09-03) | 环境-WSL与进程 |
| 142. C++ if 无花括号 + fprintf 抢作用域: 招兵循环 UB 潜伏爆雷 (09-03) | 构建-编译与部署 |
| 143. vmap 地图加载事实集: footman 缺失 / 运行时路径 / 英雄格阻挡 (09-03, 事实 4-6 后补) | 地图-vmap生成 |
| 144. MOVE_TO 翻译层认知坑: act 无 24 ≠ 强制窗失效 (09-09) | 训练-奖励与策略 |
| 145. T06 守卫格振荡陷阱: 站上格黑名单失效 → fail-count 贴脸计数 (09-09) | 训练-奖励与策略 |
| 146. BHERO_KILL 空拍误报: live_slots=0 = heroes 段整段空 (09-09) | 训练-奖励与策略 |
| 147. 间歇性局级慢速: fuse 雷达外的 4-8s/步模式 (09-09) | 训练-奖励与策略 |
| 148. GUI 死锁根因: detached 线程持锁路径退出 → interfaceMutex 永久失锁 (09-09) | 引擎-VCMI-API |
| 149. 多进程齐崩 = 系统资源耗尽特征, 勿误判应用代码 (09-09) | 环境-WSL与进程 |
| 150. Windows minidump 抓取与解析三坑 (09-09) | 环境-WSL与进程 |
| 151. Windows GUI 中文界面 + 第三方输入法: 两条独立崩溃路径 (09-09) | 环境-WSL与进程 |
| 152. fork Windows 构建 AI DLL 缺失: settings 默认名无对应产物 (09-08 闭环, 09-09 编号) | 构建-编译与部署 |
| 153. [GUARD]/[MINE] 位置重合判据 anchor↔visitable 失真: 1442 条假糖 + 真战斗漏奖 (09-10) | 训练-奖励与策略 |
| 154. PowerShell 包裹 wsl bash -c 时 $var/$( ) 被 PowerShell 层吃掉 (09-10, ≈#130) | 环境-WSL与进程 |
| 155. pkill -f 同名串自杀: 当前 shell cmdline 含目标名即被自己杀 (09-10, ≈#27) | 环境-WSL与进程 |
| 156. import ep_runner_one 有模块级副作用: 会初始化 env 并跑游戏 (09-10, ≈#128) | 训练-奖励与策略 |
| 157. 局耗时数据不可回溯: hermes 日志逐局覆盖 + ep 行无 time 字段 (09-10) | 训练-奖励与策略 |
| 158. interfaceMutex 泄漏: onPacketReceived 锁作用域收窄破坏 makeUnlockGuard 不变量 (09-10, 死锁根因①) | 引擎-VCMI-API |
| 159. SPECTATOR 无 PlayerState: getPlayerState(-4) 返回 null 无判空崩溃 (09-10, 死锁修复后第二层) | 引擎-VCMI-API |
| 160. winpthreads Normal mutex 不记录 owner: dump 静态分析定不出持锁者 (09-10) | 引擎-VCMI-API |
| 161. MinGW windows.h 宏污染三连: IGNORE / NOMINMAX / 作用域 (09-10) | 构建-编译与部署 |
| 162. fork Windows 重编四坑: genex 泄漏 / 链接序 / 缺符号 / 数据目录 (09-10) | 构建-编译与部署 |
| 163. 二进制 ≠ 源码树: 08-18 exe 含未提交临时 hack, 行为对不上源码 (09-10) | 构建-编译与部署 |
| 164. MSYS2 ninja 编译 cc1plus 静默失败 0xC0000135: PATH 缺 mingw64\bin (09-10) | 构建-编译与部署 |
| 165. GUI 线程边界无 catch-all: 未捕获 C++ 异常 → "Disaster happened" + 僵尸进程 (09-10, 第五崩) | 引擎-VCMI-API |
| 166. identifier 校验集混入 subtype 字段值: core:alchemist 拒启动 → 1 步空壳局 | 地图-vmap生成 |
| 167. ServerPlugin HeroPool 对称校验拒多敌课程: 1v3/1v7 全部无法启动 | 引擎-VCMI-API |
| 168. transient unit 停止即消失: systemctl start 报 Unit not found (09-08 补 is-active 陷阱) | 环境-WSL与进程 |
| 169. 隔夜中断形态与恢复序: keepalive 丢失 → 非优雅关机 → checkpoint 回滚 | 环境-WSL与进程 |
| 170. 多 resume 日志取"最后一次启动后窗口"的 awk 陷阱: tac|awk|tac 返回全文件 | 训练-奖励与策略 |
| 171. ".so 待重编"登记未验 target 归属: 改 A 源码却去编 B 库 | 构建-编译与部署 |
| 172. fork Windows 构建 DLL 污染: 24 种 GCC 版本混装 = 内存损坏 | 构建-编译与部署 |
| 173. 官方 VCMI 1.7.5 与 fork ModelAI.dll ABI 不兼容: MSVC vs GCC name mangling | 构建-编译与部署 |
| 174. VCMI 数据目录隔离实验结论 | 构建-编译与部署 |
| 299. #296 勘误+降噪: `Cannot answer the query -1` 实锤 `lib/callback/CCallback.cpp:53` (lib 非 mlclient) + Popen grep -v 管道降噪 (09-23) | 引擎-VCMI-API |
| 修复链 | 引擎-VCMI-API |

> 注：#57 有重复，以"信号量通信修复"为准，另一份（MMAI_USER battle hang）损坏未恢复已剔除；#80 有重复，以完整副本为准，损坏副本已剔除。

> ℹ️ **编号修正 (09-11)**：原 (09-06~09-08) 组 #132~#140 与 09-02/09-03 早期组重号（历史写入冲突），已改号为 **#166~#174**（完整映射见「待归档新增」区组头与元数据说明）；速查表与正文均已同步更新，`#132(09-06)` 等旧写法不再有效。
> ✅ #125~#174 共 50 条已于 09-11 全部分发归档至 5 个主题子文档（正文已移出本文件，本表为唯一索引）。

---

## 待归档新增（收到"保存踩坑点"时追加于此）

> 此区为新增踩坑点暂存区。用户定期自行归档到上方 5 个主题子文档后，再从本区移除。
> 新增条目沿用全局编号续接（当前最大 **#309**，下一条为 #310…），每条须带状态字段（✅/⚠️/❌/🔄），引用其他条目用 `见 #X`。
> ℹ️ **重号提示 (09-24)**：现有**两条 #300**——L1556（池图开局故障根因修正）与 L1684（关机后 keepalive 静默丢失），后者建议归档时改号。**同日已处理掉另一批重号**：原编 #301（unit 双副本漂移）→ **#306**、原编 #302（/tmp EPERM）→ **#307**（因 #301/#302 已被 trade cap 与 merge-tree 口径占用）。
> ℹ️ 编号修正 (09-11)：原 (09-06~09-08) 组 #132~#140 与早期组重号，已改号为 #166~#174：#132→#166 / #133→#167 / #134→#168 / #135→#169 / #136→#170 / #137→#171 / #138→#172 / #139→#173 / #140→#174。

> ✅ **归档完成 (09-11)**：原待归档 50 条已全部分发至 5 个主题子文档（环境 14 / 构建 13 / 引擎 10 / 训练 11 / 地图 2）。

> ✅ **归档完成 (09-24)**：原待归档 138 条（#175~#309）已全部分发至 5 个主题子文档（引擎 32 / 构建 28 / 环境 19 / 训练 27 / 地图 21，编号沿用主文档全局编号）。本区清空，后续新增踩坑点仍追加于此。

---

## 09-25 PPO-DNA 并行化（N_SUBPROC=4）新增踩坑

### #310. 并行路径 Popen 池化结构 bug — for ep 循环 N 轮后退出，buffer 永远攒不满 ❌ 已修复（09-25）

- **现象**：灰度 N=4 后训练秒退 `DONE: 0eps 1012552steps 0s`，4 个 ep_runner 同时 Popen 但没进 PPO 更新
- **根因**：并行路径 `for ep in range(N_EPISODES)` 只迭代 1000 轮，每轮 `while` 阻塞等 buffer 攒满；但 4 slot 每局 300s+，1000 轮内 buffer 永远攒不到 BATCH=2048，循环走完直接退出
- **修复**：`while` 阻塞攒满后 `continue` 跳出当轮 for ep → 进 PPO 更新块 → 下一轮 for ep 的 `_spawn_slots` Popen 新版模型。Popen 后 slot 全空（proc=None），PPO 更新后再 Popen 新版
- **教训**：并行路径需要独立的「Popen → 阻塞攒满 → PPO 更新 → 重新 Popen」循环模型，不能复用串行的 `for ep` + `if len(buffer)>=BATCH` 自然触发结构

### #311. _spawn_slots cmd 构造漏 move_to_force/act_loop_from_step 按 map 前缀分支 ⚠️ 已补全（09-25）

- **现象**：初版并行路径 `_spawn_slots` 的 cmd 缺 `--move_to_force`/`--act_loop_from_step`/`--move_to_bias`/WIN1_ENV_ARGS 注入，与串行 `run_episode` 不一致
- **根因**：初版简化用「默认值 + runner 内部 args 兜底」，但 T06 的 `move_to_force` 分支（duel=60 / 非duel=250）依赖 `run_episode` 里按 map 前缀的 cmd.extend，runner 内部只有部分兜底
- **修复**：补全 cmd 与 `run_episode` L254-318 逐条对齐（HERMES env 化 + move_to_bias/force 按 map 前缀 + T06 act_loop_from_step=60 + WIN1_ENV_ARGS 注入 + #296 grep 降噪管道），确保 N=4 时策略输入 = N=1 完全一致
- **教训**：并行路径不能「简化 cmd」，必须与串行路径逐条对齐，否则 N>1 时策略行为漂移（隐性 bug，不报错但策略学偏）

### #312. WSL 默认内存上限 = 物理内存 50%，N=4 子进程池需前置扩 .wslconfig ✅ 已扩（09-25）

- **现象**：实测 WSL `free -h` 总内存 7.6Gi（Windows 物理 15.7GB 的 50%），无 `.wslconfig` 时 WSL 默认锁死 50% 策略
- **影响**：4 ep_runner × 0.9GB + 主进程 0.9GB = 峰值 4.5GB 占 7.6Gi 的 59%，NK2 大图局峰值无余量 → 必 OOM
- **修复**：创建 `C:/Users/Administrator/.wslconfig`（memory=12GB + swap=4GB）+ `wsl --shutdown` 重启 → 实测 WSL 总内存 11Gi，N=4 降到 38%，留 ~6GB 安全垫
- **教训**：WSL2 无显式 `.wslconfig` = 默认 50% 物理内存上限；多子进程并行化前必须实测 `free -h` + 确认 `.wslconfig` 已扩

### #313. save_shutdown 清理 slots 时 NameError（slots 定义在 save_shutdown 之后）✅ 已防御（09-25）

- **现象**：`save_shutdown`（L546）注册在 `slots` 定义（L610）之前；若 SIGTERM 在 slots 定义前到达 → `for s in slots` 触发 NameError → 保存失败
- **根因**：Python `global slots` 延迟求值，但函数体执行时 `slots` 未定义
- **修复**：`if "slots" in globals():` 防御（slots 定义前 SIGTERM 跳过清理，此时无子进程残留）
- **教训**：模块级注册信号处理器 + 全局变量定义在处理器之后的代码，必须加 `globals()` 防御

### #314. `[SLOT] 全崩兜底` 日志措辞误导（正常 batch 满跳出被命名为"全崩"）✅ 已改（09-25）

- **现象**：N=4 并行日志满屏 `[SLOT] 全崩兜底: buffer=2182/2048, 跳出进 PPO 更新`，用户误判为 4 个子进程全崩
- **根因**：L815 `if all(s["proc"] is None and s["traj"] is None)` 在 4 slot 正常并行完成（4 局同时跑完 → 同时 poll 完成）时**必然为 True**（设计内 batch 满跳出），却被打印成"全崩兜底"；且 `rc=0` 才是健康标志（子进程正常退出码），日志却与"全崩"并列
- **修复**：改措辞 → L815 `[SLOT] batch 满 (buffer=X/2048), N slot 回收完毕, 跳出进 PPO 更新`；L420/L719 `[FILTER] obs_nz=0` 从「脏样本」改为「首拍全零丢弃 (reset 冷启动竞态/地图 header.players 缺陷)」点明两类根因
- **教训**：日志措辞必须与触发语义严格对齐；「兜底」「全崩」等强语义词若触发条件是设计内常态，会系统性误导排查方向。`rc=0`=健康退出 / `rc≠0`(−6 SIGABRT / −11 SIGSEGV / −15 SIGTERM)=崩溃，是判断子进程健康的唯一真锚点

### #315. H3M 池图首拍 obs 全零 = 三层叠加根因，非单一"引擎 reset 竞态" ⚠️ 排查结论（09-25）

- **现象**：N=4 灰度里 H3M 池图（King_of_Pain/good_to_go/judgement_day）偶发 `[FILTER] obs_nz=0 首拍全零丢弃`，课程图（T04/T05/T06）几乎不出现
- **三层根因**（按证据强度）：
  1. **地图 `header.players=[]` 空数组（确定性，已修 #222/#223）** — 主因。`h3m2vmap` 工具链导出时漏注入 `header.players` → 引擎不建玩家槽位 → obs 城段 owner 全 0 → runner `no_own_town` abort（`ep_runner_one.py` L762-778）→ 首拍全零。King of Pain 早期 10/10 局全脏即此（#222 修后归零）。**这是确定性地图缺陷，非偶发竞态**
  2. **引擎 reset 冷启动竞态（偶发 ~4%，#214 残余）** — `strategic_env.py` L690 `_adventure_wait()` 300s 内未收到 yourTurn 回调 / obs 填充线程未就绪 → `return np.zeros(OBS_DIM)`；H3M 72×72/108×108 大图 reset ~600s 竞争窗口大
  3. **XDG 目录缺失（已修 #308，独立故障线）** — `$HOME/.local/share/vcmi/` 不存在 → `.vmap` 加载失败误报 Permission denied → SIGABRT rc=−6 丢 traj（走 `[WARN] traj 读取失败` 分支，**不是 obs_nz=0 分支**，两条故障要分开看）
- **#228 不同源**：#228「obs 3464 修复」实为败北信号断链根修（局末 PvP 战斗结算挂起 → game_over=2 刷新），是局末问题，与局首 reset obs 全零无因果
- **排查工具**：`py/_scan_h3m_players2.py`（raw 字节级读 .vmap players 段，临时脚本查完即删）；权威预检走 `py/sync_maps_to_runtime.py --strict`（自带 header.players 预检+原子写+写后校验）
- **下一步**：N=4 灰度若 H3M 池图仍见 `[FILTER] obs_nz=0`，优先跑 `sync_maps_to_runtime.py --strict` 验在池 3 张 H3M 的 `header.players` 是否修净（确定性根因 L1），而非归因"竞态"

---

## 09-26 T14.2b 冒烟（t14-handicap 纯 JSON mod）新增踩坑

### #316. obs 资源槽 log1p 压缩，int() 取整造成「A/B 曲线重合=mod 没生效」假象 ⚠️ 定案（09-25 冒烟最大误判源）

- **现象**：t14-handicap B 组（king gold 15000）vs A 组（10000），直接 `int(obs[gold])` 对比逐帧曲线 → 完全重合 → 误判「mod 没流入引擎」
- **根因**：obs 资源槽是 `np.log1p` 压缩值（`strategic_env.py` L454-462 `_LOG1P_COLS`：players gold(+2)/total_power(+12)/weekly_income(+13)）。log1p(10000)=9.21、log1p(15000)=9.62，`int()` 都压成 9 → 假重合
- **修复/判据**：读 raw 必须 `np.exp(obs)-1` 反算。ridiculous 值铁证法（king gold 临时 500000）：B 组 obs 反算 raw=500000 原样进引擎，双通道（start resources + weekly income）确认生效
- **通用教训**：凡 obs 对比实验先查该槽是否在 `_LOG1P_COLS`，压缩槽禁止 int 取整直比

### #317. `wsl -d Ubuntu -u root bash -c` 嵌套层 shell 变量展开失效 ⚠️ 已踩（09-25 冒烟脚本调试）

- **现象**：嵌套 `bash -c "..."` 里 `$VAR` 展开被外层/内层引号吃成空串，路径命令静默跑错目录
- **修复**：一律字面路径或写 `.sh` 脚本文件执行；不靠嵌套展开。WSL 内路径统一字面量（`/home/administrator/...`）

### #318. WSL 同步后 vcmi 仓 CRLF 行尾噪音（94 行 diff） ⚠️ 已挡（09-25）

- **现象**：Windows↔WSL 同步后 vcmi 仓工作区满屏 CRLF↔LF 行尾 diff，`git diff --stat` 几百行但内容零改
- **修复**：提交前 `git add --renormalize .`（或按文件 `git checkout`）洗行尾，只带真内容改；diff 前 `git diff -w` 先扣 whitespace 看实际改动

### #319. t14-handicap 通道 B JSON key 拼写 `weeklyBonusesAI`（带 es）四方定谳 ⚠️ 定案（09-25/09-26）

- **现象**：T14.2b 做 mod 时 C++ 枚举名是 `RESOURCES_WEEKLY_BONUPS_AI`（**无 es**，官方 VCMI 历史 typo），手滑把 mod.json 的 JSON key 也照抄成无 es 版 → 被 schema `additionalProperties:false` **静默拒收**（不报错，通道 B 直接 0 效果）
- **定谳（字节级四方一致）**：合法 JSON key = `weeklyBonusesAI`（**带 es**）——`config/schemas/gameSettings.json`、官方 `gameConfig.json`、`GameSettings.cpp` L120 三元组、mod.json 四处全带 es；**仅 C++ 枚举名无 es（官方 typo）**，两侧本来就不一致
- **坑点**：`mod.json settings` 走 schema 校验（`additionalProperties:false`），错一个字母不报任何错、只是该字段被丢弃 → 表现为「mod 加载 OK 但通道 B 无效果」，极易误判为「mod 没生效」（与 #316 log1p 假象叠加成双重误判源）
- **判据/防再踩**：改 mod settings 后必跑 ridiculous 值探针（临时拉满数值看 obs 反算 raw 是否原样进引擎）——本次 weekly 通道 s29 income 8.16→10.24 即靠此坐实 key 被正确消费

---

## 09-26 P1 引擎窗口三项收口（298 对照定谳 / #215 守卫重写 / connector 重编）新增踩坑

### #320. 09-19 上游 1160 文件重同步冲掉 #215 全部 headless 守卫，且原 commit 65515ef24 随 rootfs 事故永久丢失 ⚠️ 已重写（09-26）

- **现象**：P1-3 排期写「#215 13 处 `if(ENGINE)` 守卫待 commit」，实际核树发现工作树 `client/` 对 HEAD 干净且守卫只剩上游自带的 9+1 处——09-16 的 14 处守卫（commit 65515ef24）被 09-19/09-23 上游全量重同步（`375fba919e` 1160 文件）整段冲掉
- **丢失坐实**：65515ef24 对象在 WSL 仓 / D 盘全部镜像仓 / 09-19 rootfs 备份 tar 的 .git 里均 `cat-file -t` 失败（随 09-18 WSL 引擎 2.7.10 自建 distreg、旧 rootfs 丢弃而灭失，#269 同族）；09-19 备份树同样只剩 9+1 处 → 原始 diff 无法捞回
- **处置**：按 fact_store #215 记录语义重做，收敛为 P8 终局热路径**最小 6 处**（CSH sendRestartGame / sendStartGame CLoadingScreen 双分支 + showHighScores + endGameplay discord + showServerError；Client.cpp removeGUI 二次崩点），工具 `py/patch_215_engine_guard.py`（幂等 + 锚点校验 + .bak_215 rollback）
- **通用教训**：上游全量重同步 = 未入库的补丁全灭；守卫类修复必须当窗 commit，不能留「待正式 commit」——本次跨仓欠账挂了 10 天就是反例。核守卫存活不能只信任务清单，要 `grep -c 'if (ENGINE)'` 对文件实读（注意带空格的 `if (ENGINE)`，无空格 grep 会假阴性）

### #321. .so 级 .bak 快照（libmlclient.so.bak_*298）是 09-23 的，直接 rollback 会误伤 09-24 提交 → 改用源码手术式逆向 ✅ 已用（09-26）

- **现象**：P0-2 对照实验要「回退三套 298 重编」，树里现成的 `.so.bak_stk298/.bak_netfix298/.bak_298_0923` 全是 09-23 快照——回退到 09-23 会连带丢 09-24 的 [ML-time] trade cap / force game_over 独立提交，且 09-24 之后源码（AIGateway）又改过，.so 快照与源码树不对齐
- **修复**：新工具 `py/revert_298.py`——import 三套 patch_298_*.py 的 EDITS 常量（与正向同一份 anchor/new 字符串），对每项做 `new→anchor` 精确逆向，不碰其他改动；`apply` 子命令可重放恢复。预检（revert check）19 项中 18 项可逆，BR 那 1 项 stk 锚点在 09-19 上游同步里被改动过当时就没打上 → 跳过即正确
- **通用教训**：竞态类对照实验的「基线」必须 = 现树精确逆向目标改动，不能用旧快照；每次用旧 .bak/.so 前先核 mtime 对应的提交

### #322. 298 三套 A/B 对照定谳 = 全留（压制，非根修）⚠️ 定案（09-26，N=4 + 基线对照）

- **实验**：同 4 图（good_to_go / judgement_day / elbow_room / a_viking）× 4 轮 30 步，A 臂 with-patches（09-24 .so 原态）vs B 臂 baseline（revert_298.py 逆向三套 → 重编 libvcmi/libmlclient，保留 [ML-time]/force/tradecap）
- **结果（复现率口径，#298 纪律）**：A 臂 16/16 全 rc=0 零冻结；B 臂 4/16 rc=0 + **12×rc=124 超时冻结**（judgement_day 4/4、a_viking 4/4、elbow 3/4、g2g 2/4）→ 与 09-23「基线即 4/6 异常」A/B 记录方向一致且大幅强化
- **定谳**：三套 298（栈打点 / 方案1 跳过等待 / upgrade 熔断 cap 8）**全留**——打点不撤（当哨兵），方案1 + 熔断留（A 臂健康局 0 误触发 = 只在真死锁才动手）
- **边界**：这是**压制非根治**——with-patches 臂 16 局零冻结是采样证据，冻结根因（AI EndTurn realize 死锁 / Mode B 架构级）仍在，终局后你的 turn 永不再来类问题靠 force game_over 兜底；根治方向另排（知识库 09-23 章三档）
- 证据目录：`/home/administrator/_298_p1_20260926/`（arm_a.txt / arm_b.txt + 32 份逐局 log + build log，rootfs 持久）

### #323. stats db 三连环：statsStorage 默认 "-" + rootfs 事故丢表 + P8 冒烟卡开局 ⚠️ 已解锁（09-26）

- **现象**：#215 重编后 P8 p8c_query_reply 冒烟 `game_started=False`（exit=2 或 0），server 日志 `Failed to launch game: no such table: stats`；建表后又报 `side check failed: no rows in stats_md` → seed 行；再报 `side in DB is 1, want 0` / `npools want 1`
- **根因链**：server ML 插件 `Config.h` 默认 `statsStorage="-"`（cwd 开名为 `-` 的空 sqlite）+ `statsMode="red"` 默认开启 → 09-18 rootfs 事故（#269）把 db 文件/表全丢 → 每次开局 verify 挂死。`rel/bin/-` 是 0 字节空文件，表结构在 `server/ML/sql/structure.sql`
- **修复（双保险）**：① python sqlite3 对 `rel/bin/-` 执行 structure.sql 建 `stats` + `stats_md` + seed 行 `(side=0, n_pools=1, pool_size=2)`（seed 值必须与 InitStats 的 npools/poolsize/side 参数一致，跑一次看 server 报错 `want: X` 回填）② `data/config/settings.json` 写 `server.ML.statsMode=disabled`（P8/训练链路都不用 Stats，彻底关）
- **通用教训**：`statsMode` 默认 "red" 是隐雷，任何 rootfs/db 重置后 P8 类冒烟首跑先查 `no such table`；seed 行参数别猜，跟报错抄

### #324. WSL idle shutdown 4 连重启带走后台实验 + /tmp 输出（踩坑 #201 重犯）⚠️ 已拉 keepalive（09-26）

- **现象**：P1 开工时 P1-2 A 臂后台 16 局跑到第 3 局（09:18）被 WSL 重启全清，09:18/09:20/09:22/09:35 连重启 4 次，`/tmp/_298_p1_20260926/` 输出目录整个消失，`last reboot` 铁证
- **根因**：keepalive `wsl --exec sleep infinity` 未拉起（踩坑 #201/#267 勘误：idle 判定只看 Windows 侧客户端，WSL 内进程再忙也照关）
- **修复**：① 立即拉 keepalive ② 重跑脚本输出改 **rootfs 持久路径**（`/home/administrator/_298_p1_20260926/`，/tmp 虽在 rootfs 但重启时 WSL 有清理行为，用 home 下目录最稳）③ nohup + flag 文件收尾
- **通用教训**：WSL 内任何 >30min 的后台任务，启动前必拉 keepalive；证据/输出文件落 `/home/<user>/` 不落 `/tmp`

### #325. p8c_query_reply.py exit code 打点不一致（game_started=False 分支时 2 时 0）🟡 登记（09-26）

- **现象**：同一脚本 5 次运行，`game_started=False` 时 run2 EXIT=2、run3/4/5 EXIT=0（stats 修复前后各不同）；判定只能靠日志 `VERDICT:` 行，exit code 侧面不可靠
- **处置**：不阻塞（判定口径=日志 VERDICT PASS/FAIL + `grep -c fishy`），列入开源周脚本打磨清单（P8 脚本 exit 语义统一：连接失败 1 / 未开局 2 / fishy 3 / PASS 0）

### #326. 30 步冒烟判 H3M 池图准入不可靠——满步大负图 30 步看不出来 ✅ 定谳（09-26）

- **现象**：09-21 池索引 verify 字段全是 `steps=30/250 rew≈-62`（30 步冒烟），据此 09-25 午后把 batch2（too_many_monsters + elbow_room_allies）提进训练池。全量 2135 局窗实测：两图 09-25 迁移日段就是深度负（elbow n=14 **14/14 全大负** mean -436 / too_many mean -387），当前窗 91%/98% 大负、0 正局、满步 85-96%——**30 步冒烟根本进不了 250 步满步负区，rew=-62 看着正常、整局其实是 -400~-700**
- **教训**：图池准入必须跑**满 250 步整局 N≥4**，30 步冒烟只能验"能开局不崩"，不能验奖励面
- **对照反例**：judgement_day 迁移日段 -612，54 局后翻正 +391——大负≠学不会，判留/摘看**时间桶趋势**（每 25 局均值改善 >10% 或出正局=留；平/恶化 + 0 正局 + 满步率>80% 不降、跨 2 窗=摘），不看瞬时值
- **09-26 处置**：① elbow_room_allies batch 2→99（恶化 -440→-474→-497 + 竞态 rc=124 史 09-23）= 热生效（trainer 600s 重读 _pool_index.json 刷新池，不杀训练）；② King_of_Pain 移出课程 MAPS（09-13 加入；duel focus 挤压 + 分桶恶化 -705→-746 + 0 正局；地图 md5 两侧相同已排除文件因素；WSL 尾段本就 -212~-263）= 改 train_ppo_server.py 注释掉，自然重启生效；③ too_many_monsters **保留留观 1 窗**（分桶改善中 -616→-585，~50 局后复核：改善 >20% 或正局 ≥5% 留，否则摘）
- **双副本**：`/DATA/hero3/train_server/pool/_pool_index.json`（服务器热生效）+ 主仓 `maps/h3m_to_vmap/_pool_index.json` 同改（#306 防漂移）；King 摘除同步改主仓 `py/train_wsl2_ppo_v2.py`（WSL 真相源）
- 状态: ✅ elbow/King 已摘，too_many 挂 1 窗观察

### #327. T05 三图（36_01/52_01/52_02）移出课程 MAPS——A/B 双臂定谳能力真空 ✅ 已摘（09-26）

- **判读数据链**：52_01 全历史 606 局 77% 正（449k-695k 曾是最好正图 meanR +128~+200）→ 696k 拐点（#283 蓝方 STATIC_AI 变更）后 4 个月 0 回正 → 服务器窗 3 张 T05 n=243 meanR -102~-113、**0 正局 0 大负**、满步 63-70%（温和负=磨满步+偶战死+shaping 流血，区别于 King 的 -716 灾难负）
- **A/B 定谳（N=4/臂，#298 纪律，/DATA/hero3/ab5201_20260926/）**：B1=T05 现行配置（move_to_force=60 + guard_done=15）vs B2=T06-duel 同款（gd=0），两臂 meanR **-77.5 vs -78.5 等效、0/4 正局** → 补 T06 机械参数救不回 = **能力真空非机械问题**
- **处置**：服务器 train_ppo_server.py MAPS 9→6（T05 三行注释，备份 .bak_0926_t05）+ 主仓 py/train_wsl2_ppo_v2.py 同改（#306 双副本）；**回池条件写死=新 ckpt 评测 T05 4 局 meanR≥0 且正局≥50%**（a_viking 同款）
- **教训**：① 档位级退化按整档处置不逐图 ② "曾是正图"≠"该留着观察"——4 个月 0 回正 + 参数臂证伪后观察无意义 ③ A/B 先诊断再摘除=摘/留都有证据，不是拍脑袋
- 状态: ✅ 已摘（重启生效），证据 /DATA/hero3/ab5201_20260926/（8 traj + 8 log + done.flag）
