# mq-4 诊断探针: rl_model_v5_0911.onnx 喂多样化输入, 检查 argmax 是否恒 5
# 判定: 恒5=模型本身策略坍塌(回训练线); 多样化=C++侧obs构造问题
import numpy as np
import onnxruntime as ort

MODEL = r"D:/Bigdata/hero3_fresh/rl_model_v5_0911.onnx"
OBS_DIM, GRID_CH, GRID_SIZE = 3464, 4, 21

sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
print("== inputs ==")
for i in sess.get_inputs():
    print(f"  {i.name}: {i.shape}")
print("== outputs ==")
for o in sess.get_outputs():
    print(f"  {o.name}: {o.shape}")

def run(obs, terrain, tag):
    feeds = {}
    for i in sess.get_inputs():
        n = i.name.lower()
        if "terrain" in n:
            feeds[i.name] = terrain.astype(np.float32)
        else:
            feeds[i.name] = obs.astype(np.float32)
    outs = sess.run(None, feeds)
    # 找 actor logits 输出
    logits = None
    for name, arr in zip([o.name for o in sess.get_outputs()], outs):
        if "actor" in name.lower():
            logits = arr
    if logits is None:
        logits = outs[0]
    logits = np.asarray(logits).flatten()
    am = int(np.argmax(logits))
    top5 = np.argsort(-logits)[:5]
    print(f"[{tag}] argmax={am}  top5=" +
          " ".join(f"{int(a)}:{logits[a]:+.2f}" for a in top5) +
          f"  logit_std={logits.std():.4f}")
    return am

rng = np.random.default_rng(42)
terrain0 = np.zeros((1, GRID_CH, GRID_SIZE, GRID_SIZE), dtype=np.float32)
terrain1 = np.full((1, GRID_CH, GRID_SIZE, GRID_SIZE), 0.5, dtype=np.float32)

# 1) 全零 obs
am = run(np.zeros((1, OBS_DIM), np.float32), terrain0, "zeros")
# 2) 模拟真实 obs: 按训练布局填值 (day=9, player block, hero block, local grid 有地形)
obs = np.zeros((1, OBS_DIM), np.float32)
obs[0, 0] = 9.0            # day
obs[0, 8 + 15 * 1 + 2] = np.log1p(3000)   # players[1] gold
obs[0, 128 + 26 * 1 + 5] = np.log1p(1500) # heroes[1] mp
obs[0, 3211:3251] = 1.0    # nav 相关置 1 附近
obs[0, 3315:3322] = 0.3    # target_list
obs[0, 3350:3400] = 0.7    # local 区间扰动
run(obs, terrain1, "structured")
# 3) 随机噪声 obs x5
for k in range(5):
    r = rng.random((1, OBS_DIM), dtype=np.float32)
    run(r, terrain1, f"rand{k}")
# 4) 真实量级 obs (激活值范围 0~5 随机)
for k in range(3):
    r = (rng.random((1, OBS_DIM), dtype=np.float32) * 5.0)
    run(r, terrain1, f"rand5x{k}")

print("== 判定: 若以上 argmax 全为 5 → 模型策略坍塌, 根因在训练侧 checkpoint ==")
