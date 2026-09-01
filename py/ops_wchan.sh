#!/usr/bin/env bash
set +e
get_pids() {
  ps -ef | grep 'ep_runner_one.py' | grep -v grep | awk '{print $2}'
}
for pid in 379 $(get_pids); do
  echo "--- PID=$pid ---"
  if [ ! -d /proc/$pid ]; then echo '(pid not exists)'; continue; fi
  grep -E '^(Name|State|VmSize|VmRSS|Threads):' /proc/$pid/status 2>/dev/null || true
  echo -n 'wchan='; cat /proc/$pid/wchan 2>/dev/null; echo
done
echo '=== now vs mtime ==='
date '+now=%Y-%m-%d %T'
echo -n 'log_mtime='; stat -c '%y' /mnt/d/Bigdata/hero3_fresh/train_loop.log
echo -n 'age_minutes='; awk -v now=$(date +%s) -v m=$(stat -c '%Y' /mnt/d/Bigdata/hero3_fresh/train_loop.log) \
  'BEGIN{printf "%.1f\n", (now-m)/60}'
