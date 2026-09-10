// PpoModelAI precompiled header — ensures all required includes are available
// before any VCMI headers are processed.

#include <string>
#include <functional>
#include <vector>
#include <memory>
#include <array>
#include <optional>

// VCMI 公共头 (include/vcmi/*.h) 依赖 Global.h 先行提供 boost 头与
// VCMI_LIB_NAMESPACE 宏, 与 lib/StdInc.h (= #include "../Global.h") 一致
#include "Global.h"

// 2026-09-11: 删除 boost::noncopyable stub — 真实 boost (utility.hpp) 已提供
// noncopyable (typedef noncopyable_::noncopyable), stub guard 检测不到真实
// guard (BOOST_CORE_NONCOPYABLE_HPP) 导致重定义冲突, 连带 makeDefend 等
// 类型转换报错。直接使用系统 boost 即可。
