import os, sys, time, subprocess, json

WS = "/home/administrator/vcmi-workspace"
MAPS = [f"gym/A{i}.vmap" for i in range(1, 8)]
RESULT_DIR = f"{WS}/models/v13_ppo/eval_results"
os.makedirs(RESULT_DIR, exist_ok=True)
VENV = f"{WS}/venv/bin/python"
WORKER = "/mnt/d/Bigdata/hero3_fresh/eval_worker.py"

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = f"{WS}/vcmi/rel/bin:{WS}/vcmi_gym/connectors/rel"

print(f"VCMI-v13 Eval | {len(MAPS)} maps x 100 ep")
print("=" * 60)

all_results = []
t0 = time.time()

for m in MAPS:
    t1 = time.time()
    out_file = f"{RESULT_DIR}/{m.replace('/', '_')}.json"
    print(f"\n--- {m} ---", flush=True)
    
    try:
        ret = subprocess.run(
            [VENV, WORKER, m, "100", out_file],
            env=env, cwd=WS, timeout=1200, capture_output=True, text=True
        )
    except subprocess.TimeoutExpired:
        print("  TIMEOUT")
        continue
    
    elapsed = time.time() - t1
    print(f"  time={elapsed:.0f}s exit={ret.returncode}")
    for line in ret.stdout.strip().split("\n"):
        if line.strip():
            print(f"  {line}")
    if ret.stderr.strip():
        print(f"  STDERR: {ret.stderr.strip()[:200]}")
    
    if os.path.exists(out_file):
        with open(out_file) as f:
            all_results.append(json.load(f))

total = time.time() - t0
print(f"\nSUMMARY ({total/60:.1f}min)")
print(f"{'Map':<15} {'Win%':>8} {'AvgRew':>10} {'AvgLen':>8}")
print("-" * 45)
for r in all_results:
    print(f"{r['map']:<15} {r['win_rate']:>7.1%} {r['avg_reward']:>10.0f} {r['avg_len']:>8.1f}")
if all_results:
    avg = sum(r["win_rate"] for r in all_results) / len(all_results)
    print(f"{'AVERAGE':<15} {avg:>7.1%}")
