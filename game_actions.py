"""Turn-based rules shared by every world profile and front end.

The curses loop translates keys into ``GameAction`` values. ``apply_action``
updates the game state and reports discoveries/outcomes without drawing UI.
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto

from entities import attack_entity, get_entity_at, update_entities, weapon_skill
from items import (
    ENEMY_LOOT_DROP_CHANCE,
    ENEMY_LOOT_DROP_WEIGHTS,
    add_to_inventory,
    create_item,
    drop_item,
    get_item_at,
    open_loot_box,
    use_item,
)
from tiles import CAMPFIRE, FLOOR, TILE_DATA


class ActionType(Enum):
    """Kinds of player input that can affect the game world."""

    MOVE = auto()
    PICK_UP = auto()
    USE_ITEM = auto()
    DROP_ITEM = auto()
    WAIT = auto()


@dataclass(frozen=True)
class GameAction:
    """A single requested action; direction and item index are kind-specific."""

    type: ActionType
    dx: int = 0  # Horizontal movement: -1 left, +1 right.
    dy: int = 0  # Vertical movement: -1 up, +1 down.
    item_index: int | None = None  # Inventory slot for USE_ITEM / DROP_ITEM.


@dataclass
class ActionResult:
    """Information the interface needs after an action is resolved."""

    consumed_turn: bool = False
    outcome: str | None = None
    discoveries: list = field(default_factory=list)  # (title, text) pairs.


# What a defeated boss guarantees on the floor, by tier.
BOSS_LOOT = {
    "floor": ["loot_box_silver"],
    "borough": ["loot_box_gold"],
    "district": ["loot_box_gold"],
    "city": ["loot_box_gold", "loot_box_gold"],
}


def _living_boss(game):
    """The floor's boss, if it is still alive on the floor."""
    boss = getattr(game, "boss", None)
    if boss is None or boss.get("hp", 0) <= 0:
        return None
    if boss not in game.entities:
        return None
    return boss


# XP needed to go from level n to n+1: 100 * n.
XP_PER_LEVEL = 100


def _train_skill(player):
    """One hit trains the skill matching the equipped weapon.

    Returns a level-up message, or None when the skill just gains XP.
    """
    skills = player.get("skills")
    if not skills:
        return None
    style = weapon_skill(player)
    skill = skills.setdefault(style, {"level": 1, "xp": 0})
    skill["xp"] += 1
    needed = 5 * skill["level"]
    if skill["xp"] >= needed:
        skill["xp"] -= needed
        skill["level"] += 1
        return f"Your {style.capitalize()} skill rises to level {skill['level']}!"
    return None


def _award_xp(game, amount, message_limit):
    """Grant XP and resolve level-ups. Returns level-up discoveries.

    Each level: +2 max HP, heal 2 HP, and +1 base attack every 2nd level.
    """
    player = game.player
    discoveries = []
    if amount <= 0:
        return discoveries
    player["xp"] = player.get("xp", 0) + amount
    _add_message(game, f"You gain {amount} XP.", message_limit)
    while player["xp"] >= XP_PER_LEVEL * player.get("level", 1):
        player["xp"] -= XP_PER_LEVEL * player["level"]
        player["level"] += 1
        player["max_hp"] += 2
        player["hp"] = min(player["max_hp"], player["hp"] + 2)
        rewards = "Max HP +2, healed 2 HP."
        if player["level"] % 2 == 0:
            player["base_attack"] += 1
            rewards += " Attack +1."
        discoveries.append(
            (
                "Level Up!",
                "The Borant AI announces: "
                f"\"Level {player['level']}, Crawler! {rewards} "
                "The viewers love a level-up.\"",
            )
        )
    return discoveries


def _add_message(game, text, message_limit):
    """Append a non-empty message and keep only the newest log entries."""
    if not text:
        return
    game.messages.append(text)
    del game.messages[:-message_limit]


def apply_action(game, action, message_limit=4):
    """Apply a player action, then advance hazards and enemies if it took a turn.

    Invalid movement still costs a turn, as does trying to pick up nothing.
    Browsing/cancelling an item use does not. After the action itself, the
    player's current tile is processed, then living entities take their turn.
    Terminal outcomes stop that final entity update.
    """
    player = game.player
    result = ActionResult()

    if action.type is ActionType.MOVE:
        result.consumed_turn = True
        next_x = player["x"] + action.dx
        next_y = player["y"] + action.dy

        if not (0 <= next_y < len(game.grid) and 0 <= next_x < len(game.grid[0])):
            _add_message(game, "You cannot go that way.", message_limit)
        else:
            target_tile = game.grid[next_y][next_x]
            target_props = TILE_DATA[target_tile]
            target_entity = get_entity_at(game.entities, next_x, next_y)

            # Bumping an entity is an attack; the player stays in place.
            if target_entity is not None:
                _add_message(
                    game,
                    attack_entity(player, target_entity),
                    message_limit,
                )
                skill_message = _train_skill(player)
                if skill_message is not None:
                    _add_message(game, skill_message, message_limit)
                if target_entity["hp"] <= 0:
                    dead_x, dead_y = target_entity["x"], target_entity["y"]
                    game.entities.remove(target_entity)
                    if target_entity.get("boss", False):
                        # Bosses always pay out, by tier.
                        tier = target_entity.get("boss_tier", "floor")
                        for box_kind in BOSS_LOOT.get(tier, ["loot_box_silver"]):
                            game.items.append(
                                create_item(box_kind, dead_x, dead_y)
                            )
                        _add_message(
                            game,
                            f"The {target_entity['name']} drops a loot box!",
                            message_limit,
                        )
                    elif target_entity.get("kind") != "training_dummy" and (
                        random.random() < ENEMY_LOOT_DROP_CHANCE
                    ):
                        box_kind = random.choices(
                            list(ENEMY_LOOT_DROP_WEIGHTS),
                            weights=list(ENEMY_LOOT_DROP_WEIGHTS.values()),
                            k=1,
                        )[0]
                        game.items.append(create_item(box_kind, dead_x, dead_y))
                        _add_message(
                            game,
                            f"The {target_entity['name']} drops a loot box!",
                            message_limit,
                        )
                    for discovery in _award_xp(
                        game, target_entity.get("xp", 0), message_limit
                    ):
                        result.discoveries.append(discovery)
            # The stairwell is the boss's to guard: it stays blocked
            # while the boss lives, even though the tile is walkable.
            elif target_props.get("exit") and _living_boss(game) is not None:
                boss = _living_boss(game)
                _add_message(
                    game,
                    f"The {boss['name']} blocks the stairwell! "
                    "Defeat it first.",
                    message_limit,
                )
            # A tile can either be ordinarily walkable or require a key.
            elif target_props["walkable"] or (
                target_props.get("needs_key", False) and player["has_key"]
            ):
                player["x"], player["y"] = next_x, next_y
                if target_props.get("needs_key"):
                    game.grid[next_y][next_x] = FLOOR
                    _add_message(game, "You unlocked the dungeon door!", message_limit)
                else:
                    _add_message(
                        game,
                        target_props.get("enter_msg", ""),
                        message_limit,
                    )
            else:
                _add_message(
                    game,
                    target_props.get("bump_msg", "Something blocks your way."),
                    message_limit,
                )

    elif action.type is ActionType.PICK_UP:
        # Pickup is explicit: standing on an item only announces it.
        item = get_item_at(game.items, player["x"], player["y"])
        if item is None:
            result.consumed_turn = True
            _add_message(game, "There is nothing here to pick up.", message_limit)
        elif add_to_inventory(player, item):
            result.consumed_turn = True
            game.items.remove(item)
            _add_message(game, f"You pick up the {item['name']}.", message_limit)
        else:
            _add_message(
                game,
                "Your pack is full. Drop something first.",
                message_limit,
            )

    elif action.type is ActionType.USE_ITEM:
        # Loot boxes open through the action layer: opening needs the game
        # state so rolled items can spill onto the floor when the pack is full.
        inventory = player["inventory"]
        if (
            action.item_index is not None
            and 0 <= action.item_index < len(inventory)
            and inventory[action.item_index]["type"] == "loot_box"
        ):
            result.consumed_turn = True
            messages, discovery = open_loot_box(game, player, action.item_index)
            for message in messages:
                _add_message(game, message, message_limit)
            if discovery is not None:
                result.discoveries.append(discovery)
        else:
            # use_item returns (message, consumed_turn); a wasted use, like
            # drinking a potion at full health, costs no turn.
            message, consumed = use_item(player, action.item_index)
            if message is not None:
                result.consumed_turn = consumed
                _add_message(game, message, message_limit)

    elif action.type is ActionType.DROP_ITEM:
        # Dropping is pack management, not a world action: it costs no turn.
        dropped, message = drop_item(player, action.item_index)
        if dropped is not None:
            dropped["x"], dropped["y"] = player["x"], player["y"]
            game.items.append(dropped)
        _add_message(game, message, message_limit)

    elif action.type is ActionType.WAIT:
        result.consumed_turn = True

    else:
        raise ValueError(f"Unsupported action type: {action.type!r}")

    if not result.consumed_turn:
        # No turn means no hazards or enemy movement either.
        game.outcome = result.outcome
        return result

    # Apply effects where the player ended the action. This also preserves
    # the current behavior of repeated hazard damage while standing on a trap.
    current_tile = game.grid[player["y"]][player["x"]]
    props = TILE_DATA[current_tile]
    ground_item = get_item_at(game.items, player["x"], player["y"])
    if ground_item is not None:
        _add_message(game, f"You see a {ground_item['name']} here.", message_limit)

    if props.get("pickup") == "key":
        _add_message(game, "You found a key.", message_limit)
        player["has_key"] = True
        game.grid[player["y"]][player["x"]] = FLOOR
        props = TILE_DATA[FLOOR]

    if "damage" in props:
        player["hp"] = max(0, player["hp"] - props["damage"])
        _add_message(
            game,
            f"Ouch! You took {props['damage']} damage from {props['name']}!",
            message_limit,
        )
        if player["hp"] <= 0:
            result.outcome = "defeat"

    if current_tile == CAMPFIRE and not getattr(game, "rested", False):
        if player["hp"] < player["max_hp"]:
            healed = min(3, player["max_hp"] - player["hp"])
            player["hp"] += healed
            game.rested = True
            _add_message(
                game,
                f"You rest by the fire and recover {healed} HP.",
                message_limit,
            )

    if props.get("exit") and _living_boss(game) is None:
        result.outcome = "victory"

    boss = _living_boss(game)
    boss_room = getattr(game, "boss_room", None)
    if (
        boss is not None
        and not getattr(game, "boss_announced", False)
        and boss_room is not None
        and boss_room[0] <= player["x"] < boss_room[0] + boss_room[2]
        and boss_room[1] <= player["y"] < boss_room[1] + boss_room[3]
    ):
        game.boss_announced = True
        result.discoveries.append(
            (
                boss["name"],
                "The Borant AI announces: \"Crawler, you have entered "
                f"the boss room. {boss['name']} guards the stairwell. "
                "Defeat the boss to descend!\"",
            )
        )

    if "text" in props:
        result.discoveries.append((props["name"], props["text"]))

    if result.outcome is None:
        # Enemies act only after a surviving player turn that did not win.
        for message in update_entities(game.entities, game.grid, player):
            _add_message(game, message, message_limit)
        if player["hp"] <= 0:
            result.outcome = "defeat"

    game.outcome = result.outcome
    return result
