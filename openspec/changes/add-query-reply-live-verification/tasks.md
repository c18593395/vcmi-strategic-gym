# Tasks: QueryReply(197) 实战验证

## 1. QUERY-DIAG 诊断行注入（WSL fork）

- [x] 1.1 在 ~/vcmi-native query 分发处（QueriesProcessor.cpp）加 `QUERY-DIAG: qid=<id> player=<p> type=<t>` 日志行，编译期宏 + 环境变量双控（复用 SRV-DIAG 模式）。验证：宏关编译冒烟零行为变化 ✓（vcmiserver 全绿）
- [x] 1.2 开 diag 编译部署 fork build，实机一局确认 server 日志出现 QUERY-DIAG 行且格式符合 spec。验证：`[QUERY-DIAG] qid=2 player=red type=A query of type '19MapObjectVisitQuery'...` 实测输出 ✓，对局真实建立（game_started=True，红/绿回合轮转），零 fishy

## 1B. 引擎根治补丁（apply 过程中发现的 fork 1.8 headless 崩溃链，计划外必要工作）

- [x] 1B.1 client/CServerHandler.cpp 五处 ENGINE 空指针防护（onConnectionFailed/onTimer/sendLobbyPack/myFirstColor/onConnectionEstablished+onPacketReceived+onDisconnected+applyPackOnLobbyScreen）——headless 模式 ENGINE=nullptr 全部解引用段错误（gdb 实证）。验证：编译全绿 + client1 实机不再崩 ✓
- [x] 1B.2 debugStartTest 补 `si->mlconfig.init(settings)`（fork 缺失 → statsMode 落默认 "red" → Stats dbpath="-" → "no such table: stats" 开局失败）+ Config.h 默认 statsMode 改 "disabled"（训练栈由 MLClient 显式注入不受影响）。验证：开局失败消除 ✓

## 2. 验证脚本

- [ ] 2.1 新建 py/p8c_query_reply.py：复用 py/vcmi_protocol + p8c_qdiag_smoke.py 骨架（ChangeHost 时序已验证可用），新增 query 触发（城内招募确认）+ tail QUERY-DIAG + 组包 QueryReply(197)（8B 布局优先）。验证：离线 test_serialization_protocol 全 PASS
- [ ] 2.2 脚本内实现 8B→9B 布局回退：server 拒绝（fishy/query 不匹配）时换 9B 重试一次。验证：两种布局单元用例 PASS

## 3. 实机闭环验证

- [ ] 3.1 WSL 起真实对局（python host + client1 testmap 流程，骨架已跑通），外挂触发招募 query，tail 到 QUERY-DIAG 后回送 QueryReply。验证：server 日志 query 正常应答，零 "not allowed/fishy"
- [ ] 3.2 对局继续推进 ≥2 回合（query 应答后无卡死），两次 clean run 复现。验证：日志回合翻转 + 重复运行 PASS

## 4. 结果回写

- [ ] 4.1 实测字段序/字节数回写本 change specs delta（若与离线结论不一致，以实机为准修订）。验证：openspec validate --changes PASS
- [ ] 4.2 踩坑点沉淀（ENGINE 空指针链/dbpath "-"/探活毒杀 server/端口层级）+ git commit。验证：docs 踩坑库有对应条目

## 环境备注（2.1-3.2 直接复用）

- 冒烟骨架 py/p8/p8c_qdiag_smoke.py 已全链路可用：server(diag=1) → python host → client1 guest → ChangeHost → 开局
- 禁"连了再断"探活（fork: 首连断开=host 走人→SHUTDOWN）
- client 端口读两级 settings.json 的 server.localPort（已改 3030），--serverport 不生效
- 地图须无空格名（fork 资源系统空格路径 bug），A_Warm_and_Familiar_Place.h3m 已备
