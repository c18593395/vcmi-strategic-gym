# PPO Model AI DLL for VCMI Windows

## 项目目标
实现一个 VCMI 冒险 AI DLL，加载 ONNX 模型控制一个玩家。

## AI DLL 接口
VCMI 通过 CDynLibHandler 动态加载 AI DLL，需要导出两个函数：
```cpp
extern "C" __declspec(dllexport) void GetAiName(char* name);  // 返回 AI 名称
extern "C" __declspec(dllexport) void GetNewAI(std::shared_ptr<CGlobalAI>& ai);  // 创建 AI 实例
```

## 头文件路径
VCMI 源码在 D:\Bigdata\hero3_fresh\vcmi\
包含路径：
- D:\Bigdata\hero3_fresh\vcmi\lib
- D:\Bigdata\hero3_fresh\vcmi\AI
- D:\Bigdata\hero3_fresh\vcmi

## 链接库
- D:\Program Files\VCMI\VCMI_lib.lib (已生成)
- onnxruntime (从 NuGet 或 vcpkg 获取)
- 输出到 D:\Program Files\VCMI\AI\PpoModelAI.dll

## 模型信息
- 模型文件: D:\Bigdata\hero3_fresh\wsl2_model.onnx
- 架构: MLP 256→128→128, actor(128→11), critic(128→1)
- 输入: float32[256] 观测向量
- 输出: float32[11] 动作 logits, float32[1] 价值
- 动作映射: 0=右,1=右下,2=下,3=左下,4=左,5=左上,6=上,7=右上,8=交互,9=换英雄,10=结束回合

## AI 类实现
继承 CAdventureAI（继承自 CGlobalAI）
关键方法：
- initGameInterface(env, callback, options) - 保存 CCallback，加载 ONNX 模型
- yourTurn(queryID) - 每回合调用：
  1. 读取 StrategicState（通过 CCallback 获取游戏状态）
  2. 构建 256 维观测向量
  3. ONNX Runtime 推理得到 action
  4. 映射 action 到 VCMI 命令并发送
- getBattleAIName() - 返回 "BattleAI"（战斗交给 BattleAI）

## 观测向量构建 (256维)
参考 D:\Bigdata\hero3_fresh\vcmi_gym\envs\v13\strategic_env.py 的 _build_obs 方法：
- [0-1]: 当前英雄 x, y
- [2]: 英雄兵力总数
- [3]: 英雄移动力
- [4]: 英雄等级
- [5-11]: 7 种兵种数量
- [12]: 英雄是否在战斗
- [13]: 金币
- [14-19]: 资源 (木材,水银,矿石,硫磺,水晶,宝石)
- [20-21]: 日期 (天,周)
- ... 填充到 256 维

## 动作执行
- 移动 (0-7): 调用 cb->moveHero(hero, dest, ...)
- 交互 (8): 让英雄访问当前格物体
- 换英雄 (9): 选择下一个英雄
- 结束回合 (10): cb->endTurn()

## 编译命令
```bash
cd <build_dir>
cmake -G "Visual Studio 17 2022" -A x64 \
  -DONNXRUNTIME_ROOT=<onnx_path> \
  -DVCMI_SOURCE_DIR=D:/Bigdata/hero3_fresh/vcmi \
  -DVCMI_LIB_DIR="D:/Program Files/VCMI" \
  ..
cmake --build . --config Release
```

## 输出
DLL 放到 D:\Program Files\VCMI\AI\PpoModelAI.dll
在 VCMI 中选 AI 对手时选择 "PpoModelAI"
