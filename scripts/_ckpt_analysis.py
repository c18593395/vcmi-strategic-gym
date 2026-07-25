#!/usr/bin/env python3
"""Compare model parameters across checkpoints to see training evolution."""
import torch, os, glob, json

CKPT_DIR = "/mnt/d/Bigdata/hero3_fresh/checkpoints"
BEST_MODEL = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"

# Get all checkpoints sorted by step number
ckpts = sorted(
    glob.glob(os.path.join(CKPT_DIR, "wsl2_ckpt_*.pt")),
    key=lambda f: int(os.path.basename(f).replace("wsl2_ckpt_", "").replace(".pt", ""))
)

print(f"Found {len(ckpts)} checkpoints")

# Compare parameters of first, middle, and last checkpoint
samples = [ckpts[0], ckpts[len(ckpts)//2], ckpts[-1], BEST_MODEL]
names = ["earliest", "mid", "latest_ckpt", "best_model"]

def analyze_sd(sd):
    stats = {}
    for k, v in sd.items():
        stats[k] = {
            "shape": list(v.shape),
            "mean": float(v.mean().item()),
            "std": float(v.std().item()),
            "min": float(v.min().item()),
            "max": float(v.max().item()),
            "norm": float(v.norm().item()),
        }
    return stats

print(f"\n{'='*80}")
print(f"{'Layer':<30} {'Earliest mean':>12} {'Latest mean':>12} {'Best mean':>12} {'Change':>12}")
print(f"{'='*80}")

results = []
for path, name in zip(samples, names):
    sd = torch.load(path, map_location="cpu", weights_only=True) if os.path.exists(path) else None
    results.append((name, sd))

earliest_sd = results[0][1]
for k in earliest_sd.keys():
    e_mean = earliest_sd[k].mean().item()
    l_val = results[2][1][k] if results[2][1] else None
    b_val = results[3][1][k] if results[3][1] else None
    
    if l_val is not None:
        l_mean = l_val.mean().item()
        b_mean = b_val.mean().item() if b_val is not None else 0
        change = l_mean - e_mean
        print(f"{k:<30} {e_mean:>12.4f} {l_mean:>12.4f} {b_mean:>12.4f} {change:>+12.4f}")

print(f"\n{'='*80}")
print(f"Parameter norm comparison:")
for name, sd in results:
    if sd is not None:
        total_norm = sum(float(v.norm().item()**2) for v in sd.values())**0.5
        n_params = sum(v.numel() for v in sd.values())
        print(f"  {name:<20} params={n_params:,}  total_norm={total_norm:.2f}")

# Best model details
if results[3][1]:
    bsd = results[3][1]
    print(f"\n{'='*80}")
    print(f"Best model layer stats ({BEST_MODEL}):")
    for k, v in bsd.items():
        print(f"  {k:<30} shape={list(v.shape)}  mean={v.mean():.4f}  std={v.std():.4f}  norm={v.norm():.2f}")
