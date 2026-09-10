#!/usr/bin/env python3
"""Update docs: WSL知识库 + WSL踩坑点 + 总任务 + 当前任务清单"""
import pathlib

base = pathlib.Path('D:/Bigdata/hero3_fresh/docs')

# ============================================================
# 1. WSL知识库.md — append to end
# ============================================================
kb_path = base / 'WSL知识库.md'
kb = kb_path.read_text('utf-8')

new_kb_section = """
---

## VCMI 网络协议与外挂 AI 架构调研 (09-11, GitHub 深度分析)

**触发**: 调研 xsa-dev/homm3env + Issue #5586 + VCMI 网络层源码，探索"模型外挂"可行性。

### 核心发现

1. **VCMI develop 所有 AI 都是进程内直接回调 (CCallback)** — EmptyAI 的 `yourTurn` 只做 `cb->selectionMade(0); cb->endTurn()`，编译为 OBJECT 库链接进 server，完全不经过网络层。`AIFactory.h` 证实：所有 AI (BattleAI/Nullkiller2/MMAI/StupidAI/EmptyAI) 通过 `createAdventureAI(name)` / `createBattleAI(name)` 静态构造，无动态加载。

2. **VCMI 网络层是完整的命令服务器** — `lib/network/` 有 `NetworkServer`(TCP server) + `NetworkConnection`(client 连接) + `NetworkHandler`(包分发) + `NetworkDiscovery`(UDP 广播)。客户端发 `CPackForServer` 包，server 处理后发 `CPackForClient` 包。**Server 对客户端一视同仁**，不区分人类 vs AI。

3. **`PacksForServer.h` 已定义所有战略层操作** (二进制序列化协议，非 JSON)：
   - `MoveHero(path, layer, hid, transit)` — 移动英雄
   - `EndTurn()` — 结束回合
   - `RecruitCreatures(tid, dst, crid, amount, level)` — 招募
   - `BuildStructure(tid, bid)` / `RazeStructure` — 建造/拆除
   - `UpgradeCreature(pos, id, cid)` — 升级兵种
   - `HireHero(hid, tid, nhid)` / `DismissHero(hid)` — 雇佣/解散
   - `SpellResearch(tid, spellAtSlot, accepted)` — 研究法术
   - `SetFormation(hid, formation)` / `SetTactics(hid, enabled)` — 阵型/战术
   - `CastAdvSpell(hid, sid, pos)` — 战略法术
   - `MakeAction(BattleAction, battleID)` — 战斗行动 (BattleAction = MMAI 内部同结构体)
   - `QueryReply(qid, reply)` — 回复查询
   - `TradeOnMarketplace(...)` / `ExchangeArtifacts(...)` / `BuyArtifact(...)` — 经济
   - `BulkMoveArmy/BulkSplitStack/BulkMergeStacks` — 批量部队操作
   - `BuildBoat(objid)` / `SaveGame(fname)` / `SetObjectProperty(...)` — 杂项

4. **`PacksForClient.h` 客户端收到的包**:
   - `NewTurn(day, heroesMovement, heroesMana, availableCreatures, playerIncome, ...)` — 回合开始
   - `TryMoveHero(id, result, start, end, movePoints, fowRevealed, attackedFrom)` — 移动结果
   - `PackageApplied(player, requestID, packType, result)` — 执行结果
   - `PlayerStartsTurn(queryID, player)` — Query 类型，需回复
   - `HeroLevelUp/CommanderLevelUp/BlockingDialog/GarrisonDialog` — 均为 Query，必须回复 `QueryReply`

5. **`features/battle-ml` 分支是死分支** — 最后提交 2022-07-19，作者 nullkiller，从未合并。xsa-dev/homm3env 基于此分支，其 JSON over TCP 协议是私有协议，当前 develop 无对应 server 端代码。

6. **Issue #5586 (LLM Learning Game Integration) 是纯提案** — 创建者 VCMIchatbot，4 条评论无人接活。提案的"TCP 命令服务器 + JSON 序列化"其实 VCMI 已经有了，只是格式是二进制不是 JSON。

### 外挂 AI 架构

```
VCMI Server (不改代码)
  ├─ 人类客户端 (vcmiclient) ← TCP
  └─ 外部 AI (自定义客户端) ← TCP ← 模型
```

- 外挂 AI 实现 `NetworkConnection` 协议 + `CPackForServer` 序列化
- Server 不区分人类 vs AI
- `MakeAction` 里的 `BattleAction` 与 MMAI 内部同结构体 — 战斗层和战略层共用协议
- 所有 `Query` 类型必须回复 `QueryReply`，否则 server 卡住

### 外挂路径评估

| 路径 | 难度 | 说明 |
|------|------|------|
| A. 逆向二进制序列化 | 高 | 读 `Serializeable.h` + `NetworkHandler.cpp` 推字节布局 |
| B. C++ 写 VCMI headless client | 中 | 用 VCMI 头文件，类似 EmptyAI 但走网络 |
| C. 给 VCMI 加 JSON 包装层 | 中 | 改官方代码，维护成本高 |
| D. Python 实现序列化 | 高 | struct + 变长字段处理 |

**结论**: 外挂方案对终极目标 (人 vs 人 vs 模型联网) 是更好的架构，但序列化逆向是当前瓶颈。短期继续 .so 直连，长期可探索路径 B (C++ headless client)。

### 参考项目评估

| 项目 | 价值 | 说明 |
|------|------|------|
| xsa-dev/homm3env | 低 | 2021 SOC 比赛骨架，RL 环境全是 stub，JSON 协议是死分支私有协议 |
| vcmi-gym (smanolloff) | 高 | MMAI 官方训练栈，PPO-DNA + GNN + ONNX，架构可参考 |
| CleanRL (vwxyzjn) | 中 | PPO 单文件实现，超参对照参考 |
| Issue #5586 | 低 | 纯提案，无人实施 |
| agentic-factorio-ai | 中 | LLM+RL 分层架构范式参考 |
"""

kb_path.write_text(kb.rstrip('\n') + '\n' + new_kb_section, 'utf-8')
print(f"[OK] 知识库 updated: {kb_path}")

# ============================================================
# 2. WSL踩坑点.md — append to 待归档新增
# ============================================================
cp_path = base / 'WSL踩坑点.md'
cp = cp_path.read_text('utf-8')

# The current max pit number is #174 (per the 速查表)
# But there are already #125-#174 listed. The "待归档新增" section says max is #174.
# We need to find the actual max in the 速查表 area.
# From reading: the table goes up to #174, and there are entries like #166-#174
# The note says: "当前最大 #174，下一条为 #175"
# But looking more carefully at the 速查表, there are entries like #144-#165 after #174
# Actually the table has entries up to #174 (renumbered from 132-140)
# Let me check the actual last entry in the 待归档新增 area

# The section says: "> ✅ **归档完成 (09-11)**：原待归档 50 条已全部分发...本区暂无新增待归档条目。"
# So I need to replace that with new entries

new_pitfalls = """
### #175: VCMI 网络协议是二进制序列化，非 JSON (09-11)

**现象**: 调研 xsa-dev/homm3env 时发现其 JSON over TCP 协议基于 `features/battle-ml` 分支 (2022 年死分支)，当前 VCMI develop 无此协议。VCMI 官方网络协议使用 `Serializeable` 模板 + `h & field` 做二进制序列化。

**根因**: VCMI 的网络包系统 (`lib/networkPacks/`) 从 HoMM3 原版协议继承而来，使用自定义二进制格式 (非 JSON/protobuf/msgpack)。`CPack` 基类的 `serialize(Handler &h)` 通过 `h & field` 逐字段序列化，变长字段 (std::vector, std::string) 有自定义编码。

**处理**: 外挂 AI 方案需逆向 `Serializeable.h` 的字节布局。短期不影响 (继续 .so 直连)，长期需路径 B (C++ headless client 复用 VCMI 头文件)。

**教训**: 不要假设 VCMI 有 JSON 协议 — 第三方项目 (homm3env) 的 JSON 格式是基于已废弃分支的私有协议。官方协议始终在 `lib/networkPacks/` 定义。

---

### #176: EmptyAI 不走网络 — VCMI 内置 AI 全是进程内直接回调 (09-11)

**现象**: 误以为 EmptyAI 或 MMAI 通过网络与 server 通信，实际读源码发现全部用 `CCallback` (C++ 直接函数调用)，编译为 OBJECT 库链接进 server 进程。

**根因**: `AIFactory.h` 定义 `createAdventureAI(name)` / `createBattleAI(name)` 静态工厂，所有 AI 在 server 进程内构造。`CEmptyAI::yourTurn` 直接调 `cb->selectionMade(0); cb->endTurn()`。无动态加载、无插件系统。

**处理**: 外挂 AI 必须走网络协议 (作为客户端连接 server)，不能模仿内置 AI 的 `CCallback` 路径。`--onlyAI` 标志是告诉 server 内部构造 AI，不是启动网络桥。

**教训**: VCMI 有两条 AI 路径 — 内部回调 (CCallback, 所有内置 AI) vs 网络协议 (CPackForServer, 客户端)。外挂只能用网络协议。混淆这两条路径会导致错误的架构设计。

---

### #177: features/battle-ml 分支是死分支 — 基于它的 JSON 协议不可用 (09-11)

**现象**: xsa-dev/homm3env 的 README 指向 `vcmi/vcmi/tree/battle-ml` 分支，其 TCP JSON 协议在当前 develop 无对应 server 端代码。

**根因**: `features/battle-ml` 分支最后提交 2022-07-19 (作者 nullkiller)，从未合并到 develop。当前 VCMI develop 完全没有 BattleML TCP/JSON 协议代码。

**处理**: 不要基于 battle-ml 分支做架构决策。如果要外挂 AI，走官方 `lib/network/` + `lib/networkPacks/` 协议。

**教训**: 调研第三方项目时，必须确认其依赖的上游分支是否仍然活跃。homm3env 是 2021 SOC 比赛产物，代码是骨架/存根 (step() 返回 None, update_game_state() 是 pass)，其架构参考价值仅限于"JSON over TCP 概念"，不能直接用。
"""

# Replace the "归档完成" note with new entries
old_note = '> ✅ **归档完成 (09-11)**：原待归档 50 条已全部分发至 5 个主题子文档（环境 14 / 构建 13 / 引擎 10 / 训练 11 / 地图 2），本区暂无新增待归档条目。'
new_note = '> ✅ **归档完成 (09-11)**：原待归档 50 条已全部分发至 5 个主题子文档（环境 14 / 构建 13 / 引擎 10 / 训练 11 / 地图 2）。\n' + new_pitfalls

if old_note in cp:
    cp = cp.replace(old_note, new_note)
    cp_path.write_text(cp, 'utf-8')
    print(f"[OK] 踩坑点 updated: {cp_path}")
else:
    print(f"[WARN] Could not find archive note, appending at end")
    cp_path.write_text(cp.rstrip('\n') + '\n' + new_pitfalls, 'utf-8')
    print(f"[OK] 踩坑点 appended at end: {cp_path}")

# ============================================================
# 3. 总任务.md — update progress table + milestones
# ============================================================
zt_path = base / '总任务.md'
zt = zt_path.read_text('utf-8')

# Update T8 status line — add note about network protocol research
# The T8 line currently says: "| T8 | 战斗集成 | ⬜ 待办 (v15 合并后评估) |"
# We keep it as is since we didn't do T8 work, just research

# Add milestone entry
old_milestone = "- 2026-08-31：TOWN 轴复活 (dist≤1 + blue城引导, 触发率 0→36% 局)；回城取兵链路 (visit+RECRUIT=兵直上英雄, 兵力增量管道打通)；Router 断言根因 = USING_ONNX=0 (R6, 战斗 AI 恒 StupidAI 系既定环境)；garrison obs 恒 0 发现 (撤梯子硬前置)；libMMAI 全量重编部署。"
new_milestone = old_milestone + "\n- 2026-09-11：VCMI 网络协议深度调研 — 确认外挂 AI 架构可行 (CPackForServer 二进制协议, server 不区分人 vs AI)；battle-ml 分支已死 (2022 未合并)；Issue #5586 纯提案无人实施；EmptyAI 走 CCallback 非网络。详见知识库「VCMI 网络协议与外挂 AI 架构调研」。"

if old_milestone in zt:
    zt = zt.replace(old_milestone, new_milestone)
    zt_path.write_text(zt, 'utf-8')
    print(f"[OK] 总任务 updated: {zt_path}")
else:
    print(f"[WARN] Could not find milestone anchor in 总任务")

# ============================================================
# 4. 当前任务清单.md — add research note at top
# ============================================================
ct_path = base / '当前任务清单.md'
ct = ct_path.read_text('utf-8')

# Insert a note about the research after the ⚡ header line
old_header = "> ⚡ **下次会话第一步 (0910 深夜更新)**"
new_header = "> 📖 **09-11 研究增量**: VCMI 网络协议调研完成 — 外挂 AI 架构可行 (详见知识库新章)，不影响当前训练。踩坑 #175-#177 新增 (网络协议非 JSON / EmptyAI 走 CCallback / battle-ml 死分支)。\n> ⚡ **下次会话第一步 (0910 深夜更新)**"

if old_header in ct:
    ct = ct.replace(old_header, new_header, 1)
    ct_path.write_text(ct, 'utf-8')
    print(f"[OK] 当前任务清单 updated: {ct_path}")
else:
    print(f"[WARN] Could not find header anchor in 当前任务清单")

print("\n=== All docs updated ===")
