import streamlit as st
import requests
import os


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


# ---- Sidefunktioner ----

def page_dashboard():
    st.header("Dashboard (KPI overblik)")

    if st.session_state.role not in ["FORRET", "LEDELSE", "ADMIN", "DATAREG", "SKADE"]:
        st.info("Du har ikke adgang til dashboardet.")
        return

    resp = api_get("/reporting/kpi/overview", token=st.session_state.token)
    if resp.status_code != 200:
        st.error(f"Kunne ikke hente KPI-data: {resp.text}")
        return

    data = resp.json()
    kpi = data.get("kpi", {})
    st.write(f"Genereret: {data.get('generated_at')}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Aktive abonnementer", kpi.get("active_leases", 0))
    with col2:
        st.metric("Aftaler med skader (afsluttede)", kpi.get("completed_leases_with_damage", 0))
    with col3:
        st.metric("Gns. skadesomkostning", f"{kpi.get('avg_damage_cost', 0):.0f} kr.")

    st.subheader("Omsætning pr. måned")
    for row in kpi.get("monthly_revenue", []):
        st.write(f"{row['month']}: {row['total_revenue']} kr.")

    st.subheader("Top 3 bilmodeller")
    for row in kpi.get("top_models", []):
        st.write(f"{row['car_model']}: {row['count']} aftaler")


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
                        st.markdown(
                            f"**Pris:** {l['monthly_price']} kr./md"
                        )
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

                        st.markdown(
                            f"""
                            <div style='padding:14px; margin-top:12px; border-radius:10px;
                                 background:{box_color};'>
                                <b>RKI Status:</b> {status}<br>
                                <b>Score:</b> {l.get("rki_score","—")}<br>
                                <b>Tjekket:</b> {l.get("rki_checked_at","—")}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

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
            car_model = st.text_input("Bilmodel")
            car_segment = st.text_input("Bilsegment (valgfrit)")
            car_registration = st.text_input("Registreringsnummer (valgfrit)")
            start_date = st.date_input("Startdato")
            end_date = st.date_input("Slutdato")
            monthly_price = st.number_input("Månedlig pris", min_value=0.0, step=500.0)

            if st.button("Gem aftale"):
                payload = {
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "customer_phone": customer_phone,
                    "customer_cpr": customer_cpr,
                    "car_model": car_model,
                    "car_segment": car_segment or None,
                    "car_registration": car_registration or None,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "monthly_price": monthly_price,
                }
                resp = api_post("/leases", json=payload, token=st.session_state.token)
                if resp.status_code == 201:
                    st.success("Aftale oprettet")
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
            lease_id = st.number_input("Lease ID", min_value=1, step=1)
            category = st.selectbox("Kategori", ["kosmetisk", "mellem", "alvorlig"])
            description = st.text_area("Beskrivelse")
            estimated_cost = st.number_input("Estimeret omkostning", min_value=0.0, step=500.0)

            if st.button("Gem skade"):
                payload = {
                    "lease_id": int(lease_id),
                    "category": category,
                    "description": description,
                    "estimated_cost": estimated_cost,
                }
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

            # Byg menuen (admin kun for ADMIN/LEDELSE)
            menu_options = {
                "Dashboard": "📊 Dashboard",
                "Lejeaftaler": "🚗 Lejeaftaler",
                "Skader": "🛠️ Skader",
            }
            if role in ("ADMIN", "LEDELSE"):
                menu_options["Admin"] = "👤 Admin"

            keys = list(menu_options.keys())
            labels = list(menu_options.values())

            # Find default index ud fra nuværende side
            current_page = st.session_state.page or "Dashboard"
            try:
                default_idx = keys.index(current_page)
            except ValueError:
                default_idx = 0

            choice = st.radio(
                "Navigation",
                labels,
                index=default_idx,
            )

            # Reverse lookup: label -> key
            selected_page = keys[labels.index(choice)]
            st.session_state.page = selected_page

            if st.button("Log ud"):
                st.session_state.token = None
                st.session_state.user = None
                st.session_state.role = None
                st.session_state.page = "Dashboard"
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
        elif page == "Lejeaftaler":
            page_leases()
        elif page == "Skader":
            page_damages()
        elif page == "Admin":
            page_admin()
        else:
            st.write("Ukendt side.")


if __name__ == "__main__":
    main()
