from flask import Flask, jsonify
import os
import requests
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta

app = Flask(__name__)

# ---- Base-URL'er til mikrotjenester (via Docker-netværk) ----
LEASE_BASE = os.getenv("LEASE_BASE_URL", "http://lease_service:5002")
DAMAGE_BASE = os.getenv("DAMAGE_BASE_URL", "http://damage_service:5003")
FLEET_BASE = os.getenv("FLEET_BASE_URL", "http://fleet_service:5006")
RESERVATION_BASE = os.getenv("RESERVATION_BASE_URL", "http://reservation_service:5007")


# --------- HJÆLPE-FUNKTIONER TIL FETCH ---------


def safe_get(url, params=None):
    """Wrapper om requests.get med simpel fejl-håndtering."""
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[REPORTING] Error fetching {url}: {e}")
        return []


def fetch_leases():
    return safe_get(f"{LEASE_BASE}/leases")


def fetch_damages():
    return safe_get(f"{DAMAGE_BASE}/damages")


def fetch_fleet():
    return safe_get(f"{FLEET_BASE}/vehicles")


def fetch_reservations():
    return safe_get(f"{RESERVATION_BASE}/reservations")


# --------- KPI-BEREGNINGER ---------


def compute_active_leases(leases):
    """Antal aktive abonnementer (status = ACTIVE)."""
    return sum(1 for l in leases if l.get("status") == "ACTIVE")


def compute_monthly_revenue(leases):
    """
    Omsætning pr. måned (baseret på monthly_price og start_date).
    NB: hvis monthly_price mangler (vi bruger fleet price), kan dette være 0.
    """
    revenue_per_month = defaultdict(float)

    for l in leases:
        try:
            start_date_str = l.get("start_date")
            monthly_price = float(l.get("monthly_price", 0) or 0)
            if not start_date_str:
                continue
            month_key = start_date_str[:7]  # "YYYY-MM"
            revenue_per_month[month_key] += monthly_price
        except Exception:
            continue

    return [
        {"month": month, "total_revenue": total}
        for month, total in sorted(revenue_per_month.items())
    ]


def compute_completed_with_damage(leases, damages):
    """
    (Evt. ekstra KPI) Antal afsluttede lejeaftaler med skader.
    """
    completed_ids = {l["id"] for l in leases if l.get("status") == "COMPLETED"}
    damage_lease_ids = {d["lease_id"] for d in damages if "lease_id" in d}
    return len(completed_ids.intersection(damage_lease_ids))


def compute_avg_damage_cost(damages):
    """Gennemsnitlig skadesomkostning."""
    costs = []
    for d in damages:
        try:
            cost = float(d.get("estimated_cost", 0))
            costs.append(cost)
        except Exception:
            continue
    if not costs:
        return 0.0
    return sum(costs) / len(costs)


def compute_top_models(leases, top_n=3):
    """Top N mest brugte bilmodeller."""
    models = [l.get("car_model") for l in leases if l.get("car_model")]
    counter = Counter(models)
    return [{"car_model": m, "count": c} for m, c in counter.most_common(top_n)]


def compute_fleet_status_counts(vehicles):
    """Optælling pr. flådestatus."""
    counts = defaultdict(int)
    for v in vehicles:
        status = (v.get("status") or "UNKNOWN").upper()
        counts[status] += 1
    return dict(counts)


def compute_pickup_kpis(reservations):
    """
    Afhentninger i dag / næste 7 dage + liste over kommende afhentninger.
    """
    today = date.today()
    seven_days = today + timedelta(days=7)

    pickups_today = 0
    pickups_next_7 = 0
    upcoming = []

    for r in reservations:
        pickup_str = r.get("pickup_date")
        if not pickup_str:
            continue
        try:
            pickup_dt = datetime.fromisoformat(pickup_str)
            pickup_date = pickup_dt.date()
        except Exception:
            continue

        if pickup_date == today:
            pickups_today += 1
        if today <= pickup_date <= seven_days:
            pickups_next_7 += 1
            upcoming.append(r)

    # sortér kommende efter dato
    upcoming.sort(key=lambda r: r.get("pickup_date", ""))
    return pickups_today, pickups_next_7, upcoming


def compute_expiring_leases(leases, days=30):
    """
    Lejeaftaler der udløber inden for X dage.
    Returnerer både antal og en liste med detaljer.
    """
    today = date.today()
    limit = today + timedelta(days=days)

    expiring = []

    for l in leases:
        end_str = l.get("end_date")
        if not end_str:
            continue
        try:
            end_dt = datetime.fromisoformat(end_str).date()
        except Exception:
            continue

        if today <= end_dt <= limit:
            days_to_end = (end_dt - today).days
            item = dict(l)
            item["days_to_end"] = days_to_end
            expiring.append(item)

    expiring.sort(key=lambda x: x.get("end_date", ""))
    return len(expiring), expiring


def compute_open_damages(damages):
    """
    Åbne skader (status != CLOSED).
    Returnerer antal, total estimeret omkostning og en liste over seneste skader.
    """
    open_list = []
    total_cost = 0.0

    for d in damages:
        status = (d.get("status") or "").upper()
        if status == "CLOSED":
            continue
        open_list.append(d)
        try:
            total_cost += float(d.get("estimated_cost", 0) or 0)
        except Exception:
            continue

    # sortér seneste først
    open_list.sort(key=lambda d: d.get("detected_at", ""), reverse=True)
    return len(open_list), total_cost, open_list


# --------- API-ENDPOINTS ---------


@app.get("/health")
def health():
    return {"status": "ok", "service": "reporting_service"}


@app.get("/reporting/kpi/overview")
def kpi_overview():
    """
    Samlet endpoint til ledelsesdashboardet.
    Henter data fra de andre mikrotjenester og beregner KPI'er.
    """

    leases = fetch_leases()
    damages = fetch_damages()
    vehicles = fetch_fleet()
    reservations = fetch_reservations()

    kpi = {}

    # Grund-KPI'er
    kpi["active_leases"] = compute_active_leases(leases)
    kpi["monthly_revenue"] = compute_monthly_revenue(leases)
    kpi["completed_leases_with_damage"] = compute_completed_with_damage(leases, damages)
    kpi["avg_damage_cost"] = compute_avg_damage_cost(damages)
    kpi["top_models"] = compute_top_models(leases)

    # Flåde
    kpi["fleet_status_counts"] = compute_fleet_status_counts(vehicles)

    # Afhentninger
    pickups_today, pickups_next_7, upcoming_pickups = compute_pickup_kpis(reservations)
    kpi["pickups_today"] = pickups_today
    kpi["pickups_next_7_days"] = pickups_next_7
    kpi["upcoming_pickups"] = upcoming_pickups

    # Leases der udløber snart
    expiring_count, expiring_leases = compute_expiring_leases(leases, days=30)
    kpi["leases_expiring_soon_count"] = expiring_count
    kpi["expiring_leases"] = expiring_leases

    # Skader
    open_count, total_cost, recent_open = compute_open_damages(damages)
    kpi["open_damages_count"] = open_count
    kpi["open_damages_total_cost"] = total_cost
    kpi["recent_damages"] = recent_open[:5]  # begræns til fx 5

    generated_at = datetime.utcnow().isoformat()
    return jsonify({"generated_at": generated_at, "kpi": kpi})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
