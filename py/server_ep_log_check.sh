#!/bin/bash
# 查服务器活体 ep_runner 明细日志里的 RECRUITED (绕过主日志白名单假象)
echo "===== [1] 服务器 /tmp 活体 ep 日志清单 ====="
ssh -o BatchMode=yes -o ConnectTimeout=10 root@172.16.2.40 "ls -lt /tmp/hermes_ep_*.log 2>/dev/null | head -8"
echo
echo "===== [2] 服务器活体 ep 日志 [RECRUITED] 统计 (最近 20 份) ====="
ssh -o BatchMode=yes -o ConnectTimeout=10 root@172.16.2.40 "for f in \$(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -20); do R=\$(grep -c 'RECRUITED' \$f 2>/dev/null); T=\$(grep -c 'TOWN_RETRY' \$f 2>/dev/null); E=\$(grep -c 'ECON. recruit' \$f 2>/dev/null); echo \"\$f  RECRUITED=\$R TOWN_RETRY=\$T ECON_recruit=\$E\"; done"
echo
echo "===== [3] 服务器最近一份有 RECRUITED 的 ep 日志内容样例 ====="
ssh -o BatchMode=yes -o ConnectTimeout=10 root@172.16.2.40 "for f in \$(ls -t /tmp/hermes_ep_*.log 2>/dev/null | head -40); do C=\$(grep -c 'RECRUITED' \$f 2>/dev/null); if [ \"\$C\" -gt 0 ]; then echo \"FOUND \$f count=\$C\"; grep 'RECRUITED\|EP_TIME' \$f | head -8; break; fi; done"
