# [DIAG-0829] 生成对照版 runner: 用部署版 (rel/bin) libmlclient
src = "/mnt/d/Bigdata/hero3_fresh/ep_runner_one.py"
dst = "/tmp/smoke_ep_runner_ctrl.py"
with open(src) as f:
    lines = f.readlines()
hit = 0
for i, l in enumerate(lines):
    if "STRATEGIC_STATE_LIB" in l:
        # 保持指向部署版 rel/bin (对照), 只确保路径一致
        lines[i] = 'os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"\n'
        hit += 1
assert hit == 1, f"expected 1 hit, got {hit}"
with open(dst, "w") as f:
    f.writelines(lines)
print("GEN_OK ->", dst)
