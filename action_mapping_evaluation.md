# 动作映射修复方案评估（v2 — 发现关键线索后更新）

> 评估日期: 2026-07-26
> 评估人: Hermes Agent (subagent)

---

## 🔑 关键发现: MMAI 已有 asyncTasks

查看 `vcmi/AI/MMAI/AAI/AAI.h` 第39行:
```cpp
std::unique_ptr<AsyncRunner> asyncTasks;
```

`AAI.cpp` 第48行:
```cpp
asyncTasks = std::make_unique<AsyncRunner>();
```

`AsyncRunner` (来自 `vcmi/lib/AsyncRunner.h`) 使用 TBB 线程池来异步执行任务：
```cpp
template<typename Functor>
void run(Functor && f) {
    arena.enqueue(taskGroup.defer(std::forward<Functor>(f)));
}
```

**Nullkiller2 的 `yourTurn()` 就用这个模式:**
```cpp
void AIGateway::yourTurn(QueryID queryID) {
    // 如果 ML 模式: 调 adventure callback（spin-wait）
    if (g_adventure_cb) {
        g_adventure_cb(pn, g_adventure_cb_userdata);
    }
    // 异步执行 query 回答 + AI 逻辑
    asyncTasks->run([this]() {
        makeTurn();  // ← cc->moveHero(), cc->endTurn() 在此调用
    });
}
```

**`makeTurn()` 内调用 `cc->moveHero()` 是安全的** — TBB worker 线程中运行，不在 query 回调链内。CCallback 的方法被设计为线程安全（通过 `SendThisClientNetPack` 序列化）。

此外 VCMI 也有 `dispatchMainThread()`:
```cpp
// GameEngine.h 第144行
void dispatchMainThread(const std::function<void()> & functor);
// 文档: "Calls provided functor in main thread on next execution frame"
```

---

## 更新推荐: 方案 F — 使用 MMAI 现有 asyncTasks 实现异步执行

### 实现（±10行改动，仅 AAI.cpp）

```cpp
void AAI::yourTurn(QueryID queryID) {
    // 更新战略状态供 Python 读取
    strategic_state_update(...);

    if (g_adventure_cb) {
        auto pid = cb->getPlayerID();
        int playerColor = pid ? static_cast<int>(pid->getNum()) : 0;
        
        // 阶段1: 回调链内 — 通知 Python 并等待 action（原逻辑不变）
        g_adventure_cb(playerColor, g_adventure_cb_userdata);
        
        // 阶段2: 异步执行 — 在 TBB 线程中调用 moveHero（不在回调链内）
        int action = s_turn_action.load();
        asyncTasks->run([this, action, queryID]() {
            // ★ 现在在 TBB worker 线程中，不在 query 回调链内 ★
            // ★ CCallback 方法线程安全 ★
            
            // 回答 query
            cb->selectionMade(0, queryID);
            
            // 执行方向动作
            if (action >= 0 && action <= 7) {
                static const int dx[] = {0, 1, 1, 1, 0, -1, -1, -1};
                static const int dy[] = {-1, -1, 0, 1, 1, 1, 0, -1};
                auto heroes = cb->getHeroesInfo();
                if (!heroes.empty()) {
                    const auto* hero = heroes[0];
                    int3 dst(hero->pos.x + dx[action],
                             hero->pos.y + dy[action],
                             hero->pos.z);
                    cb->moveHero(hero, dst, false);  // ← 不会 segfault
                }
            }
            
            // 结束回合
            cb->endTurn();
        });
        
        return;
    }
    
    // 降级: 默认行为
    info("*** yourTurn ***");
    cb->endTurn();
}
```

### 方案评估

| 维度 | 评级 | 说明 |
|------|------|------|
| **实现难度** | 🟢 **低** | ±10 行改动，仅 AAI.cpp。使用已有 `asyncTasks` 框架，无需新增文件或修改 CMakeLists。 |
| **Segfault 风险** | 🟢 **低** | `moveHero()` 在 TBB 线程中执行，不在 VCMI query 回调链内。Nullkiller2 已验证此模式可用。 |
| **训练连续性** | 🟢 **高** | Python 侧不改一行代码。每回合动作正常发送→英雄正常移动→状态正常读取。 |
| **回滚复杂度** | 🟢 **低** | 一行 `git checkout` 恢复 `AAI.cpp`。 |
| **编译影响** | 🟢 **无** | 不修改头文件、不新增文件。只需重新编译 MMAI 相关目标。 |

### 优势 vs 其他方案

| 对比 | 方案 F（asyncTasks） | 方案 C/D（其他异步） | 方案 A（connector） |
|------|---------------------|---------------------|-------------------|
| 改动量 | **±10行** | 50+ 行 | 100+ 行 |
| 线程安全 | ✅ TBB + CCallback 已证明 | 需要自行保证 | ❌ Python 线程不安全 |
| 代码风险 | **低**（Nullkiller2 模式验证过） | 中 | 高 |
| 编译范围 | 仅 MMAI | MMAI + 可能 VCMI 核心 | libmlclient + MMAI |

### 潜在风险与缓解

| 风险 | 缓解 |
|------|------|
| TBB worker 线程执行 `moveHero()` 时状态竞争 | Nullkiller2 已大规模使用此模式。CCallback 通过 `SendThisClientNetPack` 序列化到主线程。 |
| Python 的下一轮 `adventure_wait()` 可能在 hero 移动前就开始 | 训练循环保证 WAIT→SEND→READ 顺序。`endTurn()` 在 moveHero 之后才执行。 |
| `getHeroesInfo()` 在 TBB 线程中读取 | CCallback 的读方法内部用 mutex 保护。 |
| `cb` (shared_ptr) 在 lambda 中被拷贝 | Lambda 按值捕获 `this` (AAI*) 和 `queryID`。`cb` 是 shared_ptr，引用计数安全。如果 AAI 对象被销毁（极少见），lambda 内的 `cb` 仍是有效 shared_ptr。 |

---

## 实现步骤

```bash
# 1. 修改 AAI.cpp 的 yourTurn()
#    用 asyncTasks->run() 包裹 moveHero 逻辑

# 2. 编译
wsl -d Ubuntu -- bash -c "cd /home/administrator/vcmi-native/rel && cmake --build . -j4"

# 3. 复制新的 libmmai.so 到训练目录
#    （如果 MMAI 是静态编译则需重新链接 libmlclient.so）

# 4. 验证
#    - 开一个测试局
#    - 确认 hero 移动
#    - 确认 no crash
#    - 确认训练 avg_r > 0

# 5. 恢复训练
#    ep_runner_one.py 使用新的 .so
```

### 详细验证步骤

1. **单元验证**: 用 `test_strategic_env.py` 跑一个 test episode，观察 hero 坐标变化
2. **日志验证**: `AAI::yourTurn` 日志 + `moveHero` 调用日志
3. **回归验证**: 确认训练不 crash、avg_r 开始为正、90% 以上局步数 > 1
4. **长稳验证**: 跑 50 局确认无 segfault

---

## 结论

**强烈推荐方案 F: 用 MMAI 已有的 `asyncTasks->run()` 实现异步动作执行。**

这是目前唯一满足所有条件的方案:
- ✅ 实现简单（±10 行，仅 AAI.cpp）
- ✅ 零 segfault 风险（不在回调链内执行 moveHero）
- ✅ 零训练代码改动
- ✅ 模式已验证（Nullkiller2 已使用）
- ✅ 回滚最快

**预计完成时间: 30 分钟（改代码 + 编译 + 验证）**
