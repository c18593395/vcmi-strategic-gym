#include "ModelInference.h"
#include <algorithm>
#include <cassert>
#include <numeric>

ModelInference::ModelInference(const std::string& modelPath)
    : session(env, std::wstring(modelPath.begin(), modelPath.end()).c_str(), sessionOptions)
    , memoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault))
{
    // Get input/output count
    size_t numInputNodes = session.GetInputCount();
    size_t numOutputNodes = session.GetOutputCount();

    // Get input name and shape
    auto inputTypeInfo = session.GetInputTypeInfo(0);
    auto inputTensorInfo = inputTypeInfo.GetTensorTypeAndShapeInfo();
    inputShape = inputTensorInfo.GetShape();
    inputNames.push_back(session.GetInputNameAllocated(0, Ort::AllocatorWithDefaultOptions()).get());

    // Get output name and shape
    auto outputTypeInfo = session.GetOutputTypeInfo(0);
    auto outputTensorInfo = outputTypeInfo.GetTensorTypeAndShapeInfo();
    outputShape = outputTensorInfo.GetShape();
    outputNames.push_back(session.GetOutputNameAllocated(0, Ort::AllocatorWithDefaultOptions()).get());
}

int ModelInference::predict(const std::array<float, 256>& input)
{
    // Create input tensor
    std::vector<int64_t> actualInputShape = {1, 256};
    if (!inputShape.empty()) {
        for (size_t i = 0; i < inputShape.size(); i++) {
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

    // Run inference
    auto outputTensors = session.Run(
        Ort::RunOptions{nullptr},
        inputNames.data(),
        &inputTensor,
        1,
        outputNames.data(),
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
