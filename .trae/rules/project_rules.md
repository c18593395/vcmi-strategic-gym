# 项目规则 — HoMM3 全盘操盘 AI

## 项目一句话
VCMI 沙盒 PPO 训练战略模型 (1v7) → 真实 HoMM3 部署对战。当前主线: Phase I.2 BFS 训练验证 (v5 systemd 托管, T03×2 Level 2), Phase II 经济前置已备。

## 文档导航 (先读再动手)
| 需求 | 查 |
|------|-----|
| 项目全景 / Phase 状态表 / 训练参数 | `docs/总任务.md` |
| 当前任务 / 下一步行动 | `docs/当前任务清单.md` |
| 历史实现细节 (08-01 起归档) | `docs/已完成任务.md` |
| 踩坑 #1-#114 | `docs/WSL踩坑点.md` |
| 技术细节 / 运维知识 | `docs/WSL知识库.md` |

## 硬约束
- **OBS(3464) / 动作空间冻结**: 禁增删维度; 扩展只走预留位或旁路 (terrain 走 terrain_grid.bin, 不占 obs)
- **训练地图 = VMAP** (T01-T06 课程体系); H3M 已停用 (h3m_tool.py 逆向参考)
- **训练进程运维**: unit = system 级 enabled `/etc/systemd/system/homm3-train-v5.service`（0911 起，旧 --user transient 已废弃，踩坑 #195/#201）。改代码 → `wsl -u root systemctl stop homm3-train-v5` 优雅停 → `wsl -u root systemctl start homm3-train-v5` (checkpoint resume; 或 `sudo bash py/restart_train_v5_sys.sh`); Windows keepalive (`wsl.exe sleep infinity`) 常驻防 idle shutdown (踩坑 #114/#201)。**禁用 `systemctl --user`**（当前无 user unit，会误报 inactive/not found）
- **VCMI 铁律**: 不重编 libvcmi.so; vcmi-native 与 vcmi-native-build 双目录 cp 同步; .so 多副本部署 (改 .so 后同步全部副本)
- **晋级纪律**: 晋级与开经济不同时做, 一次只加一个难度轴
- 改 Python 后清 `__pycache__`; 动构建树前备份 .so + 源码
- **改图后必跑同步 (09-14 踩坑×2 固化)**: 权威源 `maps/training/`，运行时真实目录 `vcmi/data/Maps`（两棵 VCMI 树的 data/Maps 都是指向它的软链）。改/生成任何 .vmap 后必须 WSL 执行 `/home/administrator/vcmi-workspace/venv/bin/python py/sync_maps_to_runtime.py --strict`（自带 header.players/owner/identifier 预检+原子写+写后校验；`--check` 只校验，rc≠0 禁训）
- 代码文件保存到 /py 目录下 (用户规则); 全程中文回复

## 事实核查原则 (防文档过时)
- "X 是否在用 / X 是否生效" 类问题: 以 **代码 + 运行日志 + 二进制产物** 为准, 文档仅作索引
  - 训练主日志: `train_loop.log` (ep_runner 明细在 `/tmp/hermes_ep_*.log`, 主日志只转储 [ZOMBIE]/[ENDTURN_FUSE])
  - 运行时 .so 检查: `wsl bash -c "strings <so路径> | grep -c <符号>"`
- **Windows vcmi/ submodule 与 WSL vcmi-native 源码可能不同步** (实例: CNN 地形栅格 C++ 侧只在 WSL); 源码级改动前先在 WSL 侧 grep 确认

## 常用命令
- 训练日志实时: `Get-Content D:\Bigdata\hero3_fresh\train_loop.log -Tail 20 -Wait`
- 训练状态: `wsl bash -c "systemctl is-active homm3-train-v5"`（system unit，无 --user；存活性以 PID etime+日志 mtime 为准，踩坑 #201）
- 停止训练: `wsl -u root systemctl stop homm3-train-v5` (优雅保存; root 免密通道; 普通用户 stop 需 sudo 密码)
- 启动训练: `wsl -u root systemctl start homm3-train-v5`
- 健康监控: `py/train_health_monitor.ps1` + `monitor_alerts.log`
