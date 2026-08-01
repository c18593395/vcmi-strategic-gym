#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C8.4 BC 训练 — obs(2689) → 11 动作分类 (CrossEntropy)
网络结构与 train_wsl2_ppo_v2.py 的 Net 完全一致 (fc 2689→128→128, actor 11, critic 1),
C8.5 PPO 微调可直接加载 bc_model.pt 初始化权重。
"""
import glob
import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn

OBS_DIM = 2689
N_ACTIONS = 11


class Net(nn.Module):
    """与 train_wsl2_ppo_v2.py 完全一致 — state_dict key 必须匹配"""
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(OBS_DIM, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        self.actor, self.critic = nn.Linear(128, 11), nn.Linear(128, 1)

    def forward(self, x):
        f = self.fc(x)
        return self.actor(f), self.critic(f)


def load_data(pattern: str):
    files = sorted(glob.glob(pattern))
    assert files, f"no data files match {pattern}"
    obs_list, act_list = [], []
    for f in files:
        d = np.load(f)
        obs_list.append(d["obs"])
        act_list.append(d["actions"])
    obs = np.concatenate(obs_list).astype(np.float32)
    acts = np.concatenate(act_list).astype(np.int64)
    return obs, acts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/mnt/d/Bigdata/hero3_fresh/bc_data/bc_raw_ep*.npz")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", default="/mnt/d/Bigdata/hero3_fresh/bc_model.pt")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    obs, acts = load_data(args.data)
    print(f"data: {len(obs)} pairs  obs_nz={(obs > 0).sum(axis=1).mean():.1f}")
    uniq, cnts = np.unique(acts, return_counts=True)
    print("action 分布:", {int(k): int(v) for k, v in zip(uniq, cnts)})
    if len(obs) < 500:
        print("WARNING: 数据太少, 建议继续采集")
    if len(uniq) < 3:
        print("ERROR: 动作种类太少, 数据无效")
        sys.exit(1)

    rng = np.random.RandomState(args.seed)
    idx = rng.permutation(len(obs))
    n_val = max(200, len(idx) // 10)
    val_idx, train_idx = idx[:n_val], idx[n_val:]
    print(f"train {len(train_idx)}  val {len(val_idx)}")

    torch.manual_seed(args.seed)
    model = Net().to(args.device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    # 类权重: 少数类(END_TURN/交互)加权, 避免被方向类淹没
    counts = np.bincount(acts, minlength=N_ACTIONS).astype(np.float32) + 1.0
    w = 1.0 / counts
    w = w / w.sum() * N_ACTIONS
    ce_w = torch.tensor(w, device=args.device)
    loss_fn = nn.CrossEntropyLoss(weight=ce_w)

    best_val = 1e9
    for ep in range(args.epochs):
        perm = rng.permutation(train_idx)
        model.train()
        tl, nb = 0.0, 0
        for i in range(0, len(perm), args.batch):
            bi = perm[i:i + args.batch]
            x = torch.tensor(obs[bi], device=args.device)
            y = torch.tensor(acts[bi], device=args.device)
            logits, _ = model(x)
            loss = loss_fn(logits, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tl += loss.item()
            nb += 1
        model.eval()
        with torch.no_grad():
            xv = torch.tensor(obs[val_idx], device=args.device)
            yv = torch.tensor(acts[val_idx], device=args.device)
            logits, _ = model(xv)
            vl = loss_fn(logits, yv).item()
            acc = (logits.argmax(1) == yv).float().mean().item()
        if vl < best_val:
            best_val = vl
            torch.save(model.state_dict(), args.out)
        print(f"epoch {ep}: train_loss={tl/nb:.3f} val_loss={vl:.3f} val_acc={acc:.3f}", flush=True)

    # 最终保存 + 动作分布检查
    torch.save(model.state_dict(), args.out)
    with torch.no_grad():
        x = torch.tensor(obs[:2000], device=args.device)
        logits, _ = model(x)
        pred = logits.argmax(1).cpu().numpy()
    pu, pc = np.unique(pred, return_counts=True)
    print(f"saved {args.out}  (best_val={best_val:.3f})")
    print("模型预测分布:", {int(k): int(v) for k, v in zip(pu, pc)})


if __name__ == "__main__":
    main()
