from flask_socketio import emit


def register_socket_events(socketio):

    @socketio.on("connect")
    def on_connect():
        emit("server_status", {"connected": True})

    @socketio.on("disconnect")
    def on_disconnect():
        print("Browser disconnected")
