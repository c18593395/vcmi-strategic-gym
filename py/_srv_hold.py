#!/usr/bin/env python3
import json, time, shutil
IDX = "/DATA/hero3/train_server/pool/_pool_index.json"
idx = json.load(open(IDX, encoding="utf-8"))
n = 0
for k, v in idx.items():
    if isinstance(v, dict) and k.endswith("_ug_h3m.vmap") and v.get("batch") == 3:
        v["batch"] = 99
        v["hold_reason"] = ("09-27 条件5/6 实测定谳: ckpt1615372 带训练同款引导 N=4 局, 全在31~40步HERO_DEATH早收(0满250步), meanR全负(-7.6~-64.3), 正局率<=25%. 不满足 meanR>=0 且正局>=50%. 回退=99->3 待ckpt能力提升")
        n += 1
shutil.copy(IDX, IDX + ".bak_0927_batch3hold")
json.dump(idx, open(IDX, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
from collections import Counter
c = Counter((v.get("batch") if isinstance(v, dict) else None) for v in idx.values())
print(f"server index: {n} 张 batch:3->99 | batch分布: {dict(c)} | total {len(idx)}")
