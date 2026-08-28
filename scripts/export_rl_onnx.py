#!/usr/bin/env python3
"""导出 RL checkpoint (裸 state_dict, fc+CNN 双分支) → ONNX 双输入 (obs[1,3464], terrain[1,4,21,21]).
用法: python3 scripts/export_rl_onnx.py <ckpt.pt> <out.onnx>
架构必须与 train_wsl2_ppo_v2.py 的 Net 完全一致 (2026-08-29 对照源码逐行核对)。
"""
import sys
import torch
import torch.nn as nn
from torch.distributions import Categorical


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(3464, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.cnn = nn.Sequential(
            nn.Conv2d(4, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 21->10
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 10->5
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),                    # 5->5
            nn.Flatten(),                                                  # 1600
            nn.Linear(1600, 128), nn.ReLU()
        )
        self.merge = nn.Sequential(nn.Linear(256, 128), nn.ReLU())
        self.actor, self.critic = nn.Linear(128, 25), nn.Linear(128, 1)

    def forward(self, x, terrain=None):
        h_obs = self.fc(x)
        if terrain is not None:
            h_cnn = self.cnn(terrain)
            h = self.merge(torch.cat([h_obs, h_cnn], dim=-1))
        else:
            h = self.merge(torch.cat([h_obs, torch.zeros_like(h_obs)], dim=-1))
        return Categorical(logits=self.actor(h)), self.critic(h).squeeze(-1)


class Wrap(nn.Module):
    """ONNX 边界: 输出 actor_logits + critic 值 (与旧 bc_model_v3464b.onnx 接口一致)"""

    def __init__(self, net):
        super().__init__()
        self.net = net

    def forward(self, obs, terrain):
        pi, v = self.net(obs, terrain)
        return pi.logits, v


def main():
    ckpt_path, out_path = sys.argv[1], sys.argv[2]
    sd = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    net = Net()
    missing, unexpected = net.load_state_dict(sd, strict=True)
    net.eval()
    print(f"loaded {ckpt_path}: strict OK")

    w = Wrap(net).eval()
    obs = torch.randn(1, 3464)
    terrain = torch.rand(1, 4, 21, 21)  # [0,1] 模拟 /255 归一化后的输入
    torch.onnx.export(
        w, (obs, terrain), out_path,
        input_names=["obs", "terrain"],
        output_names=["actor_logits", "critic"],
        dynamic_axes=None,  # 固定 batch=1, 与 DLL 端一致
        opset_version=17,
        dynamo=False,  # P31: WSL 无 onnxscript, 必须传统导出器
    )
    print(f"exported -> {out_path}")

    # 数值对拍: torch vs onnxruntime
    try:
        import onnxruntime as ort
        import numpy as np
        sess = ort.InferenceSession(out_path, providers=["CPUExecutionProvider"])
        ol, cv = sess.run(None, {"obs": obs.numpy(), "terrain": terrain.numpy()})
        with torch.no_grad():
            pi, v = net(obs, terrain)
        dl, dv = pi.logits.numpy(), v.numpy()
        ok_l = np.allclose(ol, dl, atol=1e-4)
        ok_v = np.allclose(cv, dv.reshape(cv.shape), atol=1e-4)
        print(f"parity: logits allclose={ok_l} maxdiff={np.abs(ol-dl).max():.2e}; "
              f"critic allclose={ok_v} maxdiff={np.abs(cv-dv.reshape(cv.shape)).max():.2e}")
        print("argmax(torch)=%d argmax(onnx)=%d" % (dl.argmax(), ol.argmax()))
        if not (ok_l and ok_v):
            sys.exit(2)
    except ImportError:
        print("onnxruntime not available in WSL python — 跳过对拍 (DLL 端加载即验证)")


if __name__ == "__main__":
    main()
