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

---

## 待归档新增（收到“保存踩坑点”时追加于此）

> 此区为新增踩坑点暂存区。用户定期自行归档到上方 5 个主题子文档后，再从本区移除。
> 新增条目沿用全局编号续接（当前最大 #124，下一条为 #125、#126…），每条须带状态字段（✅/⚠️/❌/🔄），引用其他条目用 `见 #X`。

### #125 ⚠️ C++ 符号排查 grep 模式坑: typeinfo/vtable 是 mangled 名 (08-31)

- **现象**: 排查 Router 断言时 `readelf -sW libMMAI.so | grep -c typeinfo` 返回 0 → 误判 "RTTI 全部隐藏/缺失", 顺着 visibility 假设全量重编 (走弯路)
- **真因**: C++ 符号在 readelf 输出里是 mangled 名 — typeinfo=`_ZTI*`/`_ZTS*`, vtable=`_ZTV*`; 字面 "typeinfo" 永远匹配不到。新旧 .so 符号表结构其实完全相同 (3260 行)
- **正确姿势**: `grep -E '_ZTI.*BAI'` / `_ZTV` / `_ZTS`; 或 `c++filt` 反修饰后再 grep
- **教训**: 二进制符号排查先用已知存在的符号 (如确认存在的类) 校准 grep 模式, 再下 "缺失" 结论
- 状态: ⚠️ 认知坑, 无代码改动

### #126 ⚠️ cmake 重编 build type 覆盖坑: Release 触发 strip → 953KB 空壳 .so (08-31)

- **现象**: 全量重编 libMMAI 时手传 `-DCMAKE_BUILD_TYPE=Release` (原构建 = RelWithDebInfo) → 产物从 18.7MB 缩到 953KB, symtab/vtable/typeinfo 全空
- **危害**: 若没注意大小直接部署 = 运行时符号全无, 故障排查地狱
- **正确姿势**: 重编前先查 `grep CMAKE_BUILD_TYPE <build>/CMakeCache.txt` 对齐原值; 产物验证必查 `ls -la` 大小 vs 旧版
- 状态: ⚠️ 操作坑, 已纠正 (最终以 RelWithDebInfo 重编 18.7MB fe48be90)

### #127 ⚠️ cmake 增量操作顺序坑: set_target_properties 需重 configure / rm 须在 cmake 前 (08-31)

- **现象 1**: CMakeLists 加 `set_target_properties(MMAI PROPERTIES CXX_VISIBILITY_PRESET "default")` 后直接 make → 仍用老 flags (hidden) — **target 属性改动需重新 configure 才生成新 flags.make**
- **现象 2**: `rm -rf CMakeFiles/MMAI.dir` 放在 cmake **之后** → 把 configure 刚生成的 build.make 一起删了 → "No rule to make target build.make"
- **正确顺序**: `rm -rf <T>.dir` → `cmake ..` (重配) → `make <T>`; flags 验证: `grep -o '\-fvisibility=[a-z]*' <T>.dir/flags.make` (注意 #125 的模式坑, 精确匹配 `=hidden`)
- 关联: KNOWLEDGE.md visibility 修复条 (该修复只在 ENABLE_MMAI_TEST 测试块内, 正式构建从未生效 — 见知识库 USING_ONNX 条)
- 状态: ⚠️ 操作坑

### #128 ⚠️ ep_runner_one.py 无 __main__ 保护: import 即跑主流程 (08-31)

- **现象**: 冒烟脚本 `importlib` 整体 import ep_runner_one → 模块级 argparse + 主循环直接执行 → **真起了一局 VCMI episode** (引擎日志刷屏, 与在跑训练并发写 terrain_grid.bin)
- **危害**: 训练期并发 episode 可能污染共享文件 (terrain_grid.bin 每步重写自愈, 本次未实际损害); 冒烟脚本意图完全失效
- **正确姿势**: ep_runner 冒烟只用 `py_compile` + 纯逻辑复现 (不 import 主模块); 若要 import 须先给 ep_runner_one.py 加 `if __name__ == "__main__":` 保护 (待办)
- 状态: ⚠️ 未加保护, 冒烟规范先行

### #129 ⚠️ 日志方括号事件词前缀匹配坑: grep '\[TOWN' 把 [TOWN_BLOCKED] 一起算 (08-31)

- **现象**: `grep -c '\[TOWN'` 统计 [TOWN] 触发 = 324 次, 实为 `[TOWN_BLOCKED]` (卡死标记) 的数量; 真实 [TOWN] visited = 0 — **差点把死轴当成活轴**
- **正确姿势**: 方括号事件词统计必须带右括号精确匹配 `'\[TOWN\]'` (转义链: wsl bash -c 双引号内 \[ 会被消费一层, 跨层转义需实测); 或改用无歧义子串 `'town visited'`
- 关联: 坑 #122 (转储词表盲区) 的变体 — 统计口径坑第二例
- 状态: ⚠️ 认知坑
