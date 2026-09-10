# -*- coding: utf-8 -*-
"""gui12 会话统计: 最大天数 / 战斗次数 / 进程状态"""
import re

max_day = 0
infer_count = 0
bf = bs = 0
with open(r"D:\Bigdata\hero3_fresh\gui12_stderr.log", "r", encoding="utf-8", errors="replace") as fh:
    for line in fh:
        m = re.search(r"INFER\] day=(\d+)", line)
        if m:
            infer_count += 1
            d = int(m.group(1))
            if d > max_day:
                max_day = d
        if "battleFinished" in line:
            bf += 1
        if "battleStarted" in line:
            bs += 1

print(f"INFER 推理次数: {infer_count}")
print(f"最大天数: day={max_day}")
print(f"battleFinished: {bf} 次")
print(f"battleStarted: {bs} 次")
