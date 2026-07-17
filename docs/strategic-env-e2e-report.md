# StrategicEnv 端到端验证 — 进度与阻塞报告

> 日期: 2026-07-17
> 项目: hoMM3 全盘操盘 AI (Phase B → C)
> 负责人: (your name here)

---

## 一、当前状态

```
Phase A [VCMI冒险API]         ✅ 完成 (已验证 adventure_wait/act 连通)
Phase B [战略Gym环境]         ⏳ 代码完成，cmake修复，端到端验证阻塞
Phase C [自对弈PPO训练]       ⬜ 依赖 Phase B
```

StrategicEnv（590行，`strategic_env.py`）的 `reset()` → `adventure_wait()` 在端到端测试中挂起不返回，无法完成验证。

---

## 二、环境架构

### 2.1 目录结构

```
WSL2 Ubuntu (开发/训练环境)

~/vcmi-workspace/                    ← Python 工作区
  ├── vcmi/rel/bin/                  ← VCMI 运行时库目录 (LD_LIBRARY_PATH)
  │   ├── libmlclient.so            ← ML模块 (strategic_state, init_vcmi, start_vcmi)
  │   ├── libvcmi.so                ← VCMI核心
  │   ├── connector_v13.so → .../connectors/rel/connector_v13.so
  │   ├── config/ → source config/  ← VCMI 配置 (filesystem.json 等)
  │   ├── Mods/ → source Mods/     ← VCMI 模组
  │   ├── scripts/ → source scripts/ ← Lua 战斗脚本
  │   └── data/ → data-combined/   ← 合并的游戏数据 (含 .lod 文件)
  ├── vcmi_gym/
  │   ├── envs/v13/strategic_env.py ← 战略RL环境
  │   ├── envs/v13/vcmi_env.py     ← 战斗RL环境
  │   └── connectors/rel/          ← 编译好的 .so pybind11 模块
  │       └── connector_v13.so     ← 关键: ThreadConnector (内含冒险模式)
  ├── maps/gym/                    ← 战斗地图
  └── maps/s1.vmap                 ← 冒险地图 (36×36, 红蓝各1城1英雄)

~/vcmi-native/                     ← VCMI 源码 + 编译产物 (新版)
  ├── rel/bin/                     ← 最新编译产物
  │   ├── libmlclient.so
  │   ├── libvcmi.so
  │   └── connector_v13_adventure.so
  ├── Mods/vcmi/                   ← VCMI核心mod (mod.json)
  ├── config/                      ← VCMI配置文件
  └── scripts/                     ← Lua战斗脚本
```

### 2.2 关键组件关系

```
Python (strategic_env.py)
  └─→ connector_v13.ThreadConnector (pybind11 C++ 模块)
        ├── start()               ← 后台线程
        │     ├── g_adventure_cb = adventure_yourTurn_callback
        │     ├── init_vcmi()     ← 在 libmlclient.so 中
        │     └── ML::start_vcmi() ← 游戏主循环 (永不返回)
        ├── adventure_wait()      ← Python 线程阻塞等待
        │     └── 条件变量 _adventure_cond
        └── adventureAct()        ← Python 发送动作信号

VCMI 游戏线程 (ML::start_vcmi)
  └─→ AI::yourTurn()             ← VCMI 通知AI行动
        ├── strategic_state_update() ← 填充StrategicState
        ├── g_adventure_cb(player, userData)  ← 回调通知Python
        │     └── adventure_yourTurn_callback()
        │           ├── signal _adventure_cond → Python侧的adventure_wait返回
        │           └── wait for _adventure_action_ready
        └── cb->endTurn()
```

---

## 三、已修复的问题

### 3.1 脚本层加载失败 (13/15 修复)

**现象**: `[mod] ERROR Script layer not found: core:catapult` (15个脚本全找不到)

**根因**: `CResourceHandler::createInitial()` 在加载文件系统配置 (`config/filesystem.json`) 前，只扫描 `CONFIG/`, `DATA/`, `MODS/` 三个目录作为初始文件系统。但 `config/filesystem.json` 中的 `"SCRIPTS/": [{"type":"dir","path":"scripts"}]` 映射依赖 `scripts/` 目录被初始文件系统识别——然而 `createInitial()` 没有扫描 `SCRIPTS/`，导致 `loadDirectory()` 找不到 `scripts/` 目录，SCRIPTS 映射创建失败。

**修复**: 在 `vcmi/lib/filesystem/Filesystem.cpp` 的 `createInitial()` 中增加一行：
```cpp
recurseInDir("SCRIPTS", 16); // look for scripts
```
Commit: `859f4b79d` (vcmi submodule)

**效果**: 15个脚本中找到13个（`timedShield` 和 `timedBind` 仍是 patch 子目录问题，不致命）

### 3.2 Connector 替换为冒险版

**现象**: `strategic_env.py` 导入 `connector_v13.so` 但旧版是战斗用连接器，不支持冒险回调。

**修复**: 
1. 将 `connector_v13_adventure.so`（280K，Phase A 已验证版）复制为 `connector_v13.so`
2. 后续直接从 `vcmi_gym/connectors/build/` 重新编译 connector（支持 kwargs API）

**注意**: 旧版 Phase A 的 connector（`connector_v13.so.bak`，282K）不支持关键字参数传入，与当前 strategic_env.py 不兼容。

### 3.3 数据目录统一

**现象**: `DATA/LCDESC` 等资源找不到，VCMI无法加载游戏文本数据。

**修复**: `data/` 符号链接指向 `data-combined/`（已合并的完整游戏数据目录，含所有 .lod、.def 文件）

---

## 四、当前阻塞：adventure_wait() 回调不触发

### 4.1 现象

`reset()` 流程：
1. `_ensure_vcmi_running()` — 启动 connector.start() 后台线程 ✅
2. `_adventure_wait(timeout=300)` — 挂在 `adventure_wait()` 上 ❌

VCMI 线程日志显示到 `"Grouped 2 heroes"` 为止（地图加载完成），但没有 `[connector] adventure yourTurn: player=0` 消息。300秒超时后 segfault。

### 4.2 已排查的路径

| 尝试 | 结果 |
|------|------|
| 旧libmlclient.so + 旧connector | ABI不兼容（kwargs API vs positional args）|
| 新libmlclient.so + 旧connector (282K) | connector.start() 线程立即死亡 |
| 新libmlclient.so + 新编译connector | 线程存活，但不触发回调 |
| `red="MMAI_USER"` vs `red="StupidAI"` | 两者回调均不触发 |
| `os.chdir()` 到 `rel/bin/` | `init_vcmi()` 内部已有 `chdir(VCMI_BIN_DIR)`，无效 |
| 从 `vcmi-native/rel/bin/` 运行 | 同上结果 |
| 战斗环境 (`VCMI-v13`) 测试 | 同样挂起——确认不是 strategic_env 特有 |

### 4.3 根因分析（推测）

回调注册链应该是：
```
connector.start()
  → g_adventure_cb = adventure_yourTurn_callback  (threadconnector.cpp:466)
  → ML::start_vcmi()
    → VCMI 游戏主循环
      → 通知AI行动 → AAI::yourTurn()  (AAI.cpp:176)
        → if (g_adventure_cb)  → g_adventure_cb(player, userData)
```

但 `AAI::yourTurn()` 可能没有被调用到。可能原因：
1. VCMI 初始化时，`MMAI_USER` 被解析为 `"MMAI_USER_GYM"` 模型，但这个模型在 VCMI 的 AI 注册系统中不是标准 AI 名称
2. `init_vcmi()` 中的 `processArguments()` 创建了自定义模型包装器，但 VCMI 游戏主循环可能仍然使用标准的 AI 调度逻辑，而不是 MMAI 的 AI 路径
3. 多线程竞态：`g_adventure_cb` 在 `start()` 线程中设置，但 `AAI::yourTurn()` 在另一个线程中运行，可能存在可见性问题（虽然 `g_adventure_cb` 是全局指针，C++11 及以上应保证正确可见性）
4. VCMI 新版与旧版接口不兼容：`libvcmi.so` 是 vcmi-native 最新版编译，但 connector 是基于 vcmi-workspace 旧版编译的

### 4.4 关键代码位置

| 文件 | 行号 | 作用 |
|------|------|------|
| `vcmi_gym/connectors/v13/threadconnector.cpp` | 446-558 | `Connector::start()` — 入口 |
| 同上 | 466 | `g_adventure_cb = adventure_yourTurn_callback` — 注册回调 |
| 同上 | 545 | `init_vcmi(leftModel, rightModel, initargs)` |
| 同上 | 554 | `ML::start_vcmi()` — 启动游戏主循环 |
| 同上 | 561-568 | `adventure_yourTurn_callback()` — 回调实现 |
| 同上 | 572-583 | `Connector::adventureWait()` — Python等待回调 |
| `vcmi/ML/MLClient.cpp` | 452-557 | `init_vcmi()` — 初始化VCMI引擎 |
| 同上 | 512 | `GAME = std::make_unique<GameInstance>(aco)` |
| `vcmi/ML/strategic_state.cpp` | 19-20 | `g_adventure_cb` 声明 |
| `vcmi/AI/MMAI/AAI/AAI.cpp` | 175-184 | 回调调用点 `g_adventure_cb(playerColor, ...)` |
| `vcmi/lib/filesystem/Filesystem.cpp` | 127-157 | `createInitial()` — 已修复加SCRIPTS扫描 |
| `vcmi_gym/envs/v13/strategic_env.py` | 327-356 | `reset()` 实现 |
| 同上 | 495-535 | `_adventure_wait()` — 带超时的事件等待 |

---

## 五、修复建议

### 方案A：纯数据目录 + 旧版VCMI（推荐首选）

回退到 Phase A 已验证的完整编译链：
1. 用 `vcmi-gym/` 的全套旧版产物（`libmlclient.so`, `connector_v13.so` 等）
2. 适配 `strategic_env.py` 的 kwargs → positional args 转换
3. 确认连通后再逐步升级 lib 版本

### 方案B：重建 connector

在 `connectors/build/` 中针对新版 lib 重新编译 connector：
- 确保 `CMakeLists.txt` 正确链接新版 `libmlclient.so` 和 `libvcmi.so`
- 验证 `connector_v13.so` 的 `ThreadConnector` 构造函数签名匹配

### 方案C：在 AAI.cpp 加日志

在 `AAI.cpp` 的 `yourTurn()` 入口处加 `fprintf(stderr, ...)` 确认 VCMI 是否真的调用了这个方法。如果没调用，说明 AI 注册路径有问题。

---

## 六、环境复现命令

```bash
# WSL2 中
cd /home/administrator/vcmi-workspace

# 运行测试
timeout 90 python3 -c "
import sys, os
os.environ['LD_LIBRARY_PATH'] = '/home/administrator/vcmi-workspace/vcmi/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel'
sys.path.insert(0, '/home/administrator/vcmi-workspace')
from vcmi_gym.envs.v13.strategic_env import StrategicEnv, END_TURN
env = StrategicEnv(mapname='s1.vmap', red='MMAI_USER', blue='StupidAI', max_turns=3, boot_timeout=60)
obs, info = env.reset()
print('reset OK')
env.close()
"
```

---

## 七、git 记录

```
hero3_fresh main:    8b769c6 — Save current state
vcmi submodule:     859f4b79d — add recurseInDir(SCRIPTS,16) to createInitial()
```

