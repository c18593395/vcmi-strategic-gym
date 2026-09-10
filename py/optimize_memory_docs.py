#!/usr/bin/env python3
"""优化记忆: 更新训练状态文档 + 精简 memory"""
import pathlib

base = pathlib.Path('D:/Bigdata/hero3_fresh/docs')

# ============================================================
# 1. 更新 WSL知识库-训练状态.md — 刷新为 v5 当前快照
# ============================================================
ts_path = base / 'WSL知识库-训练状态.md'
ts = ts_path.read_text('utf-8')

# Replace the old C4 section header and content
old_header = "### 当前训练（C4）"
new_header = "### 当前训练（C4, 历史）"

ts = ts.replace(old_header, new_header)

# Add v5 snapshot after the old C4 section (before 观测向量结构)
v5_section = """
### 当前训练（v5, 截至 2026-09-11）

| 参数 | 值 |
|------|-----|
| 脚本 | train_wsl2_ppo_v2.py |
| 算法 | PPO |
| 网络 | MLP: 3464→256→128→25(act+crit) |
| Episodes | 1000 |
| Steps/ep | 200 |
| Batch | 2048 |
| 学习率 | 3e-4 |
| Clip | 0.2 |
| Epochs | 6 |
| KL_TARGET | 0.50 |
| KL_COEF | 0.3 |
| Entropy | -0.05 |
| 设备 | cuda (RTX3060) |
| 地图 | T05 6图 + T06 duel + 72X72_01 (共8图) |
| 对手 | blue=MMAI_RANDOM |
| NK2 shaping | 0.45 |
| objective_reward | 30 (矿/城事件) |
| move_to_force | 60 |
| economy_force | 24 |
| reward clip | ±300 |
| Checkpoint | 每 50 step, 保留 10 个 |
| OBS_DIM | 3464 |
| N_ACTIONS | 25 (0-24, 25-63 预留) |

**训练运行方式**: WSL systemd transient unit `homm3-train-v5`, 优雅停止 = 零损失
**训练日志**: `train_loop.log`
**健康判据**: r 双峰 — 130-160(守卫胜) / 5-30(只招兵), 均健康
**分析日志**: 先按 ROUND 头切片, batch 行 ~27 局 1 条属正常
**runner 标记**: [GUARD]/[ZOMBIE] 进 `/tmp/hermes_ep_{pid}.log` 不进主日志

**NK2+超参全表**: batch2048/LR3e-4/KL_TARGET0.5/KL_COEF0.3/entropy-0.05/move_to_force60/
objective_reward30/economy_force24/reward_clip±300; 全表见 vcmi-rl-training refs/。

**NK2死锁修复链 (08-16/17)**: 详见 vcmi-ml-module refs/deadlock-chain+battle-query-hang;
close卡死→SAVED后os._exit; 采集bash wrapper逐局独立; 采集/训练前必验npz英雄位置+动作分布
"""

ts = ts.replace("### 观测向量结构 (256 维)", v5_section + "\n### 观测向量结构 (3464 维)\n\n| 索引 | 内容 | 长度 |\n|------|------|------|\n| 0-25 | Global + Player state | 26 |\n| 26-127 | Heroes (6 × 16字段) | 102 |\n| 128-473 | Towns (8 × 43字段) | 346 |\n| 474-480 | 填充/特殊字段 | 7 |\n| 336-480 | Towns 段 (含 garrison 填充, 09-02) | 145 |\n| 3464 | 总维度 | 3464 |")

# Also update the action space section
old_actions = """### 动作空间 (11)


| ID | 动作 |
|----|------|
| 0-7 | 8 方向移动 |
| 8 | 交互（拾取/对话/攻击） |
| 9 | 下一英雄 |
| 10 | 结束回合 |"""

new_actions = """### 动作空间 (25, 0-24 有效)

| ID | 动作 |
|----|------|
| 0-7 | 8 方向移动 |
| 8 | 交互（拾取/对话/攻击） |
| 9 | 下一英雄 |
| 10 | 结束回合 |
| 11-24 | 战略动作 (招兵/建城/升级/交换/买卖/内政等, C7 映射) |
| 25-63 | 预留 (动作空间宪法冻结, 启用预留位) |

> 宪法冻结: 动作码 64 位 + obs 3464 维, 见 `docs/动作空间设计文档.md`"""

ts = ts.replace(old_actions, new_actions)

ts_path.write_text(ts, 'utf-8')
print(f"[OK] 知识库-训练状态 updated: v5 快照 + obs 3464 + 动作 25")

# ============================================================
# 2. WSL知识库.md — 添加 docs 行尾约定到约定区
# ============================================================
kb_path = base / 'WSL知识库.md'
kb = kb_path.read_text('utf-8')

old_convention = "> **约定（AI 必读）**：收到“保存知识库”→ 追加到本文件末尾「待整理」区（不自动分发到子文档，由用户定期自行归档）；收到“保存踩坑点”→ 追加到 `WSL踩坑点.md` 末尾「待归档新增」区（不自动分发）；收到“记日志/今天进展”→ 写 `WSL日志/YYYY-MM-DD.md`（新日期新建一份）。模型读取本索引后应**自动取读下方子文档与日志目录**获取完整内容。"

new_convention = old_convention + """
> **docs 行尾约定**: 知识库/踩坑点/当前任务清单 = CRLF, 总任务.md = LF+BOM (python 验证, 防 \\r\\r\\n, 显式追加); 踩坑记录旧 LF"""

kb = kb.replace(old_convention, new_convention)
kb_path.write_text(kb, 'utf-8')
print(f"[OK] 知识库 updated: docs 行尾约定")

# ============================================================
# 3. 踩坑点-构建 — 添加 mlclient 重编崩 (如果有空间)
# ============================================================
bp_path = base / 'WSL踩坑点-构建-编译与部署.md'
bp = bp_path.read_text('utf-8')

if 'strategic_state.h同步后重编即崩' not in bp:
    old_110 = "- 教训: 改 server 代码后必须确认 .o 实际重编 (ls mtime); 部署验证用行为 (CBattleQuery 卡顶)"
    new_110_extra = old_110 + """

### 111. mlclient 重编崩: strategic_state.h 同步后重编即崩 (08-26)
- **现象**: strategic_state.h 同步后重编 mlclient → start_vcmi 未调 → GAME null → 崩溃
- **注意**: 纯 8-23 源码也崩, 不是同步问题本身
- **安全操作**: 单个 .cpp 的 .o 重编 + 链接成功 (BRP/CGameHandler/AAI), 勿碰 .h
- **备份**: 工作 .so 在 `backup-t03-target-20260825_233554/`
- **教训**: 改 build 树前必备份 .so+source; 不要碰 .h 头文件, 只改 .cpp"""
    bp = bp.replace(old_110, new_110_extra)
    bp_path.write_text(bp, 'utf-8')
    print(f"[OK] 踩坑点-构建 updated: #111 mlclient 重编崩")
else:
    print(f"[SKIP] 踩坑点-构建 已有 #111")

# ============================================================
# 4. 踩坑点-引擎 — 确认 NK2 死锁链已覆盖
# ============================================================
eng_path = base / 'WSL踩坑点-引擎-VCMI-API.md'
eng = eng_path.read_text('utf-8')

if 'NK2死锁修复链' not in eng:
    import re
    nums = re.findall(r'### (\d+)\.', eng)
    last_num = int(nums[-1]) if nums else 0
    
    nk2_entry = f"""
### {last_num + 1}. NK2 死锁修复链 (08-16/17, 详见 vcmi-ml-module refs/deadlock-chain)
- **close 卡死**: env.close() 嵌入模式卡死 (58% CPU, close 线程 5s 超时无效) → SAVED 后直接 os._exit(0) 跳过
- **battle query 卡顶**: 三层 query 栈 + notifyObjectAboutRemoval 中断 → QueriesProcessor::removeQuery 任意位置强制移除
- **battleResultAccepted**: 改用 removeQuery (onRemoval 只调一次防段错误 + 移除后触发暴露链)
- **采集 bash wrapper**: 逐局独立 (防跨局状态泄漏)
- **训练前必验**: npz 英雄位置 + 动作分布 (防模型输出全空/全非法)
"""
    eng = eng.rstrip('\n') + nk2_entry + '\n'
    eng_path.write_text(eng, 'utf-8')
    print(f"[OK] 踩坑点-引擎 updated: #{last_num+1} NK2 死锁链")
else:
    print(f"[SKIP] 踩坑点-引擎 已有 NK2 死锁链")

print("\n=== 所有文档更新完成 ===")
print("\n下一步: 精简 memory (已在知识库覆盖的条目删除, 释放空间)")
