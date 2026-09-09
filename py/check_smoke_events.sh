#!/bin/bash
grep -E '\[TOWN\]|\[MINE\]|\[GUARD|\[RECRUITED\]|\[TOWN_CAPTURE\]|win|victory' /tmp/smoke_out.log | head -10
echo "==== 全部事件词统计:"
grep -oE '\[[A-Z_-]+\]' /tmp/smoke_out.log | sort | uniq -c | sort -rn | head -12
