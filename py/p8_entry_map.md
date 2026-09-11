# P8 / T13 脚本入口地图（收敛版）

> 目的：避免 26+ 个 P8 脚本平铺导致维护漂移。核心原则 = **长期复用入口统一收进 `py/p8/`**，一次性诊断脚本与 dump 归档到 `py/p8_archive/`。

## 目录结构
```
py/
├─ p8/                       # 长期入口（14 个）
│  ├─ p8b_lobby_probe.py     # P8-B 阶段1 握手验证
│  ├─ p8be_host_start.py     # P8-B 阶段2 完整开局主入口（方案F）
│  ├─ p8b_capture_reference.py # 假服务器捕获法
│  ├─ p8b_handshake_full.py  # 握手全字段离线解码
│  ├─ p8b2_guest_join.py     # 方案B 备选（已被方案F取代）
│  ├─ p8c_movehero_probe.py  # MoveHero 在线探针（踩坑 #585）
│  ├─ p8c_movehero_offline_probe.py # MoveHero 离线回归
│  ├─ p8c_query_probe.py     # QueryReply 离线验证
│  ├─ p8c_query_probe_real.py# QueryReply 实机验证（P8-C 阶段5）
│  ├─ p8c2_town_chain_probe.py # 城镇决策链
│  ├─ p8c_capture_hero.py    # 171KB StartGame 捕获（知识库 #988）
│  ├─ p8c_state_parser.py    # 171KB blob 离线解析
│  ├─ p8d_scaffold_design.py # P8-D 跨机器部署主入口
│  └─ p8_probe_v5_onnx.py    # v5 ONNX 动作分布诊断
├─ p8_archive/               # 一次性诊断归档（12 个 py + 2 个 dmp）
├─ vcmi_protocol/            # 核心协议包（不动）
└─ p8_entry_map.md           # 本文件
```

## 维护规则（防漂移）
1. 新增 P8 脚本必须带功能前缀 `p8b_*` / `p8c_*` / `p8d_*`，放到 `py/p8/` 下。
2. "一次性取证"脚本直接写到 `py/p8_archive/`，不要放 `py/p8/`。
3. 被 docs/踩坑点引用的路径改动前，先同步 `docs/` 引用，避免断链。
4. 所有 `py/p8/*.py` 内的 `sys.path` 统一用 `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 定位到 `py/`，不要再硬编码绝对路径。
