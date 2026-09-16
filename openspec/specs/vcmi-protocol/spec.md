# VCMI 网络协议（外挂 AI 客户端契约）

## Purpose

T13 外挂 AI 客户端与 VCMI server 之间的二进制网络协议契约。
真相源：逆向 `lib/serializer/`、`lib/network/`、`lib/networkPacks/`（VCMI 1.7.5 + smanolloff fork）。
详细字节级文档：`docs/序列化协议规格.md`（605 行，本 spec 为其行为契约摘要 + 指针）。
用途：约束 py/vcmi_protocol 外挂协议栈与 server 的兼容性，任何协议实现变更须先改本 spec。

## Requirements

### Requirement: TCP 帧格式
所有网络通信 SHALL 使用 4 字节 little-endian uint32 长度头 + N 字节 CPack payload 的帧格式。
- Header=0 表示心跳空包（每 10 秒保活）
- 最大包 64MB（messageMaxSize）
- TCP no_delay=true

#### Scenario: 外挂客户端发送 EndTurn
- **WHEN** 外挂客户端向 server 发送 EndTurn 包
- **THEN** 帧为 `4B len + 6B payload`，payload 符合 EndTurn 布局（见序列化规格 §5.1）

### Requirement: 二进制序列化规则
所有 CPack 字段 SHALL 按 VCMI BinarySerializer 规则编码：
- int32/uint32/Enum → LVarInt 变长整数（7bit 分段 0x7f 续位 + 0x40 负号位，末字节 & 0x3f）
- 容器 vector/set/map → uint32 长度前缀 + 元素
- string → 全局去重表（跨包 ref 共享）
- 指针 → isNull + pid + tid + 数据
- CPackForServer 头 = isNull + pid + tid + player + requestID

#### Scenario: BuildingID 编码
- **WHEN** 序列化 BuildingID（如 RecruitCreatures/Build 包内）
- **THEN** 编码为 LVarInt（非 string jsonKey）

#### Scenario: CreatureID / HeroTypeID 编码
- **WHEN** 序列化 CreatureID 或 HeroTypeID
- **THEN** 编码为 string jsonKey；跨包去重 ref 意味着外挂端不可从单包还原，须依赖 SRV-DIAG 诊断行（SetAvailableCreatures(100) 广播 / TOWNAVAIL diag）

### Requirement: 核心包字节布局
关键出站包 SHALL 符合以下布局（字节级细节见 docs/序列化协议规格.md §5）：
- EndTurn (180) = 6B
- MoveHero (182) = 22B（4 点路径）
- QueryReply (197) = 8B(absent)/9B(present)，布局 = isNull + pid + tid + player + req + qid + [0x00] / [0x01 + reply LVarInt]
  （09-16 P8-C 收尾实机验证: 8B absent 帧 server 无 197 fishy = 受理; C++ 端 save(optional) absent 走 uint32(0) 4B 路径,
  与 Python 8B absent 的 1B 0x00 存在潜在不匹配, 9B present 为回退候选, 回退判据 = 197 fishy）
- RecruitCreatures (187) = 23B
- TryMoveHero (109) 回包字段序 = id + result + start + end + movePoints + fow + attackedFrom

#### Scenario: 玩家回合门控
- **WHEN** 收到 PlayerStartsTurn(88) 包
- **THEN** 包体 = queryID + playerColor 字段序（非 player+time_limit）；外挂仅在 MY_COLOR 回合发 EndTurn，否则 server 拒绝（"not allowed/fishy"）

#### Scenario: QueryReply 实战闭环
- **WHEN** 外挂客户端收到 server query（如招募确认）并回送 QueryReply(197)，queryID/player/result 与 DIAG 诊断行一致
- **THEN** server 日志显示 query 正常应答（无 "not allowed/fishy"），对局继续推进不卡死

#### Scenario: 197 双布局布局校验
- **WHEN** 实测 197 absent/present 两种布局字节
- **THEN** 8B absent 帧 server 无 197 fishy = 受理; C++ save(optional) absent 走 uint32(0) 4B 路径与 Python 1B 0x00 理论不匹配, 9B present 为回退候选

### Requirement: QueryReply 双布局回退
外挂发 QueryReply(197) SHALL 按 8B absent 首发; 若 server 197 鱼线出现 ("applying 10QueryReply...fishy") 或 10s 内无 PackageApplied(84) 回流, 换 9B present 重试一次。
真实 qid 数据源: server QUERY-DIAG 日志行 ([QUERY-DIAG] qid=N player=X type=...) 为主, 客户端 88/154-160 query 包体首字段 qid 为辅; 仅当我方 (MY_COLOR) qid != -1 才回送, 他方只记录。
客户端 88 PlayerStartsTurn 包体的 queryID 字段 = 上一回合 qid 残值, 不作回送依据 (09-11 P8-B 实锤坑)。

#### Scenario: 无计时器场景全程 qid=-1
- **WHEN** 对局无 player timer, QUERY-DIAG 行全部 qid=-1
- **THEN** 197 帧离线组包单测 + 实机发送 zero 197 fishy + server 16PlayerStartsTurn 广播 >=2 即 PASS(qid=-1 only), 与 09-14 p8c_query_probe_real 口径一致

#### Scenario: 有真实 qid 时回送
- **WHEN** QUERY-DIAG 行出现 qid != -1 且 player 为我方
- **THEN** 组包 8B 回送; 197 zero fishy = PASS(replied)

### Requirement: 玩家回合门控
玩家回合门控 SHALL 遵循以下规则：
- **WHEN** 收到 PlayerStartsTurn(88) 包
- **THEN** 包体 = queryID + playerColor 字段序（非 player+time_limit）；外挂仅在 MY_COLOR 回合发 EndTurn，否则 server 拒绝（"not allowed/fishy"）

#### Scenario: 非我方回合禁止发决策包
- **WHEN** 88 包体 playerColor != MY_COLOR 且对局进行中
- **THEN** 外挂 SHALL 仅回 180 EndTurn 占位或不发包，不发 MoveHero/Build/Recruit，否则 server 回 "not allowed/fishy"

### Requirement: Lobby 开局流程
多人局建立 SHALL 遵循：join → LobbyChangeHost(225) → LobbySetMap(229) → LobbyPrepareStartGame(223) → LobbyStartGame(224, 含 171KB StartGame 数据) → GAMEPLAY 包流。
server 注入诊断行（SRV-DIAG）：HERO OI dump / TOWNAVAIL dump，供外挂 tail 日志获取实体信息，免解析 171KB StartGame 包。

#### Scenario: 完整对局建立
- **WHEN** host 与 client1 完成 lobby 交换并发起开局
- **THEN** 双方进入 GAMEPLAY，server 日志零 "not allowed/fishy"

### Requirement: Query 分发诊断行（QUERY-DIAG）
server 在向玩家分发 query 时 SHALL 输出诊断行（SRV-DIAG 路线，复用 #206 模式）：
- 格式：`QUERY-DIAG: qid=<queryID> player=<player> type=<query类型>`
- 输出位置：query 注册/分发的服务端代码路径，写入 vcmiserver 标准日志
- 用途：外挂端 tail 日志获取活跃 queryID，免解析 StartGame/大包

#### Scenario: 招募确认 query 分发
- **WHEN** 城内触发招募确认 query 并分发给红方玩家
- **THEN** server 日志出现一行 `QUERY-DIAG: qid=... player=0 type=...`，外挂端可据此组装 QueryReply

## Notes

- 验证基线：离线 test_e2e 145/145 PASS；实机 P8-B 阶段1/2 + P8-C 决策接入（MoveHero/Build/Recruit）PASS（0911）；
  P8-C 收尾 2.1/2.2 QueryReply 8B/9B 实机验证 PASS（09-16, py/p8/p8c_query_reply.py 两次 clean run:
  ① DIAG qid=2/red 8B 帧发出 197 zero fishy = PASS(replied); ② qid=-1 only + server 16PST广播=3>=2 + 197 zero fishy = PASS(qid=-1 only)）
- 安全约束：恶意包不得炸服（#205 retrievePack try/catch 已修，回归时保持）
- fork/1.8 已知限制：green(NK2) 客户端在 16PlayerStartsTurn 广播#2 时 runNetwork 线程段错误（dmesg 实锤，
  每次 clean run 复现），导致 server SHUTDOWN + Python 连接 RST；对局推进判据以 server 侧 16PST 广播次数为准，
  与 green 存活无关。QueryReply 8B absent 与 C++ save(optional) absent 路径（uint32 4B）存在字节级不匹配疑点，
  9B present 为回退候选，待 197 fishy 出现时验证。
