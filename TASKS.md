# VCMI-v13 Anchor 训练 — 任务清单

> 最后更新: 2026-07-15 12:45 | 模型: v13_ppo 174MB | GPU: RTX3060

## 训练架构

```
train_anchor.py (编排层) → train_v13_ppo.py (执行层) → eval_orch.py (评估层)
策略: eval 胜率反馈驱动 — 弱图加重，强图减半
```

---

## 📊 上次 32 轮结果 + eval

| 地图 | 训练ev | eval胜率 | 新权重 | 
|------|--------|----------|--------|
| A1 | 0.983 | **0%** | 3→5 ↑ |
| A2 | 0.970 | **100%** | 17→8 ↓ |
| A3 | 0.526 | **90%** | 3→4 → |
| A4 | — | — | 1→2 ↑ |
| A5 | 0.964 | **0%** | 6→6 → |
| A6 | 0.953 | **0%** | 1→5 ↑ |
| A7 | — | — | 1→2 ↑ |

**关键发现**: ev ≠ 胜率 — A1/A5 训练 ev>0.95 但 0% 胜率

## 新 Schedule (32轮)

| Phase | 轮次 | 地图 | 策略 |
|-------|------|------|------|
| 1 | R1-6 | A2,A1,A5,A2,A6,A1 | 救弱图 |
| 2 | R7-12 | A5,A2,A6,A4,A1,A2 | 继续+A4 |
| 3 | R13-18 | A5,A3,A2,A6,A7,A1 | A3加强+A7 |
| 4 | R19-24 | A5,A2,A1,A6,A4,A2 | 集中攻克 |
| 5 | R25-32 | A5,A3,A2,A1,A6,A2,A7,A3 | 平衡收官 |

**权重**: A1=5 A2=8 A3=4 A4=2 A5=6 A6=5 A7=2

恢复命令:
```
wsl -d Ubuntu -- bash -c 'pkill -9 -f train; cd ~/vcmi-workspace && source venv/bin/activate && export LD_LIBRARY_PATH=$PWD/vcmi/rel/bin:$PWD/vcmi_gym/connectors/rel && exec python -u /mnt/d/Bigdata/hero3_fresh/train_anchor.py 2>&1'
```

---

## ✅ 已完成 (8/12)

1. ✅ 换训练地图 — A1-A7 全覆盖
2. ✅ 增加步数 — 215万+ 步
3. ✅ GPU 训练 — RTX3060 130fps
4. ✅ 评估脚本 — eval_orch.py
5. ✅ 多地图泛化 — 32轮
6. ✅ 修复 A4/A7 — A1 模板重建
7. ✅ 模型续训
8. ✅ eval 胜率反馈 schedule

## ⬜ 待完成

9. 导出模型 (TorchScript/ONNX)
10. 超参搜索 (Optuna)
11. GNN v15 (前置: connector 重编译)
12. 地图生成

## 执行顺序
```
✅ 32轮训练 + eval 
✅ A4/A7 修复
✅ eval 反馈 schedule
  ↓
⬜ 跑新 schedule → eval → 迭代
  ↓
⬜ 模型导出 → 实测
```
