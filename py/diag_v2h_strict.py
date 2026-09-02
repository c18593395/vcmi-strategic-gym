#!/usr/bin/env python3
"""strict 逐对象定位 vmap2h3m 产物与 h3m_tool reader 的字节漂移点"""
import sys

sys.path.insert(0, '/mnt/d/Bigdata/hero3_fresh/scripts')
import h3m_tool  # noqa: E402

for path in sys.argv[1:]:
    print(f"== {path}")
    try:
        res = h3m_tool.parse_objects(path, tolerant=False)
        print(f"   strict OK: {res['obj_count']} objects, templates={len(res['templates'])}")
    except Exception as e:  # noqa: BLE001
        print(f"   strict FAIL @ {type(e).__name__}: {e}")
