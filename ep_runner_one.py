import sys, os, json, argparse
os.environ["STRATEGIC_STATE_LIB"] = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
sys.path.insert(0, "/mnt/d/Bigdata/hero3_fresh")
import torch, torch.nn as nn
from torch.distributions import Categorical
from vcmi_gym.envs.v13.strategic_env import StrategicEnv

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(264,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,11), nn.Linear(128,1)
    def forward(self, x):
        h = self.fc(x)
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)

parser = argparse.ArgumentParser()
parser.add_argument("max_turns", nargs="?", type=int, default=10)
parser.add_argument("outfile", nargs="?", type=str, default="/tmp/traj_one.json")
parser.add_argument("mapname", nargs="?", type=str, default="Key to Victory.h3m")
parser.add_argument("--model", type=str, default=None,
                    help="Path to red model checkpoint (uses model policy instead of random)")
parser.add_argument("--blue_model", type=str, default=None,
                    help="Path to blue model checkpoint")
parser.add_argument("--blue_ai", type=str, default=None,
                    help="AI type for blue player (MMAI_USER, StupidAI, etc.)")
args = parser.parse_args()

# Load red model if provided
red_model = None
if args.model and os.path.exists(args.model):
    red_model = Net()
    red_model.eval()
    try:
        sd = torch.load(args.model, map_location="cpu", weights_only=True)
        red_model.load_state_dict(sd)
    except:
        try:
            sd = torch.load(args.model, map_location="cpu", weights_only=False)
            if "model" in sd:
                red_model.load_state_dict(sd["model"])
            else:
                red_model.load_state_dict(sd)
        except:
            red_model = None

# --blue_model: use ML model as blue (MMAI_MODEL triggers model inference in C++)
blue = "MMAI_USER"
if args.blue_model:
    blue = "MMAI_MODEL"
    os.environ["ML_MODEL_PATH"] = args.blue_model
# --blue_ai: directly override blue AI type (takes precedence)
if args.blue_ai:
    blue = args.blue_ai

traj = {"obs": [], "act": [], "rew": [], "nobs": [], "done": [], "steps": 0, "total_rew": 0.0}
try:
    env = StrategicEnv(
        mapname=args.mapname, max_turns=args.max_turns,
        vcmi_loglevel_global="error", vcmi_loglevel_ai="error",
        vcmienv_loglevel="ERROR", red="MMAI_USER", blue=blue,
        random_heroes=1, boot_timeout=60, vcmi_timeout=15,
        red_model_path=args.model or "",
        blue_model_path=args.blue_model or "",
    )
    obs, _ = env.reset()
    for _ in range(args.max_turns):
        if red_model is not None:
            with torch.no_grad():
                obs_t = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
                pi, _ = red_model(obs_t)
                # Passability mask: obs[-8:] = 8方向可通行性
                passable = torch.tensor(obs[-8:], dtype=torch.bool)
                logits = pi.logits[0].clone()
                if passable.any():
                    logits[:8][~passable] = float('-inf')  # 非法方向概率归零
                    a = Categorical(logits=logits).sample().item()
                else:
                    a = 10  # 全堵→END_TURN
        else:
            a = int(env.action_space.sample())
        nobs, r, done, trunc, _ = env.step(a)
        # 非法方向惩扣：move 后英雄位置没变（服务器拒绝），给 -0.5
        if a < 8 and traj["steps"] > 0:
            prev_pos = (int(traj["obs"][-1][106]), int(traj["obs"][-1][107]))
            cur_pos = (int(nobs[106]), int(nobs[107]))
            if prev_pos == cur_pos:
                r = -0.5
        traj["obs"].append(obs.tolist())
        traj["act"].append(a)
        traj["rew"].append(float(r))
        traj["nobs"].append(nobs.tolist())
        traj["done"].append(bool(done or trunc))
        traj["steps"] += 1
        traj["total_rew"] = sum(traj["rew"])
        # 每步增量写入：进程崩溃也能保留已收集的数据
        with open(args.outfile, "w") as f:
            json.dump(traj, f); f.flush(); os.fsync(f.fileno())
        obs = nobs
        if done or trunc: break
        if args.model and traj["steps"] >= args.max_turns:
            break
except Exception as e:
    traj["error"] = str(e)
    # 即使异常也写一次（segfault 无法被 Python 捕获，但 OSError/Timeout 等可以）
    try:
        with open(args.outfile, "w") as f:
            json.dump(traj, f); f.flush(); os.fsync(f.fileno())
    except: pass

# 最终写入（正常退出时覆盖，确保完整数据）
with open(args.outfile, "w") as f:
    json.dump(traj, f); f.flush(); os.fsync(f.fileno())
os._exit(0)
