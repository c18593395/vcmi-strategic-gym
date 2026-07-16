#!/usr/bin/env python3
"""Fix VCMI modSettings: ensure ML, mmai included"""
import json, sys

cfg_path = sys.argv[1]

with open(cfg_path) as f:
    cfg = json.load(f)

preset = cfg["presets"]["default"]
old = preset["mods"]
print(f"Old mods: {old}")

# Required mods for adventure mode
required = ["vcmi", "core", "ML", "mmai"]
new = []
for m in required:
    if m not in new:
        new.append(m)
# Preserve any extra mods
for m in old:
    if m not in new and m not in ["ml", "roe"]:
        new.append(m)

preset["mods"] = new
print(f"New mods: {new}")

with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
print(f"Written to {cfg_path}")
