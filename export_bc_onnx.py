#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出 bc_model_v3464b.pt → onnx (Track 2 部署用, ModelAI.dll onnxruntime 加载)"""
import sys, torch, torch.nn as nn

OBS_DIM = 3464
N_ACTIONS = 25

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(OBS_DIM, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.actor, self.critic = nn.Linear(128, 25), nn.Linear(128, 1)

    def forward(self, x):
        f = self.fc(x)
        return self.actor(f), self.critic(f)

def main():
    ckpt = sys.argv[1] if len(sys.argv) > 1 else "bc_model_v3464b.pt"
    out = sys.argv[2] if len(sys.argv) > 2 else "bc_model_v3464b.onnx"
    net = Net()
    sd = torch.load(ckpt, map_location="cpu")
    # state_dict 可能带 net. 前缀 (PPO) 或裸 key (BC)
    if any(k.startswith("net.") for k in sd):
        sd = {k[4:]: v for k, v in sd.items() if k.startswith("net.")}
    net.load_state_dict(sd)
    net.eval()
    x = torch.randn(1, OBS_DIM)
    with torch.no_grad():
        a, c = net(x)
    print(f"check output: actor[0][:5]={a[0][:5].tolist()}, critic={c.item():.4f}")
    torch.onnx.export(
        net, (x,), out,
        input_names=["obs"], output_names=["actor_logits", "critic"],
        opset_version=13,
        dynamic_axes={"obs": {0: "batch"}},
        dynamo=False,  # legacy exporter, 不依赖 onnxscript
    )
    print(f"exported: {out}")

if __name__ == "__main__":
    main()
