#!/bin/bash
# P-031 duel 新窗时间桶 (部署 step>=1655053) — awk 快读 (绕开 Python 大文件慢读)
LOG=/DATA/hero3/train_server/train_full.log
STEP_NEW=1655053
grep -E "\[SLOT\].*108X108_02_duel" "$LOG" | awk -v sn=$STEP_NEW '
  {
    match($0, /step[0-9]+/); s = substr($0, RSTART+5, RLENGTH-5) + 0
    match($0, /avg_r=[-0-9.]+/); a = substr($0, RSTART+6, RLENGTH-6) + 0
    if (s < sn) next
    n++; sr += a
    if (a > 0) p++
    if (a < -2) big++
    steps[s] = a
    ep[s] = 1
  }
  END {
    if (n == 0) { print "no duel >= " sn; exit }
    print "duel >= " sn ": n=" n " avg_r=" sr/n " pos=" p " big_neg=" big+0
    # 分三桶 (step 排序)
    m = 0
    for (st in steps) { arr[m++] = st }
    # 简单插入排序
    for (i = 1; i < m; i++) {
      key = arr[i]; j = i - 1
      while (j >= 0 && arr[j] > key) { arr[j+1] = arr[j]; j-- }
      arr[j+1] = key
    }
    k = int(m / 3)
    for (b = 0; b < 3; b++) {
      lo = (b == 0) ? 0 : b * k
      hi = (b == 2) ? m - 1 : (b + 1) * k - 1
      cnt = 0; sum = 0; pp = 0
      for (i = lo; i <= hi; i++) {
        cnt++; sum += steps[arr[i]]
        if (steps[arr[i]] > 0) pp++
      }
      if (cnt > 0)
        printf "  bucket%d: step%d-%d n=%d avg_r=%.2f pos=%d(%d%%)\n", b+1, arr[lo], arr[hi], cnt, sum/cnt, pp, pp*100/cnt
    }
  }'
