#!/usr/bin/env bash
set +e
SEC=160
echo "=== wait ${SEC}s @ $(date '+%T') ==="
sleep $SEC
bash /mnt/d/Bigdata/hero3_fresh/py/ops_probe_verify.sh 2>&1
