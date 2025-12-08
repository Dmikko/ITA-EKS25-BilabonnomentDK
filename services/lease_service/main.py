import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from database import (
    init_db,
    create_lease,
    list_leases,
    get_lease_by_id,
    update_lease_status,
    update_lease_vehicle,
)

# RKI-service kører som egen container på docker-netværket
RKI_BASE_URL = os.getenv("RKI_BASE_URL", "http://rki_service:5005")
# Fleet-service kører som egen container på docker-netværket
FLEET_BASE_URL = os.getenv("FLEET_BASE_URL", "http://fleet_service:5006")


app = Flask(__name__)


def call_rki_check(customer_cpr: str | None):
    """
    Kalder RKI-service. Hvis CPR mangler eller RKI ikke svarer,
    returnerer vi en fornuftig default.
    Returnerer: (status, score, reason)
    """
    if not customer_cpr:
        return "SKIPPED", None, "CPR mangler"

    try:
        resp = requests.post(
            f"{RKI_BASE_URL}/rki/check",
            json={"cpr": customer_cpr},
            timeout=3,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "UNKNOWN").upper()
        score = data.get("score")
        reason = data.get("reason", "")
        return status, score, reason
    except Exception as e:
        # Hvis RKI er nede, vil vi stadig kunne oprette aftale
        return "PENDING", None, f"RKI-fejl: {e}"

def call_fleet_allocate(car_model: str, lease_id: int):
    """
    Kalder FleetService for at allokere en AVAILABLE bil af den ønskede model.
    Returnerer (vehicle_dict, error_dict)
    - vehicle_dict: dict med bilen, hvis succes
    - error_dict: dict med fejlbesked, hvis fejl
    """
    try:
        resp = requests.post(
            f"{FLEET_BASE_URL}/vehicles/allocate",
            json={"model_name": car_model, "lease_id": lease_id},
            timeout=5,
        )
    except Exception as e:
        return None, {"error": "fleet_service unavailable", "details": str(e)}

    try:
        data = resp.json()
    except Exception:
        return None, {"error": "Invalid JSON from fleet_service", "status_code": resp.status_code}

    if resp.status_code != 200:
        # fx 404 = ingen AVAILABLE bil
        return None, data

    return data, None


def call_fleet_update_status(vehicle_id: int, status: str, lease_id: int | None = None):
    """
    Kalder FleetService for at opdatere status på en bil.
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
            return False, {"error": "Invalid JSON from fleet_service", "status_code": resp.status_code}

    return True, None


@app.before_request
def setup():
    # Sørger for at DB og tabel findes (billig operation i SQLite)
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "lease_service"}


@app.get("/leases")
def get_leases():
    status = request.args.get("status")
    rows = list_leases(status=status)
    leases = [dict(row) for row in rows]
    return jsonify(leases)


@app.get("/leases/<int:lease_id>")
def get_lease(lease_id):
    lease = get_lease_by_id(lease_id)
    if lease is None:
        return jsonify({"error": "lease not found"}), 404
    return jsonify(dict(lease))

"""""
@app.post("/leases")
def create_lease_endpoint():
    data = request.get_json() or {}

    required = [
        "customer_name",
        "customer_email",
        "car_model",
        "start_date",
        "end_date",
        "monthly_price",
    ]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # --- RKI-flow ---
    rki_status, rki_score, rki_reason = call_rki_check(
        data.get("customer_cpr")
    )

    # Debug-log i containeren, ikke vist til bruger
    print(f"[RKI] status={rki_status}, score={rki_score}, reason={rki_reason}")

    # Sæt RKI-felter ind i data, så de bliver gemt i DB
    data["rki_status"] = rki_status
    data["rki_score"] = rki_score

    # Vi stempler tidspunkt hvis vi faktisk har forsøgt et RKI-check
    if rki_status not in ("PENDING", "UNKNOWN"):
        data["rki_checked_at"] = datetime.utcnow().isoformat()
    else:
        data["rki_checked_at"] = None

    # Standard status på lease, hvis den ikke er sat
    data.setdefault("status", "ACTIVE")

    try:
        lease_id = create_lease(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    lease = get_lease_by_id(lease_id)
    return jsonify(dict(lease)), 201
"""""


def call_fleet_allocate(car_model: str, lease_id: int):
    """
    Kalder FleetService for at allokere en AVAILABLE bil af den ønskede model.
    Returnerer (vehicle_dict, error_dict)
    - vehicle_dict: dict med bilen, hvis succes
    - error_dict: dict med fejlbesked, hvis fejl
    """
    try:
        resp = requests.post(
            f"{FLEET_BASE_URL}/vehicles/allocate",
            json={"model_name": car_model, "lease_id": lease_id},
            timeout=5,
        )
    except Exception as e:
        return None, {"error": "fleet_service unavailable", "details": str(e)}

    try:
        data = resp.json()
    except Exception:
        return None, {"error": "Invalid JSON from fleet_service", "status_code": resp.status_code}

    if resp.status_code != 200:
        # fx 404 = ingen AVAILABLE bil
        return None, data

    return data, None




@app.post("/leases")
def create_lease_endpoint():
    data = request.get_json() or {}

    required = [
        "customer_name",
        "customer_email",
        "car_model",
        "start_date",
        "end_date",
        "monthly_price",
    ]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # ---- RKI CHECK ----
    customer_cpr = data.get("customer_cpr")
    rki_status, rki_score, rki_reason = call_rki_check(customer_cpr)

    data["rki_status"] = rki_status
    data["rki_score"] = rki_score

    # Standard status på lease, hvis den ikke er sat
    data.setdefault("status", "ACTIVE")

    # 1) Opret lease i egen DB
    try:
        lease_id = create_lease(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    lease = get_lease_by_id(lease_id)
    lease_dict = dict(lease)

    # 2) Alloker bil i FleetService
    car_model = lease_dict.get("car_model") or data.get("car_model")
    allocated_vehicle = None
    fleet_error = None

    if car_model:
        allocated_vehicle, fleet_error = call_fleet_allocate(
            car_model=car_model,
            lease_id=lease_id,
        )
        # Hvis der blev allokeret en bil, så bind den til lejen
        if allocated_vehicle and "id" in allocated_vehicle:
            vehicle_id = allocated_vehicle["id"]
            update_lease_vehicle(lease_id, vehicle_id)
            # refetch lease, så vehicle_id også kommer med i svaret
            lease = get_lease_by_id(lease_id)
            lease_dict = dict(lease)

    # 3) Byg svar til frontend
    lease_dict["rki_reason"] = rki_reason      # ikke i DB, men retur til frontend
    lease_dict["fleet_vehicle"] = allocated_vehicle
    lease_dict["fleet_error"] = fleet_error

    return jsonify(lease_dict), 201





@app.patch("/leases/<int:lease_id>/status")
def change_status(lease_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    lease = get_lease_by_id(lease_id)
    if lease is None:
        return jsonify({"error": "lease not found"}), 404

    lease_dict = dict(lease)
    vehicle_id = lease_dict.get("vehicle_id")

    # Opdater lease-status i egen DB
    update_lease_status(lease_id, new_status)
    updated_lease = get_lease_by_id(lease_id)
    updated_dict = dict(updated_lease)

    fleet_result = None

    # Hvis lejen afsluttes, så forsøg at sætte bilen AVAILABLE igen i Fleet
    if new_status in ("COMPLETED", "CANCELLED") and vehicle_id is not None:
        ok, fleet_error = call_fleet_update_status(
            vehicle_id=vehicle_id,
            status="AVAILABLE",
            lease_id=None,  # vi løsner koblingen på Fleet-siden
        )
        fleet_result = {
            "ok": ok,
            "error": fleet_error,
        }

    # Udvider svar med info om Fleet-opdatering
    if fleet_result is not None:
        updated_dict["fleet_update"] = fleet_result

    return jsonify(updated_dict), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
