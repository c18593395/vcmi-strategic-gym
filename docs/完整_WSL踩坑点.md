# HoMM3 战略 AI — 踩坑记录

---

## 一、编译与构建

### 1. 9p 文件系统不可用于编译
- cmake 在 /mnt/d/ (9p挂载) 超时。必须在 ext4 上编译。

### 2. cmake -S/-B 比 cd+cmake 可靠

### 3. ENABLE_LAUNCHER/EDITOR/LOBBY 必须 OFF

### 4. RPATH 陷阱
- libmlclient.so 的 RUNPATH 指向 ext4 构建目录，部署后 ld 从 ext4 加载 libvcmi.so

### 5. cmake 自动覆盖 data symlink
- 每次重建 mlclient 后 rel/bin/data 被重置

### 6. PCH 导致重编译巨慢，加 -D ENABLE_PCH=OFF

---

## 二、运行时问题

### 54. boost::filesystem::create_directories EEXIST
- 根因: data 是符号链接，boost 不认
- 修复: data 必须是真实目录，内部文件 ln -sf

### 55. JSON 配置文件空
- VCMI 在 data/config/ 下的 SETTINGS/settings.json 等为空
- 修复: 全部写入 {"general":{"playerName":"Agent"}}

### 56. libMMAI.so 缺少 AAI 构造器（N7 重构）
- 根因: N7-N10 后 AAI.h 有 82 override 声明但 AAI.cpp 只实现 yourTurn
- 修复: 在 namespace MMAI::AAI { 后补 ctor/dtor/getBattleAIName

### 57. 备份库仍 segfault（数据问题）
- 不是库版本问题，是运行时数据/配置问题
- 排查优先级: 数据目录 > JSON 配置 > Mods > 库版本

### 58. #46 segfault — 中立玩家战斗接口初始化崩（已重新定位）
- **最初误判**: 认为是 ServerPlugin 构造器问题
- **实际位置**: `installNewBattleInterface()` 为 neutral(中立)玩家初始化战斗回调时 segfault
- **VCMI 日志证据**:
  ```
  +++ constructor +++               ← AAI 构造 OK
  *** initGameInterface ***          ← 回调初始化 OK
  Initializing the interface for player tan
  Opening BattleAI / Loaded Battle AI
  Initializing the battle interface for player neutral  ← 崩在这里！
  ```
- **怀疑根因**:
  1. `libBattleAI.so` 的 `CBattleAI::initBattleInterface()` 接收无效参数
  2. `aiCombatOptions` 结构体有非法值
  3. `cbc` (battle callback) 为 null

### 59. 用 fprintf 日志定位崩溃
- 在 ServerPlugin.cpp 的每个 InitXxx 函数加 fprintf(stderr, "DBG xxx\n")
- 重建 mlserverplugin: `cmake --build rel --target mlserverplugin -- -j4`
- 运行测试，查看 stderr 输出
- 注意: VCMI 的 fprintf(stderr) 输出在 Python 下可见，但如果 VCMI 启动为子进程则输出可能被 pipe 捕获

---

## 三、调试笔记

### GDB 安装（apt 网络不可用时）
```bash
# 从 Windows 下载 deb
powershell.exe "curl.exe -sL <url> -o C:\tmp\gdb.deb"
# WSL 中提取
dpkg-deb -x /mnt/c/tmp/gdb.deb ~/gdb_extract
sudo cp ~/gdb_extract/usr/bin/gdb-multiarch /usr/local/bin/gdb
```

### faulthandler 捕获 SIGSEGV
```python
import faulthandler
faulthandler.enable()
```
