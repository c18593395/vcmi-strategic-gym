# -*- coding: utf-8 -*-
"""诊断: rl_model_v5_0911.onnx (3464/25 双输入) 动作分布是否健康 (对比旧模型恒 argmax=5)
obs 布局按 vcmi_gym/envs/v13/strategic_env.py::_strategic_state_to_obs 权威表构造模拟输入
"""
import numpy as np
import onnxruntime as ort

MODEL = r"D:\Bigdata\hero3_fresh\rl_model_v5_0911.onnx"
sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
i_obs = sess.get_inputs()[0].name   # obs [1,3464]
i_ter = sess.get_inputs()[1].name   # terrain [1,4,21,21]
onames = [o.name for o in sess.get_outputs()]
print(f"in: {[(x.name, x.shape) for x in sess.get_inputs()]} outs={onames}")

rng = np.random.default_rng(42)
ACT_NAME = {**{i: ["N","NE","E","SE","S","SW","W","NW"][i] for i in range(8)},
            8: "INTERACT", 9: "NEXT_HERO", 10: "END_TURN"}
def aname(a): return ACT_NAME.get(a, f"ADV{a}")

def run(obs, terrain):
    outs = sess.run(None, {i_obs: obs, i_ter: terrain})
    logits = outs[0].reshape(-1)
    return logits

def mock_obs(seed, day=11, active_p=1):
    """按 3464 权威布局构造结构化模拟 obs (合理值域, 已归一化段用归一化值)"""
    g = np.random.default_rng(seed)
    obs = np.zeros((1, 3464), dtype=np.float32)
    # global 8
    obs[0, :8] = [day, (day-1)//7+1, 1, active_p, 36, 36, 0, 8]
    # players 8x15 @8: gold/total_power/weekly_income 已 log1p
    for pi in range(8):
        b = 8 + pi*15
        obs[0, b+0] = pi; obs[0, b+1] = 0 if pi == 0 else 1
        obs[0, b+2] = g.uniform(5, 12)            # gold ~ log1p(150..16万)
        obs[0, b+3] = g.uniform(0, 15)            # wood
        obs[0, b+9] = g.integers(0, 3)            # hero_count
        obs[0, b+10] = g.integers(0, 2)           # town_count
        obs[0, b+11] = 1                          # alive
        obs[0, b+12] = g.uniform(3, 12)           # total_power log1p
        obs[0, b+13] = g.uniform(4, 12)           # weekly_income log1p
        obs[0, b+14] = 2 if pi == active_p else 0 # relation
    # heroes 8x26 @128
    for hi in range(3):
        b = 128 + hi*26
        obs[0, b+0] = hi+1; obs[0, b+1] = active_p
        obs[0, b+2] = g.uniform(5, 31); obs[0, b+3] = g.uniform(5, 31); obs[0, b+4] = 0
        obs[0, b+5] = g.uniform(0, 7.5); obs[0, b+6] = 7.3   # movement/max log1p
        obs[0, b+7] = 1                                       # level
        for k in range(7): obs[0, b+15+k] = g.integers(0, 40) # army
        obs[0, b+22] = g.uniform(2, 11)                       # total_power log1p
    # towns 8x18 @336
    for ti in range(2):
        b = 336 + ti*18
        obs[0, b+0] = ti+1; obs[0, b+1] = active_p
        obs[0, b+2] = g.uniform(5, 31); obs[0, b+3] = g.uniform(5, 31)
        obs[0, b+6:b+13] = g.integers(0, 30, 7)               # garrison
        obs[0, b+15] = 0.1; obs[0, b+16] = g.uniform(0, 1)    # build/recruit mask /2^31
        obs[0, b+17] = g.uniform(0, 1)
    # local window 15x15x3 @480: ch0 可通行 0/1, ch1 对象类型, ch2 守卫
    obs[0, 480:655] = g.integers(0, 2, 175)                   # ch0
    obs[0, 655:830] = g.integers(0, 8, 175)                   # ch1
    obs[0, 830:1005] = g.integers(0, 40, 175)                 # ch2
    obs[0, 1005:1155] = 1                                     # ch2 剩余
    # global explored 32x32x2 @1155
    obs[0, 1155:2179] = g.integers(0, 2, 1024)
    obs[0, 2179:3203] = g.integers(0, 2, 1024)
    obs[0, 3203] = 0                                          # active_hero
    obs[0, 3211:3219] = [1,1,1,0,1,1,0,1]                     # passable 8 方向
    obs[0, 3330:3338] = [6,-1,3,-1,2,-1,-1,1]                 # reserved[0..7] next_dir
    return obs

def mock_terrain(seed):
    return rng.random((1, 4, 21, 21)).astype(np.float32)

z28 = np.zeros((1, 3464), dtype=np.float32)
z_ter = np.zeros((1, 4, 21, 21), dtype=np.float32)
r_ter = rng.random((1, 4, 21, 21)).astype(np.float32)

print("\n=== 随机 obs x8 ===")
acts = []
for i in range(8):
    o = rng.normal(0, 1, (1, 3464)).astype(np.float32)
    lg = run(o, r_ter)
    a = int(lg.argmax()); acts.append(a)
    print(f"#{i} argmax={a}({aname(a)}) top3={np.argsort(-lg)[:3].tolist()}")
print(f"多样性: {len(set(acts))}/8")

print("\n=== 特殊 obs (零 terrain) ===")
for tag, o in [("zeros", z28), ("ones", np.ones((1, 3464), np.float32))]:
    lg = run(o, z_ter)
    print(f"{tag}: argmax={int(lg.argmax())}({aname(int(lg.argmax()))}) top3={np.argsort(-lg)[:3].tolist()}")

print("\n=== 模拟真实 obs x16 (day 6-21, active_p 1-7, terrain 随机/零) ===")
acts = []
i = 0
for day in (6, 11, 16, 21):
    for p in (1, 4, 7):
        for ter, tn in [(mock_terrain(i), "rnd"), (z_ter, "zero")]:
            o = mock_obs(100+i, day, p)
            lg = run(o, ter)
            a = int(lg.argmax()); acts.append(a)
            print(f"day={day:2d} p={p} ter={tn:4s} argmax={a:2d}({aname(a):9s}) top3={np.argsort(-lg)[:3].tolist()} logits5={lg[5]:.2f} max={lg.max():.2f}")
            i += 1
print(f"\n多样性: {len(set(acts))}/18, 分布={ {a: acts.count(a) for a in sorted(set(acts))} }")
