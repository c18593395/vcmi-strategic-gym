# 知识库 — HoMM3 全盘操盘 AI

> 单文件知识总汇：项目概述、架构决策、踩坑记录、环境搭建、参数索引
> 最后更新：2026-07-29

---

## 一、项目概述

**目标：** AI 完整操控 HoMM3 真实游戏，与你对战（1v7），并战胜你。

**策略：** VCMI 沙盒训练战略模型，真实游戏内存操控，自对弈持续进化。

**当前阶段：** Phase C7 完成 + passability mask 落地 + Connector 适配完成(N2)，4 张开放 H3M 地图训练中（WSL2, RTX3060, PPO 自对弈）

---

## 二、双轨并行架构

```
| Track 1: 训练, 持续提升模型强度, WSL2 GPU 后台跑, 不占交互注意力
| Track 2: 真实游戏对齐, 模型落地到真实 HoMM3, Windows 内存读取验证, 需主动执行
```

---

## 三、关键技术决策

### 3.1 两段式设计

```
训练端 (WSL2):  vcmi-workspace, MMAI ON, RTX 3060
推理端 (ARM64):  root@172.16.2.40, 不需要 callback, ctypes 直读状态 + ONNX 推理
部署端 (真实游戏): 本机 HD Mod, 内存读取 + PostMessage, 模型推理
```

### 3.2 为什么放弃 ARM64 训练

**根因：** headless=true 下 VCMI networkHandler->createTimer() 不触发，游戏不进首回合。
**尝试过：** ctypes->connector 迁移、DummyVecEnv 短路、MLClient 注入 mainLoop、Xvfb —— 全部失败。

### 3.3 为什么不走内存读写

1. 通过 VCMI 引擎接口直接获取状态和动作，比逆向 HoMM3 内存格式稳定百倍
2. VCMI 接口 ABI 相对稳定
3. VCMI 可 headless（无 GUI 渲染），内存读写必须渲染窗口

---

## 四、项目文件结构

```
/mnt/d/Bigdata/hero3_fresh/          项目根（Windows 侧）
  docs/                               文档
  vcmi_gym/                           VCMI Gym 强化学习环境
    envs/v13/strategic_env.py          环境入口
    connectors/v13/threadconnector.cpp 主连接器
  train_wsl2_ppo_v2.py                 PPO 训练入口

/home/administrator/vcmi-native/       VCMI 源码树（ext4）
/home/administrator/vcmi-native-build/ VCMI 编译树（ext4）
  rel/bin/
    libmlclient.so, libvcmi.so         核心库
    AI/libMMAI.so, libStupidAI.so      AI 库
    AI/libBattleAI.so                  战斗 AI 库
    libmlserverplugin.so               ML 服务器插件
    vcmiserver, vcmiclient             可执行文件
    data/                              游戏数据（必须真实目录）
  config/                              VCMI 配置
/home/administrator/vcmi-workspace/    训练运行时
```

---

## 五、开机修复总结（2026-07-29）

### 5.1 修复清单

| # | 问题 | 修复方法 | 状态 |
|---|------|---------|------|
| 1 | CMakeCache 旧 VCMI_DIR | 删 Cache 重建 connector | 完成 |
| 2 | MLClient.cpp 回退 | 从 build 树恢复 | 完成 |
| 3 | Schema 分歧 | 同步 BATTLE_ROUND | 完成 |
| 4 | init_vcmi 线程问题 | init/start 拆分 | 完成 |
| 5 | EEXIST | real data/ 目录 | 完成 |
| 6 | JSON 空配置 | 写入有效内容 | 完成 |
| 7 | libMMAI.so 符号 | 补 ctor/dtor | 完成 |
| 8 | Mods 损坏 | 从 git 恢复 | 完成 |
| 9 | data symlink 错误 | 重建真实目录 | 完成 |
| 10 | libmlclient/vcmi 重建 | cmake --target mlclient | 完成 |
| **11** | **#46 segfault** | **已定位，待修复** | **诊断中** |

### 5.2 阻塞 #46: env.reset() segfault — 定位更新

**原先误判：** 以为在 ServerPlugin 构造器（"Grouped heroes" 消息后）。实际 ServerPlugin 构造一切正常。

**实际崩溃点：** `installNewBattleInterface` → 为 **neutral（中立）玩家初始化战斗回调**时 segfault。

**VCMI 日志时间线：**
```
[ai] INFO    +++ constructor +++               ← AAI 构造 OK
[ai] INFO    *** initGameInterface ***          ← 回调初始化 OK
[global] TRACE Initializing the interface for player tan  ← 初始玩家
[global] INFO  Opening BattleAI                ← 加载 BattleAI
[global] INFO  Loaded Battle AI                ← BattleAI 加载完成
[global] TRACE Initializing the battle interface for player neutral  ← 崩！
```

**推测根因：**
- `libBattleAI.so` 的 `CBattleAI::initBattleInterface()` 在初始化中立玩家时收到无效参数
- 或 `aiCombatOptions` 结构体有非法值导致 crash
- 或 `cbc`（battle callback）为 null

**下一步：**
- 在 `CBattleAI::initBattleInterface()` 加日志确认
- 或检查 `installNewBattleInterface` 传入参数

---

## 六、常见操作

### 6.1 编译 MMAI
```bash
cd /home/administrator/vcmi-native-build
cmake --build rel --target MMAI -- -j4
cp rel/bin/AI/libMMAI.so /home/administrator/vcmi-native/rel/bin/AI/
```

### 6.2 全量编译
```bash
cd /home/administrator/vcmi-native-build
cmake --build rel --target mlclient -- -j4
```

### 6.3 修复 data/ EEXIST
```bash
cd /home/administrator/vcmi-native-build/rel/bin
rm -rf data && mkdir -p data && cd data
for f in H3bitmap.lod H3sprite.lod Heroes3.snd Heroes3.vid H3ab_bmp.lod H3ab_spr.lod H3ab_ahd.snd H3ab_ahd.vid HotA.lod HiScore.dat; do
  ln -sf /home/administrator/vcmi-native-build/data/$f $f
done
ln -sf /home/administrator/vcmi-native-build/data/Sprites .
ln -sf /home/administrator/vcmi-native-build/data/Sounds .
ln -sf /home/administrator/vcmi-native-build/data/Video .
ln -sf /home/administrator/vcmi-native-build/data/Saves .
ln -sf /mnt/d/Bigdata/hero3_fresh/vcmi/data/Maps Maps
```

### 6.4 修复 JSON 配置文件
写入 `{"general":{"playerName":"Agent"}}` 到以下位置的 SETTINGS/settings.json/MODSETTINGS/modsettings.json/PERSISTENTSTORAGE/persistentStorage.json/KEYBINDINGSCONFIG/keyBindingsConfig.json：
- ~/.local/share/vcmi/config/
- vcmi-native/config/
- vcmi-native-build/config/
- vcmi-native-build/data/config/

### 6.5 用日志定位崩溃
修改 ServerPlugin.cpp 加 fprintf 后重建 mlserverplugin：
```bash
cd /home/administrator/vcmi-native-build
cmake --build rel --target mlserverplugin -- -j4
```

---

## 七、Phase 进度

```
Phase A: VCMI 冒险地图 API    完成
Phase B: 战略 Gym 环境        完成
Phase C: 自对弈 PPO 训练      C7 运行中
  C1-C3: 基础训练+对手池+ELO  完成
  C4: 长程训练                完成
  C5: 训练升级                 待办
  C6: 大地图适配               待办
  C7: 全部完成                完成
Phase D: 战斗集成              待办
Phase E: 真实游戏部署           待办 Track 2
Phase F: 你 vs AI (1v1)       待办
Phase G: 1v7 战胜你            待办
```
