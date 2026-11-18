from flask import Blueprint, jsonify, request

from backend.services.order_service import create_order
from backend.database.db import get_order, get_process_status, get_queue_position
from backend.rosbridge.connection import get_dispatcher, get_rosbridge_client

api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/orders")
def create_new_order():
    data = request.get_json(silent=True) or {}

    recipe_id = data.get("recipe_id")

    if not recipe_id:
        return jsonify({"error": "recipe_id is required"}), 400

    try:
        order = create_order(recipe_id)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    get_dispatcher().kick()

    order = get_order(order["order_id"])
    order["queue_position"] = get_queue_position(order["order_id"])

    return jsonify(order), 201


@api.get("/orders/<order_id>")
def order_status(order_id):
    order = get_order(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order)


@api.get("/coffee-progress")
def coffee_progress():
    return jsonify(get_process_status())


CONTROL_COMMANDS = ("pause", "resume", "force_stop", "start")


@api.post("/control/<command>")
def control(command):

    if command not in CONTROL_COMMANDS:
        return jsonify({"error": f"unknown command: {command}"}), 404

    try:
        result = get_rosbridge_client().call_service(
            f"/coffee_process/{command}", {}, "std_srvs/srv/Trigger"
        )
    except Exception as exc:
        return jsonify({"error": f"rosbridge unavailable: {exc}"}), 503

    return jsonify(
        {"success": bool(result.get("success")), "message": result.get("message", "")}
    )
