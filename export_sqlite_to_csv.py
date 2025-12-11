import sqlite3
import csv
import pathlib

ROOT = pathlib.Path(__file__).parent

# Hvor skal CSV'erne hen?
EXPORT_DIR = ROOT / "exports_csv"
EXPORT_DIR.mkdir(exist_ok=True)


def export_db(db_path: pathlib.Path):
    print(f"\n=== Ekspoterer DB: {db_path} ===")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Find alle bruger-tabeller (spring system-tabeller over)
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

        # Filnavn: <dbname>__<tablename>.csv
        csv_name = f"{db_path.stem}__{table}.csv"
        csv_path = EXPORT_DIR / csv_name

        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[h] for h in headers])

        print(f"     -> skrevet til {csv_path}")

    conn.close()


def main():
    # Find alle .db filer rekursivt under projektet
    db_files = list(ROOT.rglob("*.db"))

    if not db_files:
        print("Ingen .db-filer fundet. Tjek at du kører scriptet i projektroden.")
        return

    print("Følgende DB-filer behandles:")
    for db in db_files:
        print(f" - {db.relative_to(ROOT)}")

    for db in db_files:
        export_db(db)


if __name__ == "__main__":
    main()
