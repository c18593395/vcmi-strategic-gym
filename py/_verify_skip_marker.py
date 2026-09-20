#!/usr/bin/env python3
"""验证 _pool_index skip 标记生效"""
import json, sys

POOL_INDEX = "/mnt/d/Bigdata/hero3_fresh/maps/h3m_to_vmap/_pool_index.json"
idx = json.load(open(POOL_INDEX, encoding="utf-8"))

skip_names = set()
for vn, e in idx.items():
    if isinstance(e, dict) and e.get("blue_ai") == "skip":
        skip_names.add(vn)

print(f"skip 条目数: {len(skip_names)}")
for vn in sorted(skip_names):
    e = idx[vn]
    print(f"  {vn}")
    print(f"    reason: {e.get('reason', '?')}")
    print(f"    detail: {e.get('detail', '?')[:100]}")
    print()

# 模拟 pipeline main() 的跳过逻辑
final_name = "a_warm_and_familiar_place_h3m.vmap"
in_skip = final_name in skip_names
print(f"验证 {final_name} 在 skip 列表: {in_skip}")
if not in_skip:
    print("  [FAIL] 未找到!")
    sys.exit(1)
print("  [OK] 标记生效，pipeline 遇到此图将 STRUCTURAL_SKIP")
