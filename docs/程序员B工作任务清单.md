# 程序员B 工作任务清单（后端/地图层）

> 更新时间：2026-08-28 06:00（本轮任务 **已全部交付完毕**）
> 岗位：后端 / VMAP 地图 / 训练 MAPS 列表维护
> 总状态：BND-20260828-01 ✔ DONE / BND-20260828-02 ✔ DONE

---

### ✅ DONE 🔴 P0 — BND-20260828-01 T03 守卫移近 / MAPS 池精简（快路径）

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 2026-08-28 05:55 交付 |
| **执行路径** | **快速路径**（推荐的 10 分钟）：train_wsl2_ppo_v2.py MAPS 列表 6→2，仅保留 T03 20×20 最近两张 |
| **代码位置** | [train_wsl2_ppo_v2.py L20-27](file:///d:/Bigdata/hero3_fresh/train_wsl2_ppo_v2.py#L20-L27) |
| **变更摘要** | 从 `T03×6 (20×20×2 + 30×30×2 + 36×36×2)` → `仅 T03_20×20_01.vmap + T03_20×20_02.vmap`；30/36 四张 (含 obs_nz=314 大负率 27% 的 T03_36×36_02) 暂时注释，注释里写清每张守卫距离 + 大负率根由，等后续守卫完整 patch 再启用 |
| **验收 A (静态)** | py_compile train_wsl2_ppo_v2.py ✅ 通过；grep T03_ 只剩 2 条未注释行 ✅ |
| **验收 B (实际训练)** | OPS 06:13 v4 重启 banner `maps=2` ✅ 命中；v4 段 ep1-3 r=(-1.20, 21.40, -23.25) obs_nz 只看到 375/363（两张 T03 20×20 对应非零维数），**原灾难局主源 obs_nz=314 / 397 / 356 等远守卫图完全不出现在日志** ✔ 过滤有效；**首 3 局 r 均值 -1.02 远高于 Run9 近 50ep 基线 -58.3**（+57 分改善，晋级判据 r mean≥10 的剩余缺口靠更多局数积累验证） |
| **后续 TODO (非本轮)** | 完整守卫坐标 patch (6 张 vmap monster 移近到 hero d≤6) 可在 08-28 下午安排，届时把 MAPS 列表重新解注释 30/36 四张即可 |

---

### ✅ DONE 🟡 P1 — BND-20260828-02 endturn_streak≥30 独立兜底

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 2026-08-28 05:52 交付 |
| **代码位置** | [ep_runner_one.py L480-486](file:///d:/Bigdata/hero3_fresh/ep_runner_one.py#L480-L486)（紧接 zombie_streak 块之后 / max_turns 之前） |
| **新增代码块** | `if endturn_streak >= 30: traj["done"][-1] = True; print(f"[ENDTURN_FUSE] act10 x{endturn_streak} fuse-break, end ep at step {traj['steps']}"); break` |
| **作用** | 独立于 zombie 标记的第三层 END_TURN 防线：即使未来新旁路赋值 a=10 又忘了写 `zombie=True`，任何路径的 act10 连续 30 次都会强制终局 + done=True（阻断 GAE 扩散），和 zombie_streak≥2 形成「快速 + 兜底」双保险 |
| **验收** | py_compile ✅ 通过；grep `endturn_streak >= 30` / `ENDTURN_FUSE` 精确命中 L483/L485 ✅ |

---

### 📂 本轮后端变更索引（按路径）

| 变更 | 文件 | 行号 |
|------|------|------|
| MAPS 6→2 (BND-01 快路径) | train_wsl2_ppo_v2.py | L20-27 |
| 旁路②补 zombie=True (2a 遗漏补丁) | ep_runner_one.py | L368-370 |
| endturn≥30 兜底 (BND-02) | ep_runner_one.py | L480-486 |
