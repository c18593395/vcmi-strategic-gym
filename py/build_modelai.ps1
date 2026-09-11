# ModelAI.dll MinGW 直编脚本 (2026-09-11 teal 回合卡死修复: P0+P1+P2)
# 工具链与 09-08 成功版一致: MSYS2 mingw64 g++ 直编, 链 fork bin 的 libVCMI_lib.dll.a + bin\AI\onnxruntime.dll
# 编译参数来自 D:\vcmi-fork-build\build.ninja 的 BattleAI 条目 (-std=gnu++20, BattleAI DEFINES/INCLUDES)
Set-Location d:\Bigdata\hero3_fresh\ppomodelai
New-Item -ItemType Directory -Force -Path build | Out-Null

# 关键: 裸 PowerShell 的 PATH 没有 mingw64\bin, cc1plus/as/ld 的依赖 DLL 找不到 → 静默 exit 1
$env:PATH = 'C:\msys64\mingw64\bin;' + $env:PATH

$gpp = 'C:\msys64\mingw64\bin\g++.exe'
$argList = @(
  '-std=gnu++20','-O2','-g','-DNDEBUG','-shared',
  '-DBOOST_CONTAINER_NO_LIB','-DBOOST_CONTAINER_STATIC_LINK',
  '-DBOOST_DATE_TIME_NO_LIB','-DBOOST_DATE_TIME_STATIC_LINK',
  '-DBOOST_FILESYSTEM_NO_LIB','-DBOOST_FILESYSTEM_STATIC_LINK=1',
  '-DBOOST_PROGRAM_OPTIONS_NO_LIB','-DBOOST_PROGRAM_OPTIONS_STATIC_LINK',
  '-DENABLE_BATTLE_AI','-DENABLE_NULLKILLER2_AI','-DENABLE_STUPID_AI','-DVCMI_DLL=1',
  '-ID:/Bigdata/hero3_fresh/vcmi/lib','-ID:/Bigdata/hero3_fresh/vcmi','-ID:/Bigdata/hero3_fresh/vcmi/include',
  '-IC:/Users/Administrator/onnxruntime/extracted/onnxruntime-win-x64-1.20.1/include',
  'src/PpoModelAI.cpp','src/ModelInference.cpp','src/ObsBuilder.cpp','exports.def',
  '-LD:/vcmi-fork-build/bin','-lVCMI_lib','D:/vcmi-fork-build/bin/AI/onnxruntime.dll',
  '-o','build/ModelAI.dll'
)

$p = Start-Process -FilePath $gpp -ArgumentList $argList -NoNewWindow -Wait -PassThru `
       -RedirectStandardOutput build\build_stdout.txt -RedirectStandardError build\build_stderr.txt
Write-Output ("G++ EXIT=" + $p.ExitCode)

if ($p.ExitCode -ne 0) {
  Write-Output '--- stderr ---'
  Get-Content build\build_stderr.txt
  Write-Output '--- stdout ---'
  Get-Content build\build_stdout.txt
  exit 1
}
Write-Output 'BUILD OK'
Get-Item build\ModelAI.dll | Format-List Name,Length,LastWriteTime
