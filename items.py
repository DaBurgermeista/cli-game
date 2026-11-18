import json
import random
from pathlib import Path

DATA_FILE = Path(__file__).parent / "items.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    ITEM_DATA = json.load(f)

def create_item(kind, x, y):

    template = ITEM_DATA[kind]
    return {
        "kind": kind,
        "name": template["name"],
        "char": template["char"],
        "color": template["color"],
        "value": template["value"],
        "type": template["type"],
        "x": x,
        "y": y,
    }

def get_item_at(items, x, y):
    for item in items:
        if item["x"] == x and item["y"] == y:
            return item
    return None

def spawn_random_items(room, biomes, walkable_tiles, count=12):
    items = []
    candidates = list(walkable_tiles)
    random.shuffle(candidates)

    for x, y in candidates:
        if len(items) >= count:
            break
    
        tile_biome = biomes[y][x]
        valid_kinds = [
            kind for kind, data in ITEM_DATA.items()
            if tile_biome in data.get("biomes", [])
        ]

        if not valid_kinds:
            continue

        weights = [ITEM_DATA[k].get("spawn_weight", 1) for k in valid_kinds]
        chosen_kind = random.choices(valid_kinds, weights=weights, k=1)[0]
        items.append(create_item(chosen_kind, x, y))
    
    return items
