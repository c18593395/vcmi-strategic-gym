# WSL踩坑点 — 环境-WSL与进程

> 本文件是 `docs/WSL踩坑点.md` 拆分出的主题子文档。新增本主题踩坑点请归入此处；主文件仅作索引。

---

### 9. MSYS_NO_PATHCONV=1 必备

- **现象**: `$PWD/vcmi/rel/bin` 被 MSYS 转成 `C:/Program Files/Git/...`

- **解决**: 所有 wsl 命令前加 `MSYS_NO_PATHCONV=1`



### 10. LD_LIBRARY_PATH 含空格路径会截断

- **现象**: `export LD_LIBRARY_PATH=$PWD/vcmi/rel/bin:...` 因 MSYS 路径转换引入空格而截断

- **解决**: 用绝对路径，如 `/home/administrator/vcmi-workspace/vcmi/rel/bin`



### 11. 子进程环境继承

- **现象**: train_anchor.py 的 subprocess.run 继承的 LD_LIBRARY_PATH 可能不对

- **解决**: train_anchor 中显式设置 env 变量



---



### 21. PWD 在不同 shell 上下文中的差异

- **现象**: `bash -c` 中 `$PWD` 可能是 Windows 路径

- **解决**: 所有关键路径用绝对路径，不依赖 $PWD



### 22. python3 -c 中的引号嵌套

- **现象**: `python3 -c "print(f'{x}')"` 在 bash -c 中引号冲突

- **解决**: 复杂 Python 写文件再用 `python3 file.py`，或用 heredoc `<< 'PYEOF'`



### 23. 多个 train 进程并存

- **现象**: pgrep -f train 匹配到自身 grep 和旧残留

- **解决**: `for p in $(pgrep -f "python.*train"); do kill -9 $p; done`



### 25. GitHub 直连超时

- **现象**: git clone https://github.com/... 超时

- **原因**: 网络不通

- **解决**: 本地已有副本 D:\Bigdata\hero3\vcmi-gym\



### 26. opencode 连不上服务器

- **现象**: opencode run 报 "Unexpected server error"

- **原因**: 网络问题或 API key 未配置

- **解决**: 用本地的 deepseek-v4-pro/flash 子 Agent



---



### 27. deepseek-v4-flash 有 45 次工具调用上限

- **现象**: 子 Agent 分析到一半戛然而止

- **解决**: 大任务用 deepseek-v4-pro (同样 45 次但能力更强)，或拆成多个小任务



### 28. 子 Agent 用 patch 写文件频繁失败

- **现象**: NTFS 路径 `C:\d\Bigdata\...` 拼写错误，patch 失败

- **解决**: 让子 Agent 用 write_file 而不是 patch



### 29. 子 Agent 杀死后台进程

- **现象**: pkill -f train 副作用杀了父进程的 bash

- **解决**: `for p in $(pgrep -f "python.*train"); do kill -9 $p; done`



### 30. 子 Agent 改 symlink 后不通知

- **现象**: 子 Agent 改了 vcmi symlink 导致训练失败，父 Agent 不知道

- **解决**: 审计 Agent 检查 symlink 完整性



### 31. WSL terminate 丢失未写入文件的更改

- **现象**: `wsl --terminate Ubuntu` 后，WSL 内文件未写入的更改丢失

- **解决**: 修改 WSL 内文件后立即 flush/写入，不要在 Python heredoc 中留待后续处理



### 8. WSL 内存崩溃 (E_UNEXPECTED)

- **现象**: 训练/diag 跑一段时间后 `wsl bash` 全部返回 `Wsl/Service/E_UNEXPECTED` 乱码 — WSL 服务崩溃

- **根因**: 主机 16GB 内存仅剩 3.9GB 空闲 → WSL2 默认 50% 配额吃满 → VCMI+Python 重负载 OOM → WSL 整体崩

- **修复**: `C:\Users\Administrator\.wslconfig` 限制 `memory=6GB swap=4GB processors=8`

- **教训**: 训练机内存紧张, 监控 free -h; 训练进程死亡先查 WSL 是否崩溃 (watchdog 检测进程消失 + WSL 探测)



### 27. pkill/pgrep -f 匹配到自己 — bash -c 命令行含模式字符串自杀 (2026-08-16)



- 现象: `pkill -9 -f train_wsl2_ppo` 在 bash -c 包装里执行 → exit 9, 后续命令全没跑; pgrep -f 采样到 bash 包装进程 (rss=3MB) 而非目标 python

- 根因: bash -c "pkill -f XXX ..." 的命令行本身含 XXX → pkill -f 匹配到自己的 bash → SIGKILL

- 修复: 用精确 PID (ps aux | grep | awk 取列) 或 pgrep -f '^/绝对路径' (锚定开头, 排除 bash -c 包装)

- 教训: WSL 里 pkill -f 高危, 先 pgrep 看 PID 再 kill; 采样脚本的 pgrep 模式必须锚定可执行文件绝对路径



### 28. WSL /tmp 频繁清空 — 观测日志/轨迹丢失 (2026-08-16)



- 现象: /tmp/nk2_mem_watch.log /tmp/router_fix.log /tmp/traj_ep.json 多次消失 (复现实验日志还没分析就没了)

- 根因: WSL2 /tmp 是 tmpfs, 系统内存压力/重启时自动清理 (多次出现)

- 修复: 实验日志写项目目录 (bc_data/ 或 logs/), 不用 /tmp; 轨迹文件同样

- 教训: 长观测/实验数据必须落盘项目目录, /tmp 只放一次性临时文件



## 踩坑 #71: WSL 与 git-bash 环境坑 (2026-08-19 记忆迁移)

- `wsl bash -c '...'` 里 `$VAR` 会被展开 — 要防展开用 heredoc `<< 'ENDSCRIPT'`

- Windows subprocess 可能命中 System32\bash.exe = WSL bash (/mnt/d 有 pgrep); Hermes terminal 是 git-bash (/d/ 无 pgrep)

- git-bash /d/ 对 hero3_fresh 目录显示空 (映射坑) — 读项目文件用 python/read_file，别用 git-bash ls

- python 写 CRLF 文件: open(p,'w') 默认 newline=None 会把 \n 翻译成 \r\n — 对已含 \r\n 的文本逐行写会变成 \r\r\n 损坏 (splitlines 后每逻辑行间多出假空行, 全文件 diff 假象 477+/472-)。写回必须 open(p,'wb') 或 open(p,'w',newline='') + 显式 '\r\n'.join

- bash 双层转义: python -c 字符串里的 \\n 经 bash 后易写成真 0x0A → MSVC C2001 "常量中有换行符" (fprintf 字符串被截断)。改文件用 write_file 写修复脚本运行, 绕过 bash 转义; 或字节级 b"...\x0a..." 替换



## 踩坑 #75: python 补丁脚本残留中文注释拼接 — U+2014 SyntaxError (2026-08-19)

- 现象: patch 脚本替换后 SyntaxError: invalid character '—' (U+2014)

- 根因: 用 replace 拼接代码行时, 上一版修复 (fix_endturn) 的注释后半段 (— 模型开局帧倾向连发动作 8) 被残留拼接到新行尾 (move_stall_prev = 10**9 — ...)

- 修复: 定位行内容看实际文本 (python 读行 print repr) 再精确替换; 别猜

- 教训: 字符串替换式补丁脚本必须保留旧注释的完整性 (整行替换而非片段拼接); 出 SyntaxError 先看行 repr 找非 ASCII 残留



### 101. hermes voice 禁用了还自动触发 wake word = 旧进程未重启 (2026-08-25)

- 现象: config.yaml 已 stt.enabled=false + wake_word.enabled=false, 仍出现 "✦ Wake word detected — listening..."

- 根因: hermes 进程 10:41 启动 (早于 15:23 配置修改), wake word 监听按启动时内存配置运行, 配置文件改了没用

- 解决: 退出 hermes 重启, 新会话读新配置; 验证方法 = 进程 CreationDate 必须晚于 config.yaml mtime

- 附带: hermes tools disable tts 同样重启才生效 (工具集变更下次会话加载)

### 114. WSL2 idle shutdown 杀训练进程 (2026-08-28, v4 段 12:17 停转; 08-29 补充实证)
- 现象: train_loop.log 8.5h 无新增, WSL 侧训练进程消失, 无优雅退出打印/无异常日志 (v4 死于 08-28 12:17, hermes-agent 会话切换关闭了最后一个 Windows 客户端会话)
- 根因: 所有 Windows 侧 WSL 客户端会话全关 → WSL2 VM 自动 shutdown → 广播 SIGTERM; setsid/nohup 只脱离终端, 挡不住 VM 级 shutdown
- 处理: ① `systemd-run --user --collect --unit=homm3-train-v5 --working-directory=/mnt/d/Bigdata/hero3_fresh /bin/bash -c 'exec venv/bin/python train_wsl2_ppo_v2.py >> train_loop.log 2>&1'` 托管训练; ② Windows 侧 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList 'sleep infinity'` 防 VM idle shutdown; ③ 停止用 `systemctl --user stop homm3-train-v5` (优雅保存 state)
- 验证: 重启后日志出现 "Loaded train state (step=...)" 即断点续训成功
- 教训: 长期训练必须 systemd-run 托管 + Windows keepalive 双保险; WSL 会话全关 = VM 死刑, nohup 救不了
- **08-29 补充实证 (关机重启后必踩)**: 重启电脑后 keepalive 不会自启 → 每次执行完 wsl 命令 60~90 秒 VM 即 idle shutdown → 训练反复被 SIGTERM 优雅停止 (journal 表现为无 stop 命令来源的 "Stopping/Stopped" 循环, systemd PID 随 Boot 变化 [339]→[323]→[325])。**开机后第一件事 = 先挂 keepalive 再启动训练**; 快速判定: `wsl --list --running` 显示"没有正在运行的分发" 即 keepalive 丢失; journal 出现无命令来源的 Stopping + systemd PID 变化 = VM idle shutdown 而非人为 stop

### 120. PowerShell 传 wsl bash -c 复杂命令的引号/$ 展开坑 (2026-08-29 多次)
- 现象: `wsl bash -c '... $(ls -t ...) ...'` 里命令替换被吞/报 "syntax error near unexpected token"; awk '{print $11}' 的 $11 变空; 嵌套双引号 python -c 转义错乱
- 根因: PowerShell 对传入参数做 $ 变量展开与引号重排, 复杂 bash 语法 (命令替换/awk 位置参数/嵌套引号) 高概率损坏
- 解决: 复杂逻辑一律写成 py/ 下脚本文件再 `wsl bash -c 'python3 script.py'` (本次 check_t04_guards/check_target_list/check_next_dir 等均此模式); 简单命令也避免 $() 与 awk
- 教训: 跨 shell 边界 (PS→bash) 的命令复杂度上限极低, 第 2 次转义失败就该换脚本文件, 不要第 3 次尝试

### 130. PowerShell 双引号内 $(...) / $var 子表达式展开: wsl 复杂命令被撕裂 (2026-09-02, 09-07 补 $var 近亲)
- **现象**: `wsl bash -c "... $(ls -t ...) ..."` 中 `$(...)` 被 PowerShell 当子表达式先行执行 (报 head 不存在/空变量), bash 收到残缺命令; heredoc 正文同样被撕 (本次归档操作亲自复现); **$var 变量同理** — `wsl bash -c "L=$(grep -n ...); tail -n +$L f"` 中 `$L` 被 PowerShell 展开为空 → bash 收到 `tail -n + f` 报 invalid number (09-07 复现, 即使 `\$` 转义在跨 PowerShell→wsl 两层解析下仍不可靠)
- **正确姿势**: 复杂命令/长文本写入文件 (Write 工具 → py/_tmp_xxx.sh) 再 `wsl bash -c "bash 文件"`, 用完即删; 单条简单命令才直接 wsl bash -c
- 近亲: #154 (09-10 同坑固化 — 规范升级为复杂 bash 逻辑一律 py/ 脚本文件)
- 状态: 🔴 操作坑, 规范先行

### 131. 编译 -j8 与训练并发压死 WSL: 0x8007274c 连接失败 (2026-09-02)
- **现象**: cmake --build -j8 (MMAI 大编译单元) 与 v5 训练 (PPO+VCMI episode) 并发 → WSL 服务整体无响应 (`wsl -e echo` 超时 Wsl/Service/0x8007274c, ps/systemctl 全挂)
- **恢复**: 仅 `wsl --shutdown` 可解 (训练丢未保存进度); 恢复后必须重建 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList 'sleep infinity'` (随 VM 死亡, 踩坑 #114)
- **正确姿势**: 重编 .so 前 `systemctl --user stop homm3-train-v5` 编完再启; 或 -j4 上限; 产物验证 ls -la 大小 + strings 特征串
- 状态: 🔴 已踩, 规范先行

### 135. Python 补丁脚本三连坑: % 格式化冲突 / 锚点缩进失配 / while pos 不前进死循环 (2026-09-02)
- **现象 1**: 补丁串内嵌 printf 的 %d 被 python `% k` 格式化消费 → TypeError; **现象 2**: 源码锚点含行尾空白/Tab 缩进 → 精确字符串 count=0; **现象 3**: `while: pos=find(...)` 后 pos 停在行首不越过插入点 → 死循环吞内存 (叠加编译压死 WSL, 见 #131)
- **正确姿势**: % 用占位符 @@ + .replace; 锚点前先 sed -n 'X,Yp' | cat -A 看实际字节; 行级插入用 split('\n') 遍历; 补丁前必备份 (cp .bak_标签_时间戳)
- 状态: 🔴 操作坑, 规范先行

### 136. C++ 诊断代码远程生成三连坑: 引号拼接 / 尾杂引号 / 作用域外引用 (2026-09-02)
- **现象 1**: Python 补丁模板双引号拼接 bug 产生 `fprintf(dg, ""[RL-DIAG7]` → 编译错 stray '\'; **现象 2**: 模板参数尾部多杂引号 `? 1 : 0");` → missing terminating " character; **现象 3**: w3 诊断放在 i3 循环外但引用循环变量 i3 → 'i3' was not declared in this scope
- **修复实录**: `sed -i 's/fprintf(dg, ""\[RL-DIAG7\]/fprintf(dg, "[RL-DIAG7]/g'` 修现象 1; `sed 's/? 1 : 0"); fclose/? 1 : 0); fclose/g'` 修现象 2; 去掉 i3 引用改打 pos 修现象 3
- **正确姿势**: 生成后必 `grep -F '[RL-DIAG7]' 目标 | cat -A` 自检引号/尾字符; sed 替换式内 `\[` 易被消费致 grep Invalid range end → 用 grep -F 固定串验证; 诊断引用变量必须在同作用域; 每补一处立即增量编译 (-j4) 通过再下一处
- **关联**: #135 补丁脚本三坑姊妹篇 (彼时是脚本机制坑, 本次是生成代码内容坑)
- 状态: 🔴 操作坑, 规范先行

### 138. SearchReplace 模糊匹配残片: old_str 微差致插入错位 (2026-09-03)
- **现象**: 向 md 文档插入条目时 old_str 与原文有细微差异 (标点/空格), 工具不报错而是模糊对齐, 在目标位置产生 `④ **P1d- **P1d-v2` 类残片 (新内容嵌进旧行中段)
- **正确姿势**: 插入后必 grep 关键词复核落位与上下文; 发现残片: Grep 定位 → 精确读取上下文 → 二次 SearchReplace 修复; old_str 从 Read 输出逐字复制, 勿凭记忆重打
- 状态: 🔴 操作坑, 规范先行

### 139. /mnt/d venv 已不存在: systemd-run 相对路径启动失败 (2026-09-03)
- **现象**: v5 历史启动命令 `--working-directory=/mnt/d/Bigdata/hero3_fresh + venv/bin/python` 重启时报 `No such file or directory` — /mnt/d/Bigdata/hero3_fresh/venv 目录已消失; 实际训练 venv 在 `/home/administrator/vcmi-workspace/venv` (Phase A 验证 vcmi_gym 解析路径时已实锤)
- **危害**: systemd-run 返回 "Running as unit" 但进程秒死 (is-active=inactive), 训练假启动; unit 随 --collect 自动消失 (status 报 could not be found), 不好查
- **正确姿势**: 启动命令一律用绝对路径 `exec /home/administrator/vcmi-workspace/venv/bin/python`; 重启后必验 `is-active` + tail 主日志确认 resume 行, 不能只看 systemd-run 返回值
- 状态: 🔴 操作坑, 已纠正 (绝对路径重启成功)

### 141. WSL 断网 + Windows 有网: 双机协作下载方案 (2026-09-03)
- **现象**: R6 修复需下载 onnxruntime, WSL 侧 GitHub/镜像/pypi/gitee 全部 unreachable (连 baidu 都不通), 但 Windows 侧 curl 正常 (200 OK); WSL 无代理端口 (7890/10809/1080 全无监听, 系统代理 ProxyEnable=0)
- **危害**: WSL 内直接 curl/pip download 全失败, 白烧多轮重试
- **正确姿势**: **Windows 侧 curl.exe 下载 → 落 /mnt/d → WSL 解压安装** (`curl.exe -o D:\...\_tmp_ort.tgz <url>` → `wsl -u root tar xzf /mnt/d/... -C /opt/onnxruntime --strip-components=1`); 头文件跨平台通用 (win-x64 包 include 可直接给 linux 编译用, 但库必须 linux 版); 用完删临时文件
- **关联**: 下次 WSL 断网先 `curl.exe` 测 Windows 侧, 通则走 /mnt/d 桥, 勿在 WSL 内重试网络
- 状态: 🔴 环境坑, 方案已验证

### 149. 多进程齐崩 = 系统资源耗尽特征, 勿误判应用代码 (2026-09-09)
- **现象**: GUI 复测弹窗崩溃, 直觉归因 VCMI 代码 — 实锤为系统级: 07:14:46 Windows 资源耗尽诊断 (事件 2004, **3 个 python.exe 共吃 36GB commit**, 各 11.5-12.5GB) → 07:18:52-07:19:01 pwsh/GDEPService/agent-tool-host/**dwm.exe** (dwmcore.dll 0xc00001ad) 四进程连锁崩 + LiveKernelEvent 141
- **关键排除证据**: VCMI_client.exe **无** WER APPCRASH 事件、无新 rpt/dmp → 代码层无新崩溃; 复测撞上资源耗尽窗口 (commit 打满 → 分配失败 → 卡死/弹窗)
- **排查命令沉淀**: `Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000,1001}` (APPCRASH 详情) + `System` 日志 ProviderName='Microsoft-Windows-Resource-Exhaustion-Detector' Id=2004 (虚拟内存不足, 直接列出元凶进程与占用字节数) + `Get-CimInstance Win32_OperatingSystem` 算 CommitUsed/Limit
- **教训**: ①"弹窗崩溃"先查 WER 事件日志再怀疑代码 — 单进程崩看 Application 1000, **多进程齐崩 = 资源耗尽指纹** ②dwm.exe 崩会伪装成"游戏卡死/崩" (画面冻结) ③Resource-Exhaustion 2004 直接给元凶 PID 与字节数, 一查一个准
- 状态: ✅ 定性完毕 (VCMI 无责); 3×python 来源待用户确认 (进程已退无法回查)

### 150. Windows minidump 抓取与解析三坑 (2026-09-09)
- **坑 1**: rundll32 调 MiniDumpWriteDump 失败 (文件不存在/权限) → 改 `py/take_dump.py` ctypes 直调 API (`MiniDumpWithFullMemory|HandleData|FullMemoryInfo`)
- **坑 2**: python minidump 库对 full dump 支持差 — `baseaddr` 属性名错 (实为 `baseaddress`)、LOCATION_DESCRIPTOR 无 len()、Memory64List 栈内存读不到 → `py/walk_stuck_dump.py` 手动解析 stream directory + Memory64ListStream (type=9, n_ranges/base_rva/data_rva 三段式)
- **坑 3**: 无符号栈只见 RVA — `py/identify_all_threads.py` 用 .pdata 段函数边界 (bisect) + 导出表把线程栈 RVA 归属到函数; `stuck4_cfbb.py` 定位疑似线程 start_routine; `stuck4_heap.py` 查 GAME/mutex 周边堆完整性
- **教训**: ①工具链固化在 py/ 下五件套, 下次 GUI 死锁直接复用 ②minidump 库不可信时手解二进制格式反而快 (格式文档充分) ③抓 dump 时机 = 冻结现场时 (MiniDumpWriteDump 可对活进程抓)
- 状态: ✅ 工具链可用, 死锁 owner 定位全靠它

### 151. Windows GUI 中文界面 + 第三方输入法: 两条独立崩溃路径 (2026-09-09)
- **现象 A**: 中文界面下选图 → "Disaster happened. Attempt to read from 0x0" — **界面语言编码转换崩溃**, 与地图/逻辑无关
- **现象 B**: 第三方输入法 DLL 注入游戏进程 → 堆损坏 (随机时点崩), 与 "忘记切输入法" 复测记录吻合
- **规避**: VCMI 界面语言切 English + 系统输入法切英文 (ENG) 再复测; 两坑均无需改代码
- **教训**: ①中文 Windows 环境跑开源 GUI, 语言/输入法是独立于代码的崩溃源, 复测前先固定这两变量 ②崩溃现象随环境变量消失 = 环境因, 随代码版本复现 = 代码因
- 状态: ✅ 切英文后选图通过 (后续卡死另案, 见 #149)

### 154. PowerShell 包裹 wsl bash -c 时 $var/$( ) 被 PowerShell 层吃掉 (2026-09-10)
- **现象**: `wsl bash -c 'for f in ...; do ... $f ...; done'` 循环变量全空 / `$(cmd)` 被当 PowerShell 子表达式报 "Variable reference is not valid"
- **根因**: PowerShell 先解析外层字符串, `$f`/`$A`/`$(...)` 在到达 bash 前已被展开为空; 单引号包裹也不可靠 (多层嵌套)
- **规避**: ①复杂 bash 逻辑一律写成脚本文件 (py/ 下, 参照 audit_r5_trees.sh/stat_t06_guard_battle.sh) 再 `wsl bash 脚本路径` 执行 ②简单单命令才用 wsl bash -c 内联 ③确认: 无变量替换需求的 heredoc python 内嵌代码可直接用
- 关联: #130 (09-02 首踩, 本条为其 09-10 固化版)
- 状态: ✅ 固化 (本次新增 4 个 py/ 脚本均此模式)

### 155. pkill -f 同名串自杀: 当前 shell cmdline 含目标名即被自己杀 (2026-09-10)
- **现象**: `wsl bash -c 'pkill -f diag_obj_dump; ... python py/diag_obj_dump.py ...'` 整条命令 exit 15 (SIGTERM), 输出文件都没创建
- **根因**: pkill -f 匹配**全部进程 cmdline** — 同一条 bash 命令行里含 "diag_obj_dump.py" 字面量 (python 调用部分), bash 自身 cmdline 命中模式被杀; `[d]` 字符类技巧只防住 pkill 参数本身, 防不了同行其它部分的字面量
- **规避**: ①pkill 单独一次工具调用 (与目标操作分开) ②或精确 pgrep 取 PID 再 kill ③或模式用字符类且确保整条命令无其他字面量命中
- 关联: #27 (pkill/pgrep -f 自杀首踩, 已归档于子文档 环境-WSL与进程)
- 状态: ✅ 固化

### 168. transient unit 停止即消失: systemctl start 报 Unit not found (2026-09-06)
- **现象**: `systemctl --user stop homm3-train-v5` 后想 `start` 恢复 → `Unit homm3-train-v5.service not found`
- **真因**: v5 是 systemd-run 创建的 **transient unit**, `--collect` 使停止后 unit 定义被自动收集清除 — stop/start 模式只适用常驻 unit 文件
- **正确姿势**: 每次重启必须 systemd-run 重建 (命令固化 `py/restart_train_v5.sh`; **venv 必须绝对路径** /home/administrator/vcmi-workspace/venv/bin/python — hero3_fresh/ 下无 venv, 旧记录 `exec venv/bin/python` 相对写法在当前目录结构下必挂)
- 关联: 踩坑 #114 (keepalive) 的姊妹坑 — 两坑叠加 = 夜里中断后早上既 start 不了还得重建
- **补充 (09-08 二次复现)**: stop 后 `systemctl --user is-active homm3-train-v5` 对**已消失的 unit 照样输出 `inactive` (exit 4)**, 不报 not found — is-active 结果不能作为 unit 存在性判据; 且 `stop` 一个已消失 unit 也可能静默成功, 停机确认要看 journalctl (`Stopped homm3-train-v5.service` + train_loop.log 出现 `Saved STATE_PATH`) 而非 is-active; 重启一律 `py/restart_train_v5.sh` 勿走 systemctl start
- 状态: ✅ 已固化脚本

### 169. 隔夜中断形态与恢复序: keepalive 丢失 → 非优雅关机 → checkpoint 回滚 (2026-09-07)
- **现象**: 夜里训练中断, 早上 resume 点 (546379) 落后最后日志进度 (547071) ~700 步 (≈10 局样本未入档)
- **机理链**: Windows 侧 keepalive 会话丢失 (关机/会话清理) → VM idle shutdown 广播 SIGTERM **不走 systemctl stop 优雅保存路径** → 模型状态停在最后一次自动存档
- **恢复序 (开机后)**: ①先补挂 keepalive `Start-Process -WindowStyle Hidden wsl.exe -ArgumentList 'sleep infinity'` (见 #114) ②再 `py/restart_train_v5.sh` (transient unit 需重建, 见 #168) ③grep 'Loaded train state' 确认 resume 点
- **损失评估**: 回滚量 = 中断前日志 step - 存档 step, 小则几局大则一夜; 存档一致性无损
- 状态: ✅ 已恢复 + keepalive 已补挂 (09-07 晨)

