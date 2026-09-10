#pragma once

#include <onnxruntime_cxx_api.h>
#include <array>
#include <string>
#include <vector>

// 全局唯一推理实例 (2026-09-11 teal 回合卡死修复):
// 8 人局 = 7 个 ModelAI 玩家, 若各自构造 Ort::Env+Session 会产生
// 7 份全核线程池 (Game A 单实例正常, Game B 第 6 个 AI teal 首次
// predict 挂死). 改为进程级单例, 所有玩家共享 1 个 Env+Session.
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
    std::vector<int64_t> inputShape;
    std::vector<int64_t> outputShape;

    ModelInference(const std::string& modelPath);  // 私有: 统一走 instance()

public:
    static ModelInference& instance(const std::string& modelPath);
    int predict(const std::array<float, 256>& input);
};
