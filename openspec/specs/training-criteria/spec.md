# 训练判据与观测契约

## Purpose

WIN-x 观察窗的五判据聚合体系、日志信号判定规则（真信号 vs 假信号）、以及任务窗口纪律。
真相源：`docs/当前任务清单.md`（WIN 定义）、`WSL知识库.md`、`WSL踩坑点.md`。
约束对象：ep_runner_one.py proxy 判定逻辑、日志分析流程、判据聚合口径。改判定逻辑须先改本 spec。

## Requirements

### Requirement: capture 激励双拍确认
capture +100 奖励 SHALL 仅在双拍确认后发放：
- 空拍帧（battle/visit 瞬态共享内存 8 槽全 id=0）整体跳过，不参与 prev 对比
- 差集先挂账 `_kill_pending`；下一非空拍仍缺席才发 +100（日志输出 `confirmed 2 frames`）
- 空拍冻结挂账；英雄回来撤销挂账；真实击杀下一拍发放
- 禁止在 `_bnow=空集` 时以 `prev-空=全灭` 计算 +100（#146/#213 假奖根因）

#### Scenario: 空拍误报防护
- **WHEN** 战斗结束后共享内存帧为空（8 槽全 id=0）
- **THEN** 不触发 capture 判定，挂账保持冻结

#### Scenario: 真实占城发奖
- **WHEN** 连续两个非空拍均确认蓝城易主
- **THEN** 发放 capture +100，日志带 `confirmed 2 frames`

### Requirement: WIN-1 五判据口径
WIN-1 聚合 SHALL 使用以下判据（攒 ~40 局后评估）：
1. T06 TOWN_CAPTURE 触发非零（以修复后日志为准；BHERO_KILL 主日志白名单漏网 + 空拍误报 #146，弃用）
2. 守卫胜闭环 ≥80%
3. avg_r 跌幅 <20%
4. 自发经济 ≥80% 局不塌
5. 200 步截断局 ≤20%（只数 C 类退化；B 类截断 = 守卫胜+占矿后未 capture，不阻塞聚合）

#### Scenario: 判据①重新计零
- **WHEN** 修复部署后重新攒窗
- **THEN** capture 触发率短期为 0 属预期（历史上 218 次 TOWN_CAPTURE 全为空拍误报），重新非零才算真信号

### Requirement: 判定逻辑变更纪律
任何奖励判定/日志信号变更 SHALL：改代码 → 停窗 → 重启窗 → 验证标记（ZOMBIE/FUSE/ASSERT≈0）→ 重新攒窗。
runner stdout 的 [标记] 打印进 /tmp/hermes_ep_{pid}.log（非 train_loop.log）；验证主日志信号用 train_loop.log 的 ep_steps，验证 [标记] 用 runner log。

#### Scenario: 判据修复上线
- **WHEN** 修改 ep_runner_one.py proxy 判定并重启训练
- **THEN** 重启后先验证零假信号再开始攒判据窗口

## Notes

- ep_runner_one.py L134-136 对 T06 无条件覆盖 move_to_force=200/guard_done_steps=0（命令行传参无效），撤梯子须改该覆盖块
- WIN-2/WIN-3 错窗纪律与操作细则见 docs/当前任务清单.md
