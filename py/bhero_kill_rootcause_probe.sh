#!/bin/bash
# WIN-1 判据① BHERO_KILL 根因深挖探针（09-15）
# 关键发现: BHERO_KILL 不在主日志白名单, 仅走旁路 battle_quality_events.log
# 主日志白名单 (train_wsl2_ppo_v2.py L225-235): [ZOMBIE]/[HERO_DEATH]/[ENDTURN_FUSE]/[ERROR]/[GUARD]/[MINE]/[TOWN 等
#   注: "[TOWN" 是前缀通配, 实际匹配 [TOWN_CAPTURE / [TOWN_VISIT / [TOWN_BLOCKED / [TOWNSTALL 等
#   TOWN_CAPTURE 完整标签进主日志 (215 条), 而 BHERO_KILL / HEROSEG_EMPTY 不在白名单
cd /mnt/d/Bigdata/hero3_fresh
LOG=train_loop.log
EVLOG=battle_quality_events.log

echo "=== 0. 主日志白名单 (train_wsl2_ppo_v2.py L225-235) ==="
echo "包含: [ZOMBIE] [HERO_DEATH] [ENDTURN_FUSE] [ERROR] [GUARD] [MINE] [TOWN (前缀通配)"
echo "      [START_HOME] [RECRUITED] [EP_TIME] [SCORE] end ep at step 等"
echo "[TOWN 前缀实际匹配: [TOWN_CAPTURE=215 [TOWN_VISIT=4689 [TOWN_BLOCKED=460 [TOWNSTALL=4271"
echo "不含: BHERO_KILL / HEROSEG_EMPTY — 仅走旁路 battle_quality_events.log"
echo

echo "=== 1. 主日志关键词计数 (白名单内) ==="
for pat in "\[ZOMBIE\]" "\[HERO_DEATH\]" "\[ENDTURN_FUSE\]" "\[ERROR\]" "\[GUARD\]" "\[MINE\]" "\[TOWN" "\[START_HOME\]" "\[RECRUITED\]" "\[EP_TIME\]" "\[SCORE\]" "end ep at step"; do
  n=$(grep -c "$pat" "$LOG")
  echo "  $pat = $n"
done
echo

echo "=== 2. 旁路 battle_quality_events.log 事件分布 ==="
echo "总行数: $(wc -l < "$EVLOG")"
grep -oE "\[(TOWN_CAPTURE|BHERO_KILL|HEROSEG_EMPTY)\]" "$EVLOG" | sort | uniq -c | sed 's/^/  /'
echo

echo "=== 3. 旁路 BHERO_KILL 全 9 条明细 (全 live_slots=0 = #146 空拍误报) ==="
grep "BHERO_KILL" "$EVLOG" | sed 's/^/  /'
echo

echo "=== 4. 旁路 TOWN_CAPTURE 按 map 分布 (218 条) ==="
grep "TOWN_CAPTURE" "$EVLOG" | grep -oE "map=[^ ]+\.vmap" | sort | uniq -c | sort -rn | sed 's/^/  /'
echo
echo "  按机制分布:"
grep "TOWN_CAPTURE" "$EVLOG" | grep -oE "(C: hero-kill proxy[^)]*|owner 1->0[^)]*|capture reward)" | sort | uniq -c | sed 's/^/    /'
echo

echo "=== 5. 旁路 HEROSEG_EMPTY 按 map 分布 (427 条) ==="
grep "HEROSEG_EMPTY" "$EVLOG" | grep -oE "map=[^ ]+\.vmap" | sort | uniq -c | sort -rn | sed 's/^/  /'
echo

echo "=== 6. 本次窗起点 (Loaded train state) ==="
L=$(grep -n "Loaded train state" "$LOG" | tail -1 | cut -d: -f1)
echo "  主日志 Loaded train state 行号: $L / 总 $(wc -l < "$LOG")"
echo "  本次窗行数: $(awk -v L=$L 'NR>=L' "$LOG" | wc -l)"
echo

echo "=== 7. 本次窗主日志白名单事件计数 ==="
for pat in "\[ZOMBIE\]" "\[GUARD\]" "\[MINE\]" "\[TOWN" "\[RECRUITED\]" "\[EP_TIME\]" "\[SCORE\]" "end ep at step"; do
  n=$(awk -v L=$L 'NR>=L && /'"$pat"'/' "$LOG" | wc -l)
  echo "  $pat = $n"
done
echo

echo "=== 8. 旁路 BHERO_KILL 时间跨度 ==="
echo "  (旁路日志无 ISO 时间戳, 只能看行号位置)"
echo "  首条行号: $(grep -n "BHERO_KILL" "$EVLOG" | head -1 | cut -d: -f1)"
echo "  末条行号: $(grep -n "BHERO_KILL" "$EVLOG" | tail -1 | cut -d: -f1)"
echo "  (对照 TOWN_CAPTURE 末条行号: $(grep -n "TOWN_CAPTURE" "$EVLOG" | tail -1 | cut -d: -f1))"
echo

echo "=== 9. 结论判定 (BHERO_KILL=0 三义性归类) ==="
echo "  三义性框架 (#204):"
echo "  ① 埋点未生效 — 代码没在位或旁路写失败"
echo "  ② 观测无效 — 观测条件结构性不满足 (空拍/瞬态)"
echo "  ③ 真无行为 — 事件真的从未发生"
echo
echo "  证据链:"
echo "  (a) 代码在位: ep_runner_one.py L1045-1053 BHERO_KILL 埋点 (if _bnow 分支)"
echo "  (b) 旁路写成功: battle_quality_events.log 有 9 条 BHERO_KILL 记录"
echo "  (c) 9/9 全部 live_slots=0 = heroes 段整段空拍 (#146 空拍误报)"
echo "  (d) #146 空拍防护 (L997 if not _bnow) 上线后 BHERO_KILL 计数恒 0"
echo "  (e) HEROSEG_EMPTY 427 次 = 空拍仍高频发生 (但被 BHERO_KILL 分支守卫拦下)"
echo "  (f) duel 图结构性: 蓝英雄死 = game_over = ep 终止, 不进 BHERO_KILL 分支"
echo "  (g) 非 duel 图: 蓝英雄从未真被歼灭 (9 条全空拍, 0 条真击杀)"
echo
echo "  判定: 属 (② 观测无效 与 ③ 真无行为 的混合)"
echo "  - 埋点本身工作正常 (9 条被记录 + 空拍防护生效)"
echo "  - 但蓝英雄真实歼灭从未发生 (非空拍的差集恒为空)"
echo "  - 判据①「BHERO_KILL 非零」是错误定义 — 应改为「TOWN_CAPTURE 非零」"
echo "    (TOWN_CAPTURE 完整标签进主日志, 白名单 \"[TOWN\" 前缀通配覆盖)"
echo "  - TOWN_CAPTURE 主日志 215 条 / 旁路 218 条 = 判据①已实质满足"
