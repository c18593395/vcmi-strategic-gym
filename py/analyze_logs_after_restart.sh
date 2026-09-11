#!/bin/bash
# 重启后日志分析: 训练健康度 + C 方案 (hero-kill proxy) 是否已触发
cd /mnt/d/Bigdata/hero3_fresh
echo "== 1. train_loop.log 尾部 30 行 =="
tail -30 train_loop.log
echo
echo "== 2. battle_quality_events.log: C 方案 proxy 事件 =="
grep -c 'hero-kill proxy' battle_quality_events.log 2>/dev/null
grep 'hero-kill proxy' battle_quality_events.log 2>/dev/null | tail -5
echo
echo "== 3. battle_quality_events.log: TOWN_CAPTURE 总量分布 =="
grep 'TOWN_CAPTURE' battle_quality_events.log 2>/dev/null | sed -E 's/.*map=([^ ]+).*/\1/' | sort | uniq -c | sort -rn
echo
echo "== 4. BHERO_KILL 事件按图分布 =="
grep 'BHERO_KILL' battle_quality_events.log 2>/dev/null | sed -E 's/.*map=([^ ]+).*/\1/' | sort | uniq -c | sort -rn | head -10
echo
echo "== 5. 本轮 (step>629167) 各图 ep 明细 =="
grep -E '^\s+ep_steps|EP_TIME|EP_TRAJ' train_loop.log | awk '/step629167/{found=1} found' | tail -40
echo
echo "== 6. 健康告警 =="
grep -iE 'error|crash|zombie|zombie|WARN' train_loop.log | tail -10
tail -5 monitor_alerts.log 2>/dev/null
