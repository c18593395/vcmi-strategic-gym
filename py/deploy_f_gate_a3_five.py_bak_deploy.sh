#!/bin/bash
# A3 五修 09-23 部署脚本: 中立守卫 F 闸扩展 + 比例公式 (log_margin=0.5/temp=0.5)
# 用法: wsl -u root bash /mnt/d/Bigdata/hero3_fresh/py/deploy_f_gate_a3_five.py_bak_deploy.sh
# 前置: 训练已 stop (wsl -u root systemctl stop homm3-train-v5)
# 回退: bash 同文件第二参数 rollback (git revert 本改动)
set -e
cd /mnt/d/Bigdata/hero3_fresh

CMD="${1:-deploy}"

if [ "$CMD" = "rollback" ]; then
    echo "=== 回退 A3 五修 (git revert + 重启) ==="
    cd /mnt/d/Bigdata/hero3_fresh
    git revert HEAD --no-edit   # 回退最近 commit (A3 五修)
    # 清 __pycache__ 后重启
    find /mnt/d/Bigdata/hero3_fresh/py -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    systemctl restart homm3-train-v5
    sleep 5
    systemctl is-active homm3-train-v5
    exit 0
fi

echo "=== 部署 A3 五修 ==="
# 0. 确认训练已停
ACTIVE=$(systemctl is-active homm3-train-v5 2>/dev/null || echo inactive)
if [ "$ACTIVE" = "active" ]; then
    echo "训练仍 active, 先 stop..."
    systemctl stop homm3-train-v5
    sleep 3
fi
echo "训练状态: $(systemctl is-active homm3-train-v5 || echo inactive)"

# 1. 清 __pycache__
find /mnt/d/Bigdata/hero3_fresh/py -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
echo "__pycache__ 已清"

# 2. 语法校验
/home/administrator/vcmi-workspace/venv/bin/python -m py_compile \
    py/target_scorer.py \
    py/ep_runner_one.py \
    py/train_wsl2_ppo_v2.py
echo "py_compile PASS"

# 3. 启动训练 (checkpoint resume)
systemctl start homm3-train-v5
sleep 8
echo "=== 部署完成, 训练状态: $(systemctl is-active homm3-train-v5) ==="
echo "首局验证: 等 [EP_TIME] 出现, 检查 [SCORE] pick F 值分布 (比例公式下 F 应在 [-0.3,+1] 区间)"
echo "  战死局应减少 (英雄弱时 F<-0.3 剔除中立守卫)"
echo "  蓝英雄入池应增加 (英雄强时 F>-0.1 放行蓝英雄)"
echo "监控: Get-Content /mnt/d/Bigdata/hero3_fresh/train_loop.log -Tail 30 -Wait"
echo "如需回退: wsl -u root bash py/deploy_f_gate_a3_five.py_bak_deploy.sh rollback"
