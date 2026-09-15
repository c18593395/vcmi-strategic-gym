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
- QueryReply (197) = 8-9B（queryID + player + result）
- RecruitCreatures (187) = 23B
- TryMoveHero (109) 回包字段序 = id + result + start + end + movePoints + fow + attackedFrom

#### Scenario: 玩家回合门控
- **WHEN** 收到 PlayerStartsTurn(88) 包
- **THEN** 包体 = queryID + playerColor 字段序（非 player+time_limit）；外挂仅在 MY_COLOR 回合发 EndTurn，否则 server 拒绝（"not allowed/fishy"）

### Requirement: Lobby 开局流程
多人局建立 SHALL 遵循：join → LobbyChangeHost(225) → LobbySetMap(229) → LobbyPrepareStartGame(223) → LobbyStartGame(224, 含 171KB StartGame 数据) → GAMEPLAY 包流。
server 注入诊断行（SRV-DIAG）：HERO OI dump / TOWNAVAIL dump，供外挂 tail 日志获取实体信息，免解析 171KB StartGame 包。

#### Scenario: 完整对局建立
- **WHEN** host 与 client1 完成 lobby 交换并发起开局
- **THEN** 双方进入 GAMEPLAY，server 日志零 "not allowed/fishy"

## Notes

- 验证基线：离线 test_e2e 145/145 PASS；实机 P8-B 阶段1/2 + P8-C 决策接入（MoveHero/Build/Recruit）PASS（0911）
- 安全约束：恶意包不得炸服（#205 retrievePack try/catch 已修，回归时保持）
- 待实战样本：QueryReply(197) 实战字段验证
