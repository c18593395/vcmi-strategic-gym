#!/bin/bash
# Create baseline backup of all critical files before step2 fix attempts
set -e
DEST=/home/administrator/vcmi-workspace/route-backups/base
mkdir -p $DEST/vcmi-native/ML
mkdir -p $DEST/vcmi-native/AI/MMAI/AAI
mkdir -p $DEST/vcmi_gym/connectors/v13
mkdir -p $DEST/bin

cp /home/administrator/vcmi-native/ML/MLClient.cpp $DEST/vcmi-native/ML/
cp /home/administrator/vcmi-native/ML/strategic_state.cpp $DEST/vcmi-native/ML/
cp /home/administrator/vcmi-native/ML/strategic_state.h $DEST/vcmi-native/ML/
cp /home/administrator/vcmi-native/AI/MMAI/AAI/AAI.cpp $DEST/vcmi-native/AI/MMAI/AAI/
cp /mnt/d/Bigdata/hero3_fresh/vcmi_gym/connectors/v13/threadconnector.h $DEST/vcmi_gym/connectors/v13/
cp /mnt/d/Bigdata/hero3_fresh/vcmi_gym/connectors/v13/threadconnector.cpp $DEST/vcmi_gym/connectors/v13/

cp /home/administrator/vcmi-native/rel/bin/libvcmi.so $DEST/bin/
cp /home/administrator/vcmi-native/rel/bin/libmlclient.so $DEST/bin/
cp /home/administrator/vcmi-native/rel/bin/libmlserverplugin.so $DEST/bin/
cp /home/administrator/vcmi-workspace/vcmi_gym/connectors/rel/connector_v13.so $DEST/bin/

cp /home/administrator/vcmi-native/rel/CMakeCache.txt $DEST/vcmi-native/

echo "BASE" > $DEST/CHECKPOINT
echo "=== BACKUP COMPLETE ==="
echo "Destination: $DEST"
ls -la $DEST/bin/
echo "---"
ls -la $DEST/vcmi-native/ML/
echo "---"
cat $DEST/CHECKPOINT
