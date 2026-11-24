import json
import random
from pathlib import Path

from tiles import TILE_DATA
from vision import has_line_of_sight

DATA_FILE = Path(__file__).parent / "entities.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    ENTITY_DATA = json.load(f)

def create_entity(kind, x, y):

    template = ENTITY_DATA[kind]
    return {
        "kind": kind,
        "name": template["name"],
        "char": template["char"],
        "color": template["color"],
        "hp": template["hp"],
        "attack": template.get("attack", 1),
        "hostile": template["hostile"],
        "boss": template.get("boss", False),
        "boss_tier": template.get("boss_tier"),
        "leash": None,
        "x": x,
        "y": y,
    }

def create_player(x, y):
    return {
        "kind": "player",
        "name": "Carl",
        "char": "@",
        "color": 1,
        "hp": 5,
        "max_hp": 10,
        "base_attack": 1,
        "stats": {
            "str": 1,
            "dex": 1,
            "con": 1,
            "int": 1,
            "wis": 1,
            "luck": 1,
        },
        "has_key": False,
        "inventory": [],
        "money": 0,
        "equipped_weapon": None,
        "x": x,
        "y": y,
    }

def get_entity_at(entities, x, y):

    for entity in entities:
        if entity["x"] == x and entity["y"] == y:
            return entity
    return None

def spawn_random_entities(world_map, biomes, walkable_tiles, count=15):
    entities = []
    candidates = list(walkable_tiles)
    random.shuffle(candidates)

    for x, y in candidates:
        if len(entities) >= count:
            break
        
        tile_biome = biomes[y][x]

        valid_kinds = [
            kind for kind, data in ENTITY_DATA.items()
            if tile_biome in data.get("biomes", [])
            and not data.get("boss", False)
        ]

        if not valid_kinds:
            continue

        weights = [ENTITY_DATA[k].get("spawn_weight", 1) for k in valid_kinds]
        chosen_kind = random.choices(valid_kinds, weights=weights, k=1)[0]

        entities.append(create_entity(chosen_kind, x, y))
    
    return entities

def attack_entity(attacker, target):
    damage = attacker.get("base_attack", attacker.get("attack", 1))

    weapon = attacker.get("equipped_weapon")
    if weapon is not None:
        damage += weapon.get("value", 0)

    target["hp"] = max(0, target["hp"] - damage)

    if target["hp"] <= 0:
        return f"{attacker['name']} hits {target['name']} for {damage} damage and defeats it!"
    return f"{attacker['name']} hits {target['name']} for {damage}! ({target['hp']} HP left.)"

def _in_rect(x, y, rect):
    x0, y0, x1, y1 = rect
    return x0 <= x <= x1 and y0 <= y <= y1


def update_entities(entities, room, player, aggro_range=7):
    turn_message = []
    px, py = player["x"], player["y"]
    occupied = {(e["x"], e["y"]) for e in entities}

    for entity in entities:
        if entity["hp"] <= 0:
            continue

        ex, ey = entity["x"], entity["y"]
        distance = abs(px - ex) + abs(py - ey)
        leash = entity.get("leash")
        player_in_leash = leash is None or _in_rect(px, py, leash)

        if (
            entity.get("hostile", False)
            and distance <= aggro_range
            and has_line_of_sight(room, ex, ey, px, py)
            and player_in_leash
        ):
            if distance == 1:
                turn_message.append(attack_entity(entity, player))
                continue

            dx = 0 if px == ex else (1 if px > ex else -1)
            dy = 0 if py == ey else (1 if py > ey else - 1)

            candidates = []
            if dx != 0:
                candidates.append((ex + dx, ey))
            if dy != 0:
                candidates.append((ex, ey + dy))
            random.shuffle(candidates)

            for nx, ny in candidates:
                if not (0 <= ny < len(room) and 0 <= nx < len(room[0])):
                    continue
                if (nx, ny) == (px, py) or (nx, ny) in occupied:
                    continue
                if leash is not None and not _in_rect(nx, ny, leash):
                    continue
                if TILE_DATA.get(room[ny][nx], {}).get("walkable", False):
                    occupied.remove((ex, ey))
                    entity["x"], entity["y"] = nx, ny
                    occupied.add((nx, ny))
                    break

        elif random.random() < 0.4:
            dx, dy = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
            nx, ny = ex + dx, ey + dy
            if not (0 <= ny < len(room) and 0 <= nx < len(room[0])):
                continue
            if leash is not None and not _in_rect(nx, ny, leash):
                continue
            if (nx, ny) != (px, py) and (nx, ny) not in occupied:
                if TILE_DATA.get(room[ny][nx], {}).get("walkable", False):
                    occupied.remove((ex, ey))
                    entity["x"], entity["y"] = nx, ny
                    occupied.add((nx, ny))
    
    return turn_message
