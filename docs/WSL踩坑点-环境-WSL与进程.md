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

