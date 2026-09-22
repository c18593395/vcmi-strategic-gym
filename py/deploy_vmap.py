"""部署 King of Pain.vmap 到 3 处训练池副本"""
import shutil, os, sys

SRC = r"d:\Bigdata\hero3_fresh\maps\training\King of Pain.vmap"
DST_DIR = sys.argv[1]
DST = os.path.join(DST_DIR, "King of Pain.vmap")
shutil.copy(SRC, DST)
print(f"OK: {DST}  ({os.path.getsize(DST)} bytes)")
