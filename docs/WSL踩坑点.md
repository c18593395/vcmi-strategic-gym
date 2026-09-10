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

### #130 🔴 PowerShell 双引号内 $(...) / $var 子表达式展开: wsl 复杂命令被撕裂 (09-02, 09-07 补 $var 近亲)

- **现象**: `wsl bash -c "... $(ls -t ...) ..."` 中 `$(...)` 被 PowerShell 当子表达式先行执行 (报 head 不存在/空变量), bash 收到残缺命令; heredoc 正文同样被撕 (本次归档操作亲自复现); **$var 变量同理** — `wsl bash -c "L=$(grep -n ...); tail -n +$L f"` 中 `$L` 被 PowerShell 展开为空 → bash 收到 `tail -n + f` 报 invalid number (09-07 复现, 即使 `\$` 转义在跨 PowerShell→wsl 两层解析下仍不可靠)
- **正确姿势**: 复杂命令/长文本写入文件 (Write 工具 → py/_tmp_xxx.sh) 再 `wsl bash -c "bash 文件"`, 用完即删; 单条简单命令才直接 wsl bash -c
- 状态: 🔴 操作坑, 规范先行

### #131 🔴 编译 -j8 与训练并发压死 WSL: 0x8007274c 连接失败 (09-02)

- **现象**: cmake --build -j8 (MMAI 大编译单元) 与 v5 训练 (PPO+VCMI episode) 并发 → WSL 服务整体无响应 (`wsl -e echo` 超时 Wsl/Service/0x8007274c, ps/systemctl 全挂)
- **恢复**: 仅 `wsl --shutdown` 可解 (训练丢未保存进度); 恢复后必须重建 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList 'sleep infinity'` (随 VM 死亡, 踩坑 #114)
- **正确姿势**: 重编 .so 前 `systemctl --user stop homm3-train-v5` 编完再启; 或 -j4 上限; 产物验证 ls -la 大小 + strings 特征串
- 状态: 🔴 已踩, 规范先行

### #132 🔴 主日志选择性转储口径假象: [ECON]/[RECRUITED] 不在白名单 (09-02)

- **现象**: 主日志 grep [ECON]/[RECRUITED] = 0 → 误判"招兵从未执行"; 实际 runner stdout 全量进 /tmp/hermes_ep_*.log, 主日志只转储部分事件词 ([MINE]/[TOWN]/[ZOMBIE] 在, [ECON]/[RECRUITED]/[BUILD_NEW] 不在)
- **正确姿势**: 经济/效果类信号一律查 hermes (`grep -h ECON /tmp/hermes_ep_*.log`); 主日志只看白名单内事件
- **关联**: 坑 #122/#129 统计口径坑第三例
- 状态: 🔴 认知坑, 已纠正

### #133 🔴 VCMI 1.8 getUpperArmy() 不含 visiting hero: 与 HoMM3 直觉相反 (09-02)

- **现象**: CGTownInstance.cpp L879-884 `if(getGarrisonHero()) return getGarrisonHero(); return this;` — 只返回 garrisonHero 或 town 本身; 英雄 visit 后 dst 仍非英雄 (实测 visit=1 但 dstIsHero=0)
- **危害**: "getUpperArmy 优先 visiting hero" 的直觉假设使 P1 visit 修复后兵仍进 garrison 黑洞; 知识库 08-31 条目关键推论因此错误 (已修正)
- **正确姿势**: 招兵给 visiting hero 时显式 `dst = town->getVisitingHero()` (public const, CGTownInstance.h L132)
- 状态: 🔴 认知坑, 已修复 (P1b)

### #134 🔴 fprintf(stderr) 在 MMAI server 内不可见: console 重定向 (09-02)

- **现象**: AAI.cpp 内 fprintf(stderr,...) 诊断在 hermes/主日志均不出现 ([MMAI-DIAG] init 行证明启动期 stderr 通 hermes, 但 AI 运行期输出被吞)
- **正确姿势**: C++ 侧诊断写独立文件 `{FILE* dg = fopen("/tmp/xxx.log","a"); if(dg){fprintf(dg,...); fclose(dg);} }`; 基建: /tmp/rl_recruit_diag.log (取兵链路诊断, 验证后可删)
- 状态: 🔴 排查坑, 基建可用

### #135 🔴 Python 补丁脚本三连坑: % 格式化冲突 / 锚点缩进失配 / while pos 不前进死循环 (09-02)

- **现象 1**: 补丁串内嵌 printf 的 %d 被 python `% k` 格式化消费 → TypeError; **现象 2**: 源码锚点含行尾空白/Tab 缩进 → 精确字符串 count=0; **现象 3**: `while: pos=find(...)` 后 pos 停在行首不越过插入点 → 死循环吞内存 (叠加编译压死 WSL, 见 #131)
- **正确姿势**: % 用占位符 @@ + .replace; 锚点前先 sed -n 'X,Yp' | cat -A 看实际字节; 行级插入用 split('\n') 遍历; 补丁前必备份 (cp .bak_标签_时间戳)
- 状态: 🔴 操作坑, 规范先行

### #136 🔴 C++ 诊断代码远程生成三连坑: 引号拼接 / 尾杂引号 / 作用域外引用 (09-02)

- **现象 1**: Python 补丁模板双引号拼接 bug 产生 `fprintf(dg, ""[RL-DIAG7]` → 编译错 stray '\'; **现象 2**: 模板参数尾部多杂引号 `? 1 : 0");` → missing terminating " character; **现象 3**: w3 诊断放在 i3 循环外但引用循环变量 i3 → 'i3' was not declared in this scope
- **修复实录**: `sed -i 's/fprintf(dg, ""\[RL-DIAG7\]/fprintf(dg, "[RL-DIAG7]/g'` 修现象 1; `sed 's/? 1 : 0"); fclose/? 1 : 0); fclose/g'` 修现象 2; 去掉 i3 引用改打 pos 修现象 3
- **正确姿势**: 生成后必 `grep -F '[RL-DIAG7]' 目标 | cat -A` 自检引号/尾字符; sed 替换式内 `\[` 易被消费致 grep Invalid range end → 用 grep -F 固定串验证; 诊断引用变量必须在同作用域; 每补一处立即增量编译 (-j4) 通过再下一处
- **关联**: #135 补丁脚本三坑姊妹篇 (彼时是脚本机制坑, 本次是生成代码内容坑)
- 状态: 🔴 操作坑, 规范先行

### #137 🔴 VCMI 坐标系双口径坑: 锚点 pos vs visitablePos, 邻接判定必错 (09-02)

- **现象**: P1 邻接守卫用锚点坐标 `distSq(standPos, cur->pos) > 2` → 邻接英雄被误判"远", 71/71 全部误弃 (DIAG7: enter 有动作, afterMove 恒 0); 改 visitablePos() Chebyshev≤1 口径后同场景放行
- **机制**: `cur->pos` 与 `visitablePos()` 差 convertFromVisitablePos 对象相关偏移; 城锚点在 3x3 mask 中心 (mask=["VVVVV","VVAVV","VVVVV"]), 英雄 visit 停在邻格 — 锚点坐标系下"邻接"对城锚点距离可达 2-3, 守卫阈值 2 必误杀
- **正确姿势**: 邻接/距离/守卫判定一律 **visitable 口径** (`visitablePos()` 双方 Chebyshev≤1); 锚点坐标仅作 moveHero 目的地; 已在锚点时改走对象格本身触发 visit (与 a==8 双路径同款)
- **关联**: 知识库"城格不可站"条 (TOWN 判定 dist≤1 同源); 踩坑 #133 (getUpperArmy)
- 状态: 🔴 认知坑, 已修复 (P1c)

### #138 🔴 SearchReplace 模糊匹配残片: old_str 微差致插入错位 (09-03)

- **现象**: 向 md 文档插入条目时 old_str 与原文有细微差异 (标点/空格), 工具不报错而是模糊对齐, 在目标位置产生 `④ **P1d- **P1d-v2` 类残片 (新内容嵌进旧行中段)
- **正确姿势**: 插入后必 grep 关键词复核落位与上下文; 发现残片: Grep 定位 → 精确读取上下文 → 二次 SearchReplace 修复; old_str 从 Read 输出逐字复制, 勿凭记忆重打
- 状态: 🔴 操作坑, 规范先行

### #139 🔴 /mnt/d venv 已不存在: systemd-run 相对路径启动失败 (09-03)

- **现象**: v5 历史启动命令 `--working-directory=/mnt/d/Bigdata/hero3_fresh + venv/bin/python` 重启时报 `No such file or directory` — /mnt/d/Bigdata/hero3_fresh/venv 目录已消失; 实际训练 venv 在 `/home/administrator/vcmi-workspace/venv` (Phase A 验证 vcmi_gym 解析路径时已实锤)
- **危害**: systemd-run 返回 "Running as unit" 但进程秒死 (is-active=inactive), 训练假启动; unit 随 --collect 自动消失 (status 报 could not be found), 不好查
- **正确姿势**: 启动命令一律用绝对路径 `exec /home/administrator/vcmi-workspace/venv/bin/python`; 重启后必验 `is-active` + tail 主日志确认 resume 行, 不能只看 systemd-run 返回值
- 状态: 🔴 操作坑, 已纠正 (绝对路径重启成功)

### #140 🟡 C++ API 假设编译前必 grep 验证: typeName() 不存在实为 getTypeName() (09-03)

- **现象**: R7 埋点凭直觉写 `visitedObject->typeName()` — CGObjectInstance 实际 API 是 `getTypeName()` (CGObjectInstance.h L54), 编译期才暴露; 若在停训练窗口内编译失败则窗口拉长
- **正确姿势**: 停训练窗口前先在源码 grep 验证所有新用 API (类成员名/方法签名); 本次因编译前验证流程 (queryID/result 虚成员 grep) 已验两项, 漏了 typeName — 流程执行不彻底
- 状态: 🟡 流程坑, 规范先行

### #141 🔴 WSL 断网 + Windows 有网: 双机协作下载方案 (09-03)

- **现象**: R6 修复需下载 onnxruntime, WSL 侧 GitHub/镜像/pypi/gitee 全部 unreachable (连 baidu 都不通), 但 Windows 侧 curl 正常 (200 OK); WSL 无代理端口 (7890/10809/1080 全无监听, 系统代理 ProxyEnable=0)
- **危害**: WSL 内直接 curl/pip download 全失败, 白烧多轮重试
- **正确姿势**: **Windows 侧 curl.exe 下载 → 落 /mnt/d → WSL 解压安装** (`curl.exe -o D:\...\_tmp_ort.tgz <url>` → `wsl -u root tar xzf /mnt/d/... -C /opt/onnxruntime --strip-components=1`); 头文件跨平台通用 (win-x64 包 include 可直接给 linux 编译用, 但库必须 linux 版); 用完删临时文件
- **关联**: 下次 WSL 断网先 `curl.exe` 测 Windows 侧, 通则走 /mnt/d 桥, 勿在 WSL 内重试网络
- 状态: 🔴 环境坑, 方案已验证

### #142 🔴 C++ if 无花括号 + fprintf 抢作用域: 招兵循环 UB 潜伏爆雷 (09-03)

- **现象**: AAI.cpp a==18 分支 `if (!creatures[i].second.empty())` 无花括号, 后续补丁插入的 fprintf 单语句抢走 if 作用域 → `cb->recruitCreatures(...)` 无条件对所有 tier 执行, 空 tier `second.front()` = UB; 训练 96ep 潜伏未爆, 冒烟图内存布局不同 → segfault libMMAI.so+0x49948 (runNetwork 线程, RAX=0 解引用)
- **定位手段**: dmesg segfault 行 `ip ... in libMMAI.so[49948,...]` → `addr2line -e libMMAI.so -f -C 0x49948` 直接给出源码行 (带符号的 .so 才行, #126 strip 坑注意)
- **正确姿势**: 给无花括号 if 追加语句时必须连原句一起包花括号; fprintf 诊断行插入前后用 `cat -A` 核对作用域; 编译警告 "too many arguments for format" = fprintf 参数/占位符失配线索, 勿忽略
- 状态: 🔴 已修复 (加花括号+break 对齐 16/17)

### #143 🟡 vmap 地图三个加载事实: footman 缺失 / 运行时路径 / 英雄格阻挡 (09-03)

- **事实 1**: `core:footman` 在当前 VCMI fork 不存在 — T05 全部 4 图加载失败 (`Failed to resolve identifier monster::core:footman`); gen_level3.py 含 footman 守卫同样不可用 → **T04 实际 0 守卫的历史成因**。可用生物以现有图 hero army 实测为准 (swordsman/archer/peasant ✓)
- **事实 2**: 冒烟/训练运行时地图路径 = `rel/bin/data/Maps/` (VCMI ResourceHandler DATA 根), `Maps/training/` 是生成源不是运行时路径; 新 vmap 必须 cp 到 rel/bin/data/Maps/ 才能被 ep_runner 加载
- **事实 3**: VCMI moveHero 到**敌方英雄格**被 "destination tile is blocked" 拒绝 (英雄战不由此触发); **monster 格可进入 = 触发战斗** (T03 机制)。mapname 必含 "adventure"/"s1"/"mini" (strategic_env assert) 且 header.name 需同名
- **事实 4 (09-03 补)**: T05 全 4 图三类非法 identifier 加载失败 — monster `core:footman`(8处) / resource `core:resourceGold/Wood/Rare`(15处, 命名风格错, 正确=core:gold/wood/crystal) / hero `core:inham`(4处→core:iona); resource options 还缺 amount。**教训: 生成图的每个 identifier 必须以 fork 已加载图的实测值为准** (T04 hero/monster/town/resource 类型全表 = 安全校准集); 逐个报错逐个修 = 三轮返工, 应先全量对照校准集再写图
- **事实 5 (09-04 补, 重大)**: vmap 加载失败**不报错退出而是 fallback 复用已缓存图** → `map=` 标签与实际加载图脱钩! 实锤: _mir 图 6 张未 cp 到运行时路径, 训练 197ep 中 "T04_mir" 局实为 T05/T04 缓存图 (三连 r=141.53 局声称 20X20/36X36 不同尺寸但 obs_nz=223+act 逐字节相同 = 同一张图)。**检验方法: 同图 obs_nz 特征带一致 + 跨尺寸图 obs_nz 必不同 (20X20≈369 / 36X36≈246-309 / 52X52≈223 但 act 结构不同)**; 新增图必须 cp 到 rel/bin/data/Maps/ 并用 obs_nz 特征带对照验证真实加载
- **事实 6 (09-04)**: Edit 工具替换 MAPS 列表时 old_string 只匹配尾部 → 旧列表未闭合 + 新 MAPS 重复赋值 = SyntaxError; 改列表赋值前必读全文确认块边界, 旧块转注释存档
- 状态: 🟡 认知坑, 已沉淀 (T05 已修复验证 4/4 通过; _mir 已补副本验证真实加载)

### #132 🔴 identifier 校验集混入 subtype 字段值: core:alchemist 拒启动 → 1 步空壳局 (09-06)

- **现象**: T06 原图 1v3 两局完全一致的异常形态 = `ep_steps=1 / obs_nz=0 / r=12.50 / act=[16]` (非随机偶发, 确定性复现); 其余 6 图正常
- **真因**: fix_t06_maps.py 初版 VALID_HERO 含 `core:alchemist` — **alchemist 是职业名 (hero 的 subtype 字段合法值), 不是英雄名** (options.type); 引擎报 `Couldn't resolve hero identifier core:alchemist` → Failed to launch → runner 第一步收 done 空壳局; castle.json 实测英雄全名单 = orrin/valeska/edric/sylvia/lordHaart/sorsha/christian/tyris/... (16 个)
- **修复**: 4 原图 hero_3 alchemist→core:christian (fix_t06_hero3.py, castle.json 实名); duel 变体因删 hero_2/3 不受影响 (侥幸正常的原因)
- **教训**: identifier 校验集必须逐一实测验证 (引擎真实加载), **不能混入 subtype/template 类字段值** — 它们类型系统相同但命名空间不同; 排查信号 = "异常形态完全一致" 即确定性配置错误, 非随机故障
- 状态: ✅ 已修复 (inspect 8 图全绿 + 单集复现引擎启动成功)

### #133 🔴 ServerPlugin HeroPool 对称校验拒多敌课程: 1v3 及 1v7 全部无法启动 (09-06)

- **现象**: alchemist 修复后 1v3 仍拒启动: `Added pool 0 of owner 0/1: default` → `ERROR Failed to launch game: Owners have differently sized pools`
- **真因**: fork 训练栈 `server/ML/ServerPlugin.cpp` pool matching — 非 randomHeroes 模式且恰好 2 owner 时, 强制双方同名 pool 英雄数相等 (T04/T05/duel 全 1v1 天然通过, 1v3 red1 vs blue3 → 1≠3 throw)
- **修复**: 大小不等降级 stdout 警告 (`pool size mismatch ... skip`), pool **名**不同仍 throw (真配错图仍可发现); **libmlserverplugin.so 是独立 SHARED 库不触"勿重编 libvcmi.so"铁律** (server/ML/CMakeLists add_library mlserverplugin SHARED; 单文件重编 -j4, cmake --build rel/ --target mlserverplugin)
- **运维**: 备份链 .bak_pool_0906 (.so+源码); 副本同步 vtest/bin + hero3_vcmi/build/bin (route-backups/vcmi-gym 为历史备份不同步); **1v7 课程前置障碍已扫除**
- 状态: ✅ 已修复部署 (1v3 真实首局 73 步 r=82.38 闭环)

### #134 ⚠️ transient unit 停止即消失: systemctl start 报 Unit not found (09-06)

- **现象**: `systemctl --user stop homm3-train-v5` 后想 `start` 恢复 → `Unit homm3-train-v5.service not found`
- **真因**: v5 是 systemd-run 创建的 **transient unit**, `--collect` 使停止后 unit 定义被自动收集清除 — stop/start 模式只适用常驻 unit 文件
- **正确姿势**: 每次重启必须 systemd-run 重建 (命令固化 `py/restart_train_v5.sh`; **venv 必须绝对路径** /home/administrator/vcmi-workspace/venv/bin/python — hero3_fresh/ 下无 venv, 旧记录 `exec venv/bin/python` 相对写法在当前目录结构下必挂)
- 关联: 踩坑 #114 (keepalive) 的姊妹坑 — 两坑叠加 = 夜里中断后早上既 start 不了还得重建
- **补充 (09-08 二次复现)**: stop 后 `systemctl --user is-active homm3-train-v5` 对**已消失的 unit 照样输出 `inactive` (exit 4)**, 不报 not found — is-active 结果不能作为 unit 存在性判据; 且 `stop` 一个已消失 unit 也可能静默成功, 停机确认要看 journalctl (`Stopped homm3-train-v5.service` + train_loop.log 出现 `Saved STATE_PATH`) 而非 is-active; 重启一律 `py/restart_train_v5.sh` 勿走 systemctl start
- 状态: ✅ 已固化脚本

### #135 ⚠️ 隔夜中断形态与恢复序: keepalive 丢失 → 非优雅关机 → checkpoint 回滚 (09-07)

- **现象**: 夜里训练中断, 早上 resume 点 (546379) 落后最后日志进度 (547071) ~700 步 (≈10 局样本未入档)
- **机理链**: Windows 侧 keepalive 会话丢失 (关机/会话清理) → VM idle shutdown 广播 SIGTERM **不走 systemctl stop 优雅保存路径** → 模型状态停在最后一次自动存档
- **恢复序 (开机后)**: ①先补挂 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList 'sleep infinity'` (见 #114) ②再 `py/restart_train_v5.sh` (transient unit 需重建, 见 #134) ③grep 'Loaded train state' 确认 resume 点
- **损失评估**: 回滚量 = 中断前日志 step - 存档 step, 小则几局大则一夜; 存档一致性无损
- 状态: ✅ 已恢复 + keepalive 已补挂 (09-07 晨)

### #136 🔴 多 resume 日志取"最后一次启动后窗口"的 awk 陷阱: tac|awk|tac 返回全文件 (09-07)

- **现象**: 想取最后一次 `Loaded train state` 之后的日志窗口统计, 用 `tac f | awk '/Loaded train state/{f=1} f' | tac` — 结果拿到**全文件** (441 条 ZOMBIE 假计数, 实际当前窗口 0 条); `awk '/pat/,0'` 同样只从**第一个**匹配点开始, 混入历史窗口
- **真因**: 日志经多次重启含**多个** `Loaded train state` 行 — tac 后该行成为首行立即触发 f=1, 全部倒序内容都通过, 再 tac 回来 = 原文件; awk 范围式 `/pat/,0` 从首个匹配生效, 均无法定位"最后一次"
- **正确姿势**: 行号法三步 — `L=$(grep -n 'Loaded train state' f | tail -1 | cut -d: -f1)` → `tail -n +$L f > /tmp/cur_win.log` → 对窗口文件统计; (注意 $var 需在 bash 脚本文件内展开, 见 #130)
- **教训**: 统计口径先验证窗口边界 (`wc -l` + `tail -1` 应为最新进度行), 再看数字 — 窗口错则一切统计无效
- 状态: 🔴 已踩当日修复, 固化于临时脚本套路

### #137 🟡 ".so 待重编"任务登记未验 target 归属: 改 A 源码却去编 B 库 (09-07)

- **现象**: a1ea3f4d2d (NKAI mutex race fix) 摘取改的是 `AI/Nullkiller2/AIGateway.cpp` (= libNullkiller2.so 源码域), 但登记的部署任务写成"重编 libMMAI.so"; 执行时 `cmake --build --target MMAI` 零编译行 (`Built target MMAI` 无任何 Building 行) — cmake 正确: AIGateway.cpp 非 MMAI target 依赖
- **根因链**: ①训练栈 `--blue_ai MMAI_RANDOM` + 自弈 MMAI_USER → 运行时加载 libMMAI.so (源码 = AI/MMAI/, 与 Nullkiller2 完全两套) ②NK2 已因内存爆炸弃用 → race 根本不在训练链路 ③MMAI/ 全目录 grep removeQuery/receivedAnswerConfirmation = 0 命中, 无同构代码
- **教训**: 登记"待重编"任务前两问 — ①改动文件属于哪个 target (看 AI/<目录>/CMakeLists.txt) ②训练栈运行时实际加载哪个 .so (看 train py 的 --xxx_ai 参数); 零编译行 = 依赖未变的正确信号, 不是编译失败
- **现状处置**: 改动留在 NK2 源码树 (双树已同步), 未来回用 NK2 时重编 libNullkiller2.so 即生效; 误备份 libMMAI.so.bak_race_0907_2252 ×2 留档无害
- 状态: 🟡 已纠偏结案, 登记规范沉淀

### #138 🔴 fork Windows 构建 DLL 污染: 24 种 GCC 版本混装 = 内存损坏 (09-08)

- **现象**: fork VCMI GUI 到 lobby 后崩, headless+testmap 也崩; 崩溃地址随机 (NULL+8 / 0x260021d8be0) — 典型内存损坏; 官方 VCMI 不崩 (MSVC 纯统一)
- **真因**: fork bin 目录 324 个 DLL 来自 24 种 GCC 版本 (Rev5 16.1.0 102个 / Rev1 16.2.0 54个 / Rev2 16.1.0 47个 ... 甚至 4.8.0 1个); VCMI_lib.dll / VCMI_client.exe 编译用 GCC 16.2.0, 但 STL 对象跨 DLL 边界时混入 15.x/14.x STL ABI — 内存布局不兼容 = 随机崩
- **根因链**: 多次手动复制 DLL (OBS lua51 → msys64 lib → ...) 叠加清理时误删+重建, MSYS2 pacman 升级后各包 DLL GCC 版本漂移无统一规范
- **修复**: 备份 fork 特有文件 (VCMI_client.exe / VCMI_lib.dll / SDL2 系列 / avcodec-63 系列 / BattleAI.dll / onnxruntime.dll / lua51.dll) → 清空 bin 所有 DLL → robocopy msys64 mingw64/bin/*.dll 全量覆盖 → 还原 fork 特有文件; 323 DLL 最终 GCC 分布: 16.1→164 / 16.2→56 / 15.2→67 / 14.2→8 (同大版本 ABI 兼容)
- **教训**: ①Windows 二进制混装 GCC 版本 = 定时炸弹, 必须单一大版本 ②fork GUI 崩溃排查第一步先看 `strings *.dll | grep 'GCC:' | sort -u` ③fork 构建在 WSL GCC 13.3.0 交叉 → Windows 端 DLL 源是 MSYS2, 两者版本必须对齐 (或用 WSL gcc produce .dll 直接拷)
- 状态: ✅ 已修复 + 固化流程 (备份 → 清空 → robocopy msys64 → 还原)

### #139 🔴 官方 VCMI 1.7.5 与 fork ModelAI.dll ABI 不兼容: MSVC vs GCC name mangling (09-08)

- **现象**: 官方 VCMI 1.7.5 (MSVC) 拷贝 ModelAI.dll (GCC 16.2.0) + 必需的 GCC 运行时 DLL (libstdc++-6/libgcc_s_seh-1/libwinpthread-1) → 启动报错 "无法定位程序输入点 LIBRARY 于动态链接库 AI\ModelAI.dll"
- **真因**: 双方 VCMI_lib.dll 同一个 `GameLibrary::LIBRARY` 全局变量, MSVC 导出名 `?LIBRARY@@3PEAVGameLibrary@@EA`, GCC 导出名纯 `LIBRARY` — DLL 加载时找不到 `LIBRARY` 符号
- **尝试过**: 用 fork VCMI_lib.dll (GCC) 覆盖官方的 → 官方 client 是 MSVC 编译, 反过来找不到 MSVC 修饰的符号 → 同样崩; 跨编译器混 lib 无可行路径
- **结论**: 官方 VCMI 1.7.5 (MSVC) **永远无法加载** fork ModelAI.dll (GCC); 必须用同代同编译器的 VCMI; 路径 = 用 fork (GCC) 全链路 / 或 ModelAI 用 MSVC 重编 / 或等官方 VCMI 1.8.0 MSVC + 重编 AI
- **替代验证**: fork VCMI GUI (DLL 修复后) → lobby → 战斗模式 → ModelAI 加载成功: `Player blue will be lead by ModelAI` → `Opening ModelAI` → `Loaded ModelAI` ✅ (崩在 AI 首轮行动是别的问题, 不是加载)
- 状态: 🟡 已定位结案, 替代验证通过

### #140 🟡 VCMI 数据目录隔离实验结论 (09-08)

- **现象**: fork/官方 VCMI 均崩 → 做隔离实验: 重命名 `My Games/vcmi` → 官方 VCMI 新目录空的 → 不崩; 逐步回搬 Data/Mods/Maps/config → 定位 **Maps 目录** 非根因 (169 个原版 .h3m 时间戳 1999-03-28, 无坏文件); 真正根因在 fork 二进制/DLL (见 #138)
- **过程快照**: msys64 DLL 覆盖后 fork 到 main menu + lobby + PlayerStartsTurn → 崩在 AI 首轮行动 (NULL+8, StupidAI 也崩 → 非 ModelAI 逻辑); headless+testmap debugStartTest 初始化路径更早崩
- **教训**: GUI 崩溃定位先排除数据目录 (重命名隔离 5 分钟), 再看二进制; DLL 版本检查命令 `strings *.dll | grep 'GCC:' | sort -u` 10 秒定位
- 状态: 🟡 隔离方法固化, 根因已分流

### #144 🟡 MOVE_TO 翻译层认知坑: act 无 24 ≠ 强制窗失效 (09-09)

- **现象**: T06 capture 攻坚时分析 act 序列, 全历史 0 次 act=24, 误判 "move_to_force=60 强制窗外模型不采 24 → 引导驱动不了" 为双死锁之一, 白做 args 覆盖 (无害但多余)
- **真因**: MOVE_TO(24) 是**中间语义动作** — ep_runner 发 a=24 后, MOVE_TO 执行块 (L764-814) 立即把它翻译为方向动作 (C++ next_dir / 全图 BFS / 15×15 BFS / 贪心回退), traj 记录的是翻译后的 a — **act 里永远不会有 24**
- **更深一层**: 引导系统是**动作替换制** — 引导块算出 move_target (tx 非 None) 即接管, 无论模型采样什么都替换为引导方向; 与 move_to_force 强制窗无关。强制窗只影响 "a 的初值是 24 还是模型采样"
- **教训**: ①分析动作序列前先确认三层语义: 发送值 (a) / 记录值 (traj act) / 引擎执行值 (passable/visit), 三者可不同 ②判定引导是否生效看 move_target/tx 是否非 None, 不看 act 里有没有 24 ③诊断前先读执行块的翻译逻辑, 别拿记录层当发送层
- 状态: ✅ 认知修正 (args 覆盖保留无害)

### #145 🔴 T06 守卫格振荡陷阱: 站上格黑名单失效 → fail-count 贴脸计数 (09-09)

- **现象**: T06 capture 攻坚, hero 在守卫格 (5,7) 与邻格 (4,6) 间回跳振荡 26/60 步 (traj_ep.json 位置序列实锤), 两局 act 逐字相同 = 确定性剧本; capture 路径被堵 (两局 200 步 truncation r=28.68/30.03)
- **根因链**: ①战斗未触发/未胜 (无 [GUARD]/守卫未消失/英雄未死 — T06 守卫对象疑与 fix_t06_maps.py aggression 补丁相关, 引擎侧待专项) ②守卫排除逻辑只在 hero 恰在格上生效, 离格后 guard_best 又选中 → 往复 ③cycle_detect=5 的八步窗抓不到 2 周期振荡 (回位 4 次<5 阈值) ④位置级罚分 (r-=3) 只扣分不强改行为
- **黑名单两版迭代**: v1 = hero 站上守卫格即黑名单 — **没接住** (hero 在邻格反复被引擎拒, 从未站上, 位置重合条件永不触发; 验证局 act 逐字复现) → v2 = **fail-count 贴脸计数**: guard_best 选中且 dist<=2 每步 +1, 3 步未胜 → 黑名单 — 不依赖站上, 邻格停滞即计数
- **联动坑**: 守卫接近梯度块 (+0.3/格) 必须同步排除黑名单守卫 — 否则梯度把 hero 拉回已放弃的守卫, 与蓝城引导对抗成新振荡源
- **验证**: r 序列 28.68 → 30.03 → 41.80 (v1) → **93.95 (v2, 46 步守卫胜快速闭环)** — 振荡解除
- **教训**: ①黑名单触发条件要选 "肯定发生" 的事件 (邻格停滞计数), 别选 "可能不发生" 的 (站上格) ②修正引导类行为时, 所有拉力源 (引导/梯度/罚分) 必须同步改, 单点改会被其他拉力对抗 ③验证脚本 = 解析 traj_ep.json 的 hero 位置序列 (obs[3203] active hero → heroes 段 [128+idx*26+2/3]), 回跳计数 + 唯一位置数两指标 10 分钟定位振荡
- 状态: ✅ v2 生效 (r=93.95 实锤), 引擎侧守卫战斗未触发待专项

### #146 🟡 BHERO_KILL 空拍误报: live_slots=0 = heroes 段整段空 (09-09)

- **现象**: BHERO_KILL 埋点 (0908 上线) 捕获 9 起事件 (T05×6 + T06×3), 甄别发现全部 live_slots=0 = heroes 段整段空拍 — T06 三蓝英雄同 step 56 齐"消失"实锤非真实歼灭; 初判 "埋点工作正常, 击杀 0 = 真实观测" 被推翻
- **根因**: heroes 段 (obs [128+hi*26]) 偶发整段空 (引擎 obs 填充链偶发未填充), 空拍使全部 blue id 从集合消失 → 差集误报击杀
- **修复**: ①ep_runner 空拍防护 — `_bnow` 为空时跳过差集与 prev 更新 (防误报 + 防 prev 集合被清空) ②check_duel_watch.py 过滤 live_slots=0 行
- **教训**: ①差集检测类埋点必须防 "全空拍" (空 vs 真消失语义不同) ②事件行带 live 槽数自证真伪 ③结论下前先抽查事件明细形态 (9/9 全同一形态 = 埋点 bug 而非行为)
- 状态: ✅ 防护生效 (0 新误报), obs 填充链空拍根因待立项

### #147 🟡 间歇性局级慢速: fuse 雷达外的 4-8s/步模式 (09-09)

- **现象**: 训练 16% 局全程慢 4-8s/步 (正常 1.4s/步, 局耗时 311-398s vs 99s), 跨图均匀分布 (T05×27/T06×7), 步数与 r 正常; 0909 晨极端案例 48s/步, 后自行恢复
- **易误判**: ①初判 "单步卡 300s fuse 兜底" — 错, fuse (strategic_env.py L861 _adventure_wait timeout=300s) 只兜单步超时, 慢性 4-8s/步在雷达外 ②与 R7 battle query 卡死区分: R7 是死等冻结 (fuse 触发), 本现象是活着的慢 (hermes 日志持续写入)
- **排查锚点**: ep_runner CPU 26% (在等引擎) + 服务器侧无对应打点 → 疑宿主资源抖动/引擎偶发慢模式, 根因未定位
- **教训**: ①局耗时分析用 time 字段差分 (主日志 step 行), 超 2 倍中位数即异常局 ②"fuse 未触发" ≠ "没有慢问题" — fuse 只兜死等, 兜不了慢性慢 ③诊断先分型: 冻结型 (fuse 可兜) vs 慢性型 (需外部监控)
- 状态: 🟡 登记观察, 恶化再专项

### #148 🔴 GUI 死锁根因: detached 线程持锁路径退出 → interfaceMutex 永久失锁 (09-09)

- **现象**: ModelAI GUI 复测, AI 行动后 ~2s 画面永久冻结; minidump 实锁 owner = 已死线程的 pthread 结构, 主线程 + runNetwork 双双死等 ENGINE->interfaceMutex
- **根因**: ModelAI `heroMoved` 回调 (网络线程) 启动 detached 延迟线程调 `endTurn` — detached 线程生命周期失控, 持锁路径随线程退出失效 → interfaceMutex 状态损坏 (永久失锁), 全进程死等
- **修复 (D:\vcmi_model_ai\model_ai.cpp)**: 移除 detached 线程 → `heroMoved` (无战斗) / `battleEnded` (有战斗) 回调内**同步调用 endTurn** (waitTillRealize=false 非阻塞, 与 yourTurn 回调模式一致) + battle_active 原子变量区分两条路径 + in_my_turn 及时重置防 battleEnded 误触发
- **教训**: ①回调线程里禁开 detached 线程做续接动作 — 生命周期失控 = 锁资源泄漏定时炸弹 ②GUI 锁问题的终结证据是 minidump 的锁 owner 归属, 不是猜测 ③同步 endTurn 的前提是非阻塞语义, 先确认 waitTillRealize=false 再同步
- 状态: ✅ 修复部署 (旧版备份 ModelAI.dll.bak_0908_deadlock), gui3 复测 endTurn after heroMoved 正常流转

### #149 🔴 多进程齐崩 = 系统资源耗尽特征, 勿误判应用代码 (09-09)

- **现象**: GUI 复测弹窗崩溃, 直觉归因 VCMI 代码 — 实锤为系统级: 07:14:46 Windows 资源耗尽诊断 (事件 2004, **3 个 python.exe 共吃 36GB commit**, 各 11.5-12.5GB) → 07:18:52-07:19:01 pwsh/GDEPService/agent-tool-host/**dwm.exe** (dwmcore.dll 0xc00001ad) 四进程连锁崩 + LiveKernelEvent 141
- **关键排除证据**: VCMI_client.exe **无** WER APPCRASH 事件、无新 rpt/dmp → 代码层无新崩溃; 复测撞上资源耗尽窗口 (commit 打满 → 分配失败 → 卡死/弹窗)
- **排查命令沉淀**: `Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001}` (APPCRASH 详情) + `System` 日志 ProviderName='Microsoft-Windows-Resource-Exhaustion-Detector' Id=2004 (虚拟内存不足, 直接列出元凶进程与占用字节数) + `Get-CimInstance Win32_OperatingSystem` 算 CommitUsed/Limit
- **教训**: ①"弹窗崩溃"先查 WER 事件日志再怀疑代码 — 单进程崩看 Application 1000, **多进程齐崩 = 资源耗尽指纹** ②dwm.exe 崩会伪装成"游戏卡死/崩" (画面冻结) ③Resource-Exhaustion 2004 直接给元凶 PID 与字节数, 一查一个准
- 状态: ✅ 定性完毕 (VCMI 无责); 3×python 来源待用户确认 (进程已退无法回查)

### #150 🟡 Windows minidump 抓取与解析三坑 (09-09)

- **坑 1**: rundll32 调 MiniDumpWriteDump 失败 (文件不存在/权限) → 改 `py/take_dump.py` ctypes 直调 API (`MiniDumpWithFullMemory|HandleData|FullMemoryInfo`)
- **坑 2**: python minidump 库对 full dump 支持差 — `baseaddr` 属性名错 (实为 `baseaddress`)、LOCATION_DESCRIPTOR 无 len()、Memory64List 栈内存读不到 → `py/walk_stuck_dump.py` 手动解析 stream directory + Memory64ListStream (type=9, n_ranges/base_rva/data_rva 三段式)
- **坑 3**: 无符号栈只见 RVA — `py/identify_all_threads.py` 用 .pdata 段函数边界 (bisect) + 导出表把线程栈 RVA 归属到函数; `stuck4_cfbb.py` 定位疑似线程 start_routine; `stuck4_heap.py` 查 GAME/mutex 周边堆完整性
- **教训**: ①工具链固化在 py/ 下五件套, 下次 GUI 死锁直接复用 ②minidump 库不可信时手解二进制格式反而快 (格式文档充分) ③抓 dump 时机 = 冻结现场时 (MiniDumpWriteDump 可对活进程抓)
- 状态: ✅ 工具链可用, 死锁 owner 定位全靠它

### #151 🟡 Windows GUI 中文界面 + 第三方输入法: 两条独立崩溃路径 (09-09)

- **现象 A**: 中文界面下选图 → "Disaster happened. Attempt to read from 0x0" — **界面语言编码转换崩溃**, 与地图/逻辑无关
- **现象 B**: 第三方输入法 DLL 注入游戏进程 → 堆损坏 (随机时点崩), 与 "忘记切输入法" 复测记录吻合
- **规避**: VCMI 界面语言切 English + 系统输入法切英文 (ENG) 再复测; 两坑均无需改代码
- **教训**: ①中文 Windows 环境跑开源 GUI, 语言/输入法是独立于代码的崩溃源, 复测前先固定这两变量 ②崩溃现象随环境变量消失 = 环境因, 随代码版本复现 = 代码因
- 状态: ✅ 切英文后选图通过 (后续卡死另案, 见 #149)

### #152 🟡 fork Windows 构建 AI DLL 缺失: settings 默认名无对应产物 (09-08 闭环, 09-09 归档编号)

- **现象**: battle-only 对局 "Server gives turn to red 后 3 秒崩", StupidAI 也崩 — 初判 ModelAI 逻辑问题, 实锤与模型无关
- **根因**: `Client.cpp L253-257` 全 AI 玩家无条件走 `CDynLibHandler::getNewAI(settings ai.adventureEnemyAI)`, 默认值 "Nullkiller2" 而 `bin/AI/` 仅 ModelAI.dll + 2016 官方旧 BattleAI.dll — build.ninja 只有 NK2/StupidAI 的 .obj 编译规则**无链接目标** (fork Windows 构建从未产出 adventure AI DLL) → LoadLibraryW error 126 → throw → 崩
- **修复**: settings.json (My Games/vcmi/config) 恢复 ai.adventureAlliedAI/adventureEnemyAI = "ModelAI"; 验证 PASS (headless testmap day=31 回合轮转正常, query 链闭合)
- **教训**: ①配置里的 AI 名必须与 bin/AI/ 下 DLL 文件名一一对应, aiNameForPlayer 的存在性检查只查文件不查配置 ②"StupidAI 也崩"排除模型嫌疑但没排除配置/DLL 供给层 ③排查入口 = Windows 事件日志三类签名 (fork 0x40000015@VCMI_lib / 0xc0000374 堆 / fail-fast) + IFEO PageHeap 复现
- 状态: ✅ 已闭环 (任务清单 09-08 条), 本条补踩坑编号归档

### #153 🔴 [GUARD]/[MINE] 位置重合判据 anchor↔visitable 失真: 1442 条假糖 + 真战斗漏奖 (09-10)

- **现象**: T05 高分剧本 r 130-168 / duel r=93.95 的 +100 构成可疑; ep_1386 hero 站 (10,9) 拿 +100 但全程 0 引擎战斗; ep_418 [GUARD] step32 早于 battleStarted (发奖时战斗还没发生)
- **根因**: vmap objects.json x,y = `setAnchorPos` = 引擎 **anchor** 语义; monster 本体格 (BLOCKED|VISITABLE) = anchor − visitableOffset (mask 'A' 格位置, 3×3 中心 → offset(1,1)); hero 移动到 visitable 格才 visit 触发战斗 → 旧判据查 anchor 格 = hero **路过贴脸格假发奖**, 真战胜后站 visitable 格判据不匹配**漏奖**
- **修复**: ep_runner `_anchor_to_visitable()` 解析 template.mask 复刻 C++ `calculateVisitableOffset` (找 'A'/'T'), get_guards/get_objectives mines 换算; towns 不换算 ([TOWN] dist<=1 两侧同 anchor 语义自洽); 下游黑名单/梯度/fail-count/引导目标经源头自动生效
- **教训**: ①位置重合判据必须核对引擎坐标语义 (anchor vs visitable), Python 静态表与引擎对象坐标系不是天然一致 ②事件奖励口径优先 obs 直报字段 (owner 变化/对象消失), 位置重合是最后手段 ③假糖污染所有下游统计 — 归因前先查数据采集口径
- 状态: ✅ 修复已实施 (py_compile + 单测 3 组 + 真图对照全过), 新口径首命中验证 (duel (4,6) ×2 局 / 52X52_02_mir (38,39) 均为 vis 位), 遗留 = T06 守卫战斗触发时有时无 (aggression) 专项

### #154 🟡 PowerShell 包裹 wsl bash -c 时 $var/$( ) 被 PowerShell 层吃掉 (09-10)

- **现象**: `wsl bash -c 'for f in ...; do ... $f ...; done'` 循环变量全空 / `$(cmd)` 被当 PowerShell 子表达式报 "Variable reference is not valid"
- **根因**: PowerShell 先解析外层字符串, `$f`/`$A`/`$(...)` 在到达 bash 前已被展开为空; 单引号包裹也不可靠 (多层嵌套)
- **规避**: ①复杂 bash 逻辑一律写成脚本文件 (py/ 下, 参照 audit_r5_trees.sh/stat_t06_guard_battle.sh) 再 `wsl bash 脚本路径` 执行 ②简单单命令才用 wsl bash -c 内联 ③确认: 无变量替换需求的 heredoc python 内嵌代码可直接用
- 状态: ✅ 固化 (本次新增 4 个 py/ 脚本均此模式)

### #155 🟡 pkill -f 同名串自杀: 当前 shell cmdline 含目标名即被自己杀 (09-10)

- **现象**: `wsl bash -c 'pkill -f diag_obj_dump; ... python py/diag_obj_dump.py ...'` 整条命令 exit 15 (SIGTERM), 输出文件都没创建
- **根因**: pkill -f 匹配**全部进程 cmdline** — 同一条 bash 命令行里含 "diag_obj_dump.py" 字面量 (python 调用部分), bash 自身 cmdline 命中模式被杀; `[d]` 字符类技巧只防住 pkill 参数本身, 防不了同行其它部分的字面量
- **规避**: ①pkill 单独一次工具调用 (与目标操作分开) ②或精确 pgrep 取 PID 再 kill ③或模式用字符类且确保整条命令无其他字面量命中
- 状态: ✅ 固化

### #156 🟡 import ep_runner_one 有模块级副作用: 会初始化 env 并跑游戏 (09-10)

- **现象**: 单测 `from ep_runner_one import _anchor_to_visitable` 直接启动 MMAI/VCMI 初始化 + query 流跑到 qid 470+, 输出 141KB
- **根因**: 模块顶层有 env 构造/初始化逻辑 (非全部包在 main guard), import 即执行
- **规避**: ①测试主模块内函数 → 把被测逻辑复制到独立脚本 (或先重构主模块把纯函数抽出) ②禁 import 主模块做单测 ③print 结果必须 flush (被杀进程时缓冲丢失, 建议脚本内加 -u 或 sys.stdout.reconfigure(line_buffering=True))
- 状态: ✅ 固化 (改用独立脚本内联逻辑验证)

### #157 🟡 局耗时数据不可回溯: hermes 日志逐局覆盖 + ep 行无 time 字段 (09-10)

- **现象**: 间歇性慢速 (16% 局 4-8s/步) 需要历史样本定量画像时, /tmp/hermes_ep_*.log 只剩 2-3 个最新局, 主日志 ep 行 (ep_steps/r/act/obs_nz/map) 无耗时字段
- **修复**: ep_runner 加 `_ep_t0` + 局尾 `[EP_TIME] map= steps= secs= r= err=` 打点 + 主日志白名单补 [EP_TIME] (train_wsl2_ppo_v2.py, 主进程改动需优雅重启生效); 基线首样本 52X52_02_mir 73步94s = 1.29s/步
- **教训**: ①观测埋点要前瞻性常驻, "登记观察积累样本"必须确认样本真在积累 (hermes 覆盖机制会丢) ②per-ep 临时日志只做即时诊断, 长期统计字段必须进主日志白名单
- 状态: ✅ 基建完成, 慢局复发时聚合 [EP_TIME] 定位

### #158 🔴 interfaceMutex 泄漏: onPacketReceived 锁作用域收窄破坏 makeUnlockGuard 不变量 (09-10, GUI 死锁根因①)

- **现象**: --testmap 全 AI 局每次回合切换后整体冻结 (Resp=False); dump 显示 runNetwork 卡在 onPacketReceived 的 pthread_mutex_lock + 主线程卡在 USEREVENT 同一把锁; [MUTEX] 打点实锤 LOCKED 后无配对 UNLOCK 即 onPacketReceived EXIT = 锁泄漏
- **根因**: onPacketReceived (CServerHandler.cpp:1061) 的 scoped_lock 只覆盖 DISCONNECTING 检查 (源码级作用域即如此), 包处理 (pack->visit) 无锁运行; 而深层 handler CPlayerInterface::waitWhileDialog (CPlayerInterface.cpp:1393) 的 `makeUnlockGuard` 语义 = "析构时重锁恢复现场" — 无锁调用时析构重锁**凭空加锁且无人配对解锁** → 每次回合切换泄漏一锁
- **修复**: onPacketReceived 用 `optional<unique_lock<GameEngine::LoggingMutex>>` 持锁覆盖整个 pack->visit, 恢复"包处理持锁"不变量
- **教训**: ①makeUnlockGuard/makeUnlockSharedGuard 隐含前提 = "调用者持锁" — **任何锁作用域改动必须全链审查所有 guard 用户** ②guard 是 RAII 但"恢复现场"型 guard 的不变量靠调用约定, 编译器/RAII 救不了 ③LeakSanitizer 类工具不覆盖 std::mutex, 只能靠打点收支对账 ([MUTEX] LOCKED vs UNLOCK 计数)
- 状态: ✅ 修复 + day=31 验证

### #159 🔴 SPECTATOR 无 PlayerState: getPlayerState(-4) 返回 null 无判空崩溃 (09-10, 死锁修复后第二层)

- **现象**: 死锁修复后跑到 day=2 崩溃 `0xC0000005 读 0x6d8`, 前奏是 "getResource: No player info!" ×N 刷屏; dump 崩点 `mov rdi,[rax+0x6d8]` 前一条是 `call CGameInfoCallback::getPlayerState(PlayerColor, bool)` (IAT 0xa9e5b8)
- **根因**: testmap-onlyai 的观众视角接口 playerID=**SPECTATOR(-4)** (崩溃时 rdx=0xfffffffc 实锤), 游戏状态里 SPECTATOR 无 PlayerState → getPlayerState 返回 null → AdventureMapShortcuts::optionCanViewQuests (L647) `->quests.empty()` 无判空解引用 (+0x6d8/+0x6e0 = vector begin/end 对)
- **修复**: optionCanViewQuests 判空 (CPlayerInterface.cpp:1363 已有同类先例 "PS NULL GUARD: spectator has no PlayerState")
- **教训**: ①onlyai/观战模式引入后, 所有 `getPlayerState(interface->playerID)` 调用点都要假设 SPECTATOR; 上游无此模式所以上游代码天然不防 ②崩溃前奏的 verbose 警告刷屏 ("No player info!") 就是同源查询失败信号, 看到 spam 就该想到同族调用里有没有漏判空的
- 状态: ✅ 修复 + day=31 验证

### #160 🟡 winpthreads Normal mutex 不记录 owner: dump 静态分析定不出持锁者 (09-10)

- **现象**: 冻结 dump 里读 interfaceMutex (ENGINE+0x98) 的 pthread_mutex_t, 值 {state=2, type=0, +0x08=0x1618, owner=0xffffffff} — 曾把 0x1618 误判为持锁死线程 TID
- **根因**: ①winpthreads `pthread_mutex_t` 本体是**指针** (GENERIC_INITIALIZER=-1 惰性初始化), 真结构体在堆上; ②内部布局 `{state(Unlocked/Locked/Waiting), type(Normal/Errorcheck/Recursive), event(auto-reset HANDLE!), rec_lock, owner}` — **仅 Recursive/Errorcheck 记录 owner, Normal 恒 0xffffffff**; 0x1618 = event 句柄 (内核 HANDLE 数值巧合性地小)
- **规避**: ①std::mutex 死锁的持锁者定位**必须运行时打点** (LoggingMutex: LOCKED/UNLOCK + tid + `__builtin_return_address(0)` → .pdata 映射锁点), dump 只能证明"锁被持有"不能证明"谁持有" ②冻结 dump 抓晚了锁内存会被复用污染 (gui8 教训), 抓现场要快
- 状态: ✅ LoggingMutex 已常驻 GameEngine (复发雷达)
- 关联: 知识库 "09-10 GUI 死锁终局闭环" 章

### #161 🟡 MinGW windows.h 宏污染三连: IGNORE / NOMINMAX / 作用域 (09-10 重编)

- **现象**: 插桩加 `#include <windows.h>` 后连环编译错: ①Canvas.h `IGNORE` 枚举成员报 "expected identifier before numeric constant" ②NOMINMAX 重定义冲突 (libstdc++ os_defines.h 预定义) ③`GetCurrentThreadId` 未声明 (部分 TU 无传递包含)
- **根因**: winbase.h `#define IGNORE` (NOGDI 排除的是 wingdi, **winbase 排不掉**); libstdc++ 的 os_defines.h 已 `#define NOMINMAX 1`, 裸 `#define NOMINMAX` (空体) 与之不同 → 重定义告警/错误
- **规避**: ①标准防污染块 `#ifndef` 全守卫 + `WIN32_LEAN_AND_MEAN/NOMINMAX/NOGDI/NOUSER/NOKERNEL/NOSOUND` + `#undef IGNORE` (windows.h 之后) ②非 Windows 兜底 `static inline unsigned long GetCurrentThreadId(){return 0;}` ③**LoggingMutex 等包装器的实现放 .cpp, 头文件只留声明** — 避免在广包含头文件里引入 windows.h (一处污染全树枚举/标识符)
- 状态: ✅ 固化 (5 处插桩 TU 统一模式)

### #162 🟡 fork Windows 重编四坑: genex 泄漏 / 链接序 / 缺符号 / 数据目录 (09-10)

- **①CMake regen 泄漏**: libFacade/CMakeLists.txt 的 `target_link_libraries(vcmi PUBLIC $<TARGET_PROPERTY:vcmiMain,INTERFACE_LINK_LIBRARIES>)` 嵌套 genex 在 regen 时把 `$<LINK_ONLY:ws2_32>` 原样写进 build.ninja → ninja "bad $-escape"; 修补: `$<LINK_ONLY:X>`→`X` 再裸 token→`-lX` (**每次 CMakeLists 改动触发 regen 都要重修**)
- **②MinGW 链接序**: VCMI_server.exe 链接行 servercommon.a 在 VCMI_lib import lib 之前, servercommon 新增的 lib 符号引用 (__imp_) 解析不到; 修复: serverapp 行尾重复 `vcmi` (ld 从左到右, archive 后需再给 import lib)
- **③ENABLE_ML=OFF 缺符号**: AIGateway.cpp include 的是 ML/strategic_state.h, adventure_capture_turn 定义在 ML 侧 (OFF 不编) — 修复: facade_SRCS 加 server/strategic_state.cpp (仅依赖 lib 头) + `target_compile_definitions(vcmi PRIVATE VCMI_DLL=1)` (否则 dllimport 视图 __imp_ 未定义); **注意 target_compile_definitions 必须在 add_library 之后**
- **④NK2 残留**: AIGateway.cpp 三处 `getDate` (L177/778/1678) → `getCalendar().getCurrentDay()`; 一个未声明占位函数 `showGarrisonDialog_unused_placeholder` (09-09 手改残留) 删除
- 状态: ✅ 三产物 09-10 版落地, 备份 bin_backup_0910

### #163 🟡 二进制 ≠ 源码树: 08-18 exe 含未提交临时 hack, 行为对不上源码 (09-10)

- **现象**: 08-18 编译的 VCMI_client.exe 启动后**无人操作自动进 battle lobby + 自动开局** (Twins + ModelAI), 全源码树 grep 找不到任何自动开局逻辑 (EntryPoint/openLobby/MLClient 全排除)
- **根因**: 08-18 构建时的源码状态含未提交的临时 hack (有头验证期改动, 后来没进树) — **二进制是某个历史瞬间的快照, 源码树是另一个**; "08-18 产物 + 全部已提交修复" 的假设不成立
- **规避**: ①复测行为对不上源码预期时, 先怀疑二进制/源码漂移 (git log 时间 vs 产物时间戳) ②重编后行为变化 (如自动开局消失) 不是回归, 是 hack 消失 ③新复测口径 = `--testmap Maps/Twins.h3m` (确定性、源码可解释、bypass lobby 崩溃)
- 状态: ✅ 固化 (复测口径已更新进知识库 checklist)
