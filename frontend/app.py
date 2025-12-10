import streamlit as st
import requests
import os
from datetime import date, datetime, time
from streamlit_autorefresh import st_autorefresh
import pathlib




# ---- UI helpers ----
def rki_badge(status: str):
    if not status:
        return "❔ Ukendt"

    status = status.upper()

    colors = {
        "APPROVED": "green",
        "REJECTED": "red",
        "PENDING": "orange",
        "SKIPPED": "gray"
    }

    color = colors.get(status, "gray")
    return f"<span style='color:{color}; font-weight:bold;'>{status}</span>"


# ---- Konfiguration ----
GATEWAY_BASE = os.getenv("GATEWAY_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Bilabonnement – Intern Portal", layout="wide")


# ---- Helper-funktioner ----

def api_post(path, json=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{GATEWAY_BASE}{path}"
    resp = requests.post(url, json=json, headers=headers)
    return resp


def api_get(path, params=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{GATEWAY_BASE}{path}"
    resp = requests.get(url, params=params, headers=headers)
    return resp


def api_patch(path, json=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{GATEWAY_BASE}{path}"
    resp = requests.patch(url, json=json, headers=headers)
    return resp


def do_login(username: str, password: str):
    resp = api_post("/auth/login", json={"username": username, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        return data["token"], data["user"]
    else:
        try:
            msg = resp.json().get("error", resp.text)
        except Exception:
            msg = resp.text
        st.error(f"Login fejlede: {msg}")
        return None, None


def fetch_me(token: str):
    resp = api_get("/auth/me", token=token)
    if resp.status_code == 200:
        return resp.json()
    return None


def init_session_state():
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

        
def load_css_asset(name: str):
    """
    Loader en CSS-fil fra ./assets/<name> og injicerer den i Streamlit.
    """
    css_path = pathlib.Path("assets") / name
    if css_path.exists():
        css = css_path.read_text()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        # Valgfrit: lidt debug hvis filen ikke findes
        st.write(f"Kunne ikke finde CSS fil: {css_path}")


def add_months(start_date: date, months: int) -> date:
    """
    Lægger et antal måneder til en date uden at bruge eksterne libs.
    Bevarer dag i måneden så godt som muligt.
    """
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1

    # find sidste gyldige dag i mål-måneden
    # (håndterer 28–31 dage)
    from calendar import monthrange
    last_day = monthrange(year, month)[1]
    day = min(start_date.day, last_day)

    return date(year, month, day)





# ---- Sidefunktioner ----

def page_dashboard():
    st.header("Dashboard (KPI overblik)")

    if st.session_state.role not in ["FORRET", "LEDELSE", "ADMIN"]:
        st.info("Du har ikke adgang til dashboardet.")
        return
    

    # Auto-refresh hvert 60. sekund
    st.caption("Data opdateres automatisk hvert 60. sekund.")
    st_autorefresh(interval=60_000, key="dashboard_autorefresh")

    # Mulighed for manuelt refresh
    if st.button("Opdater nu"):
        st.rerun()

    resp = api_get("/reporting/kpi/overview", token=st.session_state.token)
    if resp.status_code != 200:
        st.error(f"Kunne ikke hente KPI-data: {resp.text}")
        return

    data = resp.json()
    kpi = data.get("kpi", {})
    st.write(f"Genereret: {data.get('generated_at')}")

    # --- Hent KPI-værdier med defaults ---
    active_leases = kpi.get("active_leases", 0)

    fleet_counts = kpi.get("fleet_status_counts", {}) or {}
    fleet_available = fleet_counts.get("AVAILABLE", 0)
    fleet_leased = fleet_counts.get("LEASED", 0)
    fleet_damaged = fleet_counts.get("DAMAGED", 0)
    fleet_repair = fleet_counts.get("REPAIR", 0)
    fleet_out_of_service = fleet_damaged + fleet_repair

    pickups_today = kpi.get("pickups_today", 0)
    pickups_next_7 = kpi.get("pickups_next_7_days", 0)

    leases_expiring_soon_count = kpi.get("leases_expiring_soon_count", 0)

    open_damages_count = kpi.get("open_damages_count", 0)
    open_damages_total_cost = kpi.get("open_damages_total_cost", 0.0)

    monthly_revenue = kpi.get("monthly_revenue", []) or []
    top_models = kpi.get("top_models", []) or []

    upcoming_pickups = kpi.get("upcoming_pickups", []) or []
    expiring_leases = kpi.get("expiring_leases", []) or []
    recent_damages = kpi.get("recent_damages", []) or []

    # ---------- ØVERSTE KPI-RÆKKER ----------

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Aktive lejeaftaler", active_leases)
    with col2:
        st.metric("Biler i drift (LEASED)", fleet_leased)
    with col3:
        st.metric("Ledige biler (AVAILABLE)", fleet_available)
    with col4:
        st.metric("Ude af drift (DAMAGED + REPAIR)", fleet_out_of_service)

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Afhentninger i dag", pickups_today)
    with col6:
        st.metric("Afhentninger næste 7 dage", pickups_next_7)
    with col7:
        st.metric("Lejeaftaler der udløber snart", leases_expiring_soon_count)
    with col8:
        st.metric("Åbne skader", open_damages_count, f"{open_damages_total_cost:.0f} kr.")

    st.markdown("---")

    # ---------- FLÅDEFORDELING ----------
    st.subheader("Flådefordeling")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        st.write(f"**AVAILABLE:** {fleet_available}")
    with col_f2:
        st.write(f"**LEASED:** {fleet_leased}")
    with col_f3:
        st.write(f"**DAMAGED:** {fleet_damaged}")
    with col_f4:
        st.write(f"**REPAIR:** {fleet_repair}")

    st.markdown("---")

    # ---------- KOMMENDE AFHENTNINGER ----------
    st.subheader("Kommende afhentninger (næste 7 dage)")

    if not upcoming_pickups:
        st.info("Ingen planlagte afhentninger i de næste 7 dage.")
    else:
        for r in upcoming_pickups:
            label = (
                f"Reservation #{r.get('id','?')} – Lease {r.get('lease_id','?')} – "
                f"{r.get('pickup_date','?')} – {r.get('status','')}"
            )
            with st.expander(label):
                st.markdown(f"**Lease ID:** {r.get('lease_id','?')}")
                st.markdown(f"**Afhentningsdato:** {r.get('pickup_date','?')}")
                st.markdown(f"**Afhentningssted:** {r.get('pickup_location') or 'Ukendt'}")
                st.markdown(f"**Status:** {r.get('status','?')}")

    st.markdown("---")

    # ---------- LEASES DER UDLØBER SNART ----------
    st.subheader("Lejeaftaler der udløber snart (næste 30 dage)")

    if not expiring_leases:
        st.info("Ingen lejeaftaler udløber inden for de næste 30 dage.")
    else:
        for l in expiring_leases:
            label = (
                f"Lease #{l.get('id','?')} – {l.get('customer_name','?')} – "
                f"{l.get('car_model','?')} (slut: {l.get('end_date','?')})"
            )
            with st.expander(label):
                st.markdown(f"**Lease ID:** {l.get('id','?')}")
                st.markdown(f"**Kunde:** {l.get('customer_name','?')}")
                st.markdown(f"**Bil:** {l.get('car_model','?')}")
                st.markdown(f"**Slutdato:** {l.get('end_date','?')}")
                st.markdown(f"**Dage til slut:** {l.get('days_to_end','?')}")

    st.markdown("---")

    # ---------- SKADEOVERBLIK ----------
    st.subheader("Skadeoverblik (seneste skader)")

    if not recent_damages:
        st.info("Ingen registrerede skader.")
    else:
        for d in recent_damages:
            label = (
                f"Skade #{d.get('id','?')} – Lease {d.get('lease_id','?')} – "
                f"{d.get('category','?')} – {d.get('status','?')}"
            )
            with st.expander(label):
                st.markdown(f"**Skade ID:** {d.get('id','?')}")
                st.markdown(f"**Lease ID:** {d.get('lease_id','?')}")
                st.markdown(f"**Kategori:** {d.get('category','?')}")
                st.markdown(f"**Estimeret omkostning:** {d.get('estimated_cost','?')} kr.")
                st.markdown(f"**Status:** {d.get('status','?')}")
                st.markdown(f"**Registreret:** {d.get('detected_at','?')}")

    st.markdown("---")

    # ---------- ØKONOMI / OMSÆTNING ----------
    st.subheader("Omsætning pr. måned")

    if not monthly_revenue:
        st.info("Ingen omsætningsdata endnu.")
    else:
        for row in monthly_revenue:
            st.write(f"{row['month']}: {row['total_revenue']:.0f} kr.")

    st.subheader("Top 3 bilmodeller (antal aftaler)")

    if not top_models:
        st.info("Ingen data for bilmodeller endnu.")
    else:
        for row in top_models:
            st.write(f"{row['car_model']}: {row['count']} aftaler")




def page_fleet():
    st.header("Flådeoverblik")

    role = st.session_state.role
    if role not in ["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"]:
        st.info("Du har ikke adgang til flådedata.")
        return

    status_filter = st.selectbox(
        "Status-filter",
        ["(alle)", "AVAILABLE", "LEASED", "DAMAGED", "REPAIR"],
        index=0,
    )

    params = {}
    if status_filter != "(alle)":
        params["status"] = status_filter

    resp = api_get("/fleet/vehicles", params=params, token=st.session_state.token)
    if resp.status_code != 200:
        st.error(f"Kunne ikke hente flådedata: {resp.text}")
        return

    vehicles = resp.json()
    if not vehicles:
        st.info("Ingen biler fundet.")
        return

    for v in vehicles:
        title = f"Bil #{v['id']} – {v.get('model_name', '—')} – {v.get('status', '—')}"
        with st.expander(title):
            st.markdown(f"**Model:** {v.get('model_name', '—')}")
            st.markdown(f"**Brændstof:** {v.get('fuel_type', '—')}")
            st.markdown(f"**Pris pr. måned:** {v.get('monthly_price', '—')} kr.")
            st.markdown(f"**Status:** {v.get('status', '—')}")
            st.markdown(f"**Aktiv lease ID:** {v.get('current_lease_id', '—')}")
            st.markdown(f"**Afhentningssted:** {v.get('delivery_location', '—')}")
            st.markdown(f"**Senest opdateret:** {v.get('updated_at', '—')}")



def page_leases():
    st.header("Lejeaftaler")

    role = st.session_state.role
    if role not in ["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"]:
        st.info("Du har ikke adgang til lejeaftaler.")
        return

    tab_list, tab_create = st.tabs(["Oversigt", "Opret ny aftale"])

    # ---------- OVERSIGT ----------
    with tab_list:
        st.subheader("Alle lejeaftaler")
        resp = api_get("/leases", token=st.session_state.token)
        if resp.status_code != 200:
            st.error(f"Kunne ikke hente lejeaftaler: {resp.text}")
        else:
            leases = resp.json()
            if not leases:
                st.info("Ingen lejeaftaler endnu.")
            else:
                for l in leases:
                    # --- RKI status / ikon til titel ---
                    status = (l.get("rki_status") or "PENDING").upper()
                    status_icon = {
                        "APPROVED": "🟢",
                        "REJECTED": "🔴",
                        "PENDING": "🟠",
                        "SKIPPED": "⚪",
                    }.get(status, "⚪")

                    expander_label = (
                        f"Aftale #{l['id']} – {l['customer_name']} – {l['car_model']} "
                        f"– RKI: {status_icon} {status}"
                    )

                    with st.expander(expander_label):
                        # Basis info
                        st.markdown(
                            f"**Kunde:** {l['customer_name']} ({l.get('customer_email', '')})"
                        )
                        st.markdown(
                            f"**Bil:** {l['car_model']} ({l.get('car_segment', '-')}), "
                            f"Reg.nr: {l.get('car_registration', '—')}"
                        )
                        st.markdown(
                            f"**Periode:** {l['start_date']} → {l['end_date']}"
                        )
                        st.markdown("---")

                                                # --- Flådeinfo / vehicle_id ---
                        vehicle_id = l.get("vehicle_id")

                        if vehicle_id is not None:
                            st.markdown(f"**Tilordnet bil (vehicle_id):** {vehicle_id}")

                            fleet_resp = api_get(
                                f"/fleet/vehicles/{vehicle_id}",
                                token=st.session_state.token,
                            )
                            if fleet_resp.status_code == 200:
                                v = fleet_resp.json()
                                st.markdown("**Flådeinfo:**")
                                st.write(
                                    f"Status: {v.get('status', '—')} | "
                                    f"Model: {v.get('model_name', '—')} | "
                                    f"Brændstof: {v.get('fuel_type', '—')} | "
                                    f"Pris pr. måned: {v.get('monthly_price', '—')} | "
                                    f"Afhentning: {v.get('delivery_location', '—')}"
                                )
                            else:
                                st.write("Kunne ikke hente flådeinfo for bilen.")
                        else:
                            st.markdown("**Tilordnet bil (vehicle_id):** —")

                        st.markdown("---")


                        # --- RKI Section ---
                        st.markdown("### RKI-vurdering")

                        col_left, col_right = st.columns([1, 2])

                        with col_left:
                            st.write("**Status:**")
                            st.write("**Score:**")
                            st.write("**Tjekket:**")

                        with col_right:
                            status_html = rki_badge(status)
                            st.markdown(status_html, unsafe_allow_html=True)
                            st.write(l.get("rki_score", "—"))
                            st.write(l.get("rki_checked_at", "—"))

                        # Farvet summary-box
                        box_color = {
                            "APPROVED": "#1f8f1f22",
                            "REJECTED": "#8f1f1f22",
                            "PENDING": "#f5c54222",
                            "SKIPPED": "#88888822",
                        }.get(status, "#88888822")
                        

                        st.markdown("---")
                        st.markdown("### Afslut lejeaftale")

                        lease_status = l.get("status", "")
                        st.write(f"Nuværende status: **{lease_status}**")

                        if lease_status == "ACTIVE":
                            if st.button("Afslut aftale", key=f"end_lease_{l['id']}"):
                                resp_end = api_patch(
                                    f"/leases/{l['id']}/end",
                                    json={},
                                    token=st.session_state.token,
                                )
                                if resp_end.status_code == 200:
                                    st.success("Lejeaftalen er afsluttet")
                                    st.rerun()
                                else:
                                    st.error(f"Fejl ved afslutning: {resp_end.text}")
                        else:
                            st.info("Aftalen kan kun afsluttes, når den er ACTIVE.")


                        #Tidligere version af RKI check med markdown boks

                        #st.markdown(
                        #    f"""
                        #    <div style='padding:14px; margin-top:12px; border-radius:10px;
                        #         background:{box_color};'>
                        #        <b>RKI Status:</b> {status}<br>
                        #        <b>Score:</b> {l.get("rki_score","—")}<br>
                        #        <b>Tjekket:</b> {l.get("rki_checked_at","—")}
                        #    </div>
                        #    """,
                        #    unsafe_allow_html=True,
                        #)

    # ---------- OPRET NY AFTALE ----------
    with tab_create:
        if role not in ["DATAREG", "LEDELSE", "ADMIN"]:
            st.info("Kun dataregistrering/ledelse/admin kan oprette aftaler.")
        else:
            st.subheader("Opret ny lejeaftale")

            customer_name = st.text_input("Kundenavn")
            customer_email = st.text_input("Kunde-email")
            customer_phone = st.text_input("Kundens telefon")
            customer_cpr = st.text_input("Kundens CPR-nummer")

            # --- Bilvalg baseret på tilgængelige biler i flåden ---
            selected_model = None
            available_models_options = ["(ingen tilgængelige data)", "Anden model (manuel indtastning)"]

            try:
                fleet_resp = api_get(
                    "/fleet/vehicles",
                    params={"status": "AVAILABLE"},
                    token=st.session_state.token,
                )
                if fleet_resp.status_code == 200:
                    vehicles = fleet_resp.json()
                    model_counts = {}
                    for v in vehicles:
                        m = v.get("model_name")
                        if not m:
                            continue
                        model_counts[m] = model_counts.get(m, 0) + 1

                    if model_counts:
                        available_models_options = [
                            f"{m} ({count} tilgængelig)"
                            for m, count in sorted(model_counts.items())
                        ]
                        available_models_options.append("Anden model (manuel indtastning)")
            except Exception as e:
                st.info(f"Kunne ikke hente tilgængelige biler fra flåden: {e}")

            chosen_model_label = st.selectbox(
                "Bilmodel (fra flåden)",
                options=available_models_options,
            )

            if chosen_model_label and chosen_model_label != "(ingen tilgængelige data)" and not chosen_model_label.startswith("Anden model"):
                # label er fx "Peugeot 208 (3 tilgængelig)" → vi splitter på " ("
                selected_model = chosen_model_label.split(" (", 1)[0]

            # Manuel override / fallback
            car_model_manual = st.text_input("Bilmodel (manuel, hvis nødvendig)")

            car_segment = st.text_input("Bilsegment (valgfrit)")
            car_registration = st.text_input("Registreringsnummer (valgfrit)")
            start_date = st.date_input("Startdato")

            lease_months = st.selectbox(
                "Lejeperiode (måneder)",
                options=[12, 24, 36],
                index=0,
            )

        



            if st.button("Gem aftale"):
                # Vælg model i prioriteret rækkefølge:
                # 1) valgt fra flåden, 2) manuel indtastning
                car_model_final = selected_model or (car_model_manual.strip() or None)

                if not car_model_final:
                    st.error("Du skal vælge eller indtaste en bilmodel.")
                else:
                    # Beregn slutdato ud fra startdato + antal måneder
                    end_date = add_months(start_date, lease_months)

                    payload = {
                        "customer_name": customer_name,
                        "customer_email": customer_email,
                        "customer_phone": customer_phone,
                        "customer_cpr": customer_cpr,
                        "car_model": car_model_final,
                        "car_segment": car_segment or None,
                        "car_registration": car_registration or None,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        
                    }
                    resp = api_post("/leases", json=payload, token=st.session_state.token)
                    if resp.status_code == 201:
                        st.success("Aftale oprettet")
                        st.rerun()
                    else:
                        st.error(f"Fejl ved oprettelse: {resp.text}")


def page_reservations():
    st.header("Afhentning af biler")

    role = st.session_state.role
    if role not in ["DATAREG", "FORRET", "LEDELSE", "ADMIN"]:
        st.info("Du har ikke adgang til afhentninger.")
        return

    tab_list, tab_create = st.tabs(["Dagens / kommende afhentninger", "Opret afhentning"])

    # ---------- OVERSIGT ----------
    with tab_list:
        st.subheader("Afhentninger")

        status_filter = st.selectbox(
            "Statusfilter",
            ["Alle", "PENDING", "READY", "PICKED_UP", "CANCELLED"],
            index=0,
        )

        params = {}
        if status_filter != "Alle":
            params["status"] = status_filter

        resp = api_get("/reservations", params=params, token=st.session_state.token)
        if resp.status_code != 200:
            st.error(f"Kunne ikke hente afhentninger: {resp.text}")
        else:
            reservations = resp.json()
            if not reservations:
                st.info("Ingen afhentninger fundet.")
            else:
                today_str = date.today().isoformat()

                for r in reservations:
                    pickup_date = r.get("pickup_date", "")
                    lease_id = r.get("lease_id")
                    status = r.get("status", "")
                    location = r.get("pickup_location", "")

                    label = f"Reservation #{r['id']} – Lease {lease_id} – {pickup_date} – {status}"
                    if pickup_date.startswith(today_str):
                        label = f"[I DAG] {label}"

                    with st.expander(label):
                        st.markdown(f"**Lease ID:** {lease_id}")
                        st.markdown(f"**Afhentningsdato:** {pickup_date}")
                        st.markdown(f"**Lokation:** {location}")
                        st.markdown(f"**Status:** {status}")

                        actual_pickup_at = r.get("actual_pickup_at")
                        if actual_pickup_at:
                            st.markdown(f"**Faktisk afhentet:** {actual_pickup_at}")

                        st.markdown("---")
                        st.markdown("**Opdater status**")

                        possible_statuses = ["PENDING", "READY", "PICKED_UP", "CANCELLED"]
                        try:
                            current_index = possible_statuses.index(status)
                        except ValueError:
                            current_index = 0

                        new_status = st.selectbox(
                            "Ny status",
                            possible_statuses,
                            index=current_index,
                            key=f"reservation_status_{r['id']}",
                        )

                        if st.button("Gem status", key=f"reservation_status_btn_{r['id']}"):
                            resp_update = api_patch(
                                f"/reservations/{r['id']}/status",
                                json={"status": new_status},
                                token=st.session_state.token,
                            )
                            if resp_update.status_code == 200:
                                st.success("Status opdateret")
                                st.rerun()
                            else:
                                st.error(f"Fejl ved opdatering: {resp_update.text}")

    # ---------- OPRET NY AFHENTNING ----------
    with tab_create:
        if role not in ["DATAREG", "LEDELSE", "ADMIN"]:
            st.info("Kun dataregistrering/ledelse/admin kan oprette afhentninger.")
            return

        st.subheader("Opret ny afhentning")

        # Hent aktive lejeaftaler (vi bruger vehicle_id herfra)
        active_leases: list[dict] = []
        try:
            leases_resp = api_get("/leases", params={"status": "ACTIVE"}, token=st.session_state.token)
            if leases_resp.status_code == 200:
                active_leases = leases_resp.json()
            else:
                st.warning(f"Kunne ikke hente aktive lejeaftaler: {leases_resp.text}")
        except Exception as e:
            st.warning(f"Fejl ved hentning af aktive lejeaftaler: {e}")

        if not active_leases:
            st.info("Der findes ingen aktive lejeaftaler.")
            return

        leases_options = [
            f"Lease #{l['id']} – {l['customer_name']} – {l['car_model']} (vehicle_id={l.get('vehicle_id')})"
            for l in active_leases
        ]
        leases_map = {label: l for label, l in zip(leases_options, active_leases)}

        selected_label = st.selectbox("Vælg lejeaftale", options=leases_options)
        selected_lease = leases_map[selected_label]
        lease_id = selected_lease["id"]
        vehicle_id = selected_lease.get("vehicle_id")

        pickup_date_input = st.date_input("Afhentningsdato", value=date.today())
        pickup_time_input = st.time_input("Afhentningstidspunkt", value=time(10, 0))

        # Vis lokation som info (kommer fra Fleet – backend bruger samme logik)
        default_location = ""
        if vehicle_id is not None:
            try:
                v_resp = api_get(f"/fleet/vehicles/{vehicle_id}", token=st.session_state.token)
                if v_resp.status_code == 200:
                    v = v_resp.json()
                    default_location = v.get("delivery_location") or ""
            except Exception as e:
                st.info(f"Kunne ikke hente lokation fra flåden: {e}")

        st.markdown(f"**Afhentningssted (fra flåde):** {default_location or 'Ukendt'}")

        if st.button("Gem afhentning"):
            pickup_dt = datetime.combine(pickup_date_input, pickup_time_input)
            payload = {
                "lease_id": lease_id,
                "vehicle_id": vehicle_id,
                "pickup_date": pickup_dt.isoformat(),
                # pickup_location sendes ikke – backend finder den via Fleet
            }
            resp = api_post("/reservations", json=payload, token=st.session_state.token)
            if resp.status_code == 201:
                st.success("Afhentning oprettet")
                st.rerun()
            else:
                st.error(f"Fejl ved oprettelse: {resp.text}")


def page_damages():
    st.header("Skader")

    role = st.session_state.role
    if role not in ["SKADE", "FORRET", "LEDELSE", "ADMIN"]:
        st.info("Du har ikke adgang til skader.")
        return

    tab_list, tab_create = st.tabs(["Oversigt", "Registrer skade"])

    with tab_list:
        resp = api_get("/damages", token=st.session_state.token)
        if resp.status_code != 200:
            st.error(f"Kunne ikke hente skader: {resp.text}")
        else:
            damages = resp.json()
            if not damages:
                st.info("Ingen skader registreret endnu.")
            else:
                for d in damages:
                    with st.expander(f"Skade #{d['id']} – Lease {d['lease_id']} – {d['category']}"):
                        st.write(d)

    with tab_create:
        if role not in ["SKADE", "LEDELSE", "ADMIN"]:
            st.info("Kun skade-rolle/ledelse/admin kan registrere skader.")
        else:
            st.subheader("Registrer skade")

            # Forsøg at hente aktive lejeaftaler til dropdown
            leases_options = []
            leases_map = {}

            try:
                leases_resp = api_get("/leases", params={"status": "ACTIVE"}, token=st.session_state.token)
                if leases_resp.status_code == 200:
                    leases_data = leases_resp.json()
                    for l in leases_data:
                        label = (
                            f"Lease #{l['id']} – {l.get('customer_name','?')} – "
                            f"{l.get('car_model','?')} "
                            f"(vehicle_id={l.get('vehicle_id','-')})"
                        )
                        leases_options.append(label)
                        leases_map[label] = {
                            "lease_id": l["id"],
                            "vehicle_id": l.get("vehicle_id"),
                        }
            except Exception as e:
                st.warning(f"Kunne ikke hente aktive lejeaftaler: {e}")

            use_manual = False

            if leases_options:
                selected_label = st.selectbox(
                    "Vælg aktiv lejeaftale",
                    options=leases_options,
                )
                selected = leases_map[selected_label]
                lease_id = selected["lease_id"]
                vehicle_id = selected["vehicle_id"]
                st.write(f"Valgt lease ID: {lease_id}, vehicle_id: {vehicle_id}")
            else:
                st.info("Ingen aktive lejeaftaler fundet – indtast lease ID manuelt.")
                use_manual = True
                lease_id = st.number_input("Lease ID", min_value=1, step=1)
                vehicle_id = st.number_input("Vehicle ID (valgfri)", min_value=0, step=1)

            category = st.selectbox("Kategori", ["kosmetisk", "mellem", "alvorlig"])
            description = st.text_area("Beskrivelse")
            estimated_cost = st.number_input("Estimeret omkostning", min_value=0.0, step=500.0)

            if st.button("Gem skade"):
                if use_manual and not lease_id:
                    st.error("Lease ID skal udfyldes.")
                else:
                    payload = {
                        "lease_id": int(lease_id),
                        "category": category,
                        "description": description,
                        "estimated_cost": estimated_cost,
                    }
                    # kun send vehicle_id hvis det er sat/gyldigt
                    if vehicle_id and int(vehicle_id) > 0:
                        payload["vehicle_id"] = int(vehicle_id)

                    resp = api_post("/damages", json=payload, token=st.session_state.token)
                    if resp.status_code == 201:
                        st.success("Skade registreret")
                    else:
                        st.error(f"Fejl ved oprettelse: {resp.text}")



def page_admin():
    st.header("Admin – Brugere & Roller")

    role = st.session_state.role
    if role not in ["ADMIN", "LEDELSE"]:
        st.info("Du har ikke adgang til admin-området.")
        return

    tab_list, tab_create = st.tabs(["Brugerliste", "Opret bruger"])

    with tab_list:
        resp = api_get("/auth/users", token=st.session_state.token)
        if resp.status_code != 200:
            st.error(f"Kunne ikke hente brugere: {resp.text}")
        else:
            users = resp.json()
            if not users:
                st.info("Ingen brugere fundet.")
            else:
                for u in users:
                    with st.expander(f"#{u['id']} – {u['username']} ({u['role']})"):
                        st.write(u)
                        new_role = st.selectbox(
                            "Ny rolle",
                            ["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"],
                            index=["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"].index(
                                u["role"]
                            ) if u["role"] in ["DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"] else 0,
                            key=f"role_select_{u['id']}",
                        )
                        if st.button("Opdater rolle", key=f"update_role_{u['id']}"):
                            resp2 = api_patch(
                                f"/auth/users/{u['id']}/role",
                                json={"role": new_role},
                                token=st.session_state.token,
                            )
                            if resp2.status_code == 200:
                                st.success("Rolle opdateret – reload siden")
                            else:
                                st.error(f"Fejl: {resp2.text}")

    with tab_create:
        st.subheader("Opret ny medarbejder")
        username = st.text_input("Brugernavn")
        email = st.text_input("Email (valgfri)")
        password = st.text_input("Kodeord", type="password")
        role_new = st.selectbox("Rolle", ["DATAREG", "SKADE", "FORRET", "LEDELSE"])

        if st.button("Opret bruger"):
            payload = {
                "username": username,
                "password": password,
                "email": email or "",
                "role": role_new,
            }
            resp = api_post("/auth/users", json=payload, token=st.session_state.token)
            if resp.status_code == 201:
                st.success("Bruger oprettet")
            else:
                st.error(f"Fejl ved oprettelse: {resp.text}")


# ---- Layout & navigation ----

def render_sidebar():
    user = st.session_state.user
    role = st.session_state.role

    with st.sidebar:
        if user:
            st.write(f"Logget ind som: **{user['username']}** ({role})")
            st.markdown("### Menu")

            menu_options = {}

            # Dashboard kun til FORRET, LEDELSE, ADMIN
            if role in ("FORRET", "LEDELSE", "ADMIN"):
                menu_options["Dashboard"] = "Dashboard"

            # Fælles menupunkter
            menu_options["Lejeaftaler"] = "Lejeaftaler"
            menu_options["Afhentning"] = "Afhentning"
            menu_options["Skader"] = "Skader"

            # Flåde-menu til relevante roller
            if role in ("DATAREG", "SKADE", "FORRET", "LEDELSE", "ADMIN"):
                menu_options["Flåde"] = "Flåde"

            # Admin kun til ADMIN/LEDELSE
            if role in ("ADMIN", "LEDELSE"):
                menu_options["Admin"] = "Admin"

            keys = list(menu_options.keys())
            labels = list(menu_options.values())

            current_page = st.session_state.page or keys[0]
            if current_page not in keys:
                current_page = keys[0]

            try:
                default_idx = keys.index(current_page)
            except ValueError:
                default_idx = 0

            choice = st.radio(
                "Navigation",
                labels,
                index=default_idx,
            )

            selected_page = keys[labels.index(choice)]
            st.session_state.page = selected_page

            if st.button("Log ud"):
                st.session_state.token = None
                st.session_state.user = None
                st.session_state.role = None
                st.session_state.page = keys[0]
                st.rerun()
        else:
            st.info("Log ind for at få adgang.")



def render_login():
    st.title("Bilabonnement – Intern Portal")
    st.subheader("Log ind")

    username = st.text_input("Brugernavn")
    password = st.text_input("Kodeord", type="password")

    if st.button("Login"):
        token, user = do_login(username, password)
        if token:
            st.session_state.token = token
            st.session_state.user = user
            st.session_state.role = user["role"]
            st.success("Login lykkedes")
            st.rerun()


def main():
    init_session_state()
    load_css_asset("theme.css")  # loader frontend/assets/theme.css

    if st.session_state.token is None:
        render_login()
    else:
        # Sørg for at vi har opdateret brugerinfo
        if st.session_state.user is None:
            me = fetch_me(st.session_state.token)
            if me:
                st.session_state.user = me
                st.session_state.role = me["role"]

        render_sidebar()

        page = st.session_state.page

        if page == "Dashboard":
            page_dashboard()
        elif page == "Flåde":
            page_fleet()
        elif page == "Lejeaftaler":
            page_leases()
        elif page == "Afhentning":
            page_reservations()
        elif page == "Skader":
            page_damages()
        elif page == "Admin":
            page_admin()
        else:
            st.write("Ukendt side.")


if __name__ == "__main__":
    main()
