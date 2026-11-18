from backend.config import (
    ROSBRIDGE_URL,
    COFFEE_PROGRESS_TOPIC,
    COFFEE_PROGRESS_TYPE,
)
from backend.rosbridge.rosbridge_client import ROSBridgeClient
from backend.services.dispatcher import Dispatcher

_client = None
_dispatcher = None


def init_rosbridge_client(socketio):

    global _client, _dispatcher

    _client = ROSBridgeClient(
        ROSBRIDGE_URL, socketio, COFFEE_PROGRESS_TOPIC, COFFEE_PROGRESS_TYPE
    )
    _dispatcher = Dispatcher(_client.call_service)
    _client.on_status = _dispatcher.on_status

    return _client


def get_rosbridge_client():

    if _client is None:
        raise RuntimeError("ROSBridge client is not initialized yet")

    return _client


def get_dispatcher():

    if _dispatcher is None:
        raise RuntimeError("Dispatcher is not initialized yet")

    return _dispatcher
