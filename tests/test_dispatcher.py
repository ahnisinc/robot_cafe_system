import pytest

import backend.database.db as db
from backend.services.dispatcher import Dispatcher

EXECUTE = "/coffee_process/execute_recipe"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "t.db")
    db.init_database()

    calls = []
    reply = {"value": {"accepted": True, "message": ""}}

    def call_service(service, args, service_type):
        calls.append((service, args))
        if isinstance(reply["value"], Exception):
            raise reply["value"]
        return reply["value"]

    return Dispatcher(call_service), calls, reply


def status(state, order_id="", order_state="", progress=0.0, current_step=""):
    return {
        "state": state,
        "order_id": order_id,
        "order_state": order_state,
        "progress": progress,
        "current_step": current_step,
    }


def test_dispatch_when_idle(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    d.on_status(status("IDLE"))
    assert calls == [(EXECUTE, {"recipe_id": "latte", "order_id": "A"})]
    assert db.get_order("A")["status"] == "RUNNING"


@pytest.mark.parametrize("state", ["RUNNING", "PAUSED", "STOPPED", "RESETTING", "HOMED"])
def test_no_dispatch_when_not_idle(env, state):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    d.on_status(status(state))
    assert calls == []
    assert db.get_order("A")["status"] == "QUEUED"


def test_fifo_order(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.save_order("B", "americano", "Americano")
    d.on_status(status("IDLE"))
    assert [c[1]["order_id"] for c in calls] == ["A"]


def test_no_double_dispatch(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.save_order("B", "latte", "Latte")
    d.on_status(status("IDLE"))
    d.on_status(status("IDLE"))
    d.kick()
    assert len(calls) == 1


def test_kick_dispatches_new_order_when_idle(env):
    d, calls, _ = env
    d.on_status(status("IDLE"))
    db.save_order("A", "latte", "Latte")
    d.kick()
    assert [c[1]["order_id"] for c in calls] == ["A"]


def test_running_progress_updates_order(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    d.on_status(status("IDLE"))
    d.on_status(status("RUNNING", "A", "RUNNING", 42.0, "Milk Station"))
    order = db.get_order("A")
    assert (order["status"], order["progress"], order["current_step"]) == (
        "RUNNING", 42.0, "Milk Station")


def test_done_detected_from_idle_message(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.save_order("B", "latte", "Latte")
    d.on_status(status("IDLE"))
    d.on_status(status("IDLE", "A", "DONE", 100.0))
    assert db.get_order("A")["status"] == "DONE"
    assert [c[1]["order_id"] for c in calls] == ["A", "B"]


def test_failed_order_marked(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.save_order("B", "latte", "Latte")
    d.on_status(status("IDLE"))
    d.on_status(status("STOPPED", "A", "FAILED"))
    assert db.get_order("A")["status"] == "FAILED"
    assert len(calls) == 1
    assert db.get_order("B")["status"] == "QUEUED"


def test_orphan_running_order_failed(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.set_order_status("A", "RUNNING")
    d.on_status(status("STOPPED"))
    assert db.get_order("A")["status"] == "FAILED"


def test_running_order_not_orphaned_while_paused(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.set_order_status("A", "RUNNING")
    d.on_status(status("PAUSED", "A", "RUNNING"))
    assert db.get_order("A")["status"] == "RUNNING"


def test_rejected_dispatch_keeps_queued(env):
    d, calls, reply = env
    reply["value"] = {"accepted": False, "message": "busy"}
    db.save_order("A", "latte", "Latte")
    d.on_status(status("IDLE"))
    assert db.get_order("A")["status"] == "QUEUED"


def test_service_error_keeps_queued(env):
    d, calls, reply = env
    reply["value"] = ConnectionError("rosbridge down")
    db.save_order("A", "latte", "Latte")
    d.on_status(status("IDLE"))
    assert db.get_order("A")["status"] == "QUEUED"


def test_queue_position(env):
    d, calls, _ = env
    for order_id in ("A", "B", "C"):
        db.save_order(order_id, "latte", "Latte")
    db.set_order_status("A", "RUNNING")
    assert db.get_queue_position("B") == 1
    assert db.get_queue_position("C") == 2
    assert db.get_queue_position("A") == 0


def test_late_running_message_does_not_revive_finished_order(env):
    d, calls, _ = env
    db.save_order("A", "latte", "Latte")
    db.save_order("B", "latte", "Latte")
    d.on_status(status("IDLE"))
    d.on_status(status("IDLE", "A", "DONE", 100.0))
    d.on_status(status("RUNNING", "A", "RUNNING", 90.0))
    assert db.get_order("A")["status"] == "DONE"
    d.on_status(status("IDLE", "B", "DONE", 100.0))
    assert db.get_order("B")["status"] == "DONE"
