"""
Probability Estimation Engine for CMER.
Implements:
1. Skellam-based bed availability distribution: P_bed = P(free(T) - held >= 1)
   where free(T) = f0 + Skellam(discharge_rate * T, admission_rate * T).
2. Freshness bands: Fresh (<=15 min), Aging (15-30 min), Stale (>30 min).
3. Reliability blending: P_ok' = R * P_ok + (1 - R) * P_prior.
4. Total availability: P_ok_total = P_bed * P_specialist * P_equipment.
"""

from typing import Dict, Any, Tuple
from scipy.stats import skellam


def compute_freshness_band(age_minutes: float) -> Tuple[str, float]:
    """
    Categorizes the age of reported data into freshness bands and confidence multiplier.
    - Fresh: <= 15 min (multiplier 1.0)
    - Aging: 15 to 30 min (multiplier 0.85)
    - Stale: > 30 min (multiplier 0.65)
    """
    if age_minutes <= 15:
        return "fresh", 1.0
    elif age_minutes <= 30:
        return "aging", 0.85
    else:
        return "stale", 0.65


def estimate_bed_probability(
    free_beds: int,
    held_beds: int,
    travel_time_min: float,
    report_age_min: float,
    discharge_rate_per_min: float = 0.05,
    admission_rate_per_min: float = 0.06,
    turnover_buffer: int = 0,
) -> float:
    """
    Computes exact probability of bed availability on arrival using Skellam distribution.
    f(T) = free_beds + Skellam(mu1, mu2) where mu1 = d * T, mu2 = a * T.
    Condition for success: free(T) - held_beds - turnover_buffer >= 1.
    """
    # Net effective beds available right now
    net_free = free_beds - held_beds - turnover_buffer
    total_time_t = max(1.0, travel_time_min + report_age_min)

    mu1 = discharge_rate_per_min * total_time_t
    mu2 = admission_rate_per_min * total_time_t

    # Required random difference X = (discharges - admissions) >= (1 - net_free)
    # Target: P(X >= k) = 1 - cdf(k - 1)
    k = 1 - net_free
    if k <= -5:
        # We have plenty of beds (e.g. net_free >= 6), probability is near 1.0
        prob = 0.99
    elif k >= 10:
        # Deeply negative bed deficit, probability is near 0.01
        prob = 0.02
    else:
        # Survival function sf(x) = 1 - cdf(x) gives P(X > x)
        # We want P(X >= k) = P(X > k - 1)
        prob = float(skellam.sf(k - 1, mu1, mu2))

    return max(0.01, min(0.99, prob))


def compute_p_ok(
    hospital: Dict[str, Any],
    ward_name: str,
    travel_time_min: float,
    category: str,
) -> Tuple[float, str, float]:
    """
    Computes total probability P_ok of receiving treatment, incorporating:
    - Bed probability (Skellam)
    - Specialist availability
    - Equipment availability
    - Historical reliability blend
    Returns: (p_ok, freshness_band, age_minutes)
    """
    from app.engine.capability import get_effective_ward
    eff_ward_name = get_effective_ward(hospital, category)
    ward = hospital.get("wards", {}).get(eff_ward_name)
    if not ward:
        # Hospital has specialty listed in capability but zero designated ward beds for this condition!
        # Penalize heavily (0 free beds, aged status) rather than borrowing standard ER beds
        ward = {"free": 0, "total": 0, "age_min": 60.0, "held": 0}

    free_beds = ward.get("free", 0)
    held_beds = ward.get("held", 0)
    age_min = ward.get("age_min", 15)

    rates = hospital.get("rates", {}).get(eff_ward_name, {"d": 0.05, "a": 0.06})
    d_rate = rates.get("d", 0.05) / 60.0  # convert hourly to per-minute
    a_rate = rates.get("a", 0.06) / 60.0


    p_bed = estimate_bed_probability(
        free_beds=free_beds,
        held_beds=held_beds,
        travel_time_min=travel_time_min,
        report_age_min=age_min,
        discharge_rate_per_min=d_rate,
        admission_rate_per_min=a_rate,
    )

    # Specialist check for category
    p_specialist = 1.0
    specialists = hospital.get("specialists", {})
    if category.upper() in ["TRAUMA", "STROKE"]:
        neuro = specialists.get("NEURO", {"on_duty": True})
        if not neuro.get("on_duty", True):
            p_specialist *= 0.2
    elif category.upper() == "CARDIAC":
        cardiac = specialists.get("CARDIAC", {"on_duty": True})
        if not cardiac.get("on_duty", True):
            p_specialist *= 0.2
    elif category.upper() == "OBSTETRIC":
        obs = specialists.get("OBSTETRIC", {"on_duty": True})
        if not obs.get("on_duty", True):
            p_specialist *= 0.3

    # Equipment multiplier
    p_equip = 1.0
    equip = hospital.get("equipment", {})
    if category.upper() in ["TRAUMA", "STROKE"] and not equip.get("CT", True):
        p_equip *= 0.25
    if category.upper() == "CARDIAC" and not equip.get("CATH_LAB", True):
        p_equip *= 0.25

    p_raw = p_bed * p_specialist * p_equip

    # Freshness attenuation
    freshness_band, freshness_factor = compute_freshness_band(age_min)
    p_fresh = p_raw * freshness_factor

    # Reliability widening: P_ok' = R * P_fresh + (1 - R) * P_prior (prior = 0.4)
    r_score = hospital.get("reliability", 0.8)
    p_prior = 0.40
    p_final = (r_score * p_fresh) + ((1.0 - r_score) * p_prior)

    return round(max(0.02, min(0.98, p_final)), 3), freshness_band, age_min
