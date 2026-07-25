#!/usr/bin/env python3
"""C5.1: Parse .h3m player count — ROE format (v0x0e).
Follows VCMI MapFormatH3M exactly for ROE."""
import gzip, os, glob, json

MAPS_DIR = "/home/administrator/vcmi-strategic/vcmi/data/Maps"
OUTPUT = "/mnt/d/Bigdata/hero3_fresh/multiplayer_maps.json"

def get_player_count(path):
    with gzip.open(path, 'rb') as f:
        data = f.read()
    n = len(data)
    if n < 50: return 0
    
    pos = 0
    # version (4 bytes uint32)
    ver = int.from_bytes(data[pos:pos+4], 'little'); pos += 4
    # areAnyPlayers (1)
    _ = data[pos]; pos += 1
    # width/height (4)
    _ = int.from_bytes(data[pos:pos+4], 'little'); pos += 4
    # hasUnderground (1)
    _ = data[pos]; pos += 1
    
    # map name: length-prefixed string (uint32 + data)
    if pos + 4 > n: return 0
    sl = int.from_bytes(data[pos:pos+4], 'little'); pos += 4 + sl
    
    # description
    if pos + 4 > n: return 0
    sl = int.from_bytes(data[pos:pos+4], 'little'); pos += 4 + sl
    
    # difficulty (1 byte, 0-4)
    if pos >= n: return 0
    pos += 1
    
    # readPlayerInfo — 8 players
    active = 0
    for i in range(8):
        if pos + 2 > n: break
        can_h = data[pos]; can_c = data[pos+1]
        pos += 2
        
        if not (can_h or can_c):
            # Inactive: skip 6 unused bytes (ROE)
            pos += 6
            continue
        
        active += 1
        
        # Active player structure (ROE format):
        # aiTactic (int8, 1 byte)
        if pos >= n: break
        pos += 1
        
        # factionBitmask (1 byte for ROE, 2 for SOD+)
        if pos >= n: break
        pos += 1
        
        # isFactionRandom (1 byte)
        if pos >= n: break
        pos += 1
        
        # hasMainTown (1 byte)
        if pos >= n: break
        has_town = data[pos]; pos += 1
        
        if has_town:
            # posOfMainTown = readInt3() (3 bytes: X, Y, level)
            if pos + 3 > n: break
            pos += 3
        
        # hasRandomHero (1 byte)
        if pos >= n: break
        pos += 1
        
        # readHero() — reads hero ID
        # For ROE: heroIdentifierInvalid=0xff, reads 1 byte
        if pos >= n: break
        hero_id = data[pos]; pos += 1
        
        if hero_id != 0xff:
            # heroPortrait (1 byte)
            if pos >= n: break
            pos += 1
            
            # heroName = readLocalizedString (uint32 + data)
            if pos + 4 > n: break
            nl = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4 + nl
        
        # No AB-level hero list for ROE
    
    return active

def main():
    h3m_files = sorted(glob.glob(os.path.join(MAPS_DIR, "*.h3m")))
    by_players = {}
    errors = []
    total = len(h3m_files)
    
    for i, f in enumerate(h3m_files):
        name = os.path.basename(f)
        pc = get_player_count(f)
        if pc > 0:
            by_players.setdefault(pc, []).append(name)
        else:
            errors.append(name)
        if (i+1) % 40 == 0 or i == 0 or i == total:
            print(f"[{i+1}/{total}]", flush=True)
    
    for pc in sorted(by_players.keys()):
        lst = by_players[pc]
        print(f"\n{pc}p [{len(lst)}]:")
        for m in sorted(lst[:15]):
            print(f"  - {m}")
        if len(lst) > 15: print(f"  ... +{len(lst)-15}")
    
    if errors:
        print(f"\nFailed [{len(errors)}]: {errors[:10]}")
    
    out = {"by_players": {str(k): sorted(v) for k,v in by_players.items()}, "total": total}
    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to {OUTPUT}")

if __name__ == "__main__":
    main()
