"""
Ranking Engine for CMER.
Calculates Expected Time to Treatment (ETT):
ETT(h) = Travel_Time(h) + ER_Delay(h) + (1 - P_ok(h)) * Reroute_Penalty(h)

Pure Python functions: does not depend on database or web framework.
Can be invoked identically by FastAPI endpoints and discrete-event simulators.
"""

import math
from typing import List, Dict, Any, Tuple
from app.engine.capability import is_hospital_capable, get_target_ward
from app.engine.probability import compute_p_ok


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def estimate_travel_time_minutes(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    road_factor: float = 1.4,
    avg_speed_kmh: float = 30.0,
) -> float:
    """
    Estimates emergency ambulance travel time with urban detour and traffic noise.
    Distance (road) = haversine * road_factor.
    Time (min) = (Distance / speed) * 60.
    """
    crow_dist = haversine_distance_km(lat1, lon1, lat2, lon2)
    road_dist = crow_dist * road_factor
    time_min = (road_dist / max(10.0, avg_speed_kmh)) * 60.0
    return round(max(2.0, time_min), 1)


def generate_reasons(
    hospital: Dict[str, Any],
    p_ok: float,
    freshness_band: str,
    age_min: float,
    travel_min: float,
    category: str,
) -> List[str]:
    """Generates human-readable clinical rationale explanations for dispatchers and EMTs."""
    reasons = []

    # Specialist explanation
    specialists = hospital.get("specialists", {})
    if category.upper() in ["TRAUMA", "STROKE"] and specialists.get("NEURO", {}).get("on_duty"):
        reasons.append("Neurosurgeon on duty")
    elif category.upper() == "CARDIAC" and specialists.get("CARDIAC", {}).get("on_duty"):
        reasons.append("Interventional Cardiologist present")
    elif category.upper() == "OBSTETRIC" and specialists.get("OBSTETRIC", {}).get("on_duty"):
        reasons.append("Obstetrician on duty")

    # Equipment / ICU explanation
    target_ward = get_target_ward(category)
    ward_info = hospital.get("wards", {}).get(target_ward, hospital.get("wards", {}).get("ER", {}))
    free_beds = ward_info.get("free", 0)
    p_pct = int(p_ok * 100)

    if free_beds > 0:
        reasons.append(f"{target_ward} has {free_beds} confirmed beds ({p_pct}% probable)")
    else:
        reasons.append(f"{target_ward} near full ({p_pct}% availability probability)")

    # Travel time
    reasons.append(f"ETA ~{int(travel_min)} min")

    # Freshness warning
    if freshness_band == "stale":
        reasons.append(f"Data {int(age_min)}m old: verify recommended")
    elif freshness_band == "aging":
        reasons.append(f"Data {int(age_min)}m old")

    return reasons


def rank_hospitals(
    hospitals: List[Dict[str, Any]],
    case_lat: float,
    case_lng: float,
    category: str,
    reroute_overhead_min: float = 25.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filters capable hospitals and ranks them by Expected Time to Treatment (ETT).
    Returns (cmer_ranked_list, baseline_nearest_list).
    """
    target_ward = get_target_ward(category)

    # 1. Baseline nearest ranking (for baseline comparison)
    baseline_all = []
    for h in hospitals:
        t_time = estimate_travel_time_minutes(case_lat, case_lng, h["lat"], h["lng"])
        capable = is_hospital_capable(h, category)
        baseline_all.append({
            "hospital_id": h["id"],
            "name": h["name"],
            "tier": h["tier"],
            "travel_time": t_time,
            "capable": capable,
            "raw_hospital": h,
        })
    baseline_all.sort(key=lambda x: x["travel_time"])

    # 2. Filter capable hospitals for CMER
    capable_candidates = [h for h in hospitals if is_hospital_capable(h, category)]
    if not capable_candidates:
        # Fallback to general capable hospitals if no facility has the full stack
        capable_candidates = [h for h in hospitals if "ER" in h.get("capabilities", [])]

    # Pre-calculate travel times for candidates
    candidate_travel: Dict[str, float] = {}
    for h in capable_candidates:
        candidate_travel[h["id"]] = estimate_travel_time_minutes(
            case_lat, case_lng, h["lat"], h["lng"]
        )

    # 3. Compute ETT for each capable candidate
    cmer_results = []
    for h in capable_candidates:
        h_id = h["id"]
        t_time = candidate_travel[h_id]
        er_delay = h.get("er_load", {}).get("est_delay_min", 10.0)

        # Estimate P_ok
        p_ok, freshness_band, age_min = compute_p_ok(h, target_ward, t_time, category)

        # Reroute penalty: travel to nearest other capable hospital + handling overhead
        other_travels = [
            estimate_travel_time_minutes(h["lat"], h["lng"], other["lat"], other["lng"])
            for other in capable_candidates if other["id"] != h_id
        ]
        nearest_other_dist_time = min(other_travels) if other_travels else 15.0
        reroute_penalty = nearest_other_dist_time + reroute_overhead_min

        # ETT equation
        ett = t_time + er_delay + ((1.0 - p_ok) * reroute_penalty)
        ett = round(ett, 1)

        reasons = generate_reasons(h, p_ok, freshness_band, age_min, t_time, category)

        cmer_results.append({
            "hospital_id": h_id,
            "hfr_id": h.get("hfr_id", ""),
            "name": h["name"],
            "tier": h["tier"],
            "lat": h.get("lat", 0.0),
            "lng": h.get("lng", 0.0),
            "ett": ett,
            "travel_time": t_time,
            "travel_time_min": t_time,
            "er_delay": er_delay,
            "er_delay_min": er_delay,
            "p_ok": p_ok,
            "freshness_band": freshness_band,
            "data_age_min": age_min,
            "reasons": reasons,
            "capable": True,
            "raw_hospital": h,
        })

    # Sort CMER by ETT ascending
    cmer_results.sort(key=lambda x: x["ett"])

    # Assign ranks
    for idx, item in enumerate(cmer_results):
        item["rank"] = idx + 1

    return cmer_results, baseline_all
