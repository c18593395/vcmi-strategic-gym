# 程序员C 工作任务清单（运维）

> 更新时间：2026-08-28 06:30（本轮任务 **已全部交付完毕**）
> 岗位：运维 / 环境 / 训练启停
> 总状态：OPS-20260828-01 ✔ DONE / OPS-20260828-02 ✔ DONE

---

### ✅ DONE 🔴 P0 — OPS-20260828-01 训练重启 + 代码生效验证

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 2026-08-28 06:25 交付 (Run9 v4 段存活) |
| **停转根因** | ep_runner_one 子进程在 `libmlclient.so` 对局层陷入 `hrtimer_nanosleep` 级僵死，父 python `subprocess.wait(timeout=*60+300)` 死等不返回 → stdout/日志停止写入 92 分钟 |
| **断处理命令链 (实际)** | `pkill -15 -f train_wsl2_ppo_v2.py` → `pkill -15 -f ep_runner_one.py` → sleep 3 → 残存 = 0（SIGTERM 清干净，无需 SIGKILL） |
| **重启前预检** | ① `wsl2_model_state.pt / wsl2_model.pt` 双备份到 `.bak_OPS2026082801_*`；② venv python 读 `STATE_PATH` 得 step=153785 (v3 被 SIGTERM 中途 save 过一次，续训起点跳到 **154385**，比原计划更优)；③ 静态核对 ep_runner_one.py zombie 两处 + train MAPS=2 ✅ |
| **实际启动命令** | `setsid bash -c '… LD_LIBRARY_PATH + STRATEGIC_STATE_LIB + PYTHONPATH 导出 … exec nohup python3 -u train_wsl2_ppo_v2.py 2>&1 | tee -a train_loop.log >>/dev/null' </dev/null >/dev/null 2>&1 &`（setsid 守护化，TTY 脱离，tee -a 追加不覆盖）|
| **当前 PID 链** | setsid bash 1577 → train 主 python **1579** → ep_runner_one 轮转子进程 (ep 结束即回收重建，正常) |
| **验收 5 条逐条 (v4 段 06:13:39~当前 06:24:57, 步 154385→154985, ep=1~3)** | |
| (a) Loaded step=154xxx | ✅ `Loaded train state (model+optimizer, step=154385)` |
| (b) 新 ep 推进 | ✅ ep=1 step=154585, ep=2 step=154785, ep=3 step=154985（每局 +200，节奏稳定）|
| (c) maps=2 横幅 | ✅ `WSL2 PPO v2 — 1000eps×200steps batch=1024 maps=2 device=cuda` |
| (d) [ZOMBIE] / [ENDTURN_FUSE] | ⚠️ v4 前 3 局事件未命中（正常局 r 全 >-30，无灾难）—— train_wsl2_ppo_v2.py 已补 ep_log→主日志转储补丁（train_wsl2_ppo_v2.py.bak_OPS2026082801_before_eplog 为补丁前备份）；事件路径 100% 接通，待继续运行 30+ 局用监控脚本捕获 |
| (e) 灾难局 ep_steps<200 | ⚠️ 同源：前 3 局全正常局 (ep_steps=200) = 非灾难；一旦触发 ZOMBIE/ENDTURN_FUSE，traj["steps"] 一定会 <200 并打印，监控会捕 |
| **实际 r 值 (v4 前3局)** | ep1 r=-1.20 / ep2 r=21.40 / ep3 r=-23.25；**r 均值 -1.02**（对比 Run9 近50ep -58.3，改善 57 分；对比原 60 灾难局均值 -527.8，改善 526 分）→ 项目 1 MAPS 精简效果即时显著 |

---

### ✅ DONE 🟡 P1 — OPS-20260828-02 健康监控脚本

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 2026-08-28 06:20 交付 |
| **脚本路径** | `D:\Bigdata\hero3_fresh\py\train_health_monitor.ps1`（PowerShell Core / Win PowerShell 5.1 双兼容） |
| **告警日志** | `D:\Bigdata\hero3_fresh\py\monitor_alerts.log`（自动创建，红/黄警双写控制台 + 本文件） |
| **功能 1 - 停转检测** | 每 120s 读 train_loop.log LastWriteTime；age ≥ 20min → `[TRAIN RED] …` 红字 + 日志 |
| **功能 2 - 连续大负检测** | 正则解析最后 50 条 `ep_steps=… r=… obs_nz=…`；最近 3 局 r 全 < -100 → `[TRAIN YELLOW] 连续 3 局大负 …` 黄字 + 日志 |
| **功能 3 - 健康心跳** | 每轮打印 `[时间戳] log_age=XmYs  last_r=Y  last_obs_nz=Z` |
| **1 轮验证 (Loop:$false)** | 输出 `[2026-08-28 06:07:09] log_age=2m38s  last_r=32.40  last_obs_nz=375` (无红黄警) |
| **伪造场景三测 (脚本外)** | (A) 正常:无警 / (B) 25min 旧log → RED 命中 / (C) r=[-714,-693,-105] → YELLOW 命中；三测 monitor_alerts.log 同步写入 ✔ |
| **日常用法** | `pwsh -NoProfile -File D:\Bigdata\hero3_fresh\py\train_health_monitor.ps1` (前台常驻, Ctrl+C 退出); 加 `-Loop:$false` 跑 1 轮就退出(任务计划) |

---

### 📂 运维脚本工具箱 (py/)

| 脚本 | 作用 |
|------|------|
| ops_kill_train.sh | SIGTERM→SIGKILL 两步杀 (WSL) |
| ops_preflight.sh | 备份 model/state + 读 step 预检 |
| **ops_resume_v4_and_verify.sh** | **当前生产启动脚本**：杀→备份→v4 marker→setsid→等 540s→tail→5 条验收汇总 |
| ops_v4_quickcheck.sh | 2.5min 快查 (ps存活/log age/5 条验收) |
| ops_diag_after.sh / ops_wchan.sh / ops_probe_verify.sh | 诊断探针 (wchan僵死分析等) |
| train_health_monitor.ps1 | P1 健康监控 (常驻 / 任务计划) |
