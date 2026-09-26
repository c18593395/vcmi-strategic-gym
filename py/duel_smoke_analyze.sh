#!/bin/bash
# 分析 duel 冒烟日志: RECRUITED=0 的具体原因 (只读统计)
LOG=${1:-/tmp/duel_smoke_1.log}
echo "===== 日志: $LOG ($(wc -l < $LOG) 行) ====="
echo
echo "--- [1] 关键打点计数 ---"
for pat in 'RECRUITED' 'TOWN_RETRY' 'TOWN_EMPTY' 'GUARD' 'own_town_blocked' 'RED_DEAD' 'HERO_DEATH' 'ZOMBIE' 'guard_done' 'force game_over'; do
  printf "%-20s %s\n" "$pat:" "$(grep -c "$pat" "$LOG" 2>/dev/null)"
done
echo
echo "--- [2] 经济动作发出统计 ([ECON] recruit/build) ---"
grep -oE '\[ECON\] [a-z0-9_]+' "$LOG" | sort | uniq -c | sort -rn | head -10
echo
echo "--- [3] 动作分布 (action 直方图, 若有) ---"
grep -oE '\[ACT\] ?[0-9]+' "$LOG" | sort | uniq -c | sort -rn | head -15
echo
echo "--- [4] 8HireHero fishy 错误 ---"
echo "count: $(grep -c '8HireHero' "$LOG")"
grep '8HireHero\|visiting hero - no place' "$LOG" | head -4
echo
echo "--- [5] 取兵窗/回城触发痕迹 ---"
grep -E 'start_home|revisit|visit_econ|TOWN.*visit|move_town|RECRUIT' "$LOG" | head -15
echo
echo "--- [6] 局末收尾 (为何 90 步结束) ---"
tail -30 "$LOG" | grep -vE 'ML-time|runServer' | head -12
echo
echo "--- [7] SCORE 目标选择 (模型在追什么目标) ---"
grep -oE '\[SCORE\] pick=\([^)]*\) type=[a-z_]+' "$LOG" | sort | uniq -c | sort -rn | head -8
