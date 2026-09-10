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

---

## 待归档新增（收到“保存踩坑点”时追加于此）

> 此区为新增踩坑点暂存区。用户定期自行归档到上方 5 个主题子文档后，再从本区移除。
> 新增条目沿用全局编号续接（当前最大 #174，下一条为 #175…），每条须带状态字段（✅/⚠️/❌/🔄），引用其他条目用 `见 #X`。
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

