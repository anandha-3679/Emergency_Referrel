"""
Unit and Integration Tests for Capability Mapping and Ranking Engine.
Tests the core scenario:
- Head injury / trauma case where the nearest clinic is 1.2 km away with NO neurosurgery/CT,
  while tertiary hospital 4 km away has complete capability.
- Validates that CMER filters out the incapable clinic and picks the tertiary facility as Primary.
- Validates that Stale data receives appropriate freshness penalties.
"""

from app.seed.city import get_seed_hospitals
from app.engine.capability import is_hospital_capable, get_required_capabilities
from app.engine.ranking import rank_hospitals, estimate_travel_time_minutes
from app.engine.probability import compute_p_ok


def test_capability_filtering_head_injury():
    """Head injury requires TRAUMA, NEURO, ICU, CT."""
    reqs = get_required_capabilities("TRAUMA")
    assert "TRAUMA" in reqs
    assert "NEURO" in reqs
    assert "ICU" in reqs
    assert "CT" in reqs

    hospitals = get_seed_hospitals()
    h_small = next(h for h in hospitals if h["id"] == "hosp-shanthi-nursing")
    h_tertiary = next(h for h in hospitals if h["id"] == "hosp-victoria")

    assert not is_hospital_capable(h_small, "TRAUMA")
    assert is_hospital_capable(h_tertiary, "TRAUMA")


def test_cmer_vs_nearest_trauma_case():
    """
    Test coordinate placed in Basavanagudi near Shanthi Nursing Home (lat 12.942, lng 77.575).
    Baseline nearest picks Shanthi Nursing Home (~0.5 km away).
    CMER MUST pick a tertiary facility (Victoria Hospital or NIMHANS) because Shanthi lacks Trauma/Neuro.
    """
    hospitals = get_seed_hospitals()
    case_lat = 12.9420
    case_lng = 77.5745

    cmer_ranked, baseline_nearest = rank_hospitals(
        hospitals=hospitals,
        case_lat=case_lat,
        case_lng=case_lng,
        category="TRAUMA",
    )

    # 1. Baseline nearest
    top_baseline = baseline_nearest[0]
    assert top_baseline["hospital_id"] == "hosp-shanthi-nursing"
    assert not top_baseline["capable"], "Shanthi Nursing should NOT be capable for severe trauma"

    # 2. CMER Primary recommendation
    top_cmer = cmer_ranked[0]
    assert top_cmer["capable"] is True
    assert top_cmer["tier"] == "tertiary"
    assert top_cmer["hospital_id"] in ["hosp-victoria", "hosp-nimhans"]
    assert len(top_cmer["reasons"]) >= 2
    print(f"\nCMER #1: {top_cmer['name']} (ETT: {top_cmer['ett']}m, P_ok: {top_cmer['p_ok']})")
    print(f"Reasons: {top_cmer['reasons']}")


def test_stale_data_freshness_detection():
    """Manipal Hospital is seeded with 42 min old ICU data (stale band)."""
    hospitals = get_seed_hospitals()
    h_manipal = next(h for h in hospitals if h["id"] == "hosp-manipal-hal")

    p_ok, band, age = compute_p_ok(
        hospital=h_manipal,
        ward_name="ICU",
        travel_time_min=15.0,
        category="TRAUMA",
    )

    assert band == "stale"
    assert age >= 30
    assert 0.0 < p_ok < 1.0


def test_distance_and_ett_monotonicity():
    """Verify that travel time increases smoothly with coordinate distance."""
    t1 = estimate_travel_time_minutes(12.90, 77.50, 12.91, 77.51)
    t2 = estimate_travel_time_minutes(12.90, 77.50, 12.99, 77.59)
    assert t2 > t1
