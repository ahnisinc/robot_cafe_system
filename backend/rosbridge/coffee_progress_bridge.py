from backend.rosbridge.rosbridge_client import ROSBridgeClient

from backend.config import (
    ROSBRIDGE_URL,
    COFFEE_PROGRESS_TOPIC,
    COFFEE_PROGRESS_TYPE,
)


class CoffeeProgressBridge:

    def __init__(self, socketio):
        self.client = ROSBridgeClient(
            ROSBRIDGE_URL, socketio, COFFEE_PROGRESS_TOPIC, COFFEE_PROGRESS_TYPE
        )

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()
