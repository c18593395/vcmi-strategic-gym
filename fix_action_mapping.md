# 动作映射修复方案 C7

## 现状
- 根因已确认：`s_turn_action` 写入但从未被读取
- 尝试过通过 MMAI `AAI::yourTurn()` 调用 `cb->moveHero()` → segfault
- 原因：在 yourTurn 回调链中调用 game action 不合法（GIL/callback 状态冲突）

## 方案 A：Connector 层直接发移动命令（推荐）

在 `libmlclient.so` 中新增函数，Python 通过 ctypes 直接调用：
```
void move_hero(int hero_id, int x, int y, int z)
```

这个函数在 VCMI 主线程上下文中运行（非回调链），可安全调用 `moveHero`。
Python 在 `_send_action()` 前调用此函数移动英雄。

### 实现步骤
1. `strategic_state.h`/`.cpp`：新增 `move_hero()` extern "C" 函数
2. 函数内部获取英雄指针→ `cb->moveHero(hero, int3(x,y,z), false)`
3. `strategic_env.py`：`step()` 中先根据 action 计算目标坐标 → 调用 `move_hero()` → 再 `_send_action()`
4. 编译验证

### 难点
- `move_hero` 函数如何获取 `cb`（CCallback）指针？
  - MMAI 的 `cb` 是全局可访问的
  - 或通过 VCMI 全局 `CGameHandler` 获取

## 方案 B：Nullkiller2 代替 MMAI_USER

切换 AI 类型为 Nullkiller2，其 `yourTurn()` 在回调后自动运行 `makeTurn()`，
英雄会由 Nullkiller2 AI 自主移动。模型作为观察者学习。

### 优劣
- ✅ 无需修改 C++，立即可用
- ❌ 模型不控制英雄，只是观察
- 可作为过渡方案

## 方案 C：修改 strategic_state.h 时保留字段 + 使用静态变量跨库通信

回到 `action` 字段方案，但 `moveHero` 由 `adventure_process_turn()` 内部执行
（同一 .so 内，无跨库问题），通过全局函数指针调用。

## 决定
先研究方案 A 的可行性。
