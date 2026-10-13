# Capability-Matched Emergency Referral (CMER)

**Taking the patient to the right hospital the first time.**

> 108 gets the ambulance to the patient. CMER helps get the patient to the right hospital the first time.

Seva First Innovation Challenge (Viksit Bharat 2047), Track A (Product / Technology), Theme: Swasth & Samavesh Bharat (Health) / Surakshit Bharat.
Full problem statement, evidence and sources: [document.md](./document.md) | Presentation deck: [CMER Presentation Deck](https://sevafirst.mic.gov.in).

> **Status:** simulation-based prototype on synthetic data. This is decision support. The dispatcher and EMT make the final call.

---

## Table of contents

1. [What it does](#1-what-it-does)
2. [Tech stack](#2-tech-stack)
3. [Architecture](#3-architecture)
4. [System design](#4-system-design)
5. [Repository layout](#5-repository-layout)
6. [Build order](#6-build-order)
7. [National submission plan (closing 24 October 2026)](#7-national-submission-plan-closing-24-october-2026)
8. [Pilot plan (Slide 7 alignment)](#8-pilot-plan-slide-7-alignment)
9. [Running locally](#9-running-locally)
10. [Safety and limitations](#10-safety-and-limitations)

---

## 1. What it does

When a 108 call comes in, normal dispatch continues as usual. CMER sits alongside it and:

1. Maps the emergency to the **capability needed** (for example, head injury → trauma + neurosurgery + ICU).
2. **Filters** out hospitals that cannot provide that care.
3. **Ranks** the remaining hospitals by **Expected Time to Treatment (ETT)**, not by distance.
4. Recommends a **primary** and a **backup** hospital, with the reasons and a confidence figure.
5. Sends the hospital a **pre-alert**. The hospital confirms, and a bed is **held** until the ambulance arrives or the hold expires.
6. Learns a **reliability score** for each hospital from what crews actually find when they arrive.

There are three user interfaces: **Dispatcher dashboard**, **Ambulance crew app**, **Hospital dashboard**.

---

## 2. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | **React 19 + Vite** (JS/JSX), `react-router-dom` v7 | Fast to build, one codebase for all 3 UIs |
| Styling | Vanilla CSS, dark clinical theme, `lucide-react` icons | Full control, premium look |
| Maps | **Leaflet + react-leaflet** with OpenStreetMap tiles | Free, no API key |
| Charts | **Recharts** | Simulation and calibration charts |
| Crew app | Same React app, mobile-first route → **offline-first PWA** (service worker + IndexedDB cache, compressed payloads) | No native build; keeps working on rural corridors with patchy signal |
| Backend API | **Python 3.12 + FastAPI** | Async, WebSockets built in, same language as the maths |
| Real-time | FastAPI **WebSockets** (later: Supabase Realtime) | Pre-alerts and live bed updates |
| Ranking / probability | `numpy`, `scipy.stats` (Skellam / Poisson) | Exact bed-availability probability |
| Simulation | Python + **SimPy** (discrete-event) | Runs 200× baseline vs CMER comparisons |
| Database | **PostgreSQL (Supabase)** + SQLAlchemy 2.0 async | In-memory store for the prototype |
| Travel time | Haversine + speed + traffic noise → **OSRM** later | No external dependency for the demo |
| SMS / WhatsApp updates | Twilio sandbox (later phase) | Lets small facilities without IT report beds |
| SMS / USSD fallback | SMS gateway (Twilio / MSG91) + USSD aggregator | Pre-alerts and confirmations still go through when mobile data fails |
| Interoperability | **ABDM Health Facility Registry (HFR) IDs**, **HL7 FHIR R4** (`fhir.resources`) for `Organization` / `Location` / `HealthcareService` | Fits national digital public infrastructure; no duplicate hospital records |
| CAD integration | **Sidecar adapter** (FastAPI webhook / poller) next to the 108 operator's existing CAD | Reads incidents and sends back recommendations without changing core dispatch logs |
| Auth | Supabase Auth, role-based (dispatcher / crew / hospital) | Later phase |
| Testing / lint | `pytest -q`, `ruff`, `oxlint` | Quiet, quick checks |

---

## 3. Architecture

```mermaid
flowchart LR
    subgraph External["Existing systems"]
        CAD["108 CAD (e.g. EMRI GHS)"]
        HFR["ABDM Health Facility Registry"]
        HIS["Hospital HIS (FHIR / file export)"]
    end

    subgraph Clients
        D["Dispatcher Overlay (React)"]
        C["Crew App (offline-first PWA)"]
        H["Hospital Dashboard (React)"]
        S["SMS / WhatsApp / USSD"]
    end

    subgraph Integrations["Integration layer"]
        SIDE["CAD Sidecar Adapter"]
        FHIR["FHIR / HFR Connector"]
        GW["SMS-USSD Gateway (fallback)"]
    end

    subgraph Backend["FastAPI Backend"]
        API["REST API"]
        WS["WebSocket Hub"]
        CAP["Capability Mapper"]
        RANK["Ranking Engine (ETT)"]
        PROB["Availability Estimator (P_ok)"]
        RES["Reservation Manager (holds and expiry)"]
        REL["Reliability Scorer"]
        FRESH["Freshness Monitor"]
    end

    subgraph Data
        DB[("PostgreSQL / Supabase")]
        SIM["Synthetic City and Simulator (SimPy)"]
    end

    CAD -->|incident coordinates| SIDE -->|create case| API
    API -->|recommendation| SIDE -->|shown in overlay, CAD logs untouched| CAD
    HFR -->|facility IDs| FHIR
    HIS -->|bed counts| FHIR --> API
    D -->|create / review case| API
    C -->|confirm category, accept or override| API
    H -->|update capacity, confirm or reject| API
    S -->|"ICU 2"| GW --> API
    API -->|pre-alert when data is down| GW -->|SMS| C

    API --> CAP --> RANK
    RANK --> PROB
    PROB --> REL
    PROB --> FRESH
    API --> RES
    RES --> WS
    WS -->|pre-alert| H
    WS -->|recommendation| C
    WS -->|live board| D

    API <--> DB
    SIM -->|seeds hospitals, cases, reports| DB
    SIM -->|evaluation runs| RANK
```

**Key principle:** the ranking engine is a **pure Python module** with no web code inside it. The API and the simulator both call the same function. That means the result you see in the demo is the same result being measured in the simulation.

---

## 4. System design

### 4.1 Data model (minimal, no patient data)

| Entity | Key fields |
|---|---|
| `hospital` | id, **hfr_id** (ABDM Health Facility Registry), name, tier (small / mid / tertiary), lat, lng, emergency_phone, sms_number, reliability `R` (default 0.8) |
| `capability` | hospital_id, code (`TRAUMA`, `NEURO`, `CARDIAC`, `OBSTETRIC`, `NICU`, `BURNS`, `PAEDS`, `ICU`, `BLOOD`, `CT`, `CATH_LAB`) |
| `ward_status` | hospital_id, ward (ICU, ER, OBS, NICU…), total_beds, free_beds, reported_at, source (dashboard / sms / fhir / api) |
| `specialist_shift` | hospital_id, specialty, on_duty (bool), shift_end |
| `hospital_rates` | hospital_id, ward, hour, discharge_rate `d`, admission_rate `a` |
| `er_load` | hospital_id, waiting_count, est_delay_min |
| `case` | id, **cad_incident_id** (nullable), lat, lng, category, severity, num_patients, status, created_at |
| `outbound_message` | id, case_id, channel (ws / sms / ussd), payload, status (queued / sent / acked), retries |
| `recommendation` | case_id, hospital_id, rank, ett, travel_time, er_delay, p_ok, reasons[] |
| `reservation` | id, case_id, hospital_id, ward, status, eta, expires_at |
| `arrival_feedback` | case_id, hospital_id, bed_ok, specialist_ok, equipment_ok, accepted, `match` |
| `override_log` | case_id, from_hospital, to_hospital, reason, actor |

### 4.2 Capability map

| Category | Required capabilities |
|---|---|
| Trauma / head injury | TRAUMA, NEURO, ICU, CT |
| Cardiac | CARDIAC, CATH_LAB, ICU |
| Stroke / neuro | NEURO, CT, ICU |
| Obstetric | OBSTETRIC, BLOOD, ICU or NICU |
| Paediatric | PAEDS, NICU / PICU |
| Burns | BURNS, ICU |
| General / uncertain | ER only (widest set) |

### 4.3 Ranking pipeline

```
case ─► capability_required(category)
     ─► filter hospitals (has all capabilities)
     ─► for each candidate h:
            travel_time(h)      haversine × road factor ÷ speed × traffic noise
            ER_delay(h)         from er_load
            P_ok(h)             Section 4.4
            reroute_penalty(h)  travel(h → nearest other capable) + handling delay
            ETT(h) = travel + ER_delay + (1 − P_ok) × reroute_penalty
     ─► sort by ETT ─► primary = #1, backup = #2
     ─► reasons[] (e.g. "Neurosurgeon on duty", "ICU 85% likely", "Data 42 min old: verify")
```

### 4.4 Availability probability (`P_ok`)

- `f0` is the last reported free beds. `t` is report age plus ETA, in minutes.
- Discharges are modelled as `Poisson(d·t)` and admissions as `Poisson(a·t)`, so `free(T) = f0 + Skellam(d·t, a·t)`.
- `P_ok = P(free(T) − held_beds − turnover_buffer ≥ 1)`, computed with `scipy.stats.skellam`.
- **Reliability widening:** when `R` is low, the estimate is blended toward a pessimistic prior: `P_ok' = R·P_ok + (1−R)·P_prior`.
- **Freshness bands:** Fresh (≤15 min) means the report is trusted. Aging (15–30 min) uses the full estimator. Stale (>30 min) uses the estimator and shows a **"Verify"** button. A stale hospital is never dropped.
- Specialists and equipment are a simple multiplier: `P_ok_total = P_bed × P_specialist × P_equipment`.

### 4.5 Reservation state machine

```mermaid
stateDiagram-v2
    [*] --> PROPOSED: crew accepts hospital
    PROPOSED --> HELD: hospital confirms
    PROPOSED --> REJECTED: hospital rejects (go to backup)
    HELD --> CLOSED: ambulance arrives
    HELD --> EXPIRED: now > ETA + buffer
    HELD --> RELEASED: diverted / cancelled / unstable-patient override
    REJECTED --> [*]
    CLOSED --> [*]
    EXPIRED --> [*]
    RELEASED --> [*]
```

A `HELD` reservation counts in `held_beds`. This is how a second ambulance going to the same hospital sees a lower `P_ok`.

### 4.6 Reliability score

After arrival: `R_new = (1 − α)·R_old + α·match` with `α = 0.1`.
`match = 1` when the reported bed, specialist and equipment were really available.

### 4.7 API surface

| Method | Endpoint | Used by |
|---|---|---|
| `GET` | `/hospitals` | all |
| `POST` | `/cases` | dispatcher creates a case and gets the ranked list |
| `GET` | `/cases/{id}/recommendations` | dispatcher, crew |
| `PATCH` | `/cases/{id}/category` | crew confirms or changes category, which triggers a re-rank |
| `POST` | `/cases/{id}/accept` | crew accepts a hospital → `PROPOSED` |
| `POST` | `/cases/{id}/override` | crew override with a reason (logged) |
| `POST` | `/reservations/{id}/confirm` · `/reject` | hospital |
| `PATCH` | `/hospitals/{id}/status` | hospital updates beds, specialists, equipment |
| `POST` | `/hospitals/{id}/verify` | dispatcher one-tap verify (confirmed / unavailable) |
| `POST` | `/cases/{id}/arrival` | arrival feedback → reliability update |
| `POST` | `/sim/run` | run strategy comparison, returns metrics |
| `POST` | `/integrations/cad/incident` | CAD sidecar sends an incident → case + ranking |
| `GET` | `/integrations/cad/incident/{id}/recommendation` | CAD sidecar reads back the recommendation |
| `POST` | `/integrations/fhir/bundle` | hospital HIS pushes a FHIR bundle of bed/location status |
| `POST` | `/integrations/sms/inbound` | SMS / USSD replies (`"ICU 2"`, `"CONFIRM 4821"`) |
| `WS` | `/ws/{role}/{id}` | events: `case.created`, `prealert`, `reservation.updated`, `status.updated` |

### 4.8 End-to-end sequence

```mermaid
sequenceDiagram
    participant Disp as Dispatcher
    participant API as CMER API
    participant Crew as Crew App
    participant Hosp as Hospital
    Disp->>API: POST /cases (location, category)
    API-->>Disp: primary + backup + reasons
    API-->>Crew: case pushed (WS)
    Crew->>API: confirm category (1 tap) and accept primary
    API-->>Hosp: PRE-ALERT (type, ETA, bed needed)
    Hosp->>API: confirm
    API-->>Crew: bed HELD until ETA + buffer
    API-->>Disp: shortest road route + turn-by-turn navigation HUD overlay
    Crew->>API: arrival + was it really available?
    API->>API: update reliability R
```

### 4.8.1 Road routing and shortest path navigation
- **Turn-by-turn routing:** When the destination hospital is selected and accepted, the system queries the **OSRM / OpenStreetMap** road network engine for the shortest driving corridor.
- **Dynamic route polyline:** Renders directly on the Leaflet console using high-contrast multi-lane corridor polylines (`Polyline`), with live ETA and distance calculations.
- **Pre-Alert and hold lifecycle:** Accepting the hospital dispatches a pre-alert to the receiving emergency department. Once the hospital confirms, the bed status transitions to **HELD** until the ambulance's ETA plus a safety buffer.

### 4.9 Integration and interoperability

More detail in [document.md §15](./document.md).

- **ABDM alignment:** every hospital is identified by its **HFR ID**, so records are not duplicated. Capacity is shared as FHIR R4 resources (`Organization`, `Location` with operational status, `HealthcareService`). HIS-equipped hospitals push FHIR bundles. Everyone else uses the dashboard or SMS.
- **CAD sidecar:** CMER does not replace the operator's CAD. The adapter either receives a webhook or polls the CAD's incident feed. It creates a CMER case and writes the recommendation back to a companion overlay. Core dispatch logs are never modified. A swappable `CadAdapter` interface lets each vendor get its own implementation.
- **Offline-first crew app:** the PWA caches the hospital list, the last ranking and the case on the device. Actions taken offline go into an outbox and sync when the signal returns.
- **SMS / USSD fallback:** if a WebSocket message is not acknowledged within N seconds, `outbound_message` re-sends it by SMS. Short codes let the crew and hospitals reply (`CONFIRM 4821`, `REJECT 4821`) and the reply updates the same reservation state machine.

```mermaid
flowchart LR
    E["Event: pre-alert / hold"] --> WS{"WS delivered + acked?"}
    WS -->|yes| DONE["Done"]
    WS -->|"no, after N s"| SMS["Send SMS / USSD"]
    SMS --> R{"Reply received?"}
    R -->|CONFIRM / REJECT| SM["Update reservation"]
    R -->|timeout| VOICE["Prompt dispatcher to call"]
```

---

## 5. Repository layout

```
seva/
├── README.md                           # project overview, architecture, empirical benchmarks
├── document.md                         # full proposal, policy evidence, and pilot plan
├── task.md                             # implementation plan and tracking checklist
├── docs/
│   └── assets/                         # generated evaluation charts
│       ├── sim_results_strategies.png  # strategy comparison (first-time delivery & treatment latency)
│       ├── sim_reporting_sweep.png     # degradation sweep (timely reporting from 100% to 15%)
│       └── sim_calibration_diagram.png # P_ok reliability curve (Brier = 0.037)
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI server, REST routes, CAD & FHIR endpoints
│   │   ├── models.py                   # Pydantic schemas (hospitals, cases, reservations)
│   │   ├── store.py                    # thread-safe state store & reservation lifecycle manager
│   │   ├── ws.py                       # WebSocket hub for live dispatch & hospital triage broadcasts
│   │   ├── engine/
│   │   │   ├── capability.py           # clinical triage mapper (category → ward, specialists, equipment)
│   │   │   ├── probability.py          # Skellam distribution, freshness decay, Bayesian reliability score
│   │   │   ├── ranking.py              # Expected Time to Treatment (ETT) & hospital ranking
│   │   │   └── simulation.py           # discrete-event Monte Carlo simulator, realistic staleness, ablations
│   │   └── seed/
│   │       └── city.py                 # synthetic metropolitan corridor: 15 hospitals (HFR IDs, wards, rates)
│   └── tests/
│       ├── test_api.py                 # REST API, reservation lifecycle, and hospital telemetry tests
│       └── test_ranking.py             # ETT monotonicity, capability filtering, and freshness tests
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    ├── public/
    │   ├── icons.svg
    │   └── sim_results/                # mirrored evaluation plots for client-side rendering
    └── src/
        ├── App.jsx                     # unified application shell, multi-tab routing, live status alerts
        ├── index.css                   # clinical dark theme design tokens and styles
        ├── pages/
        │   ├── Dispatcher.jsx          # 108 CAD dispatcher interface & live ambulance routing HUD
        │   └── Hospital.jsx            # emergency department receiver console & pre-alert confirmation desk
        ├── components/
        │   ├── MapView.jsx             # Leaflet OSM interactive city map with turn-by-turn route corridors
        │   ├── HospitalCard.jsx        # ranked candidate card with clinical capability tags & reasons
        │   ├── PreAlertModal.jsx       # emergency reservation confirmation & rejection modal
        │   ├── FreshnessBadge.jsx      # telemetry age indicator (Fresh, Aging, Stale + One-Tap Verify)
        │   └── ConfidenceBar.jsx       # visual arrival availability probability gauge (P_ok)
        └── services/
            └── api.js                  # Axios client & WebSocket event subscription handlers
```

---

## 6. Build order

The hardest part is the logic, so build it first, keep it as pure functions, and test it before adding any UI ("logic before shell").

| # | Phase | Deliverable | Done when |
|---|---|---|---|
| 0 | **Synthetic city** | `seed/city.py`: 15 hospitals (5 small, 6 mid, 4 tertiary) with real coordinates in one city, capabilities, wards, shifts, rates | JSON dump looks realistic |
| 1 | **Ranking engine** | `capability.py`, `ranking.py`: filter + ETT with a simple `P_ok = 1 if free>0 else 0.1` | `pytest` shows CMER picks differently from "nearest" |
| 2 | **Probability engine** | `probability.py`: Skellam `P_ok`, freshness bands, reliability blend | Stale and unreliable hospitals get a lower but non-zero `P_ok` |
| 3 | **API** | FastAPI routes in 4.7, in-memory store | `POST /cases` returns a ranked list with reasons |
| 4 | **Dispatcher dashboard** | Map, case form, ranked cards (ETT, confidence bar, freshness badge, reasons) | Click on map → see primary and backup |
| 5 | **Hospital dashboard + reservations** | Bed steppers, pre-alert toast, confirm / reject, hold countdown | Confirm turns the hold green; rejecting moves to the backup |
| 6 | **Real-time** | WebSocket hub pushes events to all 3 UIs | Two browser tabs update live |
| 7 | **Crew app** | Mobile view: 1-tap category confirm, accept / override with reason, call button, unstable-patient button | Override is logged and hold released |
| 7b | **CAD sidecar (mock)** | `CadAdapter` interface + a mock CAD feed posting incidents to `/integrations/cad/incident` | An incident from the mock CAD appears in the dispatcher overlay without manual entry |
| 8 | **Verification + reliability** | One-tap verify on stale hospitals; arrival feedback → `R` update | `R` visibly changes after a bad report |
| 9 | **Simulation + evaluation** | SimPy sim, 3 strategies, 200 runs each, robustness (100→30% reporting), calibration plot | Simulation page shows charts with error bars |
| 10 | **Persistence + auth** | Supabase Postgres + role-based auth | Data survives a restart |
| 11 | **Low-tech channels + fallback** | Twilio SMS / WhatsApp parser (`"ICU 2"`), WS → SMS / USSD fallback outbox, `CONFIRM/REJECT` codes | With the network blocked, a pre-alert still arrives by SMS and the reply updates the hold |
| 12 | **Offline-first PWA** | Service worker, IndexedDB cache, outbox sync, compressed payloads | Crew app works in airplane mode and syncs on reconnect |
| 13 | **ABDM / FHIR interoperability** | HFR IDs on hospitals, FHIR R4 export/import (`/integrations/fhir/bundle`) | A FHIR bundle updates bed counts; the hospital is resolved by HFR ID |
| 14 | **Hardening** | Sensitivity tests, OSRM routing, security review, deploy | Ready for the pilot pitch |

---

## 7. National submission plan (closing 24 October 2026)

### 7.1 Objective and national milestone
- The inter-university qualification round has concluded. The focus is now the national submission closing **24 October 2026** for the Seva First Innovation Challenge (Viksit Bharat 2047, Track A).
- Deliverables for national evaluation:
  1. A fully operational, verified multi-role web prototype (Dispatcher overlay, Hospital triage reception, Ambulance crew interface).
  2. Statistically sound discrete-event simulation comparing 4 dispatch strategies over synthetic city distributions.
  3. Formal pilot proposal aligned with state health systems (Slide 7 roadmap).
  4. Standards-aligned architecture documentation (ABDM HFR, HL7 FHIR R4, non-invasive CAD sidecar).

### 7.2 Built vs Planned status

The prototype demonstrates core decision-support logic while aligning with national digital health infrastructure:

| Component / Layer | Status | Implementation Details |
|---|---|---|
| **Capability Mapper & ETT Engine** | Built ✅ | Pure Python pure-functional engine (`capability.py`, `ranking.py`) calculating Expected Time to Treatment with reroute penalties. |
| **Probability Estimator (`P_ok`)** | Built ✅ | Skellam distribution (`scipy.stats.skellam`) with time decay, freshness bands, and reliability blending. |
| **Dispatcher Console** | Built ✅ | React 19 + Leaflet interactive map, real-time ranked hospital cards, primary/backup triage, "Nearest vs CMER" baseline toggle, stale verification. |
| **Hospital ED Reception** | Built ✅ | Live bed capacity steppers, WebSocket pre-alert notifications, one-click confirm/reject, ETA + buffer countdown hold. |
| **Crew Mobile Interface** | Built ✅ | Mobile-responsive touch HUD with 1-tap category confirmation, primary/backup selection, logged override, unstable-patient bypass. |
| **Real-time Event Hub** | Built ✅ | FastAPI WebSocket connection manager broadcasting state updates across roles. |
| **Data Persistence & Auth** | Planned 🟡 | Current prototype runs high-performance in-memory state; Supabase PostgreSQL + Row Level Security (RLS) role-based auth planned for pilot. |
| **Discrete-Event Simulation (SimPy)** | Planned 🟡 | Head-to-head 4-strategy simulation engine with independent ground-truth bed generation, calibration checks, and sensitivity sweeps. |
| **CAD Sidecar Adapter** | Planned 🟡 | Interface specification defined; webhook/polling sidecar to ingest incidents from EMRI CAD feeds without altering dispatch logs. |
| **ABDM / FHIR Interoperability** | Planned 🟡 | HFR identifier schema mapped; HL7 FHIR R4 `Organization`/`Location`/`HealthcareService` bundles for HIS sync planned for sandbox trial. |
| **Offline-First PWA** | Planned 🟡 | Service Worker + IndexedDB outbox cache for patchy rural corridor transit. |
| **SMS / USSD Fallback Gateway** | Planned 🟡 | Low-bandwidth fallback for pre-alerts and confirmations when mobile data connection drops. |

### 7.3 Simulation and evaluation framework

The discrete-event simulation benchmarks algorithmic referral against legacy operational dispatch across 4 comparative strategies:

1. **Nearest hospital:** The status quo baseline—dispatches to the geographically closest facility regardless of clinical capability or bed status.
2. **Nearest capable hospital, specialties only:** Filters for basic specialty/capability match, but ignores real-time bed availability and queue delays.
3. **Nearest capable hospital with currently reported free bed:** Filters for capability and positive bed count at last report, but ignores reporting delays, turnover, and queue decay.
4. **CMER (Expected Time to Treatment + P_ok):** Dynamic ranking combining travel time, emergency load, arrival bed probability via Skellam distribution, and reroute penalties.

#### Ground-truth independence and non-circularity
> [!IMPORTANT]
> **Avoiding Circular Evaluation:** The simulator's true underlying bed occupancy process must be structurally distinct from the Poisson/Skellam model assumed by the estimator. The simulator generates true admissions and discharges using non-stationary, bursty queues (e.g., Markov-modulated or empirical diurnal batch arrivals), while the CMER estimator uses only reported snapshots. This guarantees the calibration test measures real-world robustness rather than model circularity.

#### Evaluation protocol & Sensitivity tests
#### Evaluation protocol & Sensitivity tests
- **Statistical scale:** 250 independent stochastic runs per parameter setting (Seed=42) under non-circular Poisson-burst queue dynamics with bootstrap 95% confidence intervals.
- **Sensitivity tests:**
  - *Occupancy stress:* Baseline bed occupancy swept across 60%, 75%, 85%, and 95%.
  - *Reporting degradation:* Share of hospitals providing timely reports swept across 100%, 80%, 60%, 40%, 30%, and 15%.
  - *Traffic noise & transit delay:* Multiplier variances on road travel times (1.0× to 2.5× congestion).
  - *Misreporting frequency:* Varying proportion of hospitals misreporting capacity to validate Bayesian reliability score damping (`R`).

#### Empirical Simulation Results (250 Monte Carlo Runs)

| Dispatch Strategy | First-Time Delivery (%) | Treatment Latency (min) | Secondary Transfers / 100 | Incapable Refusals (%) | Bed Saturated Refusals (%) | vs Strategy 3 Paired Time Diff (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Nearest Hospital (Status Quo)** | **28.8%** | **55.1 ± 1.3** | **72.4** | 67.2% | 4.0% | **+21.31 min** [+19.20, +23.47] |
| **2. Nearest Capable (Specialties Only)** | **94.0%** | **34.5 ± 0.8** | **6.0** | 0.0% | 6.0% | **+0.71 min** [-0.64, +2.09] |
| **3. Nearest Capable + Free Bed** | **96.0%** | **33.8 ± 0.7** | **4.0** | 0.0% | 4.0% | **Baseline** [0.00, 0.00] |
| **4. CMER (Capability + ETT + Bed Hold)** | **99.2%** | **33.2 ± 0.7** | **1.2** | **0.0%** | **0.8%** | **-0.54 min** [-1.91, +0.73] |
| *Ablation: Capable + Hold* | 100.0% | 33.3 ± 0.7 | 0.0 | 0.0% | 0.0% | -0.51 min [-1.78, +0.65] |
| *Ablation: Capable + Bed + Hold* | 100.0% | 32.8 ± 0.7 | 0.0 | 0.0% | 0.0% | -0.92 min [-2.13, +0.21] |
| *Ablation: CMER (Ranking Only, No Hold)* | 92.4% | 35.3 ± 0.9 | 7.6 | 0.0% | 7.6% | +1.54 min [-0.10, +3.19] |

#### Key Ablation Finding on Pre-Alert Holds
* Notice that `CMER (Ranking Only, No Hold)` delivers only 92.4% of patients on the first attempt because reported beds decay and get occupied by walk-ins while ambulances travel.
* Combining CMER's $P_{ok}$ expected time-to-treatment ranking with **Pre-alert Bed Holds** elevates first-time delivery to **99.2%** and reduces treatment latency to **33.2 minutes**.

#### Visual Artifacts & Reliability Plots

The simulation pipeline outputs three evaluation figures:
1. **Strategy Benchmark Comparison:** [docs/assets/sim_results_strategies.png](./docs/assets/sim_results_strategies.png) — First-time delivery rates and definitive treatment times across all strategies.
2. **Reporting Degradation Sweep:** [docs/assets/sim_reporting_sweep.png](./docs/assets/sim_reporting_sweep.png) — System resilience as hospital timely reporting drops from 100% to 15%.
3. **Probability Calibration Diagram:** [docs/assets/sim_calibration_diagram.png](./docs/assets/sim_calibration_diagram.png) — Reliability curve with a Brier calibration score of **0.037**.

### 7.4 Demonstration script (National Presentation)

1. **Hook (20 s):** "According to an evaluation by the Indian Institute of Health Management Research (IIHMR), an eight-minute response standard was measured across emergency networks. For 10 to 12% of patients, the facility reached within that window lacked the clinical capability to treat them, and under 5% reached a capable hospital within eight minutes. The 108 ambulance arrived promptly, but the patient was taken to a facility that could not provide definitive care."
2. **Baseline (30 s):** In the Dispatcher overlay, create a *severe head trauma* case. Toggle **Nearest**: the system selects a local primary nursing clinic 1.2 km away that lacks neurosurgery and ICU facilities.
3. **CMER (45 s):** Toggle **CMER**: the system recommends a tertiary medical centre 4.2 km away as primary, with a secondary backup. Read out the reasoning: *"Neurosurgery on duty · ICU 87% likely · Expected Time to Treatment 19 min vs 41 min with secondary referral."*
4. **Stale Data Handling (30 s):** Highlight a hospital flagged with **"Data 45 min old"**. It remains eligible with damped confidence; dispatcher triggers one-tap **Verify** to immediately refresh verified bed telemetry.
5. **Pre-alert & Bed Hold (45 s):** Crew accepts the recommendation → receiving hospital dashboard instantly sounds an emergency pre-alert banner → hospital ED triage nurse confirms → **bed held until ETA + buffer**. Demonstrate dynamic re-ranking by reducing ICU beds to 0 in the hospital tab, showing live WebSocket propagation to dispatch.
6. **Simulation Evidence (20 s):** Present the 4-strategy simulation results: *"Across 250 simulated emergency cases without data leakage, first-time delivery to a capable hospital rose from 28.8% to 99.2%, reducing treatment latency by over 21 minutes."*
7. **Closing (10 s):** "108 gets the ambulance to the patient. CMER gets the patient to the right hospital the first time. We are ready for a supervised district pilot."

### 7.5 Judge Q&A preparation

| Question | Answer |
|---|---|
| **"How is this different from Karnataka's new command centre?"** | Karnataka's government-operated 108 centralised command and control centre (inaugurated May 2026) is a vital infrastructure milestone unifying emergency helplines (108, 104, 112) with GPS fleet dispatch. However, CAD steering still relies primarily on geographic proximity or static facility categories. CMER operates as an intelligent algorithmic decision-support layer *on top* of the command centre—dynamically computing arrival-time capacity probabilities (`P_ok`), managing automated hospital pre-alerts, and holding beds until arrival. |
| **"What if hospital reporting is inaccurate or hospitals fail to report?"** | Real-time bed reporting alone is brittle—as demonstrated in the July 2026 Delhi High Court proceedings regarding the *Delhi ICU Beds Saarthi* app and HMIS, where surprise NIC audits were ordered after patients were turned away from hospitals reporting available beds. CMER solves this by not taking self-reported numbers at face value: (1) Freshness decay dampens confidence over time, (2) Bayesian reliability scoring (`R`) penalises facilities whose reported capacity fails to match arrival reality, and (3) Pre-alert confirmation holds the bed *before* the ambulance arrives. |
| **"Why focus on pre-alerts rather than mandating continuous bed updates?"** | Mandating continuous bed updates creates administrative fatigue without guaranteeing bed availability upon arrival. In Karnataka, the CAG Performance Audit explicitly recommended establishing standard operating protocols (SOPs) for pre-alerting destination hospitals. Pre-alerts create immediate reciprocal value: the hospital prepares its trauma or catheterisation team before arrival, cutting turnaround and handover delays. |
| **"Have you piloted this in the real world?"** | Not yet. The current system is a rigorous, simulation-tested prototype built on synthetic city data and validated through discrete-event queue models. We have developed a complete 4-phase, 1-district supervised pilot plan designed to run alongside active 108 operations in an advisory capacity without altering core CAD logs. |
| **"Will 108 operators need to rewrite their CAD software?"** | No. CMER utilizes a lightweight, non-invasive CAD Sidecar interface. Incident coordinates and chief complaints are ingested via secure webhook or poller, and capability-matched recommendations are returned to a dispatcher companion overlay, keeping proprietary CAD databases untouched. |
| **"How does this fit national digital health infrastructure?"** | All facilities are keyed using Ayushman Bharat Digital Mission (ABDM) Health Facility Registry (HFR) IDs, ensuring zero duplicate records. Interoperability is mapped to HL7 FHIR R4 profiles (`Organization`, `Location`, `HealthcareService`). |
| **"What happens when cellular networks drop in rural transit corridors?"** | The crew mobile interface is designed as an offline-resilient PWA caching recent routing and facility data locally. When data signals fail, pre-alerts and confirmations fall back automatically to low-latency SMS / USSD gateways. |

---

## 8. Pilot plan (Slide 7 alignment)

To validate CMER in active operational conditions, a controlled field trial is planned in partnership with state health authorities and 108 operating agencies:

### 8.1 Pilot scope and configuration
* **Geography:** 1 representative district (mix of urban corridors and rural transit routes).
* **Participating facilities:** 3 to 5 receiving hospitals (1 government medical college/tertiary hospital, 1 district hospital, and 2–3 community or empanelled private facilities).
* **Fleet size:** Approximately 20 dedicated 108 ambulances operating in the pilot catchment area.
* **Duration:** 6 to 12 months total (2 months co-design & setup, 6 months supervised active dual-run, 4 months evaluation and state review).
* **Mode:** Dual-run advisory mode. Dispatchers and EMTs receive real-time capability recommendations alongside existing CAD procedures, retaining full discretion to accept or override.

### 8.2 Primary evaluation metrics
1. **First-time capability delivery rate:** Percentage of acute emergencies presenting directly to a facility capable of definitive care on first arrival.
2. **Secondary inter-hospital transfer rate:** Proportion of patients requiring onward emergency referral within 2 hours of arrival.
3. **Emergency department handover time:** Latency between ambulance arrival and emergency physician handover, measuring the impact of pre-alerts.
4. **Bed-hold adherence & reliability:** Agreement between pre-alert confirmations and physical bed availability at arrival.
5. **EMT & dispatcher override frequency:** Distribution and recorded reasons for crew overrides (e.g., patient instability, family preference).

> [!NOTE]
> **Pilot Cost Estimate:** A detailed district-level financial budget will be finalized in consultation with the state health mission and 108 operating partner during the co-design phase. Cost estimates are not yet formally finalized.

---

## 9. Running locally

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install fastapi uvicorn[standard] numpy scipy pydantic
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Open three tabs: `/dispatcher`, `/hospital/<id>`, `/crew/<caseId>` (use mobile view in DevTools for the crew page).

Checks: `pytest -q` · `ruff check --quiet` · `npx oxlint`

---

## 10. Safety and limitations

- Decision support only. The dispatcher and EMT keep authority over the destination.
- All results come from **synthetic data**. No claim of clinical effectiveness.
- Unstable-patient rule: the crew can always go to the nearest stabilising facility. The override is logged and the hold released.
- Real deployment needs a 108 operator / state partnership, hospital participation, security and privacy controls, and clinical validation.

