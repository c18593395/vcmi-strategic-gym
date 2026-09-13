"""批量修补 4 张 T06 _02 系 VMAP: header.players=[] → {blue,red} + mods=[] → {}

与 King patch 差异:
- 对象本身完整 (town/hero owner 已正确分配 red/blue), 只改 header
- King 是 5 玩家 H3M 图需改 owner, 这 4 张是标准 1v1/1v3 生成图

修改内容:
1. header.json:
   - players: [] → {blue:{canPlay:'PlayerOrAI',heroes:{...}}, red:{...}}
   - mods:    [] → {}
2. objects.json: 完全不动

备份后缀: .vmap.bak_players_patch
"""
import json, zipfile, shutil
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

MAPS = BASE / "maps" / "training"

TARGETS = [
    "T06_adventure_72X72_02_duel.vmap",     # ← 训练 MAPS 名单 L64
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_108X108_02_duel.vmap",
    "T06_adventure_108X108_02.vmap",
]

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


def patch_one(name):
    vmap = MAPS / name
    backup = vmap.with_suffix(".vmap.bak_players_patch")
    tmp = vmap.with_suffix(".vmap.tmp")
    if not vmap.exists():
        print(f"❌ {name} 不存在")
        return False
    if not backup.exists():
        shutil.copy2(vmap, backup)
        print(f"  备份: {backup.name}")
    else:
        print(f"  备份已存在")

    with zipfile.ZipFile(vmap, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "header.json":
                h = json.loads(data.decode("utf-8", errors="replace"))
                print(f"  players: {h.get('players')} → {list(NEW_PLAYERS.keys())}")
                print(f"  mods    : {h.get('mods')} → {{}}")
                h["players"] = NEW_PLAYERS
                h["mods"] = {}
                data = json.dumps(h, indent=2, ensure_ascii=False).encode("utf-8")
            zout.writestr(item, data)
    tmp.replace(vmap)

    # 验证
    with zipfile.ZipFile(vmap) as z:
        h = json.loads(z.read("header.json").decode("utf-8", errors="replace"))
        assert isinstance(h.get("players"), dict) and len(h["players"]) == 2, "players 修补失败"
        assert h.get("mods") == {}, "mods 修补失败"
        objs = json.loads(z.read("objects.json").decode("utf-8", errors="replace"))
        towns = [(k, v.get("x"), v.get("y"), v.get("options", {}).get("owner")) for k, v in objs.items() if v.get("type") == "town"]
        heroes = [(k, v.get("x"), v.get("y"), v.get("options", {}).get("owner")) for k, v in objs.items() if v.get("type") == "hero"]
        print(f"  对象不变: towns={len(towns)} heroes={len(heroes)} (与修补前一致)")

    size = vmap.stat().st_size
    bak_size = backup.stat().st_size
    print(f"  尺寸: {bak_size} → {size} ({size-bak_size:+d})")
    return True


def main():
    print(f"批量修补 {len(TARGETS)} 张 T06 _02 系 VMAP\n")
    ok = 0
    for name in TARGETS:
        print(f"\n=== {name} ===")
        try:
            if patch_one(name):
                ok += 1
                print("  ✅ OK")
            else:
                print("  ❌ FAIL")
        except Exception as e:
            print(f"  ❌ ERR: {e}")
    print(f"\n结果: {ok}/{len(TARGETS)} 修补成功")


if __name__ == "__main__":
    main()
