from flask import Flask, jsonify, request
from database import (
    init_db,
    list_vehicles,
    get_vehicle_by_id,
    find_available_by_model,
    update_vehicle_status,
)

app = Flask(__name__)

# Tilladte statusværdier i flåden
VALID_STATUSES = {"AVAILABLE", "LEASED", "DAMAGED", "REPAIR"}


def row_to_dict(row):
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


@app.before_request
def setup_db():
    # Sørger for at fleet.db og vehicles-tabellen er oprettet og seedet fra CSV
    init_db()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "fleet_service"}), 200


@app.route("/vehicles", methods=["GET"])
def get_vehicles():
    """
    GET /vehicles
    GET /vehicles?status=AVAILABLE
    """
    status = request.args.get("status")
    if status is not None and status not in VALID_STATUSES:
        return jsonify({"error": "Invalid status filter"}), 400

    rows = list_vehicles(status=status)
    data = [row_to_dict(r) for r in rows]
    return jsonify(data), 200


@app.route("/vehicles/<int:vehicle_id>", methods=["GET"])
def get_vehicle(vehicle_id: int):
    """
    GET /vehicles/<id>
    """
    row = get_vehicle_by_id(vehicle_id)
    if row is None:
        return jsonify({"error": "Vehicle not found"}), 404

    return jsonify(row_to_dict(row)), 200


@app.route("/vehicles/allocate", methods=["POST"])
def allocate_vehicle():
    """
    POST /vehicles/allocate
    Body: { "model_name": "...", "lease_id": 123 }

    Bruges af lease_service til at finde første AVAILABLE bil
    af en given model og markere den som LEASED.
    """
    data = request.get_json(silent=True) or {}
    model_name = data.get("model_name")
    lease_id = data.get("lease_id")

    if not model_name or lease_id is None:
        return jsonify({"error": "model_name and lease_id are required"}), 400

    row = find_available_by_model(model_name)
    if row is None:
        return jsonify({"error": "No AVAILABLE vehicle for this model"}), 404

    vehicle_id = row["id"]
    update_vehicle_status(vehicle_id=vehicle_id, status="LEASED", lease_id=lease_id)

    # Hent den opdaterede række
    updated = get_vehicle_by_id(vehicle_id)
    return jsonify(row_to_dict(updated)), 200


@app.route("/vehicles/<int:vehicle_id>/status", methods=["PUT"])
def set_vehicle_status(vehicle_id: int):
    """
    PUT /vehicles/<id>/status
    Body: { "status": "DAMAGED", "lease_id": 123 } (lease_id optional)

    Bruges fx af lease_service (LEASING / afslutning) og damage_service.
    """
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    lease_id = data.get("lease_id")  # må gerne være None

    if status not in VALID_STATUSES:
        return jsonify({"error": f"Invalid status. Must be one of {sorted(VALID_STATUSES)}"}), 400

    # Tjek om bilen findes
    row = get_vehicle_by_id(vehicle_id)
    if row is None:
        return jsonify({"error": "Vehicle not found"}), 404

    update_vehicle_status(vehicle_id=vehicle_id, status=status, lease_id=lease_id)

    updated = get_vehicle_by_id(vehicle_id)
    return jsonify(row_to_dict(updated)), 200


@app.get("/vehicles/pricing/by-model")
def get_pricing_by_model():
    """
    Returnerer månedlig pris for en given bilmodel baseret på flådedata.
    Vi finder første AVAILABLE bil med den model og bruger dens monthly_price.
    """
    model_name = request.args.get("model_name")
    if not model_name:
        return jsonify({"error": "model_name query parameter is required"}), 400

    row = find_available_by_model(model_name)
    if row is None:
        return jsonify({"error": f"Ingen AVAILABLE biler fundet for modellen '{model_name}'"}), 404

    v = dict(row)
    return jsonify({
        "model_name": v.get("model_name"),
        "monthly_price": v.get("monthly_price"),
        "example_vehicle_id": v.get("id"),
        "status": v.get("status"),
    }), 200






if __name__ == "__main__":
    # Lokalt debug-run. I Docker køres den typisk via gunicorn eller flask run.
    app.run(host="0.0.0.0", port=5006, debug=True)
