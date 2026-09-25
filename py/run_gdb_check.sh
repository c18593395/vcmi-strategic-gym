#!/bin/bash
cd /home/administrator/vcmi-native/rel/bin
B="${B:-/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap}"
timeout 120 gdb -batch -ex run -ex bt -ex 'frame 5' -ex 'info args' \
  --args "$B" --check-h3m "/tmp/T04_adventure_36X36_02.h3m" 2>&1 | tail -30
