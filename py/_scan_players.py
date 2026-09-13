"""扫描 maps/training/ 下所有 VMAP 的 header.players 状态"""
import json, zipfile
from pathlib import Path

BASE = Path("/mnt/d/Bigdata/hero3_fresh")
if not BASE.exists():
    BASE = Path(r"D:\Bigdata\hero3_fresh")

MAPS = BASE / "maps" / "training"
vmaps = sorted(MAPS.glob("*.vmap"))
print(f"扫描 {len(vmaps)} 个 .vmap\n")

ok, empty, other = [], [], []
for v in vmaps:
    try:
        with zipfile.ZipFile(v) as z:
            h = json.loads(z.read("header.json").decode("utf-8", errors="replace"))
        p = h.get("players")
        if isinstance(p, dict) and len(p) > 0:
            ok.append((v.name, sorted(p.keys())))
        elif p == []:
            empty.append(v.name)
        else:
            other.append((v.name, repr(p)[:80]))
    except Exception as e:
        other.append((v.name, f"ERR:{e}"))

print(f"✅ players OK (dict 非空): {len(ok)}")
for n, ks in ok:
    print(f"   {n:<45s} players={ks}")

print(f"\n❌ players = [] (空数组，需 patch): {len(empty)}")
for n in empty:
    print(f"   {n}")

print(f"\n⚠️ 其他状态: {len(other)}")
for n, s in other:
    print(f"   {n:<45s} {s}")
