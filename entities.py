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

def spawn_random_entities(world_map, walkable_tiles, count=15):
    entities = []
    kinds = list(ENTITY_DATA.keys())
    weights = [ENTITY_DATA[k].get("spawn_weight", 1) for k in kinds]

    chosen_tiles = random.sample(walkable_tiles, min(count, len(walkable_tiles)))

    for x, y in chosen_tiles:
        kind = random.choices(kinds, weights=weights, k=1)[0]
        entities.append(create_entity(kind, x, y))
    
    return entities