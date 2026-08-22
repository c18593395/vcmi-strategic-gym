# Phase I.2 C++ 寻路桥接方案

> 父文档: 总任务.md Phase I.2 | 状态: 方案待审, 未动手
> 日期: 2026-08-23

---

## 背景 / 根因

Phase I.1 (NK2 估值 → 奖励塑形) 调参到 ep45 撞天花板:
- klc=10.0 持续触顶, 循环 ([6,2]/[3,7]/[0,4]) 与 END_TURN(10) 穿插顽固不变
- 多次调参 (KL target/coef_min、explore、penalty、BC 重置、NK2 5x 权重) 全在同一个瓶颈打转

**根因不在奖励常数, 在 MOVE_TO 到不了矿/城**:
1. 15×15 local_tiles BFS 视野不够, 目标(矿/城)常在 15×15 之外
2. BFS 返回 None → 回退贪心方向 → 撞障碍 → 6 步 stall 放弃
3. NK2 矿/城差分信号 (占矿 +3.5~5, 占城 +10~15) 从不触发
4. 模型学不到 "占矿占城 > 循环", 收敛到局部最优循环

这正是"迷雾探测看到物质后直接过去"的未完成部分。

---

## 核心约束 (冻结铁律, 不可破)

| 约束 | 说明 |
|------|------|
| OBS_DIM=3464 不变 | 权重不废, 现有 Phase I.1 权重直接可加载评测 |
| 动作空间不变 | 0-7 方向 + 24=MOVE_TO, 不新增动作码 |
| 不重编 libvcmi.so | 只编 libmlclient.so (VCMI 铁律) |
| 不改 StrategicState 结构体布局 | 只解读 reserved 区, 不加命名字段 |

---

## 方案

### 数据流
```
C++ fill 阶段 (fill_strategic_state)
  对 target_list 8 个目标槽, 每个跑引擎 CPathfinder
  → 取路径第一个节点方向 (0-7), 写 reserved[0..7] = next_dir[8]
  (不可达/无路径 → -1)

Python MOVE_TO (a==24)
  读 obs[3330:3338] 对应 next_dir
  选 dist 最小目标 → 发射该 next_dir 方向码 (不是发 24)
  若 -1 → 回退现有贪心逻辑
```

### 关键设计决策

1. **寻路结果写 reserved 区 `[3330:3464]` 前 8 个 int32 = next_dir[8]**
   - reserved 区已在 obs 布局中映射到 `[3330:3464]`, 当前保持 0
   - 解读前 8 槽, 不加命名字段, 结构体 size 不变, ABI 不变

2. **复用引擎 CPathfinder / CPathsInfo::getPath, 不手写全图 BFS**
   - 手写全图 BFS 要处理跨层(楼梯/地下)、水域(船)、传送门, 坑多
   - 引擎 `lib/pathfinder/CPathfinder.h` 已有现成: `CPathsInfo::getPath(CGPath& out, int3 dst, ELayer)`
   - Nullkiller2 `ExecuteHeroChain::moveHeroToTile` 是同款参考

3. **不做 "C++ 收到 24 后自主走完整路径、一步 Python = 多步引擎移动"**
   - 会打乱 step 计数、每步 reward 累积、trajectory 对齐, 风险远大于收益
   - 保持逐格语义: Python 每步仍发一个方向动作 (0-7), 只是方向来自 C++ 全图寻路而非 15×15 BFS

4. **线程模型** — fill 已用 `shared_lock(CGameState::mutex)` 模式; pathfinder 调用遵守同一把锁, 防 NK2 决策损坏 / moveHero 全被拒 (踩坑 #30 同源)

---

## 关键坑: 版本漂移 (动手前必读)

两份 strategic_state.cpp 已漂移 73 行:

| 路径 | md5 | mtime | 内容 |
|------|-----|-------|------|
| `/home/administrator/vcmi-native/ML/strategic_state.cpp` | 91c0d405 | 08-19 | 新版: 有 fill_target_list + s_turn_generation |
| `/mnt/d/.../vcmi/ML/strategic_state.cpp` | 839f03c1 | 08-16 | 旧版: 缺上述 |

- `build.make` L157 铁证: cmake 编译 `/home/administrator/vcmi-native/ML/strategic_state.cpp`(根 ML 那份, 非软链接 vcmi/ML)
- `.h` 两份 md5 相同, 结构体布局一致
- **结论: Phase I.2 改 `/home/administrator/vcmi-native/ML/`(build 源), 不是 `/mnt/d/.../vcmi/ML/`(git submodule 源)**
- 遗留待办: 全面 diff 对齐 + git 同步 (总任务.md 已有此待办)

---

## 构建

- build dir: `/home/administrator/vcmi-native/rel/` (CMakeCache 在此, Unix Makefiles + gmake)
- 重编: `cd /home/administrator/vcmi-native/rel && make mlclient -j$(nproc)`
- 产物: `/home/administrator/vcmi-native/rel/bin/libmlclient.so`
- 改前备份 .so + 源 (老规矩: backups/ + *.bak)

---

## 验证步骤

1. C++ 加 next_dir 填充 + 诊断日志 (每个 target 打印 type/dist/dir)
2. 重编 libmlclient.so, 确认 .so 时间戳更新
3. Python 加 reserved 读取 + MOVE_TO 换数据源 (保留贪心回退)
4. 清两处 pycache (`/home/administrator/vcmi-workspace` + `/mnt/d/Bigdata/hero3_fresh`)
5. `--move_to_test` 单局: 确认英雄能真到达目标不再 stall
6. 用 Phase I.1 现有权重跑一小段, 对比是否出现真占矿/占城 NK2 delta

---

## 明确不做

- 不扩大 target_list (会导致 obs 偏移)
- 不手写全图 BFS (用引擎 CPathfinder)
- 不一步 Python = 多步引擎移动 (打乱 step/reward/trajectory)
- 不动动作码 0-10 (DLL 已落地)
