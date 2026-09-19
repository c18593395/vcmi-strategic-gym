#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09-19 WSL 重建补丁 5/5：MMAI 库本体版本漂移修复（AAI.cpp 落后于 AAI.h）。

1) showGarrisonDialog 实现（4 参旧版）与 AAI.h 声明（6 参新版带 customTitle）对齐；
2) router.cpp ASSERT(shared_ptr) 显式转 bool（宏展开不接受 implicit 转换）。
幂等可重放。
"""
F1 = "/home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp"
F2 = "/home/administrator/vcmi-native/AI/MMAI/BAI/router.cpp"

changed = []

s = open(F1).read()
bad = "void AAI::showGarrisonDialog(const CArmedInstance * up, const CGHeroInstance * down, bool removableUnits, QueryID queryID)\n{"
good = ("void AAI::showGarrisonDialog(const CArmedInstance * up, const CGHeroInstance * down, bool removableUnits, QueryID queryID, const MetaString & customTitle)\n"
        "{\n"
        "        (void)customTitle; // 09-19 签名对齐 AAI.h (引擎新增 customTitle 参数)")
if good.split("{")[0] in s:
    print("AAI showGarrisonDialog 已对齐，跳过")
elif bad in s:
    s = s.replace(bad, good, 1)
    open(F1, "w").write(s)
    changed.append("AAI.cpp showGarrisonDialog 签名对齐")
else:
    raise SystemExit("AAI.cpp showGarrisonDialog 锚点未找到")

s = open(F2).read()
bad2 = 'ASSERT(repo->fallbackModel, "fallback error: model is null");'
good2 = 'ASSERT((bool)repo->fallbackModel, "fallback error: model is null");'
if good2 in s:
    print("router ASSERT 已修，跳过")
elif bad2 in s:
    s = s.replace(bad2, good2, 1)
    open(F2, "w").write(s)
    changed.append("router.cpp ASSERT 显式 bool")
else:
    raise SystemExit("router.cpp ASSERT 锚点未找到")

if changed:
    print("补丁应用成功:", " + ".join(changed))

# 3) BAI.cpp 三处（shared_ptr 隐式转 bool ×2 + 字面量赋值笔误 ×1）
F3 = "/home/administrator/vcmi-native/AI/MMAI/BAI/v13/BAI.cpp"
s = open(F3).read()
fixes3 = [
    ('ASSERT(state->battlefield, "Cannot build battle action if state->battlefield is missing");',
     'ASSERT((bool)state->battlefield, "Cannot build battle action if state->battlefield is missing");'),
    ('ASSERT(stack, "no target to shoot");',
     'ASSERT((bool)stack, "no target to shoot");'),
    ('ASSERT(a == EAccessibility::ACCESSIBLE, "accessibility should\'ve been ACCESSIBLE, was: " = std::to_string(EI(a)));',
     'ASSERT(a == EAccessibility::ACCESSIBLE, "accessibility should\'ve been ACCESSIBLE, was: " + std::to_string(EI(a)));'),
]
for i, (b, g) in enumerate(fixes3, 1):
    if g in s:
        print(f"BAI.cpp 修复{i} 已在，跳过")
    elif b in s:
        s = s.replace(b, g, 1)
        changed.append(f"BAI.cpp 修复{i}")
    else:
        raise SystemExit(f"BAI.cpp 修复{i} 锚点未找到")
open(F3, "w").write(s)

if changed:
    print("全部完成:", " + ".join(changed))

# 4) global_stats.cpp 适配 11 项 schema（BATTLE_ROUND）：断言 10→11 + 构造 NA + update 动态 round
F4 = "/home/administrator/vcmi-native/AI/MMAI/BAI/v13/global_stats.cpp"
s = open(F4).read()
pending = False

b, g = ('static_assert(EI(GA::_count) == 10,', 'static_assert(EI(GA::_count) == 11,')
if g in s:
    print("global_stats 断言 11 已在，跳过")
elif b in s:
    s = s.replace(b, g, 1)
    pending = True
    print("global_stats 断言 10→11 已改")
else:
    raise SystemExit("global_stats 断言锚点未找到")

b, g = "setattr(GA::BATTLE_SIDE, EI(side));", \
       "setattr(GA::BATTLE_SIDE, EI(side)); // 09-19: 构造期 BATTLE_ROUND 置 NA\n        setattr(GA::BATTLE_ROUND, S13::NULL_VALUE_UNENCODED);"
if "GA::BATTLE_ROUND" in s:
    print("global_stats 构造 NA 已在，跳过")
elif b in s:
    s = s.replace(b, g, 1)
    pending = True
    print("global_stats 构造期 BATTLE_ROUND NA 已加")
else:
    raise SystemExit("global_stats BATTLE_SIDE setattr 锚点未找到")

b, g = "canWait ? actmask.set(EI(GlobalAction::WAIT))", \
       "setattr(GA::BATTLE_ROUND, round); // 09-19: 动态轮次\n        canWait ? actmask.set(EI(GlobalAction::WAIT))"
if "GA::BATTLE_ROUND, round" in s:
    print("global_stats update round 已在，跳过")
elif b in s:
    s = s.replace(b, g, 1)
    pending = True
    print("global_stats update 动态 round 已加")
else:
    raise SystemExit("global_stats canWait 锚点未找到")

if pending:
    open(F4, "w").write(s)
    changed.append("global_stats 适配 11 项 schema")
    print("全部完成:", " + ".join(changed))

# 5) AAI.cpp 补 onNewSystemMessageReceived 实现（AAI.h 声明了 override 但无实现 → 链接缺符号）
s = open(F1).read()
impl = ("\n"
        "// 09-19 重建补丁: AAI.h 声明了 onNewSystemMessageReceived(const override) 但实现缺失,\n"
        "// 链接 libvcmi.so 报 undefined symbol; 补透传打点实现\n"
        "void MMAI::AAI::AAI::onNewSystemMessageReceived(const std::string & msg) const\n"
        "{\n"
        "        fprintf(stderr, \"[AAI DBG] onNewSystemMessageReceived: %s\\n\", msg.c_str());\n"
        "}\n")
if "void MMAI::AAI::AAI::onNewSystemMessageReceived" in s:
    print("AAI onNewSystemMessageReceived 全限定实现已在，跳过")
elif "void AAI::onNewSystemMessageReceived" in s:
    s = s.replace("void AAI::onNewSystemMessageReceived(const std::string & msg) const",
                  "void MMAI::AAI::AAI::onNewSystemMessageReceived(const std::string & msg) const", 1)
    open(F1, "w").write(s)
    print("补丁修正: 旧实现升级为全限定名")
else:
    if not s.endswith("\n"):
        s += "\n"
    s += impl
    open(F1, "w").write(s)
    print("补丁应用成功: AAI 补 onNewSystemMessageReceived 实现")

# 6) router.cpp 补 Router::onNewSystemMessageReceived 实现（同 5，链接缺符号）
F5 = "/home/administrator/vcmi-native/AI/MMAI/BAI/router.cpp"
s = open(F5).read()
impl5 = ("\n"
         "// 09-19 重建补丁: router.h 声明了 onNewSystemMessageReceived(const override) 但实现缺失\n"
         "void MMAI::BAI::Router::onNewSystemMessageReceived(const std::string & msg) const\n"
         "{\n"
         "        fprintf(stderr, \"[Router DBG] onNewSystemMessageReceived: %s\\n\", msg.c_str());\n"
         "}\n")
if "void MMAI::BAI::Router::onNewSystemMessageReceived" in s:
    print("Router onNewSystemMessageReceived 已在，跳过")
else:
    if not s.endswith("\n"):
        s += "\n"
    s += impl5
    open(F5, "w").write(s)
    print("补丁应用成功: Router 补 onNewSystemMessageReceived 实现")
