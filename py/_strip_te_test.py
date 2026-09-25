#!/usr/bin/env python3
"""#297 实验: good_to_go 删 triggeredEvents 后试跑 (09-22)"""
import os
import json
import shutil
import sys
import zipfile

sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")

SRC = os.environ.get("SRC", "/mnt/d/Bigdata/hero3_fresh/maps/training/h3m_pool/good_to_go_h3m.vmap")
DST = os.environ.get("DST", "/home/administrator/vcmi-native/rel/bin/data/Maps/good_to_go_h3m.vmap")
with zipfile.ZipFile(SRC) as z:
    names = z.namelist()
    payload = {n: z.read(n) for n in names}

header = json.loads(payload["header.json"].decode("utf-8"))
te = header.get("triggeredEvents") or []
print(f"原 triggeredEvents: {len(te.get('conditions', []))} conditions / {len(te.get('events', []))} events" if isinstance(te, dict) else f"原 triggeredEvents: {te}")
header["triggeredEvents"] = {"conditions": [], "events": []}
payload["header.json"] = json.dumps(header, ensure_ascii=False, indent=1).encode("utf-8")

with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.writestr(n, payload[n])
print(f"已部署删事件版 → {DST}")
