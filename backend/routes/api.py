from flask import Blueprint, jsonify, request

from backend.services.order_service import create_order
from backend.database.db import get_order, get_process_status

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

        return jsonify(order), 201

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@api.get("/orders/<order_id>")
def order_status(order_id):
    order = get_order(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order)


@api.get("/coffee-progress")
def coffee_progress():
    return jsonify(get_process_status())
