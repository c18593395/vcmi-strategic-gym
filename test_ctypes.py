#!/usr/bin/env python3
"""
ctypes test: read g_strategic_state directly from libmlclient.so
"""
import ctypes
import struct
import os
import sys

def main():
    libpath = "/home/administrator/vcmi-native/rel/bin/libmlclient.so"
    
    if not os.path.exists(libpath):
        print(f"ERROR: library not found: {libpath}")
        sys.exit(1)
    
    lib = ctypes.CDLL(libpath)
    print(f"Library loaded: {libpath}")
    
    # Read g_strategic_state pointer
    g_ss = ctypes.c_void_p.in_dll(lib, "g_strategic_state")
    print(f"g_strategic_state addr: {hex(g_ss.value or 0)}")
    
    if not g_ss.value:
        print("FAIL: g_strategic_state is NULL — init_vcmi() may not have been called yet")
        print("Run VCMI first (via gym) to initialize, then re-run this script")
        sys.exit(1)
    
    # Read raw bytes from the pointer
    data = ctypes.string_at(g_ss.value, 2000)
    
    # Parse StrategicState struct layout:
    # int32 day       offset 0
    # int32 week      offset 4
    # int32 month     offset 8
    # int32 curr_plr  offset 12
    # int32 map_w     offset 16
    # int32 map_h     offset 20
    # int32 undergrnd offset 24
    # int32 plr_cnt   offset 28
    # StrategicPlayer players[8] starts at offset 32
    # StrategicPlayer is ~40 bytes (10 int32s)
    
    day, week, month, cur_plr, map_w, map_h, has_u, plr_cnt = struct.unpack_from("iiiiiiii", data, 0)
    
    print(f"\n=== StrategicState dump ===")
    print(f"Day:      {day}")
    print(f"Week:     {week}")
    print(f"Month:    {month}")
    print(f"CurPlr:   {cur_plr}")
    print(f"MapSize:  {map_w}x{map_h}")
    print(f"Undergrn: {has_u}")
    print(f"PlrCnt:   {plr_cnt}")
    
    # Read players
    print(f"\n=== Players ===")
    player_offset = 32  # after 8 int32s = 32 bytes
    strategic_player_size = 40  # 10 int32s = 40 bytes
    for p in range(min(plr_cnt, 8)):
        off = player_offset + p * strategic_player_size
        (color, human, gold, wood, mercury, ore, sulfur,
         crystal, gems, hero_cnt, town_cnt, alive) = struct.unpack_from("iiiiiiiiiiii", data, off)
        print(f"  Player {p}: color={color} human={human} gold={gold} alive={alive} heroes={hero_cnt} towns={town_cnt}")
    
    print(f"\n=== Version ===")
    # _version is at the end of the struct, but let's read it
    version = struct.unpack_from("i", data, 2000 - 4)[0]
    print(f"Version:  {version}")
    
    print("\nSUCCESS: g_strategic_state is non-NULL and readable via ctypes!")

if __name__ == "__main__":
    main()
