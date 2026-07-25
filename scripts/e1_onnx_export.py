#!/usr/bin/env python3
"""E1: ONNX 模型导出 — .pt → .onnx"""
import torch, torch.nn as nn, os

DEVICE = "cpu"
MODEL_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.pt"
ONNX_PATH = "/mnt/d/Bigdata/hero3_fresh/wsl2_model.onnx"

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(256,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.actor, self.critic = nn.Linear(128,11), nn.Linear(128,1)

    def forward(self, x):
        h = self.fc(x)
        return self.actor(h), self.critic(h).squeeze(-1)

# Load
model = Net().to(DEVICE)
model.eval()
sd = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
model.load_state_dict(sd)
print(f"Loaded: {MODEL_PATH}")

# Export
x = torch.randn(1, 256, dtype=torch.float32)  # batch=1, obs_dim=256
torch.onnx.export(
    model, x, ONNX_PATH,
    input_names=["obs"],
    output_names=["action_logits", "value"],
    dynamic_axes={"obs": {0: "batch"}},
    opset_version=17,
)
print(f"Exported: {ONNX_PATH}")
print(f"Size: {os.path.getsize(ONNX_PATH)} bytes")

# Verify
import onnxruntime as ort
sess = ort.InferenceSession(ONNX_PATH, providers=["CPUExecutionProvider"])
out = sess.run(None, {"obs": x.numpy()})
print(f"ONNX Runtime verify OK:")
print(f"  action_logits shape={out[0].shape}  sample={out[0][0][:5]}")
print(f"  value shape={out[1].shape}  value={out[1][0][0]:.4f}")

# Verify consistency with PyTorch
with torch.no_grad():
    pt_logits, pt_value = model(x)
print(f"PyTorch match:")
print(f"  logits diff max: {(out[0] - pt_logits.numpy()).max():.6f}")
print(f"  value diff max:  {(out[1] - pt_value.numpy()).max():.6f}")
