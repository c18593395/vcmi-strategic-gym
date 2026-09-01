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
