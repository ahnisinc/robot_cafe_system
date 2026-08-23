from pathlib import Path

from .yaml_loader import YAMLLoader


class RecipeManager:

    def __init__(
        self,
        recipe_directory,
    ):
        self.recipe_directory = Path(recipe_directory)

    def load_recipe(
        self,
        recipe_id,
    ):
        path = self.recipe_directory / f"{recipe_id}.yaml"
        data = YAMLLoader.load(path)

        return data["recipe"]

    def list_recipes(self):
        return sorted(path.stem for path in self.recipe_directory.glob("*.yaml"))
