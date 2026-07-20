# VCMI-v13 训练环境 — 最终状态 2026-07-12

## 编译产物
WS=/home/administrator/vcmi-workspace
libmlclient.so  → $WS/vcmi/rel/bin/ (15.9MB)
libvcmi.so      → $WS/vcmi/rel/bin/ (20MB)
connector_v13.so → $WS/vcmi_gym/connectors/rel/

## 最佳配置 (最终验证)
pi=[256,256] vf=[256,256] 独立双网络
n_steps=1024, n_epochs=15, vf_coef=0.5, lr=3e-4
batch_size=64, gamma=0.99, gae_lambda=0.95, clip_range=0.2
ent_coef=0.01, max_grad_norm=0.5

## 最终训练结果 (pi/vf独立双网络, 49 iter)
success_rate: 94% → 95%
ep_rew_mean: 1310 → 1350
value_loss: 1.78M → 631K (64% reduction)
loss: 892K → 271K (70% reduction)
clip_fraction: 0% → 5.1%
entropy: -3.2 → -0.99
fps: 34

## 运行命令
export LD_LIBRARY_PATH=$WS/vcmi/rel/bin:$WS/vcmi_gym/connectors/rel
export PYTHONPATH=$WS
cd $WS && ./venv/bin/python /mnt/d/Bigdata/hero3_fresh/train_loop.py

## 源码 Patch (3处)
1. vcmi/ML/MLClient.cpp: __declspec → ML_EXPORT
2. vcmi/ML/CMakeLists.txt: /DEF: → if(MSVC)
3. vcmi/CMakeLists.txt: VISIBILITY_PRESET hidden → default

## 模型
$WS/models/v13_ppo/ — 182MB/个 (独立双网络), ~2GB 总计
