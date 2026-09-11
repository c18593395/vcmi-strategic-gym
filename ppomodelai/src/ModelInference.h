#pragma once

#include <onnxruntime_cxx_api.h>
#include <array>
#include <string>
#include <vector>

#include "ObsBuilder.h"  // MB_OBS_DIM=3464 / MB_TERRAIN_FLOAT=1764 (CHW float)

// 全局唯一推理实例 (2026-09-11 teal 回合卡死修复):
// 8 人局 = 7 个 ModelAI 玩家, 若各自构造 Ort::Env+Session 会产生
// 7 份全核线程池 (Game A 单实例正常, Game B 第 6 个 AI teal 首次
// predict 挂死). 改为进程级单例, 所有玩家共享 1 个 Env+Session.
//
// 2026-09-11 v5 双输入改造 (模型质量线 mq-2b):
//   Net.forward(obs[1,3464], terrain[1,4,21,21]) -> actor_logits[1,25] + critic[1,1]
//   opset 17, batch=1; 输入/输出按名定位 (obs / terrain / actor_logits), 兼容导出顺序.
class ModelInference {
    Ort::Env env{ORT_LOGGING_LEVEL_WARNING, "PpoModelAI"};
    Ort::SessionOptions sessionOptions;
    Ort::Session session;
    Ort::MemoryInfo memoryInfo;
    // 2026-09-11: 用 std::string 深拷贝持有输入/输出名。
    // 旧版存 const char* (GetInputNameAllocated 临时对象行尾析构 → 悬垂指针),
    // predict 读到空名 → ORT "Invalid input name: " 全部 fallback endTurn。
    std::vector<std::string> inputNames;
    std::vector<std::string> outputNames;
    std::vector<std::vector<int64_t>> inputShapes;
    std::vector<std::vector<int64_t>> outputShapes;
    int obsInputIdx = 0;      // "obs" 输入在 session 中的索引
    int terrainInputIdx = 1;  // "terrain" 输入索引
    int actionOutputIdx = 0;  // "actor_logits" 输出索引

    ModelInference(const std::string& modelPath);  // 私有: 统一走 instance()

public:
    static ModelInference& instance(const std::string& modelPath);
    // v5 双输入: obs[3464] + terrain(CHW float /255)[1764] -> actor_logits argmax(25)
    int predict(const std::array<float, MB_OBS_DIM>& obs, const std::array<float, MB_TERRAIN_FLOAT>& terrain);
};
