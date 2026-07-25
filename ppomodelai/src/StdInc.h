// PpoModelAI precompiled header — ensures all required includes are available
// before any VCMI headers are processed.

#include <string>
#include <functional>
#include <vector>
#include <memory>
#include <array>
#include <optional>

// Boost stubs for VCMI public API headers
#ifndef BOOST_NONCOPYABLE_HPP
namespace boost {
    class noncopyable {
    protected:
        noncopyable() = default;
        ~noncopyable() = default;
        noncopyable(const noncopyable&) = delete;
        noncopyable& operator=(const noncopyable&) = delete;
    };
}
#endif
