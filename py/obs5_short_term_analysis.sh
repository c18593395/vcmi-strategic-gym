#!/bin/bash
# OBS-5 108_02_duel 无标记短终局定性 (09-14 36 局中 2 局: 34/41 步, r16/20, 8-9.4s/步偏慢)
# 目标: 从 train_loop.log 抓 108_02_duel 的终局明细, 看有无终局标记 / 战斗事件 / err 字段
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"

echo "=== 1. 108_02_duel 全部局终局行 (grep 108_02 相关终局信号) ==="
# 终局信号: END_TURN_DONE / GAME_OVER / GUARD_DONE / TOWN_CAPTURE / zombie / err
grep -nE "108_02_duel" "$LOG" 2>/dev/null | grep -E "END_TURN_DONE|GAME_OVER|GUARD_DONE|TOWN_CAPTURE|zombie|err|step.*34|step.*41|r.*16\b|r.*20\b|BATTLE|battle" | head -40

echo ""
echo "=== 2. 108_02_duel 近期 episode 明细 (最近 60 行含 108_02 的) ==="
grep -nE "108_02_duel" "$LOG" 2>/dev/null | tail -60

echo ""
echo "=== 3. 短终局特征: 34 步 / 41 步 的局 (grep step=34 / step=41) ==="
grep -nE "108_02" "$LOG" 2>/dev/null | grep -E "step[= ]*(34|41)\b|steps[= ]*(34|41)\b" | head -20

echo ""
echo "=== 4. 战斗事件 (BattleStart / battle_result) 108_02 相关 ==="
grep -nE "108_02" "$LOG" 2>/dev/null | grep -E "BattleStart|battle_result|BATTLE|combat|战斗" | head -20
