"""深挖 King vmap vs L1 vs T01 header 差异"""
import json, zipfile
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

def read_json_from_vmap(p, inner):
    with zipfile.ZipFile(p) as z:
        return json.loads(z.read(inner).decode("utf-8", errors="replace"))

def dump(tag, name):
    p = BASE / "maps" / "training" / name
    print(f"\n========== {tag} : {name} ==========")
    with zipfile.ZipFile(p) as z:
        print(f"zip entries: {z.namelist()}")
        header = json.loads(z.read("header.json").decode("utf-8", errors="replace"))
        print(f"header keys: {list(header.keys())}")
        print(f"header: {json.dumps(header, indent=2, ensure_ascii=False)[:1200]}")
    # 找第一个 town / hero 详细字段
    objs = read_json_from_vmap(p, "objects.json")
    if isinstance(objs, dict):
        vals = list(objs.values())
    else:
        vals = objs
    for o in vals:
        if o.get("type") in ("town","hero","randomTown","randomHero"):
            print(f"\n[obj] id={o.get('id')} type={o.get('type')} x={o.get('x')} y={o.get('y')} owner={o.get('owner')} mask={o.get('mask')}")
            print(f"     subtype={o.get('subtype')} formation={o.get('formation')}")
            # 完整 keys
            print(f"     keys: {list(o.keys())}")
            break

dump("KING", "King_of_Pain_h3m.vmap")
dump("L1_36", "L1_adventure_36X36_01.vmap")
dump("T01_36", "T01_adventure_36X36_01.vmap")
dump("T06_108", "T06_adventure_108X108_01.vmap")
