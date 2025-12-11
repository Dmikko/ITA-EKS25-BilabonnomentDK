import sqlite3
import csv
import pathlib
from collections import defaultdict
from datetime import datetime

ROOT = pathlib.Path(__file__).parent
EXPORT_DIR = ROOT / "exports_csv"
EXPORT_DIR.mkdir(exist_ok=True)


# -----------------------------
# Hjælpere til generel eksport
# -----------------------------

def export_db(db_path: pathlib.Path):
    """
    Eksporterer alle tabeller i en given .db-fil til CSV.
    Filnavne: <dbname>__<tablename>.csv
    """
    print(f"\n=== Eksporterer DB: {db_path} ===")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """)
    tables = [row[0] for row in cur.fetchall()]

    if not tables:
        print("  (Ingen tabeller fundet)")
        conn.close()
        return

    for table in tables:
        print(f"  -> Tabel: {table}")
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        if not rows:
            print("     (ingen rækker, springer over)")
            continue

        headers = rows[0].keys()
        csv_name = f"{db_path.stem}__{table}.csv"
        csv_path = EXPORT_DIR / csv_name

        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[h] for h in headers])

        print(f"     -> skrevet til {csv_path}")

    conn.close()


# -----------------------------
# Hjælpere til joins (analytics)
# -----------------------------

def load_table(db_path: pathlib.Path, table_name: str):
    """
    Loader en tabel som list[dict]. Returnerer [] hvis DB eller tabel mangler.
    """
    if not db_path.exists():
        print(f"  [ADVARSEL] DB mangler: {db_path}")
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"  [ADVARSEL] Kunne ikke læse {table_name} fra {db_path}: {e}")
        conn.close()
        return []

    result = [dict(r) for r in rows]
    conn.close()
    return result


def export_analytics_join():
    """
    Laver en joined CSV på tværs af:
      - leases (lease.db)
      - damages (damage.db)
      - vehicles (fleet.db)
      - reservations (reservation.db)

    Grain: én række per skade (damage),
    joinet med tilhørende lease, vehicle og (evt.) reservation.
    """
    print("\n=== Bygger analytics-join ===")

    lease_db = ROOT / "services" / "lease_service" / "lease.db"
    damage_db = ROOT / "services" / "damage_service" / "damage.db"
    fleet_db = ROOT / "services" / "fleet_service" / "fleet.db"
    reservation_db = ROOT / "services" / "reservation_service" / "reservation.db"

    leases = load_table(lease_db, "leases")
    damages = load_table(damage_db, "damages")
    vehicles = load_table(fleet_db, "vehicles")
    reservations = load_table(reservation_db, "reservations")

    print(f"  leases: {len(leases)} rækker")
    print(f"  damages: {len(damages)} rækker")
    print(f"  vehicles: {len(vehicles)} rækker")
    print(f"  reservations: {len(reservations)} rækker")

    if not leases or not damages:
        print("  Ikke nok data til at lave meningsfuldt join (leases/damages mangler).")
        return

    # Indexer leases og vehicles efter id
    leases_by_id = {l["id"]: l for l in leases if "id" in l}
    vehicles_by_id = {v["id"]: v for v in vehicles if "id" in v}

    # Indexer reservationer pr. lease_id
    # Hvis der er flere, vælger vi den tidligste pickup_date
    reservations_by_lease = defaultdict(list)
    for r in reservations:
        lease_id = r.get("lease_id")
        if lease_id is not None:
            reservations_by_lease[lease_id].append(r)

    # Vælg én "primær" reservation per lease (tidligste pickup_date)
    reservation_primary_by_lease = {}
    for lease_id, r_list in reservations_by_lease.items():
        def parse_pickup(r):
            val = r.get("pickup_date") or ""
            # pickup_date burde være ISO8601; string-sort virker fint som fallback
            try:
                return datetime.fromisoformat(val)
            except Exception:
                return val
        r_sorted = sorted(r_list, key=parse_pickup)
        reservation_primary_by_lease[lease_id] = r_sorted[0]

    # Byg joined rækker: én række per damage
    joined_rows = []

    for d in damages:
        lease_id = d.get("lease_id")
        lease = leases_by_id.get(lease_id)

        # Hvis der ikke findes lease, giver det ikke mening til analytics
        if lease is None:
            continue

        # Vehicle: kræver at lease har vehicle_id-kolonne
        vehicle = None
        vehicle_id = lease.get("vehicle_id")
        if vehicle_id is not None:
            vehicle = vehicles_by_id.get(vehicle_id)

        # Reservation: primære pr. lease_id
        reservation = reservation_primary_by_lease.get(lease_id)

        row_out = {}

        # Prefiks alle felter, så navne ikke clasher
        # Lease-felter
        for k, v in lease.items():
            row_out[f"lease_{k}"] = v

        # Damage-felter
        for k, v in d.items():
            row_out[f"damage_{k}"] = v

        # Vehicle-felter (kan være None)
        if vehicle is not None:
            for k, v in vehicle.items():
                row_out[f"vehicle_{k}"] = v
        else:
            # Sikrer at nogle typiske vehicle-felter findes (Tableau bliver gladere)
            for k in ["id", "model_name", "fuel_type", "monthly_price", "status", "delivery_location"]:
                key = f"vehicle_{k}"
                row_out.setdefault(key, None)

        # Reservation-felter (kan være None)
        if reservation is not None:
            for k, v in reservation.items():
                row_out[f"reservation_{k}"] = v
        else:
            for k in ["id", "pickup_date", "pickup_location", "status", "actual_pickup_at"]:
                key = f"reservation_{k}"
                row_out.setdefault(key, None)

        joined_rows.append(row_out)

    if not joined_rows:
        print("  Ingen joined rækker dannet (muligvis ingen skader).")
        return

    # Skriv til CSV
    # Saml alle nøgler på tværs, så vi får fuldt header-set
    all_keys = set()
    for r in joined_rows:
        all_keys.update(r.keys())

    # Sorter headers lidt pænt: lease_, vehicle_, reservation_, damage_
    def header_sort_key(k: str):
        if k.startswith("lease_"):
            prio = 0
        elif k.startswith("vehicle_"):
            prio = 1
        elif k.startswith("reservation_"):
            prio = 2
        elif k.startswith("damage_"):
            prio = 3
        else:
            prio = 9
        return (prio, k)

    headers = sorted(all_keys, key=header_sort_key)

    out_path = EXPORT_DIR / "analytics__lease_damage_vehicle.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        for r in joined_rows:
            writer.writerow([r.get(h) for h in headers])

    print(f"  -> Analytics-CSV skrevet til {out_path} ({len(joined_rows)} rækker)")


def main():
    # 1) Eksporter alle .db-filer og tabeller
    db_files = list(ROOT.rglob("*.db"))

    if not db_files:
        print("Ingen .db-filer fundet. Tjek at du kører scriptet i projektroden.")
    else:
        print("Følgende DB-filer behandles:")
        for db in db_files:
            print(f" - {db.relative_to(ROOT)}")

        for db in db_files:
            export_db(db)

    # 2) Lav samlet analytics-join til Tableau mv.
    export_analytics_join()


if __name__ == "__main__":
    main()
