// strategic_state.cpp — VCMI 冒险地图状态导出
// 用途: 在 VCMI server 游戏循环中调用, 写 JSON 到 shared file
// 编译: 作为 libvcmi.so 的一部分, 或独立 .cpp 加入 vcmi/server/

#include "lib/gameState/CGameState.h"
#include "lib/CPlayerState.h"
#include "lib/mapObjects/CGHeroInstance.h"
#include "lib/mapObjects/CGTownInstance.h"
#include "lib/mapping/CMap.h"
#include "lib/ResourceSet.h"

#include <fstream>
#include <sstream>

namespace Strategic {

static std::string g_state_file = "/tmp/vcmi_strategic_state.json";

void exportGameState(const CGameState & gs) {
    std::ostringstream json;
    json << "{";

    // 日期
    json << "\"day\":" << gs.day << ",";

    // 玩家
    json << "\"players\":[";
    bool firstPlayer = true;
    for (const auto & [color, ps] : gs.players) {
        if (!firstPlayer) json << ",";
        firstPlayer = false;

        json << "{";
        json << "\"color\":" << color.getNum() << ",";
        json << "\"human\":" << (ps.human ? "true" : "false") << ",";

        // 资源
        json << "\"resources\":{";
        json << "\"wood\":" << ps.resources[EGameResID::WOOD] << ",";
        json << "\"mercury\":" << ps.resources[EGameResID::MERCURY] << ",";
        json << "\"ore\":" << ps.resources[EGameResID::ORE] << ",";
        json << "\"sulfur\":" << ps.resources[EGameResID::SULFUR] << ",";
        json << "\"crystal\":" << ps.resources[EGameResID::CRYSTAL] << ",";
        json << "\"gems\":" << ps.resources[EGameResID::GEMS] << ",";
        json << "\"gold\":" << ps.resources[EGameResID::GOLD];
        json << "},";

        // 英雄
        json << "\"heroes\":[";
        auto heroes = ps.getHeroes();
        for (size_t i = 0; i < heroes.size(); i++) {
            if (i > 0) json << ",";
            const auto * h = heroes[i];
            json << "{";
            json << "\"id\":" << h->id.getNum() << ",";
            json << "\"x\":" << h->pos.x << ",";
            json << "\"y\":" << h->pos.y << ",";
            json << "\"z\":" << h->pos.z << ",";
            json << "\"movement\":" << h->movement << ",";
            json << "\"mana\":" << h->mana << ",";
            json << "\"level\":" << h->level << ",";
            json << "\"exp\":" << h->exp;
            json << "}";
        }
        json << "],";

        // 城镇
        json << "\"towns\":[";
        auto towns = ps.getTowns();
        for (size_t i = 0; i < towns.size(); i++) {
            if (i > 0) json << ",";
            const auto * t = towns[i];
            json << "{";
            json << "\"id\":" << t->id.getNum() << ",";
            json << "\"x\":" << t->pos.x << ",";
            json << "\"y\":" << t->pos.y << ",";
            json << "\"z\":" << t->pos.z;
            json << "}";
        }
        json << "]";
        json << "}";
    }
    json << "],";

    // 地图
    json << "\"map\":{";
    json << "\"width\":" << gs.getMap().width << ",";
    json << "\"height\":" << gs.getMap().height;
    json << "},";

    // 当前回合玩家
    json << "\"actingPlayers\":[";
    bool first = true;
    for (auto & p : gs.actingPlayers) {
        if (!first) json << ",";
        first = false;
        json << p.getNum();
    }
    json << "]";

    json << "}";

    // 原子写入
    std::string tmp = g_state_file + ".tmp";
    std::ofstream(tmp) << json.str();
    std::rename(tmp.c_str(), g_state_file.c_str());
}

void setStateFile(const std::string & path) {
    g_state_file = path;
}

} // namespace Strategic
