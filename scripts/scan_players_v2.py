#!/usr/bin/env python3
"""Scan .h3m player counts following VCMI MapFormatH3M.cpp readHeader/readPlayerInfo exactly.
Usage: python scan_players_v2.py
Reads the 158 project maps (union of available_maps.json maps+failed), outputs 2p/3p lists.
"""
import gzip, struct, os, json, glob

ROE, AB, SOD, CHR, WOG, HOTA = 0x0e, 0x15, 0x1c, 0x18, 0x33, 0x20

def parse_header(path):
    with open(path, 'rb') as f:
        raw = gzip.decompress(f.read())
    n = len(raw)
    pos = 0
    def u8():
        nonlocal pos
        v = raw[pos]; pos += 1; return v
    def u32():
        nonlocal pos
        v = struct.unpack('<I', raw[pos:pos+4])[0]; pos += 4; return v
    def i32():
        nonlocal pos
        v = struct.unpack('<i', raw[pos:pos+4])[0]; pos += 4; return v
    def sstr():
        nonlocal pos
        l = u32(); s = raw[pos:pos+l]; pos += l; return s
    def skip(k):
        nonlocal pos
        pos += k

    ver = u32()
    if ver not in (ROE, AB, SOD, CHR, WOG, HOTA):
        return {'error': 'unknown version 0x%08x' % ver, 'version': ver}

    levelAB = ver in (AB, SOD, CHR, WOG, HOTA)
    levelSOD = ver in (SOD, CHR, WOG, HOTA)
    factions_bytes = 1 if ver == ROE else (4 if ver == HOTA else 2)
    # VCMI readPlayerInfo: inactive skip is SEQUENTIAL ifs (features chain from ROE):
    # ROE->6, AB->6+6=12, SOD->6+6+1=13
    inactive_skip = 6 + (6 if levelAB else 0) + (1 if levelSOD else 0)

    if ver == HOTA:
        hota_version = u32()
        if hota_version > 9:
            return {'error': 'hota_version>9', 'version': ver}
        if hota_version >= 8:
            u32(); u32(); u32()
        if hota_version >= 1:
            u8(); u8()                      # isMirrorMap, isArenaMap
        if hota_version >= 2:
            u32()                           # terrainTypesCount
        if hota_version >= 5:
            u32(); u8()                     # townTypesCount, allowedDifficultiesMask
        if hota_version >= 7:
            u8()                            # canHireDefeatedHeroes
        if hota_version >= 8:
            u8()                            # forceMatchingVersion
        if hota_version >= 9:
            i32()                           # unknown

    are_any = u8()
    width = u32()
    has_ug = u8()
    map_name = sstr()
    sstr()                                  # description
    difficulty = u8()
    if levelAB:
        u8()                                # levelLimit

    players = []
    for i in range(8):
        can_h = u8(); can_c = u8()
        if not (can_h or can_c):
            skip(inactive_skip)             # inactive player record
            continue
        players.append({'idx': i, 'human': bool(can_h), 'ai': bool(can_c)})
        u8()                                # aiTactic
        if levelSOD:
            skip(1)                         # faction selectable
        skip(factions_bytes)                # faction bitmask
        u8()                                # isFactionRandom
        has_town = u8()
        if has_town:
            if levelAB:
                u8()                        # generateHeroAtMainTown
                skip(1)                     # starting town type
            skip(3)                         # posOfMainTown int3
        u8()                                # hasRandomHero
        hero_id = u8()
        if hero_id != 0xff:
            u8()                            # hero portrait
            sstr()                          # custom hero name
        if levelAB:
            skip(1)                         # unknown
            hc = u32()                      # heroCount
            for _ in range(hc):
                u8()                        # hero id
                sstr()                      # hero name

    return {
        'version': '0x%02x' % ver,
        'name': map_name.decode('gbk', errors='replace').rstrip('\x00'),
        'width': width, 'has_ug': bool(has_ug),
        'difficulty': difficulty,
        'players': players,
        'header_end': pos,
        'file_size': os.path.getsize(path),
    }

def main():
    base = r'D:\Bigdata\hero3_fresh'
    maps_dir = r'D:\GAMES\cbhHeroes3\Maps'
    with open(os.path.join(base, 'available_maps.json'), encoding='utf-8') as f:
        avail = json.load(f)
    usable = set(avail['maps'])
    failed = set(avail['failed'])
    all158 = usable | failed
    print('available_maps: usable=%d failed=%d union=%d' % (len(usable), len(failed), len(all158)))

    with open(os.path.join(base, 'multiplayer_maps.json'), encoding='utf-8') as f:
        old = json.load(f)
    old_names = set()
    for lst in old['by_players'].values():
        old_names.update(lst)
    print('multiplayer_maps.json: %d names, overlap with union=%d, missing=%s' % (
        len(old_names), len(old_names & all158), sorted(old_names - all158)[:5]))

    # case-insensitive lookup of actual files
    actual = {}
    for p in glob.glob(os.path.join(maps_dir, '*.h3m')):
        actual[os.path.basename(p).lower()] = p

    missing = [nm for nm in all158 if nm.lower() not in actual]
    print('missing on disk: %d %s' % (len(missing), missing[:10]))

    results = {}
    errs = []
    for nm in sorted(all158):
        p = actual.get(nm.lower())
        if not p:
            results[nm] = {'error': 'not on disk'}
            continue
        try:
            r = parse_header(p)
            results[nm] = r
        except Exception as e:
            results[nm] = {'error': 'parse exception: %r' % e}
            errs.append(nm)

    # ground-truth validation
    gt = {'Key to Victory.h3m': 2, 'Free for All.h3m': 8, 'Twins.h3m': 2,
          'Noahs Ark.h3m': 3, 'For Sale.h3m': 3, 'Elbow Room.h3m': 6,
          'Arrogance.h3m': 4, 'Battle of the Sexes.h3m': 4}
    print('\n=== GROUND TRUTH CHECK ===')
    for nm, exp in gt.items():
        r = results.get(nm, {})
        got = len(r.get('players', [])) if 'players' in r else r.get('error', '?')
        mark = 'OK' if got == exp else 'MISMATCH'
        print('  %-32s expected=%d got=%s [%s]' % (nm, exp, got, mark))

    # summary
    from collections import Counter
    cnt = Counter(len(r.get('players', [])) if 'players' in r else -1 for r in results.values())
    print('\n=== DISTRIBUTION ===')
    for k in sorted(cnt):
        print('  %sp: %d' % (k, cnt[k]))

    by_p = {}
    for nm, r in sorted(results.items()):
        if 'players' in r:
            by_p.setdefault(len(r['players']), []).append((nm, r))
    for k in (2, 3):
        print('\n=== %dp MAPS (%d) ===' % (k, len(by_p.get(k, []))))
        for nm, r in sorted(by_p.get(k, [])):
            slots = ','.join(str(p['idx']) for p in r['players'])
            print('  %-42s v=%s %4dx%-3d ug=%d diff=%d slots=[%s] usable=%s' % (
                nm, r['version'], r['width'], r['width'], int(r['has_ug']),
                r['difficulty'], slots, 'Y' if nm in usable else 'N'))

    out = {'by_players': {str(k): sorted(nm for nm, _ in v) for k, v in by_p.items()},
           'detail': {nm: r for nm, r in results.items()},
           'errors': errs}
    outpath = os.path.join(base, 'maps_player_count_v2.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('\nSaved: %s' % outpath)

if __name__ == '__main__':
    main()
