import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

FRONTEND_DIR = BASE_DIR / "frontend"

DATABASE_DIR = BASE_DIR / "database"

DATABASE_PATH = DATABASE_DIR / "cafe.db"

ROSBRIDGE_URL = os.getenv("ROSBRIDGE_URL", "ws://localhost:9090")

COFFEE_PROGRESS_TOPIC = os.getenv("COFFEE_PROGRESS_TOPIC", "/coffee_process/status")

COFFEE_PROGRESS_TYPE = os.getenv(
    "COFFEE_PROGRESS_TYPE", "cafe_interfaces/msg/ProcessStatus"
)

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")

FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
