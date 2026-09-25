#!/usr/bin/env bash
# ============================================================
# monitor_recruit.sh — 招兵四拍判据链一键检查 (T7.6, 2026-09-02)
#   拍1 [START_HOME] adjacent   (runner: 主日志累积 + /tmp/hermes_ep_* 当前局)
#   拍2 visited=1               (引擎: /tmp/rl_recruit_diag.log [RL-DIAG7] / visit=1)
#   拍3 dstIsHero=1             (引擎: [RL-RECRUIT-DIAG])
#   拍4 [RECRUITED] army power  (runner: 兵力增量落地)
# 用法: wsl bash /mnt/d/Bigdata/hero3_fresh/py/monitor_recruit.sh
# 注意: hermes_ep 日志逐局覆盖, ep 侧只反映当前局; 历史靠主日志白名单转储
# ============================================================
ROOT="${ROOT:-/mnt/d/Bigdata/hero3_fresh}"
MAIN="$ROOT/train_loop.log"
DIAG=/tmp/rl_recruit_diag.log
SO="${SO:-/home/administrator/vcmi-native/rel/bin/AI/libMMAI.so}"

echo "=== 0. 训练服务状态 (system 级 unit, 0911 起) ==="
systemctl is-active homm3-train-v5

echo ""
echo "=== 1/4 [START_HOME] 三态 (begin/adjacent/abort) ==="
if [ -f "$MAIN" ]; then
  echo "主日志累积: begin=$(grep -ac '\[START_HOME\] begin' "$MAIN") adjacent=$(grep -ac '\[START_HOME\] adjacent' "$MAIN") abort=$(grep -ac '\[START_HOME\] abort' "$MAIN")"
  grep -a '\[START_HOME\]' "$MAIN" | tail -6
else
  echo "主日志不存在: $MAIN"
fi
for f in /tmp/hermes_ep_*.log; do
  [ -e "$f" ] || continue
  n=$(grep -ac '\[START_HOME\]' "$f" 2>/dev/null)
  [ "$n" -gt 0 ] || continue
  echo "-- $(basename "$f") (mtime $(stat -c %y "$f" | cut -c12-19), 当前局):"
  grep -a '\[START_HOME\] begin' "$f" | tail -1
  grep -a '\[START_HOME\]' "$f" | tail -3
done

echo ""
echo "=== 2/4 visited=1 (引擎 visit 事件) ==="
if [ -f "$DIAG" ]; then
  echo "行数: visit=1 → $(grep -ac 'visit=1' "$DIAG"), visited=1 → $(grep -ac 'visited=1' "$DIAG")"
  grep -a -E 'visit=1|visited=1' "$DIAG" | tail -5
else
  echo "无 $DIAG (引擎招兵诊断分支 0 进入 — start_home 未邻接/未 visit)"
fi

echo ""
echo "=== 3/4 dstIsHero=1 (引擎招兵目标=英雄) ==="
if [ -f "$DIAG" ]; then
  echo "行数: $(grep -ac 'dstIsHero=1' "$DIAG")"
  grep -a 'dstIsHero=1' "$DIAG" | tail -5
fi

echo ""
echo "=== 4/4 [RECRUITED] 兵力增量 (runner) ==="
if [ -f "$MAIN" ]; then
  echo "主日志累积次数: $(grep -ac '\[RECRUITED\]' "$MAIN")"
  grep -a '\[RECRUITED\]' "$MAIN" | tail -5
fi

echo ""
echo "=== 引擎侧 .so 校验 (DIAG7 符号在位) ==="
if [ -f "$SO" ]; then
  echo "$SO rl_recruit_diag 符号数: $(strings "$SO" | grep -c rl_recruit_diag)"
else
  echo ".so 不存在: $SO"
fi

echo ""
echo "=== 检查完成 (四拍全中 = 招兵链路打通) ==="
