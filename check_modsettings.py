#!/usr/bin/env python3
"""Quick check modSettings consistency across all 3 VCMI paths"""
import json, os

paths = [
    "/home/administrator/.local/share/vcmi/config/modSettings.json",
    "/home/administrator/vcmi-native/rel/bin/data/config/modSettings.json",
    "/home/administrator/vcmi-native/rel/bin/config/modSettings.json",
]

for p in paths:
    print(f"--- {os.path.basename(os.path.dirname(p))}/{os.path.basename(p)} ---")
    if os.path.exists(p):
        with open(p) as f:
            d = json.load(f)
        mods = d.get("presets", {}).get("default", {}).get("mods", [])
        print(f"  mods: {mods}")
        print(f"  full keys: {list(d.keys())}")
    else:
        print("  MISSING")
    print()
