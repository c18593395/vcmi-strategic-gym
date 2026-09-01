# WSL知识库 — 训练状态

> 本文件是 `WSL知识库.md` 总索引下的稳定参考子文档（当前训练参数与环境搭建/部署）。
> 结论性内容，按需就地修订；内容截至 2026-08-29。

---

## 一、训练参数



### 当前训练（C4）



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



### 观测向量结构 (256 维)



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



