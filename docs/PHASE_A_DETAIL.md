# Phase A: VCMI 冒险地图 API — 全局指针 + ctypes 方案

> P0 阻塞项。方案：VCMI 侧放一个 C 结构体全局指针，Python 用 ctypes 直读。
> 不写 pybind11，不序列化，不跨进程。1 次 memcpy。

---

## 架构

```
VCMI 游戏循环 (每帧)
  └→ strategic_state_update(&gameState)
       └→ 填充 g_strategic_state (C 结构体, ~2KB)

Python (任何线程，随时)
  └→ reader = StrategicReader()
     state = reader.read()   # ctypes 读 libmlclient.so 里的全局指针
     print(state["day"], state["players"][0]["gold"])
```

**为什么比 pybind11 好**：
- 不需要编译 pybind11 绑定（不引入新依赖）
- C 结构体固定布局，Python ctypes 零拷贝读取
- 每帧填充一次，Python 随时读，无锁（单写多读）

---

## 文件

### 1. `strategic_state.h` — 结构体定义

```c
// 放到 vcmi/ML/strategic_state.h
// 和 MLClient.h 同级

struct StrategicState {
    int32_t day, week, month;
    int32_t current_player;
    int32_t map_width, map_height, has_underground;
    int32_t player_count;
    StrategicPlayer players[8];   // {color, gold, wood, ..., heroes, towns}
    StrategicHero   heroes[8];    // {id, owner, pos, movement, army[7], ...}
    StrategicTown   towns[8];     // {id, owner, pos, buildings, garrison[7]}
    int32_t game_over;            // 0=进行中, 1=红赢, 2=蓝赢
    int32_t _version;
};
// 总大小 ~2KB
```

**已写好**：`D:\Bigdata\hero3_fresh\strategic_state.h`

### 2. `strategic_state.cpp` — 填充逻辑

放 `vcmi/ML/strategic_state.cpp`，编译进 libmlclient.so。

只有一个函数：

```cpp
extern "C" StrategicState* g_strategic_state = nullptr;

void strategic_state_update(void* game_state_ptr) {
    auto& gs = *static_cast<CGameState*>(game_state_ptr);
    auto& s = *g_strategic_state;

    s.day = gs.day;
    s.current_player = gs.actingPlayers.begin()->getNum();

    for (auto& [color, ps] : gs.players) {
        // 填玩家资源
        s.players[i].gold = ps.resources[GOLD];
        // ...
    }

    for (auto* obj : gs.map->objects) {
        if (auto* hero = dynamic_cast<CGHeroInstance*>(obj)) {
            // 填英雄字段
            s.heroes[i].pos_x = hero->pos.x;
            // ...
        }
        if (auto* town = dynamic_cast<CGTownInstance*>(obj)) {
            // 填城镇字段
        }
    }
}
```

**已写好**：`D:\Bigdata\hero3_fresh\strategic_state.cpp`

### 3. `strategic_reader.py` — Python 读取器

```python
from strategic_reader import StrategicReader

reader = StrategicReader()
state = reader.read()

# state == {
#   "day": 7, "current_player": 0,
#   "players": [{"color": 0, "gold": 5000, "heroes": [...], "towns": [...]}, ...],
#   "heroes": [{"name": "Orrin", "pos": (5,3,0), "movement": 1560, ...}, ...],
#   "towns": [{"name": "Castle", "owner": 0, "buildings": 0xFF, ...}, ...],
#   "game_over": 0
# }
```

**已写好**：`D:\Bigdata\hero3_fresh\strategic_reader.py`

---

## 集成步骤

### Step 1: 放文件

```bash
cp strategic_state.h   vcmi/ML/strategic_state.h
cp strategic_state.cpp vcmi/ML/strategic_state.cpp
```

### Step 2: 修改 CMakeLists.txt

在 `vcmi/ML/CMakeLists.txt` 加一行：

```cmake
target_sources(mlclient PRIVATE strategic_state.cpp)
```

### Step 3: 初始化全局指针

在 `vcmi/ML/MLClient.cpp` 的 `init_vcmi()` 里加：

```cpp
#include "strategic_state.h"
extern StrategicState* g_strategic_state;

void init_vcmi(...) {
    g_strategic_state = new StrategicState();
    memset(g_strategic_state, 0, sizeof(StrategicState));
    g_strategic_state->_version = 1;
    // ... 原有初始化代码 ...
}
```

### Step 4: 每帧更新

在 VCMI 冒险地图 AI 回调里（`MMAI::BAI::Router` 或 `getAction` 调用点）：

```cpp
#include "strategic_state.h"
extern void strategic_state_update(void*);

// 在 getAction 开头加：
strategic_state_update(&gameState());
```

**关键**：`gameState()` 是 `CGameState&` 的访问入口，在 `IGameInfoCallback` 或 `CBattleInfoCallback` 里可用。

### Step 5: 重新编译

```bash
cd vcmi/rel
cmake --build . --target mlclient -j$(nproc)
```

### Step 6: Python 验证

```python
import sys; sys.path.insert(0, '.')
from strategic_reader import StrategicReader

reader = StrategicReader("vcmi/rel/bin/libmlclient.so")
state = reader.read()
print(state["day"], state["players"][0]["gold"])
```

---

## 任务拆分

| # | 任务 | 预计 |
|---|------|------|
| A1 | 放 `.h/.cpp` 到 vcmi/ML/，改 CMakeLists.txt | 10min |
| A2 | MLClient.cpp 加全局指针初始化 | 5min |
| A3 | 找对的位置加 `strategic_state_update()` 调用 | 30min |
| A4 | 重新编译 libmlclient.so | 5min |
| A5 | Python 验证：读 day + 玩家金币 | 10min |
| A6 | 补齐玩家的 hero_count/town_count | 20min |
| A7 | 验证英雄位置、移动力、兵力 | 20min |
| A8 | 验证城镇建筑、驻兵 | 20min |

**总计：~2 小时**
