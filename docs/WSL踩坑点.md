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
> 新增条目沿用全局编号续接（当前最大 #204，下一条为 #205…），每条须带状态字段（✅/⚠️/❌/🔄），引用其他条目用 `见 #X`。
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
- **复现/验证**: `python py/p8be_host_start.py` (阶段2 完整对局, 跑完 grep server 日志 `not allowed|fishy` 应 = 0); `python py/p8b_lobby_probe.py` (阶段1 握手)。
- **关联**: T13.10 / P8 / `docs/序列化协议规格.md` / 提交 `bdce29a` → `efb5b6b` → `407e8e5` → `9cc08b9` / 踩坑 #200。

#### #200 P8-B 阶段2 PlayerStartsTurn 字段序错 + 盲发 EndTurn 抢对方回合 → server fishy 拒绝 (2026-09-11) — ✅ 实锤修复
- **状态**: ✅ 已修复 (commit 9cc08b9)
- **背景**: P8-B 阶段2 首轮 `p8be_host_start.py` 表面 `RESULT: game_started=True`，但用户指出"没完成对局，运行就报错"。查 server 日志抓到实锤。
- **坑① 字段序错**: `PlayerStartsTurn(88)` 的 Python 定义写成 `player + time_limit`，与 C++ `Query{queryID} + PlayerColor player` 字段序不符。C++ 权威结构 (PacksForClient.h): `serialize: h & queryID; h & player;`。实机字节 `88帧 = 00 00 d800 41 00` 逐字对上：isNull(00) + pid(00) + tid(88→d800) + queryID(-1→41) + player(0)。
- **坑② 盲发抢回合**: 旧脚本在**每个** PlayerStartsTurn 都无条件发 EndTurn(player=0)，包括蓝方 (p1, ModelAI 客户端的回合)。蓝方回合被 Python 抢发 EndTurn → server 拒 "Player is not allowed to perform this action!" + "Got false in applying 7EndTurn... fishy!" + 2 条 SystemMessage。虽然 ModelAI 自己那轮正常走完、Turn 2 也轮转了，但日志里的 fishy 拒绝是真实错误信号，不算完成。
- **正确口径**: PlayerStartsTurn 包体 = `queryID(LVarInt, 无 timer 时 -1) + player(LVarInt)`。只在 `pack.player == MY_COLOR`（自己的回合）才发 EndTurn；对方回合 SKIP，交给对方客户端（ModelAI）自主管理。EndTurn 绝不替对方回合发。
- **修复**: `py/vcmi_protocol/packs.py` 重写 PlayerStartsTurn（queryID+player 字段序 + 覆写 deserialize）; `py/p8be_host_start.py` 解析 88 包体 player，加 `MY_COLOR=0` 门控; `tests/test_e2e.py` 断言 player/query_id。实机 grep `not allowed|fishy` = 0，Turn1→Turn2 两次 "successfully applied"，ModelAI 蓝方自主 TryMoveHero(40B)。离线 145/145 PASS。
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
- **复现**: `python py/p8c_capture_hero.py` (已修, 正常开局); 旧症状 = 捕获脚本报 "捕获结束" 但零 [DUMP] 行 + server 日志 SetMap 刷屏。
- **关联**: #185 (SetMap host-only) / T13.10 P8-B 阶段2 方案F / `py/p8be_host_start.py` 第 114-129 行时序范本。

#### #203 P8-B 阶段3 (P8-C) 数据源墙：我的英雄 OI+位置只在 StartGame 171KB 全状态, 回合窗口无独立位置包 (2026-09-11, 捕获分析) — 🟡 已分析, 待决策
- **状态**: 🟡 分析完成, 3 条路线待用户拍板
- **实锤**: ① turn 窗口 server 只广播 88/102/116/86/84/91/109 等, **不**单独发 GiveHero/ChangeObjPos/NewObject 位置包 (171KB 之后的 8s 内零 hero 位置包) ② `MoveHero.hid` = 引擎运行时 ObjectInstanceID, ≠ h3m 静态 heroID → P10 h3mtxt 静态 JSON 拿不到 OI, 走不通 ③ server 日志只在英雄实际移动时打 "OI xxx start (x y z)", 挂机玩家无记录。
- **结论**: Python 外挂要发真实 MoveHero, 必须从 StartGame(224) 的 `LobbyStartGame = StartInfo + CGameState(171KB)` 解析出 `CMap.heroesOnMap` / `CPlayerState.hero` OI + 坐标。CGameState 全量 Python 解析工程量大 (map 对象数组几百个 CGObjectInstance 模板 + 版本门控字段, 见 CGameState.h L196-225)。
- **三条路线 (改编号为阶段4/5/6)**: **阶段4 最小 CGameState 解析器** — 只挖到 heroesOnMap + hero OI 为止, 每包校验断言 (width=36/day=1), 工程中等, 收益=完整 MoveHero 闭环 **阶段5 降级最小闭环** — 阶段3 先做 QueryReply(197)+RecruitCreatures(187) 真实决策 (不依赖地图状态, 城镇 OI 可从 SetAvailableCreatures 拿), MoveHero 留阶段4 **阶段6 C++ headless client** — 直接复用 VCMI 序列化代码 (路径A), 工程量最大但零逆向风险。
- **复现**: `python py/p8c_capture_hero.py` (dump 171KB → %LOCALAPPDATA%/Temp/p8c_startgame.bin, 离线分析入口)。
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
- **关联**: #206 (SRV-DIAG 路线) / `CVCMIServer.cpp onPacketReceived` / `EntityIdentifiers.cpp resolveIdentifier L171` / 脚本 `py/p8c2_town_chain_probe.py`。

#### #206 P8-C 数据源墙第四路线 = SRV-DIAG server 侧注入, 免解析 171KB (2026-09-11, MoveHero 闭环实机 PASS) — ✅ 已实施
- **状态**: ✅ 落地并实机验证 (vcmi commit bc3e124fa2 + 主仓 7967511)
- **方案**: 不解析 StartGame blob, 改在 `CGameHandler::start` (`!resume` 分支) `fprintf(stderr, "[SRV-DIAG] HERO OI=%d owner=%d pos=%s", ..., hero->anchorPos().toString())` 逐英雄 dump → Python 外挂 tail server 日志拿运行时 OI+owner+锚点坐标。零逆向、零包解析、跨图通用。
- **坑中坑 (字段序)**: `TryMoveHero(109)` wire 序 = **id + result + start(int3) + end(int3) + movePoints + fowRevealed(vector) + attackedFrom**, 非直觉 id+start+end+result; 读错会把 SUCCESS(1) 当 FAILED(0) (离线 test_e2e 两侧同错自洽通过, 实机 server trace 对拍才抓出, 与 #199 同型坑)。
- **MoveHero 语义**: path = 锚点坐标序列, 每步须与英雄当前位置 8 邻域相邻 (`areNeighbours` 检查), layer=0(LAND), transit=false; day1 MP 耗尽后同格移动也回 SUCCESS(=原地 no-op), 不是拒绝。
- **实锤**: red OI=350 (1,8,0)→(2,7,0) 实移 + blue ModelAI OI=732 (16,1,1)→(15,0,1) + 3 回合轮转 + PackageApplied=True + zero fishy。
- **脚本**: `py/p8c_movehero_probe.py`。
- **关联**: #203 (数据源墙分析, 本条=第四路线闭环) / #202 (ChangeHost 时序) / #200 (PlayerStartsTurn 字段序) / `CGameHandler.cpp CGameHandler::start`。

