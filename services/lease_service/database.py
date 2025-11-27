import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "lease.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT,
            car_model TEXT NOT NULL,
            car_segment TEXT,
            car_registration TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            monthly_price REAL NOT NULL,
            status TEXT NOT NULL,
            created_by_user_id INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def create_lease(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO leases (
            customer_name,
            customer_email,
            customer_phone,
            car_model,
            car_segment,
            car_registration,
            start_date,
            end_date,
            monthly_price,
            status,
            created_by_user_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["customer_name"],
            data["customer_email"],
            data.get("customer_phone"),
            data["car_model"],
            data.get("car_segment"),
            data.get("car_registration"),
            data["start_date"],
            data["end_date"],
            data["monthly_price"],
            data.get("status", "ACTIVE"),
            data.get("created_by_user_id"),
            now,
        ),
    )

    lease_id = cur.lastrowid
    conn.commit()
    conn.close()
    return lease_id


def list_leases(status: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM leases WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM leases ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_lease_by_id(lease_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM leases WHERE id = ?", (lease_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_lease_status(lease_id: int, new_status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE leases SET status = ? WHERE id = ?", (new_status, lease_id))
    conn.commit()
    conn.close()
