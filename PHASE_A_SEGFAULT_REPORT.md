# Phase A VCMI segfault — 完整技术报告

## 一、症状

VCMI Gym (smanolloff fork) 启动冒险地图（或任何战斗地图）后约 6 秒，`runNetwork` 线程在 `libvcmi.so` 中 SEGV。

```
dmesg: runNetwork[PID]: segfault at 628 ip 0x... sp 0x... error 4 in libvcmi.so[base+a98000]
```

- **信号**: SIGSEGV (11)
- **错误码**: 4 (用户态读访问)
- **访问地址**: 0x628（空指针 + 0x628 偏移）
- **线程**: `runNetwork` — VCMI 服务器线程
- **目标库**: `libvcmi.so`
- **触发条件**: 任何地图加载（战斗图 A1-A7 和冒险图 .h3m 都崩溃）

## 二、调用栈

### addr2line 解析 1（原始 crash）
```
offset 0x4D8F04 → _ZN11CProxyIOApi8openFileERKN5boost10filesystem4pathEi
                 = CProxyIOApi::openFile(boost::filesystem::path const&, int)
                 → 源文件: lib/filesystem/MinizipExtensions.cpp:265
```

### addr2line 解析 2（Phase A 修复 CProxyIOApi 后，crash 前移）
```
offset 0x4DAFA4 → _ZN14EResTypeHelper20getTypeFromExtensionENSt7__cxx1112basic_string...
                 = EResTypeHelper::getTypeFromExtension(std::string)
                 → 源文件: lib/filesystem/ResourcePath.cpp:89
```

### addr2line 解析 3（原始库，未修 CProxyIOApi 时）
```
offset 0x4D8364 → _ZN13CProxyROIOApi8openFileERKN5boost10filesystem4pathEi
                 = CProxyROIOApi::openFile(boost::filesystem::path const&, int)
```

### Python 端完整错误日志（VCMI fatal error）
```
[global] ERROR Disaster happened.
[global] ERROR Reason: Resource with name DATA/LCDESC and type TEXT wasn't found.
[global] ERROR Call stack:
  0# libvcmi.so (unknown)
  1# libstdc++.so.6
  2# std::unexpected()
  3# libstdc++.so.6
  4# libvcmi.so
  5# CLegacyConfigParser::CLegacyConfigParser(ResourcePathTempl<(EResType)0> const&)
  6# CGeneralTextHandler::readToVector(...)
  7# CGeneralTextHandler::CGeneralTextHandler()
  8# GameLibrary::initializeLibrary()
  9# libmlclient.so (MLClient or ThreadConnector init)
```

## 三、调用链（推断）

```
ThreadConnector.start() → VCMI debugStartTest()
  → GameLibrary::initializeLibrary()
    → CGeneralTextHandler 初始化
      → CLegacyConfigParser 加载 "DATA/LCDESC"
        → CProxyIOApi/CProxyROIOApi::openFile()  ← data 指针为空
          → data->seek(0) → NULL 解引用 → SEGV at 0x628

或:
  → 服务器循环 (runNetwork)
    → CFilesystemLoader::getFiles()
      → EResTypeHelper::getTypeFromExtension()
        → 传入的字符串来自已损坏的迭代器 → 空指针读取 → SEGV at 0x628
```

## 四、根因

**VCMI 文件系统未完全初始化**，具体表现：

1. `data` symlink 被 cmake 反复覆盖，导致 VCMI 找不到游戏数据文件
2. `CProxyIOApi::openFile` 和 `CProxyROIOApi::openFile` 的 `data` 成员指针为 NULL（对应的 CInputStream/CInputOutputStream 未创建）
3. 在 ServerPlugin 构造函数执行后，VCMI 主循环尝试访问游戏资源时崩溃
4. 这是一个**级联空指针崩溃**——修一个 null check，下一个位置继续崩

与官方 vcmi/vcmi 无关——**这是 smanolloff 自定义 VCMI fork 的特有问题**：
- smanolloff/vcmi fork 基于 2025-11-19 的上游，落后 8 个月
- adventure API + ServerPlugin 是 smanolloff 自定义代码，从未进入上游
- 该 segault 在 smanolloff/vcmi-gym 项目中有 0 个 issue 提及（因为无人端到端测试过冒险 API）

## 五、已尝试的修复

### 5.1 ServerPlugin.cpp（4 处，全部通过）
```
1. tempOwner != 0/1 → continue 跳过 (原: throw)
2. Owners have different pools → 当 randomHeroes>0 时跳过检查
3. Owners have differently sized pools → 同上
4. randomHeroes requires 1 hero → 降级为 warning
```
文件: `D:\Bigdata\hero3_fresh\vcmi\server\ML\ServerPlugin.cpp`

### 5.2 MinizipExtensions.cpp（2 处，未能阻止级联崩溃）
```
1. CProxyIOApi::openFile → 加 !data 空检查 (logGlobal 未初始化则用 fprintf)
2. CProxyROIOApi::openFile → 同上
```
文件: `D:\Bigdata\hero3_fresh\vcmi\lib\filesystem\MinizipExtensions.cpp`

### 5.3 数据目录（合并方案）
创建了 `data-combined/` 目录，同时包含 VCMI 源数据和游戏数据：
```
data-combined/
  config/ → /home/administrator/vcmi-native/data/config/  (+ filesystem.json 复制)
  Mp3/ → /home/administrator/vcmi-native/data/Mp3/
  Sprites/ → /home/administrator/vcmi-native/data/Sprites/
  Data/ → /mnt/d/GAMES/Heroes3/Data/
  Maps/ → /mnt/d/GAMES/Heroes3/Maps/
```
仍 segfault。

## 六、关键文件位置

| 文件 | 路径 |
|------|------|
| ServerPlugin | `vcmi\server\ML\ServerPlugin.cpp` |
| MinizipExtensions | `vcmi\lib\filesystem\MinizipExtensions.cpp` |
| ResourcePath | `vcmi-native/lib/filesystem/ResourcePath.cpp` |
| CFilesystemLoader | `vcmi-native/lib/filesystem/CFilesystemLoader.cpp` |
| MLClient (init_vcmi) | `vcmi\ML\MLClient.cpp` |
| ThreadConnector | `vcmi_gym\connectors\v13\threadconnector.cpp` |
| Connector pybind11 | `vcmi_gym\connectors\v13\connector.cpp` |
| StrategicEnv | `strategic_env.py` |
| 测试脚本 | `test_phase_a.py`, `test_a7_serpent.py` |
| 环境检测 | `check_v13_env.py` |

## 七、建议修复方向

### 方案 A：修复 VCMI 文件系统初始化（推荐）
在 `CFilesystemLoader::getFiles()` 入口加 `if (!this)` 防护。但 root cause 是需要找到**为什么文件系统没初始化**——可能是 `initializeLibrary()` 的顺序问题，或者 `libmlclient.so` 的钩子太早触发了资源访问。

### 方案 B：对比 Phase A commit 前后的差异
Phase A commit `86b8c2c7a` 加了 adventure API 代码。对比 `0e2605fde`（前一个 commit）与 `86b8c2c7a` 的差异，看改了什么导致文件系统出问题。

### 方案 C：升级 VCMI fork
smanolloff/vcmi fork 基于 2025-11，落后官方 vcmi/vcmi 8 个月。拉取官方最新并合并 smanolloff 的自定义代码。

### 方案 D：从头编译全部组件
目前 libmlclient.so、libvcmi.so、connector_v13.so 来自不同批次的编译，混合了新旧代码。全部从同一源树重新编译干净版本。

## 八、GDB 安装命令
```bash
sudo apt-get install -y gdb
```
然后:
```bash
cd /home/administrator/vcmi-workspace
LD_LIBRARY_PATH=/home/administrator/vcmi-native/rel/bin:/home/administrator/vcmi-workspace/vcmi_gym/connectors/rel \
  gdb -batch -ex "run" -ex "bt 30" -ex "thread apply all bt 10" \
  --args python3 /mnt/d/Bigdata/hero3_fresh/check_v13_env.py
```

## 九、环境

- **OS**: WSL2 Ubuntu (noble)
- **编译目录**: `/home/administrator/vcmi-native/rel/bin/` (ext4)
- **运行目录**: `/home/administrator/vcmi-workspace/`
- **源文件**: `D:\Bigdata\hero3_fresh\vcmi\` (NTFS, 同步到 ext4)
- **游戏数据**: `/mnt/d/GAMES/Heroes3/`
- **原始二进制**: `/home/administrator/vcmi-gym/vcmi/build/bin/` (2025-04-08, 工作版)
- **Git**: `D:\Bigdata\hero3_fresh\vcmi` 子模块, commit `86b8c2c7a`
- **Python**: venv at `/home/administrator/vcmi-workspace/venv/`
- **GPU**: RTX 3060 6GB (训练用，与本问题无关)
