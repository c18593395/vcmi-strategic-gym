#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 WSL 重建补丁 4/5：ML 模式静态 AI 机制。

根因：ENABLE_ML=ON 时引擎仍按 dynlib 机制 dlopen ./AI/libMMAI.so，
但 cmake 里 ENABLE_ML 强制 set(ENABLE_MMAI OFF)（libMMAI.so 永不产出）→ 死锁。
原 WSL 隐藏配置 = CDynLibHandler 走 STATIC_AI 静态分支（按名字 new，
MMAI::AAI 符号来自 OBJECT 库）+ 解除 ML/MMAI 互斥让 OBJECT 库编出来。
幂等可重放。
"""
F1 = "/home/administrator/vcmi-native/lib/callback/CDynLibHandler.cpp"
F2 = "/home/administrator/vcmi-native/CMakeLists.txt"

changed = []

# 1) CDynLibHandler.cpp: 文件级 #define STATIC_AI
s = open(F1).read()
if "#define STATIC_AI" not in s:
    i = s.find("#include")
    assert i >= 0, "CDynLibHandler.cpp 未找到 include 锚点"
    ls = s.rfind("\n", 0, i) + 1
    s = s[:ls] + "#define STATIC_AI\n\n" + s[ls:]
    open(F1, "w").write(s)
    changed.append("CDynLibHandler+#define STATIC_AI")

# 2) CMakeLists.txt: 删除 ENABLE_ML 块内的 set(ENABLE_MMAI OFF)
s = open(F2).read()
lines = s.split("\n")
hits = [k for k, ln in enumerate(lines) if ln.strip() == "set(ENABLE_MMAI OFF)"]
if hits:
    assert len(hits) == 1, f"set(ENABLE_MMAI OFF) 出现 {len(hits)} 次，需人工确认"
    del lines[hits[0]]
    open(F2, "w").write("\n".join(lines))
    changed.append("CMakeLists 解除 ML/MMAI 互斥")

if changed:
    print("补丁应用成功:", " + ".join(changed))
else:
    print("已应用过，跳过")

# 3) CDynLibHandler.cpp: ENABLE_ML 分支 if 块缺闭合 }（原代码缺陷，原 WSL 修过）
s = open(F1).read()
bad = 'if(libpath.stem() == "libMMAI") {\n\t\treturn std::make_shared<MMAI::AAI>();\n#endif'
good = 'if(libpath.stem() == "libMMAI") {\n\t\treturn std::make_shared<MMAI::AAI>();\n\t}\n#endif'
if bad in s:
    s = s.replace(bad, good, 1)
    open(F1, "w").write(s)
    print("补丁应用成功: ENABLE_ML 分支补闭合 }")
elif good in s:
    print("闭合 } 已在，跳过")
else:
    raise SystemExit("ENABLE_ML 分支锚点未找到，需人工检查")

# 4) CDynLibHandler.cpp: AAI 类全名是 MMAI::AAI::AAI（命名空间 MMAI::AAI + 类 AAI），原码少一层
s = open(F1).read()
bad4 = "return std::make_shared<MMAI::AAI>();"
good4 = "return std::make_shared<MMAI::AAI::AAI>();"
if bad4 in s:
    s = s.replace(bad4, good4, 1)
    open(F1, "w").write(s)
    print("补丁应用成功: MMAI::AAI -> MMAI::AAI::AAI")
elif good4 in s:
    print("MMAI::AAI::AAI 已在，跳过")
else:
    raise SystemExit("make_shared<MMAI::AAI> 锚点未找到")
