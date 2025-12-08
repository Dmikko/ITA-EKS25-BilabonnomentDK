import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Standard: filen hedder lease.db i containerens /app
DB_PATH = os.getenv("LEASE_DB_PATH", "lease.db")
print(f"LEASE_DB_PATH={DB_PATH}")

def get_connection():
    """
    Åbn en SQLite forbindelse til lease.db.
    Sørger for at mappen til filen findes.
    """
    db_path = Path(DB_PATH)
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Opretter leases-tabellen med det schema vi har aftalt.
    Hvis en gammel DB eksisterer med forkert struktur, er det lettest
    at slette lease.db manuelt og lade denne funktion oprette en ny.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_cpr TEXT,
            customer_email TEXT NOT NULL,
            customer_phone TEXT,
            car_model TEXT NOT NULL,
            car_segment TEXT,
            car_registration TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            monthly_price REAL NOT NULL,
            status TEXT NOT NULL,
            vehicle_id INTEGER,                 -- NY: reference til fleet.vehicles.id
            rki_status TEXT NOT NULL DEFAULT 'PENDING',
            rki_score REAL,
            rki_checked_at TEXT,
            created_by_user_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL            -- NY: til status/ændringer
        )
        """
    )

    conn.commit()
    conn.close()


def create_lease(data: dict) -> int:
    """
    Indsætter en ny lejeaftale.
    RKI-felter starter som PENDING, score = NULL, checked_at = NULL.
    vehicle_id sættes typisk først senere, når Fleet har allokeret en bil.
    """
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    cur.execute(
        """
        INSERT INTO leases (
            customer_name,
            customer_cpr,
            customer_email,
            customer_phone,
            car_model,
            car_segment,
            car_registration,
            start_date,
            end_date,
            monthly_price,
            status,
            vehicle_id,
            rki_status,
            rki_score,
            rki_checked_at,
            created_by_user_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["customer_name"],
            data.get("customer_cpr"),
            data["customer_email"],
            data.get("customer_phone"),
            data["car_model"],
            data.get("car_segment"),
            data.get("car_registration"),
            data["start_date"],
            data["end_date"],
            data["monthly_price"],
            data.get("status", "ACTIVE"),
            data.get("vehicle_id"),            # typisk None ved oprettelse
            data.get("rki_status", "PENDING"),
            data.get("rki_score"),             # typisk None ved oprettelse
            data.get("rki_checked_at"),        # typisk None ved oprettelse
            data.get("created_by_user_id"),
            now,
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
        cur.execute(
            "SELECT * FROM leases WHERE status = ? ORDER BY id DESC",
            (status,),
        )
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
    now = datetime.utcnow().isoformat()
    cur.execute(
        "UPDATE leases SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, now, lease_id),
    )
    conn.commit()
    conn.close()


def update_rki_result(lease_id: int, rki_status: str, rki_score: float | None):
    """
    Bruges af main.py efter kald til RKI-service.
    Opdaterer rki_status, rki_score og timestamp.
    """
    conn = get_connection()
    cur = conn.cursor()
    checked_at = datetime.utcnow().isoformat()

    cur.execute(
        """
        UPDATE leases
        SET rki_status = ?, rki_score = ?, rki_checked_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (rki_status, rki_score, checked_at, checked_at, lease_id),
    )

    conn.commit()
    conn.close()


def update_lease_vehicle(lease_id: int, vehicle_id: int):
    """
    Bruges efter succesfuld allokering i FleetService.
    Binder lease til en konkret bil.
    """
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        UPDATE leases
        SET vehicle_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (vehicle_id, now, lease_id),
    )
    conn.commit()
    conn.close()
