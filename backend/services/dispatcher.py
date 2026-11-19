import threading

from backend.database import db

EXECUTE_SERVICE = "/coffee_process/execute_recipe"
EXECUTE_TYPE = "cafe_interfaces/srv/ExecuteRecipe"


class Dispatcher:
    """
    DB 대기열의 주문을 로봇이 IDLE일 때 한 잔씩 coffee_process로 보낸다.
    """

    def __init__(self, call_service):

        self.call_service = call_service
        self._lock = threading.Lock()
        self._last_state = ""

    def on_status(self, data):

        order_id = data.get("order_id", "")
        order_state = data.get("order_state", "")
        state = data.get("state", "")

        with self._lock:
            order = db.get_order(order_id) if order_id else None
            if order and order["status"] not in ("DONE", "FAILED"):
                if order_state in ("DONE", "FAILED"):
                    db.set_order_status(order_id, order_state)
                elif order_state == "RUNNING":
                    db.update_order_progress(
                        order_id,
                        "RUNNING",
                        data.get("progress", 0.0),
                        data.get("current_step", ""),
                    )

            running = db.get_running_order()
            if (
                running
                and running["order_id"] != order_id
                and state not in ("RUNNING", "PAUSED", "IDLE")
            ):
                db.set_order_status(running["order_id"], "FAILED")

            self._last_state = state
            self._try_dispatch()

    def kick(self):

        with self._lock:
            self._try_dispatch()

    def _try_dispatch(self):

        if self._last_state != "IDLE" or db.get_running_order():
            return

        order = db.get_next_queued_order()
        if not order:
            return

        try:
            result = self.call_service(
                EXECUTE_SERVICE,
                {"recipe_id": order["recipe_id"], "order_id": order["order_id"]},
                EXECUTE_TYPE,
            )
        except Exception as exc:
            print("Dispatch failed:", exc)
            return

        if result.get("accepted"):
            db.set_order_status(order["order_id"], "RUNNING")
            self._last_state = "RUNNING"
