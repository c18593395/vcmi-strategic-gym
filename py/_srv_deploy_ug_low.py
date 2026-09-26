#!/usr/bin/env python3
# 服务器侧: 部署 13 张 _ug_low 到 pool_dir + vcmi_maps, 核 md5, 合并 index (batch:3 low_density)
import json, os, tarfile, hashlib, shutil, time, glob

H = "/DATA/hero3"
TGZ = "/tmp/ug_low.tar.gz"
MD5F = "/tmp/ug_low_md5.json"
POOL_DIR = f"{H}/train_server/pool_dir"
VCMI_MAPS = f"{H}/vcmi/data/Maps"
INDEX = f"{H}/train_server/pool/_pool_index.json"

want = json.load(open(MD5F, encoding="utf-8"))
print(f"待部署 {len(want)} 张 _ug_low")

# 1) 解包到 pool_dir
with tarfile.open(TGZ) as t:
    t.extractall(POOL_DIR)

# 2) 核 md5 (pool_dir)
ok = 0
for fn, md5 in want.items():
    got = hashlib.md5(open(os.path.join(POOL_DIR, fn), "rb").read()).hexdigest()
    if got != md5:
        print(f"  [MISMATCH] {fn}")
    else:
        ok += 1
print(f"pool_dir md5: {ok}/{len(want)}")

# 3) 复制到 vcmi_maps + 核双副本
ok2 = 0
for fn in want:
    shutil.copy(os.path.join(POOL_DIR, fn), os.path.join(VCMI_MAPS, fn))
a = hashlib.md5(open(f"{POOL_DIR}/{list(want)[0]}", "rb").read()).hexdigest()
b = hashlib.md5(open(f"{VCMI_MAPS}/{list(want)[0]}", "rb").read()).hexdigest()
assert a == b, "双副本不一致!"
for fn in want:
    ha = hashlib.md5(open(f"{POOL_DIR}/{fn}", "rb").read()).hexdigest()
    hb = hashlib.md5(open(f"{VCMI_MAPS}/{fn}", "rb").read()).hexdigest()
    if ha == hb:
        ok2 += 1
print(f"vcmi_maps 双副本核对: {ok2}/{len(want)}")

# 4) 合并 index: batch:3 改为 13 张 _ug_low (全密度 _ug 保持 99 hold)
idx = json.load(open(INDEX, encoding="utf-8"))
shutil.copy(INDEX, INDEX + ".bak_0927_uglow")
for fn in want:
    e = {
        "blue_ai": "MMAI_RANDOM", "layer": "underground", "batch": 3,
        "low_density": True,
        "based_on": fn.replace("_ug_low_h3m.vmap", "_ug_h3m.vmap"),
        "verify": "ug_low 减怪重转 (地表中性怪 -50%, 保留资源/矿/地下层/玩家兵)",
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    # 保留本地 index 的 reduce 明细
    idx[fn] = e
from collections import Counter
c = Counter((v.get("batch") if isinstance(v, dict) else None) for v in idx.values())
print(f"index batch 分布: {dict(c)} | total {len(idx)}")
json.dump(idx, open(INDEX, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("deployed:", time.strftime("%Y-%m-%d %H:%M:%S"))
