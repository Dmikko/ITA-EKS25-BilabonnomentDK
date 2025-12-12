# TL;DR

Dette projekt er en **microservice-baseret intern portal** for Bilabonnement.dk,  
der digitaliserer og automatiserer centrale processer som:

- Lejeaftaler
- Flådestyring
- Afhentning af biler
- Skadeshåndtering
- Rapportering og KPI’er

Løsningen består af selvstændige services, en API-gateway og et Streamlit-frontend
med rollebaseret adgang for medarbejdere.

Formålet er at erstatte manuelle Excel-processer med en skalerbar, datadrevet arkitektur.

---

# Install’n’Go

## Forudsætninger
- Docker
- Docker Compose
- Portene **5001–5007, 8000 og 8501** skal være ledige

---

## Start systemet

Fra projektets root-mappe:

```bash
docker compose build
docker compose up


Adgang til systemet
Frontend (Streamlit):
http://localhost:8501
API Gateway:
http://localhost:8000

Testbrugere
Der er oprettet faste testbrugere – én pr. rolle:
Rolle  | Brugernavn |Password
ADMIN  |admin       |admin
LEDELSE|ledelse     |ledelse
FORRET |forret      |forret
DATAREG|data        |data
SKADE  |skade       |skade


Hurtigt overblik over services
Service
Port
auth_service
5001
lease_service
5002
damage_service
5003
reporting_service
5004
rki_service
5005
fleet_service
5006
reservation_service
5007
gateway
8000
frontend (Streamlit)
8501


Stop systemet
docker compose down

Alle data bevares via mounted SQLite-databaser.

---


















# Bilabonnement.dk – Digitalisering af interne processer  
**Microservice-baseret system med API Gateway, Streamlit-frontend og SQLite**

## Projektets formål
Dette projekt har til formål at designe og implementere en digital, microservice-baseret løsning, der understøtter og automatiserer centrale interne processer hos Bilabonnement.dk.  

Løsningen erstatter manuelle arbejdsgange og Excel-baseret datahåndtering med et sammenhængende system, der forbedrer:
- datakvalitet
- sporbarhed
- procesoverblik
- skalerbarhed
- beslutningsgrundlag via dashboards

Projektet er udviklet som en del af **ITA EKS 25** og kombinerer forretningsanalyse, procesmodellering (AS-IS / TO-BE BPMN) og softwarearkitektur.

---

## Overordnet beskrivelse
Systemet er opbygget som en **microservice-arkitektur**, hvor hver forretningsfunktion er isoleret i sin egen service med:
- eget ansvar
- eget API
- egen database (SQLite)

Al kommunikation mellem frontend og services sker via en **API Gateway**, som fungerer som single entrypoint og sikrer:
- entydig routing
- ensartet fejlhåndtering
- klar adskillelse mellem UI og backend

Frontend er implementeret i **Streamlit** og fungerer som en intern portal for medarbejdere.

---

## Forretningskontekst
Bilabonnement.dk håndterer i dag flere interne processer manuelt, herunder:
- oprettelse og administration af lejeaftaler
- flådestyring og bilstatus
- afhentning og aflevering af biler
- skadeshåndtering
- rapportering og ledelsesoverblik

Projektets løsning adresserer disse processer gennem digitalisering og systemunderstøttelse med udgangspunkt i TO-BE BPMN-modeller.

---

## Arkitektur – overblik
Systemet består af følgende hovedkomponenter:

- **Frontend (Streamlit)**
  - Intern portal for medarbejdere
  - Rollebaseret adgang via JWT
  - Dashboards, overblik og registrering

- **API Gateway**
  - Single entrypoint for frontend
  - Proxy til alle backend-services
  - Ensartet håndtering af upstream-fejl

- **Backend services (Flask)**
  - Auth Service (brugere og roller)
  - Lease Service (lejeaftaler)
  - Fleet Service (flåde og bilstatus)
  - Reservation Service (afhentning)
  - Damage Service (skader)
  - Reporting Service (KPI’er)
  - RKI Service (simuleret kreditcheck)

- **Databaser**
  - SQLite pr. service (ingen delt database)
  - Reporting Service er stateless og læser data via gateway

---

## Roller og adgang
Systemet anvender rollebaseret adgangsstyring. Følgende roller er defineret:

- **DATAREG** – dataregistrering (aftaler, afhentning)
- **SKADE** – skadeshåndtering
- **FORRET** – forretningsbrugere
- **LEDELSE** – ledelsesoverblik og dashboard
- **ADMIN** – brugere og roller

Roller afgør:
- hvilke menupunkter der er synlige
- hvilke handlinger der er tilladt i frontend

---



(Kørsel, Docker Compose og service-oversigt)
## Kørsel af projektet (lokalt)
Projektet er containeriseret og kan køres lokalt via **Docker Compose**.  
Alle services bygges og startes samlet, inklusive databaser og frontend.

### Forudsætninger
- Docker
- Docker Compose
- Git

---

## Start projektet
Fra projektets root-mappe:

```bash
docker-compose up --build

Efter opstart er systemet tilgængeligt på:
Frontend (Streamlit): http://localhost:8501
API Gateway: http://localhost:8000
Alle backend-services kører i separate containere og tilgås kun via gatewayen.

Testbrugere (login)
Følgende brugere er prædefineret i AuthService og svarer direkte til deres rolle:
Rolle  | Brugernavn |Password
ADMIN  |admin       |admin
LEDELSE|ledelse     |ledelse
FORRET |forret      |forret
DATAREG|data        |data
SKADE  |skade       |skade

Service-porte
Hver service kører på sin egen port og har sit eget ansvarsområde:
Service
Port
auth_service
5001
lease_service
5002
damage_service
5003
reporting_service
5004
rki_service
5005
fleet_service
5006
reservation_service
5007
gateway
8000
frontend (Streamlit)
8501


Docker Compose – arkitekturprincipper
Projektets Docker Compose-opsætning følger disse principper:
Én container pr. service
Én SQLite-database pr. service
Ingen delt database
Frontend kommunikerer udelukkende med API Gateway
Reporting Service er stateless
Gateway håndterer al routing og fejlhåndtering
SQLite-databaser mountes som volumes, så data bevares mellem genstarter.

Services – overblik
Frontend (Streamlit)
Intern medarbejderportal
Rollebaseret navigation
Dashboard, lejeaftaler, flåde, afhentning, skader og admin
Al kommunikation sker via API Gateway

API Gateway
Single entrypoint for frontend
Proxy til alle backend-services
Ensartet JSON-fejl ved nedbrud i upstream services
Ingen forretningslogik

Auth Service
Brugere og roller
JWT-baseret login
Rolleopdatering
Central autorisation

Lease Service
Oprettelse og administration af lejeaftaler
Tildeling af biler via Fleet Service
Automatisk statusstyring
Afslutning af aftaler

Fleet Service
Flådeoversigt
Bilstatus (AVAILABLE, LEASED, DAMAGED, REPAIR)
Priser, brændstof, afhentningslokation
Binding mellem bil og aktiv lease

Reservation Service
Afhentning af biler
Statusflow: PENDING → READY → PICKED_UP
Lokation hentes automatisk fra Fleet Service
Understøtter TO-BE BPMN for afhentning

Damage Service
Registrering af skader
Kategorisering og omkostninger
Kobling til lease og vehicle_id
Automatisk opdatering af bilstatus i Fleet

Reporting Service
KPI-beregning til dashboard
Læser data via gateway
Ingen egen database
Understøtter ledelsesoverblik

RKI Service
Simuleret kreditvurdering
Asynkront kald fra Lease Service
Returnerer APPROVED / REJECTED



## API-struktur og Gateway-routing

Systemet benytter en **API Gateway** som eneste indgangspunkt for frontend og eksterne kald.  
Alle backend-services eksponeres **kun internt**, og gatewayen fungerer som proxy.

Frontend → Gateway → Backend Services

---

## Gateway – ansvar
API Gatewayen har følgende ansvar:

- Én fælles adgang til alle services
- Central routing
- Ensartet fejlhåndtering (503 ved utilgængelige services)
- Ingen forretningslogik
- Ingen datalagring

---

## Health checks
Alle services stiller et `/health` endpoint til rådighed:

```http
GET /health

Respons:
{
  "status": "ok",
  "service": "<service_name>"
}


## Auth routes (via Gateway)

| Metode | Endpoint                | Beskrivelse        |
| ------ | ----------------------- | ------------------ |
| POST   | `/auth/login`           | Login og JWT       |
| GET    | `/auth/me`              | Hent aktuel bruger |
| GET    | `/auth/users`           | Liste over brugere |
| POST   | `/auth/users`           | Opret ny bruger    |
| PATCH  | `/auth/users/{id}/role` | Skift rolle        |

**Roller:**
`DATAREG`, `SKADE`, `FORRET`, `LEDELSE`, `ADMIN`

---

## Lease routes

| Metode | Endpoint              | Beskrivelse            |
| ------ | --------------------- | ---------------------- |
| GET    | `/leases`             | Liste over lejeaftaler |
| GET    | `/leases/{id}`        | Hent specifik aftale   |
| POST   | `/leases`             | Opret ny aftale        |
| PATCH  | `/leases/{id}/status` | Skift status           |
| PATCH  | `/leases/{id}/end`    | Afslut aftale          |

**Ved oprettelse af lease:**

* Fleet Service anvendes til at allokere bil
* Vehicle status sættes til `LEASED`
* RKI-check udføres automatisk

---

## Fleet routes

| Metode | Endpoint                           | Beskrivelse                    |
| ------ | ---------------------------------- | ------------------------------ |
| GET    | `/fleet/vehicles`                  | Liste over biler               |
| GET    | `/fleet/vehicles/{id}`             | Hent bil                       |
| POST   | `/fleet/vehicles/allocate`         | Find og reserver AVAILABLE bil |
| PUT    | `/fleet/vehicles/{id}/status`      | Opdater bilstatus              |
| GET    | `/fleet/vehicles/pricing/by-model` | Pris pr. model                 |

**Status-flow:**
`AVAILABLE → LEASED → DAMAGED → REPAIR → AVAILABLE`

---

## Reservation routes (Afhentning)

| Metode | Endpoint                    | Beskrivelse             |
| ------ | --------------------------- | ----------------------- |
| GET    | `/reservations`             | Liste over afhentninger |
| POST   | `/reservations`             | Opret afhentning        |
| PATCH  | `/reservations/{id}/status` | Opdater status          |

**Status-flow:**
`PENDING → READY → PICKED_UP → CANCELLED`

**Note:**
Afhentningslokation hentes automatisk fra **Fleet Service**.

---

## Damage routes

| Metode | Endpoint               | Beskrivelse       |
| ------ | ---------------------- | ----------------- |
| GET    | `/damages`             | Liste over skader |
| GET    | `/damages/{id}`        | Hent skade        |
| POST   | `/damages`             | Opret skade       |
| PATCH  | `/damages/{id}/status` | Opdater status    |

**Ved oprettelse af skade:**

* Fleet Service opdateres automatisk
* Bil sættes til status `DAMAGED`

---

## Reporting routes

| Metode | Endpoint                  | Beskrivelse            |
| ------ | ------------------------- | ---------------------- |
| GET    | `/reporting/kpi/overview` | KPI-data til dashboard |

---



Reporting Service:
Har ingen database
Kalder lease- og damage-data via gateway
Beregner KPI’er dynamisk

RKI routes
Metode
Endpoint
Beskrivelse
POST
/rki/check
Simuleret kreditvurdering

Respons:
{
  "status": "APPROVED | REJECTED | PENDING",
  "score": 720,
  "reason": "Simulated result"
}


Kommunikationsflow (eksempel)
Opret lejeaftale
Frontend → Gateway
Gateway → Lease Service
Lease → Fleet (allocate)
Lease → RKI
Lease gemmer aftale
Fleet opdaterer bilstatus



## Roller og adgangsstyring

Systemet anvender **rollebaseret adgang (RBAC)** baseret på JWT-tokens udstedt af Auth Service.

Roller:

DATAREG | SKADE | FORRET | LEDELSE | ADMIN

Rollen gemmes i JWT-token og valideres i frontend og backend.

---

## Rolleoversigt

| Rolle | Primære ansvarsområder |
|-----|------------------------|
| DATAREG | Opret lejeaftaler, afhentninger |
| SKADE | Registrere og håndtere skader |
| FORRET | Overblik, flåde, dashboard |
| LEDELSE | KPI’er, rapportering, overblik |
| ADMIN | Brugere, roller, fuld adgang |

---

## Frontend – adgang pr. fane

| Fane | DATAREG | SKADE | FORRET | LEDELSE | ADMIN |
|----|----|----|----|----|----|
| Dashboard | ❌ | ❌ | ✅ | ✅ | ✅ |
| Lejeaftaler | ✅ | ✅ | ✅ | ✅ | ✅ |
| Afhentning | ✅ | ❌ | ✅ | ✅ | ✅ |
| Skader | ❌ | ✅ | ✅ | ✅ | ✅ |
| Flåde | ❌ | ✅ | ✅ | ✅ | ✅ |
| Admin | ❌ | ❌ | ❌ | ✅ | ✅ |

Frontend skjuler faner dynamisk baseret på rolle.

---

## Frontend – teknisk tilgang

Frontend er bygget i **Streamlit** og fungerer som én samlet applikation:

- Ingen Streamlit Pages
- Navigation styres via `st.session_state.page`
- JWT gemmes i session state
- Alle API-kald går via Gateway

Eksempel:
```python
if role in ("ADMIN", "LEDELSE"):
    menu_options["Admin"] = "Admin"


JWT-baseret sikkerhed
Login via /auth/login
JWT returneres til frontend
JWT sendes i Authorization: Bearer <token>
Gateway videresender token til Auth Service
Backend services stoler på gateway + auth
Fordele:
Central sikkerhed
Simpel frontend
Let at udvide

Gateway – sikker proxy
Gateway anvender en fælles helper:
def _safe_forward(method, url, **kwargs):
    try:
        resp = requests.request(...)
        return resp.content, resp.status_code
    except RequestException:
        return {"error": "Upstream service unavailable"}, 503

Dette sikrer:
Ensartede fejlbeskeder
Ingen frontend-crash
Tydelig arkitektur

Miljøvariabler og isolation
Hver service konfigureres via miljøvariabler:
Ingen hardcodede URLs
Docker-venlig opsætning
Let at deploye lokalt / CI
Eksempel:
LEASE_BASE_URL
FLEET_BASE_URL
AUTH_SECRET


Testbrugere (lokal udvikling)
Der er foruddefinerede testbrugere:
Brugernavn
Rolle
admin
ADMIN
data
DATAREG
skade
SKADE
forret
FORRET
ledelse
LEDELSE

Kodeord = brugernavn

Designprincipper
Tydelig separation of concerns
Ingen frontend-logik i backend
Ingen forretningslogik i gateway
Services ejer egen database
Kommunikation via HTTP (REST)

## Datamodeller og databaser (SQLite pr. service)

Hver microservice ejer sin egen SQLite-database (bounded context).
Databaserne ligger som filer og persisteres via Docker volumes.

| Service | Databasefil | Formål |
|--------|-------------|--------|
| auth_service | `auth.db` | Brugere, roller, login |
| lease_service | `lease.db` | Lejeaftaler og status |
| fleet_service | `fleet.db` | Flåde (biler), status, pricing |
| damage_service | `damage.db` | Skadesregistrering |
| reservation_service | `reservation.db` | Afhentning/reservation |
| reporting_service | (ingen) | Aggregation/KPI via gateway |
| rki_service | (ingen) | Simuleret kreditcheck |

---

## Centrale relationer mellem services

Der findes ikke klassiske SQL-joins på tværs af services i drift.
I stedet bruges ID’er som koblingspunkt:

- `lease_service.leases.vehicle_id` peger på `fleet_service.vehicles.id`
- `damage_service.damages.lease_id` peger på `lease_service.leases.id`
- `reservation_service.reservations.lease_id` peger på `lease_service.leases.id`
- `reservation_service.reservations.vehicle_id` peger på `fleet_service.vehicles.id`

Det betyder:

- Hver service kan udvikles isoleret
- Data kobles via API-kald (runtime) eller eksport (analyse)

---

## Fleet Service – vehicles (uddrag)

Fleet er den “single source of truth” for bilernes status og nøgledata:

- `status`: AVAILABLE | LEASED | DAMAGED | REPAIR
- `delivery_location`: bruges i afhentning (reservation)
- `monthly_price`: bruges til prissætning (fleet/lookup)
- `current_lease_id`: kobler bil til aktiv lease

---

## Lease Service – leases (uddrag)

Lejeaftaler gemmer:

- Kundeinfo (navn, mail, telefon, CPR valgfri)
- `car_model` (modelnavn fra flåden / manuel fallback)
- `vehicle_id` (konkret bil i flåden)
- Periode: `start_date`, `end_date`
- Status: ACTIVE / COMPLETED

Bemærk:
- Monthly price kommer ikke længere fra brugerinput i frontend.
- Pris og bilvalg kan baseres på flådedata.

---

## Reservation Service – afhentning (uddrag)

Reservation/afhentning gemmer:

- `lease_id`
- `vehicle_id`
- `pickup_date` (datetime ISO)
- `pickup_location` (hentes fra Fleet når reservation oprettes)
- Status: PENDING | READY | PICKED_UP | CANCELLED

Dette gør afhentning mere “TO-BE korrekt”:
- Afhentningssted styres af flåden (ikke manuelt input)
- Statusflow kan håndteres i UI og i service

---

## Damage Service – skader (uddrag)

Skader gemmer:

- `lease_id`
- `vehicle_id` (valgfri men anbefalet)
- kategori, beskrivelse, estimated_cost
- status: OPEN / ... (kan udvides)

Når skade oprettes og `vehicle_id` findes:
- damage_service kalder Fleet og sætter bilen til `DAMAGED`

---

## Reporting Service – KPI’er som “API-aggregation”

Reporting har ingen database.
Den samler data via gateway:

- leases: `/leases`
- damages: `/damages`
- (kan udvides til reservations + fleet)

Fordele:
- Ingen datadobling
- KPI altid baseret på nyeste data
- God microservice-disciplin (aggregation i separat service)

---

## Eksport til CSV (Tableau / analyse)

Projektet egner sig godt til Tableau, fordi data ligger struktureret i SQLite.
Derfor kan vi tilbyde et eksport-script som:

1. Læser alle service-db’er
2. Ekporterer tabeller som CSV
3. Kan lave “analyse-views” hvor data joines på ID’er

Eksempler på nyttige analyse-exports:

- `leases_enriched.csv`
  - leases + fleet-vehicle info (model, status, location, price)
- `damages_enriched.csv`
  - damages + lease + vehicle (segment, model, location)
- `reservations_enriched.csv`
  - reservation + lease + vehicle
- `kpi_monthly.csv`
  - månedlig omsætning, active leases, skader osv.

Bemærk:
- Runtime systemet joiner via API
- Analyse joiner via eksport (offline) → Tableau-venligt

---

## Forslag til “Analyse-view” (join logik)

Når vi joiner til CSV, følger vi typisk disse regler:

- leases JOIN fleet ON leases.vehicle_id = fleet.id
- damages JOIN leases ON damages.lease_id = leases.id
- reservations JOIN leases ON reservations.lease_id = leases.id

Det giver datasæt der er mere oplagte til dashboards og BI.



## Docker-setup og container-arkitektur

Projektet kører fuldt containeriseret via Docker Compose.
Hver service bygges som sit eget image og eksponerer sin egen port.

Arkitekturen følger disse principper:

- Én service = én container
- Én database = én service (SQLite)
- Al ekstern adgang går via Gateway
- Frontend (Streamlit) taler kun med Gateway

---

## Overblik: services og porte

| Service | Container | Intern port | Host port |
|-------|----------|------------|-----------|
| auth_service | auth_service | 5001 | 5001 |
| lease_service | lease_service | 5002 | 5002 |
| damage_service | damage_service | 5003 | 5003 |
| reporting_service | reporting_service | 5004 | 5004 |
| rki_service | rki_service | 5005 | 5005 |
| fleet_service | fleet_service | 5006 | 5006 |
| reservation_service | reservation_service | 5007 | 5007 |
| gateway | gateway | 8000 | 8000 |
| frontend | frontend | 8501 | 8501 |

---

## Vigtigt designvalg: host.docker.internal

Gatewayen bruger:


http://host.docker.internal:

til at kalde backend-services.

Hvorfor?
- Gatewayen fungerer som “edge”
- Undgår circular dependencies i Docker-netværket
- Gør services nemme at debugge lokalt

Eksempel (gateway):

```env
LEASE_BASE_URL=http://host.docker.internal:5002
FLEET_BASE_URL=http://host.docker.internal:5006

Frontend kalder derimod gateway internt:
GATEWAY_BASE_URL=http://gateway:8000


Volumes og SQLite – vigtigt!
Alle SQLite-filer mountes eksplicit som volumes:
volumes:
  - ./services/lease_service/lease.db:/app/lease.db

Dette sikrer:
Data overlever container-restarts
DB-filen ikke bliver en mappe ved en fejl
Let adgang til eksport (CSV / analyse)
Typisk fejl:
Hvis DB-filen ikke findes lokalt, opretter Docker en mappe → SQLite fejler
Løsning:
Opret tom .db fil manuelt før docker compose up

Init-mønster for databaser
De fleste services bruger:
@app.before_request
def setup():
    init_db()

Det sikrer:
Tabeller oprettes automatisk
Services kan starte uden migrations
Ulempe:
init_db() kaldes ofte
OK til eksamensprojekt / prototype

Kendte faldgruber (og hvordan de blev løst)
1. 503 “Upstream service unavailable”
Årsag:
Forkert BASE_URL
Service ikke startet
Manglende dependency i docker-compose
Løsning:
Tjek gateway logs
Test service direkte via curl på host-port

2. sqlite3.OperationalError: unable to open database file
Årsag:
DB-fil mangler → Docker laver mappe
Løsning:
Opret tom .db fil
Mount korrekt volume

3. Manglende Python dependency
Eksempel:
requests glemt i requirements.txt
Løsning:
Opdater requirements.txt
Rebuild image (docker compose build)

4. Circular dependency mellem services
Eksempel:
reporting_service → gateway → reporting_service
Løsning:
Reporting kalder gateway
Gateway har INGEN depends_on til reporting

Logging og debug
Alle services kører i debug-mode:
app.run(host="0.0.0.0", port=XXXX, debug=True)

Det giver:
Stack traces i browser
Tydelige logs i Docker Desktop
Gateway returnerer altid JSON-fejl ved upstream-fejl:
{
  "error": "Upstream service unavailable",
  "upstream_url": "...",
  "details": "..."
}


Lokal udvikling – anbefalet workflow
Opret tomme .db filer
docker compose build
docker compose up
Åbn:
Frontend: http://localhost:8501
Gateway: http://localhost:8000/health


## Roller og adgangsstyring

Systemet anvender **rollebaseret adgangskontrol (RBAC)**.
Roller håndteres centralt i `auth_service` og distribueres via JWT.

### Roller i systemet

| Rolle | Formål |
|------|-------|
| DATAREG | Oprette lejeaftaler, afhentninger og se basale data |
| SKADE | Registrere og behandle skader |
| FORRET | Se forretningsdata, flåde og dashboard |
| LEDELSE | Overblik, rapportering, KPI’er, admin-adgang |
| ADMIN | Fuld adgang inkl. brugerstyring |

---

## Default test-brugere

Til udvikling og test er følgende brugere oprettet:

| Brugernavn | Password | Rolle |
|-----------|----------|-------|
| admin | admin | ADMIN |
| data | data | DATAREG |
| skade | skade | SKADE |
| forret | forret | FORRET |
| ledelse | ledelse | LEDELSE |

Disse brugere kan ændres eller suppleres via Admin-siden i frontend.

---

## JWT-flow (overblik)

1. Bruger logger ind via frontend
2. Gateway proxy’er login til auth_service
3. AuthService udsteder JWT med rolle
4. Frontend gemmer token i session_state
5. Token sendes med på alle requests

Eksempel header:

```http
Authorization: Bearer <JWT_TOKEN>


Gateway og sikkerhed
Gatewayen:
Validerer JWT (via auth_service)
Videresender Authorization-header uændret
Har ingen forretningslogik
Returnerer altid konsistent JSON ved fejl
Dette sikrer:
Ét samlet indgangspunkt
Let udskiftning af frontend
Ensartet fejlhåndtering

Frontend: bevidste designvalg
Frontend er bygget i én Streamlit-app uden separate pages.
Hvorfor ikke Streamlit Pages?
JWT håndtering er enklere i én fil
Fuld kontrol over navigation og session_state
Klarere mapping mellem roller og UI
Mindre “magisk” adfærd
Navigation styres manuelt via:
st.session_state.page


Rollebaseret UI-visning
Menu og sider vises dynamisk baseret på rolle.
Eksempel:
if role in ("ADMIN", "LEDELSE"):
    menu_options["Admin"] = "Admin"

Vigtigt:
UI skjuler funktioner
Backend er stadig “source of truth”
Frontend er et ekstra sikkerhedslag

Dashboard-adgang (bevidst valg)
DATAREG kan ikke se Dashboard.
Hvorfor?
Dashboard indeholder ledelses-KPI’er
DATAREG arbejder operationelt
Matcher TO-BE BPMN og opgavekrav
Tilladte roller:
FORRET
LEDELSE
ADMIN

UX-principper
Frontend er bevidst:
Funktionel frem for dekorativ
Rollebaseret frem for “one size fits all”
Optimeret til interne brugere
Brug af:
Tabs til flows (Oversigt / Opret)
Expanders til detaljer
Inline status-opdatering (PATCH)
Dropdowns frem for fritekst hvor muligt

Sammenhæng mellem flows
Frontend binder services sammen:
Lease → Fleet (vehicle_id)
Lease → Reservation (afhentning)
Lease → Damage → Fleet status
Reservation → Fleet lokation
Reporting → Lease + Damage
Frontend indeholder ingen joins:
Al data samles via Gateway
ReportingService samler kun til KPI’er

Fejl- og edge case-håndtering
Frontend:
Viser brugbare fejlbeskeder
Fortsætter selv hvis én service er nede
Falder tilbage til manuelle input ved behov
Eksempel:
Hvis flåde-data ikke kan hentes → manuel bilmodel

Afgrænsning (bevidst fravalg)
Ikke implementeret:
Hard deletes
Komplekse permissions pr. record
Historik/audit logs
Async events / message queue
Disse fravalg er:
Dokumenterede
Bevidste
Argumenterbare ift. opgavens scope


## Dataeksport og BI-understøttelse

Systemet er designet med henblik på at kunne fungere som **datakilde for BI-værktøjer**
som fx Tableau, Power BI eller Excel – uden at skulle give direkte adgang til databaser.

---

## Motivation

Under udviklingen blev følgende behov identificeret:

- Undgå manuel kopiering fra SQLite-viewer
- Kunne trække **opdaterede datasæt** on-demand
- Samle data på tværs af services
- Understøtte eksterne analyseværktøjer

Derfor er der tilrettelagt mulighed for **CSV-eksport** baseret på samme data,
som anvendes i dashboardet.

---

## Datakilder i systemet

Hver microservice har sin egen database:

| Service | Database |
|-------|----------|
| auth_service | auth.db |
| lease_service | lease.db |
| fleet_service | fleet.db |
| damage_service | damage.db |
| reservation_service | reservation.db |

Databaserne er:
- SQLite
- Persistent via Docker volumes
- Isoleret pr. service (ingen shared DB)

---

## Samlet eksport (koncept)

Data kan samles ved at:

1. Læse direkte fra SQLite-filerne (read-only)
2. Joine data på tværs via kendte nøgler
3. Eksportere til CSV

Primære relationer:

- `lease.id` ↔ `damage.lease_id`
- `lease.vehicle_id` ↔ `fleet.id`
- `lease.id` ↔ `reservation.lease_id`

---

## Eksempel på samlet “BI-view”

Et typisk samlet datasæt kan indeholde:

### Lease-data
- lease_id
- customer_name
- start_date
- end_date
- status

### Vehicle-data
- vehicle_id
- model_name
- fuel_type
- monthly_price
- delivery_location
- vehicle_status

### Damage-data
- damage_id
- category
- estimated_cost
- damage_status

### Reservation-data
- pickup_date
- pickup_location
- reservation_status
- actual_pickup_at

Dette giver ét fladt datasæt, der er direkte egnet til Tableau.

---

## Fordele ved CSV-eksport

- Ingen DB-adgang nødvendig
- Let at versionere
- Kan automatiseres
- Matcher undervisningens fokus på datadrevenhed

CSV-filer kan:
- Uploades manuelt til Tableau
- Bruges som datakilde i dashboards
- Deles med eksterne interessenter

---

## Sammenhæng med ReportingService

ReportingService:
- Bruger gateway
- Samler data runtime
- Leverer KPI’er via API

CSV-eksport:
- Arbejder med samme datagrundlag
- Muliggør mere dybdegående analyser
- Understøtter historik og trendanalyser

---

## Afgrænsning

Eksportløsningen:
- Er read-only
- Påvirker ikke drift
- Kræver ingen ekstra services

Ikke implementeret:
- Automatisk scheduled eksport
- Live DB-connection fra Tableau
- Streaming / real-time BI

Dette er bevidste fravalg ift. opgavens scope.

---

## Perspektivering

Løsningen kan nemt udvides med:
- `/export/csv` endpoint
- Rollebaseret adgang til eksport
- Automatisk snapshot pr. måned

Disse muligheder er teknisk realistiske inden for den eksisterende arkitektur.

---

## Docker og deployment

Projektet er fuldt containeriseret og kan startes med **én kommando** via Docker Compose.
Alle services er isolerede, men forbundet via et fælles Docker-netværk.

---

## Overordnet arkitektur i Docker

Hver service kører i sin egen container:

- auth_service
- lease_service
- damage_service
- fleet_service
- reservation_service
- reporting_service
- rki_service
- gateway
- frontend (Streamlit)

Gateway fungerer som:
- Central indgang
- Sikkerhedslag
- Routing-mekanisme mellem services

---

## Docker Compose

Systemet startes via:

```bash
docker compose up --build

Dette:
Bygger alle images
Starter services i korrekt rækkefølge
Opretter nødvendige Docker-netværk
Binder databaser som volumes

Persistens (SQLite + volumes)
Alle databaser er persistent via bind mounts:
Service             |        Volume
auth_service        |./services/auth_service/auth.db
lease_service       |./services/lease_service/lease.db
damage_service      |./services/damage_service/damage.db
fleet_service       |./services/fleet_service/fleet.db
reservation_service |./services/reservation_service/reservation.db

Fordele:
Data bevares ved container-restart
Let adgang til rå data
Nem eksport til CSV / BI

Netværk og kommunikation
Intern service-til-service
Foregår via Docker service names
Eksempel: http://lease_service:5002
Gateway-kommunikation
Gateway er konfigureret til at kalde services via:
host.docker.internal
Mappede porte
Dette valg:
Forenkler lokal debugging
Matcher undervisningsmiljø
Undgår circular dependencies

Porte (lokal adgang)
Service                 |    Port
Frontend (Streamlit)         8501
Gateway                      8000
AuthService                  5001
LeaseService                 5002
DamageService                5003
ReportingService             5004
RKIService                   5005
FleetService                 5006
ReservationService           5007


Lokal udvikling
Krav
Docker
Docker Compose
Git
Start projektet
git clone <repo>
cd project
docker compose up --build

Frontend tilgås via:
http://localhost:8501


Health checks
Alle services understøtter:
GET /health

Eksempel:
{
  "status": "ok",
  "service": "lease_service"
}

Dette bruges til:
Debugging
Driftsoverblik
Dokumentation

Fejlhåndtering
Gateway implementerer:
Timeout-beskyttelse
Ensartede fejlbeskeder
Graceful degradation
Eksempel:
{
  "error": "Upstream service unavailable",
  "upstream_url": "...",
  "details": "..."
}

Frontend kan derfor reagere korrekt uden at crashe.

Afgrænsning
Deployment er:
Lokal (Docker Compose)
Ikke cloud-baseret
Ikke skaleret horisontalt
Dette er et bevidst valg ift. opgavens omfang og fokus.

Perspektivering
Arkitekturen kan nemt udvides til:
Kubernetes
CI/CD pipeline
Cloud deployment (fx Azure / AWS)
Managed databases




## Roller og adgangsstyring

Systemet benytter **rollebaseret adgangskontrol (RBAC)**, implementeret centralt i **Gateway**.
Alle backend-services er dermed fri for direkte auth-logik og stoler på gatewayen.

---

## Roller

Følgende roller er defineret i systemet:

- DATAREG  
- SKADE  
- FORRET  
- LEDELSE  
- ADMIN  

Rollerne afspejler virksomhedens organisatoriske struktur og arbejdsopgaver.

---

## Default testbrugere

Ved opstart findes følgende testbrugere:

| Rolle | Brugernavn | Kodeord |
|----|----|----|
| ADMIN | admin | admin |
| DATAREG | data | data |
| SKADE | skade | skade |
| FORRET | forret | forret |
| LEDELSE | ledelse | ledelse |

Brugerne anvendes til:
- Test
- Demonstration
- Rollevalidering i frontend og gateway

---

## Autentificering (AuthService)

AuthService håndterer:

- Login
- JWT-generering
- Brugeropslag
- Rolleændringer

### Login-flow

1. Frontend sender credentials til `/auth/login`
2. AuthService returnerer JWT
3. JWT gemmes i frontend session
4. JWT sendes i `Authorization` header ved alle kald

Eksempel:

Authorization: Bearer

---

## Gateway som sikkerhedslag

Gateway:
- Validerer JWT
- Checker token expiration
- Matcher rolle mod route-regler
- Blokerer uautoriserede kald

Services bag gatewayen:
- Antager gyldig adgang
- Indeholder ingen auth-logik

---

## Route permissions

Gateway anvender en simpel mapping:

```python
(method, path_prefix) -> tilladte roller

Eksempel:
/leases → DATAREG, LEDELSE, ADMIN
/damages → SKADE, LEDELSE, ADMIN
/reporting/kpi → FORRET, LEDELSE, ADMIN
ADMIN har altid fuld adgang.

Frontend-adgang
Streamlit frontend:
Skjuler faner baseret på rolle
Viser kun relevant funktionalitet
Matcher gatewayens adgangsregler
Eksempel:
DATAREG kan oprette lejeaftaler
SKADE kan registrere skader
FORRET kan se dashboard
LEDELSE kan se alt
ADMIN kan administrere brugere
Dette sikrer:
Mindre risiko for fejl
Klar arbejdsdeling
Tydelig UX

Sikkerhedsovervejelser
Bevidste valg i projektet:
JWT med expiration
Central auth i gateway
Ingen direkte service-adgang fra frontend
Ensartede fejlbeskeder
Ingen hardcoded roller i services
Ikke implementeret (bevidst):
Refresh tokens
OAuth / SSO
Rate limiting
IP whitelisting
Dette er vurderet passende ift. eksamensprojektets scope.

Audit og sporbarhed
Systemet understøtter grundlæggende sporbarhed via:
Timestamps i databaser
Lease-ID / Vehicle-ID koblinger
Statushistorik i leases, damages og reservations
Dette danner grundlag for:
Rapportering
Dashboard-KPI’er
Senere udvidelser



## Dataflow og domænemodeller

Systemet er designet omkring **klare domæner**, hvor hver microservice ejer sit eget dataområde og database.
Services kommunikerer udelukkende via API-kald, typisk gennem gatewayen.

---

## Overordnet dataflow

Et forenklet dataflow for en typisk lejeaftale:

1. **DATAREG** opretter en lejeaftale i frontend  
2. LeaseService opretter lease i `lease.db`  
3. LeaseService anmoder FleetService om en AVAILABLE bil  
4. FleetService reserverer bil og sætter status til LEASED  
5. Lease gemmer `vehicle_id`  
6. ReservationService opretter afhentning baseret på lease + vehicle  
7. DamageService kan senere registrere skader  
8. ReportingService samler data via gatewayen til KPI’er  

Hver service arbejder udelukkende inden for sit eget ansvar.

---

## Centrale domæneobjekter

### Lease (LeaseService)

Repræsenterer en lejeaftale.

Nøglefelter:
- `id`
- `customer_name`
- `customer_cpr`
- `car_model`
- `start_date`
- `end_date`
- `status` (ACTIVE, COMPLETED)
- `vehicle_id`
- RKI-felter

Relationer:
- 1 lease → 1 vehicle
- 1 lease → 0..N damages
- 1 lease → 0..1 reservation

---

### Vehicle (FleetService)

Repræsenterer en bil i flåden.

Nøglefelter:
- `id`
- `model_name`
- `fuel_type`
- `monthly_price`
- `delivery_location`
- `status` (AVAILABLE, LEASED, DAMAGED, REPAIR)
- `current_lease_id`

FleetService er **single source of truth** for bilstatus.

---

### Damage (DamageService)

Repræsenterer en skade registreret på en lejeaftale.

Nøglefelter:
- `id`
- `lease_id`
- `category`
- `description`
- `estimated_cost`
- `status`

Ved oprettelse kan DamageService:
- Opdatere bilstatus i FleetService til DAMAGED

---

### Reservation (ReservationService)

Repræsenterer afhentning af bil.

Nøglefelter:
- `id`
- `lease_id`
- `vehicle_id`
- `pickup_date`
- `pickup_location`
- `status` (PENDING, READY, PICKED_UP, CANCELLED)
- `actual_pickup_at`

Pickup-lokation hentes dynamisk fra FleetService.

---

## Reporting og afledt data

ReportingService ejer **ingen data** selv.
Den:
- Henter leases via gateway
- Henter damages via gateway
- Beregner KPI’er on-the-fly

Eksempler på afledte KPI’er:
- Aktive leases
- Omsætning pr. måned
- Afsluttede leases med skader
- Gennemsnitlig skadesomkostning
- Top bilmodeller

---

## Dataintegritet

Bevidste designvalg:

- Ingen direkte database-joins på tværs af services
- ID-referencer bruges til relationer
- Statusændringer synkroniseres via API
- FleetService er autoritativ for køretøjsstatus

Dette giver:
- Lav kobling
- Klar ansvarfordeling
- Let udvidelse

---

## Konsistens vs. performance

Systemet prioriterer:
- Klarhed
- Sporbarhed
- Forretningslogik

Frem for:
- Hård konsistens på tværs af databaser

Dette er et bevidst valg, der matcher microservice-paradigmet og projektets scope.

---

## Dashboard og KPI’er

Dashboardet er implementeret i **Streamlit-frontend** og fungerer som et fælles overblik for
FORRET, LEDELSE og ADMIN.

Det er designet til at:
- Give hurtigt overblik over forretningen
- Understøtte datadrevne beslutninger
- Vise sammenhæng mellem leases, skader og flåde

---

## Datakilde

Dashboardet trækker **udelukkende data fra ReportingService** via gateway:


GET /reporting/kpi/overview

ReportingService:
- Ejer ingen data selv
- Samler data fra LeaseService og DamageService
- Beregner KPI’er dynamisk

Dette sikrer:
- Én samlet sandhed for KPI’er
- Ingen forretningslogik i frontend
- Let udvidelse af KPI’er

---

## KPI’er i dashboardet

### Aktive abonnementer
Antal lejeaftaler med status `ACTIVE`.

Formål:
- Overblik over igangværende forretning
- Indikation af belastning på flåden

---

### Omsætning pr. måned
Beregnes ud fra:
- `start_date`
- `monthly_price`

Grupperet pr. måned (`YYYY-MM`).

Formål:
- Trendanalyse
- Forretningsmæssigt overblik

---

### Afsluttede leases med skader
Antal lejeaftaler med:
- Status `COMPLETED`
- Mindst én registreret skade

Formål:
- Indblik i risici
- Kvalitet af flåden
- Procesforbedringer

---

### Gennemsnitlig skadesomkostning
Gennemsnit af `estimated_cost` på alle skader.

Formål:
- Økonomisk risikovurdering
- Input til forsikrings- og prisstrategi

---

### Top bilmodeller
De mest anvendte bilmodeller baseret på antal leases.

Formål:
- Flådestyring
- Indkøbsbeslutninger
- Efterspørgselsanalyse

---

## Visualisering i Streamlit

Dashboardet anvender:
- `st.metric` til nøgletal
- Listebaseret visning af tidsserier
- Klar typografi og struktur
- Rollebaseret adgang

Bevidst fravalgt:
- Avancerede charts (kan tilføjes senere)
- Overkompleks layout

Dette matcher:
- Projektets scope
- Fokus på arkitektur og dataflow

---

## Automatisk opdatering

Dashboardet kan:
- Genopfriskes manuelt
- Udvides med auto-refresh via Streamlit

Data er altid:
- Live
- Afledt af nuværende tilstand i systemet

---

## Perspektivering

Dashboardet er forberedt til:
- Eksport af data som CSV
- Integration med Tableau / Power BI
- Udvidelse med flere KPI’er
- Filtrering pr. periode, biltype eller afdeling

---


## Dataeksport og BI-integration

Systemet er designet, så data nemt kan genbruges uden for applikationen.
Et centralt mål har været at understøtte **datadrevet analyse** og **ekstern rapportering**.

---

## Motivation

I den oprindelige AS-IS-situation arbejdede virksomheden primært i:
- Excel
- Manuelle udtræk
- Fragmenterede datasæt

TO-BE-løsningen understøtter i stedet:
- Samlede datasæt
- Automatiseret eksport
- Direkte integration med BI-værktøjer

---

## Datakilder

Følgende databaser anvendes i systemet:

| Service | Database |
|------|------|
| AuthService | auth.db |
| LeaseService | lease.db |
| DamageService | damage.db |
| FleetService | fleet.db |
| ReservationService | reservation.db |

Hver database ejes af sin service og er persistent via Docker volumes.

---

## CSV-eksport (koncept)

Data kan eksporteres som CSV ved at:
- Læse direkte fra SQLite-databaserne
- Samle relevante tabeller
- Join’e data via ID-relationer
- Skrive strukturerede CSV-filer

Eksempler på nyttige eksport-datasæt:

- Leases med tilknyttet vehicle og status
- Leases med skader og samlede omkostninger
- Flådeoversigt med historisk status
- Afhentninger pr. lokation og dato

---

## Join-strategi

Da systemet er microservice-baseret:
- Databaser join’es **kun i eksport-scriptet**
- Ikke i runtime
- Ikke på tværs af services i applikationen

Eksempel:
- `lease.db.leases.vehicle_id`
- matches med
- `fleet.db.vehicles.id`

Dette bevarer arkitekturel renhed, men muliggør analyse.

---

## Anvendelse i Tableau / BI

CSV-filer kan anvendes direkte i:
- Tableau
- Power BI
- Excel
- Python (pandas)
- R

Fordele:
- Ingen afhængighed af live system
- Let deling med forretning/ledelse
- Understøtter eksamenskrav om datadrevenhed

---

## Perspektivering

Eksport-funktionen kan senere udvides til:
- Planlagte eksporter
- API-baseret datadump
- Automatisk upload til BI-platform
- Versionsstyrede datasæt

Dette er uden ændringer i kernearkitekturen.

---

## Projektstruktur

Projektet er organiseret efter **microservice-principper**, hvor hver service:
- Har sit eget kodegrundlag
- Har sin egen database
- Kan udvikles og testes isoleret

Rod-strukturen ser overordnet sådan ud:


.
├── frontend/
│ ├── app.py
│ ├── assets/
│ │ └── theme.css
│ └── Dockerfile
│
├── gateway/
│ ├── main.py
│ ├── requirements.txt
│ └── Dockerfile
│
├── services/
│ ├── auth_service/
│ ├── lease_service/
│ ├── damage_service/
│ ├── fleet_service/
│ ├── reservation_service/
│ ├── reporting_service/
│ └── rki_service/
│
├── docker-compose.yml
└── README.md

---

## Service-struktur (generisk)

Hver service følger samme grundstruktur:


service_name/
├── main.py
├── database.py
├── requirements.txt
├── Dockerfile
└── *.db

Fordele:
- Konsistens
- Let onboarding
- Forudsigelighed
- Genkendelig arkitektur

---

## README-struktur

Projektet indeholder:

### Root README (denne fil)
Indeholder:
- Overblik over systemet
- Arkitektur
- Roller
- Dataflow
- Dashboard og BI
- Docker og deployment

### Service-specifikke README’er
Hver service får sin egen README med:
- Ansvar og formål
- Endpoints
- Database-model
- Interaktion med andre services

Dette sikrer:
- Dokumentation på flere niveauer
- Let vedligehold
- Klar eksamensformidling

---

## Dokumentationsniveau

Bevidste valg:
- Fokus på **arkitektur og proces**
- Ikke overdreven low-level dokumentation
- Klar kobling til BPMN og TO-BE

README’erne er skrevet så:
- Undervisere kan forstå løsningen
- Medstuderende kan køre projektet
- Systemet kan videreudvikles

---

## Kodekvalitet og struktur

Projektet prioriterer:
- Klar navngivning
- Små, fokuserede funktioner
- Minimal “magic”
- Tydelig adskillelse af ansvar

Dette understøtter:
- Vedligeholdelse
- Test
- Udvidelser

---

## Klar til aflevering

Med:
- Fungerende system
- Dokumenteret arkitektur
- TO-BE procesunderstøttelse
- Datadrevet dashboard
- Rollebaseret adgang

er projektet klar til:
- Eksamensaflevering
- Mundtlig præsentation
- Videreudvikling

---

## Konklusion og refleksion

Dette projekt demonstrerer design og implementering af en **microservice-baseret løsning**,
der understøtter Bilabonnement.dk’s centrale forretningsprocesser.

Udgangspunktet var:
- Manuelle processer
- Excel-baseret databehandling
- Manglende overblik
- Lav digital modenhed

Den færdige løsning adresserer disse udfordringer direkte.

---

## Opfyldelse af mål

Projektets hovedmål var at:

> Designe og udvikle en digital, microservice-baseret løsning,
> der automatiserer og forbedrer interne processer
> og samtidig understøtter virksomheden i at blive mere datadrevet.

Dette er opnået ved:

- Digitalisering af lejeaftaler, skader, afhentning og flådestyring
- Klar opdeling i services med tydeligt ansvar
- Central gateway med sikkerhed og routing
- Rollebaseret adgang i både backend og frontend
- Datadrevet dashboard til ledelse og forretning

---

## Sammenhæng mellem analyse og løsning

Der er tydelig kobling mellem:
- AS-IS BPMN-analyser
- Identificerede pain points
- TO-BE processer
- Den implementerede arkitektur

Eksempler:
- Manuel bilallokering → FleetService
- Uigennemsigtig status → klare statusfelter
- Spredt data → samlet reporting
- Manglende overblik → dashboard og KPI’er

---

## Arkitekturvalg

Valget af microservices er begrundet i:

- Skalerbarhed
- Lav kobling
- Klar ansvarfordeling
- Let udvidelse

Gatewayen sikrer:
- Central sikkerhed
- Ensartet adgang
- Simplere frontend

SQLite er valgt bevidst:
- Let at deploye
- Velegnet til undervisningsprojekter
- Understøtter BI-eksport

---

## Læring og refleksion

Projektet har givet erfaring med:

- Microservice-arkitektur i praksis
- Docker og containerisering
- Rollebaseret adgangsstyring
- Dataflow på tværs af services
- Balancen mellem konsistens og kompleksitet
- Samspil mellem forretning, proces og teknik

Særligt arbejdet med:
- FleetService som single source of truth
- Gateway-baseret sikkerhed
- Reporting uden direkte databaseadgang

har været lærerigt.

---

## Afgrænsninger

Bevidste fravalg:

- Ingen cloud deployment
- Ingen avanceret auth (SSO/OAuth)
- Ingen message queue / event bus
- Ingen historisk audit-log

Disse er fravalgt for at:
- Holde fokus på eksamenskrav
- Undgå unødig kompleksitet
- Prioritere kvalitet frem for bredde

---

## Perspektivering

Løsningen kan udvides med:

- Event-driven arkitektur
- Notifikationer
- Avancerede dashboards
- CI/CD
- Cloud hosting
- Eksterne datakilder

Arkitekturen er forberedt til dette uden større ændringer.

---

## Afsluttende bemærkning

Projektet leverer en:
- Sammenhængende
- Skalerbar
- Velafgrænset
- Dokumenteret

digital løsning, der tydeligt demonstrerer kompetencer inden for
**IT-arkitektur, forretningsforståelse og systemudvikling**.




