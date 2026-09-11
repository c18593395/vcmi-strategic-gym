# WSL知识库 — 训练状态

> 本文件是 `WSL知识库.md` 总索引下的稳定参考子文档（当前训练参数与环境搭建/部署）。
> 结论性内容，按需就地修订；内容截至 2026-08-29。

---

## 一、训练参数



### 当前训练（C4, 历史）



| 参数 | 值 |

|---|---|

| 算法 | PPO |

| 网络 | MLP: 256→128→128→11(actor)/1(critic) |

| Episodes | 2000 |

| Steps/ep | 50 |

| Batch | 128 |

| 学习率 | 3e-4 |

| Clip | 0.2 |

| Epochs | 4 |

| 设备 | cuda (RTX3060) |

| 地图 | 110 张 H3M |

| 对手池 | 70%当前 / 20%早期 / 10%随机 |

| Checkpoint | 每 200 step, 保留 10 个 |

| 模型 | ~203KB (.pt) |




### 当前训练（v5, 截至 2026-09-11 晚 T7.4 上线后）

| 参数 | 值 |
|------|-----|
| 脚本 | train_wsl2_ppo_v2.py |
| 算法 | PPO |
| 网络 | MLP: 3464→256→128→25(act+crit) |
| Episodes | 1000 |
| Steps/ep | 200 |
| Batch | 2048 |
| 学习率 | 3e-4 |
| Clip | 0.2 |
| Epochs | 6 |
| KL_TARGET | 0.50 |
| KL_COEF | 0.3 |
| Entropy | -0.05 |
| 设备 | cuda (RTX3060) |
| 地图 | T05 6图 + T06 duel + 72X72_01 (共8图) |
| 对手 | blue=MMAI_RANDOM |
| NK2 shaping | 0.45 |
| objective_reward | 30 (矿/城事件) |
| move_to_force | 60 |
| economy_force | 24 |
| reward clip | ±300 |
| Checkpoint | 每 50 step, 保留 10 个 |
| OBS_DIM | 3464 |
| N_ACTIONS | 25 (0-24, 25-63 预留) |
| **T7.4 death_penalty** | **-50 (红英雄死亡帧追加, 全局生效, argparse 可调含 0=关闭; 09-11 晚上线, checkpoint step=637994 续训)** |

**T7.4 死亡惩罚 (09-11 上线, 观察期中)**:
- 落点: ep_runner_one.py zombie 确认点 (zombie_streak>=2 块) — `r += args.death_penalty; traj["rewards"][-1] += args.death_penalty; traj["done"][-1]=True`
- 日志: `[HERO_DEATH] penalty -50 [ZOMBIE] hero dead (all-blocked xN), end ep at step N` 进主日志白名单 (train_wsl2_ppo_v2.py L194)
- 语义: 红英雄死 (zombie) → -50; 蓝英雄死 (capture proxy) → +100; 两事件不同帧, 无同帧双罚 (方案_T74 §6 复核)
- 全局生效不按图分支: T04/T05/T06 统一
- 回退线: 接战率塌 >30% 或 avg_r 跌 >20% → 降档 -25 或 0 关闭
- 观察判据 (1-2 窗): 死亡局 r 转负 / [GUARD] 接战率不塌 (±20%) / avg_r 跌幅 <20%
- 09-11 晚首窗 11 局: 0 次 HERO_DEATH 触发 (T05 52X52 全守卫胜局, 无英雄死亡), avg_r=2.20 (基线 2.34, 跌 6%, 远低于 20% 回退线), [GUARD] 接战正常 — 判据 2/3 暂不触发, 判据 1 待死亡局出现

**训练运行方式**: WSL2 systemd **system 级 enabled unit `homm3-train-v5`** (0911 重构, 容器冷启动自动拉训练; 旧 transient/user 级已废弃), 优雅停止 = 零损失。运维: `wsl -u root systemctl restart/status homm3-train-v5`; 验证存活看 PID etime + 日志 mtime, 别只信 is-active (踩坑 #201)。
**训练日志**: `train_loop.log`
**健康判据**: r 双峰 — 130-160(守卫胜) / 5-30(只招兵), 均健康
**分析日志**: 先按 ROUND 头切片, batch 行 ~27 局 1 条属正常
**runner 标记**: [GUARD]/[ZOMBIE] 进 `/tmp/hermes_ep_{pid}.log` 不进主日志

**NK2+超参全表**: batch2048/LR3e-4/KL_TARGET0.5/KL_COEF0.3/entropy-0.05/move_to_force60/
objective_reward30/economy_force24/reward_clip±300; 全表见 vcmi-rl-training refs/。

**NK2死锁修复链 (08-16/17)**: 详见 vcmi-ml-module refs/deadlock-chain+battle-query-hang;
close卡死→SAVED后os._exit; 采集bash wrapper逐局独立; 采集/训练前必验npz英雄位置+动作分布

### 观测向量结构 (3464 维)

| 索引 | 内容 | 长度 |
|------|------|------|
| 0-25 | Global + Player state | 26 |
| 26-127 | Heroes (6 × 16字段) | 102 |
| 128-473 | Towns (8 × 43字段) | 346 |
| 474-480 | 填充/特殊字段 | 7 |
| 336-480 | Towns 段 (含 garrison 填充, 09-02) | 145 |
| 3464 | 总维度 | 3464 |



| 索引 | 内容 | 长度 |

|------|------|------|

| 0-7 | Global (day/week/month/player/map) | 8 |

| 8-103 | Players (8 × 12字段) | 96 |

| 104-241 | Heroes (6 × 23字段) | 138 |

| 242-255 | 填充零 | 14 |



### 动作空间 (11)



| ID | 动作 |

|----|------|

| 0-7 | 8 方向移动 |

| 8 | 交互（拾取/对话/攻击） |

| 9 | 下一英雄 |

| 10 | 结束回合 |



---



## 二、环境搭建



### WSL2 VCMI 编译



```bash

# 三件套同源编译（必须！）

cd ~/vcmi-native

cmake .. -DENABLE_ML=ON -DENABLE_MMAI=ON -DENABLE_NULLKILLER2_AI=ON

cmake --build . --target vcmi -j4

cmake --build . --target mlclient -j4



# Connector 编译（需 schema 同步：v14/v15 从本地 vcmi 复制）

# 新版 libmlclient 用 1-param init_vcmi(void*)，connector 适配

cp -r /mnt/d/.../vcmi/AI/MMAI/schema/v{14,15} ~/vcmi-native/AI/MMAI/schema/

cd /mnt/d/Bigdata/hero3_fresh/vcmi_gym/connectors/build

cmake .. && cmake --build . --target connector_v13 -j4

cmake --build . --target connector_v14 -j4

cmake --build . --target connector_v15 -j4



# 部署（备份旧 .so + 复制新 .so）

cp rel/*.so rel/*.so.bak.$(date +%Y%m%d)

cp build/connector_v*.so rel/



# 环境变量

export LD_LIBRARY_PATH=~/vcmi-native/rel/bin:~/vcmi-workspace/vcmi_gym/connectors/rel

export STRATEGIC_STATE_LIB=~/vcmi-native/rel/bin/libmlclient.so

```



### Connector 版本说明



| 版本 | 观测编码 | 返回类型 | adventure | 当前使用 |

|------|---------|---------|-----------|---------|

| v13 | 固定 264 维数组 | P_State | ✅ | **当前训练** |

| v14 | 同 v13（参数更细） | P_State | ❌ | 未使用 |

| v15 | 图结构（nodes+links） | py::dict | ❌ | Phase G 前迁移 |



### 启动训练



```bash

# 清 pyc

find /mnt/d/Bigdata/hero3_fresh -path "*/__pycache__" -type d -exec rm -rf {} +



# 24/7 循环

MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/train_loop.sh 2>&1 &



# 查看状态

MSYS_NO_PATHCONV=1 wsl -d Ubuntu -- bash /mnt/d/Bigdata/hero3_fresh/check_training.sh

```



---



