#!/usr/bin/env python3
# 09-14 T06 _02 系 4 图 header 缺字段批量修补
# 根因: regenerate_level5.py / regenerate_t06_108.py 只写 5 字段 header,
#        引擎启动报 "Failed to launch game: Invalid range provided: 0 ... -1"
#        (缺 victoryConditions/triggeredEvents/versionMajor 等, 01 系 13 字段正常)
# 修补: 注入 01 系同款 8 字段, 保留各图 name/description/mapLevels/players,
#        mods 置 null 与 01 系一致; terrain/objects 原样字节回写
import zipfile, json, os, shutil, sys

MAPDIR = "/mnt/d/Bigdata/hero3_fresh/maps/training"
TARGETS = [
    "T06_adventure_72X72_02.vmap",
    "T06_adventure_72X72_02_duel.vmap",
    "T06_adventure_108X108_02.vmap",
    "T06_adventure_108X108_02_duel.vmap",
]

# 取自 T06_adventure_72X72_01.vmap (引擎验证可正常成局) 的静态字段
TEMPLATE_FIELDS = {
    "allowedArtifacts": {"anyOf": ["core:pendantOfFreeWill"]},
    "defeatIconIndex": 3,
    "difficulty": "NORMAL",
    "victoryConditions": ["standardDefeat", "specialVictory"],
    "triggeredEvents": {
        "specialVictory": {
            "condition": ["allOf", ["isHuman", {"value": 1}],
                          ["haveResources", {"type": 0, "value": 100}]],
            "effect": {"type": "victory"},
            "message": {"exactStrings": None, "localStrings": None,
                        "message": [2], "numbers": None,
                        "stringsTextID": ["core.genrltxt.278"]},
        },
        "standardDefeat": {
            "condition": ["daysWithoutTown", {"value": 7}],
            "effect": {"type": "defeat"},
            "message": {"exactStrings": None, "localStrings": None,
                        "message": [2], "numbers": None,
                        "stringsTextID": ["core.genrltxt.7"]},
        },
    },
    "versionMajor": 1,
    "versionMinor": 1,
    "victoryIconIndex": 2,
}

def patch(path, do_write=True):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    raw = {n: z.read(n) for n in names}
    header = json.loads(raw["header.json"].decode("utf-8"))
    missing = [k for k in TEMPLATE_FIELDS if k not in header]
    if not missing and header.get("mods", "UNSET") is None:
        print(f"SKIP {os.path.basename(path)}: 字段已齐全")
        return False
    new_header = dict(header)
    for k, v in TEMPLATE_FIELDS.items():
        new_header.setdefault(k, v)
    new_header["mods"] = None  # 01 系为 null; players 补丁曾置 {}
    # 保持 01 系字段观感顺序
    ordered = {
        "allowedArtifacts": new_header["allowedArtifacts"],
        "defeatIconIndex": new_header["defeatIconIndex"],
        "description": new_header["description"],
        "difficulty": new_header["difficulty"],
        "mapLevels": new_header["mapLevels"],
        "mods": None,
        "name": new_header["name"],
        "players": new_header["players"],
        "victoryConditions": new_header["victoryConditions"],
        "triggeredEvents": new_header["triggeredEvents"],
        "versionMajor": new_header["versionMajor"],
        "versionMinor": new_header["versionMinor"],
        "victoryIconIndex": new_header["victoryIconIndex"],
    }
    print(f"PATCH {os.path.basename(path)}: 补 {missing} + mods->null; players 保留")
    if not do_write:
        return True
    bak = path + ".bak_header_0914"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            if n == "header.json":
                zo.writestr(n, json.dumps(ordered, indent=2, ensure_ascii=False))
            else:
                zo.writestr(n, raw[n])
    os.replace(tmp, path)
    return True

if __name__ == "__main__":
    dry = "--dry" in sys.argv
    for f in TARGETS:
        patch(os.path.join(MAPDIR, f), do_write=not dry)
    print("DONE" if not dry else "DRY-RUN DONE")
