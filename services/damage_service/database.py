import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "damage.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS damages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lease_id INTEGER NOT NULL,
            vehicle_id INTEGER,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            estimated_cost REAL NOT NULL,
            detected_at TEXT NOT NULL,
            status TEXT NOT NULL,
            created_by_user_id INTEGER
        )
        """
    )

    conn.commit()
    conn.close()


def create_damage(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO damages (
            lease_id,
            vehicle_id,
            category,
            description,
            estimated_cost,
            detected_at,
            status,
            created_by_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["lease_id"],
            data.get("vehicle_id"),
            data["category"],
            data["description"],
            data["estimated_cost"],
            data.get("detected_at", now),
            data.get("status", "OPEN"),
            data.get("created_by_user_id"),
        ),
    )

    damage_id = cur.lastrowid
    conn.commit()
    conn.close()
    return damage_id


def list_damages(status: str | None = None, lease_id: int | None = None):
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM damages WHERE 1=1"
    params: list = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if lease_id is not None:
        query += " AND lease_id = ?"
        params.append(lease_id)

    query += " ORDER BY detected_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_damage_by_id(damage_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM damages WHERE id = ?", (damage_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_damage_status(damage_id: int, new_status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE damages SET status = ? WHERE id = ?",
        (new_status, damage_id),
    )
    conn.commit()
    conn.close()
