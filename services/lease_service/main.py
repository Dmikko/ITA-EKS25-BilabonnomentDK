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
)

# RKI-service kører som egen container på docker-netværket
RKI_BASE_URL = os.getenv("RKI_BASE_URL", "http://rki_service:5005")

app = Flask(__name__)


def call_rki_check(customer_cpr: str | None):
    """
    Kalder RKI-service. Hvis CPR mangler eller RKI ikke svarer,
    returnerer vi noget fornuftigt.

    Returnerer: (status, score, reason)
    - status: APPROVED / REJECTED / PENDING / SKIPPED / UNKNOWN
    - score:  optional tal (kan være None hvis RKI ikke sender det)
    - reason: tekst til debugging/log
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


@app.patch("/leases/<int:lease_id>/status")
def change_status(lease_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    lease = get_lease_by_id(lease_id)
    if lease is None:
        return jsonify({"error": "lease not found"}), 404

    update_lease_status(lease_id, new_status)
    lease = get_lease_by_id(lease_id)
    return jsonify(dict(lease)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
