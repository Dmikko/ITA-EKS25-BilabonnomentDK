from flask import Flask, request, jsonify
import jwt
import os
from datetime import datetime, timedelta

from database import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_id,
    list_users,
    update_user_role,
    verify_password,
)

# Konfiguration
SECRET = os.getenv("AUTH_SECRET", "supersecret")  # skal matches i gateway senere
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "60"))

app = Flask(__name__)


@app.before_request
def setup():
    # Sørg for DB og en default admin-bruger
    init_db()
    ensure_default_admin()


def ensure_default_admin():
    # Opretter admin/admin hvis den ikke findes – kun til udvikling
    username = "admin"
    password = "admin"
    email = "admin@bilabonnement.local"
    role = "ADMIN"

    existing = get_user_by_username(username)
    if existing is None:
        create_user(username, password, email, role)
        print("Default admin user created: admin / admin")
    else:
        print("Admin user already exists")


def create_token(user_row):
    payload = {
        "sub": user_row["id"],
        "username": user_row["username"],
        "role": user_row["role"],
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES),
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token


def decode_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, "Missing or invalid Authorization header"

    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth_service"}


@app.post("/login")
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = get_user_by_username(username)
    if user is None:
        return jsonify({"error": "invalid credentials"}), 401

    if not verify_password(password, user["password_hash"]):
        return jsonify({"error": "invalid credentials"}), 401

    if not user["is_active"]:
        return jsonify({"error": "user is inactive"}), 403

    token = create_token(user)
    return jsonify(
        {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "email": user["email"],
            },
        }
    )


@app.get("/me")
def me():
    payload, err = decode_token_from_header()
    if err:
        return jsonify({"error": err}), 401

    user = get_user_by_id(payload["sub"])
    if user is None:
        return jsonify({"error": "user not found"}), 404

    return jsonify(
        {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user["email"],
            "created_at": user["created_at"],
        }
    )


def require_role(required_roles):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            payload, err = decode_token_from_header()
            if err:
                return jsonify({"error": err}), 401
            if payload.get("role") not in required_roles:
                return jsonify({"error": "forbidden"}), 403
            # læg payload på request-context hvis du vil
            request.jwt_payload = payload
            return fn(*args, **kwargs)

        wrapper.__name__ = fn.__name__
        return wrapper

    return decorator


@app.get("/users")
@require_role(["ADMIN", "LEDELSE"])
def get_users():
    rows = list_users()
    users = [dict(row) for row in rows]
    return jsonify(users)


@app.post("/users")
@require_role(["ADMIN", "LEDELSE"])
def create_user_endpoint():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    email = data.get("email", "")
    role = data.get("role", "DATAREG")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    try:
        create_user(username, password, email, role)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"status": "created"}), 201


@app.patch("/users/<int:user_id>/role")
@require_role(["ADMIN", "LEDELSE"])
def change_role(user_id):
    data = request.get_json() or {}
    new_role = data.get("role")
    if not new_role:
        return jsonify({"error": "role required"}), 400

    if get_user_by_id(user_id) is None:
        return jsonify({"error": "user not found"}), 404

    update_user_role(user_id, new_role)
    return jsonify({"status": "updated"}), 200


if __name__ == "__main__":
    # Til lokal udvikling (uden Docker)
    app.run(host="0.0.0.0", port=5001, debug=True)
