# H.6 任务派单说明 — 动作 11-24 实现（reasonix CLI 执行）

> 2026-08-15 | 按 D:\Bigdata\cost\REASONIX.md §10 模板派单

## 项目背景
VCMI HoMM3 RL 训练栈（英雄无敌3 强化学习）。动作由 Python (strategic_env.py) 通过 C 原子变量写入，C++ 侧 AI/MMAI/AAI/AAI.cpp 的 yourTurn() 读取并执行。当前只有动作 0-10（0-7 移动/8 交互/9 切英雄/10 结束回合），本次实现 11-24（分兵/合兵/换兵/招兵/建造/驻守/招募英雄/高层移动）。

## 必读文件（先读再动手）
1. `docs/动作空间设计文档.md` §1.2 冻结动作码表（宪法，码位永不重排）
2. `docs/H6_reasonix_task.md` — 完整任务说明（动作码表 11-24、CCallback API 签名、NK2 参照文件、实现要点、编译/部署/回归命令）
3. `vcmi/AI/MMAI/AAI/AAI.cpp` yourTurn()（177-246 行）— 现有 0-10 处理，新分支插在 241 行 `}` 之后、243 行 `selectionMade` 之前
4. `vcmi_gym/envs/v13/strategic_env.py` 第 70 行 N_ACTIONS = 11 → 25

## 任务内容
按 docs/H6_reasonix_task.md 实现动作 11-24：
- 11/12 SPLIT_1OF3/1OF2: splitStack 分 1/3、1/2 兵力给最近友方英雄
- 13 SPLIT_ALL: bulkMoveArmy(cur->id, dst->id, srcSlot)（已核实 bulkSplitStack 不能跨英雄，用 bulkMoveArmy）
- 14 MERGE_FROM: mergeStacks 从最近友方英雄合并到当前英雄
- 15 SWAP_ARMY: bulkMoveArmy 双向交换
- 16/17/18 RECRUIT: recruitCreatures 最近己方城镇招兵（最低级/最高级/全部级各1）
- 19/20/21 BUILD: buildBuilding 最近己方城镇（大厅链/兵种链/防御链第一个未建）
- 22 GARRISON: swapGarrisonHero
- 23 RECRUIT_HERO: getAvailableHeroes[0] + recruitHero
- 24 MOVE_TO: getVisitableObjs 找最近可交互对象 → moveHero + 等 2s

硬性约束：
- 所有新动作走 `asyncTasks->run(...)`（lambda 内 `std::shared_lock gsLock(CGameState::mutex)`，参照 AAI.cpp battleEnd 131-137 行）
- try/catch(...) 静默包裹，失败不崩游戏
- v1 引擎侧"最近目标"解析（欧氏距离含 z，跳过敌方 owner != PlayerColor(0)）
- 尾部统一 selectionMade(0, queryID); cb->endTurn();
- 不改 strategic_state.h/.cpp、动作码表、action_space 类型（保持 Discrete）
- 编译只用 -j4（禁 -j$(nproc)，会崩 WSL）

## 工作流（严格按序）
1. 开工：改 AAI.cpp 动作 11-24 分支 + strategic_env.py N_ACTIONS=25 + step() 注释
2. 每改完一段立即 `reasonix review --base 自审` 再继续（铁律4）
3. 同步 + 编译 + 部署 + 回归（命令见 docs/H6_reasonix_task.md 完整版）：
   - wsl bash -c "cp /mnt/d/Bigdata/hero3_fresh/vcmi/AI/MMAI/AAI/AAI.cpp /home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
   - wsl bash -c "cd /home/administrator/vcmi-native/rel && cmake --build . --target mlclient -j4 2>&1 | tail -30"
   - 编译报错→修→重编译，直到 Built target mlclient
   - 部署 3 个 .so 到 workspace + 修复 data symlink
   - 回归: wsl bash -c "cd /mnt/d/Bigdata/hero3_fresh && timeout 280 python3 -u collect_bc.py --map 'Dungeon Keeper.h3m' --episodes 1 --max_pairs 10 --out /mnt/d/Bigdata/hero3_fresh/bc_data/h6_reg.npz --wait_timeout 60" → 必须 reset OK + SAVED 10 pairs
4. 完成：git 提交（只提交 AAI.cpp + strategic_env.py + docs/H6_reasonix_task.md，禁 -A/./提交无关文件）

## 完成标准
AAI.cpp 11-24 全实现 + N_ACTIONS=25 + 编译 Built target mlclient + collect_bc.py SAVED 10 pairs。
最终报告：每个动作实现方式 + 编译/回归实际输出 + 遗留问题。
