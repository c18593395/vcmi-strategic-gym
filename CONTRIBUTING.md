# Contributing

Thanks for helping build VCMI Strategic Gym.

## Repository layout

```
connectors/   C++ pybind11 bridge into the VCMI engine (battle + strategic).
              Builds against VCMI release headers via CMake + conanfile.
envs/         Python envs. v13 carries the strategic (adventure map) stack:
              StrategicEnv, T13 protocol decoder, action space, rewards.
tools/        Arena, benchmark, smoke-test scripts.
```

## Quick start

```bash
# 1. VCMI engine (strategic server) — see README for the build path.
# 2. pybind11 sources at connectors/pybind11 (git-ignored), then the connector:
cd connectors
conan install . -of conan-generated --build=missing   # writes conan_toolchain.cmake used by the preset
cmake --preset vcmigym-rel && cmake --build rel
# 3. Env smoke test (needs libmlclient.so + connector .so on LD_LIBRARY_PATH)
python envs/v13/test_strategic_env.py
```

## CI

`python -m compileall` over `envs/` and `tools/` (syntax gate). Tests
themselves require a live VCMI server, so they are not run in CI; run them
locally in the WSL2 layout described in the README.

## Guidelines

- Keep the T13 wire protocol changes documented (field order is load-bearing;
  downstream parsers and on-disk exports assume it).
- `envs/v13/strategic_env.py` is the strategic reward/observation surface —
  reward changes are experiments; record them with the run config.
- C++ in `connectors/` must stay ABI-clean against VCMI release builds.
- One concern per PR; Chinese/English both fine for comments, English for
  public-facing docs.

## License

MIT (see LICENSE). VCMI engine itself is GPL-2.0+; the connector is a
separate process/plugin boundary and does not link engine code.
