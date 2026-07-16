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

#define ASSERT_STATE(id, want) { \
    if((want) != (connstate)) \
        throw VCMIConnectorException(std::string(id) + ": unexpected connector state: want: " + std::to_string(EI(want)) + ", have: " + std::to_string(EI(connstate))); \
}

// Python does not know about some threads and exceptions thrown there
// result in abrupt program termination.
// => use this to set a member var `_error`
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

    // ====================================================================
    // Adventure mode callback - called by VCMI thread when it is the
    // user's turn on the adventure map.
    // ====================================================================
    void adventure_yourTurn_callback(int player, void* ctx) {
        auto* conn = static_cast<Connector*>(ctx);
        std::unique_lock lock(conn->_adventure_mutex);
        conn->_adventure_player = player;
        conn->_adventure_action_ready = true;
        conn->_adventure_cond.notify_all();
    }

    const std::vector<std::string> Connector::getLogs() {
        return std::vector<std::string>(logs.begin(), logs.end());
    }

    void Connector::log(std::string funcname, std::string msg) {
#if VERBOSE || LOGCOLLECT
        boost::posix_time::ptime t = boost::posix_time::microsec_clock::universal_time();

        std::string entry = boost::str(boost::format("++ %s <%ld/%s>[GIL=%d] <%s> %s")
            % boost::posix_time::to_iso_extended_string(t)
            % static_cast<long>(getpid())
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
#endif

#if VERBOSE
        {
            std::unique_lock lock(mlog);
            std::cout << entry << "\n";
        }
#endif
#endif
    }

    void Connector::maybeThrowError() {
        if (!_error.empty()) {
            auto e = _error;
            _error = "";
            throw VCMIConnectorException(e);
        }
    }

    ReturnCode Connector::_cond_wait(const char* funcname, int id, std::condition_variable &cond, std::unique_lock<std::mutex> &l, int timeoutSeconds, std::function<bool()> &checker) {
        ReturnCode res;
        auto start = std::chrono::high_resolution_clock::now();

        while (true) {
            auto fres = checker();

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

    const MMAI::Schema::V13::ISupplementaryData* Connector::extractSupplementaryData(const MMAI::Schema::IState *s) {
        LOG("Extracting supplementary data...");
        auto any = s->getSupplementaryData();
        if(!any.has_value()) throw std::runtime_error("extractSupplementaryData: supdata is empty");
        auto err = MMAI::Schema::AnyCastError(any, typeid(const MMAI::Schema::V13::ISupplementaryData*));

        if(!err.empty()) {
            LOGFMT("anycast error: %s", err);
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
                throw std::runtime_error("attrs size mismatch: " + std::to_string(attrs.size()) + " / " + std::to_string(flatattrsize));

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
        SHUTDOWN_PYTHON_RETURN(convertState(state));
        auto code = getState(__func__, side, MMAI::Schema::ACTION_RESET);
        auto pstate = convertState(state);
        LOG("return P_State");
        return {static_cast<int>(code), pstate};
    }

    const std::tuple<int, P_State> Connector::step(int side, MMAI::Schema::Action a) {
        SHUTDOWN_PYTHON_RETURN(convertState(state));
        auto code = getState(__func__, side, a);
        auto pstate = convertState(state);
        LOG("return P_State");
        return {static_cast<int>(code), pstate};
    }

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

        LOGFMT("cond%1%.wait(lock%1%)", side);
        auto res = cond_wait(__func__, side, cond, lock, userTimeout, pred);
        LOGFMT("cond%1%.wait(lock%1%): done", side);

        SHUTDOWN_VCMI_RETURN(MMAI::Schema::ACTION_RESET);

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

    void Connector::start() {
        ASSERT_STATE("start", ConnectorState::NEW);

        setvbuf(stdout, NULL, _IONBF, 0);
        LOG("start");

        LOG("obtain lock2");
        std::unique_lock lock2(m2);
        LOG("obtain lock2: done");

        LOG("release Python GIL");
        py::gil_scoped_release release;

        std::function<bool()> predicate = [this] {
            return (connectedClient0 || red != "MMAI_USER")
                && (connectedClient1 || blue != "MMAI_USER");
        };

        LOGFMT("cond2.wait(lock2, %ds, predicate)", bootTimeout);
        auto res = cond_wait(__func__, 2, cond2, lock2, bootTimeout, predicate);
        if (res == ReturnCode::TIMEOUT) {
            throw VCMIConnectorException(boost::str(boost::format(
                "timeout after %ds while waiting for client (red:%s, blue:%s, connectedClient0: %d, connectedClient1: %d)\n") \
                % bootTimeout % red % blue % connectedClient0 % connectedClient1
            ));
            return;
        } else if (res == ReturnCode::SHUTDOWN) {
            LOG("connector is shutting down...");
            return;
        } else if (res != ReturnCode::OK) {
            throw VCMIConnectorException(boost::str(boost::format(
                "unexpected return code from cond_wait: %d\n") % EI(res)
            ));
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

        using Side = MMAI::Schema::Side;

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

        LOG("call init_vcmi(...)");
        init_vcmi(leftModel, rightModel, initargs);

        LOG("set connstate = AWAITING_STATE");
        connstate = ConnectorState::AWAITING_STATE;

        LOG("release lock2");
        lock2.unlock();

        LOG("launch VCMI (will never return)");
        ML::start_vcmi();

        if (!_shutdown)
            std::cerr << "ERROR: ML::start_vcmi() returned, but shutdown is false";
    }

    void Connector::shutdown() {
        _shutdown = true;

        // Unblock any adventure waiters so they can observe _shutdown
        _adventure_cond.notify_all();

        // *** FIX: Signal VCMI to exit gracefully ***
        //
        // Previously shutdown() only set _shutdown and notified _adventure_cond.
        // It did NOT call ML::shutdown_vcmi(), so the VCMI thread stayed
        // blocked inside cond_shutdown.wait() inside ML::start_vcmi().
        //
        // When Python later destroyed the Connector object, the VCMI thread
        // was still running, causing a segfault/terminate during cleanup.
        //
        // ML::shutdown_vcmi() signals cond_shutdown, which unblocks
        // ML::start_vcmi(), allows it to join the VCMI thread and exit
        // cleanly via quitApplicationImmediately(0).
        ML::shutdown_vcmi();
    }

    // ====================================================================
    // Adventure mode
    // ====================================================================

    const std::tuple<int, std::string> Connector::adventureWait() {
        LOG("adventureWait: waiting for yourTurn callback...");

        std::unique_lock lock(_adventure_mutex);

        std::function<bool()> pred = [this] {
            return _adventure_action_ready || _shutdown;
        };

        auto res = cond_wait(__func__, 9, _adventure_cond, lock, vcmiTimeout, pred);

        if (_shutdown)
            return {static_cast<int>(ReturnCode::SHUTDOWN), ""};

        if (res != ReturnCode::OK)
            return {static_cast<int>(res), ""};

        _adventure_action_ready = false;

        LOGFMT("adventureWait: player=%d", _adventure_player);
        return {static_cast<int>(ReturnCode::OK), std::to_string(_adventure_player)};
    }

    const std::tuple<int, std::string> Connector::adventureAct(int action) {
        LOGFMT("adventureAct: action=%d", action);

        std::unique_lock lock(_adventure_mutex);

        _adventure_action = action;
        _adventure_action_ready = false;
        _adventure_cond.notify_all();

        std::function<bool()> pred = [this] {
            return _adventure_action_ready || _shutdown;
        };

        auto res = cond_wait(__func__, 10, _adventure_cond, lock, vcmiTimeout, pred);

        if (_shutdown)
            return {static_cast<int>(ReturnCode::SHUTDOWN), ""};

        if (res != ReturnCode::OK)
            return {static_cast<int>(res), ""};

        _adventure_action_ready = false;

        LOGFMT("adventureAct: player=%d", _adventure_player);
        return {static_cast<int>(ReturnCode::OK), std::to_string(_adventure_player)};
    }
}
