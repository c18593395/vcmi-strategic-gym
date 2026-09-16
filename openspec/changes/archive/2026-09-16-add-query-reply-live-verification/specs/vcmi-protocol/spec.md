# Delta: vcmi-protocol — QueryReply 实战验证

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Query 分发诊断行（QUERY-DIAG）
server 在向玩家分发 query 时 SHALL 输出诊断行（SRV-DIAG 路线，复用 #206 模式）：
- 格式：`QUERY-DIAG: qid=<queryID> player=<player> type=<query类型>`
- 输出位置：query 注册/分发的服务端代码路径，写入 vcmiserver 标准日志
- 用途：外挂端 tail 日志获取活跃 queryID，免解析 StartGame/大包

#### Scenario: 招募确认 query 分发
- **WHEN** 城内触发招募确认 query 并分发给红方玩家
- **THEN** server 日志出现一行 `QUERY-DIAG: qid=... player=0 type=...`，外挂端可据此组装 QueryReply
