@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d D:\vcmi_model_ai\boostfs
for %%f in (directory operations path) do (
  cl /nologo /c /EHsc /std:c++17 /O2 /DBOOST_FILESYSTEM_NO_CXX20_ATOMIC_REF /I D:\boost_1_83_0 "D:\boost_1_83_0\libs\filesystem\src\%%f.cpp" > D:\vcmi_model_ai\cl_%%f.log 2>&1 || echo FAIL_%%f >> D:\vcmi_model_ai\b6.log
)
echo OBJS=%ERRORLEVEL% >> D:\vcmi_model_ai\b6.log
dir /b *.obj >> D:\vcmi_model_ai\b6.log
lib.exe /nologo /out:..\libboost_filesystem-vc143-mt-s-x64-1_83.lib *.obj >> D:\vcmi_model_ai\b6.log 2>&1
echo LIB_RC=%ERRORLEVEL% >> D:\vcmi_model_ai\b6.log
