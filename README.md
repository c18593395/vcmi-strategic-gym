# VCMI Strategic Gym

Reinforcement-learning training stack for **adventure-map (strategic) AI** in
[VCMI](https://github.com/vcmi/vcmi) — the open engine for Heroes of Might and Magic III.

The official VCMI ecosystem ships ML-based *combat* AIs (MMAI), but there is no
ML-driven *adventure/strategic* AI. This project fills that gap: a gym
environment over the VCMI server, PPO training pipelines, and model releases
that can be dropped into a VCMI build to play full maps (heroes, towns,
mines, battles).

> Status: active development. Engine-side pieces live in a companion
> `vcmi-native` fork; see the training docs for the build contract.

## Layout

```
connectors/   C++ pybind11 connectors (v13/v14/v15) bridging the VCMI engine and Python
envs/         Python environments (v13: strategic + battle, v14, v15)
tools/        arena / benchmarking utilities
```

## Prerequisites

| Requirement | Notes |
|---|---|
| Linux or WSL2, x86_64 | developed under WSL2 |
| CMake >= 3.16 + Make or Ninja | |
| Conan >= 2.13 | supplies Boost (`connectors/conanfile.py`; also pins pybind11 ~2.12) |
| Python >= 3.11 | numpy for the environments |
| VCMI engine build exporting `libmlclient` | **not upstream VCMI** — the strategic server API comes from the companion `vcmi-native` fork |
| pybind11 sources | must be present at `connectors/pybind11` (git-ignored) |

## Build the connector

```bash
# 1. pybind11 sources — connectors/CMakeLists.txt does add_subdirectory(pybind11)
git clone --depth 1 https://github.com/pybind/pybind11 connectors/pybind11

# 2. point the build at your engine checkout:
#    connectors/CMakeLists.txt:11   set(VCMI_DIR "/path/to/vcmi-native")

# 3. configure + build
cd connectors
conan install . -of conan-generated --build=missing
cmake --preset vcmigym-rel
cmake --build rel -j
```

Artifacts: `connectors/rel/connector_v13.so` (plus `connector_v14.so`,
`connector_v15.so`). The build expects the engine library at
`${VCMI_DIR}/rel/bin/libmlclient.so`.

## Run

Environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `STRATEGIC_STATE_LIB` | path to `libmlclient.so` | `${VCMI_DIR}/rel/bin/libmlclient.so` |
| `LD_LIBRARY_PATH` | must include `connectors/rel` and `${VCMI_DIR}/rel/bin` | — |
| `XDG_DATA_HOME` | VCMI data directory (maps, mods) | `~/.local/share` |

Smoke test:

```bash
export LD_LIBRARY_PATH="$PWD/connectors/rel:${VCMI_DIR}/rel/bin:$LD_LIBRARY_PATH"
export STRATEGIC_STATE_LIB="${VCMI_DIR}/rel/bin/libmlclient.so"
python envs/v13/test_strategic_env.py
```

Two caveats before you run anything:

- The scripts under `envs/v13/` carry the author's WSL2 layout as module-level
  constants (`VCMI_REL`, `CONN_REL`, `VENV_PYTHON`, ...) — edit them to match
  your own paths.
- Maps are **not** shipped here (`*.vmap` is git-ignored, as is
  `envs/v13/maps/`). Point the environment at a map that exists in your VCMI
  data directory.

## Environments

`envs/v13` is the strategic (adventure-map) stack: `StrategicEnv` drives a
hero-vs-hero map through the VCMI server and exposes a 3464-float observation
vector plus 25 discrete actions (8 movement directions, end-turn, town/hero
targeting, recruit/build, pathfinding-assisted move). The battle side
(`vcmi_env.py`, `decoder/`) is the MMAI-compatible combat environment.

`envs/v14` and `envs/v15` are ports of the same interface to newer engine
versions.

## Training

The training harness itself — curriculum over hand-built maps, reward shaping,
checkpointing, evaluation profiles — is not in this repository yet; it lives in
the companion `hero3_fresh` workspace together with the `vcmi-native` fork.
What this repository provides is the reusable half: connector, environment, and
the T13 wire protocol.

## CI

`.github/workflows/ci.yml` runs `python -m compileall` over `envs/` and
`tools/` as a syntax gate. The `test_*` scripts need a live VCMI server and an
engine checkout, so they are not CI-runnable.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT (this repository). VCMI engine code is GPL-2.0+.
