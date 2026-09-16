#!/usr/bin/env python3
"""B4 调研/校验: 读 vmap 的 header.json (players canPlay/teams) + objects.json (hero/town owner)
用法: b4_recon_players.py [vmap路径]  (默认 B2 产物)"""
import zipfile, json, re, sys

def strip_comments(text):
    return re.sub(r'//[^\n]*', '', text)

def main():
    p = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/administrator/vcmi-native/rel/bin/data/Maps/B2_adventure_knee_deep.vmap'
    z = zipfile.ZipFile(p)

    h = json.loads(strip_comments(z.read('header.json').decode('utf-8')))
    print('=== header.json players ===')
    print(json.dumps(h.get('players', {}), indent=1))
    print('howManyTeams:', h.get('howManyTeams'))
    print('difficulty:', h.get('difficulty'))
    print('allowedHeroes cnt:', len(h.get('allowedHeroes', [])))
    print('allowedFactions keys sample:', [k for k in h.keys()])

    obj = json.loads(strip_comments(z.read('objects.json').decode('utf-8')))
    items = list(obj.values()) if isinstance(obj, dict) else obj
    print('\n=== hero / town raw entries ===')
    for it in items:
        t = it.get('type', '?')
        if t in ('hero', 'town'):
            print(json.dumps(it, ensure_ascii=False)[:400])
            print('---')

if __name__ == '__main__':
    main()
