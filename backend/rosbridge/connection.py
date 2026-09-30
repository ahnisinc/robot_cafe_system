from backend.config import (
    ROSBRIDGE_URL,
    COFFEE_PROGRESS_TOPIC,
    COFFEE_PROGRESS_TYPE,
)
from backend.rosbridge.rosbridge_client import ROSBridgeClient

_client = None


def init_rosbridge_client(socketio):

    global _client

    _client = ROSBridgeClient(
        ROSBRIDGE_URL, socketio, COFFEE_PROGRESS_TOPIC, COFFEE_PROGRESS_TYPE
    )

    return _client


def get_rosbridge_client():

    if _client is None:
        raise RuntimeError("ROSBridge client is not initialized yet")

    return _client
