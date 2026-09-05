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

### #130 🔴 PowerShell 双引号内 \ 子表达式展开: wsl 复杂命令被撕裂 (09-02)

- **现象**: wsl bash -c \

### #130 🔴 PowerShell 双引号内 $(...) 子表达式展开: wsl 复杂命令被撕裂 (09-02)

- **现象**: `wsl bash -c "... $(ls -t ...) ..."` 中 `$(...)` 被 PowerShell 当子表达式先行执行 (报 head 不存在/空变量), bash 收到残缺命令; heredoc 正文同样被撕 (本次归档操作亲自复现)
- **正确姿势**: 复杂命令/长文本写入文件 (Write 工具 → /mnt/d/.../_tmp_xxx) 再 `wsl bash -c "cat 文件 >> 目标"`, 用完即删; 单条简单命令才直接 wsl bash -c
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
