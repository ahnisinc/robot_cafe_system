from flask import Flask, send_from_directory

from flask_socketio import SocketIO
from backend.config import FRONTEND_DIR, FLASK_HOST, FLASK_PORT
from backend.database.db import init_database
from backend.routes.api import api
from backend.routes.websocket import register_socket_events
from backend.rosbridge.coffee_progress_bridge import CoffeeProgressBridge


def create_app():
    # Flask 앱 생성
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = "robot-cafe-secret"

    # Socket.IO 설정
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # 데이터베이스 초기화
    init_database()

    # REST API 등록
    app.register_blueprint(api)

    # 메인 페이지 반환
    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    # 프론트엔드 정적 파일 반환
    @app.get("/<path:path>")
    def frontend_files(path):
        return send_from_directory(FRONTEND_DIR, path)

    # WebSocket 이벤트 등록
    register_socket_events(socketio)

    # ROS2 ↔ Web 서버 브리지 생성 및 시작
    bridge = CoffeeProgressBridge(socketio)
    bridge.start()

    # Flask와 Socket.IO 객체 반환
    return app, socketio


if __name__ == "__main__":

    # Flask 앱 생성
    application, socketio = create_app()

    # 서버 실행
    socketio.run(
        application, host=FLASK_HOST, port=FLASK_PORT, allow_unsafe_werkzeug=True
    )
