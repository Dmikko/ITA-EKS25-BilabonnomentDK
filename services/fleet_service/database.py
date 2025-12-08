import sqlite3
from pathlib import Path
from datetime import datetime
import csv

DB_PATH = Path(__file__).parent / "fleet.db"
CSV_PATH = Path(__file__).parent / "Bilabonnement 2025(Sheet1).csv"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Opret vehicles-tabel, hvis den ikke findes
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_date       TEXT,
            subscription_start  TEXT,
            subscription_end    TEXT,
            model_name          TEXT NOT NULL,
            purchase_price      REAL,
            fuel_type           TEXT,
            odometer_start      INTEGER,
            subscription_km     INTEGER,
            contract_km         INTEGER,
            subscription_months INTEGER,
            monthly_price       REAL,
            delivery_location   TEXT,
            subscription_years  REAL,
            status              TEXT NOT NULL DEFAULT 'AVAILABLE',
            current_lease_id    INTEGER,
            updated_at          TEXT NOT NULL
        )
        """
    )

    # Evt. simple indeks til hurtigere opslag senere
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicles_status
        ON vehicles(status)
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicles_model_status
        ON vehicles(model_name, status)
        """
    )

    conn.commit()

    # Seed fra CSV, hvis tabellen er tom
    cur.execute("SELECT COUNT(*) AS c FROM vehicles")
    count = cur.fetchone()["c"]
    if count == 0 and CSV_PATH.exists():
        seed_from_csv(cur)
        conn.commit()

    conn.close()


def _parse_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    # CSV bruger komma som decimal (fx "2,00")
    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def seed_from_csv(cur: sqlite3.Cursor):
    """
    Læser Bilabonnement 2025(Sheet1).csv og indsætter biler i vehicles-tabellen.
    Antager semikolon-separeret CSV.
    """
    with CSV_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        # FIX: fjern BOM fra første kolonnenavn (fx '\ufeffDato Indkoeb')
        if reader.fieldnames:
            cleaned = [name.lstrip("\ufeff") for name in reader.fieldnames]
            reader.fieldnames = cleaned

        now = datetime.utcnow().isoformat()

        for row in reader:
            # Hvis rækken er helt tom, spring videre
            if not any(row.values()):
                continue

            cur.execute(
                """
                INSERT INTO vehicles (
                    purchase_date,
                    subscription_start,
                    subscription_end,
                    model_name,
                    purchase_price,
                    fuel_type,
                    odometer_start,
                    subscription_km,
                    contract_km,
                    subscription_months,
                    monthly_price,
                    delivery_location,
                    subscription_years,
                    status,
                    current_lease_id,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("Dato Indkoeb"),
                    row.get("Startdato abonnement"),
                    row.get("Slutdato abonnement"),
                    row.get("Bilmaerke"),
                    _parse_float(row.get("Indkoebspris")),
                    row.get("Braendstof"),
                    _parse_int(row.get("Koert Km ved abonnemt start")),
                    _parse_int(row.get("Abonnement  Km koert")),
                    _parse_int(row.get("Aftalt kontraktabonnment KM")),
                    _parse_int(row.get("Abonnementsperiode")),
                    _parse_float(row.get("abonnement pris pr maaned")),
                    row.get("Udleveringssted"),
                    _parse_float(row.get("Abonnement Varighed (År)")),
                    "AVAILABLE",
                    None,
                    now,
                ),
            )


def list_vehicles(status: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM vehicles WHERE status = ? ORDER BY id",
            (status,),
        )
    else:
        cur.execute("SELECT * FROM vehicles ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_vehicle_by_id(vehicle_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cur.fetchone()
    conn.close()
    return row


def find_available_by_model(model_name: str):
    """
    Find første AVAILABLE bil med det givne modelnavn.
    Bruges når en ny lejeaftale oprettes.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM vehicles
        WHERE model_name = ? AND status = 'AVAILABLE'
        ORDER BY id
        LIMIT 1
        """,
        (model_name,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_vehicle_status(vehicle_id: int, status: str, lease_id: int | None):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        """
        UPDATE vehicles
        SET status = ?, current_lease_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, lease_id, now, vehicle_id),
    )
    conn.commit()
    conn.close()
