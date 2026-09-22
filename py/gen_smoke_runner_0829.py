# [DIAG-0829] 生成训练同款冒烟 runner: 拷贝 ep_runner_one.py 并把 .so 路径指向 diag 版
src = "/mnt/d/Bigdata/hero3_fresh/py/ep_runner_one.py"
dst = "/tmp/smoke_ep_runner.py"
with open(src) as f:
    lines = f.readlines()
hit = 0
for i, l in enumerate(lines):
    if "STRATEGIC_STATE_LIB" in l:
        lines[i] = 'os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/rel-diag-bin/libmlclient.so"\n'
        hit += 1
assert hit == 1, f"expected 1 hit, got {hit}"
with open(dst, "w") as f:
    f.writelines(lines)
print("GEN_OK ->", dst)
