@echo off
REM ModelAI.dll MinGW 直编脚本 (2026-09-11 teal 回合卡死修复: P0+P1+P2)
REM 工具链与 09-08 成功版一致: MSYS2 mingw64 g++, 链 fork bin 的 libVCMI_lib.dll.a + bin\AI\onnxruntime.dll
cd /d d:\Bigdata\hero3_fresh\ppomodelai
if not exist build mkdir build

C:\msys64\mingw64\bin\g++.exe -std=gnu++20 -O2 -DNDEBUG -shared ^
  -DBOOST_CONTAINER_NO_LIB -DBOOST_CONTAINER_STATIC_LINK -DBOOST_DATE_TIME_NO_LIB -DBOOST_DATE_TIME_STATIC_LINK ^
  -DBOOST_FILESYSTEM_NO_LIB -DBOOST_FILESYSTEM_STATIC_LINK=1 -DBOOST_PROGRAM_OPTIONS_NO_LIB -DBOOST_PROGRAM_OPTIONS_STATIC_LINK ^
  -DENABLE_BATTLE_AI -DENABLE_NULLKILLER2_AI -DENABLE_STUPID_AI -DVCMI_DLL=1 ^
  -DVCMI_VERSION_MAJOR=1 -DVCMI_VERSION_MINOR=8 -DVCMI_VERSION_PATCH=0 -DVCMI_VERSION_STRING=\"1.8.0\" ^
  -ID:/Bigdata/hero3_fresh/vcmi/lib -ID:/Bigdata/hero3_fresh/vcmi -ID:/Bigdata/hero3_fresh/vcmi/include ^
  -IC:/Users/Administrator/onnxruntime/extracted/onnxruntime-win-x64-1.20.1/include ^
  src\PpoModelAI.cpp src\ModelInference.cpp src\ObsBuilder.cpp exports.def ^
  -LD:/vcmi-fork-build/bin -lVCMI_lib D:/vcmi-fork-build/bin/AI/onnxruntime.dll ^
  -o build\ModelAI.dll

if errorlevel 1 (
  echo BUILD FAILED
  exit /b 1
)
echo BUILD OK
dir build\ModelAI.dll
