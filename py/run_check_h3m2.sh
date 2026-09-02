#!/bin/bash
set -e
cp /mnt/d/Bigdata/hero3_fresh/tools/h3m2vmap/main.cpp /home/administrator/vcmi-native/tools/h3m2vmap/main.cpp
cmake --build /home/administrator/vcmi-native/tools/h3m2vmap/build -j2 2>&1 | tail -1
cd /home/administrator/vcmi-native/rel/bin
B=/home/administrator/vcmi-native/tools/h3m2vmap/build/h3m2vmap
for f in "/tmp/T04_adventure_36X36_02.h3m" "/tmp/T03_adventure_30X30_01.h3m" "data/Maps/For Sale.h3m"; do
    echo "== $f"
    timeout 120 "$B" --check-h3m "$f" 2>&1 | tail -3 || echo "(engine load failed)"
done
