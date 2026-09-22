// =============================================================================
// Copyright 2024 Simeon Manolov <s.manolloff@gmail.com>.  All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// =============================================================================

#include "threadconnector.h"
#include "common.h"
#include "schema/base.h"
#include "schema/v13/constants.h"
#include "schema/v13/types.h"
#include "ML/MLClient.h"
#include "ML/model_wrappers/function.h"
#include "ML/model_wrappers/scripted.h"
#include "ML/model_wrappers/path.h"
#include "exporter.h"

#include <chrono>
#include <condition_variable>
#include <csignal>
#include <mutex>
#include <pybind11/pybind11.h>
#include <pybind11/detail/common.h>
#include <pybind11/stl.h>

#include <stdexcept>
#include <string>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <unistd.h>

#include "ML/strategic_state.h"

// 跨库回调 trampoline — 定义在 libmlclient.so 中
// 调用不跨库，g_adventure_cb 指向同库函数，ABI 安全
extern "C" void adventure_cb_trampoline(int playerColor, void* userData);
extern "C" void register_adventure_delegate(void (*delegate)(int, void*), void* userdata);
extern "C" int adventure_wait_for_turn();
extern "C" void adventure_send_action(int action);


#define ASSERT_STATE(id, want) { \
    if((want) != (connstate)) \
        throw VCMIConnectorException(std::string(id) + ": unexpected connector state: want: " + std::to_string(EI(want)) + ", have: " + std::to_string(EI(connstate))); \
}

// Python does not know about some threads and exceptions thrown there
// result in abrupt program termination.
// => use this to set a member var `_error`
//    (the exception must be constructed and thrown in python-aware thread)
#define SET_ERROR(msg) { \
    if (!_shutdown) { \
        std::cerr << boost::str(boost::format("ERROR (only recorded): %1%") % msg); \
        LOG(boost::str(boost::format("ERROR (only recorded): %1%") % msg)); \
        _error = msg; \
    } \
}

#define SHUTDOWN_VCMI_RETURN(ret) { \
    if (_shutdown) { \
        LOG("connector is shutting down"); \
        return ret; \
    } \
}

#define SHUTDOWN_PYTHON_RETURN(ret) { \
    if (_shutdown) { \
        LOG("connector is shutting down"); \
        return {static_cast<int>(ReturnCode::SHUTDOWN), ret}; \
    } \
}

namespace Connector::V13::Thread {
    void adventure_yourTurn_callback(int playerColor, void* userData);

    const std::vector<std::string> Connector::getLogs() {
        return std::vector<std::string>(logs.begin(), logs.end());
    }

    void Connector::log(std::string funcname, std::string msg) {
#if VERBOSE || LOGCOLLECT
        boost::posix_time::ptime t = boost::posix_time::microsec_clock::universal_time();

        // std::string entry = boost::str(boost::format("++ %1% <%2%>[%3%][%4%] <%5%> %6%") \
        //     % boost::posix_time::to_iso_extended_string(t)
        //     % std::this_thread::get_id()
        //     % std::filesystem::path(__FILE__).filename().string()
        //     % (PyGILState_Check() ? "GIL=1" : "GIL=0")
        //     % funcname
        //     % msg
        // );

        std::string entry = boost::str(boost::format("++ %s <%ld/%s>[GIL=%d] <%s> %s")
            % boost::posix_time::to_iso_extended_string(t)
            % static_cast<long>(getpid())
            // % std::this_thread::get_id()
            % to_base36(native_thread_id())
            % PyGILState_Check()
            % funcname
            % msg
        );

#if LOGCOLLECT
        {
            std::unique_lock lock(mlog);
            if (logs.size() == maxlogs)
                logs.pop_front();
            logs.push_back(entry);
        }
#endif // LOGCOLLECT

#if VERBOSE
        {
            std::unique_lock lock(mlog);
            std::cout << entry << "\n";
        }
#endif // VERBOSE
#endif // VERBOSE || LOGCOLLECT
    }

    ReturnCode Connector::_cond_wait(const char* funcname, int id, std::condition_variable &cond, std::unique_lock<std::mutex> &l, int timeoutSeconds, std::function<bool()> &checker) {
        ReturnCode res;
        int i = 0;
        auto start = std::chrono::high_resolution_clock::now();

        while (true) {
            // LOG(boost::str(boost::format("[%s] cond%d.wait/2: checker()...") % funcname % id));
            auto fres = checker();
            // LOG(boost::str(boost::format("[%s] cond%d.wait/2: checker -> %d") % funcname % id % static_cast<int>(fres)));

            // XXX: shutdown is not really supported
            if (_shutdown) {
                LOG("shutdown requested");
                res = ReturnCode::SHUTDOWN;
                break;
            } else if (fres) {
                res = ReturnCode::OK;
                break;
            }

            std::chrono::duration<double, std::chrono::seconds::period> elapsed =
                std::chrono::high_resolution_clock::now() - start;

            if (timeoutSeconds != -1 && elapsed.count() > timeoutSeconds) {
                LOG(boost::str(boost::format("%s: cond%d.wait/2 timed out after %d seconds\n") % funcname % id % elapsed.count()));
                res = ReturnCode::TIMEOUT;
                break;
            }
        }

        LOGFMT("[%s] cond%d.wait/2 -> EXIT %d", funcname % id % static_cast<int>(res));
        return res;
    }

    ReturnCode Connector::cond_wait(const char* funcname, int id, std::condition_variable &cond, std::unique_lock<std::mutex> &l, int timeoutSeconds, std::function<bool()> &pred) {
        std::function<bool()> checker = [&cond, &l, &pred]() -> bool {
            return cond.wait_for(l, std::chrono::milliseconds(100), pred);
        };

        return _cond_wait(funcname, id, cond, l, timeoutSeconds, checker);
    }

    // EOF TEST SIGNAL HANDLING

    const MMAI::Schema::V13::ISupplementaryData* Connector::extractSupplementaryData(const MMAI::Schema::IState *s) {
        LOG("Extracting supplementary data...");
        auto any = s->getSupplementaryData();
        if(!any.has_value()) throw std::runtime_error("extractSupplementaryData: supdata is empty");
        auto &t = typeid(const MMAI::Schema::V13::ISupplementaryData*);
        auto err = MMAI::Schema::AnyCastError(any, typeid(const MMAI::Schema::V13::ISupplementaryData*));

        if(!err.empty()) {
            LOGFMT("anycast for getSumpplementaryData error: %s", err);
        }

        return std::any_cast<const MMAI::Schema::V13::ISupplementaryData*>(s->getSupplementaryData());
    };

    const P_State Connector::convertState(const MMAI::Schema::IState* s) {
        LOG("Convert IState -> P_State");
        auto sup = extractSupplementaryData(s);
        assert(sup->getType() == MMAI::Schema::V13::ISupplementaryData::Type::REGULAR);

        auto cstate = s->getBattlefieldState();
        auto pystate = P_BattlefieldState(cstate->size());
        auto pystatedata = pystate.mutable_data();
        for (int i=0; i < cstate->size(); ++i)
            pystatedata[i] = cstate->at(i);

        auto cmask = s->getActionMask();
        auto pymask = P_ActionMask(cmask->size());
        auto pymaskdata = pymask.mutable_data();
        for (int i=0; i < cmask->size(); ++i)
            pymaskdata[i] = cmask->at(i);

        auto pylinks = P_LinksDict();

        for (const auto &[type, links] : sup->getAllLinks()) {
            py::str pytype;

            switch(type) {
            break; case MMAI::Schema::V13::LinkType::ADJACENT:
                pytype = "ADJACENT";
            break; case MMAI::Schema::V13::LinkType::REACH:
                pytype = "REACH";
            break; case MMAI::Schema::V13::LinkType::RANGED_MOD:
                pytype = "RANGED_MOD";
            break; case MMAI::Schema::V13::LinkType::ACTS_BEFORE:
                pytype = "ACTS_BEFORE";
            break; case MMAI::Schema::V13::LinkType::MELEE_DMG_REL:
                pytype = "MELEE_DMG_REL";
            break; case MMAI::Schema::V13::LinkType::RETAL_DMG_REL:
                pytype = "RETAL_DMG_REL";
            break; case MMAI::Schema::V13::LinkType::RANGED_DMG_REL:
                pytype = "RANGED_DMG_REL";
            break; default:
                throw std::runtime_error("Unexpected links type: " + std::to_string(EI(type)));
            }

            const auto srcinds = links->getSrcIndex();
            const auto dstinds = links->getDstIndex();
            const auto attrs = links->getAttributes();

            if (srcinds.size() != dstinds.size())
                throw std::runtime_error("inds size mismatch: " + std::to_string(srcinds.size()) + " / " + std::to_string(dstinds.size()));

            ssize_t n = srcinds.size();
            ssize_t attrsize = LINK_SIZES.at(EI(type));
            ssize_t flatattrsize = n * attrsize;

            if (attrs.size() != flatattrsize)
                throw std::runtime_error("attrs size mismatch: " + std::to_string(attrs.size()) + " / " + std::to_string(flatattrsize) + " / ");

            auto pyinds = py::array_t<int64_t>({ssize_t(2), n});
            std::memcpy(pyinds.mutable_data(), srcinds.data(), n*sizeof(int64_t));
            std::memcpy(pyinds.mutable_data() + n, dstinds.data(), n*sizeof(int64_t));

            auto pyattrs = py::array_t<float>({n, attrsize});
            std::memcpy(pyattrs.mutable_data(), attrs.data(), flatattrsize*sizeof(float));

            auto pytypelinks = py::dict();
            pytypelinks[py::str("index")] = pyinds;
            pytypelinks[py::str("attrs")] = pyattrs;
            pylinks[pytype] = pytypelinks;
        }

        LOG("Creating P_State...");

        auto res = P_State(
             sup->getType(),
             pystate,
             pymask,
             pylinks,
             sup->getErrorCode(),
             sup->getAnsiRender()
        );

        return res;
    }

    ReturnCode Connector::getState(const char* funcname, int side, MMAI::Schema::Action action_) {
        LOGFMT("%s called with side=%d", funcname % side);

        auto expstate = side ? ConnectorState::AWAITING_ACTION_1 : ConnectorState::AWAITING_ACTION_0;
        auto &m = side ? m1 : m0;
        auto &cond = side ? cond1 : cond0;

        ASSERT_STATE(funcname, expstate);

        LOGFMT("obtain lock%d", side);
        std::unique_lock lock(m);
        LOGFMT("obtain lock%d: done", side);

        LOGFMT("set this->action = %d", action_);
        action = action_;

        LOG("set connstate = AWAITING_STATE");
        connstate = ConnectorState::AWAITING_STATE;

        LOGFMT("cond%d.notify_one()", side);
        cond.notify_one();

        std::function<bool()> pred = [this, expstate] { return connstate == expstate || _shutdown; };

        ReturnCode res;

        {
            LOG("release Python GIL");
            py::gil_scoped_release release;

            LOGFMT("cond%1%.wait(lock%1%)", side);
            res = cond_wait(funcname, side, cond, lock, vcmiTimeout, pred);
            LOGFMT("cond%1%.wait(lock%1%): done", side);
        }

        if (!_error.empty()) {
            throw VCMIConnectorException(_error);
        }

        LOGFMT("release lock%d (return)", side);
        return res;
    }

    const std::tuple<int, std::string> Connector::render(int side) {
        SHUTDOWN_PYTHON_RETURN("");
        auto code = getState(__func__, side, MMAI::Schema::ACTION_RENDER_ANSI);
        auto sup = extractSupplementaryData(state);
        assert(sup->getType() == MMAI::Schema::V13::ISupplementaryData::Type::ANSI_RENDER);
        LOG("return state->ansiRender");
        return {static_cast<int>(code), sup->getAnsiRender()};
    }

    const std::tuple<int, P_State> Connector::reset(int side) {
        SHUTDOWN_PYTHON_RETURN(convertState(state)); // reuse last state if shutting down
        auto code = getState(__func__, side, MMAI::Schema::ACTION_RESET);
        auto pstate = convertState(state);
        LOG("return P_State");
        return {static_cast<int>(code), pstate};
    }

    const std::tuple<int, P_State> Connector::step(int side, MMAI::Schema::Action a) {
        SHUTDOWN_PYTHON_RETURN(convertState(state)); // reuse last state if shutting down
        auto code = getState(__func__, side, a);
        auto pstate = convertState(state);
        LOG("return P_State");
        return {static_cast<int>(code), pstate};
    }

    // this is called by a VCMI thread (the runNetwork thread)
    // Python does not know about this thread and exceptions thrown here
    // result in abrupt program termination.
    // => set a member var `_error` to be thrown by python-aware threads
    // Only throw here if this var was previously set and still not thrown
    MMAI::Schema::Action Connector::getAction(const MMAI::Schema::IState* s, int side) {
        SHUTDOWN_VCMI_RETURN(MMAI::Schema::ACTION_RESET);

        LOG("getAction called with side=" + std::to_string(side));

        auto &m = side ? m1 : m0;
        auto &cond = side ? cond1 : cond0;

        LOGFMT("obtain lock%d", side);
        std::unique_lock lock(m);
        LOGFMT("obtain lock%d: done", side);

        if (connstate != ConnectorState::AWAITING_STATE)
            SET_ERROR(boost::str(boost::format("%s: Unexpected connector state: want: %d, have: %d") % __func__ % EI(ConnectorState::AWAITING_STATE) % EI(connstate)));

        LOG("set this->istate = s");
        state = s;

        LOG("set connstate = AWAITING_ACTION_" + std::to_string(side));
        connstate = side
            ? ConnectorState::AWAITING_ACTION_1
            : ConnectorState::AWAITING_ACTION_0;

        LOGFMT("cond%d.notify_one()", side);
        cond.notify_one();

        std::function<bool()> pred = [this] { return connstate == ConnectorState::AWAITING_STATE || _shutdown; };

        // Now wait again (will unblock once step/reset have been called)
        LOGFMT("cond%1%.wait(lock%1%)", side);
        auto res = cond_wait(__func__, side, cond, lock, userTimeout, pred);
        LOGFMT("cond%1%.wait(lock%1%): done", side);

        SHUTDOWN_VCMI_RETURN(MMAI::Schema::ACTION_RESET);

        // the above cond_wait gave priority to a python thread which was
        // waiting in getState. It was supposed to throw any stored errors
        // If it did not (bug) => throw here
        if (!_error.empty()) {
            for (auto &msg : logs)
                std::cerr << msg << "\n";
            throw VCMIConnectorException(_error);
        }

        if (res == ReturnCode::TIMEOUT) {
            SET_ERROR(boost::str(boost::format("timeout after %ds while waiting for user\n") % userTimeout));
        } else if (res == ReturnCode::SHUTDOWN) {
            LOG("connector is shutting down...");
        } else if (res != ReturnCode::OK) {
            SET_ERROR(boost::str(boost::format("unexpected return code from cond_wait: %d\n") % EI(res)));
        } else if (connstate != ConnectorState::AWAITING_STATE) {
            SET_ERROR(boost::str(boost::format("unexpected connector state: want: %d, have: %d") % EI(ConnectorState::AWAITING_STATE) % EI(connstate)));
        }

        LOGFMT("release lock%d (return)", side);
        LOGFMT("return Action: %d", action);
        return action;
    }

    // initial connect is a special case and cannot reuse getState()
    const std::tuple<int, P_State> Connector::connect(int side) {
        LOG("connect called with side=" + std::to_string(side));

        LOG("obtain lock2");
        std::unique_lock lock2(m2);
        LOG("obtain lock2: done");

        if (side) {
            if (connectedClient1)
                throw std::runtime_error("A client with side 1 is already connected.");
            connectedClient1 = true;
        } else {
            if (connectedClient0)
                throw std::runtime_error("A client with side 0 is already connected.");
            connectedClient0 = true;
        }

        LOG("cond2.notify_one()");
        cond2.notify_one();

        auto expstate = side ? ConnectorState::AWAITING_ACTION_1 : ConnectorState::AWAITING_ACTION_0;
        auto &m = side ? m1 : m0;
        auto &cond = side ? cond1 : cond0;

        LOGFMT("obtain lock%d", side);
        std::unique_lock lock(m);
        LOGFMT("obtain lock%d: done", side);

        LOG("release lock2");
        lock2.unlock();

        ReturnCode res;

        std::function<bool()> pred = [this, expstate] { return connstate == expstate; };

        {
            LOG("release Python GIL");
            py::gil_scoped_release release;

            LOGFMT("cond%1%.wait(lock%1%)", side);
            res = cond_wait(__func__, side, cond, lock, bootTimeout, pred);
            LOGFMT("cond%1%.wait(lock%1%): done", side);
        }

        auto pstate = convertState(state);
        LOGFMT("release lock%d (return)", side);
        LOG("return P_State");
        return {static_cast<int>(res), pstate};
    }

    void Connector::init() {
        LOG("init (main thread)");
        ASSERT_STATE("init", ConnectorState::NEW);

        auto f_getAction0 = [this](const MMAI::Schema::IState* s) {
            return this->getAction(s, 0);
        };

        auto f_getAction1 = [this](const MMAI::Schema::IState* s) {
            return this->getAction(s, 1);
        };

        auto f_getValueDummy = [](const MMAI::Schema::IState* s) {
            std::cerr << "WARNING: getValue called, but is not implemented in connector\n";
            return 0.0;
        };

        auto f_getRandomAction = [](const MMAI::Schema::IState* s) {
            return RandomValidAction(s);
        };

        if (red == "MMAI_RANDOM") {
            leftModel = new ML::ModelWrappers::Function(version(), "MMAI_RANDOM", Side::LEFT, f_getRandomAction, f_getValueDummy);
        } else if (red == "MMAI_USER") {
            leftModel = new ML::ModelWrappers::Function(version(), "MMAI_USER_GYM", Side::LEFT, f_getAction0, f_getValueDummy);
        } else if (red == "MMAI_MODEL") {
            leftModel = new ML::ModelWrappers::Path(redModel);
        } else {
            leftModel = new ML::ModelWrappers::Scripted(red, Side::LEFT);
        }

        if (blue == "MMAI_RANDOM") {
            rightModel = new ML::ModelWrappers::Function(version(), "MMAI_RANDOM", Side::RIGHT, f_getRandomAction, f_getValueDummy);
        } else if (blue == "MMAI_USER") {
            rightModel = new ML::ModelWrappers::Function(version(), "MMAI_USER_GYM", Side::RIGHT, f_getAction1, f_getValueDummy);
        } else if (blue == "MMAI_MODEL") {
            rightModel = new ML::ModelWrappers::Path(blueModel);
        } else {
            rightModel = new ML::ModelWrappers::Scripted(blue, Side::RIGHT);
        }

        // This must happen in the main thread (SDL requires it)
        initargs = std::make_unique<ML::InitArgs>(
            _mapname, leftModel, rightModel,
            _redAllowMlBot, _blueAllowMlBot,
            0,                      // maxBattles (hardcoded, matching old behavior)
            _seed,
            _randomHeroes, _randomObstacles, _townChance, _warmachineChance,
            _randomArmies ? 100 : 0,  // randomStackChance (mapped from v13's randomArmies bool)
            _tightFormationChance,
            _randomTerrainChance,
            _leftVipChance,
            _rightVipChance,
            _battlefieldPattern,
            _manaMin, _manaMax,
            _swapSides,
            _loglevelGlobal, _loglevelAI, _loglevelStats,
            _statsMode, _statsStorage,
            60000,                  // statsTimeout (hardcoded, matching old behavior)
            _statsPersistFreq,
            // ML fix (2026-08-17): headless 参数化 — 环境变量 STRATEGIC_HEADLESS=0 启用 GUI (有头 MVP)
            // 默认 true (训练/采集无头零影响)
            getenv("STRATEGIC_HEADLESS") == nullptr || strcmp(getenv("STRATEGIC_HEADLESS"), "0") != 0   // headless
        );
        initargs->red = redAdventureAI;      // 冒险AI: red 玩家 (adventureAlliedAI)
        initargs->blue = blueAdventureAI;    // 冒险AI: blue/其他 (adventureEnemyAI)
        LOG("call init_vcmi");
        // Workaround: boost::filesystem::create_directories on symlink fails
        // Set XDG_DATA_HOME to a real directory before VCMI init
        // 09-23 路径环境化: 默认取 $HOME/.local/share, 不再硬编码用户名 (已设置则不覆盖)
        if (getenv("XDG_DATA_HOME") == nullptr) {
            const char* home = getenv("HOME");
            if (home != nullptr) {
                const std::string xdg = std::string(home) + "/.local/share";
                setenv("XDG_DATA_HOME", xdg.c_str(), 0);
            }
        }
        ML::init_vcmi((void*)initargs.get());
        LOG("init_vcmi returned OK");
        connstate = ConnectorState::INITIALIZED;
    }

    void Connector::start() {
        ASSERT_STATE("start", ConnectorState::INITIALIZED);

        setvbuf(stdout, NULL, _IONBF, 0);
        LOG("start (background thread)");

        LOG("obtain lock2");
        std::unique_lock lock2(m2);
        LOG("obtain lock2: done");

        LOG("release Python GIL");
        py::gil_scoped_release release;

        // Adventure mode: register callback before start_vcmi
        bool is_adventure = (_mapname.find("s1") != std::string::npos ||
                             _mapname.find("mini") != std::string::npos ||
                             _mapname.find("adventure") != std::string::npos ||
                             _mapname.find(".h3m") != std::string::npos);

        if (is_adventure) {
            LOG("Adventure mode — registering callback");
            g_adventure_cb = adventure_cb_trampoline;
            g_adventure_cb_userdata = this;
            register_adventure_delegate(handleAdventureCallback, (void*)this);
            _adventure_mode = true;
        } else {
            // Battle mode — wait for client connection
            std::function<bool()> predicate = [this] {
                return (connectedClient0 || red != "MMAI_USER")
                    && (connectedClient1 || blue != "MMAI_USER");
            };

            LOGFMT("cond2.wait(lock2, %1%s, predicate)", bootTimeout);
            auto res = cond_wait(__func__, 2, cond2, lock2, bootTimeout, predicate);
            if (res == ReturnCode::TIMEOUT) {
                throw VCMIConnectorException(boost::str(boost::format(
                    "timeout after %ds while waiting for client") % bootTimeout));
                return;
            } else if (res == ReturnCode::SHUTDOWN) {
                LOG("connector is shutting down...");
                return;
            } else if (res != ReturnCode::OK) {
                throw VCMIConnectorException(boost::str(boost::format(
                    "unexpected return code from cond_wait: %d") % EI(res)));
                return;
            }

            {
                LOG("obtain lock0");
                std::unique_lock lock0(m0);
                LOG("obtain lock0: done");
                LOG("obtain lock1");
                std::unique_lock lock1(m1);
                LOG("obtain lock1: done");
                LOG("release lock0 and lock1");
            }
        }

        LOG("set connstate = AWAITING_STATE");
        connstate = ConnectorState::AWAITING_STATE;

        LOG("release lock2");
        lock2.unlock();

        LOG("launch VCMI (will never return)");
        ML::start_vcmi();

        if (!_shutdown)
            std::cerr << "ERROR: ML::start_vcmi() returned, but shutdown is false";
    }
}  // namespace Connector::V13::Thread

// 跨库回调 — 在命名空间外定义，确保 extern "C" 兼容
extern "C" void adventure_yourTurn_callback_c(int playerColor, void* userData) {
    Connector::V13::Thread::Connector::handleAdventureCallback(playerColor, userData);
}

namespace Connector::V13::Thread {
void Connector::handleAdventureCallback(int playerColor, void* userData) {
    auto* conn = static_cast<Connector*>(userData);
    // 使用原子变量避免 mutex 死锁（adventure_wait 也在抢同一把锁）
    conn->_adventure_player.store(playerColor);
    conn->_adventure_action_ready.store(false);
    conn->_adventure_cond.notify_all();
    // 轮询等待 action（不 hold mutex）
    while (!conn->_adventure_action_ready.load() && !conn->_shutdown.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

// adventureWait: 用原子变量检查，不用 mutex
const std::tuple<int, std::string> Connector::adventureWait() {
    SHUTDOWN_PYTHON_RETURN("");
    // 通过 libmlclient.so 的原子变量通信 API 等待回合
    int player = adventure_wait_for_turn();
    if (_shutdown) return {static_cast<int>(ReturnCode::SHUTDOWN), ""};
    return {static_cast<int>(ReturnCode::OK), std::to_string(player)};
}

// adventureAct: 设置 action 信号
const std::tuple<int, std::string> Connector::adventureAct(int action) {
    SHUTDOWN_PYTHON_RETURN("");
    // 通过 libmlclient.so 的原子变量通信 API 发送 action
    adventure_send_action(action);
    return {static_cast<int>(ReturnCode::OK), "action_sent"};
}

void Connector::shutdown() {
    _shutdown = true;
    ML::shutdown_vcmi();
}
}
