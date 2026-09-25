#!/bin/bash
# 动作重复专项分析
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
SEG=$(tail -n +$LINE "$LOG")
echo "=== 本次启动 ep 数:"
echo "$SEG" | grep -c 'ep_steps='
echo
echo "=== 最近 6 ep act 序列 (完整):"
echo "$SEG" | grep -oE 'act=\[[^]]*\]' | tail -6
echo
echo "=== 相邻重复动作占比 (最近 6 ep):"
python3 - <<'EOF'
import re, glob
# 从主日志抽最近 6 个 act 序列
lines = open('/mnt/d/Bigdata/hero3_fresh/train_loop.log', errors='ignore').readlines()
acts_list = []
for l in lines:
    m = re.search(r'act=\[([0-9, ]+)\]', l)
    if m:
        acts_list.append([int(x) for x in m.group(1).split(',')])
for acts in acts_list[-6:]:
    rep = sum(1 for i in range(1, len(acts)) if acts[i] == acts[i-1])
    # 循环检测: a,b,a,b 交替
    alt = sum(1 for i in range(2, len(acts)) if acts[i] == acts[i-2] and acts[i] != acts[i-1])
    print(f"  len={len(acts)} 相邻重复={rep}({rep*100//len(acts)}%) 隔步交替={alt}({alt*100//len(acts)}%) 前几={acts[:12]}")
EOF
echo
echo "=== 引擎拒绝/错误计数 (本次启动):"
printf "TOWNSTALL: %s  'Cannot move': %s  popIfTop FAIL: %s\n" \
  "$(echo "$SEG" | grep -c TOWNSTALL)" \
  "$(echo "$SEG" | grep -c 'Cannot move hero')" \
  "$(echo "$SEG" | grep -c 'popIfTop FAIL')"
echo
echo "=== hermes 最新文件的引擎拒绝对话:"
F=$(ls -t /tmp/hermes_ep_*.log | head -1)
grep -cE 'Cannot move hero|destination tile is blocked' "$F" 2>/dev/null
grep -E 'has to answer queries' "$F" | head -2
