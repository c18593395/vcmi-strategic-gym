"""手动修补 King_of_Pain_h3m.vmap header.players 与 T01 对齐

King 当前:
  header.players = []  (空数组 → 引擎不创建玩家槽位 → town/hero owner=None)

修补为:
  header.players = {
    "blue": {"canPlay": "PlayerOrAI", "heroes": {"hero_0": {"type": "core:alchemist"}}},
    "red":  {"canPlay": "PlayerOrAI", "heroes": {"header_hero_1": {"type": "core:edric"}}}
  }

注:
- T01 采用 dict-of-players 格式 (blue/red), 且红方用 header_hero_1 作为"引擎自动生成"的 hero 名
- 但 King 的 objects.json 只有 1 个 hero (hero_0), 无第二 hero
- 保守方案: 红方不指定 heroes, 引擎会按 players 段自动生成默认 hero (或让红方 hero 缺席)
- 先看 T01 objects.json 里是否真有 header_hero_1 对象
"""
import json, zipfile, shutil
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

KING = BASE / "maps" / "training" / "King_of_Pain_h3m.vmap"
T01 = BASE / "maps" / "training" / "T01_adventure_36X36_01.vmap"
BACKUP = KING.with_suffix(".vmap.bak_pre_players_patch")

def read_vmap(p, inner):
    with zipfile.ZipFile(p) as z:
        return json.loads(z.read(inner).decode("utf-8", errors="replace"))

# 1. 检查 T01 objects.json 是否真有 header_hero_* 对象
t01_objs = read_vmap(T01, "objects.json")
print("===== T01 objects (前 5 项) =====")
for k in list(t01_objs.keys())[:5]:
    print(f"  {k}: type={t01_objs[k].get('type')} subtype={t01_objs[k].get('subtype')} owner={t01_objs[k].get('owner')} mask={t01_objs[k].get('mask')}")

# 检查 T01 全部 hero
print("\nT01 ALL heroes:")
for k, v in t01_objs.items():
    if v.get("type") in ("hero", "randomHero"):
        print(f"  {k}: subtype={v.get('subtype')} x={v.get('x')} y={v.get('y')}")

# 2. 检查 King objects
king_objs = read_vmap(KING, "objects.json")
print("\n===== King objects (全部 hero/town) =====")
for k, v in king_objs.items():
    if v.get("type") in ("hero", "randomHero", "town", "randomTown"):
        print(f"  {k}: type={v.get('type')} subtype={v.get('subtype')} x={v.get('x')} y={v.get('y')}")

# 3. 打印 T01 完整 header 作参考
print("\n===== T01 header.players =====")
t01_header = read_vmap(T01, "header.json")
print(json.dumps(t01_header.get("players"), indent=2, ensure_ascii=False))
