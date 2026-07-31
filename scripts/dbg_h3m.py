#!/usr/bin/env python3
"""Debug parse of one h3m: print version, header fields, and failing offset."""
import gzip, struct, sys, traceback

def dbg(path):
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
    def sstr(tag):
        nonlocal pos
        l = u32()
        s = raw[pos:pos+l]; pos += l
        print('  str[%s] len=%d @%d: %r' % (tag, l, pos-l-4, s[:60]))
        return s
    def skip(k, tag=''):
        nonlocal pos
        print('  skip %d [%s] -> pos=%d' % (k, tag, pos+k))
        pos += k

    ver = u32()
    print('version=0x%08x pos=%d size=%d' % (ver, pos, n))
    levelAB = ver in (0x15, 0x1c, 0x18, 0x33, 0x20)
    levelSOD = ver in (0x1c, 0x18, 0x33, 0x20)
    fb = 1 if ver == 0x0e else (4 if ver == 0x20 else 2)
    inactive_skip = 6 + (6 if levelAB else 0) + (1 if levelSOD else 0)
    print('levelAB=%s levelSOD=%s factions_bytes=%d inactive_skip=%d' % (levelAB, levelSOD, fb, inactive_skip))

    if ver == 0x20:
        hv = u32(); print('hota_version=%d' % hv)
        if hv >= 8: u32(); u32(); u32()
        if hv >= 1: u8(); u8()
        if hv >= 2: u32()
        if hv >= 5: u32(); u8()
        if hv >= 7: u8()
        if hv >= 8: u8()
        if hv >= 9: u32()

    u8(); print('areAnyPlayers @%d' % (pos-1))
    w = u32(); print('width=%d' % w)
    ug = u8(); print('hasUnderground=%d' % ug)
    sstr('name')
    sstr('desc')
    d = u8(); print('difficulty=%d @%d' % (d, pos-1))
    if levelAB:
        ll = u8(); print('levelLimit=%d' % ll)

    for i in range(8):
        if pos + 2 > n:
            print('  !! ran out at player %d pos=%d n=%d' % (i, pos, n)); return
        ch = u8(); cc = u8()
        print('  P%d canHuman=%d canComputer=%d @%d' % (i, ch, cc, pos-2))
        if not (ch or cc):
            skip(inactive_skip, 'inactive')
            continue
        u8()  # aiTactic
        if levelSOD: skip(1, 'factionSelectable')
        skip(fb, 'factionMask')
        u8()  # isFactionRandom
        ht = u8()
        print('    hasMainTown=%d' % ht)
        if ht:
            if levelAB:
                u8(); skip(1, 'townType')
            skip(3, 'townPos')
        u8()  # hasRandomHero
        hid = u8()
        print('    heroId=%d' % hid)
        if hid != 0xff:
            u8()  # portrait
            sstr('heroName')
        if levelAB:
            skip(1, 'abUnknown')
            hc = u32()
            print('    AB heroCount=%d' % hc)
            for _ in range(hc):
                u8()
                sstr('abHero')
    print('DONE players parsed, pos=%d n=%d' % (pos, n))

if __name__ == '__main__':
    p = sys.argv[1]
    print('=== %s ===' % p)
    try:
        dbg(p)
    except Exception:
        traceback.print_exc()
