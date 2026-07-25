cmake_minimum_required(VERSION 3.16)
project(PpoModelAI LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ONNX Runtime
set(ONNXRUNTIME_DIR "C:/Users/Administrator/onnxruntime/extracted/onnxruntime-win-x64-1.20.1")

add_library(PpoModelAI SHARED
    src/PpoModelAI.cpp
    src/ModelInference.cpp
    src/ObsBuilder.cpp
)

target_include_directories(PpoModelAI PRIVATE
    D:/Bigdata/hero3_fresh/vcmi/lib
    D:/Bigdata/hero3_fresh/vcmi
    C:/Users/Administrator/vcmi_include
    C:/Users/Administrator/vcmi_include/vcmi
    ${ONNXRUNTIME_DIR}/include
)

target_link_libraries(PpoModelAI PRIVATE
    "D:/Program Files/VCMI/VCMI_lib.lib"
    "${ONNXRUNTIME_DIR}/lib/onnxruntime.lib"
    delayimp.lib
)

target_link_options(PpoModelAI PRIVATE
    /DELAYLOAD:VCMI_lib.dll
    /DEF:${CMAKE_SOURCE_DIR}/exports.def
)

# Copy onnxruntime.dll next to the output DLL
add_custom_command(TARGET PpoModelAI POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${ONNXRUNTIME_DIR}/lib/onnxruntime.dll"
        "$<TARGET_FILE_DIR:PpoModelAI>"
    COMMENT "Copying onnxruntime.dll"
)
