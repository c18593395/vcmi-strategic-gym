import sys, os
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
os.environ["PYTHONPATH"] = "/mnt/d/Bigdata/hero3_fresh"

import numpy as np

# Direct file read test
fpath = "/home/administrator/vcmi-workspace/terrain_grid.bin"
if os.path.exists(fpath):
    raw = np.fromfile(fpath, dtype=np.uint8, count=1764)
    print(f"Direct file read: shape={raw.shape} nonz={np.count_nonzero(raw)}")
    print(f"First 20: {list(raw[:20])}")
    hwc = raw.reshape(21, 21, 4)
    chw = hwc.transpose(2, 0, 1).astype(np.float32) / 255.0
    print(f"CHW shape={chw.shape} range=[{chw.min():.4f}, {chw.max():.4f}]")
    print(f"Center (10,10) C0={chw[0,10,10]:.4f} C1={chw[1,10,10]:.4f}")
    # Check what terrain type center has
    print(f"Center raw: {[hwc[10,10,c] for c in range(4)]}")
else:
    print(f"File not found: {fpath}")
