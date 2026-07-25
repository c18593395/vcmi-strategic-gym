#pragma once

#include <array>
#include <vcmi/Player.h>

VCMI_LIB_NAMESPACE_BEGIN
class CCallback;
VCMI_LIB_NAMESPACE_END

class ObsBuilder {
public:
    static std::array<float, 256> buildObs(CCallback* cb, PlayerColor selfPlayer);
};
