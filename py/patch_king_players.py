"""修补 King_of_Pain_h3m.vmap - v2

修补内容:
1. header.players: [] → {blue, red} dict-of-players 格式 (与 T01 对齐)
2. town_1 (x=10, y=8) owner: red → blue  (给蓝方家城)
3. hero_0 (x=10, y=8) owner: red → blue  (让蓝方 hero 从蓝家出发)
   hero_0 保持 subtype=core:alchemist 不动 (与 T01 一致)

原始 owner 分布 (King 5 town + 1 hero):
  town_0 (4,62)  orange
  town_1 (10,8)  red    → blue    ← 蓝方家
  town_2 (65,64) blue   (原本就是蓝, 保留)
  town_3 (40,52) None   (中性, 保留)
  town_4 (54,28) None   (中性, 保留)
  hero_0 (10,8)  red    → blue    ← 蓝方主控 hero

修补后:
- Blue: 2 town (town_1+town_2) + 1 hero (hero_0)
- Red: 0 town + 0 hero  (玩家槽存在但空槽, 引擎会按默认生成)
- Neutral: 2 town (town_3, town_4) + 1 town (town_0 orange)

注: Red 方无 hero 也不阻塞训练, AI 只跑蓝方 (player 0)。
    Red 空槽让 header.players 完整保留 1v1 语义, 引擎正常创建玩家索引。
"""
import json, zipfile, shutil
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

KING = BASE / "maps" / "training" / "King_of_Pain_h3m.vmap"
BACKUP = KING.with_suffix(".vmap.bak_players_patch")
TMP = KING.with_suffix(".vmap.tmp")

NEW_PLAYERS = {
    "blue": {
        "canPlay": "PlayerOrAI",
        "heroes": {"header_hero_0": {"type": "core:iona"}}
    },
    "red": {
        "canPlay": "PlayerOrAI",
        "heroes": {"header_hero_1": {"type": "core:edric"}}
    }
}

def main():
    if not BACKUP.exists():
        shutil.copy2(KING, BACKUP)
        print(f"BACKUP created: {BACKUP}")
    else:
        print(f"BACKUP exists (skip): {BACKUP}")

    with zipfile.ZipFile(KING, "r") as zin, zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "header.json":
                header = json.loads(data.decode("utf-8", errors="replace"))
                old_players = header.get("players")
                header["players"] = NEW_PLAYERS
                if isinstance(header.get("mods"), list) and len(header.get("mods")) == 0:
                    header["mods"] = {}
                data = json.dumps(header, indent=2, ensure_ascii=False).encode("utf-8")
                print(f"\n[header.json]")
                print(f"  players BEFORE: {old_players}")
                print(f"  players AFTER : {NEW_PLAYERS}")
            elif item.filename == "objects.json":
                objs = json.loads(data.decode("utf-8", errors="replace"))
                # town_1 → blue (蓝方家)
                t1 = objs.get("town_1")
                if t1:
                    old = t1["options"].get("owner")
                    t1["options"]["owner"] = "blue"
                    print(f"\n[objects.json] town_1 ({t1['x']},{t1['y']}): owner {old!r} → 'blue'")
                # hero_0 → blue (蓝方主控)
                h0 = objs.get("hero_0")
                if h0:
                    old = h0["options"].get("owner")
                    h0["options"]["owner"] = "blue"
                    print(f"[objects.json] hero_0 ({h0['x']},{h0['y']}): owner {old!r} → 'blue'")
                print(f"\n  FINAL owner 分布:")
                for k, v in objs.items():
                    if v.get("type") in ("town", "hero", "randomTown", "randomHero"):
                        print(f"    {k:>10} type={v.get('type'):5s} ({v.get('x'):>3},{v.get('y'):>3}) owner={v.get('options',{}).get('owner')!r}")
                data = json.dumps(objs, indent=2, ensure_ascii=False).encode("utf-8")
            zout.writestr(item, data)

    TMP.replace(KING)
    print(f"\nPATCHED: {KING}")

    # 验证
    print("\n===== 验证 =====")
    with zipfile.ZipFile(KING) as z:
        h = json.loads(z.read("header.json").decode("utf-8", errors="replace"))
        print(f"players: {json.dumps(h.get('players'), indent=2, ensure_ascii=False)}")
        print(f"mods: {h.get('mods')}")
        print(f"mapLevels: {h.get('mapLevels')}")
        objs = json.loads(z.read("objects.json").decode("utf-8", errors="replace"))
        print(f"objects total: {len(objs)}")
        for k, v in objs.items():
            if v.get("type") in ("town", "hero"):
                print(f"  {k:>10} type={v.get('type'):5s} x={v.get('x'):>3} y={v.get('y'):>3} owner={v.get('options',{}).get('owner')!r}")

    # 字节数
    new_size = KING.stat().st_size
    bak_size = BACKUP.stat().st_size
    print(f"\n  文件尺寸: backup={bak_size} bytes, patched={new_size} bytes, diff={new_size-bak_size:+d}")

if __name__ == "__main__":
    main()
