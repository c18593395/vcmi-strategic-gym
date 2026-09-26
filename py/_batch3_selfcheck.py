#!/usr/bin/env python3
import sys, os, glob
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh/py")
import _convert_batch3_ug as c
files = sorted(glob.glob("/tmp/batch3_ug/*_ug.raw.vmap"))
print(f"{len(files)} raw files")
for f in files:
    ok, detail = c.selfcheck(f)
    print(f"{'PASS' if ok else 'FAIL':4s} {os.path.basename(f):36s} {detail}")
