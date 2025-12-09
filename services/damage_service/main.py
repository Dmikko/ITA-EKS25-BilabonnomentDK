import os
import requests
from flask import Flask, request, jsonify
from database import (
    init_db,
    create_damage,
    list_damages,
    get_damage_by_id,
    update_damage_status,
)

app = Flask(__name__)

# Fleet-service base URL (overstyres i Docker via FLEET_BASE_URL)
FLEET_BASE_URL = os.getenv("FLEET_BASE_URL", "http://localhost:5006")

def call_fleet_update_status(vehicle_id: int, status: str, lease_id: int | None = None):
    """
    Kalder FleetService for at opdatere status på en bil.
    Bruges når en skade registreres, så bilen sættes til fx DAMAGED.
    Returnerer (ok: bool, error_dict | None)
    """
    try:
        resp = requests.put(
            f"{FLEET_BASE_URL}/vehicles/{vehicle_id}/status",
            json={"status": status, "lease_id": lease_id},
            timeout=5,
        )
    except Exception as e:
        return False, {"error": "fleet_service unavailable", "details": str(e)}

    if resp.status_code not in (200, 204):
        try:
            return False, resp.json()
        except Exception:
            return False, {"error": f"Invalid response from fleet_service (status {resp.status_code})"}

    return True, None



@app.before_request
def setup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "damage_service"}


@app.get("/damages")
def get_damages():
    status = request.args.get("status")
    lease_id = request.args.get("lease_id")

    lease_id_int = None
    if lease_id is not None:
        try:
            lease_id_int = int(lease_id)
        except ValueError:
            return jsonify({"error": "lease_id must be an integer"}), 400

    rows = list_damages(status=status, lease_id=lease_id_int)
    damages = [dict(row) for row in rows]
    return jsonify(damages)


@app.get("/damages/<int:damage_id>")
def get_damage(damage_id):
    row = get_damage_by_id(damage_id)
    if row is None:
        return jsonify({"error": "damage not found"}), 404
    return jsonify(dict(row))


@app.post("/damages")
def create_damage_endpoint():
    data = request.get_json() or {}

    required = ["lease_id", "category", "description", "estimated_cost"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # lease_id som int
    try:
        lease_id = int(data["lease_id"])
        data["lease_id"] = lease_id
    except (ValueError, TypeError):
        return jsonify({"error": "lease_id must be an integer"}), 400

    # estimated_cost som float
    try:
        data["estimated_cost"] = float(data["estimated_cost"])
    except (ValueError, TypeError):
        return jsonify({"error": "estimated_cost must be a number"}), 400

    # ----------------------------------------------------
    # 🚀 AUTOMATISK VEHICLE LOOKUP FRA LEASE SERVICE
    # ----------------------------------------------------
    VEHICLE_LOOKUP_URL = os.getenv("LEASE_BASE_URL", "http://lease_service:5002")

    vehicle_id = None
    try:
        lease_resp = requests.get(f"{VEHICLE_LOOKUP_URL}/leases/{lease_id}", timeout=5)
        if lease_resp.status_code == 200:
            lease_data = lease_resp.json()
            vehicle_id = lease_data.get("vehicle_id")
    except Exception as e:
        print(f"[damage_service] vehicle lookup failed: {e}")

    data["vehicle_id"] = vehicle_id

    # ----------------------------------------------------
    # Gem skade
    # ----------------------------------------------------
    try:
        damage_id = create_damage(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # ----------------------------------------------------
    # Hvis vehicle_id kendt → Marker bil som DAMAGED i Fleet
    # ----------------------------------------------------
    fleet_result = None
    if vehicle_id is not None:
        ok, fleet_err = call_fleet_update_status(
            vehicle_id=vehicle_id,
            status="DAMAGED",
            lease_id=lease_id,
        )
        fleet_result = {"ok": ok, "error": fleet_err}

    row = get_damage_by_id(damage_id)
    damage_dict = dict(row)

    if fleet_result is not None:
        damage_dict["fleet_update"] = fleet_result

    return jsonify(damage_dict), 201


@app.patch("/damages/<int:damage_id>/status")
def change_damage_status(damage_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    row = get_damage_by_id(damage_id)
    if row is None:
        return jsonify({"error": "damage not found"}), 404

    update_damage_status(damage_id, new_status)
    row = get_damage_by_id(damage_id)
    return jsonify(dict(row)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
