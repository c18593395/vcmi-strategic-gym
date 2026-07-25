#pragma once

#include <onnxruntime_cxx_api.h>
#include <array>
#include <string>
#include <vector>

class ModelInference {
    Ort::Env env{ORT_LOGGING_LEVEL_WARNING, "PpoModelAI"};
    Ort::SessionOptions sessionOptions;
    Ort::Session session;
    Ort::MemoryInfo memoryInfo;
    std::vector<const char*> inputNames;
    std::vector<const char*> outputNames;
    std::vector<int64_t> inputShape;
    std::vector<int64_t> outputShape;

public:
    ModelInference(const std::string& modelPath);
    int predict(const std::array<float, 256>& input);
};
