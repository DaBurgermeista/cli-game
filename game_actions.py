"""Turn-based rules shared by every world profile and front end.

The curses loop translates keys into ``GameAction`` values. ``apply_action``
updates the game state and reports discoveries/outcomes without drawing UI.
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto

from entities import attack_entity, get_entity_at, update_entities
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
from tiles import FLOOR, TILE_DATA


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
                if target_entity["hp"] <= 0:
                    dead_x, dead_y = target_entity["x"], target_entity["y"]
                    game.entities.remove(target_entity)
                    if random.random() < ENEMY_LOOT_DROP_CHANCE:
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
        _add_message(game, "You found a boss key.", message_limit)
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

    if props.get("exit"):
        result.outcome = "victory"

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
