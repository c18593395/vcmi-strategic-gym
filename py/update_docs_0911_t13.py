#!/usr/bin/env python3
"""Update 总任务.md (add T13) + 当前任务清单.md (add T13 subtasks)"""
import pathlib

base = pathlib.Path('D:/Bigdata/hero3_fresh/docs')

# ============================================================
# 1. 总任务.md — add T13 to progress table + big-item section
# ============================================================
zt_path = base / '总任务.md'
zt = zt_path.read_text('utf-8')

# 1a. Add T13 row to progress table (after T12 row)
old_table_end = "| T12 | v15 架构迁移 (GNN + py::dict) | ⬜ Phase G 前 |"
new_table_end = old_table_end + "\n| T13 | 外挂 AI 架构 (VCMI 网络协议) | ⬜ 调研完成 / 待实施 |"
zt = zt.replace(old_table_end, new_table_end)

# 1b. Add T13 big-item section (before the milestones section)
old_milestones_header = "---\n\n## 重要里程碑时间线"
new_t13_section = """### T13 外挂 AI 架构（VCMI 网络协议外挂）
目标：实现外部 AI 客户端，通过 VCMI 官方 TCP 网络协议接入游戏，不改 VCMI 一行代码。终极目标：人 vs 人 vs 模型联网（VCMI Windows 引擎内部接口）。
架构：外挂 AI 实现 VCMI 客户端协议（`lib/network/` + `lib/networkPacks/`），与 vcmiclient 同地位接入 `NetworkServer`。Server 不区分人类 vs AI。
前置调研 (09-11)：✅ 网络协议可行 / ✅ CPackForServer 覆盖所有战略层操作 / ✅ battle-ml 死分支排除 / ✅ Issue #5586 无人实施。
子任务：T13.1 序列化逆向 / T13.2 核心包验证 / T13.3 客户端连接层 / T13.4 战略包发送器 / T13.5 客户端包解析器 / T13.6 Query 回复管理器 / T13.7 战斗包对接 / T13.8 模型接入层 / T13.9 端到端验证 / T13.10 多人对战验证。
状态：调研完成；实施 ⬜（远期，T5.8 成熟后启动）。

---

## 重要里程碑时间线"""
zt = zt.replace(old_milestones_header, new_t13_section)

# 1c. Add milestone entry (already done in previous commit, but let's verify)
old_milestone = "- 2026-09-11：VCMI 网络协议深度调研 — 确认外挂 AI 架构可行"
new_milestone = "- 2026-09-11：VCMI 网络协议深度调研 — 确认外挂 AI 架构可行 (CPackForServer 二进制协议, server 不区分人 vs AI)；battle-ml 分支已死 (2022 未合并)；Issue #5586 纯提案无人实施；EmptyAI 走 CCallback 非网络；T13 立项 (外挂 AI 架构, 远期)。详见知识库「VCMI 网络协议与外挂 AI 架构调研」。"
zt = zt.replace(old_milestone, new_milestone)

# 1d. Add T13 reference to key principles
old_principle_8 = "8. **不追官方更新**：锁战斗层版本；NK2 寻路加速 (40% 吞吐) 是红利，训练稳定后择机 merge（T6.2 关联）。"
new_principle_8 = "8. **不追官方更新**：锁战斗层版本；NK2 寻路加速 (40% 吞吐) 是红利，训练稳定后择机 merge（T6.2 关联）。"
# 1e. Add T13 reference to asset index
old_asset_end = "| 健康监控 | `py/train_health_monitor.ps1` + `monitor_alerts.log` |"
new_asset_end = old_asset_end + "\n| 外挂 AI 调研 | `docs/WSL知识库.md` 「VCMI 网络协议与外挂 AI 架构调研」章 |"
zt = zt.replace(old_asset_end, new_asset_end)

zt_path.write_text(zt, 'utf-8')
print(f"[OK] 总任务 updated: {zt_path}")

# ============================================================
# 2. 当前任务清单.md — add T13 subtasks to 待办任务总表
# ============================================================
ct_path = base / '当前任务清单.md'
ct = ct_path.read_text('utf-8')

# 2a. Update the header note about 09-11 research
old_note = "> 📖 **09-11 研究增量**: VCMI 网络协议调研完成 — 外挂 AI 架构可行 (详见知识库新章)，不影响当前训练。踩坑 #175-#177 新增 (网络协议非 JSON / EmptyAI 走 CCallback / battle-ml 死分支)。"
new_note = "> 📖 **09-11 研究增量**: VCMI 网络协议调研完成 → **T13 外挂 AI 架构立项** (远期, 见当前任务清单 P 区)。踩坑 #175-#177 新增 (网络协议非 JSON / EmptyAI 走 CCallback / battle-ml 死分支)。"
ct = ct.replace(old_note, new_note)

# 2b. Add T13 to the 远期 / 阻塞集 section (at the bottom)
old_far_end = "- 引擎侧 standardDefeat 判负根修 — 独立课题 (T7.4 关联, 死亡局 game_over 恒 0 的引擎层根因)"
new_far_entry = old_far_end + "\n- **T13 外挂 AI 架构** — 网络协议调研完成 (09-11), 待 T5.8 成熟后启动。子任务 10 项已分解 (T13.1-T13.10), 详见下方 T13 专区"

ct = ct.replace(old_far_end, new_far_entry)

# 2c. Add T13 dedicated section before the end of file
# Find a good insertion point — after 远期/阻塞集 section
old_end = ct.rstrip('\n')
t13_tasks = """

---

## T13 外挂 AI 架构任务分解（远期，T5.8 成熟后启动）

> 定位：网络协议调研完成 (09-11)，架构可行但非当前窗口。依赖 T5.8 训练成熟 (战略模型可部署) + 序列化逆向完成。不碰运行中 v5 训练。
> 目标：实现外部 AI 客户端，通过 VCMI 官方 TCP 协议接入，不改 VCMI 代码。最终实现人 vs 人 vs 模型联网。

### T13.1 序列化逆向（基础瓶颈，阻塞全部后续）
- **任务**：读 `lib/serializer/Serializeable.h` + `NetworkHandler.cpp`，推导所有基本类型的字节布局
- **关键类型**：`int3`(3 int32) / `ObjectInstanceID`(int32?) / `std::string`(变长) / `std::vector<T>`(变长) / `std::optional<T>` / `std::set<int3>` / `std::map<K,V>` / `std::shared_ptr<T>`
- **输出**：`docs/序列化协议规格.md` — 每个类型的字节格式、长度前缀编码、对齐规则
- **验证手段**：用 VCMI server 启动一局，抓 TCP 包对比推导结果
- **前置**：无（纯阅读源码）
- **预估**：2-3 天集中分析

### T13.2 核心包类型验证
- **任务**：验证 `MoveHero`、`EndTurn`、`QueryReply` 的序列化正确性
- **方法**：在 WSL2 起 VCMI server + 两个 headless client（一个空操作，一个发 EndTurn），抓包对比
- **输出**：确认字节布局与 T13.1 推导一致
- **前置**：T13.1
- **预估**：0.5 天

### T13.3 客户端连接层
- **任务**：实现 VCMI 客户端 TCP 连接协议
- **关键源码**：`lib/network/NetworkConnection.cpp`（TCP 握手、版本协商、游戏加入流程）
- **实现语言**：C++（复用 VCMI 头文件）或 Python（需完整逆向）
- **路径**：路径 B（C++ headless client）优先 — 可直接 `#include` VCMI 头文件
- **前置**：T13.1
- **预估**：2-3 天

### T13.4 战略包发送器
- **任务**：实现 `CPackForServer` 子类的序列化与发送
- **优先级包**：`MoveHero` → `EndTurn` → `QueryReply` → `RecruitCreatures` → `BuildStructure` → `UpgradeCreature` → `HireHero` → `SetFormation` → `SetTactics` → `CastAdvSpell` → `DismissHero` → `SpellResearch` → `BulkMoveArmy` → `TradeOnMarketplace` → `ExchangeArtifacts` → `BuyArtifact` → `BuildBoat` → `SaveGame` → `MakeAction`
- **输出**：`vcml/net_client.cpp` — 封装发包接口
- **前置**：T13.1 + T13.3
- **预估**：3-5 天（包多但模式统一）

### T13.5 客户端包解析器
- **任务**：实现 `CPackForClient` 子类的反序列化与处理
- **关键包**：`NewTurn` → `PlayerStartsTurn`(Query) → `TryMoveHero` → `PackageApplied` → `PackageReceived` → `HeroLevelUp`(Query) → `CommanderLevelUp`(Query) → `BlockingDialog`(Query) → `GarrisonDialog`(Query) → `MapObjectSelectDialog`(Query) → `TeleportDialog`(Query) → `ExchangeDialog`(Query) → `OpenWindow`(Query) → `InfoWindow` → `SystemMessage` → `TurnTimeUpdate` → `FoWChange` → `EntitiesChanged` → `SetResources` → `SetMovePoints` → `SetMana` → `NewObject` → `RemoveObject` → `ChangeObjPos` → `PlayerEndsTurn` → `PlayerEndsGame`
- **输出**：`vcml/net_client.cpp` 包处理回调接口
- **前置**：T13.1 + T13.3
- **预估**：3-5 天

### T13.6 Query 回复管理器
- **任务**：自动回复所有 Query 类型的包，防止 server 卡死
- **规则**：
  - `PlayerStartsTurn` → `QueryReply(qid, 0)` （"我准备好了"）
  - `HeroLevelUp` → `QueryReply(qid, skill_choice)` （选技能，可自动化）
  - `CommanderLevelUp` → `QueryReply(qid, skill_choice)`
  - `BlockingDialog` → `QueryReply(qid, 1)` （默认接受）
  - `GarrisonDialog` → `QueryReply(qid, 1)` （默认接受）
  - `MapObjectSelectDialog` → `QueryReply(qid, 0)` （默认取消）
  - `TeleportDialog` → `QueryReply(qid, 0)` （默认取消）
  - `ExchangeDialog` → `QueryReply(qid, 0)` （默认取消）
  - `OpenWindow` → `QueryReply(qid, 0)` （默认关闭）
- **输出**：`vcml/net_client.cpp` Query 自动回复链
- **前置**：T13.4 + T13.5
- **预估**：1 天

### T13.7 战斗包对接
- **任务**：实现 `MakeAction(BattleAction, battleID)` 的序列化与发送
- **关键**：`BattleAction` 结构与 MMAI 内部同构（`lib/battle/BattleAction.h`）
- **路径**：
  - 方案 A：战斗层也用外挂模型（需 `CBattleGameInterface` 网络版 — 需逆向战斗 Query 流）
  - 方案 B：战斗层用 VCMI 内置 AI（外挂只控制战略层，战斗自动走 BattleAI）
- **推荐**：方案 B 优先（少一半工作量），方案 A 后续迭代
- **前置**：T13.4 + T13.5 + T13.6
- **预估**：方案 B 0.5 天 / 方案 A 3-5 天

### T13.8 模型接入层
- **任务**：将训练好的模型（ONNX / PPO checkpoint）接入外挂客户端
- **数据流**：`CPackForClient` 状态 → obs 构建 (3464 维) → 模型推理 → action (0-24) → `CPackForServer` 包
- **复用**：训练端 obs 构建器 (`strategic_env.py`) + 动作映射表 (`动作空间设计文档.md`)
- **挑战**：训练端 obs 来自 `strategic_state.cpp` 直读内存，外挂端 obs 需从 `CPackForClient` 包重建 — 两套 obs 构建器需对齐
- **输出**：`vcml/model_bridge.cpp` + `vcml/obs_from_packs.cpp`
- **前置**：T13.4 + T13.5 + T13.6 + T5.8 成熟
- **预估**：5-10 天（obs 对齐是最大工作量）

### T13.9 端到端验证
- **任务**：运行 1 外挂 AI 客户端 vs 1 Nullkiller2 AI 客户端，同一 VCMI server
- **验证**：
  - 外挂 AI 能完成完整回合（移动→探索→占矿→战斗→结束回合）
  - 无 server 卡死 / Query 未回复超时
  - 无 crash / 无数据竞争
  - 24 局稳定性
- **输出**：`py/test_net_client.py` — 自动化端到端测试
- **前置**：T13.3 + T13.4 + T13.5 + T13.6 + T13.7(B) + T13.8
- **预估**：1-2 天

### T13.10 多人对战验证（终极目标）
- **任务**：2+ 人类客户端 + 1 外挂 AI 客户端，同一 VCMI server
- **场景**：1v7 大厅配置，AI 接入任意玩家槽位
- **验证**：
  - AI 能正常加入/退出对局
  - AI 与人类混合游戏无异常
  - AI 回合与其他玩家回合交替正常
  - 跨机器部署（AI 客户端在远程机器）
- **输出**：验证报告 + 部署文档
- **前置**：T13.9
- **预估**：1 天

### T13 总览

| 阶段 | 子任务 | 预估 | 依赖 |
|------|--------|------|------|
| 协议基础 | T13.1 序列化逆向 | 2-3d | — |
| 协议基础 | T13.2 核心包验证 | 0.5d | T13.1 |
| 连接层 | T13.3 客户端连接 | 2-3d | T13.1 |
| 包处理 | T13.4 战略包发送 | 3-5d | T13.1+T13.3 |
| 包处理 | T13.5 客户端包解析 | 3-5d | T13.1+T13.3 |
| 包处理 | T13.6 Query 回复 | 1d | T13.4+T13.5 |
| 包处理 | T13.7 战斗包对接 | 0.5-5d | T13.4+T13.5+T13.6 |
| 模型接入 | T13.8 模型接入层 | 5-10d | T13.4+T13.5+T13.6+T5.8 |
| 验证 | T13.9 端到端验证 | 1-2d | T13.3-T13.8 |
| 验证 | T13.10 多人对战 | 1d | T13.9 |
| **总计** | | **20-37 天** | T5.8 成熟后启动 |

### T13 与现有轨道的关系

| 轨道 | 关系 |
|------|------|
| Track 1 (训练) | T13 不碰训练，但依赖 T5.8 模型成熟 |
| Track 2 (真实游戏对齐) | T13 是 Track 2 的替代路径 — 不修改游戏，通过网络协议外挂 |
| T8 战斗集成 | T13.7 可复用 T8 的战斗模型，也可用内置 BattleAI |
| T9 真实游戏对齐 | T13 与 T9 是两条独立落地路径（T9=修改游戏内存 / T13=网络协议外挂）|
| T10/T11 人机对战 | T13.10 直接实现终极目标 |
"""

ct = ct.rstrip('\n') + t13_tasks + '\n'
ct_path.write_text(ct, 'utf-8')
print(f"[OK] 当前任务清单 updated: {ct_path}")

print("\n=== Done ===")
