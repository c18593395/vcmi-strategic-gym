# WSL踩坑点 — 地图-vmap生成

> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。

---

### 18. A1/A5 地图频繁崩溃或超时

- **现象**: R2 A1 1分钟 crash (exit=-7)，R3 A5 20分钟超时

- **可能原因**: 地图文件本身问题，或 VCMI 对这些地图初始化不稳定

- **现状**: A2/A6 相对稳定，A4/A7 已用 A1 模板重建修复



### 19. ml-mini.vmap 的 hero 类型问题

- **现象**: 用 core:knight 等标准英雄类型加载失败

- **原因**: vmap 需要 ML mod 的英雄类型 (ML:hero_X)

- **解决**: s1.vmap 用 ML:hero_0 等



### 20. s1.vmap 战斗模式 vs 冒险模式

- **现象**: s1.vmap 在战斗 Gym 中加载 crash

- **原因**: 战斗 Gym 期望 battle map，s1 是冒险地图



---



### 84. vmap players 数组格式 → 引擎加载即 core dump

- **现象**: T01 课程地图 NEW_GAME start 后 core dump; test_vcmi_load.py 声称 "31/31 VCMI 格式验证通过"

- **根因**: gen_v3.py 把 header players 改成数组 `[{"canComputerPlay":True,"canHumanPlay":True,"mainHero":None}]`; VCMI 1.7.4 vmap 需要 dict 格式 `{"red":{...},"blue":{...}}` (含 heroes/mainHero/team)

- **修复**: 从 train_v1.vmap 复制 header, 保留 dict players

- **教训**: test_vcmi_load.py 只查 zip 内 3 文件存在 + JSON 可解析 = **假验证**, 从未用引擎加载; 31/31 "通过" 全部是假象。验证必须 ep_runner 实跑



### 85. vmap hero 标识符 core:inham 不存在

- **现象**: "Couldn't resolve hero identifier core:inham"

- **根因**: train_v1.vmap 自身 blue hero options.type=core:inham (生成时代笔误), VCMI 英雄库无此名

- **修复**: header players.heroes 与 objects options.type/portrait 统一为 core:edric (red) / core:iona (blue)

- **推论**: train_v1.vmap 从未真正加载成功过 (inham + wt/ro 地形双问题), 历史 "VMAP 兼容性待解决, 暂用 H3M" 的真相



### 86. vmap terrain shortIdentifier: rock=rc 非 ro; 无 road 类型

- **VCMI terrains.json shortIdentifier 全表**: dirt=dt sand=sa grass=gr snow=sn swamp=sw rough=rg subterra=sb lava=lv water=wt rock=**rc**

- rd00_ (道路) 不存在 → terrain id -1; ro00_ 无效 (rock 是 rc)

- **修**: 障碍只用 wt00_/rc00_ (实际只有 gr24_ 能加载, 见 #87)



### 87. vmap 非草地地形 (wt00_/rc00_) 加载 segfault (⚠️ 待查)

- **现象**: 全草地 T01 能跑; 含 wt00_ 或 rc00_ 的任何 vmap segfault (terrain 解析通过、view 0 合法)

- **当前对策**: 课程地图全草地 (gr24_), 难度靠对象布局 (资源/野怪/城镇) 提供

- **待查**: gdb 抓栈 (疑 terrain tiles 动画加载或 view pattern 初始化)



### 88. vmap town mask 5x3 越界 → segfault (根因链核心)

- **town template mask** ["VVVVV","VVAVV","VVVVV"], anchor 居中 → 覆盖 x∈[tx-2,tx+2], y∈[ty-1,ty+1]

- **town_x<2 左越界必崩** (右界 w-2 容错不崩); hero 站 town mask 内不一定崩 (T01 边缘 V 上能跑)

- **修复**: town_x∈[2,w-3], town_y∈[1,h-2]; hero 避开 town mask (|dx|<=2 且 |dy|<=1); 生成后校验所有对象 1<=x<=w-2 且 1<=y<=h-2

- **二分定位法**: 从能跑的 T01 逐步叠加 T02 特征, 5 变体 (full/hero/town/mine/res) 一次脚本跑完 — t2d_town 即崩, 秒定位



### 89. vmap resource 对象 options 需 amount

- 早期模板 options={} → 加载崩; train_v1 参考写法 options={"amount":8}

- resource subtype 用资源类名 core:gold/wood/crystal, 非 core:resourceGold



### 91. vmap 非草地地形崩溃是 VCMI 1.7.x 共有 bug (1.7.5 也崩), 升级无用

- **验证 (2026-08-23)**: Windows 官方 VCMI 1.7.5 (VCMI_client.exe --headless --testmap) 加载含 wt00_ 的 vmap 同样 "Disaster happened" 崩溃 — 与 WSL 1.7.4 segfault 同路径 (client embedded server 端 loadMap)

- 本地与 upstream develop 的 MapFormatJson.cpp/TerrainTile.h/TerrainHandler 零差异 → 非 fork 改动引入

- mapeditor (editor 模式) 能加载到 "Making object rects" 不崩 → editor 路径更宽容

- **结论**: 升级 WSL 到 1.7.5 不能解决; 全草地绕开是唯一可行方案 (已采用)

- 1.7.5 验证方法: Windows VCMI_client --headless --testmap <map> (官方 release 支持; 用户数据在 Documents/My Games/vcmi/, 含完整 H3 数据)



### 92. T05/T06 旧 dict 版也含崩溃地形 (rd/ro/wt/sa) + T05 town 越界

- T05/T06 从 train_v1 复制 (gen_level4/5.py), terrain 含 rd00_ (道路, 不存在)/ro00_ (应为 rc)/wt00_ (崩溃)/sa00_ → 加载必崩

- T05 town_0=(1,1) 5x3 mask 越界 (x∈[-1,3])

- **修复**: 统一脚本 — terrain 全 gr24_ + town clamp [2,w-3]x[1,h-2] + hero 避开 town mask + 界内校验

- **教训**: "dict players 格式" ≠ "地图可跑"; 任何从旧模板复制的 vmap 都要重验 terrain 代码和对象坐标

### 94. "vmap 非草地 segfault" 是误判 — 真因是 NK2 守卫战斗断言 (AAI.cpp:435)

- 曾结论: wt00_/rc00_ vmap 加载必崩 → 转 H3M 路线 (浪费大量工作)

- 真因: `AAI.cpp:435 ASSERT(queryID != -1, "QueryID is -1, but we are ATTACKER")` — 守卫战斗无 CBattleDialogQuery (onlyOnePlayerHuman=false) → queryID=-1 → MMAI battleEnd 断言崩

- 触发条件: ep_runner 默认 blue_adventure_ai=Nullkiller2; 训练配置 (--blue_ai MMAI_RANDOM --blue_adventure_ai MMAI) 永不触发

- 证据: T01 全草地 + NK2 3/3 崩; + MMAI 3/3 不崩; 34水+8岩 + MMAI 3/3 不崩

- 教训: 验证地图/环境必须用训练同款配置; 崩溃先看断言/栈顶再归因格式 (grep Assertion failed)



### 108. vmap aggression 字段无效 → 守卫恒 FLEE (2026-08-27)
- 现象: vmap monster options 写 aggression:"guard", 守卫从不战斗 (恒消失无 battle)
- 根因: VCMI 的字段名是 character (CGCreature.cpp serializeEnum), aggression 无效被忽略 → 性格默认 → agression=0 → charisma>0 → takenAction 恒 FLEE
- 处理: character:"savage" (agression=10 恒 FIGHT) + neverFlees:true
- 教训: vmap 字段名以 C++ serializeJsonOptions 为准; 08-26"守卫清除检测"实为守卫逃跑误判 (假任务)

### 109. 运行时地图目录 ≠ 项目 Maps/training (2026-08-27)
- 现象: patch 项目地图后运行时行为不变 (trace 守卫还是旧兵种)
- 根因: VCMI 运行时从 vcmi-native/data/Maps 读图 (rel/bin/data → vcmi-native/data)
- 处理: 3 副本同步 (项目 Maps/training + vcmi-native/data/Maps + vcmi/data/Maps)
- 教训: patch 地图后先查运行时目录; 判定法 = trace 日志 "Hero visits X" 的兵种名

### 119. 引擎实际加载地图 = cwd/data/Maps 部署副本 (2026-08-29)
- 现象: 改 maps/training 源图后训练行为不变; 排查守卫数时源图与运行时不一致疑云
- 事实: ep_runner 子进程 cwd = `vcmi-native/rel/bin` → 引擎按相对路径 `data/Maps` 加载 = `rel/bin/data/Maps` 部署副本; 验证法: `ls -l /proc/<runner_pid>/cwd` + 比对副本 objects.json
- 本次数值核对: 部署副本与 maps/training 六图 T04 完全一致 (虚惊)
- 教训: 改图必须同步部署副本 (项目 maps/training + rel/bin/data/Maps, 可能还有 vcmi/data/Maps 共 3 副本); 排查地图问题先查 /proc/pid/cwd 定位真实加载源

