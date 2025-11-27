from flask import Flask, request, jsonify
from database import (
    init_db,
    create_lease,
    list_leases,
    get_lease_by_id,
    update_lease_status,
)

app = Flask(__name__)


@app.before_request
def setup():
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
