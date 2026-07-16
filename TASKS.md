# VCMI — 总任务清单

> 最后更新: 2026-07-16 15:30 | GPU: RTX3060

---

## Phase A — 冒险 API 开发

```
目标: VCMI adventure_wait/act 联通 → StrategicEnv → 红蓝自博弈
```

| 模块 | 状态 | 说明 |
|------|------|------|
| A6.1 回调迁移 | ✅ 完成 | `g_adventure_cb` 注册从 connector 移到 `init_vcmi()` |
| A6.2 ctypes验证 | ✅ 完成 | `strategic_state.h` 四结构体 53 字段与 Python 一致 |
| A7 ServerPlugin修复 | ✅ 完成 | tempOwner / pool匹配 / randomHeroes / 空池检查 4处 |
| A7 libvcmi保护 | ✅ 完成 | CProxyIOApi/ROIOApi 空指针检查（级联崩溃仍需根因修复）|
| A7 数据目录 | ✅ 完成 | data-combined 合并 VCMI 源+游戏数据 |
| A7 端到端测试 | 🔴 阻塞 | VCMI runNetwork segfault (0x628) — 报告已输出到 PHASE_A_SEGFAULT_REPORT.md |
| **Phase A 代码已提交** | ✅ | main: 460b467 / vcmi: 86b8c2c7a |

---

## Phase B — 战斗训练 (v13 PPO)

```
架构: train_anchor.py → train_v13_ppo.py → eval_orch.py
地图: A1-A7 (2×2 战斗 vmap)  动作: MaskablePPO 2312维
```

| 项目 | 状态 | 说明 |
|------|------|------|
| 32轮训练 | ✅ 完成 | 215万步，A1-A7全覆盖 |
| 评估脚本 | ✅ 完成 | eval_orch.py 7图×100ep |
| eval 反馈 schedule | ✅ 完成 | 弱图加重、强图减半 |
| 新 schedule (32轮) | ⏳ 待执行 | R1-R32 日程已规划 |
| **战斗环境运行** | 🔴 阻塞 | Phase A 改动后 ABI 不兼容，connector 缺 `ML::init_vcmi` 符号 |

### 阻塞原因
```
重构 connector_v13.so 时增加了 adventure API 符号，旧 connector 不兼容
需全部组件从同一源树同时编译
```

### 恢复命令
```bash
wsl -d Ubuntu -- bash -c 'pkill -9 -f train; cd ~/vcmi-workspace && \
source venv/bin/activate && \
export LD_LIBRARY_PATH=$PWD/vcmi/rel/bin:$PWD/vcmi_gym/connectors/rel && \
exec python -u /mnt/d/Bigdata/hero3_fresh/train_anchor.py 2>&1'
```

---

## Phase A/B 待完成

| 优先级 | 任务 | 依赖 |
|--------|------|------|
| P0 | 🔴 修 VCMI segfault (runNetwork 0x628) | 需要专人（报告已输出） |
| P0 | 🔴 全量同源编译 (libmlclient+libvcmi+connector) | segfault 修复后 |
| P1 | Phase A 恢复后 → 验证 adventure_wait 回调 | segfault 修复 |
| P1 | 战斗训练管线恢复 (train_anchor 跑新 schedule) | ABI 一致 |
| P2 | 模型导出 TorchScript/ONNX | 训练完成后 |
| P2 | GNN v15 迁移 | connector 重编译后 |
| P3 | 超参搜索 Optuna | 训练管线稳定后 |

---

## 代码提交

| 仓库 | 最新 commit | 备注 |
|------|------------|------|
| hero3_fresh (main) | `460b467` | Phase A 测试脚本+工具 |
| vcmi 子模块 | `86b8c2c7a` | Phase A 核心代码 (12文件) |

---

## 环境

| 项目 | 值 |
|------|-----|
| 编译 | WSL2 Ubuntu, ext4 `/home/administrator/vcmi-native/` |
| 运行 | `/home/administrator/vcmi-workspace/` |
| 源文件 | `D:\Bigdata\hero3_fresh\vcmi\` (NTFS → ext4 同步) |
| 游戏数据 | `/mnt/d/GAMES/Heroes3/` |
| Python | venv at `/home/administrator/vcmi-workspace/venv/` |
| GPU | RTX 3060 6GB (CUDA 13.1) |
