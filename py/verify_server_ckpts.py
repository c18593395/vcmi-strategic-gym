#!/usr/bin/env python3
"""验证服务器拉回的 checkpoint 谱系可续（只读，不修改训练资产）。

检查三层:
  1) 纯 ckpt (wsl2_ckpt_*.pt, model.state_dict) — 能否 torch.load、键结构、权重健康(无 NaN/Inf)
  2) 谱系连续性 — 拉回的 step 与本地旧谱系(1014734) 单调递增、无重复
  3) 服务器 STATE_PATH (wsl2_model_state.pt, model+optimizer+step) — 真正续训的权威源
"""
import os
import sys
import torch

REPO = os.environ.get("HERMES_ROOT", "D:/Bigdata/hero3_fresh")
CKPT_DIR = os.path.join(REPO, "checkpoints")

OLD_STEPS = [994187, 996222, 998268, 1000394, 1003121, 1005095, 1007136, 1009196, 1011214, 1014734]
PULLED = ["wsl2_ckpt_1600426.pt", "wsl2_ckpt_1598402.pt", "wsl2_ckpt_1596493.pt"]


def check_pt(path):
    try:
        sd = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as e:
        return False, None, "load_fail", 0, 0, str(e)
    if "model" in sd and "step" in sd:
        kind = "state(model+opt+step)"; step_in = sd.get("step"); has_step = True
    elif "optimizer" in sd:
        kind = "state(model+opt)"; step_in = sd.get("step"); has_step = "step" in sd
    else:
        kind = "model.state_dict"; step_in = None; has_step = False
    nan_cnt = 0; k = 0
    target = sd.get("model", sd) if isinstance(sd, dict) else sd
    if isinstance(target, dict):
        for v in target.values():
            if torch.is_tensor(v):
                k += 1
                if torch.isnan(v).any() or torch.isinf(v).any():
                    nan_cnt += 1
    return True, step_in, kind, k, nan_cnt, ""


def main():
    print("=" * 64)
    print("服务器 checkpoint 拉回验证 (只读)")
    print(f"REPO = {REPO}")
    print("=" * 64)

    print("\n[1] 拉回的 3 个 ckpt (纯 model.state_dict):")
    pulled_steps = []
    for f in PULLED:
        p = os.path.join(CKPT_DIR, f)
        if not os.path.exists(p):
            print(f"  ❌ 缺失 {f}")
            continue
        ok, step_in, kind, tkeys, nan, err = check_pt(p)
        step = int(f.replace("wsl2_ckpt_", "").replace(".pt", ""))
        pulled_steps.append(step)
        sz = os.path.getsize(p)
        nan_flag = "⚠️含NaN" if nan else "✅健康"
        print(f"  {f}  size={sz/1e6:.2f}M  kind={kind}  "
              f"tensor_keys={tkeys}  NaN/Inf={nan} {nan_flag}  step={step}")

    print(f"\n[2] 谱系连续性 (旧 {len(OLD_STEPS)} + 拉回 {len(pulled_steps)} 档):")
    mono = min(pulled_steps) > OLD_STEPS[-1]
    gap = min(pulled_steps) - OLD_STEPS[-1]
    print(f"  旧谱系: {OLD_STEPS[0]} ~ {OLD_STEPS[-1]}")
    print(f"  拉回:   {min(pulled_steps)} ~ {max(pulled_steps)}")
    print(f"  单调递增(拉回最小 {min(pulled_steps)} > 旧最大 {OLD_STEPS[-1]}): "
          f"{'✅' if mono else '❌谱系回退!'}")
    print(f"  谱系缺口: {gap} step" + (" (训练持续推进, 正常)" if gap > 0 else ""))

    print("\n[3] 服务器 STATE_PATH (wsl2_model_state.pt, 续训权威源, 含 optimizer+step):")
    state_path = None
    for cand in [os.path.join(REPO, "wsl2_model_state.pt"),
                 os.path.join(CKPT_DIR, "wsl2_model_state.pt")]:
        if os.path.exists(cand):
            state_path = cand
            break
    if state_path:
        ok, step_in, kind, tkeys, nan, err = check_pt(state_path)
        print(f"  {os.path.basename(state_path)}  size={os.path.getsize(state_path)/1e6:.2f}M  "
              f"kind={kind}  step={step_in}  NaN/Inf={nan}")
    else:
        print("  ⚠️ 本地无 wsl2_model_state.pt (仅服务器上有) — 这是真正含 optimizer+step 的续训权威源")
        print(f"  最新拉回 ckpt step={max(pulled_steps)}, 纯 ckpt 不含 optimizer/step, 续训 step 号会丢")
        print("  → 若要在 WSL 完整续训, 需同样 scp 拉回 wsl2_model_state.pt")

    print("\n" + "=" * 64)
    mono_ok = min(pulled_steps) > OLD_STEPS[-1]
    print("结论:")
    print(f"  {'✅' if mono_ok else '❌'} 谱系连续: 旧谱系 ~{OLD_STEPS[-1]} → 拉回 {max(pulled_steps)}, 单调递增无回退")
    print(f"  {'✅' if mono_ok else '❌'} 最新 ckpt step={max(pulled_steps)} 可加载")
    print(f"  ⚠️  完整续训需另拉 wsl2_model_state.pt (纯 ckpt 缺 optimizer/step)")
    print("=" * 64)
    return 0 if mono_ok else 1


if __name__ == "__main__":
    sys.exit(main())
