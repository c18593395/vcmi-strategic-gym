# v13 battle onnx inference verification (0908)
import os
import sys
import numpy as np
import onnxruntime as ort

MODEL = os.environ.get("MODEL", "/home/administrator/mmai-battle-test/config/MMAI/models/defender-fqcbvmti-best7.onnx")
def run():
    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(42)

    feeds = {
        "obs": (rng.standard_normal(28114) * 0.01).astype(np.float32),
        "ei_flat": np.zeros((2, 0), dtype=np.int64),
        "ea_flat": np.zeros((0, 1), dtype=np.float32),
        "lengths": np.zeros((7,), dtype=np.int32),
    }
    print("== feed shapes ==")
    for k, v in feeds.items():
        print(f"  {k}: {v.dtype} {v.shape}")

    results = sess.run(None, feeds)
    names = [o.name for o in sess.get_outputs()]
    print("== outputs ==")
    ok = True
    expect = {
        "act0_probs": (4,),
        "hex1_probs": (4, 165),
        "hex2_probs": (165, 165),
        "act0_mask": (4,),
        "hex1_mask": (4, 165),
        "hex2_mask": (165, 165),
    }
    for name, arr in zip(names, results):
        print(f"  {name}: {arr.dtype} {arr.shape} min={arr.min():.4f} max={arr.max():.4f} mean={arr.mean():.6f}")
        if tuple(arr.shape) != expect[name]:
            print(f"    !! shape mismatch vs {expect[name]}")
            ok = False
    a0 = dict(zip(names, results))["act0_probs"]
    print(f"act0_probs sum (softmax~1): {a0.sum()}")
    print("VERIFY:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    run()
