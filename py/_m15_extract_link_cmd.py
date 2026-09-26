# -*- coding: utf-8 -*-
"""M1.5 工具4: Nullkiller2.dll 手工链接 (踩坑 #68 范式)。

OBJECT 库无链接目标; bin\\AI 缺 Nullkiller2.dll (踩坑: 默认 AI=Nullkiller2 时
LoadLibraryW error 126)。本脚本:
  1. 恢复官方 main.cpp 入口 (GetGlobalAiVersion / GetAiName / GetNewAI)
  2. 编 main.cpp.obj (与 ninja 同参)
  3. g++ -shared 全量 70 obj 链 Nullkiller2.dll -> bin\\AI\\
ABI 前提 (踩坑 #68②): VCMI_lib.dll (09-11 23:31) 之后 lib 公共头未改 (已核验:
0911 晚 commit 只动 server/*.cpp) -> 69 obj (0911 05:03 编) ABI 兼容。
"""
import glob
import os
import re
import subprocess
import sys

MINGW = r'C:\msys64\mingw64\bin'
BUILD = r'D:\vcmi-fork-build'
SRC_NK2 = r'D:\Bigdata\hero3_fresh\vcmi\AI\Nullkiller2'
OBJ_DIR = os.path.join(BUILD, r'AI\Nullkiller2\CMakeFiles\Nullkiller2.dir')
MAIN_SRC = os.path.join(SRC_NK2, 'main.cpp')
MAIN_OBJ = os.path.join(OBJ_DIR, 'main.cpp.obj')
OUT_DLL = os.path.join(BUILD, r'bin\AI\Nullkiller2.dll')

MAIN_CPP = r'''/*
 * Nullkiller2.dll entry point (restored from vcmi-1.7.5 AI/Nullkiller2/main.cpp,
 * fork dropped it; required by CDynLibHandler GetProcAddress "GetAiName"/"GetNewAI").
 */
#include "StdInc.h"
#include "AIGateway.h"

#ifdef __GNUC__
#define strcpy_s(a, b, c) strncpy(a, c, b)
#endif

static const char * const g_cszAiName = "Nullkiller2";

extern "C" DLL_EXPORT int GetGlobalAiVersion()
{
	return AI_INTERFACE_VER;
}

extern "C" DLL_EXPORT void GetAiName(char * name)
{
	strcpy_s(name, strlen(g_cszAiName) + 1, g_cszAiName);
}

extern "C" DLL_EXPORT void GetNewAI(std::shared_ptr<CGlobalAI> & out)
{
	out = std::make_shared<NK2AI::AIGateway>();
}
'''

env = dict(os.environ)
env['PATH'] = MINGW + ';' + env.get('System32', r'C:\Windows\System32')

def run(cmd, **kw):
    print('>>>', ' '.join(cmd[:6]), '...')
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=BUILD, env=env, **kw)
    if r.stdout:
        print(r.stdout[-1500:])
    if r.stderr:
        print(r.stderr[-3000:])
    if r.returncode != 0:
        print(f'!! rc={r.returncode}')
        sys.exit(r.returncode)
    return r

# 1. main.cpp
with open(MAIN_SRC, 'w', encoding='utf-8', newline='\n') as f:
    f.write(MAIN_CPP)
print('main.cpp restored')

# 2. 编 main.cpp.obj (与 ninja AIGateway 同参)
common_flags = [
    '-DBOOST_CONTAINER_NO_LIB', '-DBOOST_CONTAINER_STATIC_LINK',
    '-DBOOST_DATE_TIME_NO_LIB', '-DBOOST_DATE_TIME_STATIC_LINK',
    '-DBOOST_FILESYSTEM_NO_LIB', '-DBOOST_FILESYSTEM_STATIC_LINK=1',
    '-DBOOST_PROGRAM_OPTIONS_NO_LIB', '-DBOOST_PROGRAM_OPTIONS_STATIC_LINK',
    '-DENABLE_BATTLE_AI', '-DENABLE_NULLKILLER2_AI', '-DENABLE_STUPID_AI',
    '-DVCMI_DLL=1', '-DVCMI_VERSION_MAJOR=1', '-DVCMI_VERSION_MINOR=8',
    '-DVCMI_VERSION_PATCH=0', '-DVCMI_VERSION_STRING=\\"1.8.0\\"',
    '-ID:/Bigdata/hero3_fresh/vcmi/AI/Nullkiller2',
    '-ID:/Bigdata/hero3_fresh/vcmi/lib',
    '-ID:/Bigdata/hero3_fresh/vcmi',
    '-ID:/Bigdata/hero3_fresh/vcmi/include',
    '-Wall', '-Wextra', '-Wpointer-arith', '-Wuninitialized', '-Wmismatched-tags',
    '-Wno-unused-parameter', '-Wno-switch', '-Wno-reorder', '-Wno-sign-compare',
    '-O3', '-DNDEBUG', '-std=gnu++20', '-fvisibility=default',
]
run([os.path.join(MINGW, 'c++.exe'), *common_flags,
     '-c', MAIN_SRC.replace('\\', '/'), '-o', MAIN_OBJ.replace('\\', '/')])

# 3. 收集全量 obj (CMakeLists 派生的 69 + main = 70, 对照踩坑 #68 数量纪律)
def glob_glob():
    return glob.glob(os.path.join(OBJ_DIR, '**', '*.obj'), recursive=True)

objs = sorted(glob_glob())
if len(objs) != 70:
    print(f'!! obj count = {len(objs)} (expect 70), abort')
    sys.exit(2)

# 3b. adventure_capture_turn 符号解析 (方案B): facade 侧 strategic_state obj 链入本 dll。
# 蓝方 NK2 不进 capture 路径 (AIGateway L1055 playerID==0 门), 状态副本无实际影响;
# VCMI_lib.dll 不动 (ModelAI/训练实验面零影响)。
STRAT_OBJ = os.path.join(BUILD, r'libFacade\CMakeFiles\vcmi.dir\__\server\strategic_state.cpp.obj')
assert os.path.exists(STRAT_OBJ), STRAT_OBJ
objs.append(STRAT_OBJ)

# 4. 链接
link_cmd = [
    os.path.join(MINGW, 'c++.exe'), '-shared', '-o', OUT_DLL.replace('\\', '/'),
    *[o.replace('\\', '/') for o in objs],
    '-L$BIN'.replace('$BIN', os.path.join(BUILD, 'bin').replace('\\', '/')),
    '-lVCMI_lib', '-ltbb12', '-lboost_filesystem-mt',
    '-lws2_32', '-lmswsock', '-ldbghelp', '-lbcrypt',
    '-static-libstdc++', '-static-libgcc',
]
run(link_cmd)
print('DLL OK:', OUT_DLL, os.path.getsize(OUT_DLL), 'bytes')

