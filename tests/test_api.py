from backend.app import (
    create_app
)


def test_health():

    app, socketio = (
        create_app()
    )

    client = app.test_client()

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    assert (
        response.json["status"]
        == "ok"
    )


import pytest

import backend.database.db as db
import backend.routes.api as api_module


class FakeClient:

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def call_service(self, service, args=None, service_type=None, timeout=5):
        self.calls.append((service, args, service_type))
        if self.error:
            raise self.error
        return {"success": True, "message": "paused"}


class FakeDispatcher:

    def __init__(self):
        self.kicks = 0

    def kick(self):
        self.kicks += 1


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "t.db")
    app, _ = create_app()
    return app.test_client()


def test_control_pause_calls_service(client, monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api_module, "get_rosbridge_client", lambda: fake)
    response = client.post("/api/control/pause")
    assert response.status_code == 200
    assert response.json == {"success": True, "message": "paused"}
    assert fake.calls == [("/coffee_process/pause", {}, "std_srvs/srv/Trigger")]


def test_control_unknown_cmd_404(client, monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(api_module, "get_rosbridge_client", lambda: fake)
    assert client.post("/api/control/reboot").status_code == 404
    assert fake.calls == []


def test_control_rosbridge_down_503(client, monkeypatch):
    fake = FakeClient(error=ConnectionRefusedError("refused"))
    monkeypatch.setattr(api_module, "get_rosbridge_client", lambda: fake)
    response = client.post("/api/control/force_stop")
    assert response.status_code == 503
    assert "error" in response.json


def test_order_returns_queue_position_and_kicks(client, monkeypatch):
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(api_module, "get_dispatcher", lambda: dispatcher)
    response = client.post("/api/orders", json={"recipe_id": "latte"})
    assert response.status_code == 201
    assert response.json["queue_position"] == 1
    assert dispatcher.kicks == 1
