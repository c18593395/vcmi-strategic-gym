# WSL踩坑点 — 训练-奖励与策略

> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。

---

### 23. try/catch 吞异常导致观测全零

- **现象**: strategic_state_update 内 try/catch 包裹所有逻辑，异常被吞，观测全零

- **解决**: 去掉 try/catch，让异常暴露；或在 catch 里输错 e.what()



### 24. ctypes 跨进程访问全局变量

- **现象**: Python 脚本 A 设了 g_strategic_state，Python 脚本 B 读出来是 NULL

- **原因**: 两个 python3 调用是不同进程，内存不共享

- **解决**: 必须在同一个 Python 进程中 init 和 read



---



### 32. 观测维度和 ctypes 结构体偏移必须严格同步

- **现象**: passable[8] 加入 C++ struct 后 obs[-8:] 全零，C 和 Python 的 sizeof 一致但读取位置不对

- **根因**: 英雄字段 8×23=184 超过 OBS_DIM=264 的剩余空间，passable 被写到 idx=242 而非 idx=256

- **解决**: obs 构建器强制写 passable 到 OBS_DIM-8 位置，不从当前 idx 继续



### 1. 方向映射不统一 → 模型坍缩

- **现象**：200步全选同一方向，r=-89.5/ep，vloss→0

- **根因**：`strategic_state.cpp` passability 用的 E-start 方向，`AAI.cpp` moveHero 用的 N-start。passable[0] 检查 East，action=0 移动 North → 模型认为"方向0可通"但"选方向0走不通"

- **修复**：全系统统一 `dx={0,1,1,1,0,-1,-1,-1} dy={-1,-1,0,1,1,1,0,-1}`（N-start CW）

- **三处必须一致**：`strategic_state.cpp` passability、`AAI.cpp` moveHero、Python 侧



### 65. 旧模型权重编码旧 obs 模式 — 清权重才能受益于新 obs

- **现象**: 修好 passability/day/map_size 填充后，旧模型仍然 act=[10,10,...]（END_TURN），不探索

- **根因**: 旧模型在 obs_nz=29（缺数据）上训练了 73000+ step，权重编码了"obs 大部分为零 → 无用信息 → 执行 END_TURN"

- **修复**: `rm wsl2_model.pt wsl2_model_state.pt; rm checkpoints/*.pt`，重启训练

- **验证**: 新随机模型首次 ep 就 obs_nz=61（数据完整），avg_r 从随机水平开始正常学习



---



### 6. 采集子进程无 watchdog → NK2 启动阶段卡死挂起整条采集

- **现象**: collect_bc.py 主进程 `subprocess.run(cmd)` 无限等待；ep1 (Key to Victory.h3m) 子进程卡 `futex_do_wait` 1h27m，CPU 仅 19s，无 npz 产出，输出进 pipe 无人读（日志全丢）

- **根因**: NK2 chain 重试死循环（已知 ~50% 概率）可发生在 **reset 启动阶段**——`connector.init()`/首个 yourTurn 等待无超时兜底（boot_timeout/vcmi_timeout/wait_timeout 只覆盖采集循环），子进程永久挂起，主进程 `subprocess.run` 无 timeout 跟着无限等

- **修复**: 主进程 `subprocess.run(..., timeout=900)` 整局硬超时，`TimeoutExpired` → kill 跳局 continue；重启采集并 `> collect.log 2>&1` 落盘日志

- **验证**: 修复后 ep0 正常落盘 44KB，ep1（之前卡死图）reset OK 正常采集

- **教训**: 所有子进程隔离式脚本必须有**整局级** watchdog（覆盖启动+运行全程），不能只依赖 env 内部各阶段 timeout；后台进程 stdout 必须重定向到日志文件



### 9. 被动资源收入做 per-step 奖励 → 模型坚守 END_TURN (C8.5)

- **现象**: 训练 200 步全 act=10 (END_TURN), r=2000/局 (每步 +10)

- **根因**: reward_gold_mult=0.01 → END_TURN → day 推进 → 城镇被动 gold 收入 → 每步 +5~10 白拿 → 坚守 END_TURN 最优

- **修复**: reward_gold_mult=0.0 (被动收入只做终局奖励)

- **教训**: 任何被动收入 (gold/town/资源产出) 都不能做 per-step 奖励; 主动行为驱动必须用事件奖励 (占矿/杀敌/占城) + 态势感知



### 13. fill 无锁直读 CGameState → NK2 决策损坏 (2026-08-01)

- **现象**: NK2 所有 moveHero 被服务器拒 ("destination tile is blocked" 死循环), 非崩溃

- **根因**: fill_exploration/fill_mines 在 NK2 后台线程直读 gs.getMap()/fogOfWarMap（无锁）→ 与 NK2 规划线程数据竞争 → NK2 决策数据损坏

- **定位**: H2 隔离实验（注释 fill 调用 → NK2 恢复 100 pairs 正常）

- **修复**: fill_exploration/fill_mines 内部 `std::shared_lock gsLock(CGameState::mutex)`（AAI.cpp 同模式）

- **教训**: 回调里直读 CGameState 必须加锁; callback API（getTile 等）内部有锁, 直读 gs 没有



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



## 踩坑 #73: PPO 策略坍缩链 — 横跳 → END_TURN 刷步 (2026-08-19)

- 现象: 训练 68ep 后动作纯 3/7 (SE/NW) 交替, avg_r -0.5~-0.8 稳定; 加横跳惩罚后模型躲向 END_TURN 刷步 (80%+ 动作 10)

- 诊断法: bc_model vs 训练模型同图对比诊断局 — bc 能探索 (走出出生点) = 训练伤害 (policy collapse) 非地图强制; passable 段 obs[3211:3219] 充足却打转 = 策略问题非 mask

- 根因链: 探索奖励太弱 (+1 vs step -1.5) → 走出去净亏 + 遇敌风险 → 横跳安全; 横跳惩罚 (-2) 后 END_TURN 更安全 → 刷步

- 修复: 横跳惩罚 (回两格前位置 -2) + 探索奖励 2.5 + **END_TURN 冷却 (连续 3 次屏蔽 logits[10])** + 熵 0.01→0.05 + 屏蔽 11-24 (未实现码)

- 验证: 第 3 轮 ep1-7 avg_r -1.2~+0.5 (首次转正), vloss 65-200 (上轮 400-640), 无刷步无纯横跳

- 教训: 惩罚性机制必须配套逃生通道 (横跳罚 → 模型躲 END_TURN → 需冷却); 单方向奖励调整会连锁

## 踩坑 #74: MOVE_TO 目标漂移 — 每步重选最近目标 → 来回走 (2026-08-19)

- 现象: target_list 填充正确但英雄来回漂移 (朝目标 A 走两步, 重算后改朝 B, 又改回 A...)

- 根因: 展开逻辑每步从 target_list 重新选最近目标 — 位置微动导致最近目标在多个之间跳变

- 修复: 粘滞 (move_target 状态变量, 上次目标未到达继续用; 到达才重选) + stall 检测 (连续 6 步距离不减小 → 换目标, 防被堵死循环)

- 教训: 目标导向动作必须带记忆 (sticky target), 纯贪心每步重选 = 振荡



### #76 (2026-08-19): ep_runner 缺 import numpy — 被动作 24 零出现掩盖的潜伏 bug

- 现象: 第 5 轮加 --move_to_force 强制引导后, 第一局 traj 报 error 'name np is not defined'

- 根因: ep_runner_one.py 从未 import numpy, 但 MOVE_TO 展开段 (np.asarray(obs[3251:3315])) 08-19 凌晨就加了; 第 4 轮动作 24 从未被采到 (bias 失效), 该分支从未执行, bug 潜伏 55 ep 未暴露

- 修复: 头部补 import numpy as np

- 教训: 未被执行到的代码路径上的 bug 不会被测试发现 — 引导/测试必须真的走到目标分支 (第 4 轮 24 零出现本身就是异常信号, 当时被当成'bias 无效'未深挖)



### #77 (2026-08-19): logits 偏置对模型从未见过的动作码无效 — 引导用采样强制

- 现象: 第 4 轮 --move_to_bias 2.0 线性衰减, 55 ep 动作 24 零出现

- 根因: BC 权重从未见过 24 码, 其原始 logit 极负 (-10~-30); logits 加 2.0 相对尺度太小, softmax 后概率仍 ~0, 采样永远选不到

- 修复: 第 5 轮改采样强制 (--move_to_force N: 每局前 N 步直接 a=24 不走采样), bias 仅作辅助

- 教训: 对'训练中从未出现/BC 从未见过'的动作码, logits 微调引导无效, 必须用采样约束 (强制/概率采样) 让样本真正进入 buffer





## 踩坑 #78: 强制引导动作空转 — MOVE_TO 无目标时原地 27 步 (2026-08-19, 第 5 轮判死实锤)



### 现象

- 采样强制 (每局前 26 步强制动作 24) 生效, 但 traj 位置序列前 27 步完全不动 (pos (13,15,0) 连续重复)

- 出生点附近 target_list 空 / 无可走目标 → 24 展开无移动效果, 仍消耗 step_fixed

- 后果: 模型学到 "24 = 无奖励", 强制区外 24 自发率 ≈ 0; 引导变成纯噪声污染训练



### 根因

- 强制引导只保证"采样到动作码", 不保证"动作产生状态变化" (选 24 不移动 = 假动作)

- target_list 空时 24 展开路径无兜底 (无目标 → END_TURN 的逻辑在训练端, 但强制期可能未触发或展开空耗)



### 修复方向 (待讨论, 任务清单第 6 步)

- target_list 空时 24 直接映射 END_TURN (动作 10), 不空耗

- 或返回出生点最近可达点 / 最近可走方向, 保证 24 永远产生移动



### 同类教训

- 引导动作 (bias/强制) 之前先验证: 该动作在该状态是否真实可执行且产生状态变化

- 假动作比不引导更糟: 污染动作-奖励关联



## 踩坑 #79: 动作循环惩罚诱发 END_TURN 穿插投机 (2026-08-19, 第 7 轮)



### 现象

- act_loop_penalty=3.0 后, ROUND3 动作 10 (END_TURN) 占比 6%→17.8% 全场第一 (362 次, avg 9→27.8/ep), 10-run≥3 从 11-18 次 → 77 次

- 模式: [走,走,10] 穿插 — 连续 10 计数永远 ≤1, 永不触发 END_TURN 冷却 (-5)



### 根因

- 10 前 2 次免费 (strategic_env.py: 连续 END_TURN ≥3 才 -5) → 穿插节奏下 10 成本 = 0

- 10 插入检测窗口打断 4 连重复 / 8 步交替模式 → 循环惩罚永不触发

- 成本对比: 纯循环 -3/步 vs 穿插 10 = 0 → 模型必然选择穿插投机



### 修复 (第 7 轮 v2)

- 惩罚 3.0 → 1.8 (缩小激励差)

- 检测窗口剔除 10: if a != 10: act_hist.append(a) — 10 无法打断检测, 穿插模式剔除 10 后原形毕露照样触发



### 同类教训

- 惩罚检测必须对"逃生码"免疫 (任何能打断检测窗口的动作都要剔除, 否则成为投机工具)

- 加惩罚前先验证: 动作空间里是否存在 0 成本打断检测的码



## 踩坑 #82: 地形栅格 — _init_baselines 覆盖 + 双 .so 内存隔离 (2026-08-23, Phase I.4)



### 现象

- C++ fill_terrain_grid() 写入 terrain_grid 成功 (fprintf 确认非零数据)

- Python 读 terrain_grid 全 0



### 根因 1: 双 .so 内存隔离 (未彻底解决)

- ctypes.CDLL 加载 libmlclient.so 创建实例 A

- connector (pybind11) 加载 libmlclient.so 创建实例 B

- g_strategic_state / g_terrain_grid 各自独立

- 最终绕过: 用文件传递 (C++ fwrite -> Python np.fromfile)



### 根因 2: _init_baselines() 覆盖数据 (已修复)

- _build_terrain_grid() 正确读到 1201 个非零值

- 但 _init_baselines() 在其后调用, 内含 self._terrain_grid = np.zeros(...)

- 覆盖了刚读到的数据

- 修复: terrain_grid 初始化移到 __init__, _init_baselines 不再碰



### 教训

- Python 方法调用顺序必须检查 — 后调的方法可能覆盖前调的结果

- 文件传递是 .so 双实例问题的可靠绕过方案

- struct 大小匹配 (C++ 9716 = Python 9716) 不等于内存共享



## 踩坑 #83: ep_runner load_state_dict 缺 strict=False (2026-08-23, Phase I.4 C)



### 现象

- CNN 实现后训练启动, 两局完全相同 (16步, r=6.30, 动作序列一模一样)

- 动作包含 17/18/21/22/23 (11-23 范围), 但 logits[11:24] 已 mask 为 -inf

- 16步游戏结束, 不是 END_TURN 导致



### 根因

- ep_runner 加载模型用 load_state_dict(sd) 默认 strict=True

- CNN 参数是新增的, 旧 checkpoint 没有 → 加载失败

- except 捕获后 red_model = None

- red_model is None → 全部随机动作 (env.action_space.sample())

- move_to_force 也被跳过 (检查 red_model is not None)



### 修复

- ep_runner 所有 load_state_dict 加 strict=False (3处)

- train_wsl2_ppo_v2.py 所有 load_state_dict 加 strict=False (6处)



### 教训

- 新增网络分支后, 所有 load_state_dict 必须 strict=False

- 看到"随机动作"时, 先检查模型是否加载成功





---



### 93. optimizer.load_state_dict(strict=False) TypeError → STATE_PATH 永远加载失败丢进度

- 症状: 每次重启日志 "Failed to load STATE_PATH, falling back to MODEL_PATH" → resume_step 恒 0 → 从 BC 权重重来

- 根因: PyTorch `Optimizer.load_state_dict()` 无 strict 参数 (Model 才有); 传 strict=False 抛 TypeError 进 except

- 修复: `opt.load_state_dict(sd["optimizer"])` 去掉 strict; 验证日志 "Loaded train state (model+optimizer, step=N)"

- 教训: 状态加载失败先隔离复现 (单独 torch.load + load_state_dict), except 分支静默降级会掩盖此类 bug 数轮



### 96. NK2 移除 → critic 爆炸 (vloss 159-164) (2026-08-24)

- 原始 env reward -100~-300/ep, BC 初始化的 critic 无法预测; NK2 势函数在掩盖幅度

- 修复: NK2 scale 1.0→0.3 + return normalization, vloss 159→1

- 教训: 大幅度 reward 下 critic 必须看标准化 returns; 移除 shaping 必须同时加 return norm



### 100. 训练意外停止无保存日志 (2026-08-25 09:51)

- 正常停止有 "Shutdown signal received, saving current state..."; 无此日志 = 硬杀/SIGKILL/WSL 终止

- checkpoint 仍完好 (定期/退出保存), 恢复 = 直接重启续训, 重启前 cp train.log 存档



### 116. reward clip 下限 -10 把失败 -200 剪没 → T04 输赢信号失真 (2026-08-29)
- 现象: T04 切换后局 r=-80~-110 却无一局 -200 大负; [TOWN]/胜负局 0 触发, 模型"输也无所谓"
- 根因: strategic_env.py `np.clip(reward, -10, 300)` — 上限 08 月放宽到 300 容纳 +200 胜利, 但下限仍是 -10 → blue 推平我方时 reward_win -200 被剪成 -10, 输赢信号差仅 10 分
- 修复: `np.clip(reward, -300, 300)` 对称放宽
- 教训: 放宽 clip 单侧时必须想到对称事件 (±200 胜负同帧可达两端); 奖励设计评审要看 clip 边界, 事件大额奖励会被静默截断

### 117. T04"有目标却乱逛"三连环: 近目标吸住 + 强制期不够长 + 城镇不在 target_list (2026-08-29)
- 现象: T04 19 局 r=-80~-110 全乱逛, 但 target_list 明明有矿 (type=1), C++ next_dir 全图 BFS 也对 dist=41 远目标有效
- 根因三连环: ① runner 24 展开 = 最近 dist 目标 → 资源堆 dist 5~21 恒压过矿 dist 41 → 200 步在资源堆间游走; ② move_to_force≈28 步覆盖不了 dist 41 的奔矿闭环 (T03 守卫 d≤6 才走得完) → 强化信号断裂; ③ 城镇 C++ 白名单不填 target_list → 无引导
- 修复: obj_best 目标优先层 (矿/城恒优先, 占领后排除防粘死, 城镇贪心卡死 town_blocked 兜底) + T04 move_to_force 60 常驻 + objective_reward 30 事件奖励
- 教训: 课程换图 = 目标空间距离分布全变, 引导参数 (强制期/优先级) 必须按新图目标距离重算, 不能沿用旧图调好的值

### 118. 21×21 CNN 地形栅格 ≠ 对象视野 (语义混淆) (2026-08-29)
- 现象: 讨论"视野内看不到矿"时混淆 21×21 与 15×15
- 事实: 15×15 local_tiles (obs[480:705]) = BFS 通行性视野 (hero 恒 7,7, ±7 格寻路); 21×21 terrain_grid (CNN 分支) = 纯地形 4 通道**无对象位置**; 对象感知 = target_list (8×8) + 15×15
- 教训: obs 里三种"格子表" (local_tiles/terrain_grid/target_list) 尺寸内容用途各异, 设计引导前先核对哪张表含目标对象

### 121. economy_force 50 步空转学费过重 → 24 步定版 (2026-08-29)
- 现象: 开经济首版 economy_force=50, r 均值 -93 (深负 -134/-149), 远差于开经济前 -30
- 根因: 16-21 经济动作不移动英雄 → 强制期 50 步原地 = 位置不变 -0.5/步 × 50 = -25 步罚 + 延误奔矿 (move_to_force 60 被覆盖前 50 步) + 势函数负差分
- 修复: 改回 B2 方案定值 24 步 → r 均值 -4.5, 且自主 MOVE_TO 涌现 (24 步后模型开始自主输出 24)
- 教训: 采样强制的"体验量"与"行为扭曲代价"要平衡; 4 轮轮换 (24 步) 足够建立动作-奖励关联, 更长只烧分

### 122. [ECON] 事件不进主日志转储词表 → 观察盲区 (2026-08-29)
- 现象: 开经济后 grep 主日志 [ECON] 零命中, 误判经济动作未生效; 实际 ep log 里 RECRUIT/BUILD_2 事件正常触发
- 根因: train_wsl2_ppo_v2.py 转储词表只含 [ZOMBIE]/[ENDTURN_FUSE]/[ERROR]/[GUARD]/[MINE]/[TOWN/Assertion 等, 无 [ECON]
- 解决: 观察 grep `/tmp/hermes_ep_*.log`; 词表补 [ECON] 待下次自然重启窗口
- 教训: 新增事件打印时必须同步检查主日志转储词表, 否则 grep 主日志 = 盲区

### 123. T04 分层误读三连: 无守卫/深负来源/win_rate 失真 (2026-08-29, analyze_ab T04 口径)
- 现象①: "打了打不过的守卫" — T04 **零守卫** (gen_curriculum cfg 无 monsters), 深负真因 = vs blue NK2 英雄接战战损 (red 战斗 Router 回退 StupidAI 接战必弱)
- 现象②: analyze_ab win_rate 对 T04 全 0 — 首胜判定 (r≥80 且 <60 步) 是 T03 守卫 +100 的 proxy, T04 无守卫永远凑不到 → **T04 用 avg_r/占矿率, 不看 win_rate**
- 现象③: 晋级评估 (Phase II.1 判据) 对 T04 显示 ❌ — 同因口径失真, II.1 已完成, 该行只对 T03 有效
- 判定标志: r<-150 局从未出现 = blue 从未推平我方 (blue 胜利 -200 在 clip±300 下真实传递)
- 教训: 换课程图后所有 proxy 指标 (首胜/守卫/晋级线) 必须重审语义, 不能直接沿用旧图口径

### 124. first 奖励被强制期截胡 → 自主动作零信号 (2026-08-29, 自主 16-21 卡 90+ 局根因)
- 现象: economy_force 开启后, 模型自主 16-21 卡 0.6/局, 90+ 局不涨; 所有分析聚焦"奖励密度不够/体验不够"均未命中
- 根因: [ECON] first 奖励 (+12/档, +15) 的触发条件只是"动作被选中且档位本局未发过" — economy_force 前 24 步强制轮换**把 first 全部吃光** → 模型在 step 24 后自主输出 16-21 时**零即时奖励** → 从 PPO 视角自主经济是"无收益动作", 策略没有转向理由
- 周期提醒 (B1) 只解决体验密度, 没解决回报 — 上线后自主仍 0/局 (40 步体验全是强制)
- 修复: 每次执行小额奖励 RECRUIT +2/BUILD_2 +3 (自主与强制同享) + first 保留 + 兵力增量 0.001→0.01 (招兵结果可见)
- 效果: 20+ ep 内 avg_r 段高 +0.8, 80+ 分局 3/15 常态化, 历史新高 +105.9, 自主 16-21 0.6→2.0/局
- 教训: ① 设计"引导奖励"时必须区分"强制体验的动作"与"自主动作" — 若 first 一次性奖励会被强制期消耗, 自主通道等于零信号; ② 自主率不涨先查"自主输出有没有即时回报", 再查密度; ③ 正确结构 = 大额 first 引导 + 小额每次持续信号 (前者教学后者固化)

### 128. ep_runner_one.py 无 __main__ 保护: import 即跑主流程 (2026-08-31)
- **现象**: 冒烟脚本 `importlib` 整体 import ep_runner_one → 模块级 argparse + 主循环直接执行 → **真起了一局 VCMI episode** (引擎日志刷屏, 与在跑训练并发写 terrain_grid.bin)
- **危害**: 训练期并发 episode 可能污染共享文件 (terrain_grid.bin 每步重写自愈, 本次未实际损害); 冒烟脚本意图完全失效
- **正确姿势**: ep_runner 冒烟只用 `py_compile` + 纯逻辑复现 (不 import 主模块); 若要 import 须先给 ep_runner_one.py 加 `if __name__ == "__main__":` 保护 (待办)
- 近亲: #156 (09-10 同坑复发实锤 — import 即初始化 env 并跑游戏到 qid 470+)
- 状态: ⚠️ 未加保护, 冒烟规范先行

### 129. 日志方括号事件词前缀匹配坑: grep '\[TOWN' 把 [TOWN_BLOCKED] 一起算 (2026-08-31)
- **现象**: `grep -c '\[TOWN'` 统计 [TOWN] 触发 = 324 次, 实为 `[TOWN_BLOCKED]` (卡死标记) 的数量; 真实 [TOWN] visited = 0 — **差点把死轴当成活轴**
- **正确姿势**: 方括号事件词统计必须带右括号精确匹配 `'\[TOWN\]'` (转义链: wsl bash -c 双引号内 \[ 会被消费一层, 跨层转义需实测); 或改用无歧义子串 `'town visited'`
- 关联: 坑 #122 (转储词表盲区) 的变体 — 统计口径坑第二例
- 状态: ⚠️ 认知坑

### 132. 主日志选择性转储口径假象: [ECON]/[RECRUITED] 不在白名单 (2026-09-02)
- **现象**: 主日志 grep [ECON]/[RECRUITED] = 0 → 误判"招兵从未执行"; 实际 runner stdout 全量进 /tmp/hermes_ep_*.log, 主日志只转储部分事件词 ([MINE]/[TOWN]/[ZOMBIE] 在, [ECON]/[RECRUITED]/[BUILD_NEW] 不在)
- **正确姿势**: 经济/效果类信号一律查 hermes (`grep -h ECON /tmp/hermes_ep_*.log`); 主日志只看白名单内事件
- **关联**: 坑 #122/#129 统计口径坑第三例
- 状态: 🔴 认知坑, 已纠正

### 144. MOVE_TO 翻译层认知坑: act 无 24 ≠ 强制窗失效 (2026-09-09)
- **现象**: T06 capture 攻坚时分析 act 序列, 全历史 0 次 act=24, 误判 "move_to_force=60 强制窗外模型不采 24 → 引导驱动不了" 为双死锁之一, 白做 args 覆盖 (无害但多余)
- **真因**: MOVE_TO(24) 是**中间语义动作** — ep_runner 发 a=24 后, MOVE_TO 执行块 (L764-814) 立即把它翻译为方向动作 (C++ next_dir / 全图 BFS / 15×15 BFS / 贪心回退), traj 记录的是翻译后的 a — **act 里永远不会有 24**
- **更深一层**: 引导系统是**动作替换制** — 引导块算出 move_target (tx 非 None) 即接管, 无论模型采样什么都替换为引导方向; 与 move_to_force 强制窗无关。强制窗只影响 "a 的初值是 24 还是模型采样"
- **教训**: ①分析动作序列前先确认三层语义: 发送值 (a) / 记录值 (traj act) / 引擎执行值 (passable/visit), 三者可不同 ②判定引导是否生效看 move_target/tx 是否非 None, 不看 act 里有没有 24 ③诊断前先读执行块的翻译逻辑, 别拿记录层当发送层
- 状态: ✅ 认知修正 (args 覆盖保留无害)

### 145. T06 守卫格振荡陷阱: 站上格黑名单失效 → fail-count 贴脸计数 (2026-09-09)
- **现象**: T06 capture 攻坚, hero 在守卫格 (5,7) 与邻格 (4,6) 间回跳振荡 26/60 步 (traj_ep.json 位置序列实锤), 两局 act 逐字相同 = 确定性剧本; capture 路径被堵 (两局 200 步 truncation r=28.68/30.03)
- **根因链**: ①战斗未触发/未胜 (无 [GUARD]/守卫未消失/英雄未死 — T06 守卫对象疑与 fix_t06_maps.py aggression 补丁相关, 引擎侧待专项) ②守卫排除逻辑只在 hero 恰在格上生效, 离格后 guard_best 又选中 → 往复 ③cycle_detect=5 的八步窗抓不到 2 周期振荡 (回位 4 次<5 阈值) ④位置级罚分 (r-=3) 只扣分不强改行为
- **黑名单两版迭代**: v1 = hero 站上守卫格即黑名单 — **没接住** (hero 在邻格反复被引擎拒, 从未站上, 位置重合条件永不触发; 验证局 act 逐字复现) → v2 = **fail-count 贴脸计数**: guard_best 选中且 dist<=2 每步 +1, 3 步未胜 → 黑名单 — 不依赖站上, 邻格停滞即计数
- **联动坑**: 守卫接近梯度块 (+0.3/格) 必须同步排除黑名单守卫 — 否则梯度把 hero 拉回已放弃的守卫, 与蓝城引导对抗成新振荡源
- **验证**: r 序列 28.68 → 30.03 → 41.80 (v1) → **93.95 (v2, 46 步守卫胜快速闭环)** — 振荡解除
- **教训**: ①黑名单触发条件要选 "肯定发生" 的事件 (邻格停滞计数), 别选 "可能不发生" 的 (站上格) ②修正引导类行为时, 所有拉力源 (引导/梯度/罚分) 必须同步改, 单点改会被其他拉力对抗 ③验证脚本 = 解析 traj_ep.json 的 hero 位置序列 (obs[3203] active hero → heroes 段 [128+idx*26+2/3]), 回跳计数 + 唯一位置数两指标 10 分钟定位振荡
- 状态: ✅ v2 生效 (r=93.95 实锤), 引擎侧守卫战斗未触发待专项

### 146. BHERO_KILL 空拍误报: live_slots=0 = heroes 段整段空 (2026-09-09)
- **现象**: BHERO_KILL 埋点 (0908 上线) 捕获 9 起事件 (T05×6 + T06×3), 甄别发现全部 live_slots=0 = heroes 段整段空拍 — T06 三蓝英雄同 step 56 齐"消失"实锤非真实歼灭; 初判 "埋点工作正常, 击杀 0 = 真实观测" 被推翻
- **根因**: heroes 段 (obs [128+hi*26]) 偶发整段空 (引擎 obs 填充链偶发未填充), 空拍使全部 blue id 从集合消失 → 差集误报击杀
- **修复**: ①ep_runner 空拍防护 — `_bnow` 为空时跳过差集与 prev 更新 (防误报 + 防 prev 集合被清空) ②check_duel_watch.py 过滤 live_slots=0 行
- **教训**: ①差集检测类埋点必须防 "全空拍" (空 vs 真消失语义不同) ②事件行带 live 槽数自证真伪 ③结论下前先抽查事件明细形态 (9/9 全同一形态 = 埋点 bug 而非行为)
- 状态: ✅ 防护生效 (0 新误报), obs 填充链空拍根因待立项

### 147. 间歇性局级慢速: fuse 雷达外的 4-8s/步模式 (2026-09-09)
- **现象**: 训练 16% 局全程慢 4-8s/步 (正常 1.4s/步, 局耗时 311-398s vs 99s), 跨图均匀分布 (T05×27/T06×7), 步数与 r 正常; 0909 晨极端案例 48s/步, 后自行恢复
- **易误判**: ①初判 "单步卡 300s fuse 兜底" — 错, fuse (strategic_env.py L861 _adventure_wait timeout=300s) 只兜单步超时, 慢性 4-8s/步在雷达外 ②与 R7 battle query 卡死区分: R7 是死等冻结 (fuse 触发), 本现象是活着的慢 (hermes 日志持续写入)
- **排查锚点**: ep_runner CPU 26% (在等引擎) + 服务器侧无对应打点 → 疑宿主资源抖动/引擎偶发慢模式, 根因未定位
- **教训**: ①局耗时分析用 time 字段差分 (主日志 step 行), 超 2 倍中位数即异常局 ②"fuse 未触发" ≠ "没有慢问题" — fuse 只兜死等, 兜不了慢性慢 ③诊断先分型: 冻结型 (fuse 可兜) vs 慢性型 (需外部监控)
- 状态: 🟡 登记观察, 恶化再专项

### 153. [GUARD]/[MINE] 位置重合判据 anchor↔visitable 失真: 1442 条假糖 + 真战斗漏奖 (2026-09-10)
- **现象**: T05 高分剧本 r 130-168 / duel r=93.95 的 +100 构成可疑; ep_1386 hero 站 (10,9) 拿 +100 但全程 0 引擎战斗; ep_418 [GUARD] step32 早于 battleStarted (发奖时战斗还没发生)
- **根因**: vmap objects.json x,y = `setAnchorPos` = 引擎 **anchor** 语义; monster 本体格 (BLOCKED|VISITABLE) = anchor − visitableOffset (mask 'A' 格位置, 3×3 中心 → offset(1,1)); hero 移动到 visitable 格才 visit 触发战斗 → 旧判据查 anchor 格 = hero **路过贴脸格假发奖**, 真战胜后站 visitable 格判据不匹配**漏奖**
- **修复**: ep_runner `_anchor_to_visitable()` 解析 template.mask 复刻 C++ `calculateVisitableOffset` (找 'A'/'T'), get_guards/get_objectives mines 换算; towns 不换算 ([TOWN] dist<=1 两侧同 anchor 语义自洽); 下游黑名单/梯度/fail-count/引导目标经源头自动生效
- **教训**: ①位置重合判据必须核对引擎坐标语义 (anchor vs visitable), Python 静态表与引擎对象坐标系不是天然一致 ②事件奖励口径优先 obs 直报字段 (owner 变化/对象消失), 位置重合是最后手段 ③假糖污染所有下游统计 — 归因前先查数据采集口径
- 状态: ✅ 修复已实施 (py_compile + 单测 3 组 + 真图对照全过), 新口径首命中验证 (duel (4,6) ×2 局 / 52X52_02_mir (38,39) 均为 vis 位), 遗留 = T06 守卫战斗触发时有时无 (aggression) 专项

### 156. import ep_runner_one 有模块级副作用: 会初始化 env 并跑游戏 (2026-09-10)
- **现象**: 单测 `from ep_runner_one import _anchor_to_visitable` 直接启动 MMAI/VCMI 初始化 + query 流跑到 qid 470+, 输出 141KB
- **根因**: 模块顶层有 env 构造/初始化逻辑 (非全部包在 main guard), import 即执行
- **规避**: ①测试主模块内函数 → 把被测逻辑复制到独立脚本 (或先重构主模块把纯函数抽出) ②禁 import 主模块做单测 ③print 结果必须 flush (被杀进程时缓冲丢失, 建议脚本内加 -u 或 sys.stdout.reconfigure(line_buffering=True))
- 关联: #128 (08-31 首踩, 本条为其 09-10 复发实锤)
- 状态: ✅ 固化 (改用独立脚本内联逻辑验证)

### 157. 局耗时数据不可回溯: hermes 日志逐局覆盖 + ep 行无 time 字段 (2026-09-10)
- **现象**: 间歇性慢速 (16% 局 4-8s/步) 需要历史样本定量画像时, /tmp/hermes_ep_*.log 只剩 2-3 个最新局, 主日志 ep 行 (ep_steps/r/act/obs_nz/map) 无耗时字段
- **修复**: ep_runner 加 `_ep_t0` + 局尾 `[EP_TIME] map= steps= secs= r= err=` 打点 + 主日志白名单补 [EP_TIME] (train_wsl2_ppo_v2.py, 主进程改动需优雅重启生效); 基线首样本 52X52_02_mir 73步94s = 1.29s/步
- **教训**: ①观测埋点要前瞻性常驻, "登记观察积累样本"必须确认样本真在积累 (hermes 覆盖机制会丢) ②per-ep 临时日志只做即时诊断, 长期统计字段必须进主日志白名单
- 状态: ✅ 基建完成, 慢局复发时聚合 [EP_TIME] 定位

### 170. 多 resume 日志取"最后一次启动后窗口"的 awk 陷阱: tac|awk|tac 返回全文件 (2026-09-07)
- **现象**: 想取最后一次 `Loaded train state` 之后的日志窗口统计, 用 `tac f | awk '/Loaded train state/{f=1} f' | tac` — 结果拿到**全文件** (441 条 ZOMBIE 假计数, 实际当前窗口 0 条); `awk '/pat/,0'` 同样只从**第一个**匹配点开始, 混入历史窗口
- **真因**: 日志经多次重启含**多个** `Loaded train state` 行 — tac 后该行成为首行立即触发 f=1, 全部倒序内容都通过, 再 tac 回来 = 原文件; awk 范围式 `/pat/,0` 从首个匹配生效, 均无法定位"最后一次"
- **正确姿势**: 行号法三步 — `L=$(grep -n 'Loaded train state' f | tail -1 | cut -d: -f1)` → `tail -n +$L f > /tmp/cur_win.log` → 对窗口文件统计; (注意 $var 需在 bash 脚本文件内展开, 见 #130)
- **教训**: 统计口径先验证窗口边界 (`wc -l` + `tail -1` 应为最新进度行), 再看数字 — 窗口错则一切统计无效
- 状态: 🔴 已踩当日修复, 固化于临时脚本套路

---

### #250: P-H2 同格判据 `_d1==0` 结构性不可达 — "走上敌英雄格必触发战斗"系对 #143 事实3 的误读 (09-17, WIN-1 A2 归因定谳)

- **状态**: ✅ 已修 (`--blue_hero_contact_d` 参数化, 批次B 注入 2)
- **现象**: 批次A 窗 min_d=2 贴脸 4 局, slain/contact 恒空; P-H2 接战奖 (批次B) 若按原判据开窗必恒 0
- **根因**: ① #143 事实3 原文 = "moveHero 到**敌方英雄格**被 'destination tile is blocked' **拒绝 (英雄战不由此触发)**", P-H2 代码注释转述成"走上敌英雄格 = VCMI 机制必触发战斗" — **语义反转**; ② 蓝英雄格 passable=0 本就不入 BFS (贴脸口径), 英雄 8 方向移动贴脸停在曼哈顿 2 = 机械下限, d==0 永不可达
- **处理**: 判据阈值化 `--blue_hero_contact_d` (默认 0=旧行为, 批次B 注入 2 = 曼哈顿≤2 同格+8邻, 与 legacy scorer"贴脸 8 邻"口径一致); **度量纠偏**: 曼哈顿≤1 是 4 邻域, 8 方向移动世界真 8 邻 = ≤2, 备料文档写 `_d1<=1` 是不严谨的
- **教训**: 位置重合类奖励判据必须先核"该格在引擎里是否可达" (#145 守卫格振荡 / #153 anchor↔visitable 失真同族); 引擎机制的注释引用必须回原文核对 — 转述会把"拒绝"反转成"触发"; 贴脸奖语义 = 接战塑形近似, 真实战斗触发链 (OBS-3 aggression 遗留) 是另一个问题
- 关联: `ep_runner_one.py` P-H2 段 / `docs/已完成任务.md` 09-17 条 / 批次B 判据①接战率>0

---

### #251: act 长同向段 = MOVE_TO(24) 展开的合法直线奔袭, 据 act 序列判"卡死"会误杀 (09-17, A4 深查证伪)

- **状态**: ✅ 已定性 (guide_abort 引导熔断方案证伪归档, 不部署)
- **现象**: 09-16 判 "T05 卡死段 step 38-59 (act=2 长串同向, 94/106 局 ≥10 连同按)" → 备料零推进熔断; 09-17 逐局名义轨迹重建发现引导窗停滞 0/54 局 (T05/T06/duel), 熔断捕获面 **0%**
- **根因**: `a=24` 采样后被执行段**改写为 BFS/贪心方向动作** (ep_runner L906-957: `a = nd / bfs_dir / 贪心d`), traj 记录的是展开后方向 — 长同向段 = 引导健康直线奔目标。T05 的真病因 = **目标选错** (own_town 贴脸 89.5 恒定霸屏, 38-59 段 pick 100% own_town 176/176 次), 英雄被高效引导反复回城空转, 不是走不动
- **实证**: T06 对照组自由期 (60+) 0/16 停滞 (同动段仍 20-28 继续奔袭, r +18~+105) vs T05 15/16 停滞 (r -117~-337) — 唯一差异变量 = own_town 霸屏与否 → 根治 = A3 own_town 衰减 (目标选择层), 不在运动层加熔断
- **教训**: 分析 act 序列前先确认动作是否会被 runner 改写 (24 / visit 窗 / econ_force 都覆盖采样值); "卡死"判定必须有位置轨迹佐证, 单看动作重复会把高效奔袭误判为卡死; 奖励/引导问题的治理优先查"目标选对了没", 再查"走得动不动"
- 关联: `py/a4_stall_analyze.py` (名义轨迹工具, _DIRS 编码) / `docs/备料_T05引导期卡死熔断_20260917.md` (证伪归档) / A3 部署

---

### #252: 开窗重启只验主进程 banner 不验子进程输出 → 22 局激励空转污染段 (09-16 批次A 踩, 09-17 复盘)

- **状态**: ✅ 已固化 (批次B 部署即验子进程命令行+首局特征输出)
- **现象**: 批次A L101674 开窗段 22 局零 BHERO_GRAD 输出 — ep_runner 仍是旧代码, P-H1 根本没生效, 判据窗白跑一半; 而主日志 [WIN1_BATCH] banner 明明显示注入成功
- **根因**: banner 只证明主进程 env 有值并拼进 cmd args; ep_runner 是**独立 Python 子进程**, systemd restart 前若代码文件未及时落盘/加载时序错位, 子进程仍跑旧代码 — 中间层信号无法暴露
- **处理**: 开窗后首个 ep 周期内必须 ① `ps aux | grep ep_runner` 确认命令行含新参数 ② grep 子进程特征输出 (BHERO_GRAD/新日志行) 确认新代码生效; 聚合口径区分"开窗行"与"代码生效行" (本例生效窗 = L102375 resume 起, 污染段 22 局不计)
- **教训**: 多进程链路的生效验证必须落到**最末端进程的输出**; 中间层信号 (banner/Environment/unit 文件) 都是必要非充分; 类似先例: #143 事实5 (vmap 加载失败静默 fallback 旧图, "map=" 标签与实际加载图脱钩)
- 关联: `py/win1_batchA_agg.py` (窗口定位已修) / `docs/已完成任务.md` 09-17 两条

---

### #253: 跨帧效果复核的挂起帧选错 — A3 空撞复核在窗开启帧跑, RECRUIT 未发出必零增量 → 25/25 局开局取兵窗误拉黑 (09-17, 批次B+A3 窗首日踩)

- **状态**: ✅ 已修 (pending 移到窗结束帧, 重启验证 TOWN_EMPTY=0 / RECRUITED 恢复)
- **现象**: 批次B+A3 部署首窗 25/25 局 `[TOWN_EMPTY] town=… at step 1/2` — 开局 START_HOME 取兵窗全被拉黑, "开局先回城招兵带兵"设计被废; TOWN_VISIT 与 TOWN_EMPTY 同步打印暴露时序
- **根因**: `visit_check_pending = True` 设在**窗开启帧**, 而复核在同大循环后部 army power 段立刻消费 (该帧 nobs 的兵力 = 招兵前快照) — 窗内 4 步 RECRUIT 还没发出, 零增量是必然不是空撞; "延迟一帧"实际延迟错了帧
- **处理**: pending 改在**窗结束帧**设 (visit_econ_steps 归零分支, 与 visits+1 同处) — 复核帧的 nobs 已含窗内招兵增量; 修复后首局 TOWN_EMPTY=0 / TOWN_VISIT 3 次正常 / RECRUITED 24 次恢复
- **教训**: 跨帧效果复核的挂起时机必须挂在**效果动作已发生的帧**之后, 与"触发检测"帧严格区分; 同帧触发+同帧复核 = 复核的是前状态 (必假阴性); 上线前用"事件对是否同帧出现"做时序自检 (TOWN_VISIT 与 TOWN_EMPTY 同 step 即可疑)
- 关联: `ep_runner_one.py` visit 窗状态机 / `py/win_bB_watch.py` (窗内信号监视)
