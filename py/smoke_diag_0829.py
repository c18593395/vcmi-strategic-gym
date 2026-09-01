# [DIAG-0829] P1 冒烟测试: 用 rel-diag-bin 的插桩 libmlclient.so 跑 1 个短局,
# 捕获 [MMAI-DIAG] 阶段日志, 定位 08-26 重编崩溃 (start_vcmi 未调→GAME null) 卡死点
# 运行: /home/administrator/vcmi-workspace/venv/bin/python py/smoke_diag_0829.py
import sys, os
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/rel-diag-bin/libmlclient.so"  # 必须在 import 前
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
print("[SMOKE] STRATEGIC_STATE_LIB =", os.environ["STRATEGIC_STATE_LIB"], flush=True)
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

mapname = "T03_adventure_20X20_01.vmap"  # 相对名 — VCMI 资源系统按名搜索, 不认绝对路径 (08-29 冒烟教训)
print(f"[SMOKE] map: {mapname}", flush=True)
try:
    env = StrategicEnv(
        mapname=mapname,
        max_turns=3,
        vcmi_loglevel_global="error",
        vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR",
        red="MMAI_USER",          # 训练同款: red=RL 侧
        blue="MMAI_RANDOM",       # 训练同款: blue=随机对手
        blue_adventure_ai="MMAI",
        random_heroes=1,
        boot_timeout=60,
        vcmi_timeout=120,
    )
    obs, _ = env.reset()
    print(f"[SMOKE] Reset OK, obs shape: {obs.shape}", flush=True)
    for i in range(3):
        obs, r, term, trunc, info = env.step(0)
        print(f"[SMOKE] step{i} r={r} term={term} trunc={trunc}", flush=True)
        if term or trunc:
            break
    env.close()
    print("[SMOKE] Test passed!", flush=True)
except Exception as e:
    print(f"[SMOKE] Error: {e}", flush=True)
finally:
    print("[SMOKE] done", flush=True)
