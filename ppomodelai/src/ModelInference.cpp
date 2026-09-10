#include "ModelInference.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <numeric>

// C++11 magic static: 线程安全; 7 个玩家同一路径只加载一次模型
ModelInference& ModelInference::instance(const std::string& modelPath)
{
    static ModelInference inst(modelPath);
    return inst;
}

// 限制 ONNX 线程池: 共享单例下 2 intra / 1 inter 足够 (obs 仅 256 维),
// 避免默认全核线程池在多 AI 场景下的资源放大
static Ort::SessionOptions makeSessionOptions()
{
    Ort::SessionOptions opts;
    opts.SetIntraOpNumThreads(2);
    opts.SetInterOpNumThreads(1);
    opts.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
    return opts;
}

ModelInference::ModelInference(const std::string& modelPath)
    : session(env, std::wstring(modelPath.begin(), modelPath.end()).c_str(), makeSessionOptions())
    , memoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault))
{
    fprintf(stderr, "[ModelAI] ONNX singleton session created from %s (threads 2/1)\n", modelPath.c_str());
    fflush(stderr);

    // Get input/output count
    size_t numInputNodes = session.GetInputCount();
    size_t numOutputNodes = session.GetOutputCount();

    // Get input name and shape
    auto inputTypeInfo = session.GetInputTypeInfo(0);
    auto inputTensorInfo = inputTypeInfo.GetTensorTypeAndShapeInfo();
    inputShape = inputTensorInfo.GetShape();
    inputNames.push_back(std::string(session.GetInputNameAllocated(0, Ort::AllocatorWithDefaultOptions()).get()));

    // Get output name and shape
    auto outputTypeInfo = session.GetOutputTypeInfo(0);
    auto outputTensorInfo = outputTypeInfo.GetTensorTypeAndShapeInfo();
    outputShape = outputTensorInfo.GetShape();
    outputNames.push_back(std::string(session.GetOutputNameAllocated(0, Ort::AllocatorWithDefaultOptions()).get()));

    fprintf(stderr, "[ModelAI] session ready: inputs=%zu outputs=%zu in_name='%s' out_name='%s' in_shape=%lldx%lld out_shape=%lld\n",
        numInputNodes, numOutputNodes,
        inputNames[0].c_str(), outputNames[0].c_str(),
        (long long)(inputShape.size() > 1 ? inputShape[1] : -1),
        (long long)(inputShape.size() > 0 ? inputShape[0] : -1),
        (long long)(outputShape.size() > 0 ? outputShape.back() : -1));
    fflush(stderr);
}

int ModelInference::predict(const std::array<float, 256>& input)
{
    // Create input tensor
    std::vector<int64_t> actualInputShape = {1, 256};
    if (!inputShape.empty()) {
        for (size_t i = 0; i < inputShape.size() && i < actualInputShape.size(); i++) {
            if (inputShape[i] > 0) {
                actualInputShape[i] = inputShape[i];
            }
        }
    }

    Ort::Value inputTensor = Ort::Value::CreateTensor<float>(
        memoryInfo,
        const_cast<float*>(input.data()),
        input.size(),
        actualInputShape.data(),
        actualInputShape.size()
    );

    // Run inference (局部 c_str 指针, 保证 Run 调用期间名字有效)
    const char* inName = inputNames[0].c_str();
    const char* outName = outputNames[0].c_str();
    auto outputTensors = session.Run(
        Ort::RunOptions{nullptr},
        &inName,
        &inputTensor,
        1,
        &outName,
        1
    );

    // Get output data
    float* outputData = outputTensors[0].GetTensorMutableData<float>();
    auto outputTypeInfo = outputTensors[0].GetTensorTypeAndShapeInfo();
    auto outputCount = outputTypeInfo.GetElementCount();

    // Argmax
    int bestAction = 0;
    float bestValue = outputData[0];
    for (int64_t i = 1; i < outputCount; i++) {
        if (outputData[i] > bestValue) {
            bestValue = outputData[i];
            bestAction = static_cast<int>(i);
        }
    }

    return bestAction;
}
