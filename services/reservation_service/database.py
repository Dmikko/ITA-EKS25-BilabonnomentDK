import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "reservation.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lease_id INTEGER NOT NULL,
            pickup_date TEXT NOT NULL,
            pickup_location TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            actual_pickup_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def create_reservation(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO reservations (
            lease_id,
            pickup_date,
            pickup_location,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["lease_id"],
            data["pickup_date"],
            data["pickup_location"],
            data.get("status", "PENDING"),
            now,
            now,
        ),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def list_reservations(status: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM reservations WHERE status = ? ORDER BY pickup_date",
            (status,),
        )
    else:
        cur.execute("SELECT * FROM reservations ORDER BY pickup_date")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_reservation_by_id(reservation_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_reservation_status(reservation_id: int, new_status: str):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    actual_pickup_at = None
    if new_status == "PICKED_UP":
        actual_pickup_at = now

    cur.execute(
        """
        UPDATE reservations
        SET status = ?, updated_at = ?, actual_pickup_at = COALESCE(?, actual_pickup_at)
        WHERE id = ?
        """,
        (new_status, now, actual_pickup_at, reservation_id),
    )
    conn.commit()
    conn.close()

