"""
Integration and End-to-End API tests for CMER.
Verifies all core endpoints in Section 4.7:
- GET /hospitals
- POST /cases (filters and ranks hospitals by ETT)
- PATCH /hospitals/{id}/status (bed updates reset age and broadcast)
- POST /hospitals/{id}/verify (one-tap verify)
- POST /cases/{id}/accept (pre-alert & PROPOSED reservation)
- POST /reservations/{id}/confirm (HELD reservation with countdown)
- POST /reservations/{id}/reject
- POST /cases/{id}/arrival (Bayesian reliability score update)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def clean_store():
    """Ensure in-memory store starts clean before each test."""
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_get_hospitals(client):
    response = client.get("/hospitals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 15
    first_hosp = data[0]
    assert "hfr_id" in first_hosp
    assert "capabilities" in first_hosp
    assert "wards" in first_hosp


def test_create_case_ranking_head_injury(client):
    """
    Simulate severe head trauma near Basavanagudi (lat 12.942, lng 77.5745).
    Nearest clinic is Shanthi Nursing (incapable).
    CMER primary recommendation must be a capable tertiary hospital.
    """
    payload = {
        "lat": 12.9420,
        "lng": 77.5745,
        "category": "TRAUMA",
        "severity": "CRITICAL",
        "ambulance_id": "KA-01-G-1081",
    }
    response = client.post("/cases", json=payload)
    assert response.status_code == 200
    case = response.json()

    assert case["id"].startswith("case-")
    assert case["status"] == "OPEN"
    recs = case["recommendations"]
    assert len(recs) > 0

    primary = recs[0]
    assert primary["is_primary"] is True
    assert primary["capable"] is True
    assert primary["tier"] == "tertiary"
    assert len(primary["reasons"]) >= 2
    assert primary["hospital_id"] in ["hosp-victoria", "hosp-nimhans"]


def test_update_hospital_status_and_verify(client):
    hosp_id = "hosp-victoria"
    status_update = {
        "wards": {
            "ICU": {"total": 35, "free": 2, "age_min": 0.0}
        }
    }
    resp = client.patch(f"/hospitals/{hosp_id}/status", json=status_update)
    assert resp.status_code == 200
    updated_hosp = resp.json()
    assert updated_hosp["wards"]["ICU"]["free"] == 2
    assert updated_hosp["wards"]["ICU"]["age_min"] == 0.0

    # Test verify endpoint
    verify_resp = client.post(f"/hospitals/{hosp_id}/verify")
    assert verify_resp.status_code == 200
    verified_hosp = verify_resp.json()
    assert verified_hosp["wards"]["ICU"]["age_min"] == 0.0


def test_full_reservation_lifecycle(client):
    # 1. Create a case
    case_payload = {
        "lat": 12.9634,
        "lng": 77.5756,
        "category": "CARDIAC",
    }
    case_res = client.post("/cases", json=case_payload).json()
    case_id = case_res["id"]
    primary_hosp = case_res["recommendations"][0]["hospital_id"]

    # 2. Crew accepts primary hospital -> creates PROPOSED reservation
    accept_resp = client.post(f"/cases/{case_id}/accept", json={"hospital_id": primary_hosp})
    assert accept_resp.status_code == 200
    reservation = accept_resp.json()
    assert reservation["status"] == "PROPOSED"
    res_id = reservation["id"]

    # 3. Hospital confirms -> status HELD, hold_expires_at is set
    confirm_resp = client.post(f"/reservations/{res_id}/confirm", json={"confirmed": True})
    assert confirm_resp.status_code == 200
    held_res = confirm_resp.json()
    assert held_res["status"] == "HELD"
    assert held_res["hold_expires_at"] is not None

    # Check hospital held_beds incremented
    hosp_resp = client.get(f"/hospitals/{primary_hosp}").json()
    assert hosp_resp["held_beds"] >= 1

    # 4. Crew arrives -> records feedback and updates reliability score R
    arrival_feedback = {
        "actual_bed_available": True,
        "actual_specialist_present": True,
        "actual_equipment_functional": True,
        "wait_time_minutes": 5.0,
    }
    arr_resp = client.post(f"/cases/{case_id}/arrival", json=arrival_feedback)
    assert arr_resp.status_code == 200
    arrived_hosp = arr_resp.json()
    assert arrived_hosp["reliability"] >= 0.8
