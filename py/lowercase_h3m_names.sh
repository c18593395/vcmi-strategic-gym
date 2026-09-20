#!/bin/bash
# H3M 源文件名统一小写 (09-20): VCMI VFS 资源查询路径小写化, ext4 大小写敏感 → 大写名查不到
cd /home/administrator/vcmi-native/rel/bin/data/Maps || exit 1
n=0
for f in *.h3m; do
  l=$(printf '%s' "$f" | tr 'A-Z' 'a-z')
  if [ "$f" != "$l" ]; then
    if [ -e "$l" ]; then
      echo "SKIP(dup): $f"
    else
      mv "$f" "$l"
      n=$((n+1))
    fi
  fi
done
echo "renamed: $n"
echo "remaining uppercase: $(ls | grep -c '[A-Z]')"
