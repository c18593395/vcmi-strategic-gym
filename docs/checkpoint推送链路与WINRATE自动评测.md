# Checkpoint 推送链路 + WIN RATE 自动评测

> 目标：打通 `WSL 训练存档 → scp 到服务器 → /models/load → 触发评测 → 结果回传`，
> 让**每一轮训练自动产出新模型 WIN RATE**，并集中存放在服务器一处可查。

---

## 一、架构（为什么 WIN RATE 在 WSL2 算，不在服务器）

```
┌─────────────────────────────────────────────────────────────────┐
│  WSL2 (x86, RTX3060)  —— 训练主力 + 评测农场(新模型)            │
│                                                                 │
│   train_wsl2_ppo_v2.py  (24/7 后台跑)                            │
│        │  每 50 step 存 checkpoints/wsl2_ckpt_<step>.pt          │
│        ▼                                                        │
│   ckpt_watcher.sh (cron 每 15min 触发)                          │
│        ▼  ckpt_push_hook.py                                      │
│   ① export_rl_onnx.py  → /tmp/<name>.onnx  (3464+terrain, 2输入) │
│   ② scp → 172.16.2.40:/DATA/hero3/models_incoming/<name>.onnx   │
│   ③ POST :8080/models/load + activate   (模型注册/部署侧)        │
│   ④ winrate_eval.py   (本地 WSL2 跑, 因为服务器跑不了新模型)     │
│   ⑤ 结果 POST :8088/results + scp 落盘 /DATA/hero3/output/       │
└─────────────────────────────────────────────────────────────────┘
        │                                   ▲
        │  scp / POST                        │ 结果回传
        ▼                                   │
┌─────────────────────────────────────────────────────────────────┐
│  172.16.2.40 (ARM64, 64核, 无 GPU) —— 模型仓库 + 推理 + 结果中枢 │
│   :8080 vcmi-inference   (SB3/ONNX 加载/推理, 旧架构 256 维)     │
│   :8088 vcmi-results     (WIN RATE 历史中枢, 新增)              │
│   /DATA/hero3/models_incoming/   (WSL 推送来的新模型 ONNX)       │
│   /DATA/hero3/output/winrate_*.json + winrate_history.jsonl      │
└─────────────────────────────────────────────────────────────────┘
```

**关键事实（已实测）：** 服务器 `/DATA/hero3/vcmi-build/bin/*.so` 是 **ARM64 编译的旧 v13 架构**
（obs 256 维 / 11 动作），且 ARM64 headless VCMI 因首回合不触发被放弃（知识库 §3.2）。
新模型是 **3464 维 + 4×21×21 地形 CNN + 25 动作** 的自定义 `Net`，**服务器无法运行其评测环境**。
因此 WIN RATE 评测只能在 WSL2（唯一带新架构 x86 引擎的机器）跑，结果回传服务器集中存放。

> 说明：`:8080` 的 `/models/load` 仍会把新 ONNX 注册进推理服务（供真实游戏 DLL 部署侧用），
> 但其 `predict` 目前只支持单输入 256 维旧模型——新 2 输入 ONNX 能被 load 但不能被该服务的 predict 调用，
> 属部署侧独立问题，不在本链路范围内。

---

## 二、新增/改动文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `results_hub.py` | 服务器 `/DATA/hero3/results_hub.py` + systemd `vcmi-results` | WIN RATE 历史中枢 (:8088) |
| `vcmi-results.service` | `scripts/` + 服务器 `/etc/systemd/system/` | results_hub 自启单元 |
| `winrate_eval.py` | `py/winrate_eval.py`（WSL2 跑） | 新模型 WIN RATE 评测（复用 `StrategicEnv` + `Net`） |
| `ckpt_push_hook.py` | `py/`（WSL2 跑） | 链路编排：导出→推送→评测→回传 |
| `ckpt_watcher.sh` | `py/`（WSL2 crontab） | 解耦触发器：发现新 checkpoint 就调用 hook |
| `export_rl_onnx.py` | `scripts/`（已有，复用） | `.pt → ONNX` 导出 |

---

## 三、使用方式

### 方式 A：cron 触发器（推荐，不改动正在跑的训练）
在 **WSL2** 内：
```bash
crontab -e
# 加一行（每 15 分钟检查一次新 checkpoint）:
*/15 * * * * /mnt/d/Bigdata/hero3_fresh/py/ckpt_watcher.sh >> /mnt/d/Bigdata/hero3_fresh/push_watcher.log 2>&1
```
watcher 用 `.last_ckpt_pushed` 标记去重，每个新 `wsl2_ckpt_<step>.pt` 只推送一次。

### 方式 B：训练脚本尾部 hook（每存一次 ckpt 立即触发）
在 `train_wsl2_ppo_v2.py` 的 checkpoint 保存块（`if total_steps - last_ckpt_step >= 50:` 内，约 660–684 行之后）追加：
```python
# === 自动推送链路 (checkpoint → 服务器 → WIN RATE 回传) ===
try:
    subprocess.Popen(
        ["/home/administrator/vcmi-workspace/venv/bin/python",
         "/mnt/d/Bigdata/hero3_fresh/py/ckpt_push_hook.py",
         "--ckpt", ckpt_path],
        stdout=open(f"/mnt/d/Bigdata/hero3_fresh/push_{resume_step}.log", "w"),
        stderr=subprocess.STDOUT)
except Exception as _e:
    print(f"  [WARN] push hook 启动失败: {_e}", flush=True)
```
用 `Popen`（后台）不阻塞训练。

### 手动跑一次（验证用，先小样本）
```bash
# 在 WSL2 内
/home/administrator/vcmi-workspace/venv/bin/python /mnt/d/Bigdata/hero3_fresh/py/ckpt_push_hook.py \
    --ckpt /mnt/d/Bigdata/hero3_fresh/checkpoints/wsl2_ckpt_<最新step>.pt \
    --games 4 --maps T05_adventure_36X36_01.vmap,T06_adventure_72X72_01_duel.vmap
```

---

## 四、查看每轮新模型 WIN RATE

```bash
# 服务器一处查看（局域网可达）
curl http://172.16.2.40:8088/results/latest          # 最新一条
curl http://172.16.2.40:8088/results                  # 最近 50 条
curl http://172.16.2.40:8088/results/wsl2_ckpt_123450 # 某模型历史
curl http://172.16.2.40:8088/models                   # 各模型最新 WIN RATE 聚合
```
落盘文件：`/DATA/hero3/output/winrate_history.jsonl`（每行一条）+ `winrate_<name>.json`。

---

## 五、调参

`ckpt_push_hook.py` / `winrate_eval.py` 接受的参数：
- `--maps`：逗号分隔的地图 basename（位于 `maps/training/`）。默认 3 张代表图。
- `--games`：每图局数（默认 8）。生产可上调到 16–32 提高统计置信度。
- `--blue`：蓝方 baseline（默认 `MMAI_RANDOM`；也可 `StupidAI`）。
- `--max_turns`：每局最大回合（默认 250，与训练一致）。
- `--no-eval`：只推送模型不评测；`--no-push`：只本地评测不碰服务器。

---

## 六、注意事项 / 故障排查

1. **与 24/7 训练争用 VCMI**：winrate_eval 与训练都启动 VCMI 子进程。若同时跑多个 VCMI 实例出现端口/资源冲突，
   评测局会报错并计入 `errors`（不影响训练）。建议：watcher 放在训练低峰期；或临时暂停训练再评测。
2. **WSL→服务器免密**：hook 用 `ssh/scp` 从 WSL 推文件，需 WSL 侧已配置到 `172.16.2.40` 的免密（与 Windows 侧同理）。
3. **`/models/load` 400**：同名模型已注册时返回 400，属正常（hook 已忽略）；如需覆盖，先在服务器 `restart vcmi-inference` 清注册。
4. **评测结果 game_over=0**：达到 `max_turns` 未分胜负记 DRAW，计入分母但不算胜；提高 `max_turns` 或 `--games` 可改善区分度。
5. **results_hub 自启**：`systemctl status vcmi-results`；改代码后 `systemctl restart vcmi-results`。

---

## 七、已验证

**服务器侧（本环境已实测）：**
- [x] 服务器 `:8088` results_hub 部署 + systemd 自启 + 增删查接口测试通过
- [x] `/DATA/hero3/models_incoming/` 目录已建
- [x] WSL→服务器 SSH 免密可用（BatchMode 测试通过）
- [x] 服务器 `:8080` 推理服务在线（curl `/health` 返回 80 模型）

**WSL 侧脚本（本环境语法/接口校验，因 sandbox 禁用 `wsl.exe` 无法实跑）：**
- [x] `winrate_eval.py` — `python -m py_compile` 通过
- [x] `ckpt_push_hook.py` — 修复一处 `global` 声明顺序 bug（原在 `SERVER` 已被 `default=SERVER` 引用之后才声明，导致 `SyntaxError: name 'SERVER' is used prior to global declaration`），已将 `global` 上移至 `main()` 顶部并移除非必要项；复检编译通过；`import urllib.error` 显式化
- [x] `ckpt_watcher.sh` — `bash -n` 通过
- [x] **跨文件接口一致性核对**：
  - hook 调 `export_rl_onnx.py <ckpt> <onnx>` ↔ 该脚本 `sys.argv[1], sys.argv[2]` 位置参数 ✓
  - hook 调 `winrate_eval.py --model/--maps/--games/--blue/--max_turns/--out` ↔ 该脚本 `add_argument` 同名 ✓
  - hook 读 `win_rate/wins/losses/draws/errors` ↔ `winrate_eval.py` 输出 JSON 同名键 ✓

**待用户侧执行：**
- [ ] 全链路端到端实跑（需在 WSL2 内执行，本机 sandbox 禁用了 `wsl.exe`，未在此环境跑通；按第三节手动验证一次，建议先 `--games 4` 小样本）
