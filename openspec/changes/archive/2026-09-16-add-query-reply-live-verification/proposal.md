# Proposal: QueryReply(197) 实战验证闭环（P8-C 收尾）

## Why

外挂协议栈已实机打通 MoveHero(182)/Build(185)/Recruit(187)（P8-C 决策接入闭环，0911），但 QueryReply(197) 仅有离线字节级实现（8-9B 布局），缺实战样本。VCMI server 的查询-应答机制（CQuery/CQueryReply）是对话、市场、招募确认等交互的必经路径——不验证 QueryReply，P8-C 混人回合（人机同局）会在第一个 query 弹窗时卡死。这是 P8-D 跨机前的最后一个协议盲区。

## What Changes

- 新增实战验证脚本：外挂客户端在对局中触发 server query 并回送 QueryReply(197)，验证字段序（queryID + player + result）与离线实现一致
- 新增 server 侧观测：复用 SRV-DIAG 路线（#206），在 query 分发处注入诊断行，免解析大包获取 queryID
- 验证场景选型：优先"城内英雄访问招募建筑触发确认 query"（可控、可重复、不依赖战斗）
- vcmi-protocol spec 补充 QueryReply 实战验证结果与 query 分发契约（验证后）

## Capabilities

### New Capabilities

（无——不改行为契约，仅验证既有契约）

### Modified Capabilities

- `vcmi-protocol`: 核心包布局 requirement 中 QueryReply 从"待实战验证"变为"实机 PASS"，并补充 query 分发诊断行契约（SRV-DIAG QUERY-DIAG 行格式）

## Impact

- `py/p8c_query_reply.py`（新增验证脚本，参照 p8be_host_start.py 模式）
- vcmi fork（WSL ~/vcmi-native）：CQuery 分发处可选诊断行注入（1-2 行，复用 SRV-DIAG 模式）
- 无训练侧影响：全程 Track 2（真实游戏对齐），不碰 ep_runner/奖励判定，不碰 rel/.so 部署，零停训
- 风险：QueryReply 发错 queryID 会触发 server "fishy" 拒绝（同 #204 时代行为），需先 DIAG 确认再发包
