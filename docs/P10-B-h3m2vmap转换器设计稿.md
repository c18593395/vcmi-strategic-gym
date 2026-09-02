# P10-B 设计稿 — h3m2vmap 转换器（引擎内路径 + 改写规则）

> 日期: 2026-09-01
> 定位: P10 B 步设计文档。只做接口梳理 + 规则设计，**本稿不写代码、不动构建树**。
> 源码依据: WSL `/home/administrator/vcmi-native` (1.7.4 fork, 已逐行核实, 行号以此树为准)
> 前置: A 步实测结论见 `docs/当前任务清单.md` P10 段 (08-29)
> 铁律约束: B 步编译须**独立构建目录**，禁覆盖 `rel/` 下任何 .so；不重编 libvcmi.so（本方案不修改 lib 源码，只新增 tool，天然满足）

---

## 1. 目标

把官方 H3M 图（首选 `Knee Deep in the Dead.h3m`, 36×36 ROE 2 玩家, 已在 `vcmi-native/data/Maps/maps-list.md` #74）经引擎自身加载/序列化链路转成可训练的 .vmap，并按训练约束做内存改写（删城/削守卫/白名单过滤/玩家重配）。

核心思路：**复用引擎 loader/saver，改写发生在内存 CMap 对象上**，而非手写 JSON 文本——规避踩坑 #84（假验证）、#85（标识符笔误）、#88（mask 越界）这类手拼 JSON 的整类问题。

## 2. 引擎内路径梳理（已核实）

### 2.1 全链路总览

```
Knee Deep in the Dead.h3m (gzip 包裹的二进制)
   │
   ▼  CMapService::loadMap(ResourcePath, cb)          CMapService.cpp:36
   │    └─ getMapLoader(stream, ...)                  CMapService.cpp:141
   │         ├─ zip magic (0x04034b50 等) → CMapLoaderJson   ← vmap 走这条
   │         └─ gzip magic / EMapFormat{ROE,AB,SOD,WOG,CHR,HOTA} → CMapLoaderH3M
   ▼  CMapLoaderH3M::init()                           MapFormatH3M.cpp:85
   │    ├─ LIBRARY->mapFormat->isSupported(version)   MapFormatH3M.cpp:198
   │    └─ MapIdentifiersH3M identifierMapper = LIBRARY->mapFormat->getMapping(version)  :201
   │         （H3M 索引 → 现代 jsonKey 标识符的全量映射表，转换正确性的基石）
   ▼  std::unique_ptr<CMap>  （内存中的规范地图对象）
   │
   ▼  ★ 改写层（本设计 §4：直接改 CMap / CGObjectInstance / CMapHeader）
   │
   ▼  CMapService::saveMap(map, fullPath.vmap)        CMapService.cpp:92
   │    └─ CMapSaverJson saver(&CMemoryBuffer); saver.saveMap(map);  :96-97
   ▼  CMapSaverJson::saveMap                          MapFormatJson.cpp:1395
        ├─ writeHeader()        → header.json   :1404
        ├─ writeTerrain()       → terrain_0.json :1492
        └─ writeObjects()       → objects.json  :1503
        （fixStringsTextIDInJson 收尾 + CZipSaver 打 zip → .vmap）
```

### 2.2 读侧接口（CMapService.h / CMapService.cpp）

| 接口 | 签名要点 | 说明 |
|------|---------|------|
| `IMapService::loadMap` | `(const ResourcePath&, IGameInfoCallback* cb)` | 文件路径入口；cb 传 nullptr 的可行性见 §5 待验证 V1 |
| `CMapService::loadMap` | `(const uint8_t* buffer, int size, name, modName, encoding, cb)` | 内存 buffer 入口，可绕开 ResourcePath 文件系统注册，**推荐工具主用** |
| `getMapLoader` | static | 按流头 4 字节自动分派 zip→Json / h3m→H3M loader；工具无需自己判格式 |
| `CMapLoaderH3M` 构造 | `(mapName, modName, encodingName, CInputStream*)` | encoding 建议 "CP1252"（西文官方图） |

关键依赖：`CMapLoaderH3M::init` 全程使用 `LIBRARY`（mapFormat/heroh/arth/objtypeh/skillh/spellh…），因此工具进程**必须完成 GameLibrary 两段初始化**（见 §3.2），否则 H3M 标识符映射直接不可用。

### 2.3 写侧接口（MapFormatJson.h / MapFormatJson.cpp）

`CMapSaverJson`（MapFormatJson.h:215 起）只依赖一个 `CInputOutputStream*`（工具里用 `CMemoryBuffer` 即可，参照 CMapService.cpp:95），产出即标准 vmap zip：

| 写入步骤 | 产出 | 要点 |
|---------|------|------|
| `writeHeader()` | header.json | `versionMajor=3 / versionMinor=0`（MapFormatJson.cpp:242-243，与 1.7.4 读侧兼容）；mods 清单来自 `mapHeader->mods`（H3M 图为空/仅 core，天然满足 ML 环境加载）；mapLevels（width/height/layer）；players（dict 格式——正是踩坑 #84 纠正过的形状，由 `serializeHeader/serializePlayerInfo` 生成，手拼错误不可能再犯）；triggeredEvents（胜负条件，§4-R6）；teams |
| `writeTerrain()` | terrain_0.json (per level) | 每格编码为字符串：`<terrain shortIdentifier><terView><flip>` + 可选 road/river 段（`writeTerrainTile`, :1453）。shortIdentifier 走 terrains.json 全表（gr/dt/sa/sn/sw/rg/sb/lv/wt/**rc**——踩坑 #86 的 rc 陷阱由引擎编码自动规避） |
| `writeObjects()` | objects.json | 逐对象 `obj->serializeJson(handler)` 产出 `{type:"core:xxx", subtype:"core:yyy", x,y,z, instanceName, options}`（:1503-1546）；object 间引用以 `instanceName` 编解码（MapObjectResolver, MapFormatJson.cpp:47-85）；grail 单独追加节点；空 options 自动清理 |
| `writeTranslations()` | translations 段 | mapHeader->translations，H3M 文本经 `fixStringsTextIDInJson` 归一 |

**结论（写侧）**：CMap 改写后调 `CMapService::saveMap` 即得合法 vmap，三文件内部一致性（instanceName 引用、players dict、terrain 编码）全部由引擎保证。

## 3. 转换器工具设计（h3m2vmap）

### 3.1 形态与构建

- 形态：独立 CLI 可执行 `h3m2vmap`，源码建议放 `vcmi-native/tools/h3m2vmap/main.cpp`（与 Windows 树 `tools/` 无关，不污染双树同步面）
- 构建：**新独立构建目录** `vcmi-native/build-h3m2vmap/`，CMake 新增 target 只链 `vcmi` lib（不碰 AI/ML/Server 模块）；产出放工具自身目录，**禁入 rel/**
- 环境要求：与训练同款 1.7.4 WSL 工具链；无需 onnxruntime（不链 MMAI）

### 3.2 main() 初始化序列（参照 serverapp/EntryPoint.cpp:72-92，已核实）

```cpp
int main(int argc, char** argv)
{
    // 1. CLI: <in.h3m> <out.vmap> [规则参数: 守卫系数/白名单档/删城模式...]
    // 2. 日志: CConsoleHandler + CBasicLogConfigurator
    // 3. LIBRARY = new GameLibrary;                    // EntryPoint.cpp:82 同款
    //    LIBRARY->initializeFilesystem(false);         // 数据目录 = cwd/data (工具 cwd 指向含 data/Maps 的目录)
    //    LIBRARY->initializeLibrary();                 // handlers 全量就位, H3M identifierMapper 可用
    // 4. 读: CMapService::loadMap(buffer版) → CMap
    // 5. 改: applyRewriteRules(map, cfg)               // §4, 唯一自研代码
    // 6. 写: CMapService::saveMap(map, out.vmap)
    // 7. delete LIBRARY;
}
```

注意：工具运行 cwd 须含引擎数据（mods/Maps/config），部署上直接用 `vcmi-native/rel/bin` 同款数据布局的副本目录，或 cwd 指向 `vcmi-native/`（其 data/Maps 已含全部官方 h3m，maps-list.md #74 即目标图）。

### 3.3 CLI 约定（草案）

```
h3m2vmap --in "<name>.h3m" --out out.vmap
         [--guard-scale 0.3]          # 守卫系数 = 天然课程轴 (A 步真瓶颈结论)
         [--town-mode delete|neutral] # §4-R1
         [--object-whitelist full|training45]
         [--player red=human,blue=ai]
         [--report report.json]       # 转换审计: 删了什么/改了什么/计数对账
```

## 4. 改写规则设计（loadMap 之后、saveMap 之前，全部作用于内存 CMap）

> 设计原则：每条规则幂等、可开关、出审计记录；删改对象只动 `map->objects` / 字段，不重排 ObjectInstanceID（引用完整性由 instanceName 体系承接，但删除对象仍需同步清理引用方，见 R1 风险）。

### R1 城镇处理（选图约束：城需删/封）

| 方案 | 做法 | 风险 |
|------|------|------|
| A. 删除 | 从 `map->objects` 移除 CGTownInstance；同步清理：其他对象对它的引用（如 events/mine 关联弱）、`map->instanceNames`、玩家 `PlayerInfo` 城计数 | 依赖遍历彻底；漏清引用 → 加载期 dangling |
| B. 封中立 | 保留对象，owner→NEUTRAL、清空 builtBuildings、garrison 清空 | 保守，对象数不减；但 T04 训练语义"占城"仍可达成 |
| **建议** | 首选 B（风险最小、可逆），A 作 fallback；`--town-mode` 二选一 | — |

### R2 玩家/英雄重配（→ 1v1 训练形状）

- `mapHeader->players` 重写为 red(human) / blue(computer) 两家 dict，其余清空；`howManyTeams=2`
- 现有英雄按归属重指派；不足则注入 (踩坑 #85 教训：类型必须为真实存在的 `core:edric / core:iona` 或 ML mod `ML:hero_X`)
- 英雄初始部队注入：直接改 CGHeroInstance 的 army slots（绕开 H3M "hero placeholder give units 不完整实现" 警告路径, MapFormatH3M.cpp:2275）
- allowedHeroes 重置为 `LIBRARY->heroh->getDefaultAllowed()`

### R3 守卫削减（课程轴）

- 遍历 CGCreature 对象：amount 乘 `--guard-scale`（向下取整, 最小 1）；可选按与出生点曼哈顿距离分档（近弱远强 = 渐进课程）
- 性格字段固定 `character: "savage"` + `neverFlees`（踩坑 #108：C++ 字段名是 character, aggression 无效）
- 削减后写审计：每守卫 before/after

### R4 物体过滤（白名单）

- 白名单来源：A 步实测 45 类（与 C++ `fill_target_list`/`fill_terrain_grid` 的识别集对齐, strategic_state.cpp:197）
- 不在白名单的 Obj 类型整类删除（含其associated events）；删除走与 R1-A 相同的引用清理通道
- 审计输出各类删除计数，与源图对象总数对账

### R5 地形处理

- 水域规避（A 步结论已定）：water/rock 边界格 → 就近陆地地形填充（或直接剔除沿水对象）
- 历史包袱澄清：踩坑 #94 已证 "非草地 vmap 必崩" 是误判（真因 NK2 断言，训练配置不触发）→ **本工具不强制全草地**；保留 `--terrain-flatten` 开关作为回归兜底
- 道路/河流：引擎 writeTerrainTile 自动带 road/river 段，无需干预；road 有 speed bonus 影响课程，可加 `--strip-roads` 开关（默认关）

### R6 胜负条件改写

- H3M 原生 triggeredEvents（特殊胜利条件）**整体清除**，重写为 T04 训练语义：
  - victory = 消灭对方全部英雄 + 攻占对方城镇（standard events, 与 T04 判定一致）
  - loss = 己方英雄全灭且无城
- 落点：`mapHeader->triggeredEvents`（writeHeader→writeTriggeredEvents 序列化），内存改后引擎自动成 JSON

### R7 文本/翻译

- 地图名/描述改写为训练 ID（`map.<name>.` 前缀规则由 fixStringsTextIDInJson 处理）；原 H3M 文本保留为 translations，不影响训练

## 5. 风险与待验证点（B 步开工前必答）

| # | 事项 | 状态/对策 |
|---|------|----------|
| V1 | `loadMap(name, cb)` 的 cb=nullptr 是否安全（CMapLoaderH3M::loadMap(cb) 对 cb 的使用面） | 开工首日实测定论；若不安全 → 走 buffer 版 + 构造最小 callback，或仿 mapeditor 传桩 |
| V2 | HOTA 版本图 | 首选 ROE 图（Knee Deep），不踩 `mapFormat->isSupported` 的 HotA 1.8 分支（MapFormatH3M.cpp:187）；工具对不支持的 format 直接报错拒绝 |
| V3 | 删除对象的引用清理完整性（R1-A/R4） | 方案 B 优先规避；审计 + ep_runner 实跑验证 |
| V4 | 双源码树漂移（风险登记 R5） | 本工具全部在 WSL vcmi-native 侧；Windows vcmi/ 只读参照 |
| V5 | **验证纪律**：vmap 合法性 = ep_runner 训练同款配置实跑（#84 假验证 / #94 配置同款教训），任何 JSON 层"校验通过"不作数 | D 步验证链承接：静态结构检查 → 引擎 testmap → ep_runner 冒烟 → 短训 |
| V6 | 改写与 obs 冻结约束（3464）不冲突 | 转换只改地图内容，不动 obs/动作空间；地形走 terrain_grid.bin 旁路 |

## 6. 实施序（B 步内部）

| 子步 | 内容 | 出口判据 |
|------|------|---------|
| B1 | 独立构建目录 + 空 tool 骨架（GameLibrary 两段初始化跑通） | `h3m2vmap --version` 输出正常, 不触 rel/ |
| B2 | 最小转换：loadMap→saveMap 直通（零改写） | 产出 vmap 能被引擎 loadMap 读回且 ep_runner 冒烟加载成功 |
| B3 | 改写规则 R1-R7 落地 + report 审计 | 每条规则开关独立生效；对账无差额 |
| B4 | Knee Deep 全流程产出 → 交 C/D 步（改写规则定稿 + 验证链） | vmap 入 D 步验证清单 |

### B1 完成记录（2026-09-01）

- **实现与设计稿偏差（已采纳更优路径）**：未走"根 CMakeLists 加 target + 全树重建"方案，改为**独立迷你 CMake 工程**（`tools/h3m2vmap/CMakeLists.txt`）只读链接 `rel/bin/libvcmi.so`（BUILD_RPATH/INSTALL_RPATH 指向 rel/bin）。理由：build/ 空壳、ccache 未装，全树重建 = 无缓存重编整个 libvcmi（训练在跑还要压并行度），而 rel 缓存即现成 ABI 兼容产物；只读链接零 lib 重编、零 rel 写入。根 CMakeLists 零改动。
- 源码位置：WSL `/home/administrator/vcmi-native/tools/h3m2vmap/{main.cpp,CMakeLists.txt}`，Windows 参照副本 `tools/h3m2vmap/`（改代码先改 Windows 副本再 cp 同步，双树纪律同 libmlclient）
- 构建：`cmake -S .../tools/h3m2vmap -B .../tools/h3m2vmap/build && cmake --build ... -j2`（独立 build 目录, 单编译单元秒级）
- 验收结果：`--version` 输出 `h3m2vmap (P10-B converter skeleton, B1) / engine: VCMI 1.8.0.30f62b8...`；ldd 全解析（libvcmi→rel/bin 只读, 无 not found）；`--selftest`（cwd=rel/bin）GameLibrary 两段初始化全通（config/Mods/schema 加载 → "GameLibrary init OK" → 干净退出）；`find rel -newermt '-15min'` 零命中 = rel/ 零写入
- 踩坑记录：独立工具 include 环境与 StdInc 系不同——`VCMI_LIB_NAMESPACE_*` 宏定义在**根 `Global.h`**，main.cpp 必须先 `#include "Global.h"` 再引 lib 头，否则 GameLibrary/GameConstants/LIBRARY 全部未声明
- 版本备注：fork 版本串实际为 **VCMI 1.8.0**（此前文档按 1.7.4 记述），B2 接口行为以实源码为准（本设计稿所有行号引用均已对 WSL 树核实）
- 待验证 V1（cb=nullptr）顺带降险：selftest 已证 GameLibrary 初始化独立可用，B2 首日即可直接实测 loadMap 路径

## 8. 旁路工具 — vmap2h3m 反向转换（2026-09-01 完成）

引擎**无 H3M 写出器**（只有 vmap saveMap），反向转换自建：`py/vmap2h3m.py`（Python, SOD 格式），读 vmap zip → 写官方 H3M 二进制。范围 = 训练图特征集 5 类对象（hero/town/mine/resource/monster）+ 全地形。

### 关键实现路线

- **格式知识源** = `scripts/h3m_tool.py` 的 reader 镜像（其逆向实测字节布局 = 写回依据）+ 引擎 `CMapLoaderH3M.cpp` 交叉校验
- **模板(def)来源** = donor 官方图库：按 (id,subid) 匹配后**原样复制 raw 条目**（含 anim/blockMask/visitMask），文件内对象 id 一致性天然成立，绕开 H3M 原始编号考证；缺条目时同 id 任意条目 patch subid 字节（外观可能错位但引擎可读）。默认扫 data/Maps 官方图（约 1-2 分钟，可后续加 pickle 缓存）
- **映射数据源** = 引擎 config json 的 index 字段（`Mods/vcmi/Content/config/creatures/*.json`、`heroes/*.json` 的 shortIdentifier→index），不硬编码大表。注意 VCMI creature index 含升级兵（castle: 0 pikeman 1 halberdier 2 archer 3 marksman 4 griffin 5 royal 6 swordsman…），与官方 H3 编号一致
- vmap 对象 hero 的真英雄 = `options.type`（subtype 是职业名如 core:alchemist）；owner red=0 blue=1 中立=255

### 踩坑实录（写回字节错位三连，均由 h3m_tool strict 对账定位）

| # | 错位 | 事实 |
|---|------|------|
| 1 | main_town 段 | AB+ 格式 hasMainTown 后有 **2 个额外字节**（h3m_tool 实测逆向），漏写则 players 段后全错位 |
| 2 | hero artifact 槽 | **SOD = 19 槽**（`artifactSlotsCount=18 if ver in (ROE,AB) else 19`），写 18 差 2B |
| 3 | resource 段 | `readMessageAndGuards` 的 skip4 在 msg=1 分支**内部**，msg=0 时仅 1B + u32 amount + skip4 = 9B |

### 验证链（两层）

1. 字节级：`h3m_tool.parse_objects(tolerant=False)` strict 读回对账——T04/T03 双图 **skipped=0, strict OK**
2. 引擎级：h3m2vmap 新增 `--check-h3m`（`CMapService::loadMap(buffer版)` 真实读回）——T04(36x36,9obj)/T03(30x30,10obj) 转换产物 + 官方图 For Sale(514obj) 对照 **全部 ENGINE LOAD OK**

### 引擎 loadMap 调用两事实（设计稿 §5 V1 已实测定论）

- **V1 结论：cb=nullptr 可用**（对象构造仅存指针，加载全程未解引用）
- modName 不可传 ""——readLocalizedString → `getModLanguage("")` → ModsStorage 抛异常 core dump；必须传引擎内建合法 modContext **"map"**（`CModHandler::getModLanguage` 特判）

## 7. 与现有文档的关系

- A 步实测结论 / 实施序：`docs/当前任务清单.md` P10 段
- vmap 格式踩坑全集：`docs/WSL踩坑点-地图-vmap生成.md` #84/#85/#86/#88/#94/#108/#109/#119
- 引擎对象系统/回调面背景：`docs/源码分析地图.md`
- 双树纪律：`docs/WSL踩坑点.md` 风险登记 R5 + 项目规则"事实核查原则"
