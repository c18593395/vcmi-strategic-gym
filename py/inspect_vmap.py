#!/usr/bin/env python3
"""检查 vmap 内部结构 (zip 条目 / objects.json 全量 / 地形格式) — patch 前置侦察"""
import zipfile, json, sys

p = sys.argv[1] if len(sys.argv) > 1 else "Maps/training/T03_adventure_30X30_01.vmap"
z = zipfile.ZipFile(p)
print("=== zip entries ===")
for n in z.namelist():
    print(" ", n, z.getinfo(n).file_size, "bytes")

print("\n=== objects.json (全量) ===")
objs = json.loads(z.read("objects.json"))
for k, o in objs.items():
    print(f"{k}: {json.dumps(o, ensure_ascii=False)}")

print("\n=== map.json (头部 800 字节) ===")
try:
    print(z.read("map.json").decode()[:800])
except KeyError:
    print("(no map.json)")

# 地形结构探测: 找非 objects/map 的 json 条目打印键名
for n in z.namelist():
    if n.endswith(".json") and n not in ("objects.json", "map.json"):
        try:
            data = json.loads(z.read(n))
            print(f"\n=== {n} 键结构 ===")
            if isinstance(data, dict):
                for kk, vv in list(data.items())[:6]:
                    s = json.dumps(vv, ensure_ascii=False)
                    print(f"  {kk}: {s[:200]}")
            elif isinstance(data, list):
                print(f"  list[{len(data)}] 首元素: {json.dumps(data[0], ensure_ascii=False)[:200]}")
        except Exception as e:
            print(f"  {n}: parse err {e}")
