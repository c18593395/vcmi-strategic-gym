# 项目规则 — HoMM3 全盘操盘 AI

## 项目一句话
VCMI 沙盒 PPO 训练战略模型 (1v7) → 真实 HoMM3 部署对战。当前常态：训练在服务器 172.16.2.40（`homm3-train-server` N=16），WSL 为回切备胎（SOP `py/restore_train_to_wsl.sh`）。

## 文档导航 (先读再动手)
| 需求 | 查 |
|------|-----|
| **公共规范 / SOP / 编号规则（唯一权威）** | `docs/项目管理.md` |
| 项目全景 / 大项 T1-T14 状态 / 训练参数 | `docs/总任务.md` |
| 当前任务 / 下一步行动（P + T 系列） | `docs/当前任务清单.md` |
| 历史实现细节（只增不删） | `docs/已完成任务.md` |
| 踩坑 / 技术细节 | `docs/WSL踩坑点.md` / `docs/WSL知识库.md` |
| 服务器侧 | `docs/服务器知识库.md` / `docs/服务器踩坑点.md` |

> 本文件只保留**会话注入必须**的最小硬约束 + 判活命令，完整 SOP（改动流向 / git / 开关机 / 训练启停 / 多 agent 协作 / 错窗与验证纪律）一律见 `docs/项目管理.md`，勿在此复制正文（防双权威漂移）。

## 硬约束（全量见项目管理.md §三）
- OBS(3464) / 动作空间冻结：禁增删维度；扩展只走预留位或旁路
- 训练地图 = VMAP；H3M 已停用；改/生成 .vmap 后必跑 `py/sync_maps_to_runtime.py --strict`（rc≠0 禁训）
- 改动流向：本地仓 commit → 服务器；禁在服务器侧直接改源树；知识库/踩坑点文档以服务器为权威侧改完 scp 回本地
- 训练 unit 一律 system 级（WSL `homm3-train-v5` / 服务器 `homm3-train-server`），**禁用 `systemctl --user`**；unit 双副本（/etc 与 py/ 仓内）必须同步改（踩坑 #306）
- 改 Python 后清 `__pycache__`；动构建树前备份 .so + 源码；.so 多副本改后同步
- 代码文件保存到 /py 目录下（用户规则）；全程中文回复

## 事实核查原则 (防文档过时)
- "X 是否在用 / X 是否生效": 以 **代码 + 运行日志 + 二进制产物** 为准, 文档仅作索引
  - WSL 训练主日志: `train_loop.log`; 服务器: `train_full.log`; ep 明细 `/tmp/hermes_ep_*.log`
  - 运行时 .so 检查: `wsl bash -c "strings <so路径> | grep -c <符号>"`
- Windows vcmi/ submodule 与 WSL vcmi-native 源码可能不同步; 源码级改动前先在 WSL 侧 grep 确认

## 每次会话启动（先跑）
```powershell
# keepalive 判活: 计数 ≥1 即正常 (重启 WSL/Windows 后必丢失; 幂等)
(Get-CimInstance Win32_Process -Filter "Name='wsl.exe'" | Where-Object { $_.CommandLine -like '*sleep*infinity*' }).Count
# 为 0 时拉起:
Start-Process wsl.exe -ArgumentList '-d','Ubuntu','sleep','infinity' -WindowStyle Hidden
```
训练状态: 服务器 `systemctl is-active homm3-train-server`；WSL 回切态 `systemctl is-active homm3-train-v5`（存活性以 PID etime + 日志 mtime 为准，踩坑 #201）。
