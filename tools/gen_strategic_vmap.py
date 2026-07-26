#!/usr/bin/env python3
"""
VCMI Strategic Adventure vmap Map Generator

生成用于战略层 RL 训练的大型冒险地图。
地图特征：
  - 72x72 地形（草地主，混合 dirt/road）
  - 2 个玩家，各1个主城 + 1个英雄
  - 散布资源堆（金、木、石等）
  - 中立怪物守护的矿场
  - 散布宝物
  - 道路连接关键位置

用法:
  python gen_strategic_vmap.py --size 72 --output maps/gym/adventure-strategic-s1.vmap
  python gen_strategic_vmap.py --size 96 --towns 4 --output maps/gym/adventure-strategic-large.vmap
"""

import argparse
import json
import os
import random
import zipfile
from io import BytesIO

# ============================================================
# Constants
# ============================================================

# Terrain tile types (VCMI format: "XX##_" where XX=type, ##=variant, _=rotation/flags)
GRASS_TILES = [f"gr{i:02d}_" for i in range(20, 75)]  # grass variants
DIRT_TILES  = [f"dt{i:02d}_" for i in range(0, 50)]   # dirt variants  
ROAD_TILES  = [f"ro{i:02d}_" for i in range(0, 20)]   # road variants
WATER_TILES = [f"wt{i:02d}_" for i in range(0, 30)]   # water variants
SAND_TILES  = [f"sa{i:02d}_" for i in range(0, 10)]   # sand variants

# Monster types (easy → hard)
MONSTERS_EASY = [
    "core:peasant", "core:imp", "core:gremlin", "core:skeleton",
    "core:pixie", "core:centaur", "core:gnoll", "core:troglodyte",
]
MONSTERS_MEDIUM = [
    "core:stoneGolem", "core:ironGolem", "core:harpy", "core:gargoyle",
    "core:orc", "core:ogre", "core:roc", "core:nomad",
]
MONSTERS_HARD = [
    "core:griffin", "core:minotaur", "core:hydra", "core:angel",
    "core:blackKnight", "core:boneDragon", "core:redDragon",
]

# Mine types
MINE_TYPES = [
    ("goldMine", 2000),       # 金矿最值钱
    ("sawmill", 1000),        # 锯木厂
    ("orePit", 1000),         # 矿坑
    ("alchemistLab", 1500),   # 炼金实验室
    ("sulfurDune", 1500),     # 硫磺沙丘
    ("crystalCavern", 1500),  # 水晶洞穴
    ("gemPond", 1500),        # 宝石池
]

# Artifact types
ARTIFACTS = [
    "centaurAxe", "blackshardOfTheDeadKnight",
    "greaterGnollsFlail", "ogresClubOfHavoc",
    "swordOfHellfire", "titansGladius",
    "shieldOfTheYawningDead", "breastplateOfPetrifiedWood",
    "ribCage", "scalesOfTheGreaterBasilisk",
    "helmOfChaos", "crownOfTheSupremeMagi",
    "pendantOfFreeWill", "badgeOfCourage",
    "ringOfInfiniteGems", "capeOfVelocity",
]

# ============================================================
# Map Generator
# ============================================================

class StrategicMapGenerator:
    def __init__(self, size=72, seed=None, towns_per_player=1, resource_density=0.6):
        self.size = size
        self.seed = seed or random.randint(0, 2**31 - 1)
        self.towns_per_player = towns_per_player
        self.resource_density = resource_density
        random.seed(self.seed)
        
        self.terrain = None
        self.objects = {}
        self.obj_counter = {}
    
    def _next_id(self, prefix):
        self.obj_counter[prefix] = self.obj_counter.get(prefix, -1) + 1
        return f"{prefix}_{self.obj_counter[prefix]}"
    
    def generate_terrain(self):
        """Generate terrain with grass, scattered dirt patches, and water edges."""
        self.terrain = []
        
        for y in range(self.size):
            row = []
            for x in range(self.size):
                # Borders: water
                if x == 0 or y == 0 or x == self.size - 1 or y == self.size - 1:
                    row.append(random.choice(WATER_TILES))
                # Some water lakes
                elif 10 <= x <= 15 and 10 <= y <= 15:
                    row.append(random.choice(WATER_TILES))
                elif self.size - 16 <= x <= self.size - 11 and self.size - 16 <= y <= self.size - 11:
                    row.append(random.choice(WATER_TILES))
                # Dirt patches (10% chance)
                elif random.random() < 0.10:
                    row.append(random.choice(DIRT_TILES))
                # Small sand near water
                elif (x < 3 or y < 3 or x > self.size - 4 or y > self.size - 4):
                    if random.random() < 0.2:
                        row.append(random.choice(SAND_TILES))
                    else:
                        row.append(random.choice(GRASS_TILES))
                else:
                    row.append(random.choice(GRASS_TILES))
            self.terrain.append(row)
    
    def generate_road(self, start, end):
        """Draw a rough road from start to end (Manhattan path with randomness).
        NOTE: Uses GRASS tiles, not road tiles — VCMI vmap format doesn't support
        standalone road terrain codes ("roXX_" is not a valid terrain type)."""
        x, y = start
        ex, ey = end
        path = []
        
        while (x, y) != (ex, ey):
            path.append((x, y))
            if random.random() < 0.5 and x != ex:
                x += 1 if ex > x else -1
            elif y != ey:
                y += 1 if ey > y else -1
            elif x != ex:
                x += 1 if ex > x else -1
        
        path.append((ex, ey))
        
        for px, py in path:
            if 0 <= px < self.size and 0 <= py < self.size:
                tile = random.choice(GRASS_TILES)  # VCMI vmap uses terrain-only, not standalone road codes
                self.terrain[py][px] = tile
    
    def add_player_setup(self, player_color, town_pos, hero_pos):
        """Add player town(s) and starting hero."""
        town_objs = []
        
        # Starting town
        for i in range(self.towns_per_player):
            if i == 0:
                tx, ty = town_pos
            else:
                # Additional towns nearby
                tx = town_pos[0] + random.randint(-3, 3)
                ty = town_pos[1] + random.randint(-3, 3)
                tx = max(2, min(self.size - 3, tx))
                ty = max(2, min(self.size - 3, ty))
            
            town_id = self._next_id("town")
            self.objects[town_id] = {
                "l": 0,
                "options": {
                    "formations": "random",
                    "owner": player_color,
                },
                "subtype": random.choice(["castle", "rampart", "tower", 
                                          "inferno", "necropolis", "dungeon",
                                          "stronghold", "fortress", "conflux"]),
                "template": {
                    "animation": "",
                    "mask": ["VVVVV", "VVAVV", "VVVVV"],
                    "visitableFrom": ["+++++", "++-++", "+++++"]
                },
                "type": "town",
                "x": tx,
                "y": ty
            }
            town_objs.append((tx, ty))
            
            # Clear area around town (grass)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    px, py = tx + dx, ty + dy
                    if 0 <= px < self.size and 0 <= py < self.size:
                        self.terrain[py][px] = random.choice(GRASS_TILES)
        
        # Starting hero
        hero_types = {
            "red": ["core:piquedram", "core:orrin", "core:valeska", "core:edric"],
            "blue": ["core:iona", "core:adela", "core:caitlin", "core:inham"],
        }
        hero_type = random.choice(hero_types.get(player_color, hero_types["red"]))
        
        hero_id = self._next_id("hero")
        self.objects[hero_id] = {
            "l": 0,
            "options": {
                "army": [
                    {}, {}, {},
                    {"amount": random.randint(10, 30), "type": random.choice(MONSTERS_EASY)},
                    {}, {}, {}
                ],
                "experience": 0,
                "formation": "wide",
                "owner": player_color,
                "portrait": hero_type,
                "type": hero_type,
            },
            "subtype": "core:alchemist",
            "template": {
                "animation": "AH04_.def",
                "editorAnimation": "AH04_E.def",
                "mask": ["VVV", "VAV"],
                "visitableFrom": ["+++", "+-+", "+++"]
            },
            "type": "hero",
            "x": hero_pos[0],
            "y": hero_pos[1],
        }
        
        return town_objs
    
    def add_resource(self, pos, res_type, amount):
        """Add a resource pile."""
        rid = self._next_id("resource")
        self.objects[rid] = {
            "l": 0,
            "options": {
                "amount": amount,
            },
            "subtype": res_type,
            "template": {
                "animation": "",
                "mask": ["V"],
                "visitableFrom": ["+", "-", "+"]
            },
            "type": "resource",
            "x": pos[0],
            "y": pos[1],
        }
    
    def add_monster(self, pos, monster_type, count):
        """Add a neutral monster stack."""
        mid = self._next_id("monster")
        self.objects[mid] = {
            "l": 0,
            "options": {
                "amount": count,
                "aggression": "aggressive" if random.random() < 0.3 else "guard",
                "formation": "wide",
            },
            "subtype": monster_type,
            "template": {
                "animation": "",
                "mask": ["VVV", "VAV", "VVV"],
                "visitableFrom": ["+++", "+-+", "+++"]
            },
            "type": "monster",
            "x": pos[0],
            "y": pos[1],
        }
    
    def add_mine(self, pos, mine_type, guard_monster, guard_count):
        """Add a mine guarded by monsters."""
        # Mine
        mid = self._next_id("mine")
        self.objects[mid] = {
            "l": 0,
            "options": {"owner": None},
            "subtype": mine_type,
            "template": {
                "animation": "",
                "mask": ["VVV", "VAV", "VVV"],
                "visitableFrom": ["+++", "+-+", "+++"]
            },
            "type": "mine",
            "x": pos[0],
            "y": pos[1],
        }
        # Guard monster adjacent to mine
        guard_pos = (pos[0] + 1, pos[1])
        if guard_pos[0] < self.size - 1:
            self.add_monster(guard_pos, guard_monster, guard_count)
    
    def add_artifact(self, pos, artifact_type):
        """Add an artifact."""
        aid = self._next_id("artifact")
        self.objects[aid] = {
            "l": 0,
            "options": {},
            "subtype": artifact_type,
            "template": {
                "animation": "",
                "mask": ["V"],
                "visitableFrom": ["+", "-", "+"]
            },
            "type": "artifact",
            "x": pos[0],
            "y": pos[1],
        }
    
    def add_garrison(self, pos, player_color):
        """Add a garrison (border guard) for a player."""
        gid = self._next_id("garrison")
        self.objects[gid] = {
            "l": 0,
            "options": {
                "owner": player_color,
                "formations": "random",
            },
            "subtype": "garrison",
            "template": {
                "animation": "",
                "mask": ["VVVVV", "VVAVV", "VVVVV"],
                "visitableFrom": ["+++++", "++-++", "+++++"]
            },
            "type": "garrison",
            "x": pos[0],
            "y": pos[1],
        }
    
    def populate_map(self):
        """Populate map with resources, mines, monsters, and artifacts."""
        
        # Player positions: red top-left area, blue bottom-right area
        red_town = (8, 8)
        blue_town = (self.size - 9, self.size - 9)
        red_hero = (9, 8)
        blue_hero = (self.size - 10, self.size - 9)
        
        # Add player setups
        self.add_player_setup("red", red_town, red_hero)
        self.add_player_setup("blue", blue_town, blue_hero)
        
        # Roads between player areas
        center = (self.size // 2, self.size // 2)
        self.generate_road(red_town, center)
        self.generate_road(blue_town, center)
        
        # Territory boundaries (middle of map)
        mid_x = self.size // 2
        for y in range(5, self.size - 5, 3):
            if random.random() < 0.3:
                pass  # garrison DISABLED (type unresolved)
        
        # Scatter resources in each player's territory
        for _ in range(int(self.size * self.resource_density)):
            # Random position, biased toward player territories
            if random.random() < 0.5:
                # Red territory (left half)
                x = random.randint(5, self.size // 2 - 5)
                y = random.randint(5, self.size - 6)
            else:
                # Blue territory (right half)
                x = random.randint(self.size // 2 + 5, self.size - 6)
                y = random.randint(5, self.size - 6)
            
            res_type = random.choice([
                ("core:gold", random.randint(500, 2000)),
                ("core:wood", random.randint(5, 15)),
                ("core:ore", random.randint(5, 15)),
                ("core:mercury", random.randint(3, 8)),
                ("core:sulfur", random.randint(3, 8)),
                ("core:crystal", random.randint(3, 8)),
                ("core:gems", random.randint(3, 8)),
            ])
            
            # Don't place on water or road
            tile = self.terrain[y][x]
            if "wt" in tile or "ro" in tile:
                continue
            
            self.add_resource((x, y), res_type[0], res_type[1])
        
        # Scatter neutral monsters (mini-creeps)
        for _ in range(self.size // 2):
            x = random.randint(3, self.size - 4)
            y = random.randint(3, self.size - 4)
            tile = self.terrain[y][x]
            if "wt" in tile or "ro" in tile:
                continue
            
            monster = random.choice(MONSTERS_EASY)
            count = random.randint(5, 30)
            self.add_monster((x, y), monster, count)
        
        # Place mines with guards in each territory
        mine_positions = []
        for i in range(4):  # 4 mines per side
            # Red side mines
            mx = random.randint(6, self.size // 2 - 8)
            my = random.randint(6, self.size - 7)
            mine_positions.append((mx, my, "red"))
            
            # Blue side mines
            mx = random.randint(self.size // 2 + 8, self.size - 9)
            my = random.randint(6, self.size - 7)
            mine_positions.append((mx, my, "blue"))
        
        for mx, my, side in mine_positions:
            mine_type, _ = random.choice(MINE_TYPES)
            guard = random.choice(MONSTERS_MEDIUM)
            guard_count = random.randint(20, 50)
            self.add_mine((mx, my), mine_type, guard, guard_count)
        
        # Scatter artifacts
        for _ in range(self.size // 3):
            ax = random.randint(5, self.size - 6)
            ay = random.randint(5, self.size - 6)
            tile = self.terrain[ay][ax]
            if "wt" in tile:
                continue
            
            artifact = random.choice(ARTIFACTS)
            self.add_artifact((ax, ay), artifact)
        
        # Add some hard monsters guarding good artifacts in the center
        for _ in range(5):
            cx = random.randint(self.size // 2 - 10, self.size // 2 + 10)
            cy = random.randint(self.size // 2 - 10, self.size // 2 + 10)
            guard = random.choice(MONSTERS_HARD)
            self.add_monster((cx, cy), guard, random.randint(5, 15))
            # Valuable artifact nearby
            self.add_artifact((cx + 1, cy), random.choice(ARTIFACTS[-6:]))
        
        # Add creature banks in remote areas
        for _ in range(4):
            bx = random.choice([random.randint(3, 10), random.randint(self.size - 11, self.size - 4)])
            by = random.randint(3, self.size - 4)
            self.add_monster((bx, by), random.choice(MONSTERS_HARD), random.randint(3, 10))
    
    def build_vmap(self) -> bytes:
        """Build complete vmap ZIP file."""
        header = {
            "allowedArtifacts": {"anyOf": ["core:pendantOfFreeWill"]},
            "defeatIconIndex": 3,
            "description": f"Strategic training map {self.size}x{self.size} seed={self.seed}",
            "difficulty": "NORMAL",
            "mapLevels": {
                "surface": {
                    "height": self.size,
                    "index": 0,
                    "width": self.size,
                }
            },
            "mods": None,
            "name": f"strategic-{self.size}",
            "players": {
                "blue": {
                    "canPlay": "PlayerOrAI",
                    "heroes": {
                        self._next_id("header_hero"): {"type": "core:iona"}
                    }
                },
                "red": {
                    "canPlay": "PlayerOrAI",
                    "heroes": {
                        self._next_id("header_hero"): {"type": "core:piquedram"}
                    }
                }
            },
            "victoryConditions": [
                "standardDefeat",
                "specialVictory",
            ],
            "triggeredEvents": {
                "specialVictory": {
                    "condition": ["allOf",
                        ["isHuman", {"value": 1}],
                        ["haveResources", {"type": 0, "value": 100}],
                    ],
                    "effect": {"type": "victory"},
                    "message": {
                        "exactStrings": None,
                        "localStrings": None,
                        "message": [2],
                        "numbers": None,
                        "stringsTextID": ["core.genrltxt.278"],
                    }
                },
                "standardDefeat": {
                    "condition": ["daysWithoutTown", {"value": 7}],
                    "effect": {"type": "defeat"},
                    "message": {
                        "exactStrings": None,
                        "localStrings": None,
                        "message": [2],
                        "numbers": None,
                        "stringsTextID": ["core.genrltxt.7"],
                    }
                }
            },
            "versionMajor": 1,
            "versionMinor": 1,
            "victoryIconIndex": 2,
        }
        
        # Build ZIP
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('header.json', json.dumps(header, separators=(',', ':')))
            zf.writestr('surface_terrain.json', json.dumps(self.terrain, separators=(',', ':')))
            zf.writestr('objects.json', json.dumps(self.objects, separators=(',', ':')))
        
        return buf.getvalue()


def main():
    parser = argparse.ArgumentParser(description="Generate strategic adventure vmap maps")
    parser.add_argument("--size", type=int, default=72, help="Map size (width=height)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output", type=str, required=True, help="Output .vmap path")
    parser.add_argument("--towns", type=int, default=1, help="Towns per player")
    parser.add_argument("--density", type=float, default=0.6, help="Resource density")
    args = parser.parse_args()
    
    gen = StrategicMapGenerator(
        size=args.size,
        seed=args.seed,
        towns_per_player=args.towns,
        resource_density=args.density,
    )
    
    gen.generate_terrain()
    gen.populate_map()
    
    vmap_data = gen.build_vmap()
    
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, 'wb') as f:
        f.write(vmap_data)
    
    size_kb = len(vmap_data) / 1024
    print(f"Generated: {args.output}")
    print(f"  Size: {args.size}x{args.size}, {size_kb:.0f}KB")
    print(f"  Objects: {len(gen.objects)}")
    print(f"  Seed: {gen.seed}")


if __name__ == "__main__":
    main()
