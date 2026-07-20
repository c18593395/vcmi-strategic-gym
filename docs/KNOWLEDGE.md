# VCMI Gym WSL2 训练 — 知识总结

## 环境架构

```
Python (SB3 PPO) → connector_v13.so (pybind11)
                 → libmlclient.so → libvcmi.so → libMMAI.so
                 → HoMM3 引擎 → 战场结算 → 观测返回
```

## 编译踩坑 (3个必需 Patch)

### 1. __declspec(dllexport) 不兼容 GCC
文件：ML/MLClient.cpp
问题：Windows 专有关键字，Linux GCC 不识别
修复：添加跨平台宏 ML_EXPORT
```c
#if defined(_WIN32) || defined(_MSC_VER)
  #define ML_EXPORT __declspec(dllexport)
#else
  #define ML_EXPORT __attribute__((visibility("default")))
#endif
```

### 2. /DEF: 链接标志 MSVC-Only
文件：ML/CMakeLists.txt
问题：/DEF: 是 MSVC linker 专用，ld 不识别
修复：if(MSVC) 条件包裹

### 3. CMAKE_CXX_VISIBILITY_PRESET hidden → default
文件：CMakeLists.txt
问题：hidden 导致跨 .so 的 dynamic_cast 失败
症状：`dynamic cast to V13::BAI failed`
修复：set(CMAKE_CXX_VISIBILITY_PRESET default)
注意：改后必须删 CMakeCache.txt 全量重编，增量编译不会检测 flag 变化

## 运行踩坑

### 1. WSL2 PATH 污染
问题：Windows PATH 含空格/括号 (`Program Files (x86)`) 传入 WSL 导致 bash 语法错误
修复：wsl 命令中使用纯 Linux PATH，不用 $PATH 扩展

### 2. WSL2 9p 文件系统极慢
问题：/mnt/d 源码上 cmake 卡死
修复：源码复制到 WSL 原生 ext4 (~/vcmi-native) 后再编译

### 3. 多 apt 进程死锁
问题：多个后台进程同时 sudo apt-get，锁文件冲突
修复：wsl --terminate Ubuntu 重启 + 单进程操作

### 4. VCMI 退出 segfault
问题：env.close() 时 VCMI C++ 线程 dump core
修复：训练脚本结尾 os._exit(0) 强制退出，模型由 callback 预先保存

### 5. VCMI 单实例限制
问题：同进程不能创建第二个 VCMI 实例，评估阶段崩溃
修复：去掉训练脚本内的评估，单独跑评估脚本

### 6. WSL2 内存不足 (20核并行)
问题：-j20 编译时每个 cc1plus 600MB，8GB 内存 OOM
修复：-j4 限制并行数

## 观测空间适配

v13 新版返回 Dict 观测，SB3 不支持嵌套 Dict：
```python
class FlattenV13Obs(gym.Wrapper):
    def reset(self): obs_dict, info = self.env.reset(); return obs_dict["observation"], info
    def step(self, action): obs_dict, rew, term, trunc, info = self.env.step(action); return obs_dict["observation"], rew, term, trunc, info
```

## 训练超参调优结论

| 改动 | 效果 | 结论 |
|------|------|------|
| vf_coef 0.5→1.0 | loss×2, policy_grad÷3 | ❌ 值函数权重过大挤占策略学习 |
| n_steps 512→1024 | clip 首次激活, 胜率微升 | ✅ 更长 rollout 改善 advantage 估计 |
| net_arch [64,64]→[256,256] | value_loss -60%, loss -53% | ✅ 架构扩容是核心瓶颈 |
| 共享→独立双网络 | entropy -70%, 胜率 95% | ✅ 消除 actor/critic 梯度干扰 |

## 最终配置

```python
MaskablePPO(MaskableActorCriticPolicy, env,
    policy_kwargs=dict(net_arch=dict(pi=[256,256], vf=[256,256])),
    learning_rate=3e-4, n_steps=1024, batch_size=64, n_epochs=15,
    gamma=0.99, gae_lambda=0.95, clip_range=0.2,
    ent_coef=0.01, vf_coef=0.5, max_grad_norm=0.5)
```

## 已知限制

1. v14/v15 connector 死锁 — 仅 v13 可用
2. WSL2 无 GPU 透传 (torch.cuda=False)
3. explained_variance 始终≈0 — VCMI 短 episode 稀疏奖励的度量误差，不影响实际 value_loss 收敛
4. 单进程单 VCMI 实例 — 无法并行多环境
