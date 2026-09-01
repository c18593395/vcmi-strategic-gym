# WSL知识库 — 参考速查

> 本文件是 `WSL知识库.md` 总索引下的稳定速查子文档（内存偏移/ABI/文件索引/数据流/双目录陷阱）。
> 纯查表，极少改动。

---

## 一、内存偏移表（快速索引）



### CN 3.1 (Heroes3.exe) — 固定地址



**玩家结构体：** `pb = *0x0082B0BC`



| 字段 | 偏移 | 已验证 |

|------|------|--------|

| gold | pb+0xB4 | ✅ |

| wood | pb+0x9C | ✅ |

| ore | pb+0xA4 | ✅ |

| mercury | pb+0xA0 | ✅ |

| sulfur | pb+0xA8 | ✅ |

| crystal | pb+0xAC | ✅ |

| gems | pb+0xB0 | ✅ |

| hero_count | pb+0x01 | ✅ |

| town_count | pb+0x3E | ✅ |



**英雄结构体：** `hero_addr = gd + 1170*hid + 136736`, `gd = 0x00826D40`



| 字段 | 偏移 | 已验证 |

|------|------|--------|

| pos_x | hero+0x00 | ✅ |

| pos_y | hero+0x02 | ✅ |

| pos_z | hero+0x04 | ✅ |

| cur_movement | hero+0x4D | ✅ |

| max_movement | hero+0x49 | ✅ |

| level | hero+0x55 | ✅ |

| attack | hero+0x476 | ✅ |

| defense | hero+0x477 | ✅ |

| power | hero+0x478 | ✅ |

| knowledge | hero+0x479 | ✅ |

| exp | hero+0x51 | ✅ |

| army_count[0..6] | hero+0xAD + i*4 | ✅ |

| army_type[0..6] | hero+0x91 + i*4 | ✅ |

| in_battle | 0x00825BF8 (3=战斗) | ✅ |



### HD Mod 5 RC94 + HOTA 1.6.1 — AOB 动态扫描



**玩家指针：** `base + 0x29CCFC` → pb



**英雄地址：** `pb + 0x278E0`（CN31 的 gameData 数组完全不一样）



已验证偏移同 CN31：pos_x/y, movement, max_movement

推断同 CN31（待验证）：资源, 属性, 兵力



> 详见 `对齐清单_CN31.md` 和 `对齐清单_HD.md`



---



## 二、关键文件索引



| 文件 | 用途 |

|------|------|

| `docs/总任务.md` | 全局架构、Phase A~G 进度 |

| `docs/当前任务清单.md` | 双轨可执行任务表 |

| `对齐清单_CN31.md` | CN 3.1 完整内存偏移 |

| `对齐清单_HD.md` | HD Mod 内存偏移 |

| `train_wsl2_ppo.py` | PPO 训练主脚本 |

| `ep_runner_one.py` | 单 episode 执行器（支持 --blue_model） |

| `train_loop.sh` | 24/7 循环脚本 |

| `eval_elo.py` | ELO 评估脚本 |

| `scan_maps.py` | 全地图扫描 |

| `strategic_reader.py` | Python ctypes 直读游戏状态 |

| `check_training.sh` | 训练状态查询 |

| `WSL知识库.md` | **本文件 — 单页知识总汇** |

| `docs/WSL踩坑点.md` | 踩坑详细记录 |

| `docs/step2分析.md` | step2 问题分析全记录 |

| `checkpoints/` | 模型 checkpoint 目录 |

| `maps/` | 158 张 H3M 地图 |

| `available_maps.json` | 110 张可用地图列表 |

| `scripts/` | 历史测试/一次性脚本 |

| `_archive/` | 已完成/废弃旧文件 |



---



## 三、StrategicState 结构体布局（C++ ↔ Python ABI）



```cpp

// C++ struct (WSL, libmlclient.so)

int32_t day, week, month, current_player;     //  16 字节

int32_t map_width, map_height;                 //   8

int32_t has_underground, player_count;         //   8

StrategicPlayer players[8];                    // 384 (8×48)

StrategicHero   heroes[8];                     //1216 (8×152)

StrategicTown   towns[8];                      // 704 (8×88)

int32_t game_over;                             //   4

int32_t action;                                //   4  ← Python 写入的 RL 动作

int32_t _version;                              //   4

int32_t passable[8];                           //  32

// Total: ~2380 字节

```



**关键字段偏移**（Python ctypes 必须匹配）：

- `game_over` @ 2336

- `action`    @ 2340  ← 之前漏了这个字段！

- `_version`  @ 2344

- `passable`  @ 2348  ← 没 action 时会前移 4 字节，数据全错位



## 四、数据流（修复后）



```

VCMI server → AI::yourTurn()

  → strategic_state_update(CGameState*)   // dlsym 调用，填充所有字段

  → g_adventure_cb ? callback : fallback   // g_adventure_cb 通常为 null

  → fallback: 读 action → moveHero → endTurn

  ↓

Python → 读 g_strategic_state (ctypes)

  → obs = non-zero (真实英雄位置、资源、passability)

  → 模型输出 action

  → adventure_send_action(action)  // 写入原子变量

  → 等待下一轮

```



## 五、WSL 双目录构建陷阱



| 目录 | 用途 |

|------|------|

| `/home/administrator/vcmi-native/` | 源码（可编辑） |

| `/home/administrator/vcmi-native-build/` | cmake 源目录（`CMAKE_HOME_DIRECTORY`）|

| `/home/administrator/vcmi-native-build/rel/` | 构建目录（编译产物） |

| `/home/administrator/vcmi-native/rel/` | 部署目录（训练时加载的 .so）|



**改代码后必须同步两份**：`cp vcni-native/* vcmi-native-build/*`。不然改了 vcmi-native 的 .cpp，编译的还是 vcmi-native-build 的旧代码。



**RUNPATH 陷阱**：`libmlclient.so` 和 `vcmiserver` 的 RUNPATH 指向 `/home/administrator/vcmi-native-build/rel/bin/`，运行时优先从 build 目录加载 `.so`。部署到 `rel/` 后靠 `LD_LIBRARY_PATH` 覆盖。



**#46 修复关键**：重建三件套（vcmiserver + libmlclient.so + libMMAI.so）后 segfault 消失。installNewBattleInterface 全流程通过（加 fprintf 确认）。工作组合见 `WSL踩坑点.md` #50。



**当前阻塞（2026-07-29）**：installNewBattleInterface 修复后通，但 game main loop 启动时 segfault。非代码改动导致，WSL 重启后稳定复现，所有组件版本组合均崩。需 gdb backtrace 定位。另 `adventure_wait_for_turn()` 信号量机制不工作（`AAI::yourTurn` 不设原子变量），`obs_nz=0` 的根本原因。



===



✅ **2026-07-29 全线打通**：env.reset() 返回 obs_nz=8/264！全部修复：

- Discord null dereference（`GameEngine::hasDiscord()` guard）

- 信号量通信（`AAI::yourTurn` 调 `adventure_process_turn()`）

- Hero pool even 检查（`pop_back` 替代 throw）

- step() 5 步无崩溃

- 工作组合全部用最新重建产物（见 `WSL踩坑点.md` #50）



**当前剩余：** obs_nz=8 仅 passable。`getHeroesInfo()` 返回空（地图无初始英雄），`fill_state_from_cb` 需迭代。

```





