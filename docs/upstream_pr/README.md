# 可上游化 PR 提交包（我们→官方 vcmi/vcmi）

> 制作日期：2026-09-24。制作基线：官方 `upstream/develop` = `3813f85006`（2026-09-18）；**2026-09-24 已在 `official-20260924/develop` = `94ec6b739` 复核，A/B 官方仍未修（行号见台账 §7）**。
> 两个补丁均已 `git apply --check` 对官方纯净基线验证通过。
> 本地分支已建好：`pr-fix-battle-crash`（77e96c8b9c）、`pr-fix-spectator-crash`（de94bc0c5），作者暂署 `c18593395 <c18593395@users.noreply.github.com>`。

---

## 包内文件

| 文件 | 内容 |
|------|------|
| `0001-Fix-null-battle-dereference-in-CClient-startPlayerBa.patch` | PR-A 补丁（client/Client.cpp，+15/-1） |
| `0001-Fix-spectator-crashes-in-adventure-map-interaction.patch` | PR-B 补丁（AdventureMapInterface.cpp + AdventureMapShortcuts.cpp，+10/-1） |

---

## 推送步骤（在联网机执行，沙箱无外网）

### 0. 拿官方今天最新并复核（已于 2026-09-24 完成一次，结论见台账 §7）
```bash
cd vcmi
git fetch upstream
# ⚠️ 不要用 upstream/develop 当基线：它长期停在 3813f85006(09-18)，
#    `git log 3813f85006..upstream/develop` 恒为空 → 会给出「官方未修」的假阴性。
#    改用已 fetch 的本地基线 ref（当前 = official-20260924/develop = 94ec6b739）：
BASE=official-20260924/develop
# 快速复核官方是否已修（预期无输出 = 未修，可提交）：
git log --oneline 3813f85006..$BASE -- client/Client.cpp client/adventureMap/
git grep -n "getCurrentArmy()->ID" $BASE -- client/adventureMap/AdventureMapInterface.cpp   # 若此行还在=B 仍可提
```
**2026-09-24 实测结论（94ec6b739）**：A = `Client.cpp` L656-658 `activateStack` lambda 内双 `getBattle()` 无判空（仍未修）；B = `AdventureMapInterface.cpp` L571 `getCurrentArmy()->ID` 不判空、`AdventureMapShortcuts.cpp` 无 SPECTATOR 早退（仍未修）→ **两个 PR 均可提**。
若官方已修：放弃对应 PR，更新 `docs/官方同步台账.md` §7。

### 1. 变基到最新 develop
```bash
BASE=official-20260924/develop
git checkout pr-fix-battle-crash  && git rebase $BASE
git checkout pr-fix-spectator-crash && git rebase $BASE
```
rebase 干净 = 官方没动同区域，直接进下一步；有冲突 = 官方近期改过同文件，需人工对照（回到台账 §7 流程）。

### 2. 编译自检（建议）
```bash
# WSL 内按你现有构建流程编译 client 目标，确认无警告/错误
```
沙箱内无法编译，但已做类型核实：`getCurrentArmy()` 返回 `const CArmedInstance*`（PlayerLocalState.h:88）；`BattleInfo::activeStack` 是 `si32`；`color.toString()` 在 Client.cpp 已有 4 处既有用法。

### 3. 修正提交作者（如你的 noreply 格式不同）
```bash
git config user.name "c18593395" && git config user.email "你的GitHub noreply邮箱"
git checkout pr-fix-battle-crash    && git commit --amend --reset-author --no-edit
git checkout pr-fix-spectator-crash && git commit --amend --reset-author --no-edit
```

### 4. 推到你的 fork 并开 PR
```bash
# 前置：在 GitHub 网页上把 vcmi/vcmi fork 到 c18593395 账户（若还没有）
git remote add myfork https://github.com/c18593395/vcmi.git
git push myfork pr-fix-battle-crash
git push myfork pr-fix-spectator-crash
```
开 PR（两个分开提，一 PR 一修）：
- PR-A: `https://github.com/vcmi/vcmi/compare/develop...c18593395:vcmi:pr-fix-battle-crash`
- PR-B: `https://github.com/vcmi/vcmi/compare/develop...c18593395:vcmi:pr-fix-spectator-crash`

标题与正文直接复制下面两节。PR 全程英文；CI 会自动构建。

---

## PR-A 文案

**Title:** Fix null battle dereference in CClient::startPlayerBattleAction

**Body:**

```markdown
## Problem

`CClient::startPlayerBattleAction()` resolves the battle via `gameState().getBattle()` **twice** inside the `activateStack` lambda and dereferences the result without any null check:

```cpp
battleint->activeStack(battleID, gameState().getBattle(battleID)->battleGetStackByID(gameState().getBattle(battleID)->activeStack, false));
```

If the battle instance is no longer present, or the active stack cannot be resolved, the client dereferences a null pointer and crashes.

## Observed impact

We run VCMI headless for multi-AI self-play and hit reproducible crashes on battle start (this is how the bug was found).

## Fix

Fetch the battle pointer once, log an error and return early when it or the active stack is missing, and pass the resolved stack to the battle interface. No behavior change in the normal path — strictly defensive.
```

## PR-B 文案

**Title:** Fix spectator crashes in adventure map interaction

**Body:**

```markdown
## Problem

Two places in the adventure map assume a non-spectator local player with an active selection:

1. `AdventureMapInterface::onTileLeftClicked()` dereferences `getCurrentArmy()` without a null check. In spectator mode (and in edge cases such as losing the last hero) no selection is established, so **any left click on the adventure map crashes the client**.

2. `AdventureMapShortcuts::showOverview()` unconditionally pushes `CKingdomInterface`, which queries player data (hero/town lists) on construction and throws for spectators.

## Fix

1. Cache `getCurrentArmy()` into a local and make the map click a no-op when it is null.
2. Early-return from `showOverview()` when `playerID == PlayerColor::SPECTATOR`.

Both changes are strictly defensive; behavior for regular players is unchanged.
```

---

## 注意事项

1. **不要**把 `fix_action_mapping` / RL 分支推给官方——95% 是 ML 训练专属，会被拒。
2. B 原提交（a0b584d39e）里夹带的线程 try/catch（CServerHandler/ServerRunner）**未进 PR**：用了 win32 的 `GetCurrentThreadId()` 不可移植，且"吞异常"策略需官方讨论，属于另一个话题。
3. 同文件里 `CClient::battleFinished()`（第 500-501 行）存在同款 triple `getBattle()` 不判空模式——本次刻意**未纳入**（未经我们实测修复验证），可作为 PR-A 的评论补充线索或后续独立 PR。
4. 提交后如 maintainer（IvanSavenko / starius 等）要求改动，在分支上追加 commit 即可，PR 自动更新。
