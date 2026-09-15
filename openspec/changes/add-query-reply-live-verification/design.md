# Design: QueryReply(197) 实战验证

## Context

P8-C 决策接入已闭环（MoveHero/Build/Recruit 实机 PASS，vcmi bc3e124fa2+1c3be8d030）。离线 QueryReply 实现基于源码逆向（docs/序列化协议规格.md §5.3：8-9B = LVarInt queryID + player + LVarInt result），但 VCMI 的 query 体系有变数：queryID 分配在 server 侧运行时完成，外挂无法预知。SRV-DIAG 路线（踩坑 #206）已验证：server 注入诊断行 + Python tail 日志，免解析 171KB StartGame 包。

验证环境：WSL2 内 fork build（~/vcmi-native，非 rel/ 生产 .so），编译部署属日常迭代，不触停训纪律。

## Goals / Non-Goals

**Goals:**
- 用一个可控可重复的对局场景实测 QueryReply 全链路：query 触发 → QUERY-DIAG 诊断行 → 外挂组包回送 → server 受理 → 对局继续
- 确认离线字段序实机一致（不一致则以实机为准回写规格）
- 产出可复用脚本，供 P8-C 混人回合直接引用

**Non-Goals:**
- 不做 query 超时/重试机制（§6.3 已有设计，后续变更）
- 不碰战斗 query（BattleAction 另链路）
- 不动训练侧任何文件

## Decisions

1. **验证场景 = 招募确认 query**（而非对话/市场）
   - 理由：Build→Recruit 链已实机通，城内交互可控可重复；市场/酒馆依赖地图要素。备选：访客建筑确认。

2. **queryID 获取 = QUERY-DIAG 诊断行**（而非客户端包解析）
   - 理由：同 TOWNAVAIL 先例；客户端侧 query 包（CPackForClient 197 之外的 query 类包）字段带跨包去重 ref，外挂不可还原（踩坑 #204 结论）。注入点：CQuery 注册/分发处（queries/QueriesProcessor.cpp 或 CQuery.cpp，与现有 diag 同文件族）。

3. **注入开关 = 编译期宏 + 环境变量双控**
   - 理由：与 HERO/TOWNAVAIL diag 同模式；训练栈（~/vcmi-native build 树）与对局验证用同一棵树，宏关闭时零开销。不做运行时配置文件（复杂度不值）。

4. **验证脚本 = 独立 p8c_query_reply.py**（复用 py/vcmi_protocol 栈 + p8be_host_start.py 骨架）
   - 理由：ChangeHost 时序（225→229→223→224）已有验证过的参考实现；独立脚本不污染已有 PASS 基线脚本。

## Risks / Trade-offs

- [queryID 竞态：DIAG 行读到时 query 可能已超时] → 脚本 tail 到 DIAG 行后立即发包（同进程内 tail，延迟 <100ms）；首版接受偶尔重跑
- [result 字段语义不定（0=OK? 枚举?）] → 首包先试 result=0，失败再从源码 CQueryReply 构造处逆向确认；实机结果回写规格
- [server 对错误 queryID 的拒绝行为] → 已知 "fishy" 拒绝（#204 时代观测），无害可重试；不构成炸服风险（#205 已修）
- [9B vs 8B 歧义（result 是否 LVarInt 变长）] → 两种布局都实现，先发 8B 观测，被拒则换 9B——离线测试结论是 result 小值时 LVarInt 单字节，二者一致

## Migration Plan

1. 注入 QUERY-DIAG（默认关）→ 编译 → A Warm 图冒烟确认零行为变化
2. 开 diag 跑一局确认诊断行格式
3. 验证脚本全链路 → PASS 后结果回写 vcmi-protocol spec（archive 时合并）
4. 回滚：宏关闭重编译即回原状；脚本为新增文件可直删

## Open Questions

- 混人回合中真人玩家的 query 是否也走同一 QUERY-DIAG 行（影响 P8-C 混人设计，但不影响本验证）——留到 P8-C 混人变更时确认
