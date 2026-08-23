from pathlib import Path

import yaml


def test_americano_recipe():

    path = Path(
        "cobot1_ws/src/coffee_process/"
        "config/recipes/americano.yaml"
    )

    data = yaml.safe_load(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert "recipe" in data

    recipe = data["recipe"]

    assert recipe["id"] == "americano"

    assert len(
        recipe["steps"]
    ) > 0
