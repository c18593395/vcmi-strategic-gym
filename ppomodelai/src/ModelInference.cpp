#include "ModelInference.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <numeric>
#include <random>
#include <string>

// C++11 magic static: 线程安全; 7 个玩家同一路径只加载一次模型
ModelInference& ModelInference::instance(const std::string& modelPath)
{
    static ModelInference inst(modelPath);
    return inst;
}

// 限制 ONNX 线程池: 共享单例下 2 intra / 1 inter 足够 (obs 3464 + terrain 1764),
// 避免默认全核线程池在多 AI 场景下的资源放大
static Ort::SessionOptions makeSessionOptions()
{
    Ort::SessionOptions opts;
    opts.SetIntraOpNumThreads(2);
    opts.SetInterOpNumThreads(1);
    opts.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
    return opts;
}

// 动态维度 (-1 或 0) 置 1 (batch=1)
static std::vector<int64_t> resolveShape(std::vector<int64_t> shape)
{
    for (auto& d : shape)
        if (d <= 0)
            d = 1;
    return shape;
}

static int64_t shapeElemCount(const std::vector<int64_t>& shape)
{
    int64_t cnt = 1;
    for (auto d : shape)
        cnt *= d;
    return cnt;
}

ModelInference::ModelInference(const std::string& modelPath)
    : session(env, std::wstring(modelPath.begin(), modelPath.end()).c_str(), makeSessionOptions())
    , memoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault))
{
    fprintf(stderr, "[ModelAI] ONNX v5 session created from %s (threads 2/1)\n", modelPath.c_str());
    fflush(stderr);

    // v5 双输入双输出: 遍历全部输入/输出记录名字 + shape (std::string 深拷贝防悬垂)
    const size_t numInputs = session.GetInputCount();
    const size_t numOutputs = session.GetOutputCount();
    for (size_t i = 0; i < numInputs; i++) {
        inputNames.push_back(std::string(session.GetInputNameAllocated(i, Ort::AllocatorWithDefaultOptions()).get()));
        inputShapes.push_back(resolveShape(session.GetInputTypeInfo(i).GetTensorTypeAndShapeInfo().GetShape()));
    }
    for (size_t i = 0; i < numOutputs; i++) {
        outputNames.push_back(std::string(session.GetOutputNameAllocated(i, Ort::AllocatorWithDefaultOptions()).get()));
        outputShapes.push_back(resolveShape(session.GetOutputTypeInfo(i).GetTensorTypeAndShapeInfo().GetShape()));
    }

    // 按名定位 obs / terrain 输入与 actor_logits 输出 (找不到时保持默认 0/1/0)
    for (size_t i = 0; i < inputNames.size(); i++) {
        if (inputNames[i].find("terrain") != std::string::npos)
            terrainInputIdx = static_cast<int>(i);
        else
            obsInputIdx = static_cast<int>(i);
    }
    for (size_t i = 0; i < outputNames.size(); i++) {
        if (outputNames[i].find("actor") != std::string::npos)
            actionOutputIdx = static_cast<int>(i);
    }

    fprintf(stderr, "[ModelAI] session ready: inputs=%zu outputs=%zu | obs_in[%d]='%s' | terrain_in[%d]='%s' | act_out[%d]='%s'\n",
        numInputs, numOutputs,
        obsInputIdx, inputNames.empty() ? "?" : inputNames[obsInputIdx].c_str(),
        terrainInputIdx, inputNames.size() > 1 ? inputNames[terrainInputIdx].c_str() : "?",
        actionOutputIdx, outputNames.empty() ? "?" : outputNames[actionOutputIdx].c_str());
    fflush(stderr);
}

int ModelInference::predict(const std::array<float, MB_OBS_DIM>& obs, const std::array<float, MB_TERRAIN_FLOAT>& terrain)
{
    // obs tensor [1, 3464]: session shape 元素数与数据不符时用数据驱动默认
    std::vector<int64_t> obsShape = inputShapes[obsInputIdx];
    if (shapeElemCount(obsShape) != static_cast<int64_t>(obs.size()))
        obsShape = {1, MB_OBS_DIM};

    // terrain tensor [1, 4, 21, 21] (CHW)
    std::vector<int64_t> terShape = inputShapes[terrainInputIdx];
    if (shapeElemCount(terShape) != static_cast<int64_t>(terrain.size()))
        terShape = {1, MB_GRID_CH, MB_GRID_SIZE, MB_GRID_SIZE};

    Ort::Value obsTensor = Ort::Value::CreateTensor<float>(
        memoryInfo,
        const_cast<float*>(obs.data()),
        obs.size(),
        obsShape.data(),
        obsShape.size());
    Ort::Value terTensor = Ort::Value::CreateTensor<float>(
        memoryInfo,
        const_cast<float*>(terrain.data()),
        terrain.size(),
        terShape.data(),
        terShape.size());

    std::vector<Ort::Value> inTensors;
    inTensors.push_back(std::move(obsTensor));
    inTensors.push_back(std::move(terTensor));

    // 局部 c_str 指针, 保证 Run 调用期间名字有效
    std::vector<const char*> inNames;
    inNames.push_back(inputNames[obsInputIdx].c_str());
    inNames.push_back(inputNames[terrainInputIdx].c_str());
    std::vector<const char*> outNames;
    for (const auto& n : outputNames)
        outNames.push_back(n.c_str());

    auto outputTensors = session.Run(
        Ort::RunOptions{nullptr},
        inNames.data(),
        inTensors.data(),
        inTensors.size(),
        outNames.data(),
        outNames.size());

    // actor_logits 采样 (25 动作; PPO 推理与训练一致按 softmax 概率采样, temperature=1.0)
    Ort::Value& actOut = outputTensors[actionOutputIdx];
    float* logits = actOut.GetTensorMutableData<float>();
    int64_t n = actOut.GetTensorTypeAndShapeInfo().GetElementCount();
    if (n > 25)
        n = 25;
    if (n <= 0)
        return 10;  // 输出异常: END_TURN 兜底

    // softmax(temperature=1.0)
    float maxLogit = logits[0];
    for (int64_t i = 1; i < n; i++)
        if (logits[i] > maxLogit)
            maxLogit = logits[i];
    double probs[25];
    double sum = 0.0;
    for (int64_t i = 0; i < n; i++) {
        probs[i] = std::exp(static_cast<double>(logits[i] - maxLogit));
        sum += probs[i];
    }
    if (sum <= 0.0)
        return 10;  // 数值异常: END_TURN 兜底

    // 按概率采样
    static std::mt19937 rng{std::random_device{}()};
    std::uniform_real_distribution<double> uniform(0.0, sum);
    double pick = uniform(rng);
    for (int64_t i = 0; i < n; i++) {
        pick -= probs[i];
        if (pick <= 0.0)
            return static_cast<int>(i);
    }
    return static_cast<int>(n - 1);
}
