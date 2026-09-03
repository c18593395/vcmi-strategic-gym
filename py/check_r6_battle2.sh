#!/bin/bash
F=/tmp/hermes_ep_11638.log
echo "=== 战斗相关行全文:"
grep -iE 'in_battle|battleStart|battle' "$F"
echo "=== Router 行:"
grep -i 'router' "$F" | tail -3
echo "=== ZOMBIE/结束:"
grep -E 'ZOMBIE|ep_steps' "$F" | tail -3
