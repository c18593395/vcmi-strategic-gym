"""对比 T01 town 与 King town 的完整字段"""
import json, zipfile
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

def read(p):
    with zipfile.ZipFile(BASE / "maps/training" / p) as z:
        return json.loads(z.read("objects.json").decode("utf-8", errors="replace"))

print("===== T01 town_0 完整 =====")
t01 = read("T01_adventure_36X36_01.vmap")
print(json.dumps(t01["town_0"], indent=2, ensure_ascii=False))

print("\n===== King town_0 完整 =====")
king = read("King_of_Pain_h3m.vmap")
print(json.dumps(king["town_0"], indent=2, ensure_ascii=False))

print("\n===== King hero_0 完整 =====")
print(json.dumps(king["hero_0"], indent=2, ensure_ascii=False))

print("\n===== T01 hero_0 完整 =====")
print(json.dumps(t01["hero_0"], indent=2, ensure_ascii=False))
