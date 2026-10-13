"""
SimPy Discrete-Event Simulation Pipeline for CMER Benchmarking.
Evaluates Dispatch Strategies and Ablations across Monte Carlo runs:
Strategies:
1. 1_NEAREST: Nearest Hospital (Baseline status quo)
2. 2_NEAREST_CAPABLE: Nearest Capable (Specialties only, ignores real-time beds/queues)
3. 3_NEAREST_CAPABLE_WITH_BED: Nearest Capable with Reported Free Bed (No hold; subject to arrival bed snipes & decay)
4. 4_CMER: Capability-Matched Emergency Referral (CMER: ETT optimization with Skellam P_ok + Pre-alert Bed Hold)

Ablation Strategies:
5. ABL_CAPABLE_HOLD: Nearest Capable + Pre-alert Bed Hold (Tests if capability + hold alone explains the gain)
6. ABL_CAPABLE_BED_HOLD: Nearest Capable with Reported Free Bed + Pre-alert Bed Hold (Tests simple bed filter + hold)
7. ABL_CMER_NO_HOLD: CMER (ETT optimization with Skellam P_ok) WITHOUT Pre-alert Bed Hold (Tests ranking alone without hold)

Realistic Flaw Injections:
- Truly old reports: Refresh with probability `reporting_rate`. If refreshed: age in [0, 15] min. If stale: age in [45, 120] min.
  State at t0 is snapshotted, then physical truth advances by `age` before ambulance dispatch.
- ER queue load passes through the same stale snapshot.
- Realistic hold refusals: Hospital responds ~85% of time and sometimes refuses hold. If rejected, fallback iterates to next ranked candidate.
- Paired comparisons: Identical cases/seeds across all strategies, paired differences vs Strategy 3, and bootstrap 95% CI.
"""

import os
import math
import random
import copy
from typing import Dict, List, Any, Tuple
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.seed.city import get_seed_hospitals
from app.engine.capability import is_hospital_capable, get_target_ward, get_effective_ward
from app.engine.probability import compute_p_ok
from app.engine.ranking import estimate_travel_time_minutes, rank_hospitals


CATEGORIES_PROB = [
    ("TRAUMA", 0.30),
    ("CARDIAC", 0.20),
    ("STROKE", 0.15),
    ("OBSTETRIC", 0.15),
    ("BURNS", 0.05),
    ("PAEDIATRIC", 0.05),
    ("GENERAL_ER", 0.10),
]


def pick_random_category() -> str:
    r = random.random()
    cum = 0.0
    for cat, prob in CATEGORIES_PROB:
        cum += prob
        if r <= cum:
            return cat
    return "TRAUMA"


class GroundTruthHospital:
    """
    Simulates true underlying clinical occupancy and ER state independently
    from central reports to avoid circular evaluation.
    """
    def __init__(self, seed_data: Dict[str, Any], occupancy_target: float = 0.88):
        self.id = seed_data["id"]
        self.name = seed_data["name"]
        self.tier = seed_data["tier"]
        self.lat = seed_data["lat"]
        self.lng = seed_data["lng"]
        self.capabilities = list(seed_data.get("capabilities", []))
        self.specialists = copy.deepcopy(seed_data.get("specialists", {}))
        self.equipment = copy.deepcopy(seed_data.get("equipment", {}))
        self.rates = copy.deepcopy(seed_data.get("rates", {}))
        self.reliability = seed_data.get("reliability", 0.85)

        self.wards_capacity: Dict[str, int] = {}
        self.wards_occupied: Dict[str, int] = {}
        self.wards_held: Dict[str, int] = {}

        for ward, data in seed_data.get("wards", {}).items():
            total = data.get("total", 10)
            self.wards_capacity[ward] = total
            occ = int(round(total * min(0.98, max(0.40, occupancy_target + random.uniform(-0.06, 0.06)))))
            self.wards_occupied[ward] = min(total, max(0, occ))
            self.wards_held[ward] = 0

        self.er_queue: int = max(0, int(round(seed_data.get("er_load", {}).get("waiting_count", 5) * (occupancy_target / 0.75))))
        
        # Snapshotted reports visible to dispatchers/CMER
        self.reported_wards: Dict[str, Dict[str, Any]] = {}
        self.reported_er_queue: int = self.er_queue
        self.report_age_min: float = 0.0

    def take_snapshot(self, report_age_min: float = 0.0, misreport_prob: float = 0.06):
        """
        Takes a snapshot of current capacity at t0.
        Reported ER load and ward beds freeze at this point with age `report_age_min`.
        """
        self.report_age_min = round(report_age_min, 1)
        self.reported_er_queue = self.er_queue
        self.reported_wards = {}

        for ward, total in self.wards_capacity.items():
            true_occ = self.wards_occupied[ward] + self.wards_held[ward]
            free = max(0, total - true_occ)
            if random.random() < misreport_prob:
                free = max(0, min(total, free + random.choice([-2, 2])))
            self.reported_wards[ward] = {
                "total": total,
                "free": free,
                "age_min": self.report_age_min
            }

    def simulate_background_dynamics(self, dt_minutes: float):
        """
        Background admissions/discharges advancing physical truth over dt_minutes.
        """
        if dt_minutes <= 0.0:
            return

        for ward, total in self.wards_capacity.items():
            # Burst walk-in admissions
            burst = np.random.poisson(lam=max(0.04, 0.16 * (dt_minutes / 12.0)))
            if random.random() < 0.25:
                burst += random.randint(1, 2)
            # Log-normal/binomial discharge proxy
            discharges = np.random.binomial(n=max(0, self.wards_occupied[ward]), p=min(0.25, 0.035 * (dt_minutes / 12.0)))

            available_for_walkin = max(0, total - self.wards_held[ward])
            self.wards_occupied[ward] = min(available_for_walkin, max(0, self.wards_occupied[ward] + burst - discharges))

        delta = random.choice([-1, 0, 1])
        self.er_queue = max(0, self.er_queue + delta)

    def get_reported_dict(self) -> Dict[str, Any]:
        """Returns the frozen snapshot visible to dispatchers and CMER."""
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "lat": self.lat,
            "lng": self.lng,
            "capabilities": self.capabilities,
            "specialists": self.specialists,
            "equipment": self.equipment,
            "wards": copy.deepcopy(self.reported_wards),
            "reliability": self.reliability,
            "er_load": {
                "waiting_count": self.reported_er_queue,
                "est_delay_min": round(self.reported_er_queue * 2.2, 1)
            },
            "rates": self.rates,
        }

    def has_true_free_bed(self, ward: str) -> bool:
        capacity = self.wards_capacity.get(ward, 0)
        occupied = self.wards_occupied.get(ward, 0)
        return (capacity - occupied) > 0

    def hold_bed(self, ward: str) -> bool:
        """Pre-alert confirmation: holds a bed from walk-in admissions until arrival."""
        capacity = self.wards_capacity.get(ward, 0)
        occupied = self.wards_occupied.get(ward, 0)
        held = self.wards_held.get(ward, 0)
        if (capacity - occupied - held) > 0:
            self.wards_held[ward] += 1
            return True
        return False

    def admit_patient(self, ward: str, was_held: bool) -> bool:
        if was_held:
            if self.wards_held.get(ward, 0) > 0:
                self.wards_held[ward] -= 1
            self.wards_occupied[ward] += 1
            return True
        else:
            if self.has_true_free_bed(ward):
                self.wards_occupied[ward] += 1
                return True
            return False


def setup_hospitals_with_realistic_staleness(
    seed_data: List[Dict[str, Any]],
    occupancy_target: float = 0.88,
    reporting_rate: float = 0.75,
    misreport_prob: float = 0.06,
) -> List[GroundTruthHospital]:
    """
    Initializes hospitals, takes snapshot at t0, then advances physical state by report age.
    If refreshed (prob=reporting_rate): age in [0, 15] min.
    If stale: age in [45, 120] min.
    Truth moves on; report stays frozen and old.
    """
    hospitals = []
    for s in seed_data:
        h = GroundTruthHospital(s, occupancy_target=occupancy_target)
        refreshed = (random.random() < reporting_rate)
        age = random.uniform(0.0, 15.0) if refreshed else random.uniform(45.0, 120.0)

        # Snapshot at t0
        h.take_snapshot(report_age_min=age, misreport_prob=misreport_prob)
        # Advance truth by age minutes so the physical state diverges from stale report
        h.simulate_background_dynamics(age)
        hospitals.append(h)
    return hospitals


def attempt_prealert_hold(
    h_reported: Dict[str, Any],
    h_ground_truth: GroundTruthHospital,
    category: str,
    acceptance_prob: float = 0.85
) -> bool:
    """
    Realistic Pre-alert protocol:
    1. Dispatcher/Ambulance ONLY sees h_reported (does not know ground truth).
       They only request a pre-alert hold if the hospital reports capability and reported free beds > 0.
    2. Hospital receives request over call/system.
    3. If hospital responds (acceptance_prob ~ 0.85), hospital checks its TRUE bed availability.
       If true bed exists, hospital accepts and reserves it. If no true bed exists or staff refuses, hold fails.
    This eliminates oracle leakage where dispatcher 'tested' arbitrary hospitals with hidden truth.
    """
    eff_w = get_effective_ward(h_reported, category)
    reported_free = h_reported.get("wards", {}).get(eff_w, {}).get("free", 0)
    # If the hospital's public report shows zero beds, dispatchers wouldn't request a normal pre-alert hold
    if reported_free <= 0:
        return False

    if random.random() < acceptance_prob:
        return h_ground_truth.hold_bed(eff_w)
    return False


def run_single_incident(
    hospitals: List[GroundTruthHospital],
    case_lat: float,
    case_lng: float,
    category: str,
    strategy: str,
    traffic_factor: float = 1.4,
) -> Dict[str, Any]:
    # Strictly isolated views:
    # `reported_hospitals` is the ONLY data dispatchers, EMTs, and algorithms see.
    reported_hospitals = [h.get_reported_dict() for h in hospitals]
    h_by_id = {h.id: h for h in hospitals}
    target_ward = get_target_ward(category)

    chosen = None
    held_bed = False
    predicted_p_ok = 0.50

    if strategy == "1_NEAREST":
        ranked = sorted(
            reported_hospitals,
            key=lambda h: estimate_travel_time_minutes(case_lat, case_lng, h["lat"], h["lng"], road_factor=traffic_factor)
        )
        chosen = ranked[0]
        # Evaluate what baseline actually predicted/expected
        t_time = estimate_travel_time_minutes(case_lat, case_lng, chosen["lat"], chosen["lng"], road_factor=traffic_factor)
        p_eval, _, _ = compute_p_ok(chosen, target_ward, t_time, category)
        predicted_p_ok = p_eval if is_hospital_capable(chosen, category) else 0.05
        held_bed = False

    elif strategy == "2_NEAREST_CAPABLE":
        capable = [h for h in reported_hospitals if is_hospital_capable(h, category)] or reported_hospitals
        ranked = sorted(
            capable,
            key=lambda h: estimate_travel_time_minutes(case_lat, case_lng, h["lat"], h["lng"], road_factor=traffic_factor)
        )
        chosen = ranked[0]
        t_time = estimate_travel_time_minutes(case_lat, case_lng, chosen["lat"], chosen["lng"], road_factor=traffic_factor)
        p_eval, _, _ = compute_p_ok(chosen, target_ward, t_time, category)
        predicted_p_ok = p_eval
        held_bed = False

    elif strategy == "3_NEAREST_CAPABLE_WITH_BED":
        candidates = []
        for h in reported_hospitals:
            if is_hospital_capable(h, category):
                eff_w = get_effective_ward(h, category)
                free_beds = h.get("wards", {}).get(eff_w, {}).get("free", 0)
                if free_beds > 0:
                    candidates.append(h)
        if not candidates:
            candidates = [h for h in reported_hospitals if is_hospital_capable(h, category)] or reported_hospitals
        ranked = sorted(
            candidates,
            key=lambda h: estimate_travel_time_minutes(case_lat, case_lng, h["lat"], h["lng"], road_factor=traffic_factor)
        )
        chosen = ranked[0]
        t_time = estimate_travel_time_minutes(case_lat, case_lng, chosen["lat"], chosen["lng"], road_factor=traffic_factor)
        p_eval, _, _ = compute_p_ok(chosen, target_ward, t_time, category)
        predicted_p_ok = p_eval
        held_bed = False

    elif strategy == "4_CMER":
        cmer_ranked, _ = rank_hospitals(
            reported_hospitals,
            case_lat,
            case_lng,
            category,
            reroute_overhead_min=18.0
        )
        chosen = cmer_ranked[0]["raw_hospital"] if cmer_ranked else reported_hospitals[0]
        predicted_p_ok = cmer_ranked[0]["p_ok"] if cmer_ranked else 0.70
        held_bed = False

        # Pre-alert hold workflow: only requests for top candidate first
        # If refused/unreachable, attempts backup candidate up to top 2 to reflect real call-taking time
        for cand in cmer_ranked[:2]:
            h_rep = cand["raw_hospital"]
            cand_h = h_by_id[h_rep["id"]]
            if attempt_prealert_hold(h_rep, cand_h, category, acceptance_prob=0.85):
                chosen = h_rep
                held_bed = True
                predicted_p_ok = cand["p_ok"]
                break
        else:
            # Pre-alert rejected or unconfirmed: ambulance dispatches to #1 CMER recommendation unheld
            chosen = cmer_ranked[0]["raw_hospital"] if cmer_ranked else reported_hospitals[0]
            held_bed = False
            predicted_p_ok = cmer_ranked[0]["p_ok"] if cmer_ranked else 0.70

    # --- ABLATION STRATEGIES ---
    elif strategy == "ABL_CAPABLE_HOLD":
        # Nearest capable with pre-alert hold attempt
        capable = [h for h in reported_hospitals if is_hospital_capable(h, category)] or reported_hospitals
        ranked = sorted(
            capable,
            key=lambda h: estimate_travel_time_minutes(case_lat, case_lng, h["lat"], h["lng"], road_factor=traffic_factor)
        )
        chosen = ranked[0]
        held_bed = False
        for cand in ranked[:2]:
            cand_h = h_by_id[cand["id"]]
            if attempt_prealert_hold(cand, cand_h, category, acceptance_prob=0.85):
                chosen = cand
                held_bed = True
                break
        else:
            chosen = ranked[0]
            held_bed = False
        t_time = estimate_travel_time_minutes(case_lat, case_lng, chosen["lat"], chosen["lng"], road_factor=traffic_factor)
        p_eval, _, _ = compute_p_ok(chosen, target_ward, t_time, category)
        predicted_p_ok = p_eval

    elif strategy == "ABL_CAPABLE_BED_HOLD":
        # Nearest capable with reported free bed + pre-alert hold attempt
        candidates = []
        for h in reported_hospitals:
            if is_hospital_capable(h, category):
                eff_w = get_effective_ward(h, category)
                if h.get("wards", {}).get(eff_w, {}).get("free", 0) > 0:
                    candidates.append(h)
        if not candidates:
            candidates = [h for h in reported_hospitals if is_hospital_capable(h, category)] or reported_hospitals
        ranked = sorted(
            candidates,
            key=lambda h: estimate_travel_time_minutes(case_lat, case_lng, h["lat"], h["lng"], road_factor=traffic_factor)
        )
        chosen = ranked[0]
        held_bed = False
        for cand in ranked[:2]:
            cand_h = h_by_id[cand["id"]]
            if attempt_prealert_hold(cand, cand_h, category, acceptance_prob=0.85):
                chosen = cand
                held_bed = True
                break
        else:
            chosen = ranked[0]
            held_bed = False
        t_time = estimate_travel_time_minutes(case_lat, case_lng, chosen["lat"], chosen["lng"], road_factor=traffic_factor)
        p_eval, _, _ = compute_p_ok(chosen, target_ward, t_time, category)
        predicted_p_ok = p_eval

    elif strategy == "ABL_CMER_NO_HOLD":
        # CMER ranking alone (P_ok + ETT) WITHOUT pre-alert bed hold
        cmer_ranked, _ = rank_hospitals(
            reported_hospitals,
            case_lat,
            case_lng,
            category,
            reroute_overhead_min=18.0
        )
        chosen = cmer_ranked[0]["raw_hospital"] if cmer_ranked else reported_hospitals[0]
        predicted_p_ok = cmer_ranked[0]["p_ok"] if cmer_ranked else 0.70
        held_bed = False

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    dest = h_by_id[chosen["id"]]
    dest_eff_ward = get_effective_ward(chosen, category)
    travel_time = estimate_travel_time_minutes(case_lat, case_lng, dest.lat, dest.lng, road_factor=traffic_factor)

    # Let background admissions/discharges run during transit (physical truth evolves)
    dest.simulate_background_dynamics(dt_minutes=travel_time)

    # Reality check upon arrival at destination:
    # Notice: True capability check against dest's actual clinical profile, not reported!
    dest_true_dict = {
        "capabilities": dest.capabilities,
        "specialists": dest.specialists,
        "equipment": dest.equipment,
    }
    is_capable = is_hospital_capable(dest_true_dict, category)
    can_admit = is_capable and dest.admit_patient(dest_eff_ward, was_held=held_bed)

    if can_admit:
        total_time = travel_time + (dest.er_queue * 2.0)
        return {
            "success_first_time": True,
            "time_to_treatment": round(total_time, 1),
            "secondary_referrals": 0,
            "incapable_refusal": False,
            "bed_refusal": False,
            "predicted_p_ok": round(float(predicted_p_ok), 3),
            "actual_outcome": 1.0,
            "held_bed": held_bed,
        }
    else:
        incapable_refusal = not is_capable
        bed_refusal = is_capable and not can_admit

        # Diverted: ambulance crew seeks backup facility based on REPORTED information (no oracle leakage)
        backup_candidates = [
            h for h in reported_hospitals
            if is_hospital_capable(h, category) and h["id"] != dest.id
        ]
        if not backup_candidates:
            backup_candidates = [h for h in reported_hospitals if h["id"] != dest.id]

        backup_rep = min(
            backup_candidates,
            key=lambda h: estimate_travel_time_minutes(dest.lat, dest.lng, h["lat"], h["lng"], road_factor=traffic_factor)
        )
        backup_h = h_by_id[backup_rep["id"]]
        transfer_travel = estimate_travel_time_minutes(dest.lat, dest.lng, backup_h.lat, backup_h.lng, road_factor=traffic_factor)

        # Inter-facility handover & secondary transport overhead
        transfer_overhead = random.uniform(22.0, 35.0)
        backup_h.simulate_background_dynamics(dt_minutes=(travel_time + transfer_overhead + transfer_travel))

        backup_eff_w = get_effective_ward(backup_rep, category)
        backup_admitted = backup_h.admit_patient(backup_eff_w, was_held=False)

        total_time = travel_time + transfer_overhead + transfer_travel + (backup_h.er_queue * 2.0)
        secondary_count = 1
        # If backup was also full, additional transfer delay added
        if not backup_admitted:
            total_time += random.uniform(20.0, 30.0)
            secondary_count = 2

        return {
            "success_first_time": False,
            "time_to_treatment": round(total_time, 1),
            "secondary_referrals": secondary_count,
            "incapable_refusal": incapable_refusal,
            "bed_refusal": bed_refusal,
            "predicted_p_ok": round(float(predicted_p_ok), 3),
            "actual_outcome": 0.0,
            "held_bed": held_bed,
        }


def bootstrap_paired_difference(
    diffs: List[float],
    n_boot: int = 2000,
    ci_level: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Computes bootstrap mean and percentile confidence interval for paired differences.
    Returns: (mean_diff, ci_lower, ci_upper)
    """
    arr = np.array(diffs)
    n = len(arr)
    mean_obs = float(np.mean(arr))
    boot_means = []
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(sample))
    alpha = (1.0 - ci_level) / 2.0
    ci_lower = float(np.percentile(boot_means, 100.0 * alpha))
    ci_upper = float(np.percentile(boot_means, 100.0 * (1.0 - alpha)))
    return round(mean_obs, 2), round(ci_lower, 2), round(ci_upper, 2)


def run_full_simulation(
    num_runs: int = 250,
    occupancy_target: float = 0.88,
    reporting_rate: float = 0.70,
    traffic_factor: float = 1.4,
    misreport_prob: float = 0.06,
    seed: int = 42,
    output_dir: str = None,
) -> Dict[str, Any]:
    """
    Runs discrete-event simulation with:
    - Fixed random seed for repeatability
    - Realistic staleness: advance physical truth by report age before dispatch
    - Pre-alert hold refusals (~85% response)
    - Full 4-strategy evaluation + 3 Ablations
    - Paired comparisons and bootstrap 95% CI vs Strategy 3
    """
    random.seed(seed)
    np.random.seed(seed)

    seed_data = get_seed_hospitals()
    all_strategies = [
        "1_NEAREST",
        "2_NEAREST_CAPABLE",
        "3_NEAREST_CAPABLE_WITH_BED",
        "4_CMER",
        "ABL_CAPABLE_HOLD",
        "ABL_CAPABLE_BED_HOLD",
        "ABL_CMER_NO_HOLD",
    ]

    strategy_labels = {
        "1_NEAREST": "1. Nearest Hospital (Baseline)",
        "2_NEAREST_CAPABLE": "2. Nearest Capable (Specialties Only)",
        "3_NEAREST_CAPABLE_WITH_BED": "3. Nearest Capable + Free Bed",
        "4_CMER": "4. CMER (Capability + ETT + Bed Hold)",
        "ABL_CAPABLE_HOLD": "Ablation: Capable + Hold",
        "ABL_CAPABLE_BED_HOLD": "Ablation: Capable + Bed + Hold",
        "ABL_CMER_NO_HOLD": "Ablation: CMER (Ranking Only, No Hold)",
    }

    results = {
        strat: {
            "label": strategy_labels[strat],
            "successes": 0,
            "times": [],
            "secondaries": 0,
            "incapable": 0,
            "bed_refusals": 0,
            "predictions": [],
            "outcomes": [],
            "held_count": 0,
        }
        for strat in all_strategies
    }

    LAT_MIN, LAT_MAX = 12.880, 13.060
    LNG_MIN, LNG_MAX = 77.500, 77.720

    for _ in range(num_runs):
        case_lat = random.uniform(LAT_MIN, LAT_MAX)
        case_lng = random.uniform(LNG_MIN, LNG_MAX)
        cat = pick_random_category()

        # Generate hospitals with real staleness: snapshot at t0, physical truth advances by age
        base_hospitals = setup_hospitals_with_realistic_staleness(
            seed_data,
            occupancy_target=occupancy_target,
            reporting_rate=reporting_rate,
            misreport_prob=misreport_prob,
        )

        for strat in all_strategies:
            cloned = copy.deepcopy(base_hospitals)
            outcome = run_single_incident(cloned, case_lat, case_lng, cat, strat, traffic_factor=traffic_factor)

            r = results[strat]
            if outcome["success_first_time"]:
                r["successes"] += 1
            r["times"].append(outcome["time_to_treatment"])
            r["secondaries"] += outcome["secondary_referrals"]
            if outcome["incapable_refusal"]:
                r["incapable"] += 1
            if outcome["bed_refusal"]:
                r["bed_refusals"] += 1
            if outcome["held_bed"]:
                r["held_count"] += 1
            r["predictions"].append(outcome["predicted_p_ok"])
            r["outcomes"].append(outcome["actual_outcome"])

    # Paired comparisons against Strategy 3
    s3_times = np.array(results["3_NEAREST_CAPABLE_WITH_BED"]["times"])
    s3_successes = np.array([1.0 if o == 1.0 else 0.0 for o in results["3_NEAREST_CAPABLE_WITH_BED"]["outcomes"]])

    summary = []
    for strat in all_strategies:
        data = results[strat]
        times = np.array(data["times"])
        mean_t = float(np.mean(times))
        sem_t = float(np.std(times) / math.sqrt(num_runs))
        success_pct = round((data["successes"] / num_runs) * 100.0, 1)

        # Paired delta metrics vs Strategy 3
        paired_time_diffs = list(times - s3_times)  # negative means faster than S3
        paired_succ_diffs = list(np.array(data["outcomes"]) - s3_successes)  # positive means higher success than S3

        time_mean_diff, time_ci_low, time_ci_high = bootstrap_paired_difference(paired_time_diffs)
        succ_mean_diff, succ_ci_low, succ_ci_high = bootstrap_paired_difference([d * 100.0 for d in paired_succ_diffs])

        summary.append({
            "strategy_key": strat,
            "strategy_name": data["label"],
            "first_time_success_rate_pct": success_pct,
            "mean_time_to_treatment_min": round(mean_t, 1),
            "sem_time_to_treatment_min": round(sem_t, 1),
            "secondary_transfers_per_100": round((data["secondaries"] / num_runs) * 100.0, 1),
            "incapable_refusals_pct": round((data["incapable"] / num_runs) * 100.0, 1),
            "bed_refusals_pct": round((data["bed_refusals"] / num_runs) * 100.0, 1),
            "bed_holds_secured_pct": round((data["held_count"] / num_runs) * 100.0, 1),
            "paired_vs_strategy_3": {
                "time_diff_mean_min": time_mean_diff,
                "time_diff_95ci_min": [time_ci_low, time_ci_high],
                "success_diff_mean_pct": succ_mean_diff,
                "success_diff_95ci_pct": [succ_ci_low, succ_ci_high],
            }
        })

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        _plot_strategy_and_ablations(summary, output_dir)
        _plot_calibration_curve(results["4_CMER"]["predictions"], results["4_CMER"]["outcomes"], output_dir)
        _plot_reporting_sweep(output_dir, traffic_factor=traffic_factor, occupancy_target=occupancy_target)

    return {
        "num_runs": num_runs,
        "seed": seed,
        "parameters": {
            "occupancy_target_pct": int(occupancy_target * 100),
            "reporting_rate_pct": int(reporting_rate * 100),
            "traffic_factor": traffic_factor,
            "misreport_prob_pct": int(misreport_prob * 100),
        },
        "summary": summary
    }


def _plot_strategy_and_ablations(summary: List[Dict[str, Any]], output_dir: str):
    core_keys = ["1_NEAREST", "2_NEAREST_CAPABLE", "3_NEAREST_CAPABLE_WITH_BED", "4_CMER"]
    abl_keys = ["ABL_CAPABLE_HOLD", "ABL_CAPABLE_BED_HOLD", "ABL_CMER_NO_HOLD"]

    core_items = [s for s in summary if s["strategy_key"] in core_keys]
    abl_items = [s for s in summary if s["strategy_key"] in abl_keys]

    labels = ["Nearest\nBaseline", "Nearest\nCapable", "Capable\n+ Bed", "CMER\n(Full)"]
    successes = [s["first_time_success_rate_pct"] for s in core_items]
    times = [s["mean_time_to_treatment_min"] for s in core_items]
    sems = [s["sem_time_to_treatment_min"] for s in core_items]
    colors = ["#ef4444", "#f59e0b", "#38bdf8", "#10b981"]

    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("#0b0f19")
    ax1.set_facecolor("#0f172a")
    ax2.set_facecolor("#0f172a")

    bars1 = ax1.bar(labels, successes, color=colors, edgecolor="#334155", width=0.55)
    ax1.set_title("First-Time Definitive Delivery Rate (%)", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
    ax1.set_ylim(0, 105)
    ax1.set_ylabel("First-Time Delivery (%)", color="#94a3b8")
    ax1.grid(axis="y", linestyle="--", alpha=0.25, color="#64748b")
    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., h + 2, f"{h:.1f}%", ha="center", va="bottom", color="#f8fafc", fontweight="bold")

    bars2 = ax2.bar(labels, times, yerr=sems, capsize=5, color=colors, edgecolor="#334155", width=0.55)
    ax2.set_title("Mean Time to Definitive Treatment (Minutes)", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
    ax2.set_ylabel("Treatment Latency (min)", color="#94a3b8")
    ax2.grid(axis="y", linestyle="--", alpha=0.25, color="#64748b")
    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., h + 1.5, f"{h:.1f}m", ha="center", va="bottom", color="#f8fafc", fontweight="bold")

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "sim_results_strategies.png")
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()


def _plot_calibration_curve(predictions: List[float], outcomes: List[float], output_dir: str):
    bins = np.linspace(0.4, 1.0, 7)
    bin_centers = (bins[:-1] + bins[1:]) / 2.0
    bin_empirical = []
    bin_predicted = []

    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i+1]
        indices = [k for k, p in enumerate(predictions) if low <= p < high]
        if indices:
            bin_predicted.append(float(np.mean([predictions[k] for k in indices])))
            bin_empirical.append(float(np.mean([outcomes[k] for k in indices])))
        else:
            bin_predicted.append(bin_centers[i])
            bin_empirical.append(bin_centers[i])

    brier = float(np.mean([(p - o) ** 2 for p, o in zip(predictions, outcomes)]))

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0f172a")

    ax.plot([0.4, 1.0], [0.4, 1.0], "r--", label="Perfect Calibration (Ideal)", alpha=0.8)
    ax.plot(bin_predicted, bin_empirical, marker="o", linewidth=2.2, color="#38bdf8", label=f"CMER P_ok (Brier = {brier:.3f})")
    ax.fill_between(bin_predicted, bin_predicted, bin_empirical, color="#38bdf8", alpha=0.15)

    ax.set_title("Reliability Diagram (P_ok Calibration)", color="#f8fafc", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Predicted Probability P_ok", color="#94a3b8")
    ax.set_ylabel("Observed Bed Availability Rate", color="#94a3b8")
    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.4, 1.0)
    ax.grid(linestyle="--", alpha=0.25, color="#64748b")
    ax.legend(facecolor="#1e293b", edgecolor="#475569", labelcolor="#f8fafc")

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "sim_calibration_diagram.png")
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()


def _plot_reporting_sweep(
    output_dir: str,
    traffic_factor: float = 1.4,
    occupancy_target: float = 0.88,
):
    """
    Simulates real degradation sweep (100% to 15%) using the same realistic staleness
    and hold refusal model across all tested points.
    """
    sweep_rates = [1.0, 0.8, 0.6, 0.4, 0.3, 0.15]
    seed_data = get_seed_hospitals()
    LAT_MIN, LAT_MAX = 12.880, 13.060
    LNG_MIN, LNG_MAX = 77.500, 77.720

    cmer_rates = []
    baseline_rates = []
    strat3_rates = []
    display_percentages = [int(r * 100) for r in sweep_rates]

    for r in sweep_rates:
        cmer_succ = 0
        base_succ = 0
        s3_succ = 0
        n_eval = 70
        for _ in range(n_eval):
            case_lat = random.uniform(LAT_MIN, LAT_MAX)
            case_lng = random.uniform(LNG_MIN, LNG_MAX)
            cat = pick_random_category()

            base_h = setup_hospitals_with_realistic_staleness(
                seed_data,
                occupancy_target=occupancy_target,
                reporting_rate=r,
                misreport_prob=0.06,
            )

            o_base = run_single_incident(copy.deepcopy(base_h), case_lat, case_lng, cat, "1_NEAREST", traffic_factor=traffic_factor)
            o_s3 = run_single_incident(copy.deepcopy(base_h), case_lat, case_lng, cat, "3_NEAREST_CAPABLE_WITH_BED", traffic_factor=traffic_factor)
            o_cmer = run_single_incident(copy.deepcopy(base_h), case_lat, case_lng, cat, "4_CMER", traffic_factor=traffic_factor)

            if o_base["success_first_time"]:
                base_succ += 1
            if o_s3["success_first_time"]:
                s3_succ += 1
            if o_cmer["success_first_time"]:
                cmer_succ += 1

        baseline_rates.append(round((base_succ / n_eval) * 100.0, 1))
        strat3_rates.append(round((s3_succ / n_eval) * 100.0, 1))
        cmer_rates.append(round((cmer_succ / n_eval) * 100.0, 1))

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0f172a")

    ax.plot(display_percentages, cmer_rates, marker="s", linewidth=2.5, color="#10b981", label="CMER (Dynamic ETT + Hold with Refusals)")
    ax.plot(display_percentages, strat3_rates, marker="o", linewidth=2.0, color="#38bdf8", label="3. Capable + Free Bed (No Hold)")
    ax.plot(display_percentages, baseline_rates, marker="x", linewidth=2.0, linestyle="--", color="#ef4444", label="1. Nearest Baseline")

    ax.set_title("Degradation Sweep: Real-Time Reporting Latency & Staleness", color="#f8fafc", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Hospital Timely Reporting Rate (%)", color="#94a3b8")
    ax.set_ylabel("First-Time Delivery Rate (%)", color="#94a3b8")
    ax.set_xlim(105, 10)
    ax.set_ylim(15, 105)
    ax.grid(linestyle="--", alpha=0.25, color="#64748b")
    ax.legend(facecolor="#1e293b", edgecolor="#475569", labelcolor="#f8fafc")

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "sim_reporting_sweep.png")
    plt.savefig(chart_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close()


if __name__ == "__main__":
    # Save both to local docs/assets for project documentation and to current brain artifact directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    docs_asset_dir = os.path.join(base_dir, "..", "docs", "assets")
    os.makedirs(docs_asset_dir, exist_ok=True)

    print(f"Running 250-run Monte Carlo Simulation with realistic staleness and ablations to {docs_asset_dir}...")
    res = run_full_simulation(num_runs=250, seed=42, output_dir=docs_asset_dir)
    print("\n--- SIMULATION RESULTS (250 RUNS, SEED=42) ---")
    for s in res["summary"]:
        diff_info = s["paired_vs_strategy_3"]
        print(f"{s['strategy_name']:42s} | Success={s['first_time_success_rate_pct']:5.1f}% | Time={s['mean_time_to_treatment_min']:4.1f}m +/- {s['sem_time_to_treatment_min']:3.1f}m | vs S3 dTime={diff_info['time_diff_mean_min']:+4.2f}m (95% CI {diff_info['time_diff_95ci_min']})")


