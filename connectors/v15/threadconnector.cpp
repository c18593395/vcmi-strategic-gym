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
#include "ML/model_wrappers/function.h"
#include "ML/MLClient.h"
#include "common.h"
#include "schema/base.h"
#include "schema/v15/constants.h"
#include "schema/v15/graph.h"
#include "schema/v15/types.h"
#include "ML/model_wrappers/scripted.h"
#include "ML/model_wrappers/path.h"
#include "exporter.h"

#include <chrono>
#include <condition_variable>
#include <csignal>
#include <mutex>
#include <pybind11/cast.h>
#include <pybind11/pybind11.h>
#include <pybind11/detail/common.h>
#include <pybind11/stl.h>

#include <stdexcept>
#include <random>
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

namespace {
    int RandomValidAction(const MMAI::Schema::IState * s) {
        auto any = s->getSupplementaryData();
        const auto * sup = std::any_cast<const MMAI::Schema::V15::ISupplementaryData*>(any);
        const auto * G = sup->getGraph();

        auto activeIds = G->getActiveActionIds();

        if (activeIds.empty()) {
            std::cout << "No valid actions => reset\n";
            return MMAI::Schema::ACTION_RESET;
        }

        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dist(0, static_cast<int>(activeIds.size()) - 1);
        int randomIndex = dist(gen);
        const auto id = activeIds[randomIndex];
        return static_cast<int>(id);
    }
}

namespace Connector::V15::Thread {
    namespace S15 = MMAI::Schema::V15;

    std::vector<std::string> Connector::getLogs() {
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
            % static_cast<int64_t>(getpid())
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

    const MMAI::Schema::V15::ISupplementaryData* Connector::extractSupplementaryData(const MMAI::Schema::IState *s) {
        LOG("Extracting supplementary data...");
        auto any = s->getSupplementaryData();
        if(!any.has_value()) throw std::runtime_error("extractSupplementaryData: supdata is empty");
        const auto & t = typeid(const MMAI::Schema::V15::ISupplementaryData*);
        auto err = MMAI::Schema::AnyCastError(any, typeid(const MMAI::Schema::V15::ISupplementaryData*));

        if(!err.empty()) {
            LOGFMT("anycast for getSumpplementaryData error: %s", err);
        }

        return std::any_cast<const MMAI::Schema::V15::ISupplementaryData*>(s->getSupplementaryData());
    };

    py::dict Connector::buildObsDict(const MMAI::Schema::IState * s) {
        LOG("Convert IState -> p_dict");
        const auto * sup = extractSupplementaryData(s);
        assert(sup->getType() == MMAI::Schema::V15::ISupplementaryData::Type::REGULAR);

        const auto * G = sup->getGraph();

        auto nodeTypeMap = std::unordered_map<S15::Graph::ElementType, std::string>{};

        auto p_nodesdict = py::dict();
        for (const auto & [type, name, size] : MMAI::Schema::V15::NODE_TYPES)
        {
            const auto & nodes = G->getNodes(type);
            const auto N = static_cast<py::ssize_t>(nodes.size());
            const auto D = static_cast<py::ssize_t>(size);

            auto p_attrs = py::array_t<float, py::array::c_style>({N, D});
            auto info = p_attrs.request();
            auto * ptr = static_cast<float*>(info.ptr);
            auto out = std::span<float>(ptr, N * D);

            std::ranges::fill(out, 0.0f);

            for (std::size_t j = 0; j < N; ++j)
            {
                auto row = out.subspan(j * D, D);
                int written = nodes[j]->encode(row);
                assert(written == D);
            }

            p_nodesdict[py::str(name)] = p_attrs;
            nodeTypeMap.emplace(type, name);
        }

        auto p_edgesdict = py::dict();
        for (const auto & [type, name, endpoints, size] : MMAI::Schema::V15::EDGE_TYPES)
        {
            auto p_edict = py::dict();

            const auto & edges = G->getEdges(type);
            const auto E = static_cast<py::ssize_t>(edges.size());
            const auto D = static_cast<py::ssize_t>(size);

            auto p_attrs = py::array_t<float, py::array::c_style>({E, D});
            auto p_index = py::array_t<int64_t, py::array::c_style>({static_cast<py::ssize_t>(2), E});
            auto mp_index = p_index.mutable_unchecked<2>();

            auto info = p_attrs.request();
            auto * ptr = static_cast<float*>(info.ptr);
            auto out = std::span<float>(ptr, E * D);
            std::ranges::fill(out, 0.0f);

            for (std::size_t j = 0; j < E; ++j)
            {
                auto row = out.subspan(j * D, D);
                const auto * edge = edges[j];
                int written = edge->encode(row);
                if (written != D)
                    throw std::runtime_error("written: " + std::to_string(written) + ": expected: " + std::to_string(D) + " ET=" + std::to_string(EI(edge->getType())));
                assert(written == D);

                const auto & [srcNode, dstNode] = edge->endpoints();
                int64_t isrc = G->getNodeIndex(srcNode);
                int64_t idst = G->getNodeIndex(dstNode);
                mp_index(0, static_cast<py::ssize_t>(j)) = isrc;
                mp_index(1, static_cast<py::ssize_t>(j)) = idst;
            }

            p_edict[py::str("index")] = p_index;
            p_edict[py::str("attrs")] = p_attrs;

            const auto & [src_type, dst_type] = endpoints;
            const auto & src_name = nodeTypeMap.at(src_type);
            const auto & dst_name = nodeTypeMap.at(dst_type);
            const auto key = py::make_tuple(
                py::str(src_name),
                py::str(name),
                py::str(dst_name)
            );
            p_edgesdict[key] = p_edict;
        }

        const auto & activeActionIds = G->getActiveActionIds();
        const auto A = static_cast<py::ssize_t>(activeActionIds.size());
        auto p_activeids = py::array_t<int64_t, py::array::c_style>(A);
        auto mp_activeids = p_activeids.mutable_unchecked<1>();

        // std::stringstream ss;
        // ss << "<CONN> activeActionIds: [";
        for (ssize_t i = 0; i < activeActionIds.size(); ++i)
        {
            mp_activeids(i) = activeActionIds[i];
            // ss << activeActionIds[i] << ", ";
        }
        // ss << "] </CONN>\n";
        // std::cout << ss.str() << std::flush;

        LOG("Creating p_dict...");

        return py::dict(
            py::arg("nodes") = p_nodesdict,
            py::arg("edges") = p_edgesdict,
            py::arg("active_action_ids") = p_activeids
        );
    }

    ReturnCode Connector::getState(const char* funcname, int side, MMAI::Schema::Action action_) {
        LOGFMT("%s called with side=%d", funcname % side);

        auto expstate = side ? ConnectorState::AWAITING_ACTION_1 : ConnectorState::AWAITING_ACTION_0;
        auto &m = side ? m1 : m0;
        auto &cond = side ? cond1 : cond0;

        LOGFMT("obtain lock%d", side);
        std::unique_lock lock(m);
        LOGFMT("obtain lock%d: done", side);

        // T12-PRE.1.5e-fix (09-29): 持锁校验 connstate 进入态 (替代无锁 ASSERT_STATE)。
        // 原 ASSERT_STATE 在锁外读 connstate, 与引擎线程 start() 持锁写 connstate=AWAITING_STATE
        // 形成跨线程数据竞争 → 读到中间态 → 误判 throw。现改为锁内读 connstate 校验,
        // 消除竞争; 若进入态不符 (如引擎线程已置 AWAITING_STATE), 记录 _error 供后续 throw,
        // 而非直接中断 (getAction 持锁检查会二次确认)。
        if (connstate != expstate) {
            LOGFMT("%s: connstate=%d, expected %d (entering getState)",
                funcname % EI(connstate) % EI(expstate));
            SET_ERROR(boost::str(boost::format(
                "%s: unexpected connector state at entry: want: %d, have: %d") \
                % funcname % EI(expstate) % EI(connstate)));
        }

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

    std::tuple<int, std::string> Connector::render(int side) {
        SHUTDOWN_PYTHON_RETURN("");
        auto code = getState(__func__, side, MMAI::Schema::ACTION_RENDER_ANSI);
        const auto * sup = extractSupplementaryData(state);
        assert(sup->getType() == MMAI::Schema::V15::ISupplementaryData::Type::ANSI_RENDER);
        LOG("return state->ansiRender");
        return {static_cast<int>(code), sup->getAnsiRender()};
    }

    std::tuple<int, py::dict> Connector::reset(int side) {
        SHUTDOWN_PYTHON_RETURN({}); // 引擎收局后不读悬空 state, 返回空 dict
        if (state == nullptr) {
            LOG("reset: state is null (engine not started or state not filled), returning empty dict");
            return {static_cast<int>(ReturnCode::SHUTDOWN), py::dict()};
        }
        auto code = getState(__func__, side, MMAI::Schema::ACTION_RESET);
        // getState 的 pred (connstate==expstate || _shutdown) 满足后, 引擎侧 getAction 可能
        // 已随引擎线程收局 (runServer EXIT) 而不再更新 state; 引擎自然收局路径下
        // shutdown_vcmi 释放 GAME/BAI state 前 connstate 可能停留在 AWAITING_STATE。
        // 若 _error 非空 (getState 持锁校验发现状态竞争) 或 code 为 TIMEOUT/SHUTDOWN,
        // 不读 state (可能已释放) → 直接返回 SHUTDOWN, 防悬空指针 segfault。
        if (!_error.empty() || code == ReturnCode::TIMEOUT || code == ReturnCode::SHUTDOWN) {
            LOG("reset: getState returned code=" + std::to_string(static_cast<int>(code))
                + " or _error set; not reading state (may be dangling after engine shutdown)");
            return {static_cast<int>(code), py::dict()};
        }
        if (state == nullptr) {
            LOG("reset: state became null after getState, returning empty dict");
            return {static_cast<int>(code), py::dict()};
        }
        const auto p_dict = buildObsDict(state);
        LOG("return p_dict");
        return {static_cast<int>(code), p_dict};
    }

    std::tuple<int, py::dict> Connector::step(int side, MMAI::Schema::Action a) {
        SHUTDOWN_PYTHON_RETURN({}); // 引擎收局后不读悬空 state, 返回空 dict
        if (state == nullptr) {
            LOG("step: state is null (engine not started or state not filled), returning empty dict");
            return {static_cast<int>(ReturnCode::SHUTDOWN), py::dict()};
        }
        auto code = getState(__func__, side, a);
        // 同 reset: getState 返回 TIMEOUT/SHUTDOWN 或 _error 非空时, state 可能已释放,
        // 不读 state → 直接返回 code + 空 dict, 防悬空指针 segfault。
        if (!_error.empty() || code == ReturnCode::TIMEOUT || code == ReturnCode::SHUTDOWN) {
            LOG("step: getState returned code=" + std::to_string(static_cast<int>(code))
                + " or _error set; not reading state (may be dangling after engine shutdown)");
            return {static_cast<int>(code), py::dict()};
        }
        if (state == nullptr) {
            LOG("step: state became null after getState, returning empty dict");
            return {static_cast<int>(code), py::dict()};
        }
        const auto p_dict = buildObsDict(state);
        LOG("return p_dict");
        return {static_cast<int>(code), p_dict};
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
            // need to explicitly print the logs here
            // (this exception won't be handled by python)
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
    std::tuple<int, py::dict> Connector::connect(int side) {
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

        if (res == ReturnCode::TIMEOUT) {
            // T12-PRE.1.3: enhance guard with diagnostic hint
            auto logs_snapshot = getLogs();
            std::string tail;
            for (size_t i = std::max<size_t>(0, logs_snapshot.size() - 10); i < logs_snapshot.size(); ++i)
                tail += logs_snapshot[i] + "\n";
            throw VCMIConnectorException(boost::str(boost::format(
                "connect side=%d TIMEOUT after %ds (connstate=%d, expstate=%d, shutdown=%d, loglines=%d)\n"
                "hint: engine likely failed init or map path missing; check VCMI_Client_log.txt + rel/bin/Maps/\n"
                "last log lines:\n%s") \
                % side % bootTimeout % EI(connstate) % EI(expstate) \
                % _shutdown.load() % static_cast<int>(logs_snapshot.size()) % tail.c_str()));
        } else if (res == ReturnCode::SHUTDOWN) {
            LOG("connector is shutting down...");
            throw VCMIConnectorException("connector shutdown while waiting for state (side:" + std::to_string(side) + ")");
        }

        // T12-PRE.1.5e-fix (09-29): connect 完成时校验 state 指针,
        // 防止 buildObsDict 读坏指针 (引擎侧 battleStart 回调未填 state 时)。
        if (state == nullptr) {
            // 引擎线程 start() 收局路径 (start_vcmi 正常返回) 下, 引擎已释放 BAI state,
            // 但 connector 侧 state 指针仍指向已释放内存。此时不再读 state → 返回空 dict,
            // 让 python 侧 __init__ 的 reset() 拿到 SHUTDOWN 码而非悬空指针 → 防 segfault。
            // 正常 boot 路径 (引擎未收局) 下 state 由首场 battle 的 getAction 填充, 非 null。
            LOG("connect: state is nullptr (engine already shut down or state not filled), "
                "returning empty dict to avoid reading dangling pointer");
            auto py_dict = py::dict();
            LOGFMT("release lock%d (return)", side);
            return {static_cast<int>(ReturnCode::SHUTDOWN), py_dict};
        }

        auto py_dict = buildObsDict(state);
        LOGFMT("release lock%d (return)", side);
        LOG("return p_dict");
        return {static_cast<int>(res), py_dict};
    }

    void Connector::start() {
        ASSERT_STATE("start", ConnectorState::NEW);

        setvbuf(stdout, nullptr, _IONBF, 0);
        LOG("start");

        // struct sigaction sa;
        // sa.sa_handler = signal_handler;
        // sa.sa_flags = 0;
        // sigemptyset(&sa.sa_mask);

        // if (sigaction(SIGINT, &sa, nullptr) == -1)
        //     throw std::runtime_error("Error installing signal handler.");

        LOG("obtain lock2");
        std::unique_lock lock2(m2);
        LOG("obtain lock2: done");

        LOG("release Python GIL");
        py::gil_scoped_release release;

        std::function<bool()> predicate = [this] {
            return (connectedClient0 || red != "MMAI_USER")
                && (connectedClient1 || blue != "MMAI_USER");
        };

        LOGFMT("cond2.wait(lock2, %1%s, predicate)", bootTimeout);
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
            // Successfully obtaining these locks means the
            // clients are ready and waiting for state
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
            // BAI will load the actual model based on leftModel->getName()
            leftModel = new ML::ModelWrappers::Path(redModel);
        } else {
            leftModel = new ML::ModelWrappers::Scripted(red, Side::LEFT);
        }

        if (blue == "MMAI_RANDOM") {
            rightModel = new ML::ModelWrappers::Function(version(), "MMAI_RANDOM", Side::RIGHT, f_getRandomAction, f_getValueDummy);
        } else if (blue == "MMAI_USER") {
            rightModel = new ML::ModelWrappers::Function(version(), "MMAI_USER_GYM", Side::RIGHT, f_getAction1, f_getValueDummy);
        } else if (blue == "MMAI_MODEL") {
            // BAI will load the actual model based on rightModel->getName()
            rightModel = new ML::ModelWrappers::Path(blueModel);
        } else {
            rightModel = new ML::ModelWrappers::Scripted(blue, Side::RIGHT);
        }

        // auto oldcwd = std::filesystem::current_path();

        // This must happen in the main thread (SDL requires it)
        initargs = std::make_unique<ML::InitArgs>(
            _mapname, leftModel, rightModel,
            _redAllowMlBot, _blueAllowMlBot,
            0,                      // maxBattles (hardcoded, matching old behavior)
            _seed,
            _randomHeroes, _randomObstacles, _townChance, _warmachineChance,
            _randomArmies ? 100 : 0,  // randomStackChance (mapped from v15's randomArmies bool)
            _tightFormationChance,
            _randomTerrainChance,
            _leftVipChance, _rightVipChance,
            _battlefieldPattern,
            _manaMin, _manaMax,
            _swapSides,
            _loglevelGlobal, _loglevelAI, _loglevelStats,
            _statsMode, _statsStorage,
            60000,                  // statsTimeout (hardcoded, matching old behavior)
            _statsPersistFreq,
            true                    // headless
        );
        // T12-PRE.2.1 (09-29): 显式写 red/blue 进 InitArgs。
        // 不写则引擎侧拿成员默认值 red="MMAI"/blue="Nullkiller2" (全仓无赋值点),
        // MLClient V15 分支 if(a.blue=="MMAI_USER") 永不触发 → 蓝方落 NK2 (C++ 自主 AI,
        // 不走 connector getAction(1)) → side=1 connstate 永停 AWAITING_STATE → connect 死等。
        // 对真 C++ 对手档 (NK2/StupidAI 等) 行为零变化 (写进去的就是同名默认值)。
        initargs->red = red;
        initargs->blue = blue;
        LOG("call init_vcmi(...)");
        try {
            // T12-PRE.1.5e (09-29, V15 门控): 注册引擎收局通知钩子。
            // 引擎 start_vcmi 收局后调 shutdown_vcmi → 触发此回调,
            // 在 GAME.reset (释放 BAI state) 之前置 _shutdown=true + notify_all,
            // 使后续 python 侧 reset/step 走 SHUTDOWN_PYTHON_RETURN 兜底路径,
            // 不再读悬空 state 指针 (防 segfault)。
            ML::registerShutdownCallback([this]() {
                LOG("[shutdown-hook] engine gameOver, setting _shutdown + notify");
                _shutdown = true;
                cond0.notify_all();
                cond1.notify_all();
                cond2.notify_all();
            });

            ML::init_vcmi((void*)initargs.get());
        } catch (const std::exception &e) {
            // T12-PRE.1.3: engine init failure -> propagate shutdown to all waiting threads
            LOG(std::string("init_vcmi failed: ") + e.what());
            _shutdown = true;
            cond0.notify_all();
            cond1.notify_all();
            cond2.notify_all();
            throw VCMIConnectorException(std::string("init_vcmi failed: ") + e.what());
        }

        LOG("set connstate = AWAITING_STATE");
        // T12-PRE.1.5e-fix (09-29): 引擎线程 start() 的 connstate 写点原为无锁,
        // 与 getState/getAction 的 ASSERT_STATE 检查竞争 (getState 要求进入态
        // AWAITING_ACTION_0, 引擎线程无锁写 AWAITING_STATE 破坏状态机时序)。
        // 改持 m0 锁 + notify_all, 与 getState/getAction 锁协议一致, 消除无锁写竞争。
        {
            std::unique_lock lock0(m0);
            connstate = ConnectorState::AWAITING_STATE;
        }
        cond0.notify_all();

        LOG("release lock2");
        lock2.unlock();

        LOG("launch VCMI (will never return)");
        try {
            ML::start_vcmi();
        } catch (const std::exception &e) {
            LOG(std::string("start_vcmi raised: ") + e.what());
            _shutdown = true;
            cond0.notify_all();
            cond1.notify_all();
            throw VCMIConnectorException(std::string("start_vcmi failed: ") + e.what());
        }

        if (!_shutdown)
            std::cerr << "ERROR: ML::start_vcmi() returned, but shutdown is false";
    }

    void Connector::shutdown() {
        if (_shutdown) {
            LOG("shutdown: already in shutdown state, skipping duplicate ML::shutdown_vcmi call");
            return;
        }
        _shutdown = true;
        ML::shutdown_vcmi();
    }
}
