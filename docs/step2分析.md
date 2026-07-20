# WSL2 战略层训练 — 问题与方案全记录

> 2026-07-19 | 项目：HoMM3 VCMI 战略层 PPO 训练

---

## 一、已解决的问题

### 1. VCMI 编译：ABI 不兼容导致 import 失败

**现象：** `ImportError: undefined symbol: _ZTV15LobbyQueryState`

**根因：** 项目中存在两套源码（vcmi-native 和 workspace vcmi），各有独立编译产物。
vcmi-native 的 libmlclient.so (16M) 引用了较新版本才有的 `LobbyQueryState` vtable，
但 phase-a-backup 的 libvcmi.so (14M) 是老版本编译的，不导出这个符号。
两个 .so 混搭导致动态链接失败。

**解决：** 从 vcmi-native 源码全量重编 libvcmi.so + libmlclient.so + libmlserverplugin.so，
确保三件套同源、ABI 一致。最终 libvcmi 20M（含 LobbyQueryState vtable）。

### 2. MMAI 初始化崩溃（core dump）

**现象：** VCMI 启动后 MMAI 模块初始化阶段 core dump，step1 直接挂。

**根因：** 7/19 的 vcmi-native 编译引入 `ENGINE->mainLoop()` 注入（为 ARM64 headless 模式加的），
影响 WSL2 的启动流程。同时某些 MMAI 相关代码变更导致初始化异常。

**解决：** 回退到稳定的 vcmi-native 源码 + 清理重编。最终 VCMI 正常启动，`debugStartTest` 返回正常，
AI 构造函数完成，英雄池分配成功。

### 3. 观测全为零（DummyVecEnv 短路）

**现象：** reset() 返回的 obs 256 维全是 0.0，nonzero=0。

**根因：** `strategic_env.py` 的 `reset()` 有 DummyVecEnv 短路逻辑：
VCMI 启动后立即返回 dummy obs（`_vcmi_just_started=True`），不等待第一个 yourTurn 回调。
这段代码是为 PPO 初始化时避免 30-60s 阻塞设计的，但在 subprocess 模式下每次都触发。

**解决：** 删除短路代码（13 行），让 reset() 始终等待 `_adventure_wait()`，
读到真实状态再返回。修复后 nonzero=24~59（随地图变化）。

### 4. subprocess 僵尸进程（训练卡死）

**现象：** ep_runner 进程不退出，130% CPU 自旋，训练循环阻塞。

**根因：** VCMI 启动后会创建多个后台线程（server、AI、渲染），
Python 脚本的 `sys.exit()` 不会杀死这些 C++ 线程，导致进程常驻。
旧方案用 `subprocess.wait(timeout=30)` + `proc.kill()` 野蛮杀进程，
每次 episode 耗时 30s。

**解决：** ep_runner 末尾加 `os._exit(0)`（硬退出，跳过所有 atexit/线程清理），
JSON 写入后立即终止进程。episode 耗时从 30s 降到 ~8s。

### 5. .pyc 缓存导致代码修改不生效

**现象：** 修改 Python 源码后行为不变。

**根因：** Python 的 `__pycache__/*.pyc` 缓存了旧版本的字节码，
NTFS 文件系统上 pyc 过期检测不可靠。

**解决：** 每次部署后 `find ... -name __pycache__ -exec rm -rf {} +`。

---

## 二、待解决的问题：step2 挂死

### 为什么要解决

当前只能跑 **单步 reset**（读初始状态），无法走多回合。
没有多回合就没有状态变化，没有时序 reward，
模型只能学"评估初始局面"，不能学"玩一局游戏"。

训练管道需要 `reset → step → step → ...` 循环。

### 问题本质

**第一个 yourTurn 正常触发，但 endTurn 后第二个 yourTurn 永不触发。**

调用链：
```
VCMI 启动 → red's yourTurn → g_adventure_cb → adventure_cb_trampoline
  → adventure_process_turn (设置 s_turn_player=0, 自旋等 action)
  → Python adventure_wait_for_turn() 返回 0
  → Python 发 action → adventure_send_action(0)
  → C++ 自旋退出 → cb->endTurn()
  → ??? 游戏应切换到 blue → blue's yourTurn → 回到 red → 第二个 yourTurn
  → ❌ 永远不会触发
```

已验证：
- `debugStartTest` 正常返回
- 两方 AI (MMAI) 创建成功
- 英雄分配正常
- 第一个 yourTurn 触发正常
- `cb->endTurn()` 被调用
- 之后无第二个 yourTurn

### 已尝试的方案

| # | 方案 | 改动 | 结果 |
|---|------|------|------|
| 1 | 当前代码 | endTurn→selectionMade | step1 成功，step2 挂 |
| 2 | 非 headless 模式 | threadconnector.h: headless=false | core dump（需 X display） |
| 3 | 删除手动 endTurn | 回调后 fall through 到默认代码 | segfault（无 GIL 调用 endTurn） |
| 4 | selectionMade→endTurn | 调换顺序 | 待测（已回退到原版） |

### 待尝试方案

| # | 方案 | 思路 | 难度 |
|---|------|------|------|
| 5 | 删除 `return`，不手动 endTurn | 回调只做暂停，让 VCMI 正常流程走完回合 | 低 |
| 6 | `sleep(100ms)` 后再 endTurn | 给 server 事件循环时间处理 | 低 |
| 7 | 查 CCallback::endTurn 内部 | 是否在 headless 模式下发包被丢弃 | 中 |
| 8 | 对比 MMAI 默认 yourTurn 行为 | 无 callback 时能正常循环吗？ | 中 |
| 9 | 换 AI 类型测试 | 不用 MMAI，改用 Nullkiller2/StupidAI | 中 |

### 根因假设（按可能性）

1. **headless 模式 server 事件循环不完整** — `debugStartTest` 在新线程中执行完后返回，
   线程退出，server 的事件处理可能依赖该线程。`cb->endTurn()` 发包后无人处理。
2. **GIL 时序问题** — endTurn 内部调 Python 代码需要 GIL，但 GIL 已被主线程持有时机不对。
3. **endTurn/selectionMade 协议顺序** — VCMI 要求先 answer query 再 end turn。

---

## 三、当前可用资产

| 资产 | 位置 | 状态 |
|------|------|------|
| 三件套 .so | vcmi-native/rel/bin/ | ✅ libvcmi 20M, libmlclient 16M |
| connector | vcmi_gym/connectors/rel/connector_v13.so | ✅ 7.9M |
| 备份 | route-backups/base/ | ✅ 源码+.so+cmake cache |
| H3M 地图 | 158 张 | ✅ 最多 8 玩家，2 人图 ~10 张 |
| reset 观测 | nz=24~59 | ✅ 随地图变化 |
| ep_runner | ep_runner_one.py | ✅ reset-only |
| PPO 训练 | train_wsl2_ppo.py | ✅ 单步训练跑通 |

---

## 四、恢复方法

```bash
# 恢复源码
cp /home/administrator/vcmi-workspace/route-backups/base/vcmi-native/ML/* \
   /home/administrator/vcmi-native/ML/
cp /home/administrator/vcmi-workspace/route-backups/base/vcmi-native/AI/MMAI/AAI/AAI.cpp \
   /home/administrator/vcmi-native/AI/MMAI/AAI/

# 恢复 .so
cp /home/administrator/vcmi-workspace/route-backups/base/bin/*.so \
   /home/administrator/vcmi-native/rel/bin/

# 重编
cd /home/administrator/vcmi-native/rel
cmake --build . --target vcmi -j4 && cmake --build . --target mlclient -j4
rm -f bin/data && ln -sf /home/administrator/vcmi-workspace/vcmi/data bin/data
```
