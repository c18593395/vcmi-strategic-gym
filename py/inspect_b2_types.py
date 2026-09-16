#!/usr/bin/env python3
"""列出 B2_adventure_knee_deep.vmap objects.json 的 type 短名分布, 作为 R4 白名单依据"""
import zipfile, json, collections

def strip_comments(text):
    out = []
    for line in text.splitlines():
        idx = line.find('//')
        if idx >= 0:
            line = line[:idx]
        out.append(line)
    return '\n'.join(out)

def main():
    p = '/home/administrator/vcmi-native/rel/bin/data/Maps/B2_adventure_knee_deep.vmap'
    z = zipfile.ZipFile(p)
    raw = z.read('objects.json').decode('utf-8')
    obj = json.loads(strip_comments(raw))
    items = list(obj.values()) if isinstance(obj, dict) else obj
    c = collections.Counter(it.get('type', '?') for it in items)
    print('total objects:', len(items), ' distinct types:', len(c))
    for t, n in c.most_common():
        print(f'{n:>4}  {t}')

if __name__ == '__main__':
    main()
