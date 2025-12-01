from flask import Flask, jsonify
import os
import requests
from collections import Counter, defaultdict
from datetime import datetime

app = Flask(__name__)

# Gateway base URL - ReportingService kalder gennem gateway
GATEWAY_BASE = os.getenv("GATEWAY_BASE_URL", "http://localhost:8000")


def fetch_leases():
    """Hent alle leases via gatewayen."""
    url = f"{GATEWAY_BASE}/leases"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching leases: {e}")
        return []


def fetch_damages():
    """Hent alle damages via gatewayen."""
    url = f"{GATEWAY_BASE}/damages"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching damages: {e}")
        return []


def compute_active_leases(leases):
    """KPI 1: Antal aktive abonnementer (status = ACTIVE)."""
    return sum(1 for l in leases if l.get("status") == "ACTIVE")


def compute_monthly_revenue(leases):
    """
    KPI 2: Omsætning pr. måned (baseret på monthly_price og start_date).
    Simpelt: summer monthly_price pr. YYYY-MM (start_date).
    """
    revenue_per_month = defaultdict(float)

    for l in leases:
        try:
            start_date_str = l.get("start_date")
            monthly_price = float(l.get("monthly_price", 0))
            if not start_date_str:
                continue
            # forventer format "YYYY-MM-DD" eller lignende
            month_key = start_date_str[:7]  # "YYYY-MM"
            revenue_per_month[month_key] += monthly_price
        except Exception:
            continue

    # Sortér efter måned
    result = [
        {"month": month, "total_revenue": total}
        for month, total in sorted(revenue_per_month.items())
    ]
    return result


def compute_completed_with_damage(leases, damages):
    """
    KPI 3: Antal afsluttede lejeaftaler med skader.
    Vi ser på leases med status COMPLETED og mindst én damage med samme lease_id.
    """
    completed_ids = {l["id"] for l in leases if l.get("status") == "COMPLETED"}
    damage_lease_ids = {d["lease_id"] for d in damages if "lease_id" in d}

    affected_leases = completed_ids.intersection(damage_lease_ids)
    return len(affected_leases)


def compute_avg_damage_cost(damages):
    """
    KPI 4: Gennemsnitlig skadesomkostning.
    Simpelt gennemsnit af estimated_cost.
    """
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
    """
    KPI 5: Top N mest brugte bilmodeller (baseret på car_model).
    """
    models = [l.get("car_model") for l in leases if l.get("car_model")]
    counter = Counter(models)
    most_common = counter.most_common(top_n)
    return [{"car_model": m, "count": c} for m, c in most_common]


@app.get("/health")
def health():
    return {"status": "ok", "service": "reporting_service"}


@app.get("/reporting/kpi/overview")
def kpi_overview():
    """
    Samlet endpoint til ledelsesdashboardet.
    """
    leases = fetch_leases()
    damages = fetch_damages()

    kpi = {}

    kpi["active_leases"] = compute_active_leases(leases)
    kpi["monthly_revenue"] = compute_monthly_revenue(leases)
    kpi["completed_leases_with_damage"] = compute_completed_with_damage(leases, damages)
    kpi["avg_damage_cost"] = compute_avg_damage_cost(damages)
    kpi["top_models"] = compute_top_models(leases)

    generated_at = datetime.utcnow().isoformat()
    return jsonify({"generated_at": generated_at, "kpi": kpi})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
