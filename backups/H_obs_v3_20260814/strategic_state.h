// strategic_state.h
#pragma once
#include <string>

namespace Strategic {
    void exportGameState(const class CGameState & gs);
    void setStateFile(const std::string & path);
}
