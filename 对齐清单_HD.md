# 模型对齐清单 — HD Mod 真实 HoMM3 内存
> **目标：** 将 VCMI 观测向量与 HD Mod (Heroes3_HD.exe) 真实内存地址对齐
> **用法：** 用 Cheat Engine 或 ReadProcessMemory 验证每个字段，填到"真实游戏地址"列
> **标记：** ✅ = 已验证；🔄 = 已知但需验证偏移；⏳ = 待测（优先）；⬜ = 未开始

---

## 一、观测向量整体布局 (256 维)

| 索引范围 | 长度 | 内容 |
|---------|------|------|
| 0-7 | 8 | Global（日期/玩家/地图信息） |
| 8-103 | 96 | Players（8个玩家 × 12字段/个） |
| 104-241 | 138 | Heroes（6个英雄 × 23字段/个，截断） |
| 242-255 | 14 | 填充零（未使用） |

---

## 二、Global（索引 0-7）

> HD Mod 基址 = `Heroes3_HD.exe` 模块基址（一般为 `0x00400000`）
> 指针链：`base + 0x29CCFC` → pb（玩家结构体指针）
> 注意：HD Mod 地址**每次加载都可能变化**，绝对地址不可固定，只能用指针链

| 索引 | 字段 | VCMI 类型 | 描述 | HD Mod 地址公式 | 状态 |
|------|------|-----------|------|----------------|------|
| 0 | day | int32 | 当天 (1-7) | `?` | ⏳ 待测 |
| 1 | week | int32 | 当周 (1-4) | `?` | ⏳ 待测 |
| 2 | month | int32 | 当月 (1+) | `?` | ⏳ 待测 |
| 3 | current_player | int32 | 当前行动玩家颜色 | `pb + ?` （CN31用0x82B0B4直读） | ⏳ 待测 |
| 4 | map_width | int32 | 地图宽（格数） | `?` | ⏳ 待测 |
| 5 | map_height | int32 | 地图高（格数） | `?` | ⏳ 待测 |
| 6 | has_underground | int32 | 是否有地下层 | `?` | ⏳ 待测 |
| 7 | player_count | int32 | 玩家数 (2) | `?` | ⏳ 待测 |

---

## 三、Players（索引 8-103，8个玩家 × 12字段）

> HD Mod：`pb = *(base + 0x29CCFC)` → 当前玩家结构体指针
> 玩家步进（stride）= `0x168`（360 bytes，同 CN31 的 PLAYER_STRIDE，但**需验证**）

### 每个玩家的 12 个字段（偏移相对 pb）

| 偏移 | 字段 | VCMI 类型 | 描述 | HD Mod 地址公式 | 状态 |
|------|------|-----------|------|----------------|------|
| +0 | color | int32 | 颜色编号 (0=红) | `pb + 0x00` → BYTE（推断同CN31） | 🔄 推断 |
| +1 | human | int32 | 是否人类玩家 | `pb + ?` | ⏳ 待测 |
| +2 | gold | int32 | 金币 | `pb + 0xB4` → DWORD（推断同CN31） | 🔄 推断 |
| +3 | wood | int32 | 木材 | `pb + 0x9C` → DWORD | 🔄 推断 |
| +4 | mercury | int32 | 水银 | `pb + 0xA0` → DWORD | 🔄 推断 |
| +5 | ore | int32 | 矿石 | `pb + 0xA4` → DWORD | 🔄 推断 |
| +6 | sulfur | int32 | 硫磺 | `pb + 0xA8` → DWORD | 🔄 推断 |
| +7 | crystal | int32 | 水晶 | `pb + 0xAC` → DWORD | 🔄 推断 |
| +8 | gems | int32 | 宝石 | `pb + 0xB0` → DWORD | 🔄 推断 |
| +9 | hero_count | int32 | 英雄数量 | `pb + 0x01` → BYTE | 🔄 推断 |
| +10 | town_count | int32 | 城镇数量 | `pb + 0x3E` → BYTE | 🔄 推断 |
| +11 | alive | int32 | 是否存活 | `?` | ⏳ 待测 |

> 注意：CN 3.1 已验证的资源偏移（0x9C~0xB4）在 HD Mod 下**结构体布局可能相同**，但必须实测验证。
> 历史CE扫描：HD Mod 资源直接地址曾在 `0x0058A350`-`0x0058A368` 范围（依赖模块基址，每次不同）

> 另一条线索：`base+0x29CCFC` 给出的 pb 指向玩家结构体。如果结构体与 CN 3.1 相同（PC版同源）：
> - 玩家索引 `pb+0x00`=player_id, `pb+0x01`=heroescount
> - 当前英雄 `pb+0x04`=curhero_idx（-1=城镇 ✅ 已验证）
> - 英雄ID表 `pb+0x08`=heroes[8] DWORD数组
> - 城镇ID表 `pb+0x40`=towns[48]
> - 资源 `pb+0x9C`~`pb+0xB4` 同CN31
> - 收入 `pb+0x108` 同CN31
> **以上均为推断，每个字段都需实测对齐验证**

---

## 四、Heroes（索引 104-241，最多 6 个英雄 × 23字段）

> HD Mod：`hero_addr = pb + 0x278E0`（直接从 scene.py 代码中得出）
> **注意：** 这个地址公式 vs. CN31 的 `gd + 1170*hid + 136736` 完全不同
> HD Mod 用了**固定偏移从 pb 跳到英雄**，而非通过 gameData 数组
> 英雄步进未知，需验证

### 每个英雄的 23 个字段（偏移相对 hero_addr）

| 偏移 | 字段 | VCMI 类型 | 描述 | HD Mod 地址公式 | 状态 |
|------|------|-----------|------|----------------|------|
| +0 | id | int32 | 英雄唯一 ID | `pb + 0x08 + slot*4`（从ID表） | 🔄 推断 |
| +1 | owner | int32 | 归属玩家颜色 | `hero + 0x22` → BYTE（推断同CN31） | 🔄 推断 |
| +2 | pos_x | int32 | 地图 X 坐标 | `hero + 0x00` → WORD | ✅ 已知 |
| +3 | pos_y | int32 | 地图 Y 坐标 | `hero + 0x02` → WORD | ✅ 已知 |
| +4 | pos_z | int32 | 地图层 | `hero + 0x04` → WORD（推断同CN31） | 🔄 推断 |
| +5 | movement | int32 | 当前移动力 | `hero + 0x4D` → WORD | ✅ 已知 |
| +6 | max_movement | int32 | 最大移动力 | `hero + 0x49` → DWORD | ✅ 已知 |
| +7 | level | int32 | 英雄等级 | `hero + 0x55` → BYTE | 🔄 推断 |
| +8 | attack | int32 | 攻击力 | `hero + 0x476` → BYTE | 🔄 推断 |
| +9 | defense | int32 | 防御力 | `hero + 0x477` → BYTE | 🔄 推断 |
| +10 | power | int32 | 力量 | `hero + 0x478` → BYTE | 🔄 推断 |
| +11 | knowledge | int32 | 知识 | `hero + 0x479` → BYTE | 🔄 推断 |
| +12 | mana | int32 | 当前魔法值 | `hero + 0x18` → WORD（推断同CN31） | ⏳ 待测 |
| +13 | max_mana | int32 | 最大魔法值 | `?` | ⏳ 待测 |
| +14 | exp | int32 | 经验值 | `hero + 0x51` → DWORD | 🔄 推断 |
| +15 | army_slot0 | int32 | 部队格1 — 数量 | `hero + 0xAD` → DWORD | 🔄 推断 |
| +16 | army_slot1 | int32 | 部队格2 — 数量 | `hero + 0xB1` → DWORD | 🔄 推断 |
| +17 | army_slot2 | int32 | 部队格3 — 数量 | `hero + 0xB5` → DWORD | 🔄 推断 |
| +18 | army_slot3 | int32 | 部队格4 — 数量 | `hero + 0xB9` → DWORD | 🔄 推断 |
| +19 | army_slot4 | int32 | 部队格5 — 数量 | `hero + 0xBD` → DWORD | 🔄 推断 |
| +20 | army_slot5 | int32 | 部队格6 — 数量 | `hero + 0xC1` → DWORD | 🔄 推断 |
| +21 | army_slot6 | int32 | 部队格7 — 数量 | `hero + 0xC5` → DWORD | 🔄 推断 |
| +22 | in_battle | int32 | 是否战斗中 | `?`（HD无scene=3标志，需方向键测试判断） | ⏳ 待测 |

### 英雄索引表

| 英雄 | 观测索引范围 | HD Mod 地址公式 |
|------|-------------|----------------|
| Hero 0 | 104-126 | `pb + 0x278E0 + 0*?`（步进未知） |
| Hero 1 | 127-149 | `pb + 0x278E0 + 1*?` |
| Hero 2 | 150-172 | `pb + 0x278E0 + 2*?` |
| Hero 3 | 173-195 | `pb + 0x278E0 + 3*?` |
| Hero 4 | 196-218 | `pb + 0x278E0 + 4*?` |
| Hero 5 | 219-241 | `pb + 0x278E0 + 5*?` |

---

## 五、HD Mod 已知地址（已验证 ✅）

### 指针链
| 路径 | 地址 | 说明 | 状态 |
|------|------|------|------|
| 基址 | `module_base` | 默认 `0x00400000` | ✅ |
| pb 指针 | `base + 0x29CCFC` | → pb 当前玩家结构体 | ✅ |

### 场景检测
| 标志 | 地址/偏移 | 值含义 | 状态 |
|------|----------|-------|------|
| 当前英雄索引 | `pb + 0x04` | -1=城镇, 0~155=英雄 | ✅ 已验证 |
| 场景标志（pb+0x3C） | `pb + 0x3C` | `0xFF01FF3F`=冒险图, `0x0001FF3F`=城镇 | ✅ 已验证 |
| 英雄位置（pb+hero_offset） | `pb + 0x278E0` | DWORD, 低16位=X, 高16位=Y | ✅ 已验证 |

### 英雄字段（已验证 ✅）
| 字段 | 偏移 | 类型 | 说明 |
|------|------|------|------|
| pos_x | `hero + 0x00` | WORD | 已验证（位置读法与CN31一致） |
| pos_y | `hero + 0x02` | WORD | 已验证 |
| mp_cur | `hero + 0x4D` | WORD | 当前移动力（同CN31） |
| mp_max_cache | `hero + 0x49` | DWORD | 最大MP缓存（不更新，同CN31） |

---

## 六、不在观测向量中的字段

### 部队类型

| 字段 | HD Mod 偏移 | 状态 |
|------|-----------|------|
| army_type[0..6] | `hero + 0x91 + i*4` → DWORD（推断同CN31） | 🔄 推断 |

### 城镇信息
> HD Mod 城镇结构体偏移完全未知

### HD Mod 关键差异（⚠️ 与 CN31 核心不同）

| 项目 | CN31 | HD Mod | 影响 |
|------|------|--------|------|
| 基址 | 固定0x00400000 | 可变（ASLR） | 必须用指针链 |
| pb指针 | `base + 0x42B0BC` | `base + 0x29CCFC` | 完全不同 |
| gameData | 有 (`0x00826D40` 指针) | 未知 | 日期/所有权读取方式不同 |
| 场景检测 | `dword_825BF8` 直读 | pb+0x04 + pb+0x3C + 方向键测试 | 无场景标志位代替 |
| 英雄地址 | gameData数组 (stride 1170) | pb + 0x278E0（固定偏移） | 寻址完全不同 |
| 输入方式 | keybd_event 生效 | PostMessageW 生效 | 硬件/消息机制不同 |
| 弹性窗口 | 无（全屏） | 有（窗口化） | HD_screen只占左上角 |

---

## 七、优先测量顺序（HD Mod 版本）

| 优先级 | 字段 | 原因 |
|--------|------|------|
| P0 | **hero_addr 步进** | 完全未知英雄数组间距 |
| P0 | **游戏日期读取** | 无 gameData 指针，需扫描找日期地址 |
| P0 | **战斗检测** | HD无 scene=3 标志，需找战斗标志位 |
| P1 | 所有资源偏移（pb+0x9C~0xB4） | 推断相同但须实测 |
| P1 | 当前玩家ID（current_player） | CN31有0x82B0B4直读，HD需找对应 |
| P1 | mana / max_mana | 两个版本均待测 |
| P1 | map_size / has_underground | 简单扫描 |
| P2 | 城镇全部字段 | 完全未探索 |
| P2 | 所有权表（ownership） | 无gameData需找等效读取方式 |

> 建议测法：CE搜当前英雄名字 → 得到英雄地址 → 验证已知偏移 → 推算步进 → 逐字段对齐
