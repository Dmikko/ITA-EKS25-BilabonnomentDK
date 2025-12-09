import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from database import (
    init_db,
    create_reservation,
    list_reservations,
    get_reservation_by_id,
    update_reservation_status,
)

app = Flask(__name__)

FLEET_BASE_URL = os.getenv("FLEET_BASE_URL", "http://fleet_service:5006")


@app.before_request
def setup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "reservation_service"}


@app.get("/reservations")
def get_reservations():
    status = request.args.get("status")
    rows = list_reservations(status=status)
    return jsonify([dict(r) for r in rows])


@app.get("/reservations/<int:reservation_id>")
def get_reservation(reservation_id):
    row = get_reservation_by_id(reservation_id)
    if row is None:
        return jsonify({"error": "reservation not found"}), 404
    return jsonify(dict(row))


@app.post("/reservations")
def create_reservation_endpoint():
    data = request.get_json() or {}

    required = ["lease_id", "pickup_date", "vehicle_id"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # lease_id og vehicle_id som int
    try:
        lease_id = int(data["lease_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "lease_id must be an integer"}), 400

    try:
        vehicle_id = int(data["vehicle_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "vehicle_id must be an integer"}), 400

    pickup_date = data["pickup_date"]

    # --- slå lokation op i FleetService ---
    pickup_location = "Ukendt"
    try:
        resp = requests.get(f"{FLEET_BASE_URL}/vehicles/{vehicle_id}", timeout=5)
        if resp.status_code == 200:
            v = resp.json()
            pickup_location = v.get("delivery_location") or "Ukendt"
        else:
            print(f"[reservation_service] Fleet lookup failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"[reservation_service] Fleet lookup error: {e}")

    # Gem reservation – pickup_location kommer nu fra Fleet
    try:
        reservation_id = create_reservation(
            {
                "lease_id": lease_id,
                "vehicle_id": vehicle_id,
                "pickup_date": pickup_date,
                "pickup_location": pickup_location,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    row = get_reservation_by_id(reservation_id)
    return jsonify(dict(row)), 201


@app.patch("/reservations/<int:reservation_id>/status")
def change_reservation_status(reservation_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    row = get_reservation_by_id(reservation_id)
    if row is None:
        return jsonify({"error": "reservation not found"}), 404

    update_reservation_status(reservation_id, new_status)
    row = get_reservation_by_id(reservation_id)
    return jsonify(dict(row)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
