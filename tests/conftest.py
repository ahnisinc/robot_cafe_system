import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for package in ("robot_driver", "robot_control", "coffee_process"):
    sys.path.insert(0, str(ROOT / "cobot1_ws" / "src" / package))
