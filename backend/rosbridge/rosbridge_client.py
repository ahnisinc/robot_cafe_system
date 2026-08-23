import json
import threading
import time

import websocket


class ROSBridgeClient:

    def __init__(self, url, socketio, topic, message_type):

        self.url = url

        self.socketio     = socketio
        self.topic        = topic
        self.message_type = message_type
        self.ws           = None
        self.running      = False
        self.thread       = None

    def start(self):

        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):

        self.running = False

        if self.ws:

            try:
                self.ws.close()

            except Exception:
                pass

    def _run(self):

        while self.running:

            try:
                self._connect()

            except Exception as exc:
                print("ROSBridge connection error:", exc)

                time.sleep(3)

    def _connect(self):

        self.ws = websocket.create_connection(self.url, timeout=5)

        subscribe_message = {
            "op": "subscribe",
            "id": "coffee_progress",
            "topic": self.topic,
            "type": self.message_type,
            "throttle_rate": 100,
        }

        self.ws.send(json.dumps(subscribe_message))

        print("Connected to ROSBridge:", self.url)

        while self.running:

            raw = self.ws.recv()

            if not raw:
                break

            message = json.loads(raw)

            self._handle_message(message)

    def _handle_message(self, message):

        if message.get("op") != "publish":
            return

        if message.get("topic") != self.topic:
            return

        data = message.get("msg", {})

        self.socketio.emit("coffee_progress", data)
