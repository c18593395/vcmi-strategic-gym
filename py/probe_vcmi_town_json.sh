#!/bin/bash
# v7: dungeon.json 建筑 jsonKey
F="${F:-/home/administrator/vcmi-native/config/factions/dungeon.json}"
grep -nE '"fort"|"jsonKey"|dwelling|"name"|"special1"|"mageGuild"' "$F" | head -30
echo "=== buildings 段样例 ==="
/home/administrator/vcmi-workspace/venv/bin/python - <<'PYEOF'
import json
d = json.load(open("/home/administrator/vcmi-native/config/factions/dungeon.json"))
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("fort", "dwelling", "jsonKey") or (isinstance(v, dict) and "jsonKey" in v):
                print(path + "/" + k, "->", json.dumps(v, ensure_ascii=False)[:150])
            walk(v, path + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]")
walk(d)
PYEOF
