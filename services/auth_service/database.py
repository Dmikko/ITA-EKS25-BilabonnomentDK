import sqlite3
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path(__file__).parent / "auth.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def create_user(username: str, password: str, email: str, role: str = "DATAREG"):
    password_hash = generate_password_hash(password)
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, email, role, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """,
        (username, password_hash, email, role, now),
    )
    conn.commit()
    conn.close()


def get_user_by_username(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def list_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_user_role(user_id: int, new_role: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)
