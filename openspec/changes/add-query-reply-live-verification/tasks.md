# Tasks: QueryReply(197) 实战验证

## 1. QUERY-DIAG 诊断行注入（WSL fork）

- [ ] 1.1 在 ~/vcmi-native query 分发处（QueriesProcessor.cpp / CQuery.cpp）加 `QUERY-DIAG: qid=<id> player=<p> type=<t>` 日志行，编译期宏 + 环境变量双控（复用 SRV-DIAG 模式）。验证：宏关编译冒烟零行为变化
- [ ] 1.2 开 diag 编译部署 fork build，A Warm 图起一局，确认 server 日志出现 QUERY-DIAG 行且格式符合 spec。验证：grep QUERY-DIAG 非空且字段齐全

## 2. 验证脚本

- [ ] 2.1 新建 py/p8c_query_reply.py：复用 py/vcmi_protocol + p8be_host_start.py 骨架（ChangeHost 时序），新增 query 触发（城内招募确认）+ tail QUERY-DIAG + 组包 QueryReply(197)（8B 布局优先）。验证：离线 test_serialization_protocol 全 PASS
- [ ] 2.2 脚本内实现 8B→9B 布局回退：server 拒绝（fishy/query 不匹配）时换 9B 重试一次。验证：两种布局单元用例 PASS

## 3. 实机闭环验证

- [ ] 3.1 WSL 起真实对局（host + client1 + testmap guest 流程），外挂触发招募 query，tail 到 QUERY-DIAG 后回送 QueryReply。验证：server 日志 query 正常应答，零 "not allowed/fishy"
- [ ] 3.2 对局继续推进 ≥2 回合（query 应答后无卡死），两次 clean run 复现。验证：日志回合翻转 + 重复运行 PASS

## 4. 结果回写

- [ ] 4.1 实测字段序/字节数回写本 change specs delta（若与离线结论不一致，以实机为准修订）。验证：openspec validate --changes PASS
- [ ] 4.2 踩坑点沉淀（queryID 竞态/布局歧义实测结论）+ git commit。验证：docs 踩坑库有对应条目
