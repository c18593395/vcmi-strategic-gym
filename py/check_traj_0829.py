#!/usr/bin/env python3
# [DIAG-0829] 检查 traj_ep.json 结构与步数
import json
d = json.load(open("/tmp/traj_ep.json"))
if isinstance(d, dict):
    for k, v in d.items():
        if isinstance(v, (list, dict)):
            print(k, "len=", len(v))
        else:
            print(k, "=", v)
    if "steps" in d:
        print("STEPS =", d["steps"])
else:
    print("list len=", len(d))
    print("first item keys:", list(d[0].keys()) if d and isinstance(d[0], dict) else d[0])
