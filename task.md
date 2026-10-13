# Task Tracking: Capability-Matched Emergency Referral (CMER)

## Architecture Overview
- **Backend:** FastAPI (Python 3.12) with pure mathematical ranking engine (`scipy.stats` Skellam distribution for $P_{ok}$ + ETT optimization).
- **Frontend:** React 19 + Vite (JavaScript/JSX), Leaflet maps, dark clinical theme.
- **Interoperability:** CAD Sidecar interface, ABDM Health Facility Registry (HFR) IDs, FHIR R4 schema alignment, and offline-first / SMS-USSD fallback mechanism.

## Immediate Next Steps
- [ ] Build Crew App (`/crew` 1-tap accept/override mobile view) and Frontend Simulation View (`/simulation`).

## Completed Tasks
- [x] Bootstrapped token-efficient agent rules (`.antigravityrules`)
- [x] Configured quiet linter (`ruff.toml`)
- [x] Initialized architecture specification and prototype roadmap (`README.md`, `document.md`)
- [x] Discrete-Event Simulation Pipeline (`backend/app/engine/simulation.py`):
  - 4-strategy head-to-head Monte Carlo comparison across 200 independent stochastic runs.
  - Non-circular ground-truth bed queue dynamics (burst walk-in admissions & log-normal stay proxy).
  - Pre-alert bed hold vs unheld bed race conditions.
  - Automated plot generation (`sim_results_strategies.png`, `sim_calibration_diagram.png`, `sim_reporting_sweep.png`).
  - REST endpoint: `GET /simulation/results`.
- [x] Scaffolding & Seed Data (Python venv, Vite React, 15 synthetic Bengaluru hospitals with HFR IDs)
- [x] Capability Mapping & Ranking Engine:
  - `backend/app/engine/capability.py`: maps clinical emergencies (TRAUMA, CARDIAC, STROKE, etc.) to capability profiles and target wards.
  - `backend/app/engine/probability.py`: computes $P_{ok}$ using Scipy Skellam distribution, freshness decay (fresh/aging/stale), and reliability blending.
  - `backend/app/engine/ranking.py`: pure-Python ETT optimization pipeline + clinical rationale explanations.
  - `backend/tests/test_ranking.py`: 4 tests passed verifying that CMER bypasses incapable clinics for severe trauma cases and correctly accounts for stale data.
- [x] API Layer & Real-time Hub:
  - `backend/app/models.py`: Pydantic models with strict typing, clinical categories, and ABDM HFR identifier alignment.
  - `backend/app/store.py`: In-memory datastore for 15 hospitals, active cases, reservations, held bed tracking, and event logs.
  - `backend/app/ws.py`: WebSocket manager for role-based channels (`dispatcher:all`, `hospital:{id}`, `crew:{case_id}`).
  - `backend/app/main.py`: REST routes (`GET /hospitals`, `POST /cases`, `PATCH /hospitals/{id}/status`, `POST /hospitals/{id}/verify`, `POST /cases/{id}/accept`, `POST /reservations/{id}/confirm`, `/reject`, `POST /cases/{id}/arrival`, `/events` polling, `/ws`).
  - `backend/tests/test_api.py`: 4 end-to-end integration tests verifying ranking, bed updates, reservations, and reliability score updates. All 8 backend tests passing.
- [x] Dispatcher Dashboard (Frontend):
  - `frontend/src/pages/Dispatcher.jsx`: Full clinical console with incident triage selector, one-tap hospital verification, and WebSocket listeners.
  - `frontend/src/components/MapView.jsx`: High-contrast CartoDB Dark Matter map with interactive hospital markers colored by capability/freshness and click-to-reposition incident pin.
  - `frontend/src/components/HospitalCard.jsx`: Displays ETT in minutes, P(ok) confidence bar, freshness badge, and clinical rationale breakdown.
  - Interactive "CMER (Capability + ETT)" vs "Baseline Nearest" toggle demonstrating the core problem.
  - "Incoming from 108 CAD" integration simulation button.
- [x] Hospital Dashboard & Reservations:
  - `frontend/src/pages/Hospital.jsx`: Real-time hospital reception portal with dropdown facility switcher (`/hospital/:id`).
  - Interactive Bed Steppers (+ / -) for ICU, ER, Trauma, Burns wards that dynamically push bed updates over WebSockets and trigger re-ranking.
  - On-Duty Specialist and Operational Equipment toggle roster (Neurosurgeon, Interventional Cardiologist, CT scanner, etc.).
  - `frontend/src/components/PreAlertModal.jsx`: High-priority siren modal for incoming 108 pre-alerts with 2-minute countdown timer and 1-tap "Confirm & Hold Bed" or "Reject".
  - Active reservation cards showing hold status and expiration times.


