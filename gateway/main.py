from flask import Flask, request, jsonify
import os
import requests
import jwt

app = Flask(__name__)

# ---- Konfiguration ----
# Disse kan du overskrive med env vars, fx når I bruger Docker
AUTH_BASE = os.getenv("AUTH_BASE_URL", "http://localhost:5001")
LEASE_BASE = os.getenv("LEASE_BASE_URL", "http://localhost:5002")
DAMAGE_BASE = os.getenv("DAMAGE_BASE_URL", "http://localhost:5003")
REPORT_BASE = os.getenv("REPORT_BASE_URL", "http://localhost:5004")


# SKAL matche SECRET i AuthService
AUTH_SECRET = os.getenv("AUTH_SECRET", "supersecret")

# Simple mapping: (method, path_prefix) -> tilladte roller
ROUTE_PERMISSIONS = {
    ("GET", "/leases"): ["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"],
    ("POST", "/leases"): ["DATAREG", "LEDELSE", "ADMIN"],
    ("GET", "/leases/"): ["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"],  # /leases/<id>
    ("PATCH", "/leases/"): ["DATAREG", "LEDELSE", "ADMIN"],                    # /leases/<id>/status
    # Auth-ruter styres inde i AuthService

    # Nye: damages
    ("GET", "/damages"): ["SKADE", "FORRET", "LEDELSE", "ADMIN"],
    ("POST", "/damages"): ["SKADE", "LEDELSE", "ADMIN"],
    ("GET", "/damages/"): ["SKADE", "FORRET", "LEDELSE", "ADMIN"],   # /damages/<id>
    ("PATCH", "/damages/"): ["SKADE", "LEDELSE", "ADMIN"],           # /damages/<id>/status



    # NY: Reporting
    ("GET", "/reporting/kpi"): ["FORRET", "LEDELSE", "ADMIN"],
}


def _decode_jwt_from_header():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, "Missing or invalid Authorization header"

    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


def _requires_auth_for_path(method: str, path: str) -> bool:
    # Alt under /auth tillades uden JWT, resten kræver token
    if path.startswith("/auth"):
        return False
    # Health/diagnostic kan evt. være åbne
    if path.startswith("/health"):
        return False
    return True


def _check_role(payload, method: str, path: str):
    """
    Matcher method + path op imod vores simple ROUTE_PERMISSIONS.
    Vi matcher på prefix, fx "/leases/" for /leases/<id> og /leases/<id>/status
    """
    # Find passende key
    for (m, prefix), roles in ROUTE_PERMISSIONS.items():
        if m == method and path.startswith(prefix):
            user_role = payload.get("role")
            # 👇 SUPER IMPORTANT TIL DEV & ADMIN:
            if user_role == "ADMIN":
                return True, None  # admin må ALT
            if user_role not in roles:
                return False, f"Role '{user_role}' not allowed for {method} {path}"
    return True, None


@app.before_request
def global_auth_check():
    method = request.method
    path = request.path

    if not _requires_auth_for_path(method, path):
        return None  # tillad uden check

    payload, err = _decode_jwt_from_header()
    if err:
        return jsonify({"error": err}), 401

    ok, role_err = _check_role(payload, method, path)
    if not ok:
        return jsonify({"error": role_err}), 403

    # Hvis du vil, kan du gemme payload på request-context
    request.jwt_payload = payload
    return None


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}


# -------- AUTH ROUTES (proxy til AuthService) --------

@app.post("/auth/login")
def auth_login():
    url = f"{AUTH_BASE}/login"
    resp = requests.post(url, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())


@app.get("/auth/me")
def auth_me():
    # Forwarder bare token videre til AuthService
    url = f"{AUTH_BASE}/me"
    headers = {
        "Authorization": request.headers.get("Authorization", "")
    }
    resp = requests.get(url, headers=headers)
    return (resp.content, resp.status_code, resp.headers.items())


@app.get("/auth/users")
def auth_users():
    url = f"{AUTH_BASE}/users"
    headers = {
        "Authorization": request.headers.get("Authorization", "")
    }
    resp = requests.get(url, headers=headers)
    return (resp.content, resp.status_code, resp.headers.items())


@app.post("/auth/users")
def auth_create_user():
    url = f"{AUTH_BASE}/users"
    headers = {
        "Authorization": request.headers.get("Authorization", "")
    }
    resp = requests.post(url, headers=headers, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())


@app.patch("/auth/users/<int:user_id>/role")
def auth_change_role(user_id):
    url = f"{AUTH_BASE}/users/{user_id}/role"
    headers = {
        "Authorization": request.headers.get("Authorization", "")
    }
    resp = requests.patch(url, headers=headers, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())


# -------- LEASE ROUTES (proxy til LeaseService) --------

@app.get("/leases")
def gw_get_leases():
    url = f"{LEASE_BASE}/leases"
    resp = requests.get(url, params=request.args)
    return (resp.content, resp.status_code, resp.headers.items())


@app.get("/leases/<int:lease_id>")
def gw_get_lease(lease_id):
    url = f"{LEASE_BASE}/leases/{lease_id}"
    resp = requests.get(url)
    return (resp.content, resp.status_code, resp.headers.items())


@app.post("/leases")
def gw_create_lease():
    url = f"{LEASE_BASE}/leases"
    resp = requests.post(url, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())


@app.patch("/leases/<int:lease_id>/status")
def gw_change_lease_status(lease_id):
    url = f"{LEASE_BASE}/leases/{lease_id}/status"
    resp = requests.patch(url, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())



# -------- DAMAGE ROUTES (proxy til DamageService) --------

@app.get("/damages")
def gw_get_damages():
    url = f"{DAMAGE_BASE}/damages"
    resp = requests.get(url, params=request.args)
    return (resp.content, resp.status_code, resp.headers.items())


@app.get("/damages/<int:damage_id>")
def gw_get_damage(damage_id):
    url = f"{DAMAGE_BASE}/damages/{damage_id}"
    resp = requests.get(url)
    return (resp.content, resp.status_code, resp.headers.items())


@app.post("/damages")
def gw_create_damage():
    url = f"{DAMAGE_BASE}/damages"
    resp = requests.post(url, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())


@app.patch("/damages/<int:damage_id>/status")
def gw_change_damage_status(damage_id):
    url = f"{DAMAGE_BASE}/damages/{damage_id}/status"
    resp = requests.patch(url, json=request.get_json())
    return (resp.content, resp.status_code, resp.headers.items())



# -------- REPORTING ROUTES (proxy til ReportingService) --------

@app.get("/reporting/kpi/overview")
def gw_kpi_overview():
    url = f"{REPORT_BASE}/reporting/kpi/overview"
    resp = requests.get(url)
    return (resp.content, resp.status_code, resp.headers.items())



if __name__ == "__main__":
    # Til lokal udvikling uden Docker
    app.run(host="0.0.0.0", port=8000, debug=True)
