import zipfile, json, os

out = "/mnt/d/GAMES/Heroes3/Maps/gym/s1.vmap"
os.makedirs(os.path.dirname(out), exist_ok=True)

terrain = []
for y in range(36):
    row = []
    for x in range(36):
        if y in (1, 34):
            row.append("ro{:02d}_".format(x % 32))
        else:
            row.append("gr{:02d}_".format(x % 32))
    terrain.append(row)

objects = {
    "hero_0": {
        "type": "hero", "subtype": "ML:hero_0",
        "x": 2, "y": 2, "l": 0,
        "options": {
            "owner": "red", "name": "Orrin",
            "experience": 1000,
            "army": [{}, {}, {"amount": 10, "type": "core:pikeman"}, {}, {}, {}, {}],
            "primarySkills": {"attack": 2, "defense": 2, "spellpower": 1, "knowledge": 1}
        }
    },
    "hero_1": {
        "type": "hero", "subtype": "ML:hero_1",
        "x": 33, "y": 33, "l": 0,
        "options": {
            "owner": "blue", "name": "Adela",
            "experience": 1000,
            "army": [{}, {}, {"amount": 10, "type": "core:pikeman"}, {}, {}, {}, {}],
            "primarySkills": {"attack": 1, "defense": 2, "spellpower": 2, "knowledge": 2}
        }
    },
    "town_0": {
        "type": "town", "subtype": "castle",
        "x": 1, "y": 3, "l": 0,
        "template": {"animation": "AVCCAST0.DEF", "editorAnimation": "",
            "mask": ["VVVVVV","VVVVVV","VVVVVV","VVBBBV","VBBBBB","VBBABB"],
            "visitableFrom": ["---","+-+","+++"]},
        "options": {"owner": "red", "buildings": {"allOf": ["core:fort", "core:tavern"]}, "tightFormation": "wide"}
    },
    "town_1": {
        "type": "town", "subtype": "castle",
        "x": 34, "y": 32, "l": 0,
        "template": {"animation": "AVCCAST0.DEF", "editorAnimation": "",
            "mask": ["VVVVVV","VVVVVV","VVVVVV","VVBBBV","VBBBBB","VBBABB"],
            "visitableFrom": ["---","+-+","+++"]},
        "options": {"owner": "blue", "buildings": {"allOf": ["core:fort", "core:tavern"]}, "tightFormation": "wide"}
    },
}

header = {
    "name": "S1 - Strategic Test",
    "description": "Minimal 36x36 adventure map for strategic RL training",
    "versionMajor": 1, "versionMinor": 1,
    "difficulty": "NORMAL", "mods": None,
    "players": {
        "red": {"canPlay": "PlayerOrAI", "heroes": {"hero_0": {"type": "ML:hero_0"}}},
        "blue": {"canPlay": "PlayerOrAI", "heroes": {"hero_1": {"type": "ML:hero_1"}}}
    },
    "mapLevels": {"surface": {"height": 36, "index": 0, "width": 36}},
    "triggeredEvents": {
        "specialVictory": {"condition": {"allOf": []}, "message": "Victory!"},
        "standardDefeat": {"condition": {"noneOf": []}, "message": "Defeat"}
    },
    "victoryIconIndex": 2, "defeatIconIndex": 3,
    "allowedArtifacts": {"anyOf": []},
    "events": [], "rumors": []
}

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("header.json", json.dumps(header, indent=2))
    z.writestr("objects.json", json.dumps(objects, indent=2))
    z.writestr("surface_terrain.json", json.dumps(terrain))

print("Created s1.vmap ({}B)".format(os.path.getsize(out)))
