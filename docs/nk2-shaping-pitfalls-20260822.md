# NK2 势函数奖励塑形 — 踩坑记录 (2026-08-22)

## 问题链

### 1. gold 被动漂移
- nk2_state_value 含 `p0.gold × 0.0005`, 每步恒定 +0.375 (城镇日收入~750)
- delta 恒定, reward=-1.125/步, 与旧奖励无异
- **修复**: 注释掉 gold 项

### 2. 资源+军力漂移
- gold 去掉后仍有 +0.236/步漂移
- 来源: wood/ore 捡拾 (0.008×) + 招募军力增长 (0.00005×)
- **修复**: 资源项全部注释; 军力保留计算(threat比率用)但不加value

### 3. step_fixed 淹没信号
- 默认 -1.5, 200步 = -300; 占矿一次才 +0.5
- **修复**: NK2 模式自动 override 到 -0.05

### 4. 构造器赋值顺序 bug
- `self.reward_step_fixed = reward_step_fixed` 在 line 535
- override 代码在 line 545 → self 已赋值, override 改的是局部变量
- **修复**: override 移到赋值前

### 5. explore 奖励被跳过
- NK2 路径在 line 980 return, 跳过了 explore 奖励
- 模型无动力移动, delta=0 时奖励全负
- **修复**: 在 return 前加 explore 计算

### 6. KL 塌缩
- KL_COEF_MIN=0.01, klc 降到 0.01~0.05
- 策略自由漂移, 高方差
- **修复**: KL_COEF_MIN=0.05

## 最终配置
```
nk2_state_value: 矿(0.5+w) + 城(2.0+income+fort) + 威罚(-2.0cap) + 胜负(±50)
step_fixed: -0.05
explore: 1.5/新格子
KL_COEF_MIN: 0.05
act_loop_penalty: 3.0 (P1=4步重复, P2=8步交替, P3=9步三阶)
```

## 教训
- 势函数必须零被动漂移, 否则恒定 delta 掩盖事件信号
- 构造器里赋值顺序: 先 override 参数, 再 self.x = param
- NK2 return 前不能跳过其他奖励分量
- pycache 必须双侧清 (Windows D: + WSL home)
