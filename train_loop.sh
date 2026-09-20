#!/bin/bash
# 24/7 战略层 PPO 训练循环
# 轮换 H3M 地图，断点续训，进程守护

set -e

WORKSPACE=/home/administrator/vcmi-workspace
VENV=$WORKSPACE/venv/bin/python
TRAINER_V1=/mnt/d/Bigdata/hero3_fresh/py/train_wsl2_ppo.py
TRAINER_V2=/mnt/d/Bigdata/hero3_fresh/py/train_wsl2_ppo_v2.py
LOG=/mnt/d/Bigdata/hero3_fresh/train_loop.log
V2_FLAG=/mnt/d/Bigdata/hero3_fresh/.use_v2

# 选择版本（Round 2 完成后通过 cron 创建 .use_v2 flag 自动切换）
TRAINER=$TRAINER_V1
if [ -f "$V2_FLAG" ]; then
    TRAINER=$TRAINER_V2
fi

export LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-native/rel/bin/AI:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel
export STRATEGIC_STATE_LIB=/home/administrator/vcmi-native/rel/bin/libmlclient.so

# 清 pyc 缓存
find /mnt/d/Bigdata/hero3_fresh -path "*/__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "=== HoMM3 Strategic PPO 24/7 Loop ===" | tee -a $LOG
echo "Start: $(date)" | tee -a $LOG

ROUND=0
while true; do
    ROUND=$((ROUND + 1))
    echo "" | tee -a $LOG
    echo "=== ROUND $ROUND | $(date) | $(basename $TRAINER) ===" | tee -a $LOG
    
    cd $WORKSPACE
    $VENV -u $TRAINER 2>&1 | tee -a $LOG
    RC=${PIPESTATUS[0]}
    
    if [ $RC -eq 0 ]; then
        echo "Round $ROUND completed successfully" | tee -a $LOG
    else
        echo "Round $ROUND exited with code $RC, restarting in 5s..." | tee -a $LOG
        sleep 5
    fi
    
    # 僵尸清理
    pkill -9 -f vcmiserver 2>/dev/null || true
    pkill -9 -f ep_runner_one 2>/dev/null || true
    sleep 2
done
