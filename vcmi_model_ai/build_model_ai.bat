@echo off
REM Build ModelAI.dll against VCMI_lib.lib (import lib from installed VCMI 1.7.5)
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d D:\vcmi_model_ai
cl /nologo /EHsc /std:c++17 /O2 /W3 /LD model_ai.cpp ^
  /I D:\vcmi-1.7.5 ^
  /I D:\vcmi-1.7.5\lib ^
  /I D:\vcmi-1.7.5\include ^
  /I D:\boost_1_83_0 ^
  /I D:\oneTBB-2021.13.0\include ^
  /link VCMI_lib.lib /LIBPATH:D:\vcmi_model_ai ^
  /OUT:ModelAI.dll > build.log 2>&1
echo BUILD_RC=%ERRORLEVEL% >> build.log
type build.log
