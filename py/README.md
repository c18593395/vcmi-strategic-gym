# py/ — 程序文档（脚本总索引）

> **用途**: 每个 .py 是干什么的、谁调用它、还能不能删。避免重复造轮子。
> **维护约定**: ① 新脚本必须带头部注释（第一行 docstring 或 `#` 说明块，说明"做什么+谁调用"）② 新脚本入库时在本文件对应分类登记一行 ③ 一次性探针用完不删也行，但要在描述里标 `[一次性]`。
> **最近整理**: 2026-09-23（**一次性产物归档 259 项 → `py/_archive_0923/`**，不删仅移出 git 视野；在用工具 34 项入库；根目录 31 个 .py 于 09-19 迁入 py/，引用已全量更新；生成器 `_gen_pydoc.py` 已随归档移入 `_archive_0923/`）

---

## 〇、核心链路图（谁调用谁）

```
systemd unit homm3-train-v5 (py/homm3-train-v5.service, 由 py/restart_train_v5_sys.sh 重建)
  └─ train_wsl2_ppo_v2.py          ← PPO 主循环 (GPU, cuda)
       └─ 每局 spawn: ep_runner_one.py        ← 单局执行器 (CPU 推理, --model 加载 ckpt)
            ├─ import vcmi_gym.envs.v13.strategic_env.StrategicEnv   (repo 根 sys.path 硬编码)
            ├─ lazy import py/target_scorer.py (--target_chain scorer 时)
            └─ ctypes → /home/.../vcmi-native/rel/bin/libmlclient.so → VCMI 引擎 (进程内 server)
  旁路评估: eval_promo.py / eval_elo.py / h3m_batch_pipeline.py (批转管线) 同样 spawn ep_runner_one.py
```

## 一、核心文件精述（动训练/管线前必读）

| 文件 | 作用 | 备注 |
|------|------|------|
| **ep_runner_one.py** (1684行) | 单局执行器：起 StrategicEnv、加载模型推理、奖励塑形全套参数 (WIN1/.move_to/economy/guard/attack_bypass/traj 落盘)。**训练与所有验证的总入口** | L4 sys.path 插 repo 根 (vcmi_gym)；L751 插 py/ (target_scorer)。改后须清 `__pycache__`；⚠ #266 存量: L1614 `traj["rewards"]` 应为 `traj["rew"]`（待修） |
| **train_wsl2_ppo_v2.py** (608行) | PPO 训练主循环 v5（GAE 0.9/BATCH 2048/3464 obs/25 动作/MAPS 10 图/checkpoint 每 50 步）。L106 RUNNER 指向 py/ep_runner_one.py；WIN1 参数经环境变量注入 (WIN1_ENV_ARGS) | systemd 托管；改码等自然重启窗，勿杀进程 |
| **train_wsl2_ppo.py** (300行) | V1 稳定回退版（.use_v2 flag 切换约定）。日常不用 | |
| **target_scorer.py** (340行) | P10 动作 24 目标加权排序旁路打分器（纯 Python，OBS/动作冻结不破） | 测试: test_target_scorer.py |
| **h3m_batch_pipeline.py** (252行) | 官方 H3M 全量批转管线: 断点续跑 → h3m2vmap 转换 → strip 去地下 → 部署 → 250 步训练同款验证 → PASS 入 maps/training/h3m_pool。报告 `maps/h3m_to_vmap/_pipeline_report.json` | 日志 `tmp/h3m_pipeline/run_all.log`（D 盘，PowerShell Get-Content -Wait 可看） |
| **h3m2vmap.py** (492行) | H3M→VMAP 转换统一入口（封装 tools/h3m2vmap C++ 二进制 + 逆向参考 h3m_tool）。二进制重建: `bash py/run_b4_build.sh` | C++ 源在 tools/h3m2vmap/（Windows 树为权威，同步 WSL 编译） |
| **strip_underground_vmap.py** (252行) | vmap 去地下层后处理（JSON 层删对象/修 header/自检），含 load_json 剥注释公共函数——**解析 vmap JSON 一律走它** | |
| **sync_maps_to_runtime.py** (333行) | maps/training → 运行时 data/Maps 权威同步（--strict 带预检+原子写+校验; --check 只查）。**改图后必跑** | 踩坑 #224 |
| **eval_promo.py** (425行) | 晋级全 profile 评估（地图池 profile 化、奖励参数对齐生产、spawn ep_runner） | 训练窗内勿跑（CPU/GPU 竞争） |
| **eval_elo.py** (266行) | ELO 评估: 当前模型 vs stupidai/旧 checkpoint，红蓝轮换 10 局 | |
| **curriculum_manager.py** (281行) / **train_curriculum.py** (297行) | 课程学习管理器（Level 0-5 地图池/晋级条件/状态存取）+ 课程训练驱动脚本（T01-T06 课程时代，现 v5 直选 MAPS） | 历史主线，保留 |
| **passable_gate_watch.py** (68行) | WIN-1 passable 闸门 4 判据看板（按最后 WIN1_BATCH 行切窗，只读） | |
| **contact_log_snapshot.py** (42行) | 贴脸局日志快照器（环形 5 槽×240s + BHERO_CONTACT 触发），重启入口 py/restart_snapshotter.sh | |
| **homm3-train-v5.service** + **restart_train_v5_sys.sh** | systemd system 级 unit 定义 + 重建/启停脚本（ExecStart 已指 py/train_wsl2_ppo_v2.py；09-19 同步更新 WSL 侧 /etc/systemd/system 并 daemon-reload） | 禁用 systemctl --user（踩坑 #229） |

**0919 WSL 重建补丁系列（用户会话，5 件套，配 04:46-05:03 全量重编）**: patch_vcmidirs_0919（VCMIDirsXDG 补 libraryName/libraryPath=ML 便携模式）/ patch_gameengine_0919（LoggingMutex 打点跨平台 gettid）/ patch_static_ai_0919（CDynLibHandler STATIC_AI 静态分支——解决 ENABLE_ML 强制 MMAI OFF 的 libMMAI.so dlopen 死锁）/ patch_schema13_battleround_0919（v13 GLOBAL_ENCODING 补 BATTLE_ROUND）/（另有一件）。与"重编 libMMAI.so"是两条互斥路线，**已采用 STATIC_AI 路线**。

## 二、分类索引

### A. 训练配套（常用）

| 文件 | 说明 |
|------|------|
| win1_batchA_agg.py / win1_window_aggregate.py / win1_guardrail_probe.py | WIN-1 激励窗聚合: 生效窗定位（最后 WIN1_BATCH 行）/ 五判据聚合 / TOWN_VISIT 取兵有效率 |
| win_bB_watch.py | 批次B+A3 首窗双轨信号验证（只读） |
| check_win1_watch.py | duel/1v3 观察窗统计（自发经济/200步局/战斗质量三指标） |
| analyze_train_log.py / analyze_train.py / analyze_detail.py / analyze_latest.py | train_loop.log 指标提取与分段分析（ent/avg_r/地图表现/ZOMBIE）四代变体，日常用 analyze_train_log |
| analyze_ab.py / analyze_guard.py / analyze_zombie.py / analyze_deadlock.py / analyze_acts.py / analyze_trunc200.py / analyze_traj.py / analyze_trainlog.py / analyze_session_log.py | 专题分析: A/B 分层晋级 / act10 连喷 / 僵尸段溯源 / 段统计 / 动作语义表 / 200 步截断 / 轨迹动作 / 1 步局分布 / 会话窗口报告 |
| s2_gate_check.py / s2_auto_review.py | S2 撤梯子判据复查 / 自动收口监控（Windows 后台每 5 分钟） |
| build2_probe.py | A6 定谳工具: act20 触发统计（证明 BUILD_2 一直在发，零触发是白名单假象） |
| a2_contact_probe.py / a3_selftest.py / a4_stall_analyze.py | A2 接战探针 / A3 衰减数学自测 / A4 引导期切局分析 |
| check_training_wrapper.py | Windows 侧包装: subprocess 调 wsl bash check_training.sh |
| poll_traj.py | 轮询 /tmp/traj_ep.json 到可解析，输出每步奖励与英雄位置 |
| dump_traj_act.py | traj 动作序列分段摘要（econ_force 生效验证） |
| eval_on_round3_done.py | 旧版: Round3 完成检测→基线评估→重启（历史） |

### B. H3M→VMAP 转换与地图工具

| 文件 | 说明 |
|------|------|
| pick_flat_h3m.py | 官方图筛选: 单层/无地下/不过河（硬条件 H1/H2 形式化）→ h3m_flat_pool.json/csv |
| check_map_players.py | 快速扫 H3M 玩家数（gzip 头解析，P8 选图用） |
| fix_kop_town_subtype.py / patch_king_players.py / patch_king_dragon_0914.py / patch_king_rebuild_0914.py / vcmi_full_to_slim.py / verify_kop_slim.py / deploy_vmap.py | King of Pain 入池七件套: town subtype 修补 / players dict 化+owner 重分配 / core:dragon 替换 / 阵营重建(1v3+中立城) / 完整格式→精简训练格式 / 精简版可读性验证 / 部署 |
| patch_t06_02_header_0914.py / patch_t06_02_players.py / gen_redloss_probe_0914.py | T06 _02 系 header 补字段 / players 批量修补 / 完整 header 模板生成（#225） |
| patch_h3_server_0914.py / patch_h3_souser_0914.py / patch_h3_wire_0914.py | H3 引擎补丁①②③: removeQuery PvP 计数欠减(#228) / 持久化 g_ml_player_cb / 通信线修复（改 WSL 引擎源码的补丁脚本，带备份） |
| clean_vmap_json.py | vmap JSON 剥 `//` 注释转严格 JSON（#220） |
| fix_t05_maps.py / _v2 / _v3, fix_t06_maps.py / fix_t06_hero3.py | T05/T06 图 identifier 修复四代（footman→swordsman / resource 映射 / inham→iona / alchemist 职业≠英雄名） |
| gen_t03_smoke.py / gen_t04_smoke.py / _v6 / gen_t04_mirror.py / gen_t05_expand.py / gen_t06_duel.py | 课程图生成史: 守卫加强冒烟 / BAI 决策冒烟 / 镜像变体 / T05 扩图 / T06 duel 矩阵 |
| check_t06_maps.py / check_guard_dist.py / check_map_towns.py / check_town_template.py / check_t04_deploy.py / check_t04_*.py / check_t06_objs（peek_t06_objs.py） | 图检查器: duel 可用性 / 守卫距离 / 城镇 owner / 城模板 visitableOffset / 部署副本对比 / hero-mine-town 坐标 |
| inspect_*.py（inspect_vmap/inspect_t03~t06/inspect_monster/inspect_terrain_codes/inspect_b2_types/inspect_knee_objects） | vmap 结构侦察族（zip 条目/对象谱系/identifier 合法性），patch 前置侦察 |
| probe_engine_config.py / probe_vmap_details.py / vmap_obj_survey.py / diag_v2h_strict.py / diag_v2h_trace.py | vmap2h3m 反向转换器调研族 |
| analyze_36X36_02.py / _map.py / check_terrain_2001.py / check_traj_2001.py / check_map_2001.py / _b.py / sim_traj_2001.py | 2001/36X36 专题诊断（地形障碍/守卫踏格/方向向量仿真） |
| scan_starting_passability.py / scan_maps.py | 110 张 H3M 起始 passability 扫描 / 全图 3 步可进性扫描（出 available_maps.json） |
| validate_maps.py | 生成→BFS 校验→实跑→不过丢弃重生成 的地图验证管道 |
| check_nounder_traj.py / diag_faeries.py / check_b2_knedeep.py / rename_b2_knee.py | 无地下验证 traj 检查 / Faeries header 诊断 / B2 直通产物检查 / B2 冒烟重命名 |

### C. T13 外挂协议（P8 系列，已完成闭环）

| 文件 | 说明 |
|------|------|
| test_serialization_protocol.py (924行) | T13.2 二进制序列化核心验证（LVarInt/BinarySerializer/CPack 子类） |
| p8c_movehero_probe_real.py | P8-C MoveHero 实机探针（Query 协议栈验证） |
| p8d_deploy_probe.py / p8d_dual_node_sim.py / p8d_two_instance.py | P8-D 跨机部署三步验证（本机 13/13 → WSL 双节点 → 同机 2 实例） |
| p8e_human_mix_probe.py | P8-E 人机混局探针（2 客户端拓扑） |

### D. VCMI 上游同步（C4 系列，历史会话）

c4b_step2_patch / c4b_step2d_cmake / c4b_step4_nk2_fix / c4b_step6_armymgr_fix / c4b_step7_buildanalyzer_fix / fix_7632_conflict — #7632 摘取的冲突解决/NK2 注册/Calendar 断层适配/`<ranges>` 补 include 等精确 patch 脚本（幂等，改 WSL 引擎源码用）。

### E. GUI/崩溃/反汇编取证（Windows 侧，工具链五件套+会话产物）

| 文件 | 说明 |
|------|------|
| take_dump.py / minidump_capture.py | ctypes MiniDumpWriteDump 抓 full/带栈 dump |
| walk_stuck_dump.py / analyze_deadlock_dump.py / analyze_vcmi_dump.py / parse_crash_dmp.py / parse_crash_dump.py / parse_crash_dump2.py / parse_crashinfo_mini.py / dump_streams.py | minidump 解析族（流枚举/CONTEXT/模块归属/线程栈） |
| stuck4_cfbb.py / stuck4_heap.py / stuck4_mutex.py / stuck4_owner.py / stuck4_reentry.py | gui_stuck4 死锁五连：符号化/堆检查/锁反汇编/找持锁者/重入验证（定谳 #158 interfaceMutex 泄漏） |
| gui5_mutex_owner*.py / gui8_mutex_owner*.py / gui5_engine_obj.py / gui12_stats.py / read_mutex_owner.py / read_crash_dialog.py / scan_stack_objects.py / resolve_vfunc.py | 各 gui 会话的锁持有者/堆对象取证 |
| iat_disasm.py / pe_export.py / pdata_funcs.py / resolve_frames*.py / resolve_iat.py / resolve_ra.py / disasm_stuck4.py / disasm_gui*_*.py / find_callers.py / lib_exports.py / list_imports.py | MinGW PE 反汇编/IAT 符号化/.pdata 函数边界 工具链（反复迭代的会话版本） |
| verify_v13_inference.py | v13 战斗 onnx 推理验证 |
| patch_diag_0829.py / smoke_diag_0829.py / smoke_pair_0829.py / smoke_t01_0829.py / gen_smoke_runner_0829.py / gen_smoke_ctrl_0829.py / fix_diag_0829.py / check_traj_0829.py | 08-29 P1 重编崩溃诊断会话全套（插桩 patch/对照冒烟/标记修复） |

### F. 历史/遗留（原理样参考，日常不用）

| 文件 | 说明 |
|------|------|
| collect_bc.py / bc_train.py / export_bc_onnx.py | BC 三件套: 专家轨迹采集 / BC 训练（Net 与 v2 对齐）/ BC→onnx 导出 |
| train_level0.py / train_level0_simple.py | Level 0 (T01) 早期专用训练脚本（课程时代） |
| scan_starting_passability.py（见 B） / strategic_reader.py | ctypes 直读 libmlclient StrategicState（Phase I 调试遗产，仍可用） |
| test_model_game.py | 最早"模型控真实游戏"试验（07-22） |
| test_t01_map*.py / test_terrain_*.py | T01 加载与地形栅格冒烟测试族（08-23 地形栅格开发期） |
| optimize_memory.py / optimize_memory_docs.py / update_docs_0911.py / update_docs_0911_t13.py | 文档批量搬运/更新工具（历史会话产物，勿对当前 docs 重跑） |
| eval_on_round3_done.py | 见 A |
| win3_eval_difficulty_axis.py / win3_move_town_108_02_duel.py | WIN-3 难度轴评估 / 挪城脚本（备而不用） |
| probe_victory.py / probe_town_structure.py / probe_gate_path.py / probe_onnx_action5.py / probe_t06_gameover.py / probe_redloss 系(gen_redloss_probe_0914) | 专题探针: 胜利条件字段 / 城结构 BUILD 备料 / approach2 门格 BFS / onnx argmax 恒 5 诊断 / game_over 判别器（#186/#188） |
| patch_aai_p1e.py / _diag / _r2 / _r3 | P1e 取兵链 moveHero 双病灶修复四连（改 AAI.cpp 的补丁脚本） |
| rename_b2_knee.py | 见 B |

### G. 本目录工具（`_` 前缀 = 一次性/再生器）

| 文件 | 说明 |
|------|------|
| _gen_pydoc.py | 头部说明提取器（本文档再生成用; 输出 _pydoc_draft.json） |
| _migrate_root_py_0919.sh | 0919 迁移脚本（已执行完毕，留档；可删） |
| _schema_check.py | C 头 ↔ Python ctypes 结构解析对账（strategic_state ABI 时代工具） |
| _verify.py | 最小 env 冒烟（07-29 联调遗产） |
| check_import_chain_0919.py / check_torch_cuda_0919.py | 0919 重建后的 import 链 / cuda 自检 |

## 三、0919 迁移记录（根目录 → py/）

- **迁入 31 个**: ep_runner_one / train_wsl2_ppo_v2 / train_wsl2_ppo / target_scorer 已在 py（其余 27 个历史脚本：bc_train, collect_bc, curriculum_manager, eval_elo, eval_on_round3_done, export_bc_onnx, scan_maps, scan_starting_passability, strategic_reader, test_*, train_curriculum, train_level0*, validate_maps, _schema_check, _verify, analyze_train, analyze_traj, check_training_wrapper 等）
- **引用同步更新**: train_wsl2_ppo_v2.py L106 RUNNER / h3m_batch_pipeline.py / eval_promo.py / 13 个历史脚本的 RUNNER 常量 / train_loop.sh TRAINER_V1/V2 / py/homm3-train-v5.service + py/restart_train_v5_sys.sh ExecStart / **WSL 侧 /etc/systemd/system/homm3-train-v5.service（已 daemon-reload）** / 3 个诊断 sh
- **验证**: py_compile 全过；docs 里的历史路径引用不回改（历史记录保持原貌）
- 安全性: ep_runner 的 vcmi_gym 导入走硬编码 repo 根 (L4)、target_scorer 走硬编码 py/ (L751)，迁移不破坏
