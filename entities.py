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
        "hostile": template["hostile"],
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