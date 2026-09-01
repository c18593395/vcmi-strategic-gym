#!/usr/bin/env bash
# OPS-20260828-01 启动前备份 + 验证断点 step 值
set -e
cd /mnt/d/Bigdata/hero3_fresh
STAMP=$(date +%Y%m%d_%H%M%S)
echo "STAMP=$STAMP"

# 备份训练状态与模型
cp -f wsl2_model_state.pt "wsl2_model_state.pt.bak_OPS2026082801_$STAMP"
cp -f wsl2_model.pt       "wsl2_model.pt.bak_OPS2026082801_$STAMP"
ls -la "wsl2_model_state.pt.bak_OPS2026082801_$STAMP" "wsl2_model.pt.bak_OPS2026082801_$STAMP"

# 验证 checkpoint 内 step 值 (无需 GPU, 在 CPU 上读)
export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so
export PYTHONPATH=/mnt/d/Bigdata/hero3_fresh
/home/administrator/vcmi-workspace/venv/bin/python3 - <<'PY'
import torch
p = "/mnt/d/Bigdata/hero3_fresh/wsl2_model_state.pt"
sd = torch.load(p, map_location="cpu")
keys = list(sd.keys())
print("keys_top =", keys[:12])
print("step =", sd.get("step"))
print("best_vloss =", sd.get("best_vloss"))
# ep_count 也打印一下，如果有保存
for k in ("ep_count", "last_ckpt_step", "kl_coef"):
    if k in sd:
        print(f"{k} =", sd[k])
PY
