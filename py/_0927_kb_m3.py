# -*- coding: utf-8 -*-
"""09-27 知识库追加: M3 观战 0x98 根因 + --spectate 零重编修复 + testmap 摘自己机制。"""

TEXT = '''
### 09-27 T13.11 M3 观战位 0x98 空指针根因 + --spectate 零重编修复（vs 真 NK2 观战底座）

**背景**: T13.11 M1/M1.5/M2 已闭环（红方模型位 vs 蓝方 Nullkiller2 真打）；M3 用户纯观战——第 3 个客户端连 3030 进 lobby。

**0x98 根因（fork 源码静态推演 + server log 时序实锤，非 cdb 崩栈）**:
1. 崩的不是 server：M3 v2 三连接后崩点在**第 3 个 client 自身**（非 slot 路径装界面 `Attempt to read from 0x98`），与 09-10 已修的 `getPlayerState()->quests` 0x6d8 同族（fork client SPECTATOR 路径又一处未判空）。dmp 落盘 0 字节（fork crash handler 没写成）→ 改靠 server log 时序 + 源码定位。
2. **真元凶 = fork `--testmap` 内置「摘自己」**（`client/CServerHandler.cpp debugStartTest` 段落 `setPlayer(myFirstColor())`，注释 "Click on color to remove us from it"）：第 3 个 client 连入后自动把自己从蓝方槽位摘掉 → 变成「未分配玩家」→ 走默认非 slot 路径 → 装界面读 0x98 崩。server log 实锤：`Player color 1 will be controlled from connection 2`（cid2 正确）之后，client3 发一条 `L14 LobbySetPlayer` 把蓝方**抢占**改绑 `connection 3`（cid3 拿走蓝方装 ModelAI），client1 被挤成 neutral。
3. **修复（零重编，走 fork 原生参数）**：观战位 client 加 `--spectate`（`clientapp/EntryPoint.cpp L171`，"enable spectator interface for AI-only games"）→ 显式走 spectate 分支装 `PlayerColor::SPECTATOR` interface（`client/Client.cpp` 无 human slot 自动 spectate 段）绕开 0x98 未判空路径。**不是源码判空修**，是绕过；治本=fork 那条默认非 slot 路径加 `getPlayerState()` 判空重编 client（留后续）。
4. **人类 GUI 观战即用**（去 headless）：`D:\\vcmi-fork-build\\bin\\VCMI_client.exe --testmap Maps/Twins.h3m --donotstartserver --serverport 3030 --spectate`。

**M3 实跑（`py/p11_m3_spectate_probe.py` v3 PASS）**: 三连接（Python 红 / client1 蓝NK2 / client3 观战位）全存活 + 对局照常（红蓝交替 4 轮）+ 蓝方 server 侧受控=cid2 + 观战位日志净 + 三进程全活。

**附带勘误（P8-E 旧结论作废）**: P8-E（09-15）「3 客户端 join Twins → server NEW_GAME 崩」在当前 server 已**不复现**（09-16 #205 robustness 后）；M3 v2/v3 三连接对局正常开始。

**settings.json 状态**: `adventureEnemyAI=Nullkiller2`（M1.5 切，备份 `.bak_pre_nk2_0927`）；M3 未再动。蓝方身份以 server log `Player color 1 will be controlled from connection 2` 为准（client 自身 log 摘 slot 后可能无 `will be lead by` 行）。
'''

with open(r'docs/WSL知识库.md', 'a', encoding='utf-8', newline='') as f:
    f.write(TEXT)
print('WSL知识库.md 追加完成')
