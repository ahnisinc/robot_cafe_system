import uuid

from backend.database.db import (
    save_order,
    get_order,
)

RECIPE_NAMES = {
    "americano": "Americano",
    "latte": "Latte",
    "cappuccino": "Cappuccino",
}


def create_order(recipe_id):

    if recipe_id not in RECIPE_NAMES:
        raise ValueError("Unknown recipe")

    order_id = "ORD-" + uuid.uuid4().hex[:8].upper()
    save_order(order_id, recipe_id, RECIPE_NAMES[recipe_id])

    return get_order(order_id)
