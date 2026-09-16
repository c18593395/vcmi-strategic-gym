#!/usr/bin/env python3
# B2 冒烟重命名: B2_KneeDeep.vmap → B2_adventure_knee_deep.vmap
# 原因: strategic_env.py 断言 mapname 必须含 s1/mini/adventure/h3m 关键字 (adventure 模式)
# 双副本同步: maps/training/ (ep_runner 静态预检) + rel/bin/data/Maps/ (VCMI 运行时 DATA 根)
import shutil, os
OLD = "B2_KneeDeep.vmap"
NEW = "B2_adventure_knee_deep.vmap"
pairs = [
    ("/mnt/d/Bigdata/hero3_fresh/maps/training", "maps/training"),
    ("/home/administrator/vcmi-native/rel/bin/data/Maps", "rel/bin/data/Maps"),
]
for root, label in pairs:
    p_old = os.path.join(root, OLD)
    p_new = os.path.join(root, NEW)
    if os.path.exists(p_old):
        os.remove(p_old)
        print(f"[rm]  {label}/{OLD}")
    if os.path.exists(p_new):
        print(f"[ok]  {label}/{NEW} already present")
    else:
        print(f"[? ]  {label}/{NEW} missing")
# 从工具源目录重新拷 + 重命名
src = "/home/administrator/vcmi-native/tools/h3m2vmap/B2_KneeDeep.vmap"
for root, label in pairs:
    dst = os.path.join(root, NEW)
    shutil.copy2(src, dst)
    print(f"[cp]  {label}: {os.path.basename(src)} -> {NEW} ({os.path.getsize(dst)}B)")
print("=== verify ===")
for root, label in pairs:
    p = os.path.join(root, NEW)
    print(f"{label}: exists={os.path.exists(p)} size={os.path.getsize(p) if os.path.exists(p) else '-'}")
    old = os.path.join(root, OLD)
    print(f"{label}: old name exists={os.path.exists(old)} (应为 False)")
