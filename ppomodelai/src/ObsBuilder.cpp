#include "StdInc.h"
#include "ObsBuilder.h"

#include "callback/CCallback.h"
#include "callback/CPlayerState.h"
#include "int3.h"
#include "mapObjects/CGHeroInstance.h"
#include "CCreatureHandler.h"
#include "GameConstants.h"

VCMI_LIB_NAMESPACE_BEGIN

std::array<float, 256> ObsBuilder::buildObs(CCallback* cb, PlayerColor selfPlayer)
{
    std::array<float, 256> obs{};
    size_t idx = 0;

    // --- Global info (8 values: indices 0-7) ---
    obs[idx++] = static_cast<float>(cb->getDate(Date::DAYOFWEEK));  // day
    obs[idx++] = static_cast<float>(cb->getDate(Date::WEEK));       // week
    obs[idx++] = static_cast<float>(cb->getDate(Date::MONTH));      // month
    obs[idx++] = static_cast<float>(selfPlayer.getNum());            // current_player
    int3 mapSize = cb->getMapSize();
    obs[idx++] = static_cast<float>(mapSize.x);  // map_width
    obs[idx++] = static_cast<float>(mapSize.y);  // map_height
    obs[idx++] = static_cast<float>(mapSize.z > 0 ? 1 : 0);  // has_underground

    // player_count: count players on map
    auto allPlayers = cb->getPlayerStates();
    bool isActive[8] = {false};
    int playerCount = 0;
    for (auto& p : allPlayers) {
        if (p->status == EPlayerStatus::INGAME) {
            isActive[p->color.getNum()] = true;
            playerCount++;
        }
    }
    obs[idx++] = static_cast<float>(playerCount);

    // --- Players (8 * 12 = 96: indices 8-103) ---
    for (int pi = 0; pi < 8; pi++) {
        if (isActive[pi]) {
            auto pState = cb->getPlayerState(PlayerColor(pi));
            obs[idx++] = static_cast<float>(pi);             // color
            obs[idx++] = 0.0f;                                // human (0 for AI)
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::GOLD]);    // gold
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::WOOD]);    // wood
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::MERCURY]);// mercury
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::ORE]);     // ore
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::SULFUR]);  // sulfur
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::CRYSTAL]); // crystal
            obs[idx++] = static_cast<float>(pState->resources[EGameResID::GEMS]);    // gems
            obs[idx++] = static_cast<float>(pState->heroes.size());  // hero_count
            obs[idx++] = static_cast<float>(pState->towns.size());   // town_count
            obs[idx++] = 1.0f;  // alive
        } else {
            idx += 12;  // skip
        }
    }

    // --- Heroes (up to 6, 23 fields each: indices 104-241) ---
    auto allHeroes = cb->getHeroesInfo();
    int heroCount = 0;
    for (auto* hero : allHeroes) {
        if (idx + 23 > 256) break;
        if (heroCount >= 6) break;

        auto& pos = hero->pos;
        obs[idx++] = static_cast<float>(hero->getHeroType());// id (approximate)
        obs[idx++] = static_cast<float>(hero->tempOwner.getNum());// owner
        obs[idx++] = static_cast<float>(pos.x);              // pos_x
        obs[idx++] = static_cast<float>(pos.y);              // pos_y
        obs[idx++] = static_cast<float>(pos.z);              // pos_z
        obs[idx++] = static_cast<float>(hero->movementPointsRemaining());// movement
        obs[idx++] = static_cast<float>(hero->movementPointsLimit());    // max_movement
        obs[idx++] = static_cast<float>(hero->level);         // level
        obs[idx++] = static_cast<float>(hero->getPrimSkillLevel(static_cast<PrimarySkill::PrimarySkill>(0))); // attack
        obs[idx++] = static_cast<float>(hero->getPrimSkillLevel(static_cast<PrimarySkill::PrimarySkill>(1))); // defense
        obs[idx++] = static_cast<float>(hero->getPrimSkillLevel(static_cast<PrimarySkill::PrimarySkill>(2))); // power
        obs[idx++] = static_cast<float>(hero->getPrimSkillLevel(static_cast<PrimarySkill::PrimarySkill>(3))); // knowledge
        obs[idx++] = static_cast<float>(hero->mana);          // mana
        obs[idx++] = static_cast<float>(hero->manaLimit());   // max_mana
        obs[idx++] = static_cast<float>(hero->experience());  // exp

        // Army (7 slots)
        int totalArmy = 0;
        for (auto& slot : hero->Slots()) {
            if (slot.first.getNum() < 7) {
                obs[idx + slot.first.getNum()] = static_cast<float>(slot.second->getCount());
            }
            totalArmy += slot.second->getCount();
        }
        idx += 7;  // army_count[0..6]

        obs[idx++] = 0.0f;  // in_battle (not easy to check here)
        heroCount++;
    }

    // Fill remaining heroes slots with zeros
    while (idx < 256 && heroCount < 6) {
        idx += 23;
        heroCount++;
    }

    // Pad to exactly 256
    while (idx < 256) {
        obs[idx++] = 0.0f;
    }

    return obs;
}

VCMI_LIB_NAMESPACE_END
