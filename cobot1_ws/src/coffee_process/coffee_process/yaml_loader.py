from pathlib import Path

import yaml


class YAMLLoader:

    @staticmethod
    def load(path):

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(str(path))

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return yaml.safe_load(file)
