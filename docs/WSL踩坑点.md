# 踩坑点文档索引（AI 必读）

> 本文件 `docs/WSL踩坑点.md` 是踩坑点总索引，长期保留。
> 收到“保存踩坑点”指令时，模型写入本文件末尾「待归档新增」区（唯一方式，不自动分发到下方子文档；由用户定期自行归档）。
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

## 条目归属速查（按原文档出现顺序）

| 条目 | 归属文档 |
| --- | --- |
| 1. 9p 文件系统不可用于编译 | 构建-编译与部署 |
| 2. cmake -S/-B 比 cd+cmake 可靠 | 构建-编译与部署 |
| 3. ENABLE_LAUNCHER/EDITOR/LOBBY 必须 OFF | 构建-编译与部署 |
| 4. RPATH 陷阱 | 构建-编译与部署 |
| 5. cmake 自动覆盖 data symlink | 构建-编译与部署 |
| 6. PCH 导致重编译巨慢 | 构建-编译与部署 |
| 7. connector 和 libmlclient 必须 API 匹配 | 构建-编译与部署 |
| 8. 训练和冒险测试用不同的 connector/libmlclient 组合 | 构建-编译与部署 |
| 9. MSYS_NO_PATHCONV=1 必备 | 环境-WSL与进程 |
| 10. LD_LIBRARY_PATH 含空格路径会截断 | 环境-WSL与进程 |
| 11. 子进程环境继承 | 环境-WSL与进程 |
| 12. DATA/LCDESC 缺失 → VCMI 初始化崩溃 | 引擎-VCMI-API |
| 13. CONFIG/FILESYSTEM 缺失 | 引擎-VCMI-API |
| 14. g_adventure_cb lambda 导致 crash | 引擎-VCMI-API |
| 15. env.reset() 阻塞 (战斗模式) | 引擎-VCMI-API |
| 16. VCMI 关闭时 SIGSEGV | 引擎-VCMI-API |
| 17. train_anchor.py 的 capture_output 问题 | 引擎-VCMI-API |
| 18. A1/A5 地图频繁崩溃或超时 | 地图-vmap生成 |
| 19. ml-mini.vmap 的 hero 类型问题 | 地图-vmap生成 |
| 20. s1.vmap 战斗模式 vs 冒险模式 | 地图-vmap生成 |
| 21. dlsym 找到旧版 strategic_state_update | 引擎-VCMI-API |
| 22. struct 尺寸不可改 | 引擎-VCMI-API |
| 23. try/catch 吞异常导致观测全零 | 训练-奖励与策略 |
| 24. moveHero 在回调链中 segfault | 引擎-VCMI-API |
| 25. "Player is not allowed to perform this actio… | 引擎-VCMI-API |
| 26. waitTillRealize=false 对 endTurn 必要 | 引擎-VCMI-API |
| 27. SEND→WAIT→READ 顺序防 race | 引擎-VCMI-API |
| 28. 两处 battle hook 防护 | 引擎-VCMI-API |
| 29. 非红方 guard（pc!=0 直接 endTurn） | 引擎-VCMI-API |
| 30. EmptyAI 不在 AIS 列表 | 引擎-VCMI-API |
| 31. canMoveBetween 不足够精确 | 引擎-VCMI-API |
| 21. PWD 在不同 shell 上下文中的差异 | 环境-WSL与进程 |
| 22. python3 -c 中的引号嵌套 | 环境-WSL与进程 |
| 23. 多个 train 进程并存 | 环境-WSL与进程 |
| 24. ctypes 跨进程访问全局变量 | 训练-奖励与策略 |
| 25. GitHub 直连超时 | 环境-WSL与进程 |
| 26. opencode 连不上服务器 | 环境-WSL与进程 |
| 32. subprocess stderr=DEVNULL 吞掉 MMAI 诊断 | 构建-编译与部署 |
| 33. VCMI 内部重定向 stdout/stderr | 引擎-VCMI-API |
| 34. __declspec(dllexport) 在 GCC 下不识别 | 构建-编译与部署 |
| 35. init_vcmi ABI 不匹配（3-arg vs 1-arg） | 构建-编译与部署 |
| 36. CMakeLists.txt 硬编码 VCMI_DIR 覆盖 -D 参数 | 构建-编译与部署 |
| 37. Schema 版本冲突（BATTLE_SIDE vs BATTLE_ROUND） | 构建-编译与部署 |
| 38. 三份 VCMI 源码各自不同步 | 构建-编译与部署 |
| 27. deepseek-v4-flash 有 45 次工具调用上限 | 环境-WSL与进程 |
| 28. 子 Agent 用 patch 写文件频繁失败 | 环境-WSL与进程 |
| 29. 子 Agent 杀死后台进程 | 环境-WSL与进程 |
| 30. 子 Agent 改 symlink 后不通知 | 环境-WSL与进程 |
| 31. WSL terminate 丢失未写入文件的更改 | 环境-WSL与进程 |
| 32. 观测维度和 ctypes 结构体偏移必须严格同步 | 训练-奖励与策略 |
| 33. TerrainTile::blocked() 是函数不是成员变量 | 引擎-VCMI-API |
| 34. TerrainTile::terType 不存在 | 引擎-VCMI-API |
| 35. 两个 libmlclient.so 实例导致 g_strategic_state 不共享 | 构建-编译与部署 |
| 36. passability mask 全堵时应回退 END_TURN 而非抛异常 | 引擎-VCMI-API |
| 37. vcmi-native 缺 v14/v15/v13 constants.h 的 LINK… | 构建-编译与部署 |
| 38. v15 预存 header/impl 返回类型不匹配 | 构建-编译与部署 |
| 39. Connector 适配新 1-param init_vcmi(void*) API | 构建-编译与部署 |
| 41. strategic_state_update 从未被调用 | 引擎-VCMI-API |
| 42. strategic_state.h ABI 不匹配（Windows vs WSL） | 引擎-VCMI-API |
| 43. CMake /DEF: 标志导致 MinGW ld 链接失败 | 构建-编译与部署 |
| 44. vcmi-native 和 vcmi-native-build 两份源码不一致 | 构建-编译与部署 |
| 45. CCallback::gameState() 在 yourTurn 回调时返回空 CGa… | 引擎-VCMI-API |
| 46. g_strategic_state->action 不被 adventure_send_… | 引擎-VCMI-API |
| 47. `extern "C"` 不允许嵌套 | 构建-编译与部署 |
| 40. 部署新 connector .so 需备份旧文件 | 构建-编译与部署 |
| 48. selectionMade 在 moveHero 前导致服务器拒绝+segfault | 引擎-VCMI-API |
| 49. strategic_state_update / fill_state_from_cb … | 引擎-VCMI-API |
| 修复链 | 引擎-VCMI-API |
| 1. 方向映射不统一 → 模型坍缩 | 训练-奖励与策略 |
| 2. canMoveBetween 太宽松 → passability 全1 | 引擎-VCMI-API |
| 3. waitTillRealize=true → moveHero/endTurn 卡死 | 引擎-VCMI-API |
| 4. Non-red 玩家不处理 → step 超时 | 引擎-VCMI-API |
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
| 1. MLClient.h InitArgs 头文件与 .so 布局漂移 | 构建-编译与部署 |
| 2. connector_v13.so 本体丢失 | 构建-编译与部署 |
| 3. adventureAlliedAI/EnemyAI 全被改成 Nullkiller2 → … | 引擎-VCMI-API |
| 4. build 目录 ServerPlugin 缺野怪保护 → NK2 打野 abort | 引擎-VCMI-API |
| 5. onlyai 下无 human → 所有玩家走 adventureEnemyAI | 引擎-VCMI-API |
| 6. 采集子进程无 watchdog → NK2 启动阶段卡死挂起整条采集 | 训练-奖励与策略 |
| 7. 战斗 AI 三选一全废 (C8.5 训练卡死根因链) | 引擎-VCMI-API |
| 8. WSL 内存崩溃 (E_UNEXPECTED) | 环境-WSL与进程 |
| 9. 被动资源收入做 per-step 奖励 → 模型坚守 END_TURN (C8.5) | 训练-奖励与策略 |
| 10. 进程内 server 代码在 libmlclient.so (C8.5) | 构建-编译与部署 |
| 11. 无 playerID 的玩家 (neutral) 触发 MMAI ASSERT 崩溃 (… | 引擎-VCMI-API |
| 12. TerrainTile::isClear() 无 from 参数 → segfault … | 引擎-VCMI-API |
| 13. fill 无锁直读 CGameState → NK2 决策损坏 (2026-08-01) | 训练-奖励与策略 |
| 14. VCMI settings 写读层不一致 → AI 分配失效 (2026-08-01) | 引擎-VCMI-API |
| 15. extern "C" 语法两坑 (2026-08-01) | 构建-编译与部署 |
| 16. 编译树 MMAI 旧版陷阱 (2026-08-01) | 构建-编译与部署 |
| 17. 动作 8 INTERACT 从未实现 — 文档与代码脱节 (2026-08-15) | 引擎-VCMI-API |
| 18. swapGarrisonHero 未进城挂起 120s (2026-08-15) | 引擎-VCMI-API |
| 19. moveHero 单格版只允许相邻格 + 目标必须是可站格 (2026-08-15) | 引擎-VCMI-API |
| 20. 冒烟测试必须 MMAI 模式 — Nullkiller2 是假象源 (2026-08-1… | 引擎-VCMI-API |
| 21. bulkSplitStack 是军队内部平铺, 不能跨英雄转移 (2026-08-15 … | 引擎-VCMI-API |
| 22. NK2 采集后期卡死 — adventure_wait 90s 超时兜底 (2026-0… | 训练-奖励与策略 |
| 23. OBS v3 大数值字段未归一化 → 训练数值爆炸 (2026-08-16 H.8 根因) | 训练-奖励与策略 |
| 24. passable mask 与 moveHero 目标格不一致 — 英雄模板 visit… | 引擎-VCMI-API |
| 25. C++ 修复写了但未同步编译树/未重编/未部署/未提交 = 修复从未生效 (2026-0… | 构建-编译与部署 |
| 26. NK2 卡死根因 — Router battleStart 战斗模型加载失败 (2026… | 引擎-VCMI-API |
| 27. pkill/pgrep -f 匹配到自己 — bash -c 命令行含模式字符串自杀 (… | 环境-WSL与进程 |
| 28. WSL /tmp 频繁清空 — 观测日志/轨迹丢失 (2026-08-16) | 环境-WSL与进程 |
| 29. NK2 卡死 6 环修复链 — 6 环全闭环 ✅ (2026-08-16 晚, 死锁链另… | 引擎-VCMI-API |
| 30. 战斗后客户端收包静默 + NK2 EndTurn 死循环 — 4 层死锁修复链 (202… | 引擎-VCMI-API |
| 31. NK2 英雄交换查询死锁 — q=1 obj=1 mov=1 永久卡死 (2026-08… | 引擎-VCMI-API |
| 踩坑 #32: 有头 GUI (embedded 非 headless) 与标准 client-… | 引擎-VCMI-API |
| 34. 有头验证 08-18: WSLg 虚拟显卡无 GPU 合成 (显示无解) / 官方 Wi… | 引擎-VCMI-API |
| 66. 模型 AI DLL (Windows VCMI) 编译与部署坑 (2026-08-18) | 构建-编译与部署 |
| 67. fork 战斗链从未可用 — 任意战斗触发即崩 0x98, 双根因 (2026-08-1… | 引擎-VCMI-API |
| 68. BattleAI.dll 手动链接必须 9 obj + stale obj ABI 漂移… | 构建-编译与部署 |
| 69. AI DLL static 变量跨实例共享 — red/green 同 DLL 串状态 … | 构建-编译与部署 |
| 70. 1.7.5 官方版部署 — MSVC 编译 + 缺失符号替代 (2026-08-18 晚… | 构建-编译与部署 |
| 踩坑 #71: WSL 与 git-bash 环境坑 (2026-08-19 记忆迁移) | 环境-WSL与进程 |
| 踩坑 #72: ModelAI 战斗后回合挂死 — yourTurn 线性执行 (2026-08… | 引擎-VCMI-API |
| 踩坑 #73: PPO 策略坍缩链 — 横跳 → END_TURN 刷步 (2026-08-19) | 训练-奖励与策略 |
| 踩坑 #74: MOVE_TO 目标漂移 — 每步重选最近目标 → 来回走 (2026-08-1… | 训练-奖励与策略 |
| 踩坑 #75: python 补丁脚本残留中文注释拼接 — U+2014 SyntaxError… | 环境-WSL与进程 |
| #76 (2026-08-19): ep_runner 缺 import numpy — 被动作… | 训练-奖励与策略 |
| #77 (2026-08-19): logits 偏置对模型从未见过的动作码无效 — 引导用采样… | 训练-奖励与策略 |
| 踩坑 #78: 强制引导动作空转 — MOVE_TO 无目标时原地 27 步 (2026-08-… | 训练-奖励与策略 |
| 踩坑 #79: 动作循环惩罚诱发 END_TURN 穿插投机 (2026-08-19, 第 7 … | 训练-奖励与策略 |
| 踩坑 #80: libmlclient.so 多路径加载 + BFS 目标格 blocked 豁… | 构建-编译与部署 |
| 踩坑 #82: 地形栅格 — _init_baselines 覆盖 + 双 .so 内存隔离 (… | 训练-奖励与策略 |
| 踩坑 #83: ep_runner load_state_dict 缺 strict=False… | 训练-奖励与策略 |
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

> 注：#57 有重复，以“信号量通信修复”为准，另一份（MMAI_USER battle hang）损坏未恢复已剔除；#80 有重复，以完整副本为准，损坏副本已剔除。

> ℹ️ **编号修正 (09-11)**：原 (09-06~09-08) 组 #132~#140 与 09-02/09-03 早期组重号（历史写入冲突），已改号为 **#166~#174**（完整映射见「待归档新增」区组头与元数据说明）；速查表与正文均已同步更新，`#132(09-06)` 等旧写法不再有效。
> ✅ #125~#174 共 50 条已于 09-11 全部分发归档至 5 个主题子文档（正文已移出本文件，本表为唯一索引）。

| 条目 | 归属 |
| --- | --- |
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
| 166. identifier 校验集混入 subtype 字段值: core:alchemist 拒启动 → 1 步空壳局 | 地图-vmap生成 |
| 167. ServerPlugin HeroPool 对称校验拒多敌课程: 1v3/1v7 全部无法启动 | 引擎-VCMI-API |
| 168. transient unit 停止即消失: systemctl start 报 Unit not found (09-08 补 is-active 陷阱) | 环境-WSL与进程 |
| 169. 隔夜中断形态与恢复序: keepalive 丢失 → 非优雅关机 → checkpoint 回滚 | 环境-WSL与进程 |
| 170. 多 resume 日志取"最后一次启动后窗口"的 awk 陷阱: tac|awk|tac 返回全文件 | 训练-奖励与策略 |
| 171. ".so 待重编"登记未验 target 归属: 改 A 源码却去编 B 库 | 构建-编译与部署 |
| 172. fork Windows 构建 DLL 污染: 24 种 GCC 版本混装 = 内存损坏 | 构建-编译与部署 |
| 173. 官方 VCMI 1.7.5 与 fork ModelAI.dll ABI 不兼容: MSVC vs GCC name mangling | 构建-编译与部署 |
| 174. VCMI 数据目录隔离实验结论 | 构建-编译与部署 |
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
| 299. #296 勘误+降噪: `Cannot answer the query -1` 实锤 `lib/callback/CCallback.cpp:53` (lib 非 mlclient) + Popen grep -v 管道降噪 (09-23) | 引擎-VCMI-API |

---

## 待归档新增（收到“保存踩坑点”时追加于此）

> 此区为新增踩坑点暂存区。用户定期自行归档到上方 5 个主题子文档后，再从本区移除。
> 新增条目沿用全局编号续接（当前最大 #283，下一条为 #284…），每条须带状态字段（✅/⚠️/❌/🔄），引用其他条目用 `见 #X`。
> ℹ️ 编号修正 (09-11)：原 (09-06~09-08) 组 #132~#140 与早期组重号，已改号为 #166~#174：#132→#166 / #133→#167 / #134→#168 / #135→#169 / #136→#170 / #137→#171 / #138→#172 / #139→#173 / #140→#174。

> ✅ **归档完成 (09-11)**：原待归档 50 条已全部分发至 5 个主题子文档（环境 14 / 构建 13 / 引擎 10 / 训练 11 / 地图 2）。

### #175: VCMI 网络协议是二进制序列化，非 JSON (09-11)

**现象**: 调研 xsa-dev/homm3env 时发现其 JSON over TCP 协议基于 `features/battle-ml` 分支 (2022 年死分支)，当前 VCMI develop 无此协议。VCMI 官方网络协议使用 `Serializeable` 模板 + `h & field` 做二进制序列化。

**根因**: VCMI 的网络包系统 (`lib/networkPacks/`) 从 HoMM3 原版协议继承而来，使用自定义二进制格式 (非 JSON/protobuf/msgpack)。`CPack` 基类的 `serialize(Handler &h)` 通过 `h & field` 逐字段序列化，变长字段 (std::vector, std::string) 有自定义编码。

**处理**: 外挂 AI 方案需逆向 `Serializeable.h` 的字节布局。短期不影响 (继续 .so 直连)，长期需路径 B (C++ headless client 复用 VCMI 头文件)。

**教训**: 不要假设 VCMI 有 JSON 协议 — 第三方项目 (homm3env) 的 JSON 格式是基于已废弃分支的私有协议。官方协议始终在 `lib/networkPacks/` 定义。

---

### #176: EmptyAI 不走网络 — VCMI 内置 AI 全是进程内直接回调 (09-11)

**现象**: 误以为 EmptyAI 或 MMAI 通过网络与 server 通信，实际读源码发现全部用 `CCallback` (C++ 直接函数调用)，编译为 OBJECT 库链接进 server 进程。

**根因**: `AIFactory.h` 定义 `createAdventureAI(name)` / `createBattleAI(name)` 静态工厂，所有 AI 在 server 进程内构造。`CEmptyAI::yourTurn` 直接调 `cb->selectionMade(0); cb->endTurn()`。无动态加载、无插件系统。

**处理**: 外挂 AI 必须走网络协议 (作为客户端连接 server)，不能模仿内置 AI 的 `CCallback` 路径。`--onlyAI` 标志是告诉 server 内部构造 AI，不是启动网络桥。

**教训**: VCMI 有两条 AI 路径 — 内部回调 (CCallback, 所有内置 AI) vs 网络协议 (CPackForServer, 客户端)。外挂只能用网络协议。混淆这两条路径会导致错误的架构设计。

---

### #177: features/battle-ml 分支是死分支 — 基于它的 JSON 协议不可用 (09-11)

**现象**: xsa-dev/homm3env 的 README 指向 `vcmi/vcmi/tree/battle-ml` 分支，其 TCP JSON 协议在当前 develop 无对应 server 端代码。

**根因**: `features/battle-ml` 分支最后提交 2022-07-19 (作者 nullkiller)，从未合并到 develop。当前 VCMI develop 完全没有 BattleML TCP/JSON 协议代码。

**处理**: 不要基于 battle-ml 分支做架构决策。如果要外挂 AI，走官方 `lib/network/` + `lib/networkPacks/` 协议。

**教训**: 调研第三方项目时，必须确认其依赖的上游分支是否仍然活跃。homm3env 是 2021 SOC 比赛产物，代码是骨架/存根 (step() 返回 None, update_game_state() 是 pass)，其架构参考价值仅限于"JSON over TCP 概念"，不能直接用。

---

### #178: `MMAI::ASSERT` 宏带 namespace 前缀非法展开 → mlclient-cli 编译失败 (09-11)

**状态**: ✅ 已解决

**现象**: C4 #7632 全量 build 时 `mlclient-cli` 报 `AI/MMAI/common.h:23:9: error: expected unqualified-id before 'if'`。agent-v13/14/15.cpp 各 1 处 `MMAI::ASSERT(err.empty(), ...)` 编译不过。

**根因**: `ASSERT` 宏定义在 `namespace MMAI` 内（common.h L20-23：`#define ASSERT(cond, msg) if(!(cond)) throw std::runtime_error(...)`），但 **C/C++ 宏替换不受命名空间限定**——`MMAI::ASSERT(...)` 被展开成 `MMAI::if(!(cond))`，`MMAI::if` 非法。历史遗留 bug（08-01 起 mlclient-cli target 从未编过，暴露即首编），非 C4 引入。

**处理**: 三处 sed 去 `MMAI::` 前缀（agent-v13.cpp L35 / agent-v14.cpp L35 / agent-v15.cpp L42），vcmi-native 与 vcmi-workspace/vcmi 双仓同步修复，全量 build 后 `[100%] Built target mlclient-cli`。

**教训**: 宏永远不带 `NS::` 前缀调用；凡宏定义在 namespace 内，使用处直接裸名。验证旧项目时注意"从未编译过的 target"可能藏着历史语法债。

---

### #179: std::views 传递 include 断裂 — BuildAnalyzer 需显式 `#include <ranges>` (09-11)

**状态**: ✅ 已解决

**现象**: C4 cherry-pick 后部分文件编译报 `std::views::` 未声明，即使已间接包含其他 C++20 头文件。

**根因**: `<bits/range_to.h>` 等传递 include 链在本工具链版本下不稳定，`std::views` 不能依赖传递引入。

**处理**: 在直接使用 `std::views` 的 TU 显式 `#include <ranges>`。

**教训**: 涉及 C++20 新特性（ranges/coroutines/concepts）必须显式 include，不赌传递引入；不同 GCC/clang 版本传递链差异大。

---

### #180: ResetInfo 周判断新旧 API 映射 — 复合判断 ≡ `period==7` (09-11)

**状态**: ✅ 已解决

**现象**: cherry-pick #7632 引入的 `ResetInfo` 新字段与旧代码 `weeks/days/months` 复合判断（`weeks*7 + days` 之类）语义不一致，NK2 代码按新 API 写。

**根因**: 新版把"第 N 周"判断简化为 `ResetInfo::period == 7`（周期=7 即每周）。

**处理**: 旧复合判断统一改写成 `period==7` 判周；`getDate(DAY)` 取绝对天数、`getDate(DAY_OF_WEEK)` 取 1-7。完整新旧映射表见知识库「C4 #7632 执行记录」章。

**教训**: merge 上游重构性 commit 时，先 grep 出所有旧 API 调用点，逐一按新 API 语义改写，不能只改编译报错处。

---

### #181: getCalendar → getDate 等价改写要点 (09-11)

**状态**: ✅ 已解决

**现象**: #7632 删除 `getCalendar()` 返回结构，日历读取改 `getDate(UNIT)`。

**根因**: 上游 API 重构；`getCalendar` 的 week/month 字段由 `getDate(DAY)`（绝对天数）与 `getDate(DAY_OF_WEEK)`（1-7，周一=1）组合等价替代。

**处理**: `CSpellHandler.h` 等调用点逐处改写；周恒 7 天的语义保持不变。

**教训**: 等价改写前先用小样例算一遍天数/星期对应关系，防止 off-by-one（DAY_OF_WEEK 是 1-based）。

---

### #182: `sed -n` 输出隐藏行首 tab — patch 锚点必须 `cat -A` 实测缩进 (09-11)

**状态**: ✅ 已解决

**现象**: 用 `sed -n 'Xp' file` 取出的行做 SearchReplace 锚点时反复失败；`grep -n` 找到的行与文件实际缩进对不上。

**根因**: 文件内混用 tab 缩进，sed/Read 输出把 tab 渲染成空格（或吞掉前导空白），锚点字符串实际是空格开头而非 tab 开头。

**处理**: 关键锚点先 `cat -A`（或 `sed -n 'Xp' file | cat -A`）实测真实字符再写入 patch；本会话 C4 知识库 SearchReplace 首败（anchor 多算 1 行）也用重读文件末尾确认的方式避免。

**教训**: patch 失败先怀疑"看不见的字符"，`cat -A` 显示 tab(`^I`) 与行尾(`$`)，比反复对照肉眼输出可靠。

---

### #183: .so 副本三目录不在训练链路 — 不同步防污染 (09-11)

**状态**: ✅ 已解决（实锤，无需同步）

**现象**: C4 c4-5 "多副本同步" 步骤要求把新 libvcmi.so 等同步到 vcmi-native-build / vtest / hero3_vcmi/build 三处旧副本；事实核查发现三处均为旧版 .so 且**不在训练运行时链路**，同步反而污染基线。

**根因**: 训练真身架构（0911 实锤链）：`train_wsl2_ppo_v5.sh`（transient unit, systemd-run --collect）→ `train_wsl2_ppo_v2.py`（`LD_LIBRARY_PATH` 硬编码 `rel/bin`，`STRATEGIC_STATE_LIB`=`rel/bin/libmlclient.so`）→ `ep_runner_one.py` → `strategic_env.py`（CDLL 加载 rel/bin/libmlclient.so）→ `threadconnector.cpp` → `MLClient.cpp` `GAME->server().debugStartTest(mapname)` = **libmlclient 内嵌 server，进程内线程运行，不启动独立 vcmiserver 进程**。三副本目录是历史构建产物，无人引用。

**处理**: 新栈 .so 全部留在 rel/bin 原位即生效，三副本不动；备份安全网 `~/so_backup_0910_7632/`（libvcmi.so.bak_0910 + libMMAI.so）保留用于回滚。

**教训**: "改 .so 后同步全部副本"的旧纪律建立在多副本被引用的假设上；动副本前先 grep 运行时实际加载路径（LD_LIBRARY_PATH / STRATEGIC_STATE_LIB / CDLL 路径）确认真身，副本同步改为"确认真身后再议"。

---

### #184: #7632 后 T05 小图 +15% 变慢 — NK2 收益与图规模相关 (09-11, 闭环)

**状态**: ✅ 已解决（观察闭环, 假设坐实, 用户拍板保留新栈）

**现象**: 新栈 5 局实测：T05_52X52_mir 旧 97s×6 局极稳 → 新 112s×2 局极稳 = **+15% 慢**（双方极稳，非噪音）；T06_duel 新 4.96s/步落在旧区间 3.67-6.23s/步内（仅 1 局样本）；reward 不劣化（T05 r=166.6/161.8 vs 旧 ~160；T06 r=135.4/137.7 正常）。

**根因（假设）**: 官方 #7632 的 +40% 吞吐 benchmark 是大规模寻路场景；T05 小图 NK2 寻路回合占比低，优化不敏感，且 PathfinderCache 在小图上的维护成本可能是净负。

**处理**: 首窗只观察吞吐与稳定性（纪律：不与其他变更同窗）；T06 duel 需攒 3-4 局稳态样本再判定；T05 若持续 112s 级则判定"本负载无收益"，评估回滚（git revert native 两笔 + workspace 一笔，或换回 `~/so_backup_0910_7632/` 的 libvcmi.so）。

**教训**: 上游 benchmark 收益数字（+40%）不能外推到本项目负载；落地后必须用**同图 EP_TIME 严格对比法**（新旧栈同 map 对比消除地图难度变量）判定，且要等稳态样本（≥3 局）再下结论。

### 待归档新增

#### #185 T13.10 Lobby/P8 前置完成但实机多人局未完成 (2026-09-11) — ✅ 已解决 (阶段1+2 实机 PASS)
- **状态**: ✅ 已解决 — P8-B 阶段1 (lobby join, efb5b6b) + 阶段2 (完整对局 EndTurn 轮转, 407e8e5 + 9cc08b9) 均实机 PASS
- **背景**: T13 外挂 AI 协议客户端完成 `py/vcmi_protocol/`, 新增 Lobby 包解析与 P8-A 实机入口; 离线单测 `144 passed, 0 failed`。
- **坑**: 离线解析通过 ≠ 真实 VCMI server 接受。Lobby 握手、玩家槽位、StartInfo/CMapInfo、跨客户端同步仍需实机抓包验证; 不能把 `LobbyUpdateState` 部分字段占位解析当作完成多人局。
- **正确口径**: 完成的是 P8 前置: TCP/CPack/Query/ModelBridge/Lobby 基础包。未完成的是 P8-B/C: 实机启动 VCMI server/client, AI 与人类同局完成至少 1 局。
- **解决**: 阶段1 假服务器捕获法对拍 BYTE-IDENTICAL 56B; 阶段2 方案F (Python host + LobbyChangeHost 让位 + guest SetMap + StartGame + EndTurn 轮转)。阶段2 首轮虽表面 game_started=True，但 server 日志实锤 "not allowed/fishy" 拒绝（见 #200），真正 zero-fishy 全绿由 9cc08b9 达成。
- **复现/验证**: `python py/p8/p8be_host_start.py` (阶段2 完整对局, 跑完 grep server 日志 `not allowed|fishy` 应 = 0); `python py/p8/p8b_lobby_probe.py` (阶段1 握手)。
- **关联**: T13.10 / P8 / `docs/序列化协议规格.md` / 提交 `bdce29a` → `efb5b6b` → `407e8e5` → `9cc08b9` / 踩坑 #200。

#### #200 P8-B 阶段2 PlayerStartsTurn 字段序错 + 盲发 EndTurn 抢对方回合 → server fishy 拒绝 (2026-09-11) — ✅ 实锤修复
- **状态**: ✅ 已修复 (commit 9cc08b9)
- **背景**: P8-B 阶段2 首轮 `p8be_host_start.py` 表面 `RESULT: game_started=True`，但用户指出"没完成对局，运行就报错"。查 server 日志抓到实锤。
- **坑① 字段序错**: `PlayerStartsTurn(88)` 的 Python 定义写成 `player + time_limit`，与 C++ `Query{queryID} + PlayerColor player` 字段序不符。C++ 权威结构 (PacksForClient.h): `serialize: h & queryID; h & player;`。实机字节 `88帧 = 00 00 d800 41 00` 逐字对上：isNull(00) + pid(00) + tid(88→d800) + queryID(-1→41) + player(0)。
- **坑② 盲发抢回合**: 旧脚本在**每个** PlayerStartsTurn 都无条件发 EndTurn(player=0)，包括蓝方 (p1, ModelAI 客户端的回合)。蓝方回合被 Python 抢发 EndTurn → server 拒 "Player is not allowed to perform this action!" + "Got false in applying 7EndTurn... fishy!" + 2 条 SystemMessage。虽然 ModelAI 自己那轮正常走完、Turn 2 也轮转了，但日志里的 fishy 拒绝是真实错误信号，不算完成。
- **正确口径**: PlayerStartsTurn 包体 = `queryID(LVarInt, 无 timer 时 -1) + player(LVarInt)`。只在 `pack.player == MY_COLOR`（自己的回合）才发 EndTurn；对方回合 SKIP，交给对方客户端（ModelAI）自主管理。EndTurn 绝不替对方回合发。
- **修复**: `py/vcmi_protocol/packs.py` 重写 PlayerStartsTurn（queryID+player 字段序 + 覆写 deserialize）; `py/p8/p8be_host_start.py` 解析 88 包体 player，加 `MY_COLOR=0` 门控; `tests/test_e2e.py` 断言 player/query_id。实机 grep `not allowed|fishy` = 0，Turn1→Turn2 两次 "successfully applied"，ModelAI 蓝方自主 TryMoveHero(40B)。离线 145/145 PASS。
- **关联**: T13.10 / P8-B 阶段2 / 踩坑 #185 / `docs/序列化协议规格.md` / 提交 `9cc08b9` / 技能 `vcmi-network-protocol`。

#### #186 vcmienv ERROR 日志级下 T06 终局双重失明：超时 forcing 零痕迹，9/10 判真实 game_over (2026-09-11) — ✅ 实锤（只读）
- **状态**: ✅ 实锤（只读取证），探针已写待错窗执行
- **背景**: 排查 [GUARD_DONE] 早停 + TOWNSTALL 可达性 + target_list 排序链时，需定判 T06 历史 10 局终局来源。
- **坑**: ep_runner L330 传 `vcmienv_loglevel="ERROR"` → strategic_env L883 WARNING "timed out after 300s" 与 L766 INFO "Episode done" 双双被抑制；进 ep 日志的超时痕迹只有 L725 ERROR "adventure_wait timed out: … — forcing episode end"，而 9/10 历史 T06 局该 ERROR 缺失 ⇒ 判为真实 game_over（纠正此前"旁证指向超时 forcing"的推断）。但 L1182 步尾静默 break + 训练高亮词表无超时词 ⇒ 超时 forcing 路径依旧双重失明，是隐藏的终止源。
- **正确口径**: 判 T06 终局来源不靠日志推，用 obs[19]/[34] alive 判别器（见 #188）或探针 `vcmienv_loglevel="INFO"` 实跑（`py/probe_t06_gameover.py`，错窗执行：停 v5 → 跑 → 重启）。
- **关联**: #187 / #188 / `py/probe_t06_gameover.py` / 当前任务清单 g3b 事实块 / ep_runner L330-L332 / strategic_env L724-L736、L766、L883、L1182。

#### #187 NK2 模式无末步 ±200：末局 reward 无终局方向判别力 (2026-09-11) — ✅ 实锤
- **状态**: ✅ 实锤（只读取证）
- **背景**: 曾试图从 EP_TRAJ 末局 r 定判胜负（预设 NK2 末步注入胜负 ±200 reward）。
- **坑**: `--use_nk2_shaping` 下 `_calc_reward` L1057 提前 return，胜负 ±200 不进管道；r=135.4 级数值在 timeout/go=1/go=2 三场景均可凑出，末 r 无判别力。
- **正确口径**: 终局方向只信 obs alive 判别器（#188）或探针终局 4-tuple dump，不用末 r。
- **关联**: #186 / #188 / 当前任务清单 g3b 事实块 / strategic_env `_calc_reward` L1057。

#### #188 obs 无 game_over 通道：players 段 alive 作只读判别器，battle_quality_events 死路封档 (2026-09-11) — ✅ 实锤
- **状态**: ✅ 实锤（只读取证）
- **背景**: EP_TRAJ 无 terminal 字段 + 9/11 T06 traj 被 52X52 并发跑 (pid 45100) 覆盖丢失，只剩 1/11 样本；需另找只读判别路径。
- **坑①**: obs 3464 冻结（铁律）无 game_over 通道 → 用 players 段（base=8、每玩家 15 字段、alive 为第 12 个）：红 p0 alive=obs[19]、蓝 p1 alive=obs[34]；配合 C++ alive_count≤1 → game_over=last_alive+1 规则：双 0 = timeout forcing（全零 obs）；obs[19]=1 & obs[34]=0 = go=1 红胜；obs[19]=0 & obs[34]=1 = go=2 蓝胜；双 1 + 200 步到顶 = 截断无 terminal。
- **坑②**: `battle_quality_events.log` 40 条 T06 HEROSEG_EMPTY 全 `go=0 slots=0/0 ah=0 cur_p=0` = 观测瞬态空拍，非终局事件，死路封档。
- **正确口径**: 只读定判用 alive 判别器四场景表；实跑定判用探针终局 4-tuple + players obs[8:43] sanity dump。
- **复现/验证**: `python -c` 读 traj 末帧 obs[19]/obs[34]，或探针 `--out py/probe_t06_traj.json` 后看 terminal block。
- **关联**: #186 / #187 / `py/probe_t06_gameover.py` / 当前任务清单 g3b 事实块。

#### #189 8 人局 7 份 ONNX 实例：teal AI 首次 predict 挂死 (2026-09-11) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（Game B teal 卡死现场），源码修复已落 `ppomodelai/src/` 未 commit
- **背景**: PpoModelAI 插件 8 人局（7 个 ModelAI 玩家）teal 首次 predict 挂死。
- **坑**: 每个 ModelAI 各自构造 `Ort::Env + Session` → 7 份全核 ONNX 线程池，第 6 个 AI 起资源放大导致挂死；Game A 单实例正常掩盖问题。
- **正确口径**: 多 AI 插件推理走进程级单例 `ModelInference::instance()`（C++11 magic static 线程安全，同路径只加载一次）+ 线程池限制（intra 2 / inter 1，obs 仅 256 维够用）；加载失败置 `nullptr` 而非半构造。
- **关联**: #190 / 知识库 "PpoModelAI teal 卡死修复" 章 / `ppomodelai/src/ModelInference.{h,cpp}`。

#### #190 GetInputNameAllocated 悬垂指针：ORT "Invalid input name: " 全 fallback endTurn (2026-09-11) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（源码审查），修复已落未 commit
- **背景**: 排查 predict 异常 / 动作全 endTurn 现象。
- **坑**: 旧版 `inputNames` 存 `session.GetInputNameAllocated(...).get()` —— 返回的 allocator 对象行尾析构，`const char*` 悬垂；ORT 报 "Invalid input name: " 后 inference 全部走 fallback endTurn，表面像"模型不动作"。
- **正确口径**: ORT C++ API 返回"持有分配的包装器"时，用 `std::string` 深拷贝持有名字，`Run` 调用期间才取局部 c_str；勿存临时对象指针。
- **关联**: #189 / `ppomodelai/src/ModelInference.cpp`。

#### #191 moveHero 双坐标 anchor↔visitable：server 判 blocked → client 崩溃 (2026-09-11, gui9 实测) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（gui9 卡死/崩溃现场），修复已落未 commit
- **背景**: PpoModelAI 发出 move 后 server 拒绝或 client `onPacketReceived` 崩溃。
- **坑**: `hero->pos` 是**模板锚点格**，英雄实际交互格 = `visitablePos()` = `pos - getVisitableOffset()`（英雄模板 1x2，offset 非 0）；server `CGameHandler::moveHero` 对收到的 dst 再做 `convertToVisitablePos(dst)` 且成功后 `setAnchorPos(pack.end)` → **请求参数是 anchor 语义**。本地用 anchor 格直接当目标发 → 双方判的格子错位一格 → server 判 blocked 拒绝。
- **正确口径**: 本地 tile/pathfinder 判定用 visitable 语义目标；请求参数 `dest = visitableDest + getVisitableOffset()` 转回 anchor。再叠本地三重门（全过才发 move，任一失败 endTurn）：① tile 拒绝（岩石 / `blocked && !visitable`）② simultaneous-turns 目标格有他人对象（保守 endTurn）③ pathfinder `turns>0`/不可达（本回合 MP 不够）。与 09-10 "anchor↔visitable 双坐标系" 章（[GUARD]/[MINE] 假糖根因）同源。
- **关联**: #189 / 知识库同章 / `ppomodelai/src/PpoModelAI.cpp`。

#### #192 构建/链接/可观测性三坑：boost stub guard 失配 + DLL 导出缺失 + 插件 logAi 失明 (2026-09-11) — ✅ 已修
- **状态**: ✅ 源码修复已落未 commit
- **背景**: PpoModelAI 插件重编 + 卡死取证过程。
- **坑①**: 自写 `boost::noncopyable` stub 的 guard 名与真实 boost guard（`BOOST_CORE_NONCOPYABLE_HPP`）不符 → 重定义冲突 + `makeDefend` 等类型转换连锁报错；修法：删 stub，`StdInc.h` 改 `#include "Global.h"`（与 `lib/StdInc.h` 口径）直接用系统 boost。
- **坑②**: `exports.def` 要求 `GetAiName`/`GetNewAI` 但源码缺失 → 链接失败；参照 `AI/MMAI/main.cpp` 约定在 `PpoModelAI.cpp` 尾部补齐（`__GNUC__` 下需 `strcpy_s` 兼容宏）。
- **坑③**: 插件 `logAi` 输出在 client log 中**零命中**（teal 卡死时无 from-turn 内进度可观测）；取证只能靠 stderr 直出（`AI_TRACE` 宏：`fprintf(stderr)` + `fflush`，配合客户端 stderr 管道）。
- **关联**: #189-#191 / 知识库 "PpoModelAI teal 卡死修复" 章。

#### #193 构建树 ninja 静默失败：终端 PATH 缺 mingw64\bin → cc1plus DLL_NOT_FOUND 零输出 (2026-09-11) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（gui12 修复重编期），规避法已固化
- **背景**: 修 `client/CPlayerInterface.cpp` 后在 Trae 终端跑 `ninja`，`Building CXX object` 步 `FAILED: [code=1]` 但 **c++ 编译器零 diagnostic 输出**，稳定复现。
- **坑**: 新开终端 PATH 无 `C:\msys64\mingw64\bin` → g++ 驱动 spawn `cc1plus.exe` 时其依赖 DLL（libgmp/libmpfr/libisl/libzstd 等）找不到 → `0xC0000135 (STATUS_DLL_NOT_FOUND)` → 驱动**不打印任何错误**直接 exit 1。表现为"编译失败但无错误信息"，极易误判成源码/编码问题。链接期另一表现：`ld.exe: cannot open output file bin\VCMI_client.exe: Permission denied` = 游戏进程未退占用 exe（先杀 VCMI_client 再编）。
- **正确口径**: 编构建树前先 `$env:Path = 'C:\msys64\mingw64\bin;' + $env:Path`；ninja 用绝对路径 `C:\msys64\mingw64\bin\ninja.exe`（不在 PATH）。排查口诀：编译 FAILED 无输出 → 手动跑 `cc1plus.exe --version` 看 exit 是否 `-1073741515`。**另**: 任何 CMake re-run 会重新生成 build.ninja 并复活 `$<LINK_ONLY>` 转义坑（PowerShell 正则替换 9 处 → `-l` 形式），改 cpp 不触发、改 CMakeLists 必触发。
- **关联**: #192 / `D:\vcmi-fork-build\build.ninja`。

#### #194 VCMI fork settings 键路径错：combatAlliedAI 读 server 段 → 空 dll 名 → runNetwork 线程死亡全局卡死 (2026-09-11, gui11 实测) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（client 日志铁证），修复已落未 commit
- **背景**: 用户开 quickCombat 攻击野怪守卫 → 战斗开始瞬间全局冻结（AI 无新回合、client 进程存活、无 crash dump）。
- **坑**: `client/CPlayerInterface.cpp:1874` 写 `settings["server"]["combatAlliedAI"]`，但 schema（`config/schemas/settings.json`）定义在 **`ai` 段**（默认 "BattleAI"，全库其余 6 处引用均为 `settings["ai"][...]`）→ 恒返回空串。用户 `adventure.quickCombat=true` 时 `battleStart` → `prepareAutoFightingAI` → `getNewBattleAI("")` → 尝试加载 `.\AI\.dll`（**空库名**）→ throw → 异常沿包 apply 链传播到 **runNetwork 收包线程 → 线程终止** → client 不再收发任何包 → 全局卡死（runServer 线程还活着等 query 回复，永不超时）。
- **正确口径**: 键路径改 `settings["ai"]["combatAlliedAI"]`。取证口诀：**战斗开始后冻结，先查 client 日志 `Cannot open dynamic library` / `thread terminated by exception`**（`VCMI_Client_log.txt`，比 stderr 关键行更直接）；`[runServer]` 标签说明单进程模式（server 为内嵌线程，无独立 VCMI_server.exe 进程可查）。
- **关联**: #193 / `vcmi/config/schemas/settings.json` ai 段 / gui13 实测战斗 7s 闭环 + 多轮推进正常。

#### #195 transient unit 第三次复现：v5 停止后 `systemctl start` 报 "Unit not found"，重启必须 `py/restart_train_v5.sh` systemd-run 重建 (2026-09-11) — ⚠️ 三次复现 + 口径固化
- **状态**: ⚠️ 三次复现（09-06 首踩 / 09-08 二次 / 09-11 本条），规避口径已固化
- **背景**: 09-11 C 方案部署停训窗，优雅停 `systemctl --user stop homm3-train-v5` 后直接 `systemctl --user start` 想重启 → exit 5 "Unit not found"；排查确认 WSL systemd user manager 无持久单元目录（`/home/administrator/.config/systemd/user` 与 `/etc/systemd/user` 均不存在，仅单一用户 administrator uid 1000）。
- **坑**: v5 由 `systemd-run --user --collect --unit=homm3-train-v5` 创建，`--collect` 使 stop 后单元定义被自动清除，单元即消失；且 `is-active` 对已消失单元照样输出 `inactive`（exit 4）→ **不能作为单元存在性判据**，极易误判为"服务停了 start 一下即可"。
- **正确口径**: 重启 v5 一律 `py/restart_train_v5.sh`（内部 systemd-run 重建；venv 必须绝对路径 `/home/administrator/vcmi-workspace/venv/bin/python` — hero3_fresh 目录下无 venv）；重启前用 `train_loop.log` 尾部 `Saved STATE_PATH` + journalctl 确认停机完成，勿靠 `is-active`。Windows 侧 keepalive（`wsl.exe sleep infinity`，09-11 实查 4 进程常驻）防 idle shutdown 需同时保住。
- **复现/验证**: 本条执行链 — 重建后 unit `active`、主进程+ep_runner 双进程在位、`Loaded train state (model+optimizer, step=629167)` 无缝续训、`grep -c '_t06_hero_kill_capture' ep_runner_one.py` = 3 确认 C 方案代码在位。
- **关联**: #168（transient unit 二次复现）/ #114（Windows keepalive）/ `py/restart_train_v5.sh` / `py/check_v5_state.sh`、`py/verify_v5_restart.sh`。

#### #196 policy logits 平坦 → argmax 恒定单动作：部署推理必须 softmax 采样与训练一致 (2026-09-11, mq-4 实测) — ✅ 实锤 + 已修
- **状态**: ✅ 实锤（onnx 探针 + 实机两局验证），采样版 dll 已部署
- **背景**: mq-4 首次实机 1v7 验证，ModelAI v5 全链路通但三个 AI 动作恒 5/6 不动；最初误判旧 dll 未替换（logAi 格式相同是巧合），Grep 源码确认新代码在跑后转向模型本身。
- **坑**: checkpoint 导出的 `rl_model_v5_0911.onnx` policy 头 logits 高度平坦 — `py/probe_onnx_action5.py` 全输入域（零 obs / 结构化 obs / 随机噪声×5 / 0~5 量级随机×3）argmax 恒 6，top1-top2 差仅 0.1~0.3，logit_std≈0.19 → **argmax 退化为常数函数**；而训练侧采样动作多样（act=[0,17,18,16...3,3,3]）。对比实锤：训练采样多样 ≠ argmax 单峰，同一权重两种决策模式行为天差地别。
- **正确口径**: PPO 部署推理必须按 softmax 概率采样（temperature=1.0）与训练一致，argmax 只适合评估/对拍。实现（`ModelInference.cpp` predict 尾部）：maxLogit 减去防 exp 溢出 → double probs 累加 → `static std::mt19937 rng{std::random_device{}()}` + uniform_real_distribution 轮盘减法采样；sum≤0 或输出异常兜底 return 10（END_TURN）。
- **复现/验证**: 采样版 dll 二次实机 PASS — turn1=[5,7,5,7,5,5,7] turn2=[7,7,5,5,5,7,5] turn3=[5,5,7,7,7,5,5]，moveHero 真实执行且方向语义吻合（见 #198），day1→4 无卡死。训练 logits 拉开差距后换新 onnx，部署侧零改码。
- **关联**: #189（单例推理）/ 知识库 "mq 模型部署线闭环" 章 / `py/probe_onnx_action5.py` / `ppomodelai/src/ModelInference.cpp`。

#### #197 AI_TRACE stderr 在 Windows GUI 子系统实机不可见：实机观测一律走 VCMI_Client_log.txt 的 logAi 通道 (2026-09-11, mq-4 实测) — ✅ 实锤
- **状态**: ✅ 实锤（三次日志捕获空 + 对照组实锤）
- **背景**: mq-4 取证尝试用 `AI_TRACE`（`fprintf(stderr)` + fflush，`[ModelAI p%d]` 前缀）经 stderr 管道捕获 AI 决策明细，filter 三次全空。
- **坑**: `fprintf(stderr)` 在 Windows GUI 子系统（VCMI_client.exe）运行期**实机不可见**（仅启动阶段 MUTEX 噪音偶见）——与 #192 坑③"stderr 直出取证"结论冲突，实际那是 teal 卡死期 logAi 失明的特例，**正常期 logAi 通道可靠**，#192 坑③适用范围就此修正。
- **正确口径**: 实机监控一律读 `C:\Users\Administrator\Documents\My Games\vcmi\logs\VCMI_Client_log.txt` 中 `PpoModelAI: ...` 行（logAiLogger 通道，`PpoModelAI.cpp` 403/447/578 行 yourTurn/action/obs 输出全量可靠可见）；stderr 管道只当启动期诊断用。
- **复现/验证**: 采样版验证全程走 VCMI_Client_log.txt，7 AI "v5 model loaded successfully" + 动作流 + moveHero 请求坐标全部取到。
- **关联**: #192（坑③修正）/ 知识库 "PpoModelAI teal 卡死修复" 章 / 知识库 "mq 模型部署线闭环" 章。

#### #198 v5 动作方向表 N-start CW（0=N..7=NW）：5=SW=(-1,+1)，AAI.cpp E-start 旧表弃用 (2026-09-11, 实机坐标验证) — ✅ 实锤
- **状态**: ✅ 实锤（moveHero 请求坐标三方吻合）
- **背景**: 实机动作流验证方向语义，需确认 action→(dx,dy) 映射真实口径。
- **坑**: AAI.cpp 52-55 行留有 E-start 顺时针旧方向表遗产，易误导映射排查；文档若写"5=W"之类旧语义会与实机行为矛盾。
- **正确口径**: v5 动作 0-7 移动为 **N-start CW**：0=N..7=NW，`DIR_DX={0,1,1,1,0,-1,-1,-1}` / `DIR_DY={-1,-1,0,1,1,1,0,-1}`。实机铁证：action=5 → moveHero 请求 (10,65)→(9,66) 即 dx=-1,dy=+1 = SW，严格吻合；P2 (105,100)→(104,101)、P6 (67,34)→(66,35) 同向验证。action=7(NW) 对不可达目标被 server 正确拒绝（非 bug）。
- **复现/验证**: 任何实机 action 流对照该表逐一验坐标即可；PPoModelAI.cpp 本地 tile 判定同表。
- **关联**: #191（anchor↔visitable 双坐标）/ 知识库 "mq 模型部署线闭环" 章 / `ppomodelai/src/PpoModelAI.cpp`。

#### #199 h3mtxt (alexanderbelous/h3mtxt) mingw GCC 编译三连坑 (2026-09-11) — ✅ 已解决 (3 源码补丁)
- **状态**: ✅ 已解决; roundtrip 4 图全 PASS
- **背景**: P10-C 备料, Windows mingw64 (GCC 16.2, Ninja, O3+flto) 构建 h3mtxt, 上游只测 MSVC → 编不过, 逐个修。
- **坑 1 - partial specialization after instantiation**: `H3JsonReaderBase.h` EnumBitmask 模板特化在某些 TU 内晚于隐式实例化 → GCC 硬错误 (MSVC -fpermissive 档)。修: 非 MSVC 分支加 `-fpermissive` (`cmake/h3mtxt_common.cmake`)。
- **坑 2 - 基类/派生类同名模板重载二义**: `H3WriterBase::writeData(EnumIndexedArray<...>)` 与 `H3MWriter::writeData(EnumIndexedArray<...>)` — GCC 派生类名字查找把 base 版与 derived 版判二义 (MSVC/Clang 选精确匹配)。修: 删基类版, 保留 H3MWriter 版。
- **坑 3 - consteval 静态成员类内前向使用**: `ObjectPropertiesVariant::isInline<T>()` 在类内 `std::conditional_t<isInline<T>(),...>` — GCC "used before its definition" (complete-class context 不覆盖 alias 默认实参)。修: 改命名空间级 `inline constexpr` 变量模板 (`Detail_NS::kObjectPropertiesIsInline<T>`), 类内 static_assert 同步换。
- **口径**: 三坑共同模式 = **GCC 对类内模板实参推导中的成员模板/consteval 前向引用比 MSVC 严**, 上游 MSVC-only 项目跨编译器先预期此类错误; 修复优先级 = 命名空间变量模板 > -fpermissive > 删冗余重载。
- **附带坑**: ① exe 不吃 `/c/...` MSYS 路径 → `MSYS_NO_PATHCONV=1` + `C:/...` ② ROE 图拒读 (仅 AB/SoD) ③ 输出 JSON 带 `//` 注释非严格 JSON, Python 解析需 json5 或剥注释 ④ 构建慢 (866 目标 LTO ~40min)。
- **复现/验证**: `tools/h3mtxt/build/src/h3mtxt/h3mtxt.exe`; roundtrip 判据 = gzip 解压后 raw 逐字节一致 (gzip 头 mtime 差异忽略)。
- **关联**: 知识库 "P10-C 备料" 章 / #193 (mingw PATH 前置) / P10。

#### #201 WSL 发行版容器空闲关停杀训练 — systemctl is-active 也会骗人 (2026-09-11) — ✅ 已修 (双层)
- **状态**: ✅ 已修复; 训练 PID 存活 14min+ 连跑多局验证
- **现象**: Hermes 侧 `wsl bash restart_train_v5.sh` 拉起训练后无日志输出; unit 每次只活 17-45s (14:07/14:27 两次 44s/49s, 14:38 起 system 级 unit 仍 17s 一停)。当时误判两层: 先怪 user-level transient unit (改 system 级无效), 再怪 vmIdleTimeout=-1 非法值 (方向也错)。
- **根因**: **发行版容器空闲关停** — 最后一个 wsl 会话退出 → WSL 终止整个 Ubuntu+systemd 容器 (非 VM!) → 下条 wsl 命令冷启动容器 → 训练 unit 随命令会话死亡。VM 层 boot_id 恒定 + uptime 连续, journal 里 15:05:07 出现整套 `Stopped multi-user.target` 关停序列但 VM 没重启 = 容器级关停实锤。vmIdleTimeout 只管 VM, 管不到发行版容器。**任何挂法 (user/system 级 unit) 都逃不掉**, 因为死的是整个 systemd。
- **处理**: 双层修复 ① Windows 侧常驻 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList '--exec','sleep','infinity'` (有活跃会话 → 容器不关停; Windows 重启后需重起) ② system 级 enabled unit `homm3-train-v5` (/etc/systemd/system, User=administrator, StandardOutput=append 到 train_loop.log; `wsl -u root` 免密装, 容器冷启动时自动拉训练)。旧 `py/restart_train_v5.sh` (user 级 transient, 坑 #195/#168) **已废弃**。
- **教训**: ① 验证训练存活 = `ps -o lstart,etime -C python` (PID 存活时长) + 日志 mtime 推进 + step 行出现, **`systemctl is-active` 会骗人** — 容器冷启动后 unit 自动拉起也显示 active, 但下一会话结束就死 ② 首局需 ~6-10min 才出第一条 step 行, "没日志"≠"没在跑", 要先分清 "进程被杀循环重启" (banner 反复出现) vs "首局未完" ③ container idle shutdown 与 VM idle shutdown 是两层, journal 关停序列 + boot_id + uptime 三件套联合定位 ④ git-bash 调 powershell 时 `$_` 会被 bash 吞掉 (Where-Object 全炸), 用 `tasklist /FI` 替代。
- **关联**: #195 (transient unit 坑, 本坑为其真解) / #168 / 知识库 09-11 训练存活机制重构章 / 任务清单 L9 运维命令 / `.wslconfig` vmIdleTimeout=2147483647 (VM 层保险, 非本坑根修)。

#### #202 P8-B ChangeHost 时序：必须在 guest 连入后才发，否则静默拒绝开局永卡 (2026-09-11, 捕获脚本首跑踩) — ✅ 实锤
- **状态**: ✅ 已修 (p8c_capture_hero.py 同步 p8be 时序)
- **现象**: `p8c_capture_hero.py` 首跑 60s 全空捕获——server 日志尾部 client1 反复发 `11LobbySetMap`(10+) + `14LobbySetPlayer`, 最后 "Connection lost", 游戏从未开局。
- **根因**: 脚本在 `VCMI_client.exe` 刚 Popen 就发 LobbyChangeHost(225)→cid=2；但 client1 此时还没连上，cid=2 不存在 → server 静默拒绝。client1 随后以 guest 身份加入 → 其 host 侧 SetMap/SetPlayer 被 host-only 检查全部拒掉 (SetMap 静默丢, 见 #185 解法) → mi_loop 10s 超时空转 → 永不开局。
- **正确口径**: ChangeHost 前必须确认目标 guest 已 join = 等到**第 2 个 LobbyUpdateState(226)** (p8be 的 `client2_seen`) 才发。同坑变体: 目标 cid 必须是实际存在的 connection ID。
- **复现**: `python py/p8/p8c_capture_hero.py` (已修, 正常开局); 旧症状 = 捕获脚本报 "捕获结束" 但零 [DUMP] 行 + server 日志 SetMap 刷屏。
- **关联**: #185 (SetMap host-only) / T13.10 P8-B 阶段2 方案F / `py/p8/p8be_host_start.py` 第 114-129 行时序范本。

#### #203 P8-B 阶段3 (P8-C) 数据源墙：我的英雄 OI+位置只在 StartGame 171KB 全状态, 回合窗口无独立位置包 (2026-09-11, 捕获分析) — 🟡 已分析, 待决策
- **状态**: 🟡 分析完成, 3 条路线待用户拍板
- **实锤**: ① turn 窗口 server 只广播 88/102/116/86/84/91/109 等, **不**单独发 GiveHero/ChangeObjPos/NewObject 位置包 (171KB 之后的 8s 内零 hero 位置包) ② `MoveHero.hid` = 引擎运行时 ObjectInstanceID, ≠ h3m 静态 heroID → P10 h3mtxt 静态 JSON 拿不到 OI, 走不通 ③ server 日志只在英雄实际移动时打 "OI xxx start (x y z)", 挂机玩家无记录。
- **结论**: Python 外挂要发真实 MoveHero, 必须从 StartGame(224) 的 `LobbyStartGame = StartInfo + CGameState(171KB)` 解析出 `CMap.heroesOnMap` / `CPlayerState.hero` OI + 坐标。CGameState 全量 Python 解析工程量大 (map 对象数组几百个 CGObjectInstance 模板 + 版本门控字段, 见 CGameState.h L196-225)。
- **三条路线 (改编号为阶段4/5/6)**: **阶段4 最小 CGameState 解析器** — 只挖到 heroesOnMap + hero OI 为止, 每包校验断言 (width=36/day=1), 工程中等, 收益=完整 MoveHero 闭环 **阶段5 降级最小闭环** — 阶段3 先做 QueryReply(197)+RecruitCreatures(187) 真实决策 (不依赖地图状态, 城镇 OI 可从 SetAvailableCreatures 拿), MoveHero 留阶段4 **阶段6 C++ headless client** — 直接复用 VCMI 序列化代码 (路径A), 工程量最大但零逆向风险。
- **复现**: `python py/p8/p8c_capture_hero.py` (dump 171KB → %LOCALAPPDATA%/Temp/p8c_startgame.bin, 离线分析入口)。
- **关联**: T13.10 P8-B 阶段3 / 技能 vcmi-network-protocol 路径A/B/C / #185 / `docs/序列化协议规格.md` / C++ 结构: `PacksForLobby.h LobbyStartGame` + `CGameState.h L196` + `CMap.h heroesOnMap` + `StartInfo.h L169`。

#### #204 新惩罚/事件标签上线验证陷阱：0 次触发 ≠ 未生效 + 全 log 计数跨重启污染 (09-11, T7.4 死亡惩罚首窗) — ⚠️ 方法论坑

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

#### #205 外部客户端发非法 entity 字符串可炸服 — retrievePack 未捕获 IdentifierResolutionException (2026-09-11, P8-C Recruit 测试踩出) — ✅ 已修
- **状态**: ✅ 已修 (vcmi 1c3be8d030): `CVCMIServer::onPacketReceived` 对 `retrievePack` try/catch (`IdentifierResolutionException` + `std::exception`) → 丢弃恶意包并 log, 不再 Disaster。
- **现象**: Python 外挂发 `RecruitCreatures(187)` 带 placeholder `crid="<ref510>"` → server "Disaster happened" 全服崩溃 (dump 落盘)。
- **根因**: `EntityIdentifierWithEnum::serialize`(!saving) → `CreatureID::decode("<ref510>")` → `resolveIdentifier` 尾部 `throw IdentifierResolutionException` → 异常穿透 `GameConnection::retrievePack` 直达顶栈。任何 wire 内 entity-string 字段 (CreatureID/HeroTypeID/SpellID/BuildingID? BuildingID 是 StaticIdentifier LVarInt 除外) 都可被外部客户端用于炸服 — **联网对战安全漏洞**。
- **坑中坑**: `SetAvailableCreatures(112)` 的 CreatureID 字符串带跨包去重 (负数 ref 引用 171KB StartGame 里首次写入的字面量), 外挂侧单包解析无法还原 → 招兵 crid 来源 = 新增 `[SRV-DIAG] TOWNAVAIL` (build 成功后 dump `town->creatures` 各级 jsonKey)。
- **字段序修正 (同窗)**: `BuildingID` = `StaticIdentifierWithEnum` → wire LVarInt 数字 (非 string); `HeroTypeID` = `EntityIdentifier` → wire string jsonKey; `SetAvailableCreatures(112)` = tid + `vector<pair<ui32, vector<CreatureID>>>`。
- **关联**: #206 (SRV-DIAG 路线) / `CVCMIServer.cpp onPacketReceived` / `EntityIdentifiers.cpp resolveIdentifier L171` / 脚本 `py/p8/p8c2_town_chain_probe.py`。

#### #206 P8-C 数据源墙第四路线 = SRV-DIAG server 侧注入, 免解析 171KB (2026-09-11, MoveHero 闭环实机 PASS) — ✅ 已实施
- **状态**: ✅ 落地并实机验证 (vcmi commit bc3e124fa2 + 主仓 7967511)
- **方案**: 不解析 StartGame blob, 改在 `CGameHandler::start` (`!resume` 分支) `fprintf(stderr, "[SRV-DIAG] HERO OI=%d owner=%d pos=%s", ..., hero->anchorPos().toString())` 逐英雄 dump → Python 外挂 tail server 日志拿运行时 OI+owner+锚点坐标。零逆向、零包解析、跨图通用。
- **坑中坑 (字段序)**: `TryMoveHero(109)` wire 序 = **id + result + start(int3) + end(int3) + movePoints + fowRevealed(vector) + attackedFrom**, 非直觉 id+start+end+result; 读错会把 SUCCESS(1) 当 FAILED(0) (离线 test_e2e 两侧同错自洽通过, 实机 server trace 对拍才抓出, 与 #199 同型坑)。
- **MoveHero 语义**: path = 锚点坐标序列, 每步须与英雄当前位置 8 邻域相邻 (`areNeighbours` 检查), layer=0(LAND), transit=false; day1 MP 耗尽后同格移动也回 SUCCESS(=原地 no-op), 不是拒绝。
- **实锤**: red OI=350 (1,8,0)→(2,7,0) 实移 + blue ModelAI OI=732 (16,1,1)→(15,0,1) + 3 回合轮转 + PackageApplied=True + zero fishy。
- **脚本**: `py/p8/p8c_movehero_probe.py`。
- **关联**: #203 (数据源墙分析, 本条=第四路线闭环) / #202 (ChangeHost 时序) / #200 (PlayerStartsTurn 字段序) / `CGameHandler.cpp CGameHandler::start`。

#### #207 Query 协议栈四层隐性缺陷 — 离线单测通过实机不可用 (2026-09-12, P8-C QueryReply 探针首跑抓出) — ✅ 已修 (全协议栈返正)
- **背景**: `test_e2e.py` 162 项 PASS, 但首跑 `p8c_query_probe.py` 6/6 全 FAIL, 且失败现象一致 (`[QUERY] X: qid=-1 (INVALID, 跳过回复)`, 但 mock server 明明下发 qid=7/12/15/42)。逐层排查后暴露 4 处协议栈隐性缺陷, 均在 `test_e2e` 覆盖盲区。
- **层 1 — QueryManager 用 type_id 代替 query_id**: `handle_query` 原实现 `qid = query_data.get("type_id")`, 把包类型号 (154/156/157/88) 当 qid 回复; VCMI 官方 `Query{queryID}` 是**所有 Query 派生包的首字段**, 与 type_id 无关。→ 改为 `qid = data.get("query_id", -1)`。
- **层 2 — 三个 Query 派生类字段序错位**: `HeroLevelUp(154)` / `BlockingDialog(156)` / `GarrisonDialog(157)` 原走基类默认序列化 (player 首字段), 但 `PacksForClient.h` 明确它们首字段是 `queryID` (`HeroLevelUp` L1308: queryID+player+heroId+primskill+skills; `BlockingDialog` L1349: queryID+text+components+player+flags+soundID; `GarrisonDialog` L1392: queryID+objid+hid+removableUnits+customTitle 版本门控)。→ 三处全部覆写 `serialize/deserialize`, 首字段改回 queryID, 与 `PlayerStartsTurn(88)` (#200 已修) 一致。
- **层 3 — parse_client_pack 扁平 vs 嵌套不一致**: 原 `parse_client_pack/parse_server_pack` 返回**扁平 dict** (`{type_id, class_name, 字段全平铺}`), 但 `QueryManager.handle_query` 和 `VCMIProtocolClient._handle_packet` 都在读 `result.get("data", {})`。→ 单测 `test_query_manager` 手写了带 `data` 键的 dict 所以 PASS, **实际 wire 层不可用**。已统一改为返回 `{type_id, class_name, data: {字段...}, raw}` 嵌套结构; `test_e2e.py::test_client_packs` 同步把 15+ 处 `result.get(field)` 改为 `result["data"].get(field)`。
- **层 4 — TryMoveHero 字段序错位**: 原占位 `source/destination/reason`, 实机 wire 是 `oid + result + start(int3) + end(int3) + movePoints + fowRevealed(vector<int3>) + attackedFrom(int3)` (PacksForClient.h; 与 #206 记录的字段序一致)。→ 覆写 serialize/deserialize, test_e2e 断言从 2 → 7 (oid/result/start/end/move_points/fow_len)。
- **qid=-1 语义补全**: `handle_query` 增加 `qid==-1 → skip 回复 + history 记 skipped=True` (VCMI 官方 `NetPacksBase.h L47-50` 明确"非实际 query, 不应回复"; PlayerStartsTurn 无回合计时器时即为 -1)。
- **回归**: e2e **167/167 PASS** (断言数从 162 → 167, TryMoveHero 覆盖加深) / `p8c_query_probe.py` 离线 **6/6 PASS** / `p8c_query_probe_real.py` 实机 **PASS(qid=-1 only, 14 回合 27 次 PlayerEndsTurn, zero fishy)** / `p8c_movehero_probe_real.py` 实机 **PASS (turns_act=4 move_accepted=9 move_failed=0)**。
- **教训**: ①单测手写 dict 会掩盖 wire 结构不一致 (与 #178/#204 同型"两侧同错自洽"坑); ②字段序 bug 必须实机对拍才抓出, 离线 mock 双方自洽通过无诊断力; ③`Query` 派生类首字段全为 queryID, 覆写基类序列化不是可选项。
- **关联**: #200 (PlayerStartsTurn 字段序) / #206 (TryMoveHero 字段序, 本条重述 packs.py 落地) / #178 (ASSERT namespace) / #204 (0 命中三义性) / 脚本 `py/p8/p8c_query_probe.py` + `py/p8c_movehero_offline_probe.py` / `py/p8/p8c_query_probe_real.py` + `py/p8c_movehero_probe_real.py`。

#### #208 Query 分支 `continue` 吞 PlayerStartsTurn — server 等回合结束超时踢连接 (2026-09-12, `p8c_query_probe_real.py` 首跑实机 FAIL 抓出) — ✅ 已修 (分支内补特判)
- **背景**: 协议栈四层修复 (#207) 后, `p8c_query_probe_real.py` 实机首跑仍 FAIL — 只收到 1 条 `PlayerStartsTurn qid=-1 (INVALID, 跳过回复)` 后 `[RECV] 断开`。查代码发现 recv_loop 里 `if tid in QueryManager.QUERY_TYPES: ... continue` 分支把 `PlayerStartsTurn(88)` 吞掉, 后面的 `elif tid == 88: act_turn()` 兜底永不触发, EndTurn 永不下发, server 等我方回合结束超时踢连接。
- **修复**: 在 Query 分支里对 `tid == 88` 做特殊处理 — 无论 qid 是否 -1, 只要 player == MY_COLOR 且 not end_turn_sent, 立即 `turn_count++` + `act_turn()` + `end_turn_sent=True`。这与 #200 记录的 "PlayerStartsTurn 是 Query 派生" 语义一致, 但业务逻辑与 Query 回复正交。
- **实机复验**: turns_act=14 turn_ends(102)=27 query_received=28 (全部 qid=-1) query_reply_sent=0 bad_keywords=0 → **VERDICT: PASS(qid=-1 only)** — 无计时器场景下的官方预期行为 (NetPacksBase.h L47-50)。
- **教训**: ①Query 分支不能只写"回复/跳过"两义 — 业务事件 (回合切换) 也要消费; ②实机是协议栈的终极仲裁 — 离线 6/6 PASS 的 probe 不能覆盖"分支优先级"这类控制流 bug; ③`qid=-1` 语义 = "非实际 query, 不应回复", 不等于 "整包可忽略" — 包本身可能携带业务事件。
- **关联**: #200 (PlayerStartsTurn 是 Query 派生) / #207 (Query 协议栈四层修复) / `py/p8/p8c_query_probe_real.py` L141-151 (修复位置)。

#### #209 TOWNSTALL 卡住检测 `>=` 把路径平台段（BFS plen 持平）误判停滞 → 提前 TOWN_BLOCKED 禁用城镇引导 (2026-09-12, 日志分析实锤) — ✅ 已修 (09-12 实施, 重启窗验证)
- **状态**: ✅ 已修 (09-12 L877 `>=` 改 `>` 实施 + 重启 `homm3-train-v5` 验证; 重启窗口 TOWN_BLOCKED=0 全绿)
- **背景**: 日志分析发现 `[TOWNSTALL]` 假阻塞实例 — passability mask 8 邻全 1 仍判 stall（典型 L73327：`hero=(8,7) tgt=(2,1) plen=6 block=(7,6) pas=[1,1,1,1,1,1,1,1]`）；全 log 统计 TOWNSTALL 3817 次 / TOWN_BLOCKED 460 次。排查 `ep_runner_one.py` L872-898 卡住检测核心后定位根因。
- **坑① `>=` 把"进度持平"也计停滞（主根因）**: L877 `if cur_dist >= move_stall_prev: move_stall += 1`。BFS plen 在横向移动/绕岩路径的平台段**不变**（绕岩前段曼哈顿不降反升已注明 L868，但 plen 横向移动时仍会持平），`>=` 把这种合法持平也累积进 `move_stall`，攒满 6 步即 L892 `move_stall >= 6` 触发 TOWN_BLOCKED → L893-894 `town_blocked=True` 本局禁用城优先引导。8 邻全通（pas 全 1）却判 stall 即此症状：英雄在绕岩/横移平台段被误杀。
- **坑② `dyn_blocked.add` 副作用把可通行格入黑名单**: L881-887 在 `move_stall==1` 时取 BFS 首步格 `(_bx,_by)` 加入 `dyn_blocked`（设计意图=敌方英雄等动态障碍），但平台段首步格实际是**可通行格**（pas 全 1 实证）→ 后续 BFS 重规划绕行该格，进一步拉偏路径，放大误判。
- **影响面**: 局仍正常完成（招兵/打守卫/拿分不中断），仅损失 town_visited 约 +30/局 的奖励；TOWN_BLOCKED 460 次为误判占比大头。
- **正确口径 / 修复方案**: L877 `>=` 改 `>` — 只惩罚"进度变差"（plen 增加），允许"进度持平"（平台段不再累积 `move_stall`）；代价是真卡死（原地打转）累积变慢（6 步 → 8~10 步触发），可接受。修复需 stop/restart 训练（`systemctl --user stop homm3-train-v5` 优雅停 → `py/restart_train_v5.sh` 重建，见 #195/#201），待自然 checkpoint 重启窗实施，不与其他变更同窗。
- **复现/验证**: `grep -n "TOWNSTALL\|TOWN_BLOCKED" /mnt/d/Bigdata/hero3_fresh/train_loop.log`（3817/460 量级）；修复后同 grep 预期 TOWN_BLOCKED 频次显著下降，且 pas 全 1 的 TOWNSTALL 实例不再出现。
- **关联**: #204 (0 命中三义性 / 全 log 切窗法) / #195/#201 (重启窗口径: systemd transient unit + keepalive) / 任务清单"活跃任务 6 长期观察集 TOWNSTALL 引导可达性"行 / `ep_runner_one.py` L872-898。

#### #210 T7.4 HERO_DEATH 判据 1 在 T05 负载段恒 0 触发 — C 方案 proxy 与 zombie 全堵正交 (2026-09-12, 子 agent 分析) — ✅ 根因定位
- **状态**: ✅ 根因已定位（代码 + 日志双向对照），无需修复代码，需切观察窗样本池
- **背景**: T7.4 死亡惩罚三判据观察，首窗 11 局 T05 36X36/52X52 全部 `[HERO_DEATH]=0`，判据 1 (死亡局 r 转负) 无法验证。子 agent 排查 `ep_runner_one.py` L1212-L1223 + `strategic_env.py` L1117 后定判。
- **坑**: HERO_DEATH 触发条件 = `zombie_streak >= 2` (8 方向全堵, `passable.any()=False`)，与 C 方案 proxy 的 `blue_hero_killed` (blue 英雄被 red 击杀)**完全正交**（L1216 注释明确"正交"）。T05 守卫战 autofight 必胜 ([ep_runner_one.py L904](file:///d:/Bigdata/hero3_fresh/py/ep_runner_one.py#L904))，red 英雄几乎不战死 → 无全堵机会；T06 duel 蓝英雄一死 → game_over 当步 end → 同样无机会。
- **正确口径**: 判据 1 样本池应切到 T06 72X72 duel (blue 英雄存活 → red 进攻 → 有反杀全堵机会)；blue_hero_killed 保持不计入 HERO_DEATH (避免双罚, 激励轴错窗纪律)；VCMI 引擎 standardDefeat 未落地前 `game_over==2` 判负不生效 (方案_T74 §6 远期 C++ 课题)。
- **复现/验证**: `grep -c "HERO_DEATH" /mnt/d/Bigdata/hero3_fresh/train_loop.log` 当前 = 0；切到 T06 duel 图池后观察 1-2 窗 (~100 局) 复核。
- **关联**: 任务清单"活跃任务 3 T7.4 死亡惩罚" / #204 (0 命中三义性) / `ep_runner_one.py` L1212-L1223 / `strategic_env.py` L1117。

#### #211 P8-D 远程连接 `_do_connect` 调不存在的 `_socket_connect` + Windows atomic rename 失败 (2026-09-12, 实机验证抓出) — ✅ 已修
- **状态**: ✅ 已修 (commit 待 git 提交)
- **背景**: P8-D 跨机器部署脚手架 (auth + remote_connection + deployment) 本机实机验证 13/13 PASS 前需修复 2 处。
- **坑①**: `RemoteVCMITCPConnection._do_connect` 原调 `self._vcmi._socket_connect()` (VCMITCPConnection 无此方法) → 改为 `ok = self._vcmi.connect(); self._sock = self._vcmi.sock`。
- **坑②**: `StatusFileWriter._write` 用 atomic rename (先写 `.tmp` 再 rename 到 `.json`)，Windows NTFS 目标已存在时 `tmp.rename` 抛 `FileExistsError` → 改为直接 `with open(self._path, 'w') as f: json.dump(data, f)`。
- **坑③**: HSK 权限 0o600 检查在 Windows 下 `os.chmod` 不生效 (NTFS 无 POSIX 权限位) → 放宽为仅 Linux/macOS 检查，Windows 打印"跳过 POSIX 权限检查"。
- **正确口径**: 跨机器脚手架本机验证 = 启动真实 VCMI_server + TCP 探活 + RemoteVCMITCPConnection 连接 + 状态文件读写 + 部署命令构造；双机部署路径按既定口径**不用第二台真实机器**，统一用「单机双实例」实跑完成（`py/p8d_two_instance.py` 13/13 PASS：2 真实 VCMI_server 端口隔离 3030/3031 + 2 真实 ModelAI client 跨实例 + HSK 跨实例预交换 + HMAC 正负例 + 双节点状态文件，共享 fork build 无需副本）。
- **复现/验证**: `python py/p8d_deploy_probe.py --local` 13/13 PASS；双机路径用 `python py/p8d_two_instance.py` 13/13 PASS（单机双实例）；`python py/p8d_deploy_probe.py --remote <host> --port 3030` 保留可用但不再作为待办。
- **关联**: P8-D / `py/vcmi_protocol/remote_connection.py` / `py/vcmi_protocol/deployment.py` / `py/p8d_deploy_probe.py`。

#### #212 gen_t06_duel.py 直接写 JSON 不走引擎 loader/saver → 缺 terrain_0.json + 蓝英雄贴蓝镇 6 格 vs 红方 3 格不对称 (2026-09-12, 生成 + check 检查抓出) — ✅ 已证伪（2026-09-13 引擎源码定判）
- **状态**: ✅ 两项缺陷均无害, 地图可正常入池训练。①缺 terrain_0.json 是误报（引擎 `MapFormatJson.cpp` L248-255 `getTerrainFilename(0)` 返回 `surface_terrain.json` 而非 `terrain_0.json`, 引擎从未读 `terrain_0.json`）; ②蓝方贴镇 6 格 vs 红方 3 格不对称描述有误（实际双方均 dist=6, 完全对称; `check_t06_maps.py` L134 阈值 5 偏严触发 WARN 是阈值问题非地图问题）
- **背景**: 09-12 用户要求"先生成 T06 duel 地图备用"。手写 `py/gen_t06_duel.py` 直接构造 VCMII JSON (header.json + surface_terrain.json + objects.json), 生成 3 张 72X72_02/108X108_01/108X108_02 duel 并 `cp` 进 `v13/maps/` + 副本, `check_t06_maps.py` 7 维全绿即宣布可用。
- **定判过程 (09-13)**: ①WSL 侧 `grep surface_terrain` 在 `vcmi-native/lib/mapping/MapFormatJson.cpp` L251 命中: `if(i==0) return "surface_terrain.json"` → **引擎读 surface_terrain.json, 不存在 terrain_0.json 这个文件名**, 1v3 源图也全缺 terrain_0.json → 缺 terrain_0.json 不影响引擎加载/寻路。②`check_duel_coords2.sh` 提取 objects.json 顶层 x/y: 三张 duel 图 red hero→town 与 blue hero→town 曼哈顿距离均为 6（72X72: (5,5)→(2,2)=6, (66,66)→(69,69)=6; 108X108: (5,5)→(2,2)=6, (102,102)→(105,105)=6）→ **双方完全对称**, "不对称"描述有误, 6 格本身是 T06 课程图设计值（非 duel 1-2 格惯例, 但 T06 本身就是大地图探索阶段, 6 格合理）。
- **正确口径**: T06 duel 地图 `gen_t06_duel.py` 生成产物可直接入池, 无需补 terrain_0.json 或调坐标。若后续要更紧凑的 duel 布局（贴镇 1-2 格）, 可走 P10-B h3m2vmap 管线重写。
- **复现/验证**: `unzip -l <vmap>` 只有 3 文件（header.json + surface_terrain.json + objects.json）正常; 引擎 `MapFormatJson.cpp` L248-255 `getTerrainFilename(0)="surface_terrain.json"` 是引擎 terrain 文件名映射, 不依赖 terrain_0.json。
- **关联**: P10-B h3m2vmap 设计稿 §8 / `MapFormatJson.cpp` L248-255 / `check_t06_maps.py` L134 阈值 5 → 建议 T06 图阈值放宽至 7 / `check_duel_coords2.sh`（坐标对称性验证脚本）。

#### #213 T06 duel C 方案 hero-kill proxy +100 全误报：obs 战斗瞬态部分少报 vs BHERO_KILL 守卫不对称 (2026-09-13, 日志分析实锤) — ✅ 已修
- **状态**: ✅ 已修 (ep_runner_one.py L948 加 `and not args.mapname.endswith('_duel.vmap')`, duel 跳过 C 方案)
- **背景**: 09-12 日志分析发现 duel 的 49 条 `[TOWN_CAPTURE] blue_hero_killed=[1]` 同期 `BHERO_KILL` = 0，启动单独核查 duel 中 +100 是"真触发"还是"误报"。
- **坑 — 两条路径守卫不对称 (ep_runner_one.py L948 vs L963)**: C 方案 L948 计算 `bhero_ids_prev - _bnow` 时**无 `_bnow` 非空守卫**，战斗瞬态 obs 部分少读（_bnow 非全空但少了 id=1）→ 集合差误判为"击杀" → +100。而 L963 的 `BHERO_KILL` 有 `if _bnow:` 守卫，全空拍时跳过。两条相似路径守卫不对齐 = 隐蔽缺陷。
- **根因 — 三重证据链确认 49/49 全部误报**: ①`BHERO_KILL=0` → obs 正常状态蓝英雄从未消失（集合差恒 0）; ②`HEROSEG_EMPTY=0` → 全空拍诊断未触发（战斗瞬态 _bnow 非全空，有部分英雄但少了 id=1）; ③ep 继续运行 → TOWN_CAPTURE step 95 后 ep 正常到 step 96 才 end（err=no），若真击杀 duel 应当步 game_over 不该多跑 1 步。
- **影响评估**: 49 次 × +100 = 4900 虚假 reward 注入 PPO 价值网络; 集中在 duel 早期 step（28-99 占 67%），让 agent 学到"进战斗=+100"的错误价值关联; duel 局 r 基线被抬高约 +100/局。
- **修复 — 方案 B duel 删除 C 方案**: L948 加 `and not args.mapname.endswith('_duel.vmap')`。duel 蓝英雄死=game_over=ep 终止，游戏引擎已处理终止信号，不需额外 reward proxy; proxy 只在"蓝英雄死但 ep 不终止"的 1v3/1v7 场景才有必要。
- **教训**: ①两条相似代码路径的守卫条件必须对齐 — 一处有 `if _bnow` 另一处没有 = 隐蔽缺陷; ②战斗瞬态的 obs **部分少报**（非全空）是比全空拍更隐蔽的误报源，全空拍防护（L934 `if not _bnow`）拦不住部分少报; ③duel 中蓝英雄死 = game_over = ep 终止，游戏引擎已处理，**不需要额外 reward proxy** — proxy 只在"蓝英雄死但 ep 不终止"的 1v3/1v7 场景才有必要; ④日志分析发现"同类事件频率异常"（TOWN_CAPTURE=49 但 BHERO_KILL=0）时应立即启动核查，不可放过。
- **复现/验证**: `grep -c 'TOWN_CAPTURE.*duel' train_loop.log` = 49 (修复前); `grep -c 'BHERO_KILL' train_loop.log` = 0 (全图); duel 局 TOWN_CAPTURE 全部 blue_hero_killed=[1] + step 28-193 + ep 正常结束 → 49/49 误报。修复后 duel 局不再触发 C 方案 TOWN_CAPTURE。
- **关联**: #210（HERO_DEATH 与 C 方案 proxy 正交）/ #204（0 命中三义性）/ 知识库「T06 duel C 方案 hero-kill proxy +100 全误报修复」章 / `ep_runner_one.py` L944-962 / #212（同窗 T06 duel 地图证伪）。

#### #214 72X72_02_duel 引擎 reset 冷启动竞态 → 首拍 obs 全空 `steps=1 secs=603 obs_nz=0` → 方案 A 脏样本过滤 (2026-09-13, 日志分析实锤) — ✅ 已修
- **状态**: ✅ 已修 (train_wsl2_ppo_v2.py L220-225 加 `obs_nz==0 → return None` 过滤, 脏样本不进 PPO buffer; checkpoint step=675915 续训)
- **背景**: 09-13 日志分析发现 `72X72_02_duel` 4 局 `steps=1 secs=603 obs_nz=0`（`no_own_town` + `hero=(0,0) towns=[NONE]`），同图其余 103 局正常（obs_nz=301）。`01_duel`/`108X108 duel` 0 局命中，异常仅 02_duel。
- **定判过程**: ①地图文件正常（objects.json 蓝方 hero_1(66,66)/红方 hero_0(5,5)/town_0/1 全在）→ 非地图缺陷; ②`secs=603`（≈600 秒）= 首拍 `env.reset()` 阻塞 600 秒后正常返回全零 obs（引擎冷启动竞态，obs 段填充线程未就绪）; ③全零 obs → `_own=None`（8 城段全 0）→ `start_home=False` 打印 `abort(no_own_town)`（[ep_runner_one.py L596](file:///d:/Bigdata/hero3_fresh/ep_runner_one.py#L596)）→ 软放弃不终止 → 但 `act=16` 无效动作 + 引擎 `done=True` → 单步即终局 `steps=1`; ④01_duel/108X108 不命中 = load 顺序/共享内存缓存状态差异（非确定性竞态，偶发 4/103≈4%）。
- **影响评估**: 4 局全零 obs + 无效动作 = 脏样本，进 buffer 会污染 PPO 价值网（"无效动作→12.5 reward" 的错误价值关联）。占比小（4/103）且 PPO 有 clip+GAE 截断，影响可控，但判据统计需剔除。
- **修复 — 方案 A 脏样本过滤 (最稳，1 行，零引擎改动)**: [train_wsl2_ppo_v2.py L220-225](file:///d:/Bigdata/hero3_fresh/train_wsl2_ppo_v2.py#L220-L225) `obs_nz==0 → print([FILTER]) → return None`，调用方 L377 `if traj is None: continue` 已处理 None → 全零 obs 局不进 buffer。停训窗：`wsl -u root systemctl stop homm3-train-v5` → 清 `py/__pycache__` + `py/vcmi_protocol/__pycache__` + `scripts/__pycache__` → `systemctl start` resume step=675915。
- **教训**: ①`obs_nz=0` 是引擎冷启动竞态的信号（`secs≈600` 首拍阻塞 + obs 全零 + `no_own_town`），非地图缺陷 — 排查顺序先查地图文件（objects/header），再查 reset 时序; ②duel 图引擎 reset 竞态偶发命中，但**全零 obs 局对 PPO 价值网是纯噪声**（无学习价值），训练端一行过滤即可消除污染，零引擎改动（错窗纪律友好）; ③方案 B（引擎 reset 重试 1-2 次）留作后续 — 需改 ep_runner + 清缓存 + 单独开引擎轴，且不改引擎 C++ 根因（reset 卡死在引擎侧）。
- **复现/验证**: `grep -c 'FILTER.*obs_nz=0' train_loop.log` = 修复后脏样本被过滤次数（应为 4 的倍数，每局 1 条）; 修复前 `grep -c 'obs_nz=0' train_loop.log` 含正常局 obs_nz=0（无，正常局 obs_nz=301）; 判据统计剔除 `steps=1 obs_nz=0` 局。
- **关联**: #212（同窗 02_duel 地图缺陷证伪）/ #213（duel C 方案误报）/ 知识库「T7.4 死亡惩罚 09-13 方向纠正 + 02_duel 引擎 reset 竞态」章 / `train_wsl2_ppo_v2.py` L220-225 / `ep_runner_one.py` L590-596 `no_own_town` 软放弃段。

#### #215 King of Pain L69 字符串截断导致地图被 Python 解析器 drop，MAPS 静默少 1 张 (2026-09-13, 用户"King of Pain 入池"指令核实发现) — ✅ 已修
- **状态**: ✅ 已修 (train_wsl2_ppo_v2.py L69 `"King_of_Pain_h3` → `"King_of_Pain_h3m.vmap",` 补全闭合, py_compile OK, AST 解析 MAPS=9)
- **背景**: 用户指令"King of Pain.h3m.vmap，把这个地图加进来训练"。核实 L69 时发现该条已写但**字符串被截断**（`"King_of_Pain_h3` 未闭合引号），Python 解析器把该条视为无效/合并到上条 → King 从未真正入 MAPS，`maps=9` 与 King 缺失同时存在但日志无报错（`random.choice(MAPS)` 抽不到 King 属正常，误判为"9 图抽样需时间"）。
- **根因 — 字符串截断无报错**: 上一轮改 MAPS 时 L69 写入 `King_of_Pain_h3` 但**漏了后续 `m.vmap",` 部分**，引号未闭合。Python 对这种截断的处理 = 解析器把该条目 drop（不会像 `SyntaxError` 那样报错退出，因为文件其余部分合法），导致 MAPS 静默少 1 张。`py_compile` 通过（语法层面合法，只是少了元素），AST 解析确认 `MAPS len = 9` 而非预期的 10。
- **坑 — 静默 drop 的隐蔽性**: ①`py_compile` 不报错（语法合法）；②训练正常启动、`maps=9` 与磁盘一致（9 是实际 MAPS 长度）；③日志无"King of Pain" episode（`random.choice` 抽不到 = 正常表象）；④误判为"9 图抽样需时间才抽中"，实际 King 根本不在池里。
- **修复**: L69 SearchReplace 补全为 `"King_of_Pain_h3m.vmap",`（带 `_h3m` 后缀，`strategic_env.py` 强制要求 mapname 含 s1/mini/adventure/h3m 之一）。补全后 AST 解析 MAPS=9（T05 3 + T06 3 + King 1 + T04 2），`maps=9` 与磁盘一致。
- **教训**: ①改 MAPS 列表后**必须 AST 解析验证条数**（`python3 -c "import ast; t=ast.parse(open('train_wsl2_ppo_v2.py').read()); [print(n.elts) for n in ast.walk(t) if isinstance(n, ast.List) and any(hasattr(e,'id') and e.id=='MAPS' for e in n.elts) if False]"` 简化为 `grep -c '\.vmap' train_wsl2_ppo_v2.py` 对比预期条数）；②字符串截断 = 引号未闭合 → Python 静默 drop，`py_compile` 拦不住，必须**逐条核对 MAPS 元素数量**；③用户说"把 X 图加进来"时，**先核实 X 是否已在 MAPS 但被截断/drop**，而非直接追加（避免重复条目或漏检截断）。
- **复现/验证**: `python3 -c "import ast,sys; t=ast.parse(open('train_wsl2_ppo_v2.py').read()); [print(len(n.elts)) for n in ast.walk(t) if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='MAPS' for x in n.targets)]"` → 输出 `9`（修复前输出 `8`，King 被 drop）。`grep -n 'King_of_Pain' train_wsl2_ppo_v2.py` → L69 `"King_of_Pain_h3m.vmap",`（闭合正常）。
- **关联**: #214（02_duel 引擎 reset 竞态）/ 任务清单 09-13 地图轴增量（King of Pain 入池 + T04 回池 + T05 MIR 3 张移除）/ `train_wsl2_ppo_v2.py` L48-73 MAPS 段 / `strategic_env.py` L150-154 T04/T05/T06 引导分支（King 不带 T 前缀不走此分支，潜在引导缺失需观察）。

#### #216 VCMI saveMap randomTown subtype = `core:object` 占位符 (2026-09-13, King of Pain roundtrip 撞 KeyError 时发现) — ✅ 已修
- **状态**: ✅ 已修（`py/vcmi_full_to_slim.py` L146-165 加回退链 `object → availableFactions[0] → dungeon`；`py/fix_kop_town_subtype.py` 就地修补 3 处副本 × 5 镇 → `core:dungeon`）
- **背景**: P11 roundtrip 首次跑通时 `py/vmap2h3m.py` L276 `FACTION_CODE[sub_raw]` 抛 `KeyError: 'object'`。探查 41 张训练图 town subtype 分布 → **King_of_Pain_h3m.vmap 是唯一 `core:object` 的图**（其余 L1/T01-T06 全为真族系 `core:castle/conflux/dungeon` 等）。
- **根因**: VCMI 引擎 `randomTown` 对象的 `subtype` 字段被 saveMap 写成 `core:object` 占位符（真族系藏在 `options.availableFactions` 数组里，King of Pain 5 镇全指向 `dungeon`）。`py/vcmi_full_to_slim.py` 原直接透传 subtype → 精简 vmap 沿用占位符 → vmap2h3m.py 查 FACTION_CODE 表找不到 `object` → KeyError。
- **坑 — 单点污染**: 全库 41 张训练图仅 King 一张异常，正常图掩盖了转换 bug 长达 12 天（09-01 首次运行到 09-13 才撞上 roundtrip 触发）。
- **修复**: ①`vcmi_full_to_slim.py` town 转换分支加**三级回退**: `obj.subtype` (非 object 占位) → `options.availableFactions[0]` → `dungeon` 兜底；②`fix_kop_town_subtype.py` 剥 JSON 注释后按 (x,y) 匹配就地修补，不动其它字段（保留 owner/formation/mask/template）。
- **教训**: ①VCMI saveMap 不保证 subtype 是真值，尤其随机化对象（randomTown/randomMonster/randomHero），必须查 options 里的具体化字段；②`peep 41 张训练图 subtype 分布` 是最快的异常检测手段（Counter + 找唯一值）；③精简格式字段值 = 训练时 ep_runner 会真查 FACTION_CODE 表，占位符 = 隐藏地雷。
- **复现/验证**: `python3 py/peek_t06_town_subtype.py` 输出 King `Counter({'core:object': 5})`（修补前）/ `Counter({'core:dungeon': 5})`（修补后）；41 张训练图 town subtype 分布 → 唯一异常即 King。
- **关联**: #215（King L69 字符串截断）/ P10-B 设计稿 §8 / P11 VMAP→H3M 段 / `py/vmap2h3m.py` L276 / `py/vcmi_full_to_slim.py` L146-165 / `py/fix_kop_town_subtype.py`。

#### #217 MINE_CODE 别名不完整 → crystalCavern/orePit/sulfurDune KeyError (2026-09-13, King of Pain roundtrip 撞 KeyError 时发现) — ✅ 已修
- **状态**: ✅ 已修（`py/vmap2h3m.py` MINE_CODE 补别名映射 + abandoned 走跳过）
- **背景**: 修补完 town subtype 后重跑 roundtrip，vmap2h3m.py L305 抛 `KeyError: "mine 'crystalCavern' 无 subid 映射"`。
- **根因**: `MINE_CODE` 只写死了 7 条 canonical 名 (`sawmill/alchemistLab/oreMine/sulfurMine/crystalMine/gemPond/goldMine`)，但 VCMI 完整 vmap 用的是**描述性长名** (`orePit/sulfurDune/crystalCavern`)。King of Pain 38 张 mine 分布：sawmill×6, alchemistLab×6, sulfurDune×6, goldMine×5, crystalCavern×5, orePit×5, gemPond×4, abandoned×1。
- **坑 — 长名 vs 短名不对称**: RESOURCE_CODE 用短名 (`wood/ore/sulfur/crystal/gems/gold`)，MINE_CODE 却混用了长名 (`sawmill/alchemistLab`) 和短名 (`oreMine/goldMine`)——不同来源对象类型命名风格不一致，转换器必须两个都覆盖。
- **修复**: `MINE_CODE` 补别名 `'oreMine':2/'orePit':2, 'sulfurMine':3/'sulfurDune':3, 'crystalMine':4/'crystalCavern':4`，同时补 `'abandoned': -1` 走跳过分支（donor 库无独立 abandoned 模板）。`abandoned` 语义 = 子资源已损毁的矿洞，H3M 无对应独立 def，写文件会破坏对账。
- **教训**: ①双表 (`FACTION_CODE`/`MINE_CODE`/`RESOURCE_CODE`) 必须覆盖 VCMI 所有实际命名变体，官方图用长名 → 别名映射是刚需；②`abandoned` 类"半成品"对象要么跳过要么合成，**不能**当普通矿硬写（subid≥7 = 已损坏语义，引擎读时会走 abandoned 分支而不是普通矿）。
- **复现/验证**: `python3 py/peek_kop_mines.py` 输出 mine subtype Counter；修补后 vmap2h3m.py 输出 counts = {'hero':1,'mine':37,'town':5,'resource':68,'monster':57} = 168/173 (37 mine = 38 - 1 abandoned)。
- **关联**: #216（town subtype 占位符）/ P11 VMAP→H3M 段 / `py/vmap2h3m.py` L44-49 MINE_CODE / L302-314 mine 分支 / `py/peek_kop_mines.py`。

#### #218 h3m2vmap 批量转换: `cb->gameState().getMap()` 空指针 SIGSEGV (2026-09-13, 全库 159 张 H3M 批量转 VMAP 时发现) — ✅ 已修
- **状态**: ✅ 已修（`tools/h3m2vmap/main.cpp` loadMap 前 `new EditorCallback(nullptr)` 传入 + `editorCb->setMap(map.get())` 绑定；已同步至 `/home/administrator/vcmi-native/tools/h3m2vmap/main.cpp` 并重建）
- **背景**: 用户指令"把 H3M 地图都转换为 VMAP，每次一张检查"。全库 159 张 H3M (v21=56, v28=47, v14=47, None=9)。首张 `King of Pain` 一次跑通；其余带装备英雄的图（含大量装备/宝物）在 `Saving objects` 阶段稳定 SIGSEGV (rc=-11)。
- **根因**: VCMI 保存英雄装备时 (`CGHeroInstance::serializeCommonOptions`)，`CArtifactSet::serializeJsonArtifacts` 需要 `const_cast<CMap*>(...)` 做 artifact 模板查找。原始代码走 `else` 分支 `&cb->gameState().getMap()` — 但 `h3m2vmap` 是**离线工具**，`cb` 由 `main.cpp` 传 `nullptr` → 空指针解引用 SIGSEGV。
- **坑 — 官方图与 VMAP 图不对称**: L1/T01-T06 训练图**早已**是 VMAP (VCMI 引擎生成)，装备 hero 走的是 `gameState` 路径（cb 非空）；只有 H3M 首次转换才触发 `cb=nullptr` 分支，King of Pain 恰是**不带装备**的图，掩盖问题；批量跑剩余 158 张带装备图全部崩溃。
- **修复 — 利用引擎既有 EditorCallback 分支**: 源码 `CGHeroInstance.cpp` L1646-1652 早就留了 `dynamic_cast<EditorCallback*>(cb)` 分支专门处理编辑器场景（走 `ecb->getMapConstPtr()`）。只需让 `h3m2vmap` 正确初始化该 callback：
  ```cpp
  EditorCallback * editorCb = new EditorCallback(nullptr);
  auto map = service.loadMap(data.data(), ..., inPath, "map", "CP1252", editorCb);
  if(!map) { delete editorCb; delete LIBRARY; return 1; }
  editorCb->setMap(map.get());  // 绑定已加载 map
  // ... saveMap(data, map, writer, editorCb);  // 传入 editorCb 而非 nullptr
  ```
- **教训**: ①VCMI `saveMap` 支持 `EditorCallback` 作为 `IGameInfoCallback` 的离线场景实化，工具链应显式使用而非传 `nullptr`；②`h3m2vmap` 首次跑通不代表全库能跑，必须批量抽样（带装备 hero、带装备宝物、地下层、多镇）；③"cb=nullptr 崩溃"的地图特征 = **含装备 hero**，可用 `grep -l '"equipments"' *.vmap` 预判。
- **复现/验证**: 修复前 `h3m2vmap --save "A Warm and Familiar Place.h3m" out.vmap` → SIGSEGV rc=-11，gdb 栈顶 `rip 0x7ffff7a260b0 <CGHeroInstance::serializeCommonOptions+1600>`；修复后同命令 rc=0 输出 vmap。全库 159 张批量跑：`ok=130 + warn_mismatch=29 + fail=0`。
- **关联**: #219（析构期 SIGSEGV #2 exit(0)）/ P10-B h3m2vmap 转换器 §6 B2 / `tools/h3m2vmap/main.cpp` L28-70 / `/home/administrator/vcmi-native/lib/mapObjects/CGHeroInstance.cpp` L1646-1652 / `lib/callback/EditorCallback.h` / `maps/h3m_to_vmap/_report.json`。

#### #219 h3m2vmap 析构期 SIGSEGV #2: TextLocalizationContainer 与 Bonus 析构顺序 (2026-09-13, 全库批量转换时发现) — ✅ 已修（跳过析构）
- **状态**: ✅ 已修（`tools/h3m2vmap/main.cpp` 结尾用 `exit(0)` 跳过析构链；不重编 libvcmi.so，不改 rel/ 下 .so）
- **背景**: #218 修复后批量跑第 3 张（144x144 大图 `Back For Revenge`）在 `ROUNDTRIP MISMATCH` 打印后稳定 SIGSEGV。前 2 张（36x36/72x72 小图）正常退出。
- **根因**: roundtrip 完成、map 对象析构期间，`Bonus::Description` 内部文本引用触发 `TextLocalizationContainer::translateString` → `std::unordered_map::_M_find_before_node` 桶数组非法访问。原因 = **析构顺序错乱**：`LIBRARY` 里的文本容器先被删除（`delete LIBRARY`），但 map 析构时 bonus 字段仍持有对已释放容器的引用。
- **坑 — 大地图才触发**: 小图（36x36/72x72）bonus 字段少，析构路径短，未命中已释放指针；144x144 大图对象数量大，析构时 bonus 引用密度高，稳定命中 UAF。同类型崩溃只与对象数量相关，与 map 内容无关。
- **修复 — 跳过析构**: 工具是一次性进程，roundtrip 完成 = 目标已达成，不需要优雅析构。`exit(0)` 直接终止进程，跳过所有析构链 → 完全绕开 UAF。
  ```cpp
  // 2026-09-13 修复 #2: roundtrip 后正常析构触发 SIGSEGV
  // (TextLocalizationContainer 与 map 对象析构顺序问题)
  exit(0);
  ```
- **教训**: ①一次性的 CLI 工具不需要优雅析构，`exit(0)` 是最省事的兜底；②`delete LIBRARY` 顺序 = UAF 高危信号，凡是"引用其他模块数据"的对象都要警惕析构顺序；③大地图 roundtrip 的 MISMATCH 与析构崩溃是两个独立问题，前者警告即可（序列化不完全），后者需跳过析构。
- **复现/验证**: 修复前 `Back For Revenge` → rc=-11；修复后同地图 rc=0 且 vmap 落盘完整（5317 objects）。全库 159 张批量跑：0 张 SIGSEGV。
- **关联**: #218（EditorCallback 方案）/ #220（saveMap JSON 注释兼容）/ `tools/h3m2vmap/main.cpp` 尾部 / `maps/h3m_to_vmap/_report.json`。

#### #220 h3m2vmap 输出 JSON 含 C++ 注释 + 144x144 大图 roundtrip MISMATCH (2026-09-13, 全库批量转换时发现) — ✅ 已修（Python 侧兼容）
- **状态**: ✅ 已修（`py/h3m_batch_to_vmap.py` 加 `_strip_c_comments` + `_loads_permissive`；roundtrip MISMATCH 降级为警告不阻塞 rc=0）
- **背景**: 工具链 C++ 层两处 SIGSEGV 修复后批量跑前 20 张 → 12 张 `validate_exception: json.loads` 失败，报错 `Expecting property name enclosed in double quotes`。剩余为 roundtrip MISMATCH。
- **根因 1 (JSON 注释)**: VCMI `saveMap` 用 `writeJson` 序列化时会插入 C++ 单行注释（形如 `// game` 之类），**输出不是严格合法 JSON**。VCMI 引擎自身解析器容错，但 Python `json.loads` 严格模式报错。
- **根因 2 (roundtrip MISMATCH)**: 144x144 大地图（18 张）saveMap 序列化不完全，roundtrip 会丢少量对象（例：`A Viking` 3092→3054, `Back For Revenge` 5318→5317）。原因 = VCMI saveMap 存在不完全序列化路径（地下层对象、装饰性元素等），非阻塞。
- **修复 1 (JSON 兼容)**: `py/h3m_batch_to_vmap.py` 加 `_strip_c_comments` 移除 `//` 到行尾（保留字符串内 `//`），`_loads_permissive` 先严格解析失败后 strip 重试。
- **修复 2 (MISMATCH 降级)**: C++ `main.cpp` roundtrip 检测到数量不匹配只打 WARNING 不再 `return 1`；Python 侧新增 `warn_mismatch` 状态计数（区别于 `ok`/`fail`）。
- **教训**: ①VCMI saveMap 输出**非严格合法 JSON** 是**引擎特性**而非 bug，Python 侧必须剥注释；②roundtrip MISMATCH 大地图普遍存在（29/159 ≈ 18%），判定为警告不阻塞批量流程；③"引擎能读 ≠ Python json.loads 能读"是常见坑，涉及 VCMI JSON IO 的下游工具必须加 permissive 层。
- **复现/验证**: 修复前 12 张 `json.loads` 抛异常；修复后 `_strip_c_comments` + `_loads_permissive` 全库通过。全库最终：`ok=130, warn_mismatch=29, fail=0`；尺寸分布 36x36=32 / 72x72=71 / 108x108=38 / 144x144=18。
- **关联**: #218 / #219 / `py/h3m_batch_to_vmap.py` L60-90 / `tools/h3m2vmap/main.cpp` roundtrip 段 / `maps/h3m_to_vmap/_report.json`。

#### #221 King of Pain 引擎 reset 竞态复现（H3M 72x72 大图同 02_duel 模式）— 方案 A 全捕获，无 PPO 污染 (2026-09-13, 训练日志分析) — ✅ 已捕获
- **状态**: ✅ 方案 A 已捕获（`train_wsl2_ppo_v2.py` L220-225 `obs_nz==0 → return None`），3 局 King 首局全部 `[FILTER] obs_nz=0 脏样本丢弃`，0 条进 buffer
- **背景**: King of Pain H3M 官方图（72x72）入池后首局 3 次全部 `steps=1, secs=603, r=12.5, obs_nz=0`。同 #214 的 02_duel 模式：引擎 reset ~600s 冷启动后 obs 段填充线程未就绪 → `no_own_town` abort → 单步终局。
- **共性**: H3M 72x72 大图（King）与 T06 duel 图（02_duel）reset 耗时 ~600s 共性 = 地图对象数量多（King 173 对象 / 02_duel 数百对象），引擎 obs 段填充耗时。T05/T06 小图（36X36/52X52）reset <5s 无此问题。
- **影响**: King 在 9 图池里占 1/9 抽样频率，且每次抽中都是脏样本 = **暂时无有效训练贡献**。若持续 1 步 abort（需观察后续局），可能是 `vcmi_full_to_slim.py` 转换质量或引擎 reset 初始化时序问题，需排查 VMAP 文件结构。
- **处置**: 暂不移出 MAPS（样本量不足下结论）。方案 A 过滤保护了 PPO buffer 不污染。持续观察：若 5 局+ 全部 1 步 abort → 排查 VMAP 或移出 MAPS。
- **⚠️ 根因修正 (2026-09-13)**: 本条假设"reset 竞态"为初判。经逐层排查（#222/#223）证实真实根因 = **King VMAP `header.players = []` 空数组**（#222），T06 _02 系列 4 张同病（#223），引擎不创建玩家槽位 → obs 城段 owner 全为 0 → `no_own_town` 是**必然触发**而非竞态偶发。方案 A 过滤仍生效但方向错——脏样本源是地图本身，不是引擎时序。
- **⚠️ 后续死因: dragon identifier 缺失 (2026-09-13)**: King 修复 `header.players` 后训练日志仍报错 `[%p/runServer][global] ERROR Failed to find object of type monster::core:dragon` → `NEW_GAME` 失败 → 引擎挂起/反复重启。根因 = King of Pain H3M 官方图引用 SoD 龙单位（`monster::core:dragon`），当前 `libvcmi.so` 注册表无此 identifier。处置：用户确认 King 在修改中，暂不干预训练。
- **T04 状态更新 (2026-09-13)**: T04 2 张（`T04_adventure_36X36_01` + `T04_adventure_30X30_01`）已从 MAPS 移除（用户拍板走大图轴），T7.4 判据 1 样本源转 T06 大图池。
- **关联**: #214（02_duel 引擎 reset 竞态 + 方案 A）/ #215（King L69 语法截断）/ #216-#220（H3M 转换工具链）/ #222（King 真实根因：header.players=[]，本条竞态假设已被 #222 修正）/ #223（T06 _02 系列批量修补）/ `train_wsl2_ppo_v2.py` L220-225 / `ep_runner_one.py` L590-596 `no_own_town` 软放弃段。

#### #222 King_of_Pain_h3m.vmap `header.players=[]` 真实根因 + 单图 patch 修补 (2026-09-13) — ✅ 已修复
- **状态**: ✅ `py/patch_king_players.py` v2 已执行，King VMAP header.players 注入 blue/red（对齐 T01 格式），town_1 + hero_0 owner → blue，训练方 = player 0 = blue 逻辑一致；备份 `King_of_Pain_h3m.vmap.bak_players_patch`
- **背景**: 训练日志 King 3 局全部 `steps=1, secs=603, obs_nz=0, no_own_town abort`。初判竞态（#221），后逐层排查发现 3 种可能（引擎 reset 竞态 / 地图初始化异常 / 地图 players 段缺失）；用 `py/_check_king.py` + `py/_deep_king.py` 对比 L1/T01/T06 三份有效训练图，坐实是地图初始化异常。
- **根因**: King VMAP 解包后 `header.players = []`（空数组），而 L1/T01/T06 有效图为 `{blue:{...}, red:{...}}` dict-of-players 格式。VCMI 引擎按 `header.players` 创建玩家槽位（player 0..N-1），空数组 → 无玩家索引 → obs 8 城段 owner 字段全 0 → `ep_runner_one.py` L584-596 `no_own_town` 判定必然 abort。
- **对象分布（King 原状）**: 5 town + 1 hero，town_0=orange, town_1=red, town_2=blue, town_3/4=None, hero_0=red。是**多玩家 H3M 图**（原 5 色），非 1v1 训练图。
- **修补策略**: 与 T01 对齐 header.players 加 blue/red 双槽；town_1 + hero_0 owner 改 blue（让蓝方 = player 0 至少 1 城 1 将）；Red 空槽保留 1v1 语义（AI 只跑 player 0，Red 是否空不影响训练）。修补后 Blue 有 2 town（town_1+town_2）+ 1 hero，Neutral 有 3 town。
- **踩坑**: 
  - King 是 **5 玩家 H3M 图**（不是 1v1），h3m2vmap 转换后 `header.players=[]` = 工具链缺陷（其他 158 张 H3M 同病，只是未入池未暴露）；
  - `objects.json` 是 **dict-of-dicts**（`name → obj`），非 list，遍历用 `for k, v in objs.items()`；
  - `owner` 字段位置在 `obj.options.owner`（不是 `obj.owner`），值是颜色字符串（"blue"/"red"/"orange"/"teal"/"green"/"yellow"）不是玩家索引；
  - obs 城段 `obs[336:480]` 8 城 × 18 字段，owner 位置在 `_tb2+1`，coords 在 `_tb2+2/+3`；`no_own_town` 判定 = `owner=0 且 coords 有值 → 己方城`；
  - `header.mods: []` → `{}` 也对齐 T01（list → dict）。
- **修复**: `py/patch_king_players.py` v2 脚本（zipfile 重写包，header.json + objects.json 同步改，TMP 原子替换）。运行结果：`players BEFORE=[] → AFTER={blue,red}`；`town_1 owner red→blue`；`hero_0 owner red→blue`；文件 +68 bytes（10713→10781）；备份保留原状。
- **教训**: 
  - `obs_nz=0 + no_own_town` 二义性诊断：#214 定义为"引擎 reset 竞态"，但**同症状可能有多种根因**（本次 #222 = 地图 header.players 空）。排查路径 = 优先解包 VMAP 看 `header.players` 而非先假想时序。
  - H3M→VMAP 转换工具链（h3m2vmap 系列）未处理 `header.players` 字段是**已知缺陷 #4**：L1/T01 是人工制作的 VMAP（有 players），H3M 转换产物全部 `players=[]`。批量入池前需批量修补或改工具链。
- **验证**: 修补后训练应显示 King 首局 `steps>>1, obs_nz>0, no_own_town 不再触发`。训练当前 inactive，patched VMAP 已就位，等下一次启动可回归验证。若仍 1 步 abort 则说明还有第二重缺陷（如 mods 缺 core 依赖等），再逐层排查。
- **关联**: #221（竞态假设被本条修正）/ #214（方案 A 过滤）/ #215-#220（King L69 + h3m2vmap 工具链）/ `py/patch_king_players.py` / `maps/training/King_of_Pain_h3m.vmap` / `maps/training/King_of_Pain_h3m.vmap.bak_players_patch`。
- **后续**: (a) 启动训练验证 King 是否 `obs_nz>0`；(b) 批量排查 `maps/training/*.vmap` 的 `header.players` 是否有其他图也是空数组；(c) 长期：改 h3m2vmap 工具链在导出时注入默认 `header.players`。

#### #223 T06 _02 系列 4 张 VMAP 批量 `header.players=[]` 修补 (2026-09-13) — ✅ 已修复
- **状态**: ✅ `py/patch_t06_02_players.py` 已执行，4/4 全部成功；备份 `.vmap.bak_players_patch` 保留；`py/_scan_players.py` 回归 60 张 VMAP 全部 `players OK`，`players=[]` 空数组 0 张
- **背景**: #222 修补 King 后，用 `py/_scan_players.py` 批量扫描 60 张 VMAP，发现 4 张 `T06_adventure_*_02(_duel).vmap` 也有 `header.players=[]` 空数组（`_01` 系列正常）。**其中 `T06_adventure_72X72_02_duel.vmap` 就在训练 MAPS 名单 L64**（09-12 错窗切地图轴新增），若不修补下次训练启动会同样 1 步 abort。
- **根因**: T06 `_02` 系列是 `fix_t06_maps.py` 生成的镜像变体，与 `_01` 走同一生成管线但生成脚本未注入 `header.players`。同 #222，h3m2vmap / T06 生成脚本共同缺陷 = 未处理 `header.players` 字段。
- **修补差异（vs King）**: 
  - King 是 5 玩家 H3M 图，对象 owner 也错（hero_0=red），需同时改 objects.json
  - T06 _02 是标准 1v1/1v3 生成图，town/hero owner 已正确（town_0/hero_0=red @ 左上，town_1/hero_1=blue @ 右下），**只改 header.json 不动 objects.json**
  - mods: `[]` → `{}` 与 King 一致
- **修补结果**:
  | 文件 | 对象 | 尺寸 |
  |------|------|------|
  | T06_72X72_02_duel.vmap | 2 town + 2 hero | 1723→1804 |
  | T06_72X72_02.vmap | 4 town + 4 hero | 1787→1868 |
  | T06_108X108_02_duel.vmap | 2 town + 2 hero | 1895→1976 |
  | T06_108X108_02.vmap | 4 town + 4 hero | 1959→2038 |
- **教训**: 
  - `header.players=[]` 是**系统性缺陷**（King H3M + T06 _02 生成脚本共 5 张受影响），不是孤立个案；
  - 未来新增 VMAP 入 MAPS 前**必扫** `header.players`（写 `py/_scan_players.py` 常态化到入池流程）；
  - L1 老 VMAP 是 `players=[{...}, {...}]` list 格式（8 张，非空数组），引擎也能识别，属"兼容但不标准"，本轮未动（不在 MAPS）。
- **回归验证**: 扫描结果 52 张 `players OK` + 8 张 L1 老格式 = 60 张全部可识别，`players=[]` 归零。
- **关联**: #222（King 单图 patch，本条为其批量扩展）/ #214（方案 A 过滤仍生效作兜底）/ `py/patch_t06_02_players.py` / `py/_scan_players.py` / `train_wsl2_ppo_v2.py` L64（`T06_adventure_72X72_02_duel.vmap`）。
- **训练 MAPS 名单现状 (2026-09-13 更新)**: 10 图全部 `players OK`（T05×3 + T06 72X72_01_duel + 72X72_01 + 72X72_02 + 108X108_02_duel + 108X108_02 + King_h3m），无脏图。T04 2 张（36X36_01 + 30X30_01）已移除，T06 72X72_02 + 108X108_02 + 108X108_02_duel 3 张新入池。

#### #224 VMAP 运行时部署拓扑：maps/training 改了不部署 = 旧图继续跑（两次事故放大器） (2026-09-14) — ✅ 已固化
- **现象**: 09-14 修 T06 _02 4 图 header 后探针仍 segfault/挂死，一度以为"补丁非充分还有第二层缺陷"；交叉拼装探针图（好 header+坏 body / 坏 header+好 body）两张都报 `Bad value for map: xxx.vmap (relative to: ./data/Maps)`，rc=1 死在 `MLClient.cpp` validateFile（L177-194），根本没进引擎地图加载器。
- **根因（拓扑事实，代码+软链实锤）**:
  - ep_runner 连接器 = 进程内 ctypes libmlclient.so，`MLClient.cpp` L489 `chdir(VCMI_BIN_DIR)` 后从 **`userDataPath()/Maps` = `VCMI_BIN_DIR/data/Maps`** 读图（L307-308 validateFile / L421 拼 `Maps/<mapname>`）；地图**不是**直接从仓库 `maps/training/` 读。
  - 两棵 VCMI 树的入口 `vcmi-native/rel/bin/data/Maps` 与 `vcmi-native-build/rel/bin/data/Maps` **都是符号链接，指向同一真实目录** `/mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps`（= Windows `vcmi/data/Maps`）。**不是双副本**——往两处 cp 实际写同一文件。
  - 09-13 的 players 补丁、09-14 上午的 header 补丁都只改了权威源 `maps/training/`，运行时真实目录里还是 09-06/09-12 旧文件。探针"行为变化"（挂死→段错误）是非确定性竞态，不是补丁效果。
- **排查方法（复用）**: 训练/探针时 `pgrep -f ep_runner_one` → `ls -la /proc/<pid>/cwd`（= rel/bin）→ `ls --time-style` 对比运行时 vmap 与源文件 mtime/hash；`readlink -f <data/Maps>` 看真实目录。core dump 不可用（core_pattern=`|/wsl-capture-crash`，ulimit -c=0）。
- **探针图命名**: 地图名必须含 `s1/mini/adventure/h3m`（strategic_env.py L522 assert），且**必须先部署到运行时目录**否则 Bad value。
- **修复/固化**: `py/sync_maps_to_runtime.py`（#226 后建立的权威同步工具，见知识库 09-14 章）：MAPS 清单 AST 解析为唯一同步范围 + resolve() 软链去重 + 预检 + 原子写 + 写后 hash 复验。已写入 `.trae/rules/project_rules.md` 硬约束：**改/生成任何 .vmap 后必跑 `--strict`，rc≠0 禁训**。
- **教训**: "改了源文件"≠"运行时生效"；任何"修了没效果"先 hash/mtime 对比运行时产物再怀疑修复方向（呼应事实核查原则：以二进制产物为准）。
- **关联**: #222/#223（players/header 补丁只改源未部署的两批图）/ #225 / #226 / `py/sync_maps_to_runtime.py` / `ML/MLClient.cpp` L307/L421/L489。

#### #225 T06 _02 4 图 header 只有 5 字段：缺 8 字段 → `Invalid range provided: 0 ... -1` 挂死 / NEW_GAME SIGSEGV (2026-09-14) — ✅ 已修复
- **现象**（max_turns=1 单图探针，独立 outfile 避免与训练 traj 冲突）:
  - 72X72_02 / 72X72_02_duel（旧运行时图）：rc=137 挂满 timeout，`ERROR Failed to launch game: Invalid range provided: 0 ... -1`，死在 NEW_GAME 启动，traj 从未写。
  - 108X108_02 / _duel：rc=139 SIGSEGV（~17-20s），无明确 ERROR，日志止于 `[SRV-DIAG] NEW_GAME start`。
- **根因**: #223 只补了 players（注入 blue/red + mods→{}），但 `_02` 系 header.json 仍只有 5 字段（name/description/mapLevels/mods/players），正常 `_01` 系/108_01 系是 **13 字段**。源头 = `maps/training/regenerate_t06_108.py` L182 与 `regenerate_level5.py` L209 的 header 模板只写 5 字段。报错串定位到 `lib/CRandomGenerator.cpp` L59/81/96：对空容器随机取值（区间 0...-1），缺的 victoryConditions 等字段触发。
- **修复**: `py/patch_t06_02_header_0914.py` 补 8 字段：allowedArtifacts / defeatIconIndex / difficulty / victoryConditions=[standardDefeat, specialVictory] / triggeredEvents / versionMajor=1 / versionMinor=1 / victoryIconIndex=2（备份 `.bak_header_0914`）；两个生成器模板同步治本。**但单独补 header 探针仍失败——因为 #224 未部署**，部署到运行时真实目录后 4 图 max_turns=1 全绿（4-6s，obs_nz 249-291）。
- **完整 200 步局验证（rc=0 零致命）**: 72_02 110步/432s/r=217.0；72_02_duel 95步/389s/r=130.7；108_02 93步/400s/r=416.4；108_02_duel 30步/328s/r=36.2（蓝速败正常终局）。回池 MAPS 6→10，生产首局即原 SIGSEGV 图 108_02 完整 200 步 r=169.5。
- **教训**: header 字段完整性是入池硬门槛（players 只是其一）；sync 工具的预检已把 13 字段/双方城镇/owner 合法性固化，新图自动卡。
- **关联**: #223（players 层）/ #224（部署层）/ `py/patch_t06_02_header_0914.py` / `regenerate_t06_108.py` L182 / `regenerate_level5.py` L209。

#### #226 King of Pain 残余三层缺陷连环：core:dragon 非法 id / orange 玩家4 崩溃 / red 被 09-13 补丁错送成无城无英雄 (2026-09-14) — ✅ 已修复
- **现象**: #224 部署 players 修补版 King 后，603s 卡死消失但逐层炸出新错（典型剥洋葱）：
  1. `Failed to find object of type monster::core:dragon` → `Failed to resolve identifier`，NEW_GAME 失败。
  2. 修 dragon 后 rc=139 SIGSEGV，`ERROR Cannot find player 4 info!`（`lib/callback/CGameInfoCallback.cpp` L89，gameState().players 无 color=4=orange）。
  3. 修 orange 后 max_turns=1 通过（rc=0/3s/obs_nz=348），但 200 步局 60 步 `err=yes`，traj error = `name 'passable' is not defined`（见 #227）。
- **根因逐层**:
  - **dragon**: `py/vcmi_full_to_slim.py` MONSTER_LEVEL_MAP L36-37 把 randomMonsterLevel4/5 映射成 `core:dragon`，core mod 无此泛指 id（只有 redDragon/blackDragon/greenDragon，注册表在 `/home/administrator/vcmi-native/config/creatures/*.json`，**JSONC 带注释**需清洗后解析）。King 4 个守卫 monster_29/31/37/47。
  - **orange**: town_0(4,62) owner=`orange`（options.owner，藏在 options 内不在顶层），header 只注入 blue/red 两槽 → 引擎建 player 4 对象时找不到玩家信息直接段错误。
  - **red 无城无英雄（#222 补丁方向性错误）**: #222 的 `patch_king_players.py` 把原图**本属 red 的 town_1(10,8)+hero_0 一起改成了 blue**（脚本注释自承认"Red: 0 town + 0 hero"），blue 独占 2 城，red 空槽——这就是 `no_own_town` 脏局的另一半根因，当时"引擎会按默认生成"的假设不成立。
- **修复（1v3 重建，对齐 72X72_01 模板 schema：hero subtype=core:alchemist 职业 / options.type=英雄人物 / 城旁 3 格对角驻守）**:
  - `py/patch_king_dragon_0914.py`：4 个 dragon→core:swordsman（图内已在用的三兽集，量 4/6 不变，不叠强度轴；备份 `.bak_dragon_0914`）；转换器 L36-39 治本。
  - `py/patch_king_rebuild_0914.py`（备份 `.bak_rebuild_0914`）：town_0 orange→blue、town_1 blue→**red（还原）**、town_4 null→blue（town_2 保 blue、town_3 留中立）；hero_0→red 移 (13,11)；新建 hero_1/2/3 blue @(7,65)/(62,61)/(57,31)，iona/edric/christian + 25 peasant。脚本带**驻守城镇距离=3、其他城≥5、非同格、0≤坐标<72** 断言，173→176 对象。
  - 验证：max_turns=1 rc0/obs_nz=348；修掉 #227 后完整局 **120步/240s/r=183.1 rc=0 err=no**。
- **非致命遗留（不阻塞）**: 启动警告 `Abandoned mine at (38,70) has no valid resource candidates`（1 个废弃矿）；偶发 `Cannot move hero, destination tile is blocked`（gr57 地形"全通"假设与引擎有小偏差，服务器拒绝单步，不崩不脏）。
- **教训**: ① 对象 owner 在 `obj.options.owner`（颜色字符串，只允许 red/blue/null，orange 等=非法槽）；② 补丁改归属后必须验证**双方都有城有英雄**，不能制造空阵营；③ 修一层崩一层是地图加载顺序决定的正常现象，必须跑到 rc=0 err=no 完整局才算数；④ 难度纪律下修非法怪用图内既有三兽集，不引入红龙新强度。
- **关联**: #221/#222（players/竞态）/ #224（部署）/ #227（passable）/ `py/vcmi_full_to_slim.py` L32-40 / `py/patch_king_dragon_0914.py` / `py/patch_king_rebuild_0914.py`。
- **生产闭环 (2026-09-14 同窗口 36 局)**: resume 685402 后 King 先出 1 局脏（steps=1/603s，方案 A FILTER 拦截），随后**首个生产有效局 149 步/259s/r=157.2/obs_nz=348/err=no**（[GUARD_DONE] step149 正常早停），与探针局（120 步 r=183.1）互证。同窗 72_02 系/108_02 系零 SIGSEGV 零 err=yes，TOWN_CAPTURE 4 次全在 1v3 图，HERO_DEATH=0。明细见知识库「生产回池首批验证」小节。

#### #227 ep_runner L1196 `passable` 只在带模型分支定义：无模型探针横跳即 NameError，err=yes 局静默不进 buffer (2026-09-14) — ✅ 已修复
- **现象**: King 完整局探针（不带 `--model`）60 步提前结束，traj `"error": "name 'passable' is not defined"`；主日志侧 `train_wsl2_ppo_v2.py` L240 `if d.get("steps",0)>0 and not d.get("error")` 决定进 buffer——**error 局被静默跳过且无 [FILTER] 日志**（白跑还看不见）。
- **根因**: `passable = torch.tensor(obs[3211:3219]...)` 只在 `if red_model is not None:`（L435，训练带 `--model`）分支内定义；L519 同引用在分支内安全，**L1196 两格往返横跳处理（move_to_force 之后无条件执行）在分支外**。无模型探针一旦横跳即 NameError；训练生产因永远带模型不踩此坑——但使所有探针的 err=no 结论不可信。
- **修复**: L1196 改为直接取同源 `_p8 = obs[3211:3219]`（8 方向可通行性，与模型分支同一 obs 切片），带模型路径行为不变。py_compile + 清 `__pycache__`（ep 子进程逐局加载，未停训即生效）。
- **教训**: 分支内局部变量被分支外公共路径引用是典型潜伏 bug；探针（无模型）与生产（带模型）是两套执行路径，探针结论前先确认 traj 无 error 字段。
- **关联**: #226（由 King 完整局暴露）/ `ep_runner_one.py` L435/L519/L1196 / `train_wsl2_ppo_v2.py` L240（error 局静默过滤）。

#### #228 08-17 removeQuery 补丁的多玩家计数欠减：PvP 战斗结算永久挂起 → currentBattles 残留 → simturns 占城全拒 + 判负检查永不跑 (2026-09-14) — ✅ 已修复（H3 窗口当晚闭环）
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

#### #229 system unit 迁移后旧 `systemctl --user` 静默给出错误答案：is-active 报 not found/inactive 差点误判训练死亡 + 旧 transient 脚本双开风险 (2026-09-15) — ✅ 已修正（口径统一+脚本封禁）
- **现象**: 09-15 凌晨按旧项目规则执行 `systemctl --user is-active homm3-train-v5` 返回 inactive，`systemctl --user status` 报 "Unit could not be found"，初判训练已挂；实查 `pgrep -af train_wsl2` 训练在跑（PID 160），`cat /proc/160/cgroup` = `0::/system.slice/homm3-train-v5.service`，`systemctl is-active homm3-train-v5`（system 级）= active、MainPID=160、日志 mtime 正常推进。
- **根因**: 0911 晚 #201 窗口已把托管从 user 级 transient（`systemd-run --user --collect`）重构为 system 级 enabled 持久 unit（`/etc/systemd/system/homm3-train-v5.service`，User=administrator）；WSL 无用户 manager 持久单元（#195 已实证 `~/.config/systemd/user` 与 `/etc/systemd/user` 均不存在）。但 project_rules、活文档与 6 个运维脚本仍写旧 `--user` 命令——架构迁移后旧命令不提示"架构变了"，而是静默输出 inactive/not found，诱导"训练挂了"的错误结论。
- **双开风险（更危险）**: 旧脚本 `py/restart_train_v5.sh`、`py/_restart_v5.sh` 仍可执行且会 `systemd-run --user` 重建 user twin；`py/restart_train_v5_sys.sh` L29 专门有一行 `systemctl --user stop ... 2>/dev/null || true` 清 twin，证明双开实例真实发生过。两个训练进程并发 = checkpoint 互踩 + VCMI 资源争用。
- **处置（09-15，纯文档/脚本，零运行时触碰）**: ①project_rules 硬约束+常用命令统一为 `wsl -u root systemctl stop|start homm3-train-v5`（实测 wsl -u root 免密 uid=0；普通用户 stop 需 sudo 密码）并明示禁用 --user；②当前任务清单关机流程、WSL知识库 09-11 部署段、scripts/rebuild_tasks.py 同步；③check_train_log/monitor_recruit/check_mt200/verify_v5_restart/_status_check/probe docstring 去 --user；④两个旧 restart 脚本头部加废弃说明 + `echo FATAL >&2; exit 100` 硬封禁（旧命令保留在 exit 之后仅作历史）；⑤历史踩坑条目（#168/#195/#201 等）与一次性侦查脚本不改，保留当时事实。
- **教训**: ①"命令能执行且返回了值"不代表"命令问的对象还存在"——运维口径变更后，旧命令的静默错误答案比命令不存在更危险；判活坚持 #201 三件套（PID etime + 日志 mtime + cgroup/MainPID），is-active 只作辅助；②架构迁移类变更必须同步"规则文件+活文档+可执行脚本"三层，只改知识库不够（规则文件是 agent 每次必读入口）；③废弃脚本不能只靠注释，必须让执行本身失败（exit 非 0），防止后来者照抄运行。
- **关联**: #168（is-active 对消失 unit 也输出 inactive）/ #195（transient 停止即消失）/ #201（容器空闲关停 → system 级 enabled unit 重构，本条是其口径漂移余波）/ `.trae/rules/project_rules.md` L18 / `py/restart_train_v5_sys.sh`。

#### #230 P8-E 人机混局探针 3 客户端连 Twins 触发 server NEW_GAME 崩溃 (09-15, P8-E 实跑踩) — ✅ 已收敛为 2 客户端

- **状态**: ✅ 已修（收敛为 2 客户端拓扑，P8-E PASS）
- **现象**: P8-E 初版 4 客户端（Python host + 人类 GUI×2 + 外挂 AI）→ server "Picking random factions for players" → "Disaster happened" 崩溃。二版 3 客户端（Python host + 人类 GUI + 外挂 AI）→ 同样崩溃。`14LobbyStartGame` 广播成功但 server 随后在 NEW_GAME 初始化阶段崩溃。
- **根因**: Twins.h3m 仅 2 玩家 slot。VCMI server 的 NEW_GAME 初始化在 "Picking random factions for players" 阶段为每个 join lobby 的客户端分配玩家 slot，超出地图 max players（2）时触发 "Disaster happened"。3 客户端 = 3 个 join lobby 的客户端 → 超出 2 slot → 崩。
- **收敛**: 改为 2 客户端拓扑（P8-B 范式）：Python host + 外挂 AI（AI 是第 2 个 join 的客户端，占 Twins 第 2 slot）。人类 GUI 不 join lobby（不带 `--testmap`/`--serverport`，避免 `EntryPoint.cpp` L379 默认 `onlyai=true` 导致人类 GUI 也 join lobby），仅验证"人类 GUI 进程与 AI 同机共存"。判定 `srv_log_cc()>=3` → `>=2`。
- **复现**: `python py/p8e_human_mix_probe.py`（已修，PASS）；旧症状 = server log 末尾 "Player 0/1 is controlled by human" + "Picking random factions" → "Disaster happened" + crashinfo.dmp。
- **关联**: #202（ChangeHost 时序，本条是其 2 客户端拓扑的前置约束）/ Twins.h3m 仅 2 玩家 slot / `EntryPoint.cpp` L379 `VCMI_TESTMAP_ONLYAI` 默认 true / `py/p8e_human_mix_probe.py` / 知识库 P8-E 人机混局章。

#### #231 capture proxy 空拍误报 218/218：差集判定没吃"本拍观测无效"分支，#209 只堵 duel 留 169 个非 duel 假 +100 (2026-09-15) — ✅ 已修复（空拍跳过+双拍确认）

- **现象**: WIN-1 判据①"1v3 TOWN_CAPTURE 非零"长期显示达标且触发即 `blue_hero_killed=[1,2,3]` 三蓝全灭；但动作序列重建显示触发当步红英雄意图位置仅 (34,18)，蓝英雄/蓝城全在 x≥66，零接触；同图 4 个 200 步截断局动作逐位相同（确定性局），"成功局"与失败局前 75 拍动作完全一致。`battle_quality_events.log` 严格配对（同图同步）：**全历史 218 次 TOWN_CAPTURE 100% 紧跟一条 `[HEROSEG_EMPTY] slots=0/0×8`，真实 BHERO_KILL 全历史仅 9 次（且 live_slots=0 同样可疑），现地图池时代 0 次**。
- **根因**: `ep_runner_one.py` heroes 段观测存在瞬态空拍（8 槽全 id=0 = 共享内存未填充帧，战斗/visit 窗口，412 次样本）。代码 L926 注释自己写明"空拍=观测无效，**跳过差集**与 prev 更新防误报"，但实现上：① L935 空拍分支只 print 诊断；② L951 proxy 判定无条件执行 `prev - _bnow`，空拍时 `_bnow=空集` → 差集恒等于 prev 全量 → 必发 +100；③ L967 的 prev 不更新保护管不到同拍的 proxy 判定。09-13 #209 已用"duel 49/49 全误报"实锤同一机制，但修复方式 = 仅排除 `_duel.vmap` 后缀，非 duel 的 169 次继续裸奔，假 +100 长期污染价值学习。
- **次生误诊**: 当日凌晨 analyze_trunc200.py ⑤专项把 72_02 截断归因为"地形堵点 (40,5)/蓝城贴东缘"，建议改图挪城。解包 `T06_adventure_72X72_02.vmap` 证伪：surface_terrain = gr24_ ×5184 全草地（零河零山零路），(40,5) 草地、蓝城 (69,2) BFS=64 完全可达；`block=(40,5)` 是 TOWNSTALL 引导把"BFS 建议但引擎拒绝的首步格"拉黑的诊断输出（动态障碍语义），被误读成静态墙。截断本质 = 确定性策略东缘空转（前 51 步打同矿/同守卫后一路东向，东缘空输出 ~90 步）。
- **处置（09-15，695099 停启窗）**: ep_runner_one.py L952-979 重写为状态机：① proxy 判定条件加 `_bnow`（空拍帧整体跳过）；② 差集先进 `_kill_pending` 挂账，下一**非空**拍仍缺席才发 +100（日志带 `confirmed 2 frames`）；空拍冻结挂账、id 回来撤账、仍缺滚动再挂一拍；duel 排除保持。真击杀仅晚 1 拍发奖不漏。七序列桩测 ALL_PASS（空拍误报/多空拍/瞬态恢复/duel 0 奖；真杀延迟确认/双杀一次/滚动确认 +100）；py_compile + 清 `__pycache__`；resume 后首批局零 Traceback 零误报。
- **教训**: ① **"跳过差集"的承诺必须落在同一个判定上**——防护写在 prev 更新处（L967）、奖励判定（L951）没吃，等于没防；同一份观测有效性（空拍标志）要同时门控所有下游消费者；② 局部修复（只排 duel）要回问"其他调用方是否同病"，#209 的 49/49 证据已证明机制是普遍的，后缀排除只是压症状；③ 日志分析不能只靠动作码+单条诊断推断空间事实，地形/可达性必须解包 vmap 实证（`zipfile`+BFS 五分钟事），否则会基于误读提出改图这种高成本动作；④ 事件配对验证用严格键（map+step，注意 capture 行是 `at step N` 不是 `step=N`，正则不一致会得出 strict=0 的假反证，需当场解释矛盾）。
- **关联**: #209（duel 49/49 误报，只修后缀）/ #213（C 方案 proxy 上线）/ 空拍根因候选（C++ 填充竞态，L926 注释）/ `ep_runner_one.py` L923-979 / `battle_quality_events.log` / 任务清单 WIN-1 区（判据①重新攒窗）。

#### #232 P10 经济期远目标碾压：蓝英雄 plen=64 经济期无衰减 → 200 步跑满 r=-11.3 (2026-09-15, P10 scorer 灰度启用首日) — ✅ 已修（V×0.2 衰减）

- **现象**: P10 `--target_chain scorer` 灰度启用后，T05_adventure_36X36_01 step 28 蓝英雄候选 `plen=64 F=-0.33 score=168.7` 碾压 runner_up（近距离取兵）89.5，经济期锁死 64 步远目标，200 步跑满终局 `r=-11.3`（负收益）。
- **根因**: `w_win*delta_cap*V`（1.5×100=150）在打分公式里对蓝英雄/蓝城无条件放大，`w_dist*g`（0.5×64=32）远小于 150 → 经济期开局远目标被锁定。`step_budget` 保守估算（`max_turns=10`，每回合约 20 步 → `step_budget=10*20-28=172`），远候选 plen=64 < 86（budget×0.5）不触发步预算惩罚，远目标持续霸占打分头部。
- **修复**: `py/target_scorer.py` 打分循环内（`score_candidates`），经济期 + `g>50` 的蓝英雄/蓝城候选 `V × 0.2`（100→20 / 80→16），让近距离取兵/资源堆正常胜出。同步修正 `g` 定义顺序（先 BFS 算 `g`，再对 V 做衰减）。
- **验证**: King_of_Pain_h3m step 28 选 `own_town`（plen=1 近距离取兵），守卫战斗 +100，115 步正常终局，`r=119.3` 正收益。经济期远目标衰减修复后，经济期正常节奏恢复。
- **教训**: ① `w_win`（胜利贡献权重）对远目标是无条件乘法项，必须配合 `g`（实际路径长度）做经济期衰减，否则远目标开局即锁死；② 打分公式里所有乘法项的"适用窗口"要显式声明，经济期/capture 期对远目标的贡献系数应分阶段；③ 灰度首日首局即暴露 bug = `[SCORE]` 诊断日志的价值（没有这条日志，64 步远目标锁定会被误判为"模型正常学远目标"）。
- **关联**: P10 方案 §3 / `py/target_scorer.py` `score_candidates` L250-271（V 衰减段）/ `ep_runner_one.py` L675-717（scorer 分支）/ `train_wsl2_ppo_v2.py` L196（`--target_chain scorer` 透传）。

#### #233 P10 候选池坐标变量混用：`tx,ty` 未定义 NameError（蓝城/取兵城候选 BFS 过滤段）(2026-09-15, P10 离线测试发现) — ✅ 已修（`c["pos"]` 取坐标）

- **现象**: `py/test_target_scorer.py` 测试 4（硬约束过滤）运行时，`score_candidates` 内蓝城/取兵城候选的 BFS 过滤段抛 `NameError: name 'tx' is not defined`；只有蓝英雄/资源堆候选（走 `tx, ty = c["pos"]` 赋值路径）正常。
- **根因**: `score_candidates` 的打分循环（`for c in cands:`）里，蓝城/取兵城候选的 BFS 过滤段直接引用了 `tx, ty`，但 `tx, ty` 只在循环前针对"当前主角位"赋值，**蓝城/取兵城候选的坐标存在 `c["pos"]`（= `btx, bty`）**，未从候选 dict 里取出来就用了自由变量。
- **修复**: 在打分循环内（`for c in cands:` 之后第一行），统一从 `c["pos"]` 取坐标：`_cx, _cy, _cz = c["pos"]`，将蓝城/取兵城候选的 BFS 过滤段改为 `bfs_full_dir(mapname, hx, hy, _cx, _cy, ...)`；蓝英雄/资源堆候选同理统一用 `_cx, _cy`。
- **教训**: 候选池多类型并存时，坐标变量名必须在循环体内统一从 `c["pos"]` 解包，**不允许自由变量跨候选类型混用**；离线测试必须覆盖所有 5 类候选（蓝英雄/蓝城/取兵城/资源堆/守卫），仅测蓝英雄+资源堆会漏掉蓝城/取兵城的坐标路径。
- **关联**: `py/target_scorer.py` `score_candidates` 打分循环 / `py/test_target_scorer.py` 测试 4（硬约束过滤）。

#### #234 训练脚本透传 `--target_chain scorer` + `[SCORE]` 进主日志 (2026-09-15, P10 灰度启用) — ✅ 已上线

- **现象**: P10 scorer 分支在 `ep_runner_one.py` 已就位，但训练脚本 `train_wsl2_ppo_v2.py` 未透传 `--target_chain scorer`，实际训练进程仍走 legacy 路径；且 `[SCORE]` 诊断日志未进主日志白名单，训练日志里 grep 不到打分详情。
- **根因**: 灰度启用需要两处联动：① `train_wsl2_ppo_v2.py` 在构建 ep_runner 命令行时透传 `--target_chain scorer`（或按需透传 `--target_chain legacy` 回退）；② `[SCORE]` 加入 `train_wsl2_ppo_v2.py` 主日志转储词表（`highlights` 列表），否则 ep_runner 子进程的 `[SCORE]` print 不进 `train_loop.log`，无法从主日志侧 grep 诊断。
- **处置（09-15）**: `train_wsl2_ppo_v2.py` L196 新增 `cmd.extend(["--target_chain", "scorer"])`（P10 灰度开关，默认 legacy 零行为变化，scorer 启用 `target_scorer.py` 统一打分器）；L222 `highlights` 列表补 `"[SCORE]"`。py_compile 通过，停启训练（`wsl -u root systemctl stop/start homm3-train-v5`），清 `__pycache__`，首局验证修复生效（King_of_Pain step 28 选 own_town 而非远蓝英雄，r=119.3 正收益）。
- **教训**: 灰度开关启用是"训练脚本 + ep_runner 参数 + 主日志词表"三层联动，改任何一层都要检查另外两层是否同步；`[SCORE]` 这类新日志标签必须先加进主日志白名单，否则子进程日志对主日志不可见，灰度观察期形同虚设。
- **关联**: #232（经济期远目标碾压，本条灰度首日暴露）/ #233（坐标变量混用，离线测试先暴露）/ `train_wsl2_ppo_v2.py` L196/L222 / `ep_runner_one.py` L133-144（argparse 7 参数）/ `py/target_scorer.py`。

#### #235 合批部署前未核查触发前置：S2 前置断链（BHERO_KILL 全历史 0 次）差点把 S2 与 D3/C2 L0 混进同一停启批次 (2026-09-15, WIN-1 五判据聚合核查发现) — ⚠️ 方法论坑

- **现象**: 原计划"D3 熵 bonus + C2 L0 崩溃插桩 + T7.5 S2 奖励系数"三项合批，同一 `train_wsl2_ppo_v2.py` + `ep_runner_one.py` 停启批次一次部署。三项代码都已实施 + py_compile 过 + `__pycache__` 已清，只差一次 `systemctl stop/start`。合批前用 `py/win1_five_criteria_snapshot.sh` 聚合 WIN-1 五判据，发现判据① TOWN_CAPTURE/BHERO_KILL 非零 **BHERO_KILL 全历史 0 次**（HEROSEG_EMPTY=0 空拍过滤已生效，无新误报）——S2 触发前置（WIN-1 达标）不满足。若把 S2 与 D3/C2 L0 混批，会让激励轴变化与 capture 修复验证混入同一观察窗，WIN-1 判据① 无法归因。
- **根因**: 合批部署只核对了"改动已落盘 + py_compile 过 + 与已有停启批次同批"三个技术前置，未核对每项改动的**触发前置**（是否满足启动条件）。D3/C2 L0 无触发前置（属基建类，可独立部署），S2 有明确触发前置（WIN-1 达标 + capture proxy 稳定 ≥2 窗）。合批判断把"技术上可合批"误当作"业务上该合批"。
- **处置（09-15, 用户拍板）**: ①`ep_runner_one.py` 5 处 SearchReplace 回退 S2 数值改动（RECRUIT +0.25→+0.5 / BUILD_2 +0.375→+0.75 / 兵力系数 0.03→0.02），与 HEAD 完全一致；②保留 3 处注释改动（L1151 陈旧 `× 0.01`→`× 0.02` 修正 + L1185-1186/L1204 两处 S2 回退说明注释，为后续触发时提供上下文）；③D3 + C2 L0 独立合批部署；④WIN-1 判据① BHERO_KILL 全历史 0 次作为前置断链事实写进知识库与任务清单，S2 延后。
- **教训**: ①**合批判断必须双维**：技术前置（同批可行性）+ 业务前置（每项触发条件是否满足），缺一即漏；②"预期短期 capture=0"不等于"前置已满足"——BHERO_KILL 全历史 0 次是结构性前置断链（真 capture 从未发生），非"样本量不够"；③判据聚合脚本（如 `win1_five_criteria_snapshot.sh`）应作为每次合批部署前的**强制检查项**，而非事后追查工具；④回退代码时保留有价值的注释修正（如陈旧注释修正）+ 触发延后说明，为后续重新实施提供上下文。
- **关联**: #204（0 命中三义性：埋点未生效/观测无效/真无行为，本条判据① BHERO_KILL=0 属"真无行为"）/ #210（HERO_DEATH 0 根因）/ #228（败北信号根修）/ #231（capture proxy 空拍误报修复，让判据①能真实反映"真 capture 未发生"）/ WIN-1 五判据原文 / `py/win1_five_criteria_snapshot.sh` / `py/win1_window_split.sh` / `ep_runner_one.py` L1148-1210 / 知识库 S2 回退决策章。

#### #236 D3 entc 行（L534 per-epoch）需攒满 1 个 BATCH 才触发，部署后前 30min 看不到 entc 属正常现象 (2026-09-15, D3 部署验证发现) — ⚠️ 观察口径坑

- **现象**: D3 熵 bonus 09-15 05:34 部署后，连续检查 3 次（05:38/05:53/06:50）`grep entc train_loop.log` 均 0 命中，一度怀疑 L534 print 语句未生效或 `__pycache__` 未清。实际上 entc 字段在 ep=14 行（`step698978`，约 05:34+55min 后）才首次出现。
- **根因**: `train_wsl2_ppo_v2.py` 有两类 step 日志行：L435（per-episode，每局打一行，格式 `stepX avg_r=Y ep=N time=Zs`，**无 entc/vloss/loss/kl 字段**）和 L534（per-epoch，每攒满 1 个 BATCH=2048 条样本才打一行，格式含 `vloss/loss/kl/klc/entc/ent`）。T6.4 大图每局 ~130 step，BATCH 需 ~10-14 局 / ~55min。部署后前 30min 仅 ep=1-5（~5 局 / ~650 step），远未攒满 1 个 BATCH，L534 行尚未触发，故 grep entc=0 是**数据未到**而非**代码未生效**。
- **教训**: ①部署新字段后验证需等 1 个完整 BATCH 周期（~55min），不可用前 30min 的 grep 0 命中下结论；②区分 per-episode 行（L435，高频）与 per-epoch 行（L534，低频）——前者每局打，后者每 BATCH 打；③`__pycache__` 已清 + `py_compile` 过 + 源文件 grep 到字段 ≠ 运行中进程已加载新代码，最终以日志行为准。
- **关联**: #235（合批双维前置核查）/ `train_wsl2_ppo_v2.py` L435/L534 / 总任务.md「09-15 部署后首份观察记录」。

#### #237 T06 duel act_loop_penalty + 横跳 8 步窗门控随 move_to_force=200 全程失效 + `r = -0.5` 赋值覆盖同帧正 reward (2026-09-15, T06 duel 轨迹分析发现) — ✅ 已修复

- **状态**: ✅ 已修复（ep_runner_one.py 3 处 + train_wsl2_ppo_v2.py 1 处，`wsl -u root systemctl stop/start` 重启生效）
- **背景**: T06 duel（72X72_02_duel / 108X108_02_duel）200 步截断局 r=-410~-446，act=2（SW）方向卡死 130+ 次，无任何 GUARD/CAPTURE 正向触发。根因分析发现三个机制耦合。
- **坑① act_loop_penalty 门控永假（主根因）**: `ep_runner_one.py` L1226 `if args.act_loop_penalty > 0 and traj["steps"] >= args.move_to_force:`。T06 被 L150 无条件覆盖 `move_to_force=200`，而 `max_turns=200`，最后一帧 step=199，`traj["steps"] >= 200` 全程 False → 动作级循环惩罚（连续 4 步同动作 -1.0）在 T06 **全程被跳过**。小图（T03/T05）`move_to_force=60` 无此问题。
- **坑② 横跳 8 步窗门控同样失效**: L1269 `if len(traj["obs"]) >= 8 and traj["steps"] >= args.move_to_force:` 同一门控，T06 全程 False → 8 步窗 ≤2 格交替 -3.0 + 强制随机方向 均不生效。
- **坑③ `r = -0.5` 赋值 bug（放大器）**: L1257 `if prev_pos == cur_pos: r = -0.5` 是**赋值**而非累加。英雄被墙/边界挡时 r 被直接重置为 -0.5，同帧累积的 NK2 探索奖励、经济 RECRUIT +12/+0.5、BUILD +15/+0.75 全部丢失。T06 duel 200 步中 ~130 步 act=2 被挡 → 每次赋值覆盖前帧奖励，-440 的主要来源之一。
- **正确口径 / 修复方案**:
  1. 新增 `--act_loop_from_step` 参数（默认 0 = 跟随 move_to_force，保持非 T06 图行为不变）；T06 专属传 60 → step≥60 后循环惩罚生效
  2. 横跳 8 步窗门控同步改用 `act_loop_from_step`（与 act_loop 同一解耦逻辑）
  3. `r = -0.5` 改 `r += -0.5`（累加，保留同帧其他正 reward）
- **预期效果**: T06 duel r 从 -440 回升至 -200~-300；act=2 循环占比下降；非 T06 图行为不变（`act_loop_from_step=0` 时回退到 `move_to_force`）。
- **复现/验证**: `grep -n "act_loop_from_step" ep_runner_one.py train_wsl2_ppo_v2.py` 确认 3 处；`grep "T06.*steps=200" train_loop.log` 观察新 r 值是否回升。
- **关联**: #232（P10 经济期远目标无衰减）/ #228（败北信号根修）/ `ep_runner_one.py` L110/L150/L1226/L1257/L1269 / `train_wsl2_ppo_v2.py` L184 / 当前任务清单 WIN-1 ⑤ / P10-target。

#### #238 P10 V×0.2 衰减对 108_02_duel 无效：蓝英雄 plen=201 > 200 步预算，经济+空转确定性无 capture (09-16, 日志分析发现) — ⚠️ 已定性（结构性不可达，按 WIN-3 ① 走 72X72_02_duel 单图轴）

- **状态**: ⚠️ 已定性（108_02_duel 结构性不可达，按 WIN-3 ① 切 72X72_02_duel 单图轴；108_02_duel 暂移出 MAPS 或提 250 步）
- **现象**: 09-16 重启段 duel 图（72_01_duel / 72_02_duel / 108_02_duel）持续 200 步截断，r 在 -1261 ~ -1283（108_02 最严重）。`[SCORE]` 行 `pick=(102,102) type=blue_hero score=110.9 plen=201 V=100 F=-0.32 runner_up=92.3`，模型每帧持续 `+10/+40/+120` 招兵 + 经济（act=16-21）+ 大量 END_TURN（act=2），200 步走完仍未到 capture 点。
- **根因**: 蓝英雄 (102,102) BFS 距离 201 步 > 200 步预算（`max_turns=200`），属**结构性不可达**——与 WIN-3 评估「108_02_duel 红 hero→蓝镇 曼哈顿 200 步 = 100% 截断率」结论一致。P10 V×0.2 衰减（#232）把 score 从 V=100 压到 110.9（经济期远目标 F=-0.32），但 **衰减只降 score 不改 plen 不可达性**，模型仍被 P10 scorer 选中 blue_hero 目标（runner_up 接近头名），只会"经济+东进"确定性空转。
- **72_01/72_02 duel 同因**: 蓝英雄 plen=68/129，经济期衰减同样未让 capture 真正发生（#232 灰度首日 King r=119.3 正收益，但 duel 图 r 仍 -1200+）。
- **正确口径 / 处理**:
  1. **P10 V×0.2 衰减对 duel 图无效**：衰减只是降 score 排序，不解决 plen > 步预算 的结构性不可达。duel 图需按 WIN-3 ① 切 72X72_02_duel 单图轴（距离 128 步 = 64%，200 步内可达）。
  2. **108_02_duel 二选一**（不混做）：① 提 250 步（全局影响所有图，T05 小图节奏变慢 ~25%）；② 挪蓝镇到 (98,98)（`py/win3_move_town_108_02_duel.py` 09-15 备料，距离 200→174 = 69%）。当前不动，待 WIN-1 达标后走 WIN-3 难度轴。
  3. **WIN-1 判据⑤ 200 步截断率**：本段 duel 图 200 步截断 ≥30%（ep16/ep20/ep28 全 duel），高于⑤ 20% 红线，但全属 B 类（守卫胜+占矿后未 capture），按 09-15 拍板口径不阻塞 WIN-1 聚合。
- **复现/验证**: `grep "108X108_02_duel" train_loop.log | grep "steps=200"` 观察截断率；`grep "pick=.*blue_hero.*plen=20" train_loop.log` 看 P10 scorer 是否选中不可达目标。
- **关联**: #232（P10 V×0.2 衰减）/ #237（T06 duel act_loop 门控失效）/ WIN-3 ① 72X72_02_duel 单图轴 / 知识库「WIN-3 难度轴纯评估」章 / `py/target_scorer.py`。
- **09-16 处置**: ✅ 提 250 步方案已部署——`STEPS_PER_EP 200→250` + T06 `move_to_force=250` + 清 `__pycache__` + stop/start（PID 25924），新 banner 行 96902 `1000eps×250steps` 已生效；T05 小图节奏变慢 ~25% 需后续观察。**#239 副作用已修复**：duel 图 r 从 -1665 回升至 -123~-183（改善 89-93%），"结构性不可达"定性作废（108_02 plen=201<250 已可达）。

#### #239 T06 duel move_to_force 全覆盖 250 步副作用：act=2 循环惩罚 190 步累积 r≈-1665 (09-16) — ✅ 已修复（P10-target-2b）

- **状态**: ✅ 已修复（`ep_runner_one.py` T06 覆盖块区分 duel/非 duel，`systemctl stop/start` 重启生效）
- **背景**: WIN-3② 250 步方案部署后，duel 图（72X72_02_duel / 72X72_01_duel / 108X108_02_duel）250 步截断局 r 从旧 200 步的 -1280~-1289 恶化至 **-1665~-1671**，恶化幅度 ~1245。
- **现象**: 250 步截断局 act 序列 = 前 50 步经济动作（2 为主，穿插 16-21），后 200 步全 `2`（MOVE_DOWN 经济空转），与 #238 行为模式一致但惩罚累积时间更长。
- **根因分解**:
  - **主根因**: T06 覆盖块 `move_to_force=250`（与 `max_turns=250` 同步）→ act_loop 门控 `traj["steps"] >= act_loop_from_step(60)` → step 60~249 共 190 步 act=2 循环惩罚 -1.0/步 全生效
  - **旧 200 步行为**: `move_to_force=200=max_turns` → act_loop 门控永假 → 0 步惩罚生效 → r 仅 -0.1 步罚 × 200 + NK2 ≈ -1280
  - **新 250 步行为**: `move_to_force=250` 与 `act_loop_from_step=60` 解耦 → 190 步 × -1.1（步罚+循环罚）≈ -209，加 NK2 威胁漂移 + 横跳/往返惩罚 ≈ -1456，**总计 ≈ -1665**
  - **模型行为特征**: duel 图蓝英雄 plen=129/201 < 250 理论可达，但 act=2（MOVE_DOWN）循环占主导而非 24（MOVE_TO），模型未学会用 P10 引导路径，前 50 步经济动作 + 后 200 步 act=2 死循环
- **修复方案**（P10-target-2b）:
  - `ep_runner_one.py` L153 T06 覆盖块改为：
    ```python
    if args.mapname.startswith('T06'):
        if 'duel' in args.mapname:
            args.move_to_force = 60   # duel: P10 引导前 60 步走 24，避免 190 步循环惩罚
        else:
            args.move_to_force = 250   # 非 duel 1v3: 蓝城全程引导
        args.guard_done_steps = 0
    ```
  - duel 图 `move_to_force=60` 与 `act_loop_from_step=60` 同步：P10 SCORE 引导前 60 步内驱动 24 MOVE_TO，step 60 后模型已脱离 act=2 循环
  - 非 duel T06（1v3）维持 `move_to_force=250`，蓝城引导需全程
  - `train_wsl2_ppo_v2.py` L184 注释同步更新
- **验证结果**（重启后 5 局 duel）:
  | 局 | 图 | steps | r | 对比 |
  |----|----|-------|---|------|
  | 1 | 72X72_02_duel | 74 | -183 | -1665→-183，改善 89% |
  | 2 | 72X72_02_duel | 158 | -123 | 改善 93% |
  | 3 | 108X108_02_duel | 139 | -137 | 改善 92% |
  | 4 | 72X72_01_duel | 62 | -174 | 改善 89% |
  | 5 | 72X72_02_duel | 111 | -165 | 改善 90% |
  - steps 不再卡 250 截断，act 序列从全 `2` 死循环变为 `3,4,5,6,7,18,19,20,21` 混合探索
- **#238 定性更新**: "108_02_duel 蓝英雄 plen=201 > 200 步预算结构性不可达"已作废——250 步后 plen=201 < 250 已可达，duel 图 r 极差问题彻底解除
- **关联**: #237（T06 duel act_loop 门控解耦）/ #238（108_02_duel 结构性不可达）/ #232（P10 V×0.2 衰减）/ `ep_runner_one.py` L153 / `train_wsl2_ppo_v2.py` L184 / 当前任务清单 P10-target-2b

#### #240 独立 C++ 工具缺 `Global.h` → 宏/类型未声明编译失败（P10-B1 h3m2vmap 骨架首编踩）(09-01) — ✅ 已修

- **状态**: ✅ 已解决（main.cpp 首行 include `Global.h`）
- **现象**: `tools/h3m2vmap/main.cpp` 首编报 `GameConstants 未声明 / LIBRARY 未声明 / GameLibrary does not name a type`。
- **根因**: 独立迷你工程不走 serverapp 的 include 链，`VCMI_LIB_NAMESPACE_*` 等宏定义在源码树根 `Global.h`，lib 头依赖该宏展开；单独引 lib 头时宏未定义，类型解析全炸。
- **修复**: main.cpp 在引任何 lib 头之前 `#include "Global.h"`；CMake `target_include_directories` 含 `${VCMI_SOURCE_DIR}` 与 `${VCMI_SOURCE_DIR}/include`。
- **教训**: 凡脱离 CMake 顶层工程树独立链接 `rel/bin/libvcmi.so` 的工具，必须直接引根头，不能赌 serverapp 的传递 include。

#### #241 H3M 写回字节错位三连：AB+ main_town 2B / SOD hero artifact 19 槽 / resource msg=0 分支 1B（vmap2h3m 首版 strict 对账全抓出）(09-01) — ✅ 已修

- **状态**: ✅ 已解决（`py/vmap2h3m.py` 三处载荷修复，strict 读回 skipped=0）
- **现象**: 首版 vmap→H3M(SOD) 产物经 `h3m_tool.parse_objects(tolerant=False)` strict 对账在 3 处错位：header @62 main_town 段偏移、对象流 skipped>0、resource 对象后 4B 漂移。
- **根因分解**:
  - **main_town**: AB+（SOD 0x1c 属 AB+ 谱系）main_town 段比 ROE 多 2B 头字节，漏写 → 其后全错位
  - **hero artifact**: SOD 谱系 19 槽 vs ROE/AB 18 槽（`h3m_tool._features` 中 `artifactSlotsCount=18 if ver in (ROE,AB) else 19`），写 18 槽少 2B
  - **resource**: `readMessageAndGuards` 的 skip4 属于 `msg=1` 分支内部；`hasMessage=0` 时只写 1B 标志 + u32(amount) + 4B，不应再 skip
- **修复**: `w.u8(1); w.u8(0); w.u8(0)` 补 main_town 2B；artifact 改 `b'\xFF\xFF'*19` + u16 backpack=0；resource 分支 `w.u8(0); w.u32(amount); w.raw(b'\x00'*4)`。
- **教训**: H3M 对象载荷随版本谱系（ROE/AB/SOD）变体，写回必须以目标版本 features 表为准；strict 读回是发现偏移问题的唯一可靠手段（对照 trace 逐对象定位 GAP，`py/diag_v2h_strict.py` / `py/diag_v2h_trace.py`）。

#### #242 `CMapService::loadMap` buffer 版：cb=nullptr 可用但 modName 必须传 `"map"`，传 `""` 走 ModsStorage 异常 core dump (09-01, h3m2vmap --check-h3m 验证踩) — ✅ 定论

- **状态**: ✅ 已定论（`tools/h3m2vmap/main.cpp --check-h3m` 实跑 `ENGINE LOAD OK`）
- **现象**: 独立工具调 `service.loadMap(data, size, path, "", "CP1252", nullptr)` 时 SIGABRT（core dump），官方原图同样崩，一度误判 cb 为根因。
- **根因**: gdb 栈定位 = `CModLoaderH3M::readLocalizedString` → `CModHandler::getModLanguage("")` → `ModsStorage` 抛异常（`CMapHeader::mapRegisterLocalizedString` 对 modName 特判 `"map"`，`""` 无特判落入 ModsStorage 查找抛异常）。
- **修复**: modName 传 `"map"`，cb 保持 nullptr（V1 定论：buffer 版 loadMap 不需要 EditorCallback）。
- **教训**: 引擎局部字符串注册对 modName 有特判白名单，独立工具调用时传 `"map"` 而非空串；异常崩栈先 gdb 定位符号再下结论，勿误归因（见 #204 三义性教训）。

#### #243 独立迷你 CMake 工程：空 build/ 壳 + 无 ccache 全树重建代价高，改只读链接 rel 产物 (09-01, B1 构建决策) — ✅ 已落地

- **状态**: ✅ 已解决（`tools/h3m2vmap/CMakeLists.txt` 独立工程）
- **现象**: vcmi 构建树 `build/` 为空壳、ccache 未装，改 1 行 C++ 全树重建不可接受。
- **方案**: 独立工程 `add_executable` + `target_link_libraries(${VCMI_LIB_DIR}/libvcmi.so)`，`set_target_properties BUILD_RPATH/INSTALL_RPATH ${VCMI_LIB_DIR}` 只读链 `rel/bin/libvcmi.so`，零 lib 重编、零 rel 写入；单编译单元秒级出二进制。
- **教训**: 工具类 C++（转换器/校验器）不要挂主构建树，独立工程 + 只读 RPATH 链 rel 产物；.so 升级后 RPATH 不变免改工程（见踩坑 #4 RPATH 陷阱的正面用法）。

#### #244 双树纪律：Windows 侧 include Edit 丢失 → 同步后 WSL 编译仍报未声明 (09-01, h3m2vmap --check-h3m 编译踩) — ✅ 已修

- **状态**: ✅ 已解决（重新 Edit 补 include + 双树 md5sum 核对后编译通过）
- **现象**: Windows 侧 `tools/h3m2vmap/main.cpp` 新增 `CMapService` 相关 include 的 Edit 未真正落盘（md5 显示 cp 到 WSL 的内容不含新 include），WSL 编译报 `'CMapService' was not declared`。
- **教训**: 双树（Windows 副本 → WSL vcmi-native）同步后，编译前 `md5sum` 双侧核对，不假设 Edit 一定写成功；WSL 侧 grep 源码确认再编译（与 project_rules「事实核查原则」一致）。

#### #245 PowerShell 内联复杂命令反复炸 → 统一写 .py/.sh 脚本文件经 wsl bash 执行 (09-01, 本会话工具链开发全程) — 🔄 绕过中

- **状态**: 🔄 约定已固化（本会话全部诊断/构建/验证脚本落地 `py/run_v2h_verify.sh` / `py/run_check_h3m2.sh` / `py/run_gdb_check.sh` 等）
- **现象**: PowerShell 内联 for/数组/嵌套引号在 `wsl bash -c` 传递时引号转义反复炸（`&`/`{`/`(` 被 PowerShell 先行解析）。
- **处理**: 凡多行 bash/复杂命令一律写成 `py/*.sh`（或 `.py`）脚本文件，再 `wsl bash py/xxx.sh` 执行；单条简单命令（grep/systemctl）可内联。
- **教训**: 与 #75（python 补丁脚本残留拼接）、#22（python3 -c 引号嵌套）同源——Windows↔WSL 边界上的引号/换行转义是高频坑，脚本文件是稳态解法。

#### #246 ep_runner 图名断言：直通产物 vmap 命名须含 `s1/mini/adventure/h3m` 关键词，否则 strategic_env 加载即炸 (09-16, B2 冒烟首跑踩) — ✅ 已固化

- **状态**: ✅ 已固化（B2 冒烟产物改名 `B2_adventure_knee_deep.vmap`，两处副本同步；后续直通转换产物统一带 `adventure_` 前缀）
- **现象**: `ep_runner_one.py 6 /tmp/b2_knee_traj.json B2_KneeDeep.vmap` 首跑即断言失败：`Map 'B2_KneeDeep.vmap' must contain 's1', 'mini', or 'adventure'`（`strategic_env.py` L522）。
- **根因**: ep_runner/strategic_env 对训练图名做课程门控（T0x_s1/T0x_mini/adventure/h3m 家族前缀路由），H3M 直通转换产物原名（驼峰、无关键词）不在白名单。
- **处理**: `py/rename_b2_knee.py` 双份改名（`rel/bin/data/Maps/` + `maps/training/`）；冒烟重跑通过。
- **教训**: 任何新图入 ep_runner 链路前，图名先过关键词断言；命名纪律 = 前缀带课程/家族关键词。关联：#224（改图后必跑 sync_maps_to_runtime）/ 任务清单 P10-B B2 记录。

#### #247 CMapSaverJson::writeObjects 紧凑 vector 假设：eraseObject 置 null 不重排 → 尾部对象漏写 + null 槽位写空壳 (09-16, B3 R4 首跑踩) — ✅ 已修

- **状态**: ✅ 已修（R4 改 `removeObject` 按 ID 降序删，ROUNDTRIP OK 366→366）
- **现象**: B3 R4 用 `eraseObject`（置 null 保序）删 47 个白名单外对象后，RULED 内存对象 366 正确，但 `ROUNDTRIP MISMATCH in=366 out=330`，读回日志 36 次 `Object type missing {instanceName:"",subtype:"",type:""}` 空壳。
- **根因**: `CMapSaverJson::writeObjects`（MapFormatJson.cpp:1503）先 `resize(getObjects().size())`（过滤 null 后的数量），再循环 `map->getObject(ObjectInstanceID(i))` **直接索引原始 objects vector**——该 API 假设 vector 紧凑无 null。eraseObject 只做 `objects.at(id)=nullptr` 不重排 → 原始 vector 仍 413 项（47 个 null 槽），按 i=0..365 索引时：null 槽位取到空 → 空壳 JSON；落在原始尾部（≥366 位置）的 36 个有效对象**永远不会被写出**。
- **处理**: R4 改用 `CMap::removeObject`（CMap.cpp:593，vector erase + 后续对象 id 重排 + towns/heroesOnMap/terrain tile blockingObjects/visitableObjects 引用全修正），且**按 ObjectInstanceID 从大到小删**——每次删除只重排 ≥ 该 id 的对象，待删集合中更大的 id 已删完，小 id 不受影响，顺序安全。
- **教训**: 引擎内改 CMap 后要 saveMap 的路径，删对象只能 `removeObject`；`eraseObject` 是为 editor undo/redo 场景设计的（保留槽位），与 JSON 序列化器的紧凑假设互斥。审计口径：`getObjects().size()` 是过滤后数量，`objects.size()` 才是原始槽位数，对账时要分清。

#### #248 B3 引擎 C++ API 一揽子坑（getTypeName 短名 / setOwner 与 builtBuildings 均 private / TargetTypeID 嵌套 using / boost 选项数字连字符 / GameLibrary cwd 依赖） (09-16, B3 开发全程) — ✅ 已固化

- **状态**: ✅ 已固化（main.cpp 全部按正确 API 重写，B3 全规则 + 9 case 开关对账通过）
- **坑 1 — `getTypeName()` 返回短名不是 `core:` 全名**：返回 `mountain`/`oakTrees`/`town`/`monster`（与 objects.json 的 type 字段同源），R4 白名单写 `core:town` 全部不匹配 → 413 对象全进待删集。白名单必须用短名。
- **坑 2 — `CGTownInstance::setOwner` 是 private**（`setOwner(IGameEventCallback&, const PlayerColor&) const`，遮蔽基类 1 参版）→ 直接写 public 成员 `t->tempOwner = PlayerColor::NEUTRAL`。
- **坑 3 — `builtBuildings` 是 private 且无 getter** → `t->getBuildings()` 拷贝出集合计数 + `t->removeAllBuildings()` 清空。
- **坑 4 — `EventCondition::TargetTypeID` 是嵌套 using**（VariantIdentifier<ArtifactID,...>），构造 `EventCondition(DAYS_WITHOUT_TOWN, 0, TargetTypeID())` 必须写全限定 `EventCondition::TargetTypeID()`。
- **坑 5 — boost program_options 选项名含数字+连字符不安全**：`--r3-scale` 报 `unrecognised option`，改下划线 `--r3_scale`。
- **坑 6 — GameLibrary 初始化依赖 cwd**：`CResourceHandler::load("config/filesystem.json")` 相对路径，工具必须在 `/home/administrator/vcmi-native` 下执行，否则 `CONFIG/FILESYSTEM not found` abort。**复犯提醒（09-16 B4 验证脚本首跑 SIGABRT RC=134）：任何新转换/验证/冒烟 shell 脚本模板必须首行 `cd /home/administrator/vcmi-native || exit 1`，勿靠记忆补**。
- **教训**: VCMI 引擎 API 大量 private 封装（对象操作走引擎方法而非直改字段）；B3 全部坑在 `tools/h3m2vmap/main.cpp` 注释中有就地说明。

#### #249 PowerShell 调 `wsl bash -c "..."` 时 `$var`/`$(...)` 被 PowerShell 先行插值 → WSL 侧拿空变量，grep/wc 静默返回空/0 (09-16, WIN-1 归因核查踩) — ✅ 已固化

- **状态**: ✅ 已固化（改用单引号包整条 bash 命令 / 弃 shell 变量写完整路径；本次因它多排查 2 轮"文件里为什么没有 BHERO_KILL"）
- **现象**: `wsl bash -c "L=/path; grep -c BHERO_KILL $L"` 在 PowerShell 执行返回 `0`（实际 9 条）；`wc -l $F` 返回 `0`；`$(grep ...)` 报 `grep 不是 cmdlet`。
- **根因**: PowerShell 对**双引号**字符串做自身插值：`$L`/`$F`/`$(...)` 在离开 Windows 之前就被 PowerShell 展开成空串/子表达式执行结果，WSL bash 收到的命令已无变量。不报错、静默给错数据——比 #245（引号转义炸错）更隐蔽：输出像合法的 `0` 而非异常。
- **处理**: 三选一 ① 整条命令用单引号包（PowerShell 不插值单引号内容）；② 不用 shell 变量，写完整路径；③ 复杂逻辑落 .sh 文件再执行（同 #245 教训）。
- **教训**: 判定"文件里没有 X"之前，先用 `ls -l` 字节数与 `wc -l` 对账，确认命令真的读到了文件；PowerShell 侧一切 `$` 一律视为已被消费，跨 wsl 传命令默认单引号。

#### #254 `WIN1_ENV_ARGS` 缺 A2 参数映射 → ep_runner 收不到 `--blue_hero_attack_bypass`，scorer 链选中蓝英雄后贪心回退全 blocked → 引擎反复 `Cannot move hero, destination tile is blocked!` (09-17, A2 旁路首次部署踩) — ✅ 已修

- **状态**: ✅ 已修（`train_wsl2_ppo_v2.py` `WIN1_ENV_ARGS` 补两条映射）
- **现象**: A2 攻击步旁路代码已写入 `ep_runner_one.py`（argparse + 状态变量 + MOVE_TO 执行段蓝英雄分支），但训练启动后日志反复出现 `Cannot move hero, destination tile is blocked!`；`ps aux | grep ep_runner_one` 显示子进程反复重启（RestartCount 226+）；`[BHERO_ATTACK]` 日志零触发。
- **根因**: `train_wsl2_ppo_v2.py` 的 `WIN1_ENV_ARGS` 映射字典（L108-110）没有 `HOMM3_BLUE_HERO_ATTACK_BYPASS` 和 `HOMM3_ATTACK_F_MIN` 两条，导致 ep_runner 子进程命令行缺少 `--blue_hero_attack_bypass` 参数。默认值 `blue_hero_attack_bypass=0`（关），但 `move_blue_hero_target=True`（scorer 链选中蓝英雄）时，贪心回退仍只走 `pas[d]==1`；蓝英雄格 `passable=0`（blocked）→ 所有 cand 方向全 blocked → `a=24`（END_TURN 等价）→ 引擎拒绝 → `blocked` 错误反复。
- **修复**: `train_wsl2_ppo_v2.py` L110（`HOMM3_OWN_TOWN_MAX_VISITS` 后）加两行：
  ```python
  "HOMM3_BLUE_HERO_ATTACK_BYPASS": "--blue_hero_attack_bypass",
  "HOMM3_ATTACK_F_MIN": "--attack_f_min",
  ```
- **教训**: ① 新增 ep_runner argparse 参数必须同步检查 `train_wsl2_ppo_v2.py` `WIN1_ENV_ARGS` 映射，否则参数永远走默认值，且不会报错（静默零行为）；② "blocked" 错误的根因不是引擎问题，而是 Python 侧引导层选中了 passable=0 的目标格但攻击步旁路关；③ 验证新参数是否传到子进程：`ps aux | grep ep_runner_one | grep 'blue_hero_attack_bypass'` 应有输出，或看 `[WIN1_BATCH]` 日志行是否包含该参数。
- **关联**: A2 攻击步旁路 / `ep_runner_one.py`（argparse L85-168）/ `train_wsl2_ppo_v2.py`（`WIN1_ENV_ARGS`）/ `docs/方案_攻击步旁路_20260917.md` / 踩坑 #250（P-H2 同格不可达）

#### #255 PowerShell `wsl bash -c "..."` 双引号内 for 循环 `$var` 被先行插值，`git merge-base --is-ancestor` 全空结果 (09-17, VCMI 上游侦察踩) — ✅ 已固化

- **状态**: ✅ 已固化（#249 同源，本次再次踩到，改用 Python 脚本 / 单引号包整条 bash）
- **现象**: 在 PowerShell 里执行 `wsl bash -c "cd /home/administrator/vcmi-native; for s in $(git rev-parse HEAD); do git merge-base --is-ancestor $s 65515ef24 && echo yes || echo no; done"` 时，for 循环变量 `$s` 在 PowerShell 双引号里被先行展开为空字符串，到达 WSL 后 `git merge-base --is-ancestor $s 65515ef24` 变成无操作数（只跟 HEAD 比），全部静默返回 `yes`/空结果；`grep -c` 同样返回 0。
- **根因**: PowerShell 对双引号字符串做自身插值：`$s`/`$f`/`$(...)` 在 Windows 侧被展开成空串或子表达式执行结果，WSL bash 收到的命令已无变量。比 #245（引号转义炸错）更隐蔽——输出像合法的 `yes`/`0` 而非异常，容易误判为"没有该提交"。
- **处理**: 三选一 ① 整条 bash 命令用单引号包（PowerShell 不插值单引号内容）；② 不用 shell 变量，写完整路径/完整哈希；③ 复杂逻辑（含 for 循环、管道、JSON 解析）直接落 Python 脚本（`py/scan_vmap_events.py` / `py/locate_mana_hits.py` / `py/probe_victory.py`），完全绕开跨 shell 变量传递。
- **教训**: ① #249 固化后仍需警惕——任何 `wsl bash -c "..."` 里出现 `$` 一律默认被 PowerShell 吞掉；② 涉及 for 循环 / 多行逻辑的跨 WSL 命令，优先落 Python/`.sh` 脚本，不要内联；③ 判断"命令无输出"时，先确认 WSL 侧变量是否真的存在（`echo "$var"` 自检），避免把"变量被吞"误判为"结果为零"。
- **关联**: #249（同机制首次固化）/ #245（引号转义炸错对照）/ `py/probe_victory.py`（vmap 探查工具，本轮为绕开本坑新建）

#### #257 `pgrep -f`/`pkill -f` 在 `wsl bash -c` 内匹配 bash 自身命令行 → 服务假阳性 ALIVE、`||` 短路致后台进程从未启动 (2026-09-18, 快照器部署踩) — ✅ 已固化

- **状态**: ✅ 已固化（快照器"部署成功"假象持续 ~40 分钟，取证一直空转才暴露）
- **现象**: `wsl bash -c "pgrep -f contact_log_snapshot >/dev/null || (nohup python contact_log_snapshot.py &); pgrep -f contact_log_snapshot && echo ALIVE"` 返回 pid 且输出 ALIVE，但快照器从未工作（环形快照零文件）。另 PowerShell **单引号**包 `wsl bash -c '...$(pgrep...)...'` 也失守——`$(...)` 在 PowerShell 侧被执行成字面数字拼进 bash 命令（`for p in 3553; do` 语法炸），推翻"#255 单引号安全"的旧口径。
- **根因**: `pgrep -f` 按完整命令行匹配——`bash -c "... contact_log_snapshot ..."` 的 **bash 进程自身命令行含关键字** → pgrep/pkill 永远"找到"自己所在的 bash → `||` 判"已在跑"跳过启动；`pkill -f` 则直接把 bash 自己杀掉（exit 15）。
- **处理**: ① 匹配串加进程特征再过滤：`ps aux | grep contact_log_snapshot.py | grep -v grep | grep -c 'bin/python'`（三段过滤，bash 命令行不含 `bin/python` 前缀）；② 启动+验证逻辑落 **sh 脚本文件**执行（`py/restart_snapshotter.sh`，脚本内 `SELF=$$` 排除自身 pid）——文件执行零引号传递，是 #255/#257 的共同终极解；③ PowerShell 单引号在跨 wsl 场景一律不再信任，复杂命令一律脚本化。
- **教训**: ① "进程存活检测"必须用与进程名无关的特征组合并排除自匹配，或干脆检查**进程产物**（本例：环形快照文件是否生成——产物检查第一时间就能暴露假部署）；② `X || 启动X` 的幂等启动模式在 `-f` 模糊匹配下天然自欺；③ #255 的"单引号安全"结论**只对简单命令成立**，含 `$(...)`/`$var` 的复杂命令单引号也会失守。
- **关联**: #255（同日跨 shell 插值主坑，本条为其单引号失守扩展 + 自匹配假阳性变体）/ #256（交织误归属，同日观测链三连坑）/ `py/contact_log_snapshot.py` + `py/restart_snapshotter.sh`（本坑产物）

#### #256 主日志 10-env 交织写入 + 事件行不含地图名 → 按地图名分段抓取把 [SCORE] 等事件误归属相邻局 (2026-09-18, T7.6 冒烟踩) — ✅ 已固化

- **状态**: ✅ 已固化（分析结论因此差点全部走偏，冒烟中途发现纠正）
- **现象**: T7.6 冒烟用 `awk '/地图名/{f=1} f&&/SCORE|BHERO/{print}'` 按地图分段抓 train_loop.log，把 `step40 pick=(32,34) type=blue_hero` 两条 [SCORE] 判给 72X72_01 局，据此推演"攻击步条件全满足却零触发"循环推理 2 轮无果。
- **根因**: 主日志由 10 个 env 的 ep_runner 子进程**交织 append**（同一局内的行也不连续）；而 `[SCORE]`/`[BHERO_CONTACT]` 等事件行**不含 map= 字段**——按地图名置位的分段标志只能由含地图名的行（BHERO_GRAD/EP_TIME/START_HOME，全在局尾/局头）置位，事件行实际落进了**相邻局**的段。
- **正确口径**: ① 归属事件行必须用"局边界"（上一条 EP_TIME 到下一条 EP_TIME 之间）而非地图名置位；② 单局分析直接用 `/tmp/hermes_ep_<pid>.log`（ep_runner stdout 全量单局，无交织，pid 与 ps aux/启动时间对应）；③ 结论性归因（"某局 pick 过 X"）必须有局边界证据，交织日志上的"同段出现"不构成归属。
- **教训**: ① 多进程写同一日志时，任何"按内容分窗"的 grep/awk 都要先画行序模型，确认锚点行真的在窗内；② hermes_ep 单局日志是局级归因的第一证据源，主日志只用于跨局统计；③ "条件全满足但没触发"类死循环推理，第二优先级永远是"怀疑观测工具本身"。
- **关联**: #255（同日 PowerShell 插值坑，观测链第二坑）/ `py/a2_contact_probe.py` / `py/passable_gate_watch.py`（看板按"最后 WIN1_BATCH 行"切窗不受本坑影响）/ 知识库 09-18 T7.6 冒烟章

#### #258 GitHub 建仓认证链断：gh device flow 端点 POST 被掐 + keyring token 失效 → 建仓"浏览器手建 + SSH push"，gh CLI 用 `GH_TOKEN` 驱动 (2026-09-18 踩 → 09-19 修复) — ✅ 已修复

- **状态**: ✅ 已修复（09-19：gh CLI 走 `GH_TOKEN` 环境变量驱动，绕开 `gh auth login` 的 `read:org` 硬校验；git push/clone 走 SSH 443；API 走 `api.github.com`。token 存 `~/.config/gh-token`(600) + Windows 用户级 `GH_TOKEN` env var 持久化）
- **现象**: ① `gh auth status` 报 keyring token 失效（401，旧 token 过期）；② `gh auth login -s web`（device flow）POST `https://github.com/login/device/code` 报 `wsarecv: A connection attempt failed`；③ 手动 curl 复现：GET github.com / api.github.com / raw 全 200，唯独 POST /login/device/code 连接超时（curl 28）；④ gh-proxy.com 代理该端点返回 404（只代理 raw/release/clone 路径，不代理 /login）。
- **根因**: 大陆网络环境对 github.com 的 **POST** 端点间歇性掐断（GET 通、POST 不稳，GFW SNI 干预特征）；gh 的 OAuth device flow 强依赖该 POST 端点；gh-proxy 系加速站覆盖不到 /login 认证端点。
- **精确网络拓扑（09-19 复测，实测 HTTP 码/连通性）**:
  - `api.github.com` **HTTPS 通**（GET 200 / POST 返回真 HTTP 码，0.3-0.6s）→ gh CLI / 直接 API 走这里
  - `github.com` **HTTPS:443 被掐**（git ls-remote https:// 报 "Could not connect to server"）→ git 不能走 HTTPS
  - `github.com` **SSH:443（ssh.github.com）通**（`ssh -T git@github.com` → "Hi c18593395!"）→ git push/clone/fetch 全走 SSH remote（`git@github.com:...`）
  - `github.com/login/*`（device flow / oauth）被掐 → gh 交互式登录不可用
- **gh CLI 正解（`GH_TOKEN` 驱动，绕开 login scope 校验）**:
  - 关键实锤：`gh auth login --with-token` 对 classic PAT **硬性校验 `read:org` scope**（gh 2.87.2），只有 `repo` 的 token 会被拒（报 `missing required scope 'read:org'`）——但 **`GH_TOKEN` 环境变量直接驱动 gh 不触发该校验**，`repo` scope 对 fork/PR/管自有仓全够用。
  - 修法：token 存 `~/.config/gh-token`(chmod 600) → `[Environment]::SetEnvironmentVariable('GH_TOKEN', $t, 'User')` 持久化成 Windows 用户级 env var（rc 里不留明文，只从 600 文件读）→ 新进程 `gh auth status` 显示 `✓ Logged in ... (GH_TOKEN)`。
  - 注意：git 操作仍走 **SSH**（`git@github.com` 443），token 只驱动 gh CLI（fork/PR/CI 管仓，全打 `api.github.com`）。`.netrc`（machine github.com）可建但无意义——git 走不到 github.com HTTPS。
- **正确处理（建仓三条路，按可用度排）**: ① **gh CLI（GH_TOKEN）fork/建仓/开 PR（全自动，本仓已具备）**；② SSH push（443 代理 ssh.github.com，首推已用）；③ 浏览器手建（30 秒兜底）。PAT 生成时 scope 勾 `repo`+`read:org`+`workflow` 可让 `gh auth login --with-token` 也走通（当前只 `repo` 也能被 GH_TOKEN 驱动，够用）。
- **教训**: ① 大陆网络下 gh device flow 默认不可用，第一步直接试 `gh auth status` 确认 token 有效性；② **gh 挑食 `read:org` 的解法不是重登而是 `GH_TOKEN` env var 驱动**（绕开 scope 校验，`repo` 就够）；③ 网络要分层实测（`api.github.com` / `github.com` HTTPS / `github.com` SSH443 / `github.com/login` 四通各不同），别用"gh 修不了"一杆子打死——能通的那条路（GH_TOKEN + SSH）就是"修好 gh"；④ gh-proxy.com 能力边界记牢：raw/release/clone 加速可用，POST /login（device flow）不可用。
- **关联**: #184（gh auth 401 子 agent 认证坑）/ #259（#205 PR 提取，推 PR 依赖本条打通的 gh/SSH）/ vcmi_gym 仓首推（本坑触发场景）/ 知识库 09-18 开源立项章 + 09-19 gh 修复增量

#### #259 摘取候选须 `merge-base --is-ancestor` 复核 + fork 基线 diff 不能 apply 上游 (2026-09-18, #205 官方 PR 提取踩) — ✅ 已固化

- **状态**: ✅ 已固化（本轮把"官方 3 小 PR"清单从 3 收窄到 1）
- **现象**: ① 按 skill ref 的"摘取候选"清单推荐先提 NKAI race `a1ea3f4d2d` + JSON seek `01f741713c`，动手前用 `git merge-base --is-ancestor <sha> upstream/develop` 一核，发现两者**都已进官方**（NKAI=Ivan Savenko 6 月自修、JSON seek=kdmcser 9 月 10 日修）——skill ref 里"仍 MISSING"的记录已随上游迭代过时，照单推荐等于提重复 PR。唯一还原创可提的是 #205 服务端 pack try/catch。② 本地 #205 的 diff（commit `1c3be8d030`）是相对 **smanolloff fork 基线**写的（`retrievePack` 在 L164、`auto pack`），而 `upstream/develop` 上在 **L147**——文件已分叉，`git apply`/`git cherry-pick` 不能直接用，得基于 `upstream/develop` 重建。
- **根因**: 摘取候选清单是某一时点的快照，官方 develop 在 9 月还在滚动合入（09-11 复核时还 MISSING，09-18 已被上游维护者自己修掉）。"能否提 PR"的判据不是"我本地有没有"，而是**"upstream/develop 是否已含等价修复"**——必须每次动手前用 `merge-base --is-ancestor` 对上游实锤，不能信静态记录。
- **正确处理**: ① 每个摘取候选提 PR 前先 `git fetch upstream && git merge-base --is-ancestor <fix-sha> upstream/develop && echo 已含 || echo 可提`；② fork 基线改的 diff 要进官方，**不 cherry-pick**，而是在 `git worktree add -b <pr-branch> <path> upstream/develop` 干净 worktree 上**手工重建**（只摘该修的段，剔掉本地混入的诊断脚手架，如 #205 剔 `[SRV-DIAG]`/`TOWNAVAIL` fprintf）；③ 重建后做符号级实锤（异常类定义位置/成员、被调函数返回类型、既有同构代码块），不裸信"改了能编译"。
- **附带坑（同轮）**: `git worktree add /d/.../vcmi_pr205` 在 MSYS 下把 `/d/` 当字面量，worktree 实际落到 `D:/d/...`（native git 不转 MSYS 路径）；`git worktree list` 能看到真实落点，后续 `cd` 用 native `D:/d/...` 路径。
  - **09-19 已收口**: worktree 已 `git worktree move` 迁回正路 `D:/Bigdata/hero3_fresh/vcmi_pr205`（HEAD 20ba315945 不变），`D:\d` 整树误建残留（含 7-15 旧版 strategic_state.cpp/threadconnector.cpp 快照，正路 git 已有新版覆盖）已全清。后续引用一律用 `D:/Bigdata/hero3_fresh/vcmi_pr205`。
- **教训**: ① 上游跟踪型清单（MISSING/候选）一律视为"待复核"快照，不是结论——提 PR/摘取前逐条对 `upstream/develop` 重验；② "我方已修"≠"官方需我提"，判据永远是对上游的 `is-ancestor`；③ fork 基线 diff 进官方走 worktree 手工重建，不走 cherry-pick。
- **关联**: #258（gh API 认证断，推 PR 需浏览器手建 fork 或用户出 PAT）/ 知识库 09-18「官方小 PR 清单（09-18 复核后收窄）」/ worktree `vcmi_pr205` 分支 `pr205-server-pack-guard`

#### #260 官方 H3M 图 R1 城镇归零 → 引擎不生成英雄 → 3 步 zombie 崩局 (09-18/19, 官方图转换链验证踩) — ✅ 已修（官方图一律 --no-r1）

- **状态**: ✅ 已修
- **现象**: wdc/ui 首版官方图转换后训练验证 3 步即死，obs 无英雄，zombie。
- **根因**: R1"城镇归零"针对自制图设计，但官方图**地图上无英雄实体**——英雄全靠 mainTown `generateHeroAtMainTown` 开局生成；R1 把城 owner 归 NEUTRAL 后引擎开局不生成任何英雄 → obs heroes 段空 → 3 步死。
- **处理**: 官方图转换命令统一 `h3m2vmap --save <in.h3m> <out.vmap> --no-r1`。
- **教训**: 改写层每条 R 规则都有隐含前提（"图上有英雄实体"）；对陌生地图族启用前先用最小验证局探行为，不能默认规则正交可组合。
- **关联**: #261（参数顺序）/ 知识库 09-19 章（官方图兼容三大根因）

#### #261 h3m2vmap 开关参数放位置参数前 → 被当文件名 "cannot open or empty" (09-18, 官方图转换踩) — ✅ 已固化

- **状态**: ✅ 已固化
- **现象**: `h3m2vmap --no-r1 --save a.h3m b.vmap` 报 `cannot open or empty: --no-r1`。
- **根因**: 工具按位置顺序解析 argv，`--no-r1` 出现在第一个文件参数之前被当作输入文件名。
- **处理/口径**: 开关一律放位置参数**之后**：`h3m2vmap --save <in> <out> --no-r1`。
- **教训**: 自研 CLI 开关解析多为顺序实现，与 GNU 习惯（开关任意位置）不同；报 "cannot open" 先查参数顺序。
- **关联**: #260

#### #262 R2 硬编码 aiSlot 遇他色实体 segfault rc=139 + blue 槽 factions 空 → "Expected at least 2 non-neutral players" (09-18, R2v2 立项踩) — ✅ 已修（R2v2 智能重配定稿）

- **状态**: ✅ 已修（R2v2 上线后 72×72 有地下 2p 图池对手色限制解除，159 张官方图全量可转）
- **现象**: ① Ready or Not（3p tan）转换后验证 segfault rc=139，stderr "Cannot find player 2 info!"；② Faeries 转换后 "Expected at least 2 non-neutral players, got 1" 拒启；③ 曾试"从官方 playable 槽选 aiSlot"仍败——blue 槽 factions 空被引擎剔除。
- **根因**: ① R2 旧版只认 red/blue 两色，官方图 pink(7)/green(3)/tan 等槽位有实体 → 引擎按槽位查 PlayerInfo 缺失崩；② blue 槽 `allowedFactions` 为空被引擎剔出"非中立玩家"计数，只剩 red 1 家拒启（blue 是 StrategicEnv 硬假设 AI 槽，不可让渡给其他色）。
- **处理（R2v2 终版，`tools/h3m2vmap/main.cpp`）**: **aiSlot 恒=blue(1)**；他色英雄 removeObject（降序）、他色非英雄实体 tempOwner=NEUTRAL（城记入 neutralTowns）；blue 无城时从被中立化城中挑"离 red mainTown 曼哈顿最远"的归还 blue 作出生城（hasMainTown/generateHeroAtMainTown/posOfMainTown 三同步）；blue `allowedFactions` 空则补全 9 种族 + isFactionRandom=true。report 键 `R2v2_*` 可审计。
- **教训**: ① "Cannot find player N info" 类 segfault 必须查 rc（bash 段错误打 stderr 不进日志），rc=139 优先怀疑玩家槽位与实体色不齐；② 玩家重配的不变量是"每个有实体的色必须有 PlayerInfo 且 factions 非空"，补齐不变量比逐图打补丁可扩展。
- **关联**: #218/#219（批量转换 segfault 前科）/ 知识库 09-19 章 / `py/probe_r2v2.sh`（report 键探针）

#### #263 管线 subprocess 转换全失败：#248 cwd 坑换皮重踩 + header 带 `// game` 注释 json.loads 炸 (09-18, h3m_batch_pipeline 首跑踩) — ✅ 已修

- **状态**: ✅ 已修
- **现象**: ① 管线跑起来 h3m2vmap 转换 100% 失败，手动同命令成功；② strip 阶段 `json.loads(header)` 撞注释解析错（Faeries header 带 `// game` 注释）。
- **根因**: ① #248 老坑换皮：subprocess 未设 `cwd=/home/administrator/vcmi-native`，config/Mods 数据依赖缺失 → 引擎起不来；② #220 已知 vmap JSON 含 C++ 注释，管线新代码绕过公共工具直接 json.loads。
- **处理**: ① 管线 `run()` 内 `kw.setdefault("cwd", vcmi-native)` 全局兜底（不靠调用点记忆）；② 全部 vmap JSON 解析统一走 `strip_underground_vmap.load_json`（剥注释）。
- **教训**: ① "手动成功、脚本失败"第一嫌疑是 cwd/env 差异（#248 同源）；② 已知解析坑要在公共工具函数里根治，新代码不允许绕过公共入口裸 json.loads。
- **关联**: #248（cwd 首踩）/ #220（注释 JSON 首踩）/ `py/h3m_batch_pipeline.py`

#### #264 `pkill -f 'ep_runner_one.py.*h3m'` 险些误杀主训练：图名含 h3m 跨进程误伤 (09-19, 管线残留清理踩) — ✅ 已固化（pkill -f 家族第四坑）

- **状态**: ✅ 已固化（杀前进程树核查躲过一劫）
- **现象**: 清理管线残留 ep_runner 时拟用 `pkill -f 'ep_runner_one.py.*h3m'`；核查发现主训练 ep_runner 命令行同样含 `h3m`（图池 King_of_Pain_h3m 等）→ 该模式会**把主训练 worker 一起杀**。
- **根因**: `-f` 全命令行匹配 + 主训练图名天然含 `h3m`，"按图名选进程"的模式串无法区分管线验证局与主训练局。
- **处理/口径**: ① 杀前必查 `ps -o pid,ppid,lstart,cmd` 用 **ppid/启动时间** 区分（主训练 ep_runner ppid=主训练主进程，管线残留 ppid=1/nohup）；② 只 kill 实锤 PID，禁模式串批量杀；③ 当轮实锤 5497=主训练、6049=残留，仅 kill 6049。
- **教训**: pkill -f 家族四连坑（自匹配 #27/#155、`||` 短路假阳性 #257、跨进程误伤本条）——共同解是"脚本化 + 特征过滤 + 杀前人工核对 PID 清单"；训练在线期间任何 pkill 先画进程树。
- **关联**: #27/#155/#257 / 主训练 PID 163（train_wsl2_ppo_v2.py）/ `py/h3m_batch_pipeline.py`

#### #265 `rm -rf` 删掉运行中进程正写的日志 → `/proc/PID/fd/1` 抢救 + WSL /tmp 日志打通 Get-Content (09-19, 批跑日志运维踩) — ✅ 已修

- **状态**: ✅ 已修（日志全量抢救回 D 盘，批跑无中断）
- **现象**: ① 想把 `/tmp/h3m_pipeline` 挪到 D 盘，`rm -rf` 后重建软链，`run_all.log` 从此"消失"；② 先 `ln -sfn` 把 /tmp/h3m_pipeline 指到 D 盘后，再 `cp /tmp/h3m_pipeline/ /mnt/d/...` 复制 0 文件。
- **根因**: ① 批跑进程（PID 6363）持有已打开 fd → `rm -rf` 后文件标记 deleted 但进程继续往里写（目录里不可见）；② 软链已把两端指成同一路径，`cp` 源=目标，复制自身失败。
- **处理**: ① `ls -la /proc/6363/fd/1` 确认 `(deleted)` → `cat /proc/6363/fd/1` 全量读出日志内容写回 D 盘（无需重启批跑）；② Windows 侧长期 `Get-Content -Tail 20 -Wait` 的正确姿势：**数据落 D 盘**（`/mnt/d/Bigdata/hero3_fresh/tmp/h3m_pipeline`），WSL 侧建入口软链 `ln -sfn /mnt/d/... /tmp/h3m_pipeline`（链建在 WSL /tmp 下，方向 WSL→D 盘）；③ `ln -sfn` 对已存在的**真实目录**不会替换——先删旧目录再建链。
- **教训**: ① 进程正写的文件 rm 后并未消失，`/proc/PID/fd/N` 是唯一抢救口；② 对运行中服务的输出路径做迁移，正确顺序是"软链替换 + 重启服务指向新路径"，不能先 rm；③ WSL 日志要给 PowerShell 用，一律数据落 /mnt/d、/tmp 只放链。
- **关联**: #28（/tmp 清空丢日志前科）/ `py/h3m_batch_pipeline.py` / 知识库 09-19 章运维节

#### #266 ep_runner_one.py L1614 `traj["rewards"]` 键名存量 bug：死亡局 KeyError (09-19 盘点发现) — ⚠️ 待修（等停训窗合批）

- **状态**: ⚠️ 待修（训练在线，不单独停启）
- **现象**: 管线独立验证（--model 驱动）死亡局（steps<50% FAIL）时 runner 侧 KeyError: 'rewards'；主训练无感。
- **根因**: `ep_runner_one.py` L1614 轨迹键实为 `traj["rew"]`；主训练路径靠"丢弃 error 局"兜底从未暴露。
- **影响**: 独立验证死亡局轨迹解析中断，FAIL 只剩 steps 数，吞掉死亡局诊断信息。
- **处理**: 改 `traj["rewards"]` → `traj["rew"]`；建议下次停训窗随其他改动合批部署（改 Python 后清 `__pycache__`）。
- **教训**: "主训练没报错"≠"代码没 bug"，只说明错误路径没走到；共享 runner 的旁路用法（独立验证）是 bug 的天然探测器。
- **关联**: `py/ep_runner_one.py` / `py/h3m_batch_pipeline.py` train_verify



#### #267 360 安全卫士拦截 keepalive：计划任务被删 + `wsl.exe sleep infinity` 进程被杀 → idle shutdown 反复发生 (2026-09-19 定性) — ✅ 已定性（用户拍板：不做自动启动，每次手工启动）

- **状态**: ✅ 已定性；**拍板：取消全部自动启动机制，keepalive 每次手工拉起**
- **现象**: ① 09-18 22:31 与 09-19 02:24 两次 WSL idle shutdown（keepalive 明明部署过）② 09-19 深夜排查发现 `homm3-wsl-keepalive`/`homm3-wsl-keepalive-guard` 两个计划任务**整个消失**（schtasks 报"找不到指定的文件"）、`wsl.exe sleep infinity` 进程 **0 个**（Get-CimInstance 实测）——360 安全卫士主动防御（ZhuDongFangYu）把"隐藏窗口脚本 + 计划任务持久化 + 常驻 wsl.exe"识别为可疑行为链清理。
- **根因**: 360 主动防御对"计划任务持久化 + Hidden 窗口脚本（VBS/PowerShell -WindowStyle Hidden）+ 非交互常驻进程"组合的典型拦截；重注册后也可能被再次静默删除（第一次 Register-ScheduledTask 成功但任务后来消失）。
- **处理**: ① **用户拍板放弃自动启动**——删除/不再重建任何计划任务，keepalive 改为**每次启动训练后手工拉起**：`Start-Process wsl.exe -ArgumentList '-d','Ubuntu','sleep','infinity' -WindowStyle Hidden`（或双击 `py/homm3_wsl_keepalive.vbs`）② 手工拉起后用产物检查验证：`(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" | ? { $_.CommandLine -like '*sleep*infinity*' }).Count` ≥1 ③ 如后续想加白：360 界面 → 信任区添加 `d:\Bigdata\hero3_fresh\py\homm3_wsl_keepalive.vbs` / `py\homm3_keepalive_guard.ps1`（360 无 CLI 加白接口，须界面操作）。
- **教训**: ① "部署成功"≠"长期生效"——安全软件会事后静默清理，**存活类部署必须定期产物验证**（进程计数/文件存在），不能只看注册时返回 SUCCESS；② Windows 侧环境的对抗性（360 等）是 WSL 训练存活问题的隐藏维度，排障顺序应加上"查安全软件拦截记录"；③ enabled unit 的 systemd 自动拉起是可靠的最终兜底（02:25:42 自动恢复零损失实证），keepalive 只是减少冷启动次数。
- **关联**: #114（keepalive 首次引入）/ #201（容器空闲关停）/ #257（假阳性检测法——产物检查思想同源）/ 知识库 09-18 keepalive 章 / `py/homm3_keepalive_guard.ps1`（保留文件但不再注册任务）/ `py/homm3_wsl_keepalive.vbs`

#### #268 highlights 白名单缺标签 → [ECON]/[BHERO_ATTACK]/[BHERO_KILL] 等事件行主日志永不可见，造成"零触发"假象 (2026-09-19, A6 排查踩) — ✅ 已修已固化

- **状态**: ✅ 已修（补 [ECON]/[BHERO_ATTACK]/[BHERO_KILL]/[ATK_DBG] 四标签进白名单，重启窗生效实测可见）
- **现象**: 任务清单 A6 遗留"[ECON] first BUILD_2 全窗 0 条（BUILD 动作无效嫌疑）"挂了两天；排查用 act 序列统计实锤 act20 历史 79% 局在发——**动作一直在发生，只是日志看不见**。同理 [BHERO_ATTACK]（T7.6 冒烟）在主日志 grep 恒空也含此因（当时归因于"未触发"部分正确、部分为本坑）。
- **根因**: train_wsl2_ppo_v2.py 主进程在 ep_runner 退出后按 **highlights 关键词白名单**过滤 stdout 转储进主日志（L258-270）；新增埋点若忘记同步加白名单，事件行就永远只存在于 /tmp/hermes_ep_*.log（且单文件每局覆盖，见 #256 姊妹坑）。
- **处理**: ① 白名单补 [ECON]/[BHERO_ATTACK]/[BHERO_KILL]/[ATK_DBG]（重启窗生效）；② 新增埋点时的 checklist 加一项"highlights 白名单同步"。
- **教训**: ① 判据统计类标签（如 [BHERO_SLAIN]）与诊断标签要分开管理，新增奖励/埋点必须同步白名单，否则判据永远读零——与 #254（参数静默零行为）同属"静默不生效"家族；② 观测不到 ≠ 没发生：先用旁路数据（act 序列/BHERO_EV_LOG/hermes log）反证，再下"零触发"结论；③ 主日志是**过滤视图**不是全量日志，全量在 /tmp/hermes_ep_*.log。
- **关联**: #256（交织误归属，同为观测链坑）/#257（假阳性检测）/ #254（静默零行为家族）/ `py/build2_probe.py`（act20 统计探针）/ 知识库 09-19 凌晨章 A6/A9 定谳

#### #269 WSL 引擎自更新到 2.7.10 后 cold-start 重建 distro 元数据 — 训练 venv/systemd unit 全丢，rootfs 被重置为全新 Ubuntu (09-19) — 🔄 用户重装 ext4.vhdx 中（防再犯三件套已固化）

- **状态**: ✅ 事故已收口（rootfs 重装 + 训练 resume step=770300 device=cuda）；三件套台账：① vcmi-native 推 D 盘镜像仓 ✅（09-19 白天收口，见 #278）② 定期 wsl --export ⏳ ③ 重建脚本 setup_wsl_train.sh 固化 ⏳
- **现象**: 09-19 02:47 训练 `homm3-train-v5` 正常运行（PID 160/2083，T05/T06 图池，step=770300）；02:50:10 触发 "Shutdown signal received, saving current state..." 优雅存盘（wsl2_model.pt + wsl2_model_state.pt 双写 D:\Bigdata\hero3_fresh，step=770300）。随后 WSL 引擎 2.7.10 自更新窗口内，`wsl -l -v` 列出的 distro 注册表条目与 `HKCU\...\WSL` 键消失，cold-start 时 `ext4.vhdx` 被重建为 1.2G 全新 Ubuntu（/home 仅 44K，无 venv、无 systemd unit、无 C 扩展），03:13 起 `homm3-train-v5` 服务找不到 unit 文件，训练中断。
- **根因链（有把握 + 没把握分开说）**:
  - 有把握：ext4.vhdx 03:13 被重建，旧注册表元数据（HKCU\WSL 键 + distro GUID）丢失，rootfs 内容重置为全新 Ubuntu；
  - 没把握：重建触发的确切机制（引擎 2.7.10 自更新后首次 cold-start 时的元数据迁移/修复 vs 其它）。本次窗口期 WSL 引擎 2.7.10.0（HKLM Lxss\MSI Version），引擎行为与 2.6/2.7 早期不同，自更新后注册表/元数据兼容性是最大嫌疑。
- **损失评估（数据分层）**:
  - ✅ 安全（Windows D 盘）: 模型 checkpoint（wsl2_model.pt + wsl2_model_state.pt，step=770300）、训练日志（train_loop.log）、maps/data、openspec、docs、.so 产物（rel/bin）、全部源码与 scripts（hero3_fresh 主仓 D 盘）。
  - ❌ 丢失（原 rootfs）: `/home/administrator/vcmi-workspace/venv`（PyTorch+CUDA）、`/etc/systemd/system/homm3-train-v5.service`（system 级 enabled unit）、C 扩展（.so 的 C 依赖/编译缓存）、home 目录其它（ssh 配置/git config/pip 缓存）。
  - 注：`D:\Bigdata\hero3\vm\Hero3TrainVM.vhdx`（7.97G）与 `D:\Bigdata\ubuntu-noble-wsl.rootfs.tar.gz` 均**不是**当前训练 WSL 的 rootfs 备份——前者是 07-16 的 HyperV 时代老镜像（1 月未动），后者是原始 rootfs 基线（新装 Ubuntu 镜像，非已装 venv 的状态）。两者都**不能**用来恢复已装好的 venv/unit。
- **防再犯三件套（用户拍板要做，重装完成时执行）**:
  1. **vcmi-native 推 D 盘镜像仓**：`git push D:\Bigdata\git-mirrors\vcmi-native.git mmai-ml`（本地 bare 仓即可，不需要 GitHub），让 6 个战略层 commit + 132 个管线文件有第二落点，rootfs 再丢也不致命。
  2. **定期 `wsl --export` 备份 rootfs**：大改/晋级达标后跑 `wsl --export Ubuntu D:\backup\ubuntu-YYYYMMDD.tar.gz`（export 是 rootfs 级快照，可 `wsl --import` 恢复；**不要直接拷 ext4.vhdx**——动态盘离线拷贝后开机可能无法挂载，export 才是正确姿势）。频率建议：每周一次 + 每次大改/晋级后必做。
  3. **重建脚本固化在 D 盘**：`setup_wsl_train.sh`（venv 建 + 依赖装 + systemd unit 写 + 服务启），unit 文件内容从 09-11 #201 窗口记录复现（/etc/systemd/system/homm3-train-v5.service，User=administrator，StandardOutput=append 到 train_loop.log，ExecStart 用绝对路径 venv）。把 rootfs 丢失的代价从"灾难"降成"30 分钟重建"。
- **触发时机（运维检查口径）**: 每次 Windows 更新 / WSL 引擎版本跳了之后，先 `wsl -l -v` + 查 `D:\wsl\Ubuntu\ext4.vhdx` mtime，确认没被重置再开工；可选把 WSL 引擎更新设成手动（Windows Update 设置 → 高级选项 → 暂停/手动控制 driver updates），降低自更新撞训练窗口概率。
- **教训**: ① rootfs（WSL 内部）与 Windows D 盘（宿主）是**两套数据层**，checkpoint/源码/产物全部落 D 盘是本次没丢训练进度的根本原因——这条分层纪律必须保持：任何新工件（新脚本、新 .so、新数据）默认落 D 盘，不在 rootfs 里留唯一副本；② 引擎自动更新是本次导火索，"更新后检查一次 WSL 状态"应成为更新后例行检查；③ 注册表键/元数据丢失 ≠ 数据丢失，ext4.vhdx 还在就有恢复窗口，panic 前先分层盘点"哪些数据在哪一层"。
- **关联**: #201（容器空闲关停双层修复——本次 keepalive/systemd unit 架构是其产物）/ #168（unit 消失 + is-active 骗人，同族）/ #267（keepalive 被 360 清，本窗口期 keepalive 已按拍板改为手工拉起）/ 知识库 09-19 章「WSL rootfs 重置事故 + 防再犯三件套」。

#### #270 ENABLE_ML 默认 OFF → ML/ 子树不进构建树，`No rule to make target 'mlclient'` (09-19 重建踩) — ✅ 已修（-DENABLE_ML=ON）

- **状态**: ✅ 已修（cmake 加 `-DENABLE_ML=ON`，configure 一次过）
- **现象**: 重建后 `cmake --build rel --target mlclient` 报 `gmake: *** No rule to make target 'mlclient'`；`make help` 里只有 vcmi/vcmiclient/vcmiserver，无任何 ML 目标。
- **根因**: vcmi 根 CMakeLists.txt L113 `option(ENABLE_ML "Enable compilation of extensions for MMAI training" OFF)` 默认 OFF；L778-779 `if(ENABLE_ML) add_subdirectory(ML)`——ML/ 子树（mlclient 库 + mlclient-cli）**根本不进构建树**。原 WSL 编译时显然带过此开关，但开关不在任何文档/脚本里，属"环境记忆丢失"。
- **处理**: `cmake -S . -B rel ... -DENABLE_ML=ON`（configure 阶段同时注入 `-DENABLE_ML` 宏定义，strategic_state.cpp 的 ML 分支依赖它）。
- **教训**: ① **非默认开关必须在重建脚本/文档中固化**——本次 4 个 cmake 开关（ENABLE_ML=ON / ENABLE_DISCORD=OFF / LAUNCHER/EDITOR/TEST=OFF）全是靠报错逐个试出来的，应写进防再犯三件套的 `setup_wsl_train.sh`；② `make help` 查 target 存在性是定位"开关缺失 vs target 写错"的第一步。
- **关联**: #269（rootfs 重置，本坑是其重建副产品）/ #271（同批 cmake 开关）

#### #271 ENABLE_DISCORD 默认 ON + submodule 未拉 → configure 炸 `discord-presence does not contain a CMakeLists.txt` (09-19 重建踩) — ✅ 已修（-DENABLE_DISCORD=OFF）

- **状态**: ✅ 已修
- **现象**: cmake configure 报 `CMake Error at client/CMakeLists.txt:553 (add_subdirectory): .../client/lib/discord-presence does not contain a CMakeLists.txt file`。
- **根因**: client/CMakeLists.txt L545-556 `if(ENABLE_DISCORD)` 默认打开 → `add_subdirectory(lib/discord-presence)`；而 `D:\Bigdata\hero3_fresh\vcmi\` 副本当初 `git clone` 时**未拉 submodule**（discord-presence 目录为空壳）。训练引擎与 Discord RPC 毫无关系，此依赖纯属客户端附带。
- **处理**: `-DENABLE_DISCORD=OFF`（Discord.cpp 源文件仍在 vcmiclientcommon 源列表里，但宏关闭后其内容被 `#ifdef` 保护，不参与编译）。
- **教训**: ① **副本搬运源码树时 submodule 完整性必须校验**（`git submodule status` / 看关键目录是否空壳）；② 对训练无用的可选依赖优先关而不是补——补 submodule 需要网络 + git 重建，关一个开关零成本。
- **关联**: #270（同批 cmake 开关）/ #269

#### #272 D 盘 vcmi/ 副本缺原 WSL 本地补丁：VCMIDirsXDG 缺 libraryName/libraryPath 纯虚实现 → `cannot declare variable 'singleton' to be of abstract type` (09-19 重建踩) — ✅ 已修（patch_vcmidirs_0919.py）

- **状态**: ✅ 已修（补丁脚本幂等可重放，落 `py/patch_vcmidirs_0919.py`）
- **现象**: 编译 `lib/VCMIDirs.cpp` 报两轮 abstract type 错：① 缺 `libraryName`（VCMIDirs.h L58 纯虚）② 补完再缺 `libraryPath`（L51 纯虚）。
- **根因**: **D 盘 vcmi/ 副本与原 WSL vcmi-native 源码不同步**（项目规则早有警告，本次第 2 次实锤）。头文件里 IVCMIDirs 的 10 个纯虚函数，Linux 侧实现链（IVCMIDirsUNIX/VCMIDirsXDG）缺 2 个——原 WSL 树里这 2 个实现是本地补丁，从未回推 D 盘副本。md5 对比证明不是拷贝损坏，是**副本本身就没有**。
- **处理**: `VCMIDirsXDG` 类内补 `libraryName() { return "lib" + basename + ".so"; }` + `libraryPath() { return "."; }`（与 VCMIDirsWIN32 ML 便携口径一致，L208 实证 WIN32 版 libraryPath 也是 "."）。
- **教训**: ① 重建编译遇 C++ 报错，**第一怀疑不是"代码有 bug"而是"副本缺本地补丁"**——历史补丁可查 `docs/服务器知识库.md` 同步台账 + `py/patch_passable_0917.py` 先例；② 补丁一律写成幂等脚本落 py/ 目录（可重放、可审计），本次 4 个补丁全部按此模式；③ 同类风险还没排完：可能仍有 WSL 侧独有改动未回推，后续编译/运行报错优先走此排查路径。
- **关联**: #44/#269（三份源码不同步老问题）/ #273/#274（同批补丁）/ `py/patch_passable_0917.py`（strategic_state.cpp passable 补丁，先例）

#### #273 GameEngine.cpp 死锁诊断打点用 Win32 API 无平台 guard (09-19 重建踩) — ✅ 已修（patch_gameengine_0919.py）

- **状态**: ✅ 已修
- **现象**: 编译 client 至 97% 报 `GetCurrentThreadId was not declared in this scope`（GameEngine.cpp L27/34/43）。
- **根因**: 09-10 死锁诊断补丁给 `GameEngine::LoggingMutex` 加 mutex 打点，直接用 `GetCurrentThreadId()`（Win32 API）+ 无 `#ifdef` 平台保护——当时显然只在 Windows 侧编过，原 WSL 树应有平台适配补丁（副本缺失，同 #272 家族）。
- **处理**: 包一层 `_dbg_tid()`：Win32 分支保留原 API，Linux 分支 `syscall(SYS_gettid)`（语义等价：内核线程 id，日志排障口径不变）。
- **教训**: ① 跨平台项目里**任何平台专用 API 必须当场包抽象层**，"以后再说"=给重建埋雷；② 死锁诊断打点保留（stderr [MUTEX] 行），Linux 侧同样有死锁排查价值。
- **关联**: #272（副本缺补丁家族）/ 知识库 09-10 死锁诊断章

#### #274 v13 GLOBAL_ENCODING 缺 BATTLE_ROUND 条目：types.h 11 项 vs constants.h 10 条 → static_assert `Found uninitialized elements` (09-19 重建踩，#37 的重演) — ✅ 已修（patch_schema13_battleround_0919.py）

- **状态**: ✅ 已修（编译期 static_assert 全绿；OBS 冻结口径未动）
- **现象**: vcmiclientcommon 编过之后，ML 目标编 mlclient 时炸 `AI/MMAI/schema/v13/constants.h:283/286: static assertion failed: Found uninitialized elements / Found wrong element at this index`。
- **根因**: v13 `types.h` 的 `GlobalAttribute` 枚举有 **BATTLE_ROUND（11 项，index 1）**，但 `constants.h` 的 `GLOBAL_ENCODING` 表只有 **10 条**（BATTLE_SIDE 直接跳 BATTLE_SIDE_ACTIVE_PLAYER）——`UninitializedEncodingAttributes` 按枚举 `_count` 遍历 `.at(i)`，末位越界/错位 → 编译期断言双杀。**这正是踩坑 #37（BATTLE_SIDE vs BATTLE_ROUND schema 版本冲突）的延续**：服务器知识库当年记录的修复动作"补 BATTLE_ROUND 到 GLOBAL_ENCODING"补在了原 WSL vcmi-native 侧，D 盘副本的 constants.h 没带出来。md5 对比再次确认是副本缺补丁（同 #272 家族），不是拷贝损坏。
- **处理**: 按 **v14 同位置先例**（v14 constants.h L182-184 带注释："LS is correct encoding but since it replaces BATTLE_SIDE ... use LE to keep the dimensions unchanged"）在 BATTLE_SIDE 之后插入 `E5(X::GA::BATTLE_ROUND, X::LE, MAX_ROUNDS + 1)`（v13 已有 `MAX_ROUNDS=30` 常量）。编译过 = schema 自洽。
- **教训**: ① **types.h 与 constants.h 是必须成对同步的一对文件**——同一段历史在 #37（运行时 core dump 风险）和本次（编译期炸）栽了两次；② v14/v15 是 v13 的后继版本，**补缺失内容先查后继版本同位置写法**（语义与维度注释都在）；③ 编译期 static_assert 是 schema 冻结的守护神——它能炸恰好证明 OBS 编码一致性有人盯着。
- **关联**: #37（BATTLE_SIDE vs BATTLE_ROUND 初代）/ #272（副本缺补丁家族）/ 服务器知识库「同步 v13 schema + 补 BATTLE_ROUND」条目 / `py/patch_schema13_battleround_0919.py`

#### #275 wsl.exe 会话回收 SIGHUP 全灭 nohup 后台编译任务 (09-19 重建踩) — ✅ 已修（长任务一律 systemd-run）

- **状态**: ✅ 已修（编译/下载全部改 systemd-run 托管）
- **现象**: `wsl bash -c "... nohup cmake --build ... &"` 命令本身退出后，后台编译在 ~15% 处全灭：`gmake[3]: ... Hangup` ×N + `SIGHUP`。free 显示内存充裕（非 OOM，dmesg 无 oom-kill）。
- **根因**: blocking=false 的 RunCommand 结束 → wsl.exe 客户端退出 → WSL 回收启动会话 → **整个进程组收 SIGHUP**。nohup 只对"启动时已是后台且 stdin 脱离"的进程免疫 SIGHUP 的默认动作，但 make 的并行子进程树在会话 leader 消失时仍被成组带走（Hangup 语义）。同窗口期老 pip 进程（pts/0 残留会话）侥幸存活，具有迷惑性。
- **处理**: 长任务一律 **system 级 transient unit** 托管：`wsl -u root systemd-run --unit=<名> --collect bash -c '... > /tmp/xx.log 2>&1'`。root 免密通道（项目规则）+ 日志落文件 + journalctl 可查 + 与 wsl.exe 会话生死完全解耦。本次编译（vcmi-build919×3 轮）与 pip 安装（pip919）均靠它跑完。
- **教训**: ① **WSL 里"后台任务"只有两种活法：systemd-run 托管，或 keepalive 会话在挂**——nohup/setsid 在 wsl.exe 会话回收面前不可靠；② --unit 命名带日期（919）便于 journalctl 定位；③ 与 #201/#267 的 keepalive 体系互补：unit 管"活"，keepalive 管"VM 不关"。
- **关联**: #201（system unit 训练架构，同一哲学）/ #267（keepalive 手工纪律）/ #114（idle shutdown）

#### #276 Windows→wsl bash -c 嵌套引号失守：heredoc/内联 python 一律传不过去 (09-19 重建踩) — ✅ 已修（写脚本落 py/ 再执行）

- **状态**: ✅ 已修（流程性规避）
- **现象**: `wsl bash -c "python3 - <<'EOF' ... EOF"` 与 `python -c 'print("x")'` 两类命令，PowerShell→wsl.exe→bash 三层引号转义后被破坏：heredoc 定界符丢失（`unterminated triple-quoted string`）、`\"` 变形（`unexpected EOF while looking for matching quote`）。同一命令在纯 bash 里完全正常。
- **根因**: PowerShell 对 `\"` 与 `$` 的预处理 + wsl.exe 参数再分片，多层叠加后 bash 收到的已经不是原文本。
- **处理**: **跨层传复杂脚本 = 写文件**。补丁类脚本落 `py/patch_*.py`（还白得幂等可重放与 git 留痕），一次性检查写临时 .py 或用 grep/sed 单行（无嵌套引号的简单命令可直传）。本次 `check_torch_cuda_0919.py` 即临时验证脚本落盘先例。
- **教训**: ① 三层引号转义不可调试也不可复现，**凡是带引号嵌套的 WSL 命令一律落文件**；② 与 #257（单引号失守）同家族，合并记忆：WSL 命令复杂度上限 = 无嵌套引号的单行。
- **关联**: #257（单引号失守扩展，同族）

#### #277 pip 装 CUDA 全家桶 45 分钟 0 进展卡死 (09-19 重建踩) — ✅ 已修（kill 重装 + --default-timeout=60）

- **状态**: ✅ 已修（重装 ~25 分钟装完 torch 2.14.0+cu130 全家桶）
- **现象**: `pip install torch onnxruntime numpy -i aliyun` 后台跑 45 分钟，pip 进程活着（Sl+ 状态），但 `pip list` 无 torch、`/tmp/pip-install-*` 全部 4KB——**零下载进展**。
- **根因**: 网络切换/360 重启窗口期建立的 HTTP 连接僵死，pip 无超时默认无限等。
- **处理**: kill 后 systemd-run 重跑 + `--default-timeout=60`；aliyun 源实测 ~720KB/s 稳定（triton 248MB、cublas 423MB 等大件逐个过）。torch CUDA 版必须装：训练 `DEVICE = "cuda" if available else "cpu"`，且 WSL GPU 直通验证 `/dev/dxg` + `/usr/lib/wsl/lib/libcuda.so` 存在 → RTX 3060 Laptop 识别成功。
- **教训**: ① **长下载挂后台必须验下载进展**（/tmp/pip-install-* 体积），进程存活 ≠ 在干活；② venv 重建后 torch 版本会漂移（本次 2.14.0+cu130 vs 原环境未知），checkpoint 的 state_dict 跨版本兼容没问题，但首次 resume 后要盯一个 batch 的 loss 量级是否正常。
- **关联**: #275（systemd-run 托管）/ #269（venv 丢失重建）

#### #277b 补记：keepalive 缺位期训练 unit 反复"Shutdown→冷启动"的日志形态识别 (09-19) — ✅ 识别（非故障）

- **状态**: ✅ 已识别；解法 = keepalive 手工拉起（#267 拍板纪律）
- **现象**: 重建收尾期 train_loop.log 连续 4 组 `Loaded train state (step=770300)` + `Shutdown signal received`——训练"反复重启"。
- **根因**: 重建期间无 keepalive 常驻：每条 wsl 命令会话结束 → VM idle shutdown → systemd 给 unit 发 SIGTERM（训练优雅存盘，**checkpoint 零损失**）→ 下条命令 VM 冷启动，unit disabled（restart 脚本只 start 不 enable）不自动拉起。
- **处理**: 保持手工纪律：先 `wsl.exe -d Ubuntu sleep infinity`（keepalive 常驻）再 `systemctl start homm3-train-v5`。**不要**为此把 unit 改 enabled（用户已拍板 VM 生命周期由 keepalive 控制）。
- **教训**: 日志形态学："Loaded+Shutdown 成对反复" = VM 生命周期问题，不是训练崩溃；训练崩溃的特征是 traceback/segfault 无 Shutdown 行。
- **关联**: #267（keepalive 纪律）/ #275（会话回收）/ #269

#### #278 `wsl --export` 进行中发行版被锁 → 所有 WSL 命令报 `Wsl/Service/CreateInstance/0x8000000d` (09-19 踩) — ✅ 已识别（等待导完自愈）

- **状态**: ✅ 已识别；处理 = 等导完（或杀 export 进程），**勿 shutdown 折腾**
- **现象**: WSL 命令全部失败（乱码 + `Wsl/Service/CreateInstance/0x8000000d`），`wsl --shutdown` 后依旧；但注册表 Lxss 项完好。
- **根因**: 另一进程在跑 `wsl.exe --export Ubuntu <tar>`（本例为 MeterSphere 相关脚本，08:19-08:23，tar 写到 17.8GB）——**export 期间发行版被锁定**，任何 CreateInstance（含新开 bash）被拒。
- **识别法**: `wsl -l -v` 看 STATE 列 = **`Exporting`** 即此坑；再 `Get-CimInstance Win32_Process -Filter "Name='wsl.exe'"` 看 `--export` 进程与目标路径确认来源。
- **教训**: ① WSL 全命令报错的排查顺序：`wsl -l -v` 看状态 → 注册表 → 服务重启，**Exporting/Converting 等过渡态先等再动**；② export 期间训练被 SIGTERM 优雅存盘（checkpoint 无损），但 unit 不会自动重启（disabled，见 #277b）。
- **关联**: #269（rootfs 事故）/ #277b（unit 不自启）/ #267（keepalive）

#### #279 根目录脚本"集体消失"虚惊：并行会话 `git mv` 到 py/ + export 锁定期的读取假象 (09-19 踩) — ✅ 已识别（零损失）

- **状态**: ✅ 已识别；文件从未丢失（git mv 保留 + WSL 侧读取假象）
- **现象**: 冒烟报 `can't open file '/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py': No such file or directory`；WSL 侧 `ls` 该目录只见部分文件；一度误判"Windows 侧文件被删"，险些启动大规模恢复。
- **根因（两层叠加）**:
  1. **真因**: 并行会话执行了 `git mv`——提交 `ab7518a`（09:18:38 "openspec 收口"）把根目录全部 .py **重命名到 py/**（`ep_runner_one.py => py/ep_runner_one.py | 0` 纯改名），且同步更新了 `train_wsl2_ppo_v2.py` 的 `RUNNER` 绝对路径与 unit ExecStart——**是规范落实（"代码文件保存到 /py"规则）不是丢失**；
  2. **放大器**: export 锁定期（#278）对 /mnt/d（drvfs 9p 缓存）的枚举/stat 结果不一致，造成"目录半空"的假象，误导排查方向。
- **识别法（对账三件套）**: ① Windows 侧 `Test-Path` 直接验证（绕开 WSL）② `git log --all --oneline -- <file>` 查该文件的全部历史提交 ③ `git status -s` 统计 D/deleted——若 status 无 D 而 Test-Path False → 文件是 untracked 或已被 mv，**先查 git log 再动手**。
- **教训**: ① 多会话并行操作同一仓库时，**任何"文件消失"先查 git log --all**——mv/改名在 log 里一眼可见（`=> py/xxx` 语法）；② drvfs 9p 缓存在系统繁忙时会给出不一致视图，单次 ls/stat 不可信，重挂载或换 Windows 侧验证；③ 本项目 git 仓库**未跟踪文件极多**（?? 数百个），"不在 git 里"≠"丢了"，git status 无 D 只说明丢的不是 tracked 文件。
- **关联**: #278（export 锁定）/ ab7518a（openspec 收口提交，含 mv）/ 用户规则"代码文件保存到 /py"

#### #280 ML 模式静态 AI 机制：STATIC_AI 隐藏宏 + ENABLE_ML/MMAI 互斥死锁 + MMAI 源码 8 处半成品修复 (09-19 重建踩，最大单坑) — ✅ 已修（patch_static_ai_0919.py + patch_mmai_build_0919.py）

- **状态**: ✅ 已修（冒烟全绿：3 步 r=+3.4 err=no → 训练恢复 step 累加正常）
- **现象链（按暴露顺序）**:
  1. 引擎报 `Cannot open dynamic library './AI/libMMAI.so'` → runNetwork 线程 THREW（blue=MMAI_RANDOM 无 AI 可用）；
  2. 补 `#define STATIC_AI` 后又暴露 AAI.h 声明的 `onNewSystemMessageReceived` 无实现 → `libvcmi.so: undefined symbol`；
  3. `static_assert(EI(GA::_count) == 10)` whistleblower（v13 global_stats 期望旧 10 项 schema）；
  4. AAI.cpp showGarrisonDialog 旧 4 参签名 vs AAI.h 新 6 参（customTitle）；
  5. router.cpp/BAI.cpp 多处 `ASSERT(shared_ptr)` 隐式转 bool 编译错 + `"...": = std::to_string()` 笔误；
  6. `MMAI::AAI::AAI` 嵌套命名空间全限定名修正（类在 namespace MMAI::AAI 内）。
- **根因（三层）**:
  1. **机制**: ENABLE_ML=ON 时 cmake 强制 `set(ENABLE_MMAI OFF)`（CMakeLists L352）→ MMAI 目标不编 → `libMMAI.so` 永不存在 → 但引擎仍按 dynlib 机制 dlopen → **死锁**。原 WSL 的解法是 `STATIC_AI` 宏（CDynLibHandler 走静态分支，按名字直接 `new MMAI::AAI::AAI`，免 dlopen）——此宏在 cmake 里无任何定义处，属**纯编译期隐藏配置**（原 WSL 构建命令注入，随 rootfs 丢失）；
  2. **互斥**: 解除 `set(ENABLE_MMAI OFF)` 让 MMAI OBJECT 库编出来（提供 AAI/Router 符号进 facade）；MMAI 需要 onnxruntime C++（装 /opt/onnxruntime 1.30.0；其 cmake config 有 lib64/include 打包 bug，`mv cmake cmake.bak` 走手工查找分支绕开）；
  3. **源码质量**: D 盘副本的 AI/MMAI 源码是**从未编译过的半成品**（原 WSL 运行时用的 `libMMAI.so` 是更早版本产物、09 月"同步"进 vcmi-native-build 的老 .so，与新源码不配套，且从未入 git，随 rootfs 丢失）。8 处修复全是签名漂移/隐式转换/笔误级。
- **修复清单（全部幂等脚本化）**: `py/patch_static_ai_0919.py`（#define STATIC_AI + 解除互斥）+ `py/patch_mmai_build_0919.py`（AAI 签名对齐 / router+BAI ASSERT / global_stats 11 项适配含 BATTLE_ROUND 动态 round / AAI+Router 补 onNewSystemMessageReceived 实现）。
- **教训**: ① **"libMMAI.so 文件"是旧机制残影，STATIC_AI 才是 ML 模式正解**——重建时优先恢复机制而非找文件；② cmake 互斥逻辑（ML→MMAI OFF）本身是 D 盘副本带的"上游态"，原 WSL 必然改过——#272 家族第 5 例；③ fork 的 MMAI 源码与引擎头长期漂移，**第一次编译它必然连续爆错**，按 error 逐个对齐签名即可，都是机械修复；④ static_assert whistleblower 是好事——它拦住了 global_stats 与 schema 的静默不一致。
- **关联**: #272-#274（副本缺补丁家族）/ #270（ENABLE_ML）/ #37（BATTLE_ROUND 初代）/ `py/patch_mmai_build_0919.py` / `/opt/onnxruntime`（ORT C++ 库，1.30.0）

#### #282 环境语义变更登记：STATIC_AI 激活蓝方对抗行为，red 死亡率 0%→63%，S2 基线作废重开 (09-19 用户拍板 B) — ✅ 已接受（新环境为今后标准）

- **状态**: ✅ 用户拍板接受新环境（blue 会移动/战斗/发展 = 训练方向期望）；S2 窗作废重开基线
- **现象（恢复段 19 局 vs 灾难前 S2 窗 164 局, `py/eval_resume_0919.py` + `py/eval_by_map_0919.py`）**:
  - red 死亡（HERO_DEATH, all-blocked x2 熔断）**0/164 局 → 12/19 局 (63%)**；
  - duel 三图 r 均值 **-173/-138/-108 → +50/+134/+153**——贴脸挂死僵局消失，改打真实胜负；
  - 非 duel 图 r 翻倍（36X36: 34→164 / 72X72_02: 78→257）；步数中位 96→61；
  - blue 英雄探针实测（`py/probe_blue_track_0919.py`，30 步）：blue adventure 前期仍站桩出生城，但**战斗参与活跃**（duel 出胜负 = blue 主动攻杀 red）。
- **根因**: #280 STATIC_AI 修复的**行为副作用**——原环境（老 rootfs .so）AI dlopen 全失败 → 守卫与 blue 战斗 = CEmptyAI 站桩/僵局；修复后 MMAI::BAI::Router 真实战斗 AI 生效，blue 会攻杀。red 模型（checkpoint 770300）未变，纯环境变更。
- **影响**: ① **S2 撤梯子窗基线失效**（avg_r/招兵/建设频率与旧环境不可比，"一次一轴"被动违反——环境变更与撤梯子叠加）→ S2 基线从恢复点重开计数 40 局再复查；② red 63% 死亡率 → 有效步数骤降（median 96→61），训练信号贫化，PPO 需要适应期；③ r 中位 150 为假象（死前探索/NK2 分堆积），评估勿直接读 r 均值。
- **决策记录**: 用户选择"B 接受新环境 + 逐局对比确认根因"（拒 A 复刻站桩回退）。观察项：若 red 死亡率持续 >50% 且学不到长程行为 → 议 blue 降级（MMAI_RANDOM 弱化参数）；`all-blocked 困死` 与 `真战死` 同罚 -50 的语义偏重与否，攒数据后再议。
- **教训**: ① **AI 行为变更 = 环境变更**，与改奖励/改图同级，必须独立窗口评估基线——本次 STATIC_AI 修复附带的环境变更差点被当成 S2 窗正常数据混入；② 对抗训练里 blue 强度是核心超参，blue 行为版本的每次变化都应登记（老 libMMAI.so 时代 vs STATIC_AI 新源码时代，从本条起为"新环境纪元"）；③ 评估先看结束原因分布（HERO_DEATH/ZOMBIE/满步占比），r 均值在环境变更时无意义。
- **关联**: #280（STATIC_AI 修复，本坑直接成因）/ #277b（日志形态）/ 工具 `py/eval_resume_0919.py` / `py/eval_by_map_0919.py` / `py/probe_blue_track_0919.py`

#### #283 62% 困死定性：all-blocked x2 熔断非战死，属 STATIC_AI 合理环境副作用，不触发 blue 降级 (09-19 S2 新基线 40 局收口) — ✅ 定性完成（蓝方围堵非过强）

- **状态**: ✅ 已定性（合理副作用，不触发降级；S2 新基线 40 局收口）
- **现象（恢复段 40 局，`py/death_by_segment_0919.py` + `py/eval_new_baseline_0919.py`）**:
  - HERO_DEATH **0/164（灾难前）→ 25/40（恢复段）= 62%**，全部 `[ZOMBIE] hero dead (all-blocked x2)` 罚 -50，分布全段均匀（局 01-10/11-20/21-30/31-40 各≈6 例）；
  - 关键矛盾点：**BHERO_CONTACT / BHERO_ATTACK / BHERO_SLAIN / startBattle 全 0**——红方英雄根本没进过战斗就被困死。
- **定性结论**:
  1. **困死 ≠ 战死**：62% 死亡率是蓝方会移动/围堵后把红方英雄卡死在角落（all-blocked x2 熔断），不是蓝方战斗强度把红方打残。BHERO_* 战斗事件归零是铁证——没有任何一次正式战斗发生，全是被围堵困死。
  2. **不触发 #282 观察项的 blue 降级**：#282 留的观察项是"red 死亡率持续 >50% 且**学不到长程行为** → 议 blue 降级（MMAI_RANDOM 弱化）"。但本定性指出根因在**蓝方围堵策略**而非**蓝方战斗强度**，blue 降级（弱化战力）无法对症解决"围堵"问题，且会削弱训练信号。用户拍板**不降级**。
  3. **62% 困死是合理训练信号**：新环境下 red 需要学会"突围"（不被围堵卡死），而非被动挨打。PPO 适应期内有效步数下降（median 96→72-94）属预期，待模型学会突围后步数会回升。
- **S2 新基线收口**：40 局已攒满（行 111328-112636），恢复段 19 局作废不纳入，本 40 局作为 S2 新基线正式生效。r 均值 153.8 / 中位 154.7 / 无负局 / 30 局 r≥100。duel 三图 r 全转正（139/146/148）。
- **教训**: ① **评估"死亡率"必须先看结束原因分布**——HERO_DEATH 行带 [ZOMBIE] all-blocked 标签就是困死而非战死，配 BHERO_* 战斗事件计数交叉验证（本例全 0 = 未进战斗）；② **观察项的触发条件要带"根因匹配"约束**——#282 观察项"死亡率>50% 才议降级"是必要条件非充分条件，需确认根因是"蓝方过强"才议降级，"蓝方围堵"则议红方突围能力，对策完全不同；③ **环境副作用定性要先于对策选择**——先定性（困死 vs 战死），再决定降级/接受/改训练信号，避免拿错对策。
- **关联**: #282（环境变更登记 + 观察项出处）/ #280（STATIC_AI 修复，根因）/ 工具 `py/death_by_segment_0919.py` / `py/eval_new_baseline_0919.py`

#### #284 attack_bypass 开 1 仍 0 触发 — 根因 B：蓝英雄 obs 外时 move_blue_hero_target 恒 False，贴脸强攻旁路从未进入 (09-19 冒烟实锤) — 🔄 绕过中

- **状态**: 🔄 绕过中（开 bypass 无效，需改 SCORE 选择器识别 obs 外蓝英雄，或改旁路触发条件不依赖 move_blue_hero_target）
- **现象**: 用户拍板"开 `--blue_hero_attack_bypass 1` + `--blue_hero_contact_d 2` + `--attack_f_min -1.0`"（L179 已改），停训跑冒烟 3 局 T06_72_02_duel 看 `[BHERO_ATTACK]` 触发率。结果 grep `[BHERO_ATTACK]`=0、`[ATK_DBG]`=0——开 bypass 后贴脸强攻旁路**从未进入**，`[HERO_DEATH]`=1（仍困死）。
- **根因**: attack_bypass 触发条件 L990 要 `move_blue_hero_target=True`（来自 SCORE pick 蓝英雄，L786），但困死局 SCORE `pick=blue_hero plen=0`（蓝英雄不在 obs 8 槽内 → plen=0），`move_blue_hero_target` 恒 False，旁路从未进入。开 bypass 对"蓝英雄 obs 外"的困死**完全无效**。三层根因中，战斗触发层（根因 A）只是表象，真正的阻塞在**目标选择层**（SCORE 选不出 obs 外蓝英雄）。
- **处理**: 冒烟实锤后停训（当前 inactive），keepalive 常驻。下一步需重新评估修复方向：① 改 SCORE 选择器，让它能识别 15×15 视野外的蓝英雄（需 obs 增强或旁路）；② 改攻击旁路触发条件，不依赖 `move_blue_hero_target`（直接按"贴脸蓝英雄坐标"判定，蓝英雄坐标从 blue_hero_id_target 或 live_slots 取，而非 SCORE pick）；③ 接受困死率现状，先恢复主训练攒局。
- **教训**: ① **开一个参数开关≠旁路真正被触发**——必须验证触发条件链最末端是否满足（本例 bypass=1 但 move_blue_hero_target=False，旁路 0 进入）；② **冒烟要带触发链路诊断**——`[ATK_DBG]` 全 0 说明连诊断行都没打印（旁路代码段根本没进），比 `[BHERO_ATTACK]`=0 信息更强；③ **obs 冻结约束下的目标选择盲区**——3464 obs 只编码 8 槽英雄，蓝英雄在视野外时 SCORE 自然选不到，这是 OBS 冻结的铁律副作用，扩展只能走预留位或旁路（terrain 走 terrain_grid.bin 同理）。
- **关联**: #283（困死定性，本条是其修复尝试失败）/ #282（环境变更，根因）/ `py/train_wsl2_ppo_v2.py` L179 / `py/smoke_attack_bypass_3ep.py` / `py/ep_runner_one.py` L990/L786

#### #285 战死 → ah=-1 → fallback=0 坐标错位连锁：假贴脸 d=0 / 假 BHERO_ATTACK / zombie 假判定 — **#283 困死定性推翻** (09-19 冒烟 traj 逐帧实锤) — ✅ 已修（ah=-1 立即终局）

- **状态**: ✅ 已修（`ep_runner_one.py` 记录段前插 ah=-1 立即终局 `[RED_DEAD]`+death_penalty+done；修复后 120 局 ZOMBIE=0）
- **现象**: FORCE 冒烟 3 局 `[BHERO_ATTACK]`=4 条（"133% 触发率"）但 3 局全 `[HERO_DEATH]` all-blocked。逐帧 dump traj obs（`/tmp/smoke_force_traj*.json`）实锤：step 33 红英雄 (8,8) 走 act=3 → **踩中立怪 → `BattleProcessor::startBattle bid=0` → `CGCreature::battleFinished winner=1` 战败被歼** → step 34 起 obs 英雄段重排（蓝英雄顶 slot0、ah=-1、passable 全 0）→ Python `ah = obs[3203] if obs[3203]>=0 else 0` fallback=0 → hx,hy 读到蓝英雄坐标 (66,66) → FORCE 段算出**假贴脸 d=0**（pw_self=pw_blue=1 同字段实锤）→ 连发假 BHERO_ATTACK → pas 全 0 → zombie_streak×2 → "all-blocked 困死"假象。
- **根因**: 战死不是终局信号——旧逻辑红英雄死后还跑 2+ 拍错位决策，把"战死"伪装成"困死"。**BHERO_ATTACK 冒烟"133% 触发率"全是假阳性**（含 pw_self=pw_blue 相等的铁证：同一 slot 字段读两次）。
- **#283 推翻（09-19 修复后 120 局重统计）**: 困死(HERO_DEATH/ZOMBIE)=**0/120**、战死(RED_DEAD)=**72/120=60%**——旧"62% all-blocked 困死"全部是战死误判（62%↔60% 完美互证），"蓝方围堵"叙事不成立，**核心问题从来是打不过中立怪乱踩**。
- **修复（`ep_runner_one.py` 记录段前）**: `if int(nobs[3203])<0 and not (done or trunc): r+=death_penalty; done=True; print([RED_DEAD])`——语义分干净：ah=-1=战死终局 / ah>=0+pas 全0×2=真困死（zombie 保留给后者）。修复后冒烟：假 HERO_DEATH 3/3→0/3、假攻击 4→0、RED_DEAD 3/3 正确。
- **教训**: ① **死亡必须立即终局**——英雄死后 obs 编码重排（heroes 段稳定排序，蓝英雄顶 slot0），继续采样全是错位垃圾帧污染 buffer；② **冒烟"触发率"要先验真**——d=0 且 pw_self=pw_blue 是"读到自己人"的指纹；③ **traj JSON 逐帧 dump 是 obs 疑云的终极手段**（np.asarray(obs,dtype=float32).astype(int32) 按偏移切片，比 grep 日志快准）；④ **结局对了不代表链路对**——HERO_DEATH -50 罚了但过程全是假攻击垃圾帧。
- **关联**: #283（被本条推翻）/ #284（假贴脸的表层）/ `py/ep_runner_one.py` L1607-1614（RED_DEAD）/ `py/smoke_attack_bypass_3ep.py` / 知识库 09-19「根因C'」章

#### #286 守卫战力 half-self 拍脑袋近似 → F 恒正 → 打不过也踩 → 战死 60% (09-19 A3 战力闸根治) — ✅ 已修

- **状态**: ✅ 已修（A3 四改动：真实战力 + BFS 避怪 + t[6] 反解 + F 硬闸，09-19 部署攒局）
- **现象**: 修复后 120 局战死 60%（duel 图 65%），英雄 act=3 走格踩中立怪 `MapObjectVisitQuery → startBattle` 战败即死（#285）。
- **根因（双层）**: ① **target_scorer `candidate_power_c` half-self 近似**——守卫 pc = power_self×0.5（"无静态读值"注释实为拍脑袋）→ F 恒正 → SCORE 认为怪都能打；② **passable 新口径（#247 方案甲）副作用**——怪格 blocked&&visitable=可走（为了能打守卫），BFS 导航会规划**穿怪格路径** → 路过误踩。
- **数据可用性讽刺**: 真实战力数据一直都在——`target_list[i][6]`=资源目标附带守卫战力 log2（C++ `fill_target_list` guardingCreatures×calc_army_power，strategic_state.cpp L226-238）、`local_tiles[2]`=15×15 邻域怪战力 log2、vmap objects.json monster 带 subtype+amount——Python 侧从没用过。
- **修复（A3 四改动，全 Python 旁路零重编）**: ① `get_guards` 5 元组带真实战力 AIValue×amount（peasant=20/archer=67/swordsman=119，训练图怪仅此 3 种，未知回退 150）；② SCORE BFS 避怪（非守卫目标时怪格入 blocked，目标格豁免）；③ `candidate_power_c` 重写（守卫直读 + 资源堆 t[6] 反解 2^gp-1，half-self 废弃）；④ F 硬闸 F<-0.3 不入池（蓝英雄/蓝城豁免）。自测：守卫400 vs 英雄100 → F=-0.95 剔除 ✓。
- **教训**: ① **拍脑袋近似要标注到期日**——half-self 上了线就没人记得它是猜的；② **战力类近似先查 C++ 侧有没有真值**——t[6]/local_tiles ch2 都是现成的；③ **开一扇门（passable 放开怪格）要查谁会从门里走进来**（BFS 穿怪）；④ **判据设计**：战死率 <35% / duel 净胜率 >0% / 守卫胜率不塌（T7.8）。
- **关联**: #285（战死终局链）/ #283（被推翻的旧定性）/ `py/ep_runner_one.py` L218-237/L1098-1102 / `py/target_scorer.py` L106-125/L294-297 / T7.8 观察窗

#### #287 F 闸 self 战力读错字段：obs[base+10] 是英雄**法力属性**非军队战力，注释 "total_power" 系误导 (09-19 日志分析实锤) — ✅ 已修（军队战力公式）

- **状态**: ✅ 已修（ep_runner L766 + BHERO_ATTACK 段两处换 army_count×AIValue 公式）
- **现象**: A3 初版上线后 14 局战死 86%、guard_pick=0、fought_won=0——比不改还差。SCORE 蓝英雄 F 恒 -0.32。
- **根因**: `power_self = int(obs[base + 10])` 注释写 "active hero total_power (H_F_POW=10)"——**错**。C++ `StrategicHero` 第 10 字段 = 英雄四维的 **Power 属性（法力/咒力，初始≈1）**；真实军队战力 `total_power` 在 `name[32]` 之后（v3 扩展），**26-stride 之外，obs 未编码**。F 闸拿法力(1)比军队(400+) → F 必大负 → A3 硬闸全剔 → 打得过的怪也不打。
- **修复**: 军队战力复用 L1492 兵力公式 `Σ army_count[field 15-21] × [10,40,120,350,900,1600,2500]`（VCMI AI value 阶梯）。traj 验证：旧读法恒 1，新读法 5250（15×tier3）✓。BHERO_ATTACK 段 pw_self/pw_blue 同步修（F 打印真值）。
- **教训**: ① **字段语义以 C++ struct 定义为准，别信 Python 侧注释**（误导性注释存活 3 周没被发现，因为 F 是软降权时错误无害，A3 硬闸一上立刻爆发——**软闸掩盖字段错误，硬闸放大暴露**）；② "改完行为反而变差"≠改错方向，可能是**堵住了旧的隐性作弊/漏洞**后的真实现状。
- **关联**: #286（A3 战力闸）/ `py/ep_runner_one.py` L766-777 / L1053-1072 / `py/ep_runner_one.py` L1492-1500（军队公式出处）

#### #288 mask 与 BFS 避怪打架：贴脸目标方向被 mask → 3/7 振荡刷负分 (r=-809 实锤) + 微负蓝英雄直奔被反杀 (10/10 死局同构) — 🔄 修复上线观察中

- **状态**: 🔄 修复上线观察中（贴脸目标豁免 + 蓝英雄硬闸 -0.1 + f_min=0 三处，满窗 100 局验证）
- **现象一（振荡大负局）**: r=-809 局：step 182 起 SCORE 恒 pick 邻格资源 plen=1 但到不了，act 3/7 交替 150+ 步，250 步跑满 -809。mask 豁免2 后仍现 -735.7×2/-488/-437 等 -300+ 大负局 12 个/58 局。
- **根因一**: BFS 避怪"目标格豁免"规划进格路径（首步邻格是怪格），**mask 又屏蔽该方向** → BFS 说走、mask 说不行 → 模型在剩余方向振荡，act_loop(-1/步) + cycle(-3/次) + nk2 shaping 负值累积刷到 -700 量级。**惩罚体系把"合法绕怪绕行"误杀**（#195 "BFS plen 持续下降=合法绕行不误杀" 教训的 act_loop 版重演）。
- **根因二（微负送死）**: 10/10 死局全同构——`SCORE pick blue_hero F=-0.20`（微负，**刚好穿过 -0.3 硬闸与 f_min=-0.2 边界**）→ 直奔 → 贴脸 d=2（ATK_DBG 132→133→134: d=6→4→2 实录）→ **蓝英雄主动进攻**（MMAI 攻击移动）→ 红败。微负 = 蓝方仅略强，正确行为是先攒兵变强再 capture。
- **修复（三处）**: ① mask 豁免2：贴脸目标（切比雪夫=1）方向不 mask（F 硬闸已保证打得过才 pick，BFS 豁免是有意的）；② SCORE 蓝英雄硬闸 -0.3 → **-0.1**（微负不 pick，空转 250 步好过送死 -50）；③ f_min -0.2 → **0.0**（正 F 才攻）。
- **已知残留**: 贪心回退（全图 BFS 不可达时 pas[d] 直选）未避怪；**act_loop/cycle 惩罚对绕怪合法绕行的误杀**未修（下一轴候选：惩罚前查 BFS plen 是否下降，合法绕行不罚）；ch2 只含资源守护怪不含游荡怪（ch1 对象类型层可补，Obj::MONSTER 判定备用）。
- **教训**: ① **每修一处会顶出新形态**（战死→振荡），约束系统调参要一次攒够样本再动，4 局小样本会骗人（25%→72% 假波动）；② **阈值卡边界的参数最危险**（-0.2 闸 vs F=-0.20 恰好放行），阈值应留 2 倍余量；③ 大负局的 reward 拆解用 traj["rew"] 逐帧 dump 最快（75 帧 -1 = act_loop 刷屏指纹）。
- **关联**: #286/#287 / `py/ep_runner_one.py` L591-618（mask+豁免2）/ `py/target_scorer.py` L294-303（硬闸）/ `py/train_wsl2_ppo_v2.py` L179-183（f_min=0）/ T7.8 判据③（大负局）

#### #281 rootfs 重置连带丢 .ssh 与 .git 元数据 — WSL GitHub SSH + vcmi-native git 全修复，513 未入库战略层增量入 git (09-19) — ✅ 已修

- **状态**: ✅ 已修（SSH key 恢复 + vcmi-native git 重建 + 513 未跟踪增量 commit d62071da8a 并推 D 盘镜像仓；训练进程全程零影响）
- **现象**: ① `/home/administrator/.ssh` 整个被 rootfs 重置丢掉 → WSL 内所有 GitHub SSH 操作 `Permission denied (publickey)`，gym 仓 fetch/push 不可用（HTTPS 通但 origin 配的是 SSH）；② `/home/administrator/vcmi-native/.git` 是坏 submodule 指针（`gitdir: ../.git/modules/vcmi`，父 `.git/modules` 随重置消失）→ `fatal: not a git repository`，工作区文件在但 git 历史断了。
- **根因**: .ssh 密钥与 .git 元数据全在 rootfs（易失层）；幸而 #269 当晚已建 D 盘 bare 镜像仓 `D:\Bigdata\git-mirrors\vcmi-native.git`（三件套①），修复材料齐全。
- **处理（顺序）**: ① 从 Windows `C:\Users\Administrator\.ssh` 拷回 `id_ed25519`(+pub) 到 `/home/administrator/.ssh` 与 `/root/.ssh`（GitHub 注册的是 ed25519，rsa 那把被拒）；写 `~/.ssh/config`（administrator+root 两份：`Host github.com / IdentityFile ~/.ssh/id_ed25519 / IdentitiesOnly yes`）→ `ssh -T git@github.com` 认证通过；② `git clone -b mmai-ml-wsl /mnt/d/Bigdata/git-mirrors/vcmi-native.git` 取健康 .git，旧坏目录改名留底后把新 .git 接回原路径（工作区 6092 文件零丢失），`chown administrator .git`；③ **关键发现**：git 快照 `30f62b8` 只到 BAI/v13，工作树另有 513 个未跟踪文件（BAI/v14 + schema/v14 + agent-v15 战略层增量，08-29 快照后未入库，正是"最大潜在丢失"那块）→ 保护性 commit `d62071da8a` + 推回 D 盘镜像仓；2821 个 `M` 抽样证实全部 CRLF↔LF 行尾噪音（删行尾后 diff 为空），**不提交不污染**；④ 全程只动目录名与 .git 元数据，.so/训练进程（当时 ep_runner_one.py 在跑）零影响。
- **教训**: ① rootfs 重置丢的不只是"工件"，**.ssh 身份与 .git 元数据同属易失层**——重装后必须逐仓验 git 可用性，不能只看文件在不在；② git status 里 2821 个 `M` 不代表 2821 处内容改动——CRLF 全树噪音先抽样删行尾对比，**别把行尾翻转混进 commit**；③ bare 镜像仓是首选修复材料：WSL git 坏了可离线从 `/mnt/d` 重新克隆；④ .git 属主=administrator 的仓 root 直接跑 git 会 dubious ownership——`safe.directory` 或改用 administrator 身份；⑤ 9p 挂载（/mnt/d）属 root，D 盘镜像仓的 push 要用 root+safe.directory，WSL 仓的操作要用 administrator。
- **关联**: #269（rootfs 重置事故，本条是其连带修复）/ #277b（keepalive 手工纪律，本窗口期训练存活前提）/ 知识库 09-19「网络恢复窗口」章

#### #287 批跑管线 walrus 作用域 bug — 验收后 `steps_done` 未定义致 NameError 隐患 (09-19 全量批跑前修复) — ✅ 已修

- **状态**: ✅ 已修（`py/h3m_batch_pipeline.py`：`entry["verify_steps"] = _extract_steps(detail)`，py_compile 全绿）
- **现象**: 全量批跑启动前复查管线代码，发现验收成功分支 `entry["verify_steps"] = steps_done if (steps_done := _extract_steps(detail)) else 0` 里 `steps_done` 仅在 walrus 表达式内赋值，该表达式之后的代码（skip 判定、resume-fail 逻辑）若引用 `steps_done` 则 NameError；且 walrus 后接 `else 0` 使 0 值被静默吞掉，无法区分"真的 0 步"与"提取失败"。
- **根因**: walrus `:=` 的作用域就是当前表达式所在语句——赋值在 if 条件里完成，语句结束后变量**并不保证**在后续作用域可见（局部函数/分支场景下直接 NameError）；`steps_done if ... else 0` 写法把提取值与失败兜底混在一起，破坏了"report 条目必须如实记录 verify_steps"的断点续跑语义。
- **处理**: ① 验收分支改为独立语句 `entry["verify_steps"] = _extract_steps(detail)`（提取失败返回 0 但语义清晰：提取失败 = 早期死亡 = FAIL，不会被误 skip）；② 新增 `--resume-fail` 开关：默认信任旧 PASS 条目（100 步时代产物）不重验，开 `--resume-fail` 时只重验 report 中 fail/convert_fail 且无池文件的条目；③ skip 判定条件改为 `verify_steps is None`（旧条目无此字段）兼容 100 步时代 report。
- **教训**: ① **walrus 别跨语句引用**——赋值只在表达式内有效，后续代码引用是运行时炸雷；② 断点续跑的 report 字段要有"显式空值"语义（None=历史条目无此字段 vs 0=提取到 0 步），用 is None 判定而非 == 0；③ 旧格式 PASS 条目与新判据（250 步）冲突时，"默认信任 + 显式开关重验"比"全量重验"省十几个小时，但必须把开关写进文档（本条 + 任务清单 WIN-4）。
- **关联**: 知识库 09-19「H3M 全量批跑」章 / `py/h3m_batch_pipeline.py` / `py/run_h3m_batch.sh`

#### #288 _pipeline_report.json 键值契约不统一 — 键=文件名、值无 "h3m" 字段，外部脚本易 KeyError (09-19 批跑监控实锤) — ✅ 已约定（监控脚本统一读键名）

- **状态**: ✅ 已约定（监控/统计脚本一律 `for h3m_name, st in report.items()` 读键名，勿取 `st["h3m"]`）
- **现象**: 写批跑进度统计一行式脚本时 `v["h3m"]` 直接 KeyError——report 是 `dict[h3m文件名, {status, verify_steps, ...}]`，条目值里**没有** "h3m" 字段，文件名本身就是键。
- **根因**: 管线写 report 时 `report[h3m.name] = entry`，entry 内只存 status/verify/verify_steps/convert/strip 结果，没回写文件名；读 report 的脚本若按"值里有名字"的直觉写 `v["h3m"]` 就挂。
- **处理**: 监控口径固化：① PASS/FAIL 计数 = `sum(1 for v in report.values() if v.get("status")=="PASS")`；② 图名 = 键本身 `report.keys()`；③ 进行中 = `grep "^\[" h3m_batch_run.log | tail`（日志行头 `[N/159] 文件名 → out.vmap`）。
- **教训**: ① 共享 JSON report 要有**显式键值契约注释**（管线文件 docstring 写明"键=H3M 文件名，值不含 h3m 字段"），否则每个读脚本各猜一次；② `dict` 同时承担"文件名索引 + 条目数据"时，宁可冗余存一份 name 在值里也不省那几十字节——读侧的健壮性远比写侧省空间重要。
- **关联**: #287（同文件同修复窗）/ 知识库 09-19「H3M 全量批跑」章（跟踪命令）/ `py/h3m_batch_pipeline.py`

#### #289 SOD 自定义英雄头段解析缺失 — 9/159 官方图 parse_header 抛 "自定义英雄 N 暂不支持" (09-19 普查发现) — ⚠️ 待查（不阻塞批跑：失败图转换仍走 R2v2 重配+验收兜底，只是无类型统计）

- **状态**: ⚠️ 待查（h3m_tool 未实现 disposed/custom hero 段；补法明确=读 156 个英雄槽位）
- **现象**: `py/h3m_type_survey.py` 全量普查 159 图，9 张 SOD 图 parse_header 失败：A Viking We Shall Go(×2) / Battle of the Sexes(×2) / Last Chance(×2) / Marshland Menace / Resource War(×2)，报错 `自定义英雄 N 暂不支持`。
- **根因**: SOD 的 H3M 头段带"自定义英雄"（disposed hero / custom hero）标志位，英雄数据段从 2 槽（默认红/蓝英雄）膨胀为 156 个英雄槽位（每玩家最多 78 英雄×2），h3m_tool.py 的 parse_header 遇到该标志位直接抛 NotImplementedError 式分支。
- **处理**: 暂不修（普查器已把这 9 图列入 parse_fail 清单跳过，不影响其余 150 图统计；批跑管线走的是 R2v2 智能重配——重配时 aiSlot 恒 blue + 他色中立化 + 英雄删除，**不依赖** 自定义英雄头段解析，9 张图转换验证正常进行）。修的话：在 parse_header 自定义英雄分支读 156 槽位（每槽位 80 字节，含 name/class/level 等），约 30 行。
- **教训**: ① 普查器（只读统计）与批跑管线（转换+验收）对解析器的依赖程度不同——统计器挂 9/159 只丢统计维度，管线挂才丢图；② 失败清单要进产物 JSON（parse_fail 字段）留档，别静默吞异常；③ SOD 9 张全在 C 盘源 `vcmi/data/Maps`，D 盘批跑用的同名文件转换无问题（管线不读该头段）。
- **关联**: 知识库 09-19「H3M 全量批跑」章（parse_fail 9 张清单）/ `scripts/h3m_tool.py` / `py/h3m_type_survey.json`

#### #288 ps1 被 AI 编辑工具保存后 UTF-8 BOM 丢失 → PS 5.1 按 ANSI 解析 → 中文注释字节错位破坏代码结构 → RED 阈值条件意外为真 (09-21 实锤) — ✅ 已修（补 BOM + 纪律固化）

- **状态**: ✅ 已修（补回 BOM 后复测通过）；**纪律：任何工具编辑含中文的 ps1 后必须验证首 3 字节 = 239,187,191（EF BB BF）**
- **现象**: `py/train_health_monitor.ps1` 被 SearchReplace 编辑后运行，`log_age=19s`（训练健康）却触发 `TRAIN RED "0.3 分钟无更新"`——`if ($age.TotalMinutes -ge 20)` 条件单独实测恒 False，逻辑本身没坏。
- **根因**: 原文件带 UTF-8 BOM，编辑工具保存时**静默丢弃 BOM**。Windows PowerShell 5.1 对无 BOM 文件按 ANSI/GBK 解析：UTF-8 中文（3 字节/字）被按 GBK（2 字节/字）错误配对——不只是字符串乱码，字节流错位传导会**破坏代码解析结构**（本次表现为 stale 红警分支被意外执行）。条件表达式全 ASCII（`-ge 20`）不受影响，单独测试恒 False——**症状与根因分离，极难定位**。
- **处理**: 读首 3 字节确认无 BOM → `[IO.File]::WriteAllBytes($p, ([byte[]](239,187,191) + $b))` 补回 → 复测 RED 误报消失、中文正常。**注意：每次编辑后 BOM 都可能再丢（本次会话内丢了两次），必须编辑后即验**。
- **教训**: ① ps1 含中文 = BOM 是文件格式的一部分，不是可有可无的元数据；② "条件为 False 却执行了"这类灵异 bug，先查文件编码再怀疑逻辑；③ 校验命令一行：`$b=[IO.File]::ReadAllBytes('x.ps1'); $b[0] -eq 239`；④ 混合 ASCII/中文的 ps1 里，乱码输出（如 `鍒嗛挓`）本身就是 BOM 丢失的强信号。
- **关联**: `py/train_health_monitor.ps1` / 知识库 09-20/21 章（JEV 工具链）

#### #289 h3m2vmap 与 libvcmi.so 符号布局脱钩：lib 重编后转换器二进制未重链 → 17 张图全部 convert_fail (09-21 定性修复) — ✅ 已修（cmake --build 重链）

- **状态**: ✅ 已修（`cmake --build tools/h3m2vmap/build --target h3m2vmap` 仅 Linking 步骤秒级完成）；衍生坑见 #290
- **现象**: 批转 report 里 17 张图 convert_fail，err 全部相同：``Symbol `_ZN13GameConstants12VCMI_VERSIONE' has different size in shared object, consider re-linking``——进程启动即死，转换逻辑一步未跑。
- **根因**: **时间戳铁证**：`tools/h3m2vmap/build/h3m2vmap` = 09-19 07:44，`rel/bin/libvcmi.so` = 09-19 09:46（#280 STATIC_AI 修复重建）。h3m2vmap 链接的是旧符号布局的 libvcmi，运行时 dlopen 加载新 .so → 符号尺寸校验失败。lib 重编后**必须重链所有链接它的可执行文件**，这与 ".so 多副本部署同步"是同一纪律的链接期版本。
- **处理**: 重链后冒烟对照——原 PASS 图（Faeries）`ROUNDTRIP OK` 无损 ✅；原 convert_fail 图从"启动即死"变为"解析+规则应用正常"（72x72/2923 对象解析成功）。重链不触发重编译，训练在跑时执行无 CPU 冲击。
- **教训**: ① convert_fail 的 err 若**全部相同** = 系统性问题（工具/环境），不是图的问题——归因脚本 `py/h3m_fail_triage.py` 已内置同 err 去重（一次 JEV 调用定性全组）；② `ls -la --time-style=+%F_%T` 对比二进制与 .so 时间戳是脱钩问题的一行定位法；③ libvcmi.so 重编的 SOP 应追加"重链 h3m2vmap"步骤（与 VCMI 铁律"vcmi-native 双目录 cp 同步"同列）。
- **关联**: #290（重链暴露的段错误，衍生坑）/ 知识库 09-20/21 章 / `py/h3m_batch_pipeline.py`（convert_fail 记录）

#### #290 h3m2vmap 重链后新暴露：B3 规则应用阶段段错误，原 convert_fail 图群全军覆没 (09-21 冒烟实锤) — ✅ 已修（pool 英雄 null 槽，vcmi-native 41a99cd52c）

- **状态**: ✅ 已修（09-21 深夜 gdb 定位 + main.cpp 修复 + Battle of the Sexes 全链验证 667s 卡死 → 24s 正常跑）
- **现象**: 重链后冒烟对照：Faeries（原 PASS，72x72/1545 对象）转换成功 `ROUNDTRIP OK`；**Dragon Orb（72x72/2923 对象）与 Back For Revenge（144x144/5318 对象）均在 `applying B3 rules R1=0 R2=1 R3=1.00 R4=1 R5=0 R6=1 R7=1` 后 `dumped core`**——解析正常、规则参数打印正常，死在规则应用中途。
- **根因**（09-21 gdb 实锤）: R2v2 重配的 compactNullSlots 压缩后，hero pool 占位英雄走**虚拟 ID**（objects 向量之外），但 main.cpp 尾部又 `map.objects.push_back(nullptr)` 把 null 塞回向量 → 规则应用阶段 R2v2 调 `CMap::removeObject` → 重编号循环 `(*iter)->id` 解引用 null 槽（CMap.cpp:691）→ segfault。非尺寸/非图内容问题——**任何带多余英雄（>2）的官方图必炸**。
- **处理**: main.cpp 删 push_back(nullptr)，pool 英雄只分配虚拟 ID 不进 objects 向量（`h->id = ObjectInstanceID(map.objects.size() + poolCount)`）。修复后 Battle of the Sexes（108x108/3297 对象，此前 3 连败）转换 + sanitize + 250 步 verify 全链通过。
- **教训**: ① 修好"启动即死"的表层 bug 后**必须立即冒烟深路径**——底层 bug 会被表层 bug 完全遮蔽（本条在 #289 修复前不可见）；② 对照冒烟（原 PASS 图 + 原 FAIL 图各一）是区分"回归 vs 遗留"的最快手段；③ **并行会话改同一文件必先对齐**——本条修复时曾与并行 compactNullSlots 方案冲突（我加的 null 压缩块 vs 对方虚拟 ID 方案），回滚我方块后修对方方案的 push_back 漏洞收口。
- **关联**: #289（前置修复，本条因其暴露）/ #291（批转重启续跑）/ vcmi-native commit `41a99cd52c` / 知识库 09-20/21 章 / 任务清单 WIN-4 状态栏

#### #291 批转进程目录快照失效：启动后源文件被重命名 → 持有失效名列表逐张 cannot open 白跑 (09-21 实锤) — ✅ 已修（杀进程重启断点续跑）

- **状态**: ✅ 已修（04:50 杀 177204/177222 → run_h3m_batch.sh 重启，新枚举全小写名，PASS 38 skip + fail 重验）
- **现象**: 批转 03:53 启动后推进到 [52/159] 起连续 `convert: cannot open or empty: .../data/Maps/Golems Aplenty Allied.h3m`——但目录里该文件实际存在（小写名 `golems aplenty allied.h3m`）。3 试重试全秒败，每张浪费 ~6s 且 report 记 convert_fail 污染。
- **根因**: 管线 `main()` 开头一次性 `sorted(Path(H3M_DIR).glob("*.h3m"))` 枚举**目录快照**；03:53 启动时目录还有大写名，小写化（`py/lowercase_h3m_names.sh`，VFS 大小写钉 #285 系）在批转启动**之后**生效 → 进程持有已消失的旧名 → `cannot open`。**长跑批处理的目录快照与运行时文件系统脱节**。
- **处理**: kill wrapper+python（**先杀 wrapper** run_h3m_batch.sh 再杀 python，顺序反了 wrapper 会走 [3/3] 自动拉起训练）→ 直接重跑 `run_h3m_batch.sh 250`：新进程重新枚举小写名；PASS 判定 `status==PASS and exists(final_path)` 不受旧名 convert_fail 污染（旧名键是垃圾数据但无害），resume-fail 自动重验。
- **教训**: ① **文件系统重命名类操作必须排在长跑批处理启动之前**，或在批处理每张图处理前重新 `os.path.exists(h3m)` 快速失败（ENOENT 类不可重试错误不该吃 3 试重试）；② 批转 FAIL err 全相同（cannot open）= 系统性问题（#289 同款判据：同 err 去重定性）；③ "cannot open or empty" 且 `ls | grep -i <名>` 能命中 = 名字对不上而非文件缺失，先 diff 枚举名 vs 目录实况。
- **关联**: #289（同 err 定性法）/ #290（本轮一并重验）/ `py/h3m_batch_pipeline.py`（L218 枚举点）/ `py/lowercase_h3m_names.sh` / `py/run_h3m_batch.sh`

#### #292 横跳振荡（两格往返）move_reject_streak 抓不住：位置每步都在变，卡死计数永不命中 → zigzag 惩罚刷分死循环 (09-21 修复) — ✅ 已修（主仓 cfe5941）

- **状态**: ✅ 已修上线（ep_runner_one.py，批转 verify 与主训练共用，待观测窗复验）
- **现象**: T7.8 大负局形态之一：英雄在 [A,B] 两格往返（act 方向对拍），每步位置都在变 → `move_reject_streak`（09-20 卡死熔断，判据=位置 3 拍不变）永不触发；每步吃 zigzag -2.0 + act_loop/cycle 位置类惩罚三连击 → 150 步刷到 -700 量级（neg_ep_anatomy 归因主源）。
- **根因**: 两格往返是**运动学上的死循环但字节层面位置在变**——现有熔断器全部以"位置不变"为前提（stuck_endturn/cycle 检测窗），对"高频振荡"这类**动态卡死**盲区。zigzag -2.0 惩罚被 NK2 邻域探索奖励（3x3 ×0.2）部分对冲（净 -0.5），不足以让策略跳出。
- **处理**: 新增 `_stuck_osc_streak`——zigzag 惩罚命中（cur_pos==prev2_pos）连续 ≥6 拍 → 强制 a=10（END_TURN 推进回合，移动点恢复解卡），触发后清零防连发；位置正常变化时清零。a=10 不进 act_hist 无自激。与 stuck_endturn（move_reject ≥3）并列同级熔断器。
- **教训**: ① 卡死检测要有**两条正交轴**：时间轴（位置不变）+ 频率轴（位置振荡），单轴熔断必有盲区；② 惩罚对冲（-2.0 vs +0.2×邻域）下惩罚失去行为矫正力，只剩熔断兜底——大负局归因（neg_ep_anatomy）是发现这类"惩罚失效"的唯一窗口；③ 新熔断器上线前先在归因工具里统计预期触发频率（zigzag 连击 ≥6 的局数），避免误伤合法绕行。
- **二次修复（09-21 高负局解剖实锤，两处盲区 + 一处缺漏）**: ① **递增行漏写**——首版只在位置变化时清零，zigzag 命中分支忘写 `_stuck_osc_streak += 1`，计数器恒 0 熔断永不触发；② **a<8 分支盲区**——整段 zigzag 更新挂在 `if a < 8` 内，模型输出 MOVE_TO(24) 由引导层展开成方向移动时 a=24 不进分支 → 引导路径横跳零计数（-803/-1101 局 [3,7] 对拍 250 步零干预实锤）；③ **奖励面与护栏分离**——重构后 `_stuck_osc_streak` 每拍基于位置更新（不依赖动作类型），zigzag -2.0 扣分维持 a<8 原口径（奖励面零变更，只修行为护栏）。配套 scorer 单目标拉黑 `ts_blocked`（stall/横跳放弃的格子本局不再 pick；城目标豁免已有 town_blocked 整类兜底）+ 引导路径消费 `[GUIDE_OSC_DROP]`（>=6 放弃目标+拉黑）。冒烟：同图修复前 -803（250 步纯循环）→ 修复后 step28 触发熔断、120 步战死正常收局（-471，1v3 能力性死）。注意 `_scored` 元素是 `(score, cand_dict, meta)` 三元组，过滤取 `s[1]["pos"]`（首版 `s.get` 炸 tuple）。
- **三次修复（09-21 实战复盘 -909 局，终版锚点换"数次数"）**: 首版+二次修复上线后实战 -909 局死循环依旧（同 pick (10,13) 100+ 拍、[GUIDE_OSC_DROP] 零触发）——**真实横跳形态 = act3 连发 9 次 + 多格晃动，非严格 [3,7] 对拍**，zigzag prev2 判定（位置回到两格前）与 move_stall 距离启发式（增/减交替清零）都抓不全。终版换锚点：**`ts_pick_count` 同目标累计 pick 计数 ≥8 → ts_blocked 拉黑 + `[SCORE_BLACK]` 打点**——不依赖任何位置启发式，直接锚定"同目标长时间完不成"这个事实（plen=1 完不成 = 引擎拒入该格）。冒烟：[GUIDE_OSC_DROP] step28 + [SCORE_BLACK] ×3（step52/81/139 逐死格拉黑）→ 190 步正常收局 r=-393（残值 = 1v3 能力性战死）。教训：**当行为形态不可枚举时，数事实次数（同目标反复 pick）比建位置/动作模型可靠**。
- **关联**: #287/#288（同卡死家族）/ 知识库 09-21 章（neg_ep_anatomy）/ 主仓 `cfe5941`/`8303ca2`/`c61e4db` / `py/neg_ep_anatomy.py`

#### #298 batch1 三图开局随机失败静默吞局：query -1 / segfault 概率性发作，阻塞 h3m 池混合轴 (09-22 深挖) — 🔄 挂起待专项（C++ 侧 #296 族深挖）

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

#### #293 timeout 判据形同虚设：adventure_wait 超时被 ep_runner 内部捕获 (rc=0 steps=1)，管线 detail 判据不含 "timeout" → StupidAI 重试机制上线以来零触发 (09-21 定性修复) — ✅ 已修（主仓 afdb414 + cfe5941）

- **状态**: ✅ 已修上线（批转实战首触发：[1/160] MMAI_RANDOM timeout → 自动 StupidAI 重试）
- **现象**: `train_verify()` 的 timeout 判据读 traj detail 字符串，但 adventure 300s 超时被 ep_runner 捕获后**正常收局**（rc=0，steps=1，detail="steps=1<30"）→ 上层 `[RETRY] timeout → blue=StupidAI` 分支从未命中，#293（原设计）自上线即死代码。
- **根因**: 判据放在**错误的信号面**——超时事实只存在于 verify 日志文本（`adventure_wait timed out`），traj/detail 是被捕获后的"体面收局"假象。**跨进程错误传递链上每一层都会改写错误的表现形式**，判据必须挂在事实发生的层面。
- **处理**: ① 管线读 verify 日志文本识别 `adventure_wait timed out` → detail 打 timeout 标记（afdb414）；② 配套 `train_wsl2_ppo_v2.py` 读 `_pool_index.json` 蓝方 AI 标签（管线 pool_index_update 写入 StupidAI/timeout 图），训练期采样到 timeout 图自动用 StupidAI 蓝（cfe5941，10min 缓存刷新，索引缺失=全默认零行为变化）。
- **教训**: ① 错误判据要挂**事实源头**（日志/返回码/状态字），不要挂下游转述（detail 字符串拼接）；② "零触发的防御机制"要主动演习一次（本轮 timeout 重试上线多日首次实战才确认能跑）；③ 断点索引（_pool_index.json）是管线与训练器之间的解耦契约，格式变更需双侧同步。
- **关联**: 知识库 09-21 章 / `py/h3m_batch_pipeline.py`（train_verify + pool_index_update）/ `py/train_wsl2_ppo_v2.py`（_refresh_pool_blue_ai）/ 主仓 `afdb414`/`cfe5941`

#### #294 adventure timeout 图双根因：teams 红蓝同队 + mainTown 指向无城 —— sanitize v2 造城方案根治 (09-21 定谳) — ✅ 已修（双冒烟验证：700s 超时 → 33s/35s 正常跑）

- **状态**: ✅ 已修（sanitize_v2 + A2 管线提前终止，下轮 resume-fail 生效）；v1→v2 演进含一次证伪教训
- **现象**: 批转 [1/160] a viking we shall go **allied**（MMAI+StupidAI 双超 700s）与 [3/160] a warm and familiar place（普通图）同模式 FAIL：引擎日志 `Cannot answer the query -1!` → `Can not end turn for player that is not in game!` → `Got false in applying 7EndTurn` 循环刷屏 → adventure 300s 超时；`[HEROSEG_EMPTY] slots=[0/0 ×8]`（英雄槽全空 = 红蓝英雄均未 spawn）。
- **归因过程**（三轮 diff 反转）: ① header.players 逐键 diff（timeout vs PASS 同图变体）——players 结构**完全一致**，候选根因 1 证伪；② objects 全量对比——allied 与 PASS 图 2488 对象完全相同（同图变体），objects 层证伪；③ 整 header 逐键 diff → **唯一差异键 `teams: [["red","blue"]]`**——红蓝同队 = 引擎无敌人 → 轮转/胜负逻辑崩。但 warm 图 teams=ABSENT 仍 timeout → 第二根因：`blue.mainTown` 指向 (17,16) **全图仅 1 城（red 的）** → blue 英雄无法生成。
- **v1 教训（先证伪后定谳）**: mainTown 无效 → 删键 → 冒烟实锤 `Failed to launch game: Expected at least 2 non-neutral players for non-randomHeroes mode, got 1`——**每个参战玩家必须有英雄**，删出生点不解决问题。
- **v2 修复（sanitize_vmap_players_0920.sanitize_v2）**: ① `teams` 键删除（VCMI 缺省 = 各自敌对 = 1v1 标准态）；② mainTown 指向无城 → **造城**：copy 现有城对象模板（deepcopy 保全部字段）改 owner/坐标/instanceName，generateHero=true 在城处生成英雄。全图 0 城极端情况回退删键。
- **验证**: allied 图 teams 删除 → 700s 双超 → **33s 正常 40 步**（r=-183.5）；warm 图造城 → 700s 双超 → **35s 正常 40 步**（r=-184.5）。
- **A2 配套（h3m_batch_pipeline.train_verify）**: subprocess.run → Popen + 10s log 轮询——`Failed to launch game` 或 `not in game` 计数≥50 → 提前 kill（700s → ~90s），detail 不含 "timeout" 不触发 StupidAI 重试（图本身坏，换蓝方 AI 无意义）。
- **教训**: ① "同症状 ≠ 同根因"——timeout 图有两型（结盟/无出生城），对照 diff 只能定性一张，第二张要独立找同图变体或逐键全 diff；② diff 归因三段式：候选字段 diff → 全量 objects diff → 整 header 逐键 diff，逐层排除最省力；③ 清洗类工具的"删"要配合引擎的**存在性约束**（非 neutral 玩家≥2 有英雄），删之前想清楚引擎少了它会怎样；④ 造城模板 deepcopy 现有城是零结构风险方案（字段全集天然合法）。
- **关联**: #285（HEROSEG_EMPTY 区分）/ #293（timeout 重试链路）/ `py/sanitize_vmap_players_0920.py`（sanitize_v2）/ `py/h3m_batch_pipeline.py`（train_verify 轮询）/ 知识库 09-21 章第 7 钉小节

#### #295 vmap2h3m 反转工具 4 个坑 (09-21 实锤) — ✅ 已修/已定位

- **状态**: ✅ 已修（Python 侧注释容错）/ 已定位（3 个非 bug 坑 + 1 个引擎侧结论）
- **背景**: 首次用 `vmap2h3m.py` 将 `Faeries.vmap` 反转为 `.h3m` 并用引擎侧验证，暴露 4 个连续问题。
- **坑 1 — vmap 读 JSON 撞 `// game` 注释 (#220 同源，Python 侧未同步修)**:
  - VCMI saveMap 输出 JSON 带 `// game` 行注释，**非合法 JSON**，引擎自身解析器容错，但 Python `json.loads` 严格模式报错 `Expecting property name enclosed in double quotes`。#220 已在 `py/h3m_batch_to_vmap.py` 修过 `_strip_c_comments` + `_loads_permissive`，但 **`py/vmap2h3m.py` 的 `read_vmap` 漏了同一套容错**（独立工具，未继承）。
  - 修复：`vmap2h3m.py` 引入 `_strip_json_comments`（按字符串，逐行剥离）+ `_loads_permissive`（先严格后容错），替换 `read_vmap` 里 3 处 `json.loads`。**patch 脚本 `py/_fix_vmap2h3m_strip_comments.py`**。
- **坑 2 — 同名函数冲突**:
  - `vmap2h3m.py` 顶层**已有一个** `strip_json_comments`（用于 `load_engine_indexes` 读 h3m_tool 的索引 JSON，签名 `path→json.loads`，与 h3m2vmap.py 的同名函数不同）。我 patch 新引入的 `strip_json_comments`（按字符串，签名 `text→string`）**覆盖**了旧版，导致 `load_engine_indexes` 拿到字符串当 dict 用 → `'str' object has no attribute 'keys'`。
  - 修复：新版重命名为 `_strip_json_comments`（前缀 `_` 表私有），避开旧版。
- **坑 3 — h3m 非 randomHeroes 局需 ≥2 非中立玩家**:
  - 引擎侧 `Expected at least 2 non-neutral players in the game`。`Faeries` 是 1 非中立玩家（red）→ 引擎降级/拒绝完整开局。141 张有 ≥2 非中立玩家，18 张单玩家（Faeries 这类）。测试脚本改 `random_heroes=1`（随机英雄模式跳过此检查）。
  - **注意**: 双玩家图（All for One, red+blue）也复现 `query -1` → 此坑**非** `query -1` 的根因（误判已推翻），仅为测试时需 `random_heroes=1`。
- **坑 4 — 图名大小写**:
  - `data/Maps/` 目录里 `Faeries.vmap` 是首字母大写，`faeries_test_v2h3.h3m` 是小写。引擎按精确大小写匹配 → 测试脚本 `--map` 默认值用小写文件名，否则 `Bad value for map`。
- **教训**: ① VCMI saveMap 输出 JSON 带 `// game` 注释是**引擎特性**，凡读 vmap 的 Python 工具（`vmap2h3m.py`/`h3m_batch_to_vmap.py`/`sync_maps_to_runtime.py`）都必须有容错层，新增工具不能漏（#220 只修了批转管线，`vmap2h3m.py` 是独立工具未继承）；② 同名函数引入 patch 前必须 `grep` 确认目标文件是否已有同名定义，避免静默覆盖；③ 反转测试图优先选 ≥2 非中立玩家的双玩家图（141 张）作储备，单玩家图（18 张）需 `random_heroes=1` 绕开。
- **复现/验证**: `python py/vmap2h3m.py maps/h3m_to_vmap/Faeries.vmap /tmp/out.h3m --engine-root ... --report ...` → 修复前 `JSONDecodeError`，修复后成功输出 75790B；`py/_test_v2h3m_engine_load.py` → 引擎侧回读 `HERO OI=55 pos=(6 6 0)`、`TOWN OI=67 pos=(28 27 1)` 与 h3m_tool 逐项一致。
- **关联**: #220（JSON 注释容错，同源不同工具）/ #294（`query -1` 另一侧——sanitize players 残留）/ `py/vmap2h3m.py` L152-172 / `py/_fix_vmap2h3m_strip_comments.py` / `py/_test_v2h3m_engine_load.py`

#### #296 h3m 反转图引擎侧 `query -1` 非致命但卡 reset()——引擎侧问题，Python 够不到 (09-21 实锤) — ⏸ 已定位/搁置

- **状态**: ⏸ 已定位（引擎侧，需改 mlclient 源码容错才彻底），用户拍板"引擎可读性结论已足够，停止 30 步适配"
- **现象**: `vmap2h3m.py` 反转出的 `.h3m` 放 `data/Maps/`，`_test_v2h3m_engine_load.py`（StrategicEnv libmlclient.so）开局后：
  - 地图加载成功，引擎回读对象完整（`HERO OI=55 pos=(6 6 0)`、`TOWN OI=67 pos=(28 27 1)` 等，与 h3m_tool 逐项一致）→ **字节镜像正确，VCMI 能解析**
  - 但 `runNetwork` 线程 2 次 `ERROR Cannot answer the query -1!`，随后 `reset()` 内部 `assert_state(AWAITING_STATE)` + `cond1.wait` **永远阻塞**，30 步跑不完
- **根因（引擎侧）**:
  - `Cannot answer` 文本在 `libvcmi.so` 二进制内（源码树 `grep -rn` 无源码匹配），**Python/Pybind 层改不动**
  - **⚠️ 09-23 勘误**: 报错实际位置 = `lib/callback/CCallback.cpp:53` `CCallback::sendQueryReply` 收到 `QueryID(-1)` 时 `logGlobal->error`。`[runNetwork]`/`[TBB worker N]` 只是调用线程标签，非报错位置。`CCallback` 在 **libvcmi.so** 内（lib/callback/），重编 libmlclient 不影响该报错
  - 发出方 `[runNetwork]` = [CServerHandler.cpp](file:///home/administrator/vcmi-native/client/CServerHandler.cpp) 的 mlclient 网络线程，开局后做一次同步状态查询（query id 1），回复失败 → `query -1`
  - 真正卡 `reset()` 的根因不是 `query -1`，而是 **h3m 反转图在 mlclient `runNetwork` 开局初始化阶段，地图/玩家状态未被正常注册到 game state**，connector 永远等不到 `AWAITING_STATE`。`query -1` 是症状，非病因
  - **与玩家数无关**：单玩家图（Faeries）和双玩家图（All for One, red+blue）都复现 → 推翻"≥2 非中立玩家"假设
  - **与 #294 同源不同层**：#294 是 vmap 侧（sanitize 未清 `header.players` 结构 → 引擎拒绝 END_TURN）；本条是 h3m 侧（mlclient 开局状态注册/查询问题）。两者表面都是 `Cannot answer the query -1`，但机制不同
- **未走路径（引擎侧，违反铁律，需评估）**:
  - 改 `libmlclient.so` 源码（`client/CServerHandler.cpp` `runNetwork` 查询容错：失败不阻塞/重试/跳过），重编 mlclient——**mlclient 不在"不重编 libvcmi.so"铁律内**（铁律只禁 libvcmi.so），但属 C++ 改动，需 WSL 重编
  - 或定位 `query -1` 具体查什么（mlclient `client/` 源码），确认是开局初始化时序还是 h3m 玩家结构注册缺失，再决定容错 vs 补数据
- **教训**: ① h3m 反转图的引擎可读性验证**到"地图加载+对象读回一致"层已足够**，30 步 rollout 需 mlclient 开局状态注册适配，是独立 C++ 工作，不值得为反转验证去碰；② `Cannot answer the query -1` 在 h3m 侧与 vmap 侧（#294）是**两种不同机制**的同表面现象，归因要看上下文（vmap 是 `Can not end turn`，h3m 是开局 reset 阻塞），别混为一谈；③ pybind connector（v13 `threadconnector.cpp`）的 `reset()` 是 C++ 函数，Python 够不到，适配要改 C++ 重编。
- **复现/验证**: `python py/_test_v2h3m_engine_load.py --steps 30` → `[ok] reset, obs shape=(1024,)` 不返回（卡死）；`grep -E 'Cannot answer|HERO OI|TOWN OI' /tmp/v2h3m_allforone.log` → 对象读回一致 + 2 次 query -1。
- **09-21 实测复现（all_for_one_h3m.vmap）**：`vmap2h3m.py` 反转 `all_for_one_h3m.vmap`（h3m_pool）→ `allforone_test.h3m`（42574B，6 城+47 怪，donor=`all for one.h3m`）；`_test_v2h3m_engine_load.py --map allforone_test.h3m --steps 30` 实测：引擎日志 `SRV-DIAG TOWN OI=0..5` 六座城坐标与 h3m_tool 读回逐项一致（地图加载层通过），`runNetwork` 线程 `Cannot answer the query -1!` 复现，`reset()` 永久阻塞（30s 无 obs 返回，kill -9 强停）。**结论与 #296 定性完全一致：引擎可读性结论已足够，30 步 rollout 属 mlclient C++ 侧 h3m 开局初始化问题，Python 层改不动，维持搁置**。
- **关联**: #294（同表面不同层）/ #295（vmap2h3m 工具链坑）/ `py/_test_v2h3m_engine_load.py` / `client/CServerHandler.cpp` L156 `runNetwork` / `vcmi_gym/connectors/v13/threadconnector.cpp` L322 `reset()`

#### #297 地下城图（mainTown 锚点在地下层）去层后蓝方无出生点 → HEROSEG_EMPTY 开局卡死——结构性不可修，`_pool_index` skip 机制封档 (09-21 实锤)

- **状态**: ✅ 已定性 + skip 机制落地（pipeline 结构性 SKIP，非代码 bug）
- **现象**: 批转 `--resume-fail` 跑到 `[3/160] a warm and familiar place.h3m`：转换成功（2 处玩家痕迹清洗 + 253 对象 strip 去地下层），但 250 步验收 `[FAIL] adventure timeout (engine stuck, steps=1) (682s)`；`blue_ai=StupidAI` 重试仍同败。取证 `verify_tail.log`：`[HEROSEG_EMPTY] slots(id/owner)=[0/0×8]` + `adventure_wait timed out: after 300s` → 开局即死。
- **根因链（本图专属，非共性 bug）**:
  - raw vmap 中蓝方**唯一城** `town_404`(blue) 位于**地下层** `l=1, (17,16)`；`blue.mainTown={"l":1,"x":17,"y":16}` 即指向它
  - `strip_underground_vmap.py` 删除全部 `z>=1` 对象（253 个）→ 该城被删；`strip` 本身不动 `header.players`
  - 下一环节 `sanitize_vmap_players_0920.py` sanitize_v2 校验 mainTown 锚点：`(17,16)` 处已无城 → 删 `blue.mainTown` 键
  - 蓝方最终无任何 mainTown → `generateHero=true` 无锚点 → `HEROSEG_EMPTY slots=[0/0×8]` → 引擎 300s adventure_wait 超时强停 → `steps=1 engine stuck`
  - 属"地下城"结构性问题（同 09-19 普查 UNDERGROUND=98 风险标签一类），**不可修复入池**
- **修复（#295 方案）**: 结构性 skip 标记机制——
  1. `maps/h3m_to_vmap/_pool_index.json` 加条目：`"a_warm_and_familiar_place_h3m.vmap": {"blue_ai": "skip", "reason": "地下城", "detail": "...", "ts": "2026-09-21"}`
  2. `py/h3m_batch_pipeline.py` main() 启动读入 `_pool_index`，收集 `blue_ai=="skip"` 的 `_skip_names`；循环体命中则打印 `[STRUCTURAL_SKIP] ...` 并 continue（`_idx` 必须预置 `{}` 防 NameError，已修）
  3. 验证：`py/_verify_skip_marker.py` 确认标记生效；`py/_syntax_check.py` ast 语法 OK
- **教训**: ① `engine stuck steps=1` + `HEROSEG_EMPTY` 组合 = 出生点缺失类结构性死因，先查 mainTown 锚点是否被 strip/sanitize 删光，**别在 AI 强度上重试**（StupidAI 重试对结构性死因零作用）；② 普查 UNDERGROUND=98 图里有"主城镇在地下层"的极端子集（去层即死），这类图应提前识别入 skip 列表而非逐张试错；③ skip 条目格式固定 `{"blue_ai":"skip","reason":...,"detail":...,"ts":...}`，后续同类图（含 #294 双根因中无城可造城的）直接照格式补条目。
- **复现/验证**: `wsl bash -c "python py/_verify_skip_marker.py"` → `[OK] 标记生效`；重跑管线命中 `[STRUCTURAL_SKIP] a_warm_and_familiar_place`。
- **关联**: #294（adventure timeout 双根因 sanitize v2）/ #289/#290（批转工具链）/ `py/h3m_batch_pipeline.py` L244-L280 / `py/_probe_warm_mainTown.py` / `py/_verify_skip_marker.py` / `maps/h3m_to_vmap/_pool_index.json`

#### #298 H3M 入池批次过滤未实现 → 水/岛/地下图全池均匀采样，模型未学造船/跨层直接大负 (09-21 用户纠正后修复) — ✅ 已修（`HOMM3_H3M_BATCH` env + `_pool_index.json` `batch` 字段）

- **状态**: ✅ 已修（`py/train_wsl2_ppo_v2.py` + `maps/h3m_to_vmap/_pool_index.json`，commit 62bbc47）
- **现象**: `HOMM3_H3M_MIX` 开关全池均匀随机（`random.choice(_POOL_MAPS)`），137 张图无批次区分。h3m_pool 里 26 张水/岛图 + 14 张地下层图与 5 张安全图混在一起采，模型从未学过造船/跨层 → 采到水图直接大负（reward 无 SHIP 项，模型全卡水边不动）。
- **根因**: WIN-5 设计时 `HOMM3_H3M_MIX` 只控"混入比例"，没控"采哪些图"。用户 09-21 纠正"这里面有好多有水，是岛屿的，我们都还没有训练过，会直接负数"后才意识到需要按能力维度分批。
- **修复**:
  1. `_pool_index.json` 给 7 张图标 `batch` 字段：首批 5 张（good_to_go/judgement_day/elbow_room/a_viking_we_shall_go_allied/a_viking_we_shall_go）标 `batch:1`；二批 2 张（too_many_monsters/elbow_room_allies）标 `batch:2`
  2. `train_wsl2_ppo_v2.py` 新增 `HOMM3_H3M_BATCH` env（默认 0=不过滤）；`>0` 时 `_POOL_MAPS` 只采 `_pool_index.json` 里**显式标了 `batch` 且 `<= 阈值`** 的图，没标 `batch` 的一律不放行（水/岛/地下图未标记 = 不入采样）
  3. 生成脚本 `py/_gen_pool_batches2.py` 按 `water_touched`/`has_island`/`has_underground` 三字段 + `risk_tag` 四批分类，输出 `maps/h3m_to_vmap/_pool_batches.json`
- **教训**: ① 全池均匀随机在多能力图混池时必然引入未学能力维度的图 → 大负；任何"入池前未学"的能力维度（水/岛/地下/门）都必须有**显式批次门槛**；② 普查字段（`h3m_type_survey.json` 的 `water_touched`/`has_island`/`has_underground`）是分批的权威依据，不能只看 `risk_tag`（`dense_neutral` 图也可能有水）；③ 水/岛/地下三类能力维度独立，不能合并为"难图"一批——地下跨层与水边卡船是完全不同的失败模式，各自需要独立激励轴。
- **关联**: WIN-5 任务清单入池节奏段 / `py/_gen_pool_batches2.py` / `maps/h3m_to_vmap/_pool_batches.json` / `maps/h3m_to_vmap/_pool_index.json` / `py/train_wsl2_ppo_v2.py` L165-L192
