"""探查训练地图的 victory/specialVictory 字段结构。"""
import json
import zipfile
from pathlib import Path

BASE = Path(r"D:\Bigdata\hero3_fresh\maps\training")
SAMPLES = [
    "T05_adventure_36X36_01.vmap",
    "T06_adventure_72X72_02.vmap",
    "T05_adventure_52X52_01_mir.vmap",
    "B2_adventure_knee_deep.vmap",
    "L1_adventure_20X20_01.vmap",
]

for name in SAMPLES:
    p = BASE / name
    if not p.exists():
        print(f"[skip] {name}")
        continue
    print(f"\n=== {name} ===")
    with zipfile.ZipFile(p) as z:
        h = json.loads(z.read("header.json"))
        # 只挑出与 victory/trigger/condition 相关的字段
        for k, v in h.items():
            kl = k.lower()
            if any(s in kl for s in ("victor", "trigger", "condition", "special", "end", "event")):
                s = json.dumps(v, ensure_ascii=False)
                if len(s) > 400:
                    s = s[:400] + "..."
                print(f"  {k}: {s}")
