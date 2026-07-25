# 两个问题的完整解答

> 背景：对方在无 GPU 服务器上尝试 H3M 战略层训练，遇到两个阻塞问题
> 来源：我们项目已全部踩过并解决

---

## 问题 1：headless 下 engineUser==null，adventure 回调永不触发，死等 120s 超时

### 现象

```
headless 启动：
  1. debugStartTest 正常返回
  2. 第一个 yourTurn 能触发（adventure_wait 返回）
  3. 发完 action 后，第二个 yourTurn 永不触发
  4. adventure_wait_for_turn() 死等 120s → timeout
```

### 根因

VCMI 的 `yourTurn` 回调走 **CPlayerInterface**，但 headless 模式下不创建它。

```
headless 启动
  → CVCMIServer 创建, AI 初始化, 地图加载
  → 第一个 yourTurn：Nullkiller2::yourTurn() 里 g_adventure_cb 能走通
  → endTurn 后，server 切到下一个 player
  → 没有 CPlayerInterface → 网络包路由不到 AI
  → 第二个 yourTurn 永远不会来
  → adventure_wait 死等超时
```

### 解决方案（三件套）

**① 用 Nullkiller2，不用 MMAI**

MMAI 在 headless 下初始化 core dump。Nullkiller2 的 `AIGateway::yourTurn()` 有现成的 `g_adventure_cb` 钩子：
```cpp
void AIGateway::yourTurn(QueryID queryID) {
    if (g_adventure_cb) {
        strategic_state_update(cc->getGameStatePtr());
        g_adventure_cb(pn, g_adventure_cb_userdata);  // 阻断等 Python
    }
    nullkiller->makeTurn();  // fall through，不手动 endTurn
}
```

编译参数：
```cmake
-DENABLE_MMAI=OFF -DENABLE_NULLKILLER2_AI=ON
```

**② 回调后 fall through，不手动 endTurn**

```cpp
// ❌ 错误：回调里手动 endTurn
g_adventure_cb(pn, userdata);
cb->endTurn();  // 破坏 server 状态机

// ✅ 正确：回调后 return，让 Nullkiller2 自己走完
g_adventure_cb(pn, userdata);
// → 不调 endTurn，Nullkiller2 内部处理
```

**③ step() 必须是 WAIT→SEND 顺序**

```
❌ SEND → WAIT：action 发太早，s_turn_player 被消费，下一轮回调不来
✅ WAIT → SEND：先等 yourTurn 读状态，再发 action
```

### 验证方法

```bash
# 启动日志中必须有这一行
[DBG] setting g_adventure_cb

# 确认 AI 正确
grep "Nullkiller" MLClient.cpp
# → settings.write({"ai", "adventureAlliedAI"}) -> Nullkiller2
```

```python
env = StrategicEnv(mapname="Key to Victory.h3m", 
                   red="MMAI_USER", blue="MMAI_USER")
obs = env.reset()
assert np.count_nonzero(obs) > 0, "obs 全零说明 DummyVecEnv 短路未修复"

for i in range(5):
    obs, rew, done, _ = env.step(random_action)
    print(f"step {i}: obs_nz={np.count_nonzero(obs)}")
# 5 步全通 = 修复成功
```

---

## 问题 2：Xvfb 方案 — 所有 H3M 地图被系统 kill，adventure_wait 依然超时

### 现象

```bash
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
./VCMI_client
# → 进程 3 秒内被 kill
# → adventure_wait 依然超时
```

### 根因（三重致命）

| # | 原因 | 细节 |
|---|------|------|
| 1 | **内存暴涨** | VCMI_client 非 headless 模式加载 GUI 资源（图片/字体/音乐），+Xvfb 软渲染，内存从 500MB → 3GB+，被 OOM killer 杀 |
| 2 | **进程存活检测** | VCMI 的 CSDLHandler/ILogger 检测到无实际 display（Xvfb fake），某些定时器/事件循环进入空转分支，守护进程认为 client dead → SIGKILL |
| 3 | **adventure 回调依然不触发** | 非 headless 下 CPlayerInterface 确实创建了，但 yourTurn 走 **UI 事件队列**（SDL 键盘事件），不走 `g_adventure_cb`。ML 模块的 atomic 变量没人设，adventure_wait 照常死等 |

### 结论：Xvfb 是死路

三个致死原因中任何一个都足够否决。**不要在这条路上浪费时间。**

### 正确路线

```
❌ Xvfb + headless=false
❌ 无 GPU 服务器训练
✅ headless=true + Nullkiller2 + 修回调问题
✅ 训练和推理分离
```

---

## 针对"无 GPU 服务器"的完整建议

### 路线图

```
有 GPU 的机器（云/本地）:
  PPO 训练 → 2000ep × 50步
  → 出 .pt checkpoint (203KB)
  → torch.onnx.export() → .onnx

无 GPU 服务器:
  ① 编译 VCMI + ML 模块（同源三件套）
     cmake -DENABLE_ML=ON -DENABLE_NULLKILLER2_AI=ON -DENABLE_MMAI=OFF
  ② ONNX Runtime CPU 推理（模型 51K 参数，<5ms）
  ③ headless 模式加载模型
  ④ 循环：读 state → ONNX 推理 → adventure_send_action
```

### 技术验证要点

```bash
# 1. 三件套同源编译（必须！）
libvcmi.so    ~20M
libmlclient.so  ~16M
connector_v13.so ~8M
# 日期一致 = 同一次编译

# 2. 环境变量
export LD_LIBRARY_PATH="~/vcmi-native/rel/bin:~/vcmi_gym/connectors/rel"
export STRATEGIC_STATE_LIB="~/vcmi-native/rel/bin/libmlclient.so"

# 3. 每次改代码清 pyc
find /project -path "*/__pycache__" -type d -exec rm -rf {} +

# 4. ep_runner 用 os._exit(0) 硬退出
# 避免 VCMI 线程阻止 Python 进程退出
```

### 我们踩过的坑（对方可直接跳过）

| 坑 | 解决 | 耗时 |
|----|------|------|
| ABI 不兼容（两套源码混搭 .so） | 全量重编三件套 | ~3h |
| MMAI core dump | 切 Nullkiller2 | ~2h |
| DummyVecEnv 短路（obs 全零） | 删短路代码 | ~1h |
| subprocess 僵尸（130% CPU 自旋） | os._exit(0) | ~1h |
| step2 挂死（第二个 yourTurn 不来） | WAIT→SEND + 不手动 endTurn | ~8h |
| Xvfb 进程被杀 | 放弃 Xvfb | ~4h |
| vmap 误当战略图 | 只用 H3M 经典图 | ~2h |

**总计节省：~21h 的踩坑时间。**
