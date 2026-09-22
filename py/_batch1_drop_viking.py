#!/usr/bin/env python3
"""batch1 判定执行: 摘除 a_viking×2 (两局 -900 级刷墙, 图能力真空), batch1 剩 3 张 (09-22)"""
import json

P = "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_index.json"
idx = json.load(open(P, encoding="utf-8"))
changed = []
for k, v in idx.items():
    if isinstance(v, dict) and v.get("batch") == 1 and "a_viking" in k:
        v["batch"] = 99  # 99 = 暂缓 (能力真空, 模型提升后回评); BATCH=1 过滤自动排除
        v["hold_reason"] = "a_viking 两局 -934/-891 act3 刷墙 250 步满步, 大图无近目标能力真空 (09-22 50 局判定摘除)"
        changed.append(k)
json.dump(idx, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("摘除:", changed)

# 复核: BATCH=1 过滤后剩余
left = [k for k, v in idx.items() if isinstance(v, dict) and v.get("batch") is not None and v.get("batch") <= 1]
print("batch1 剩余:", left)
