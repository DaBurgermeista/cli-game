import json
import random
from pathlib import Path

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
        "x": x,
        "y": y,
    }

def create_player(x, y):
    return {
        "kind": "player",
        "name": "Adventurer",
        "char": "@",
        "color": 1,
        "hp": 3,
        "max_hp": 5,
        "base_attack": 1,
        "has_key": False,
        "inventory": [],
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
