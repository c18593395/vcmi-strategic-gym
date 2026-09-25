#!/bin/bash
# R6 验证: 本次启动(最后一次 Loaded train state)之后的 Router 异常与新日志
LOG="${LOG:-/mnt/d/Bigdata/hero3_fresh/train_loop.log}"
LINE=$(grep -n 'Loaded train state' "$LOG" | tail -1 | cut -d: -f1)
echo "resume at line $LINE"
echo "--- Router exception after resume:"
tail -n +$LINE "$LOG" | grep -c 'Router. battleStart exception'
echo "--- battle/BAI 相关新日志:"
tail -n +$LINE "$LOG" | grep -iE 'battle|BAI|StupidAI' | grep -v 'battleStart exception' | tail -5
echo "--- ep 进度:"
tail -n +$LINE "$LOG" | grep 'ep_steps=' | tail -3
