"""
Synthetic City Dataset: Bengaluru Metro Region (15 hospitals)
Tiers:
- small: 5 primary clinics / nursing homes (ER only or limited capabilities)
- mid: 6 community / district hospitals (general surgery, paediatrics, obstetrics, ER)
- tertiary: 4 major multispecialty / trauma centres (trauma, neuro, cardiac, cath lab, burns, icu, nicu, ct)

Each hospital includes ABDM HFR identifier, coordinates, ward bed status,
specialist availability, discharge/admission rates, and ER loads.
"""

from typing import Dict, List, Any

# Capability codes
CAPABILITIES = {
    "TRAUMA": "Trauma Care / Emergency Surgery",
    "NEURO": "Neurosurgery & Stroke Unit",
    "CARDIAC": "Cardiology / Cath Lab",
    "CATH_LAB": "Interventional Cath Lab",
    "OBSTETRIC": "Obstetrics & High-Risk Delivery",
    "NICU": "Neonatal Intensive Care Unit",
    "PAEDS": "Paediatrics Intensive / Ward",
    "BURNS": "Specialized Burns Unit",
    "ICU": "Intensive Care Unit (Ventilator Capable)",
    "CT": "24x7 Computed Tomography Scanner",
    "BLOOD": "24x7 Blood Bank with Cross-matching",
    "ER": "Standard Emergency Room",
}

# 15 Seed Hospitals centered around Bengaluru urban & peripheral emergency corridors
HOSPITALS_DATA: List[Dict[str, Any]] = [
    # --- TERTIARY HOSPITALS (4) ---
    {
        "id": "hosp-victoria",
        "hfr_id": "IN-KA-BLR-00109",
        "name": "Victoria Hospital & BMCRI Trauma Centre",
        "tier": "tertiary",
        "lat": 12.9634,
        "lng": 77.5756,
        "emergency_phone": "+91-80-26701150",
        "sms_number": "+919880110001",
        "reliability": 0.88,
        "capabilities": ["TRAUMA", "NEURO", "CARDIAC", "CATH_LAB", "BURNS", "ICU", "CT", "BLOOD", "ER", "PAEDS"],
        "wards": {
            "ICU": {"total": 35, "free": 4, "age_min": 12},
            "ER": {"total": 50, "free": 11, "age_min": 10},
            "BURNS": {"total": 20, "free": 3, "age_min": 25},
            "TRAUMA": {"total": 40, "free": 6, "age_min": 8},
        },
        "specialists": {
            "NEURO": {"on_duty": True, "name": "Dr. Ramesh (Neurosurgery)"},
            "TRAUMA": {"on_duty": True, "name": "Dr. Priya (Trauma Lead)"},
            "CARDIAC": {"on_duty": True, "name": "Dr. Sandeep (Cardio)"},
        },
        "equipment": {"CT": True, "CATH_LAB": True, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.12, "a": 0.15}, "ER": {"d": 0.40, "a": 0.45}},
        "er_load": {"waiting_count": 8, "est_delay_min": 12},
    },
    {
        "id": "hosp-nimhans",
        "hfr_id": "IN-KA-BLR-00215",
        "name": "NIMHANS Neuro & Trauma Emergency",
        "tier": "tertiary",
        "lat": 12.9392,
        "lng": 77.5959,
        "emergency_phone": "+91-80-26995000",
        "sms_number": "+919880110002",
        "reliability": 0.94,
        "capabilities": ["TRAUMA", "NEURO", "ICU", "CT", "BLOOD", "ER"],
        "wards": {
            "ICU": {"total": 30, "free": 2, "age_min": 6},
            "ER": {"total": 40, "free": 5, "age_min": 5},
            "NEURO_ICU": {"total": 25, "free": 3, "age_min": 10},
        },
        "specialists": {
            "NEURO": {"on_duty": True, "name": "Dr. Chandrashekar (Senior Neuro)"},
            "TRAUMA": {"on_duty": True, "name": "Dr. Ananya (Neuro-Trauma)"},
        },
        "equipment": {"CT": True, "CATH_LAB": False, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.08, "a": 0.11}, "ER": {"d": 0.35, "a": 0.38}},
        "er_load": {"waiting_count": 6, "est_delay_min": 10},
    },
    {
        "id": "hosp-jayadeva",
        "hfr_id": "IN-KA-BLR-00340",
        "name": "Sri Jayadeva Institute of Cardiovascular Sciences",
        "tier": "tertiary",
        "lat": 12.9239,
        "lng": 77.5996,
        "emergency_phone": "+91-80-22977400",
        "sms_number": "+919880110003",
        "reliability": 0.92,
        "capabilities": ["CARDIAC", "CATH_LAB", "ICU", "BLOOD", "ER"],
        "wards": {
            "ICU": {"total": 45, "free": 5, "age_min": 15},
            "ER": {"total": 35, "free": 8, "age_min": 12},
            "CCU": {"total": 30, "free": 4, "age_min": 10},
        },
        "specialists": {
            "CARDIAC": {"on_duty": True, "name": "Dr. Manjunath (Interventional)"},
        },
        "equipment": {"CT": True, "CATH_LAB": True, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.15, "a": 0.18}, "ER": {"d": 0.45, "a": 0.40}},
        "er_load": {"waiting_count": 5, "est_delay_min": 8},
    },
    {
        "id": "hosp-manipal-hal",
        "hfr_id": "IN-KA-BLR-00488",
        "name": "Manipal Hospital Old Airport Road",
        "tier": "tertiary",
        "lat": 12.9584,
        "lng": 77.6493,
        "emergency_phone": "+91-80-25024444",
        "sms_number": "+919880110004",
        "reliability": 0.85,
        "capabilities": ["TRAUMA", "NEURO", "CARDIAC", "CATH_LAB", "OBSTETRIC", "NICU", "PAEDS", "BURNS", "ICU", "CT", "BLOOD", "ER"],
        "wards": {
            "ICU": {"total": 40, "free": 1, "age_min": 42},  # Stale report (>30m) for testing verification flow!
            "ER": {"total": 30, "free": 4, "age_min": 35},
            "NICU": {"total": 15, "free": 2, "age_min": 40},
        },
        "specialists": {
            "NEURO": {"on_duty": True, "name": "Dr. Rajesh (On-Call)"},
            "CARDIAC": {"on_duty": True, "name": "Dr. Swathi (Cardio)"},
            "TRAUMA": {"on_duty": True, "name": "Dr. Kiran (Trauma)"},
        },
        "equipment": {"CT": True, "CATH_LAB": True, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.10, "a": 0.12}, "ER": {"d": 0.30, "a": 0.35}},
        "er_load": {"waiting_count": 7, "est_delay_min": 14},
    },

    # --- MID-TIER HOSPITALS (6) ---
    {
        "id": "hosp-bowring",
        "hfr_id": "IN-KA-BLR-00512",
        "name": "Bowring & Lady Curzon Hospital (Shivajinagar)",
        "tier": "mid",
        "lat": 12.9832,
        "lng": 77.6033,
        "emergency_phone": "+91-80-25591325",
        "sms_number": "+919880110005",
        "reliability": 0.78,
        "capabilities": ["OBSTETRIC", "PAEDS", "ICU", "BLOOD", "ER"],
        "wards": {
            "ICU": {"total": 18, "free": 3, "age_min": 14},
            "ER": {"total": 25, "free": 7, "age_min": 10},
            "OBS": {"total": 30, "free": 6, "age_min": 20},
        },
        "specialists": {
            "OBSTETRIC": {"on_duty": True, "name": "Dr. Geetha (OBGYN)"},
            "PAEDS": {"on_duty": True, "name": "Dr. Arvind (Paeds)"},
        },
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.07, "a": 0.08}, "ER": {"d": 0.25, "a": 0.30}},
        "er_load": {"waiting_count": 9, "est_delay_min": 18},
    },
    {
        "id": "hosp-kc-general",
        "hfr_id": "IN-KA-BLR-00620",
        "name": "KC General Hospital (Malleswaram)",
        "tier": "mid",
        "lat": 12.9982,
        "lng": 77.5714,
        "emergency_phone": "+91-80-23341771",
        "sms_number": "+919880110006",
        "reliability": 0.81,
        "capabilities": ["OBSTETRIC", "PAEDS", "ICU", "ER", "BLOOD"],
        "wards": {
            "ICU": {"total": 15, "free": 2, "age_min": 18},
            "ER": {"total": 28, "free": 6, "age_min": 15},
            "OBS": {"total": 25, "free": 4, "age_min": 12},
        },
        "specialists": {
            "OBSTETRIC": {"on_duty": True, "name": "Dr. Suma (OBGYN)"},
            "PAEDS": {"on_duty": False, "name": "Off-shift"},
        },
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.06, "a": 0.07}, "ER": {"d": 0.22, "a": 0.26}},
        "er_load": {"waiting_count": 6, "est_delay_min": 14},
    },
    {
        "id": "hosp-jayanagar-gen",
        "hfr_id": "IN-KA-BLR-00731",
        "name": "Jayanagar General Hospital",
        "tier": "mid",
        "lat": 12.9298,
        "lng": 77.5835,
        "emergency_phone": "+91-80-26630940",
        "sms_number": "+919880110007",
        "reliability": 0.76,  # Known slightly lower reliability for testing
        "capabilities": ["OBSTETRIC", "PAEDS", "ER", "BLOOD"],
        "wards": {
            "ER": {"total": 20, "free": 4, "age_min": 16},
            "OBS": {"total": 20, "free": 3, "age_min": 22},
        },
        "specialists": {
            "OBSTETRIC": {"on_duty": True, "name": "Dr. Vimala (OBGYN)"},
        },
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.20, "a": 0.22}},
        "er_load": {"waiting_count": 7, "est_delay_min": 15},
    },
    {
        "id": "hosp-chinmaya",
        "hfr_id": "IN-KA-BLR-00844",
        "name": "Chinmaya Mission Hospital (Indiranagar)",
        "tier": "mid",
        "lat": 12.9784,
        "lng": 77.6408,
        "emergency_phone": "+91-80-25280461",
        "sms_number": "+919880110008",
        "reliability": 0.86,
        "capabilities": ["OBSTETRIC", "PAEDS", "ICU", "ER", "CT"],
        "wards": {
            "ICU": {"total": 12, "free": 2, "age_min": 9},
            "ER": {"total": 18, "free": 5, "age_min": 8},
        },
        "specialists": {
            "OBSTETRIC": {"on_duty": True, "name": "Dr. Nalini (OBGYN)"},
            "PAEDS": {"on_duty": True, "name": "Dr. Pradeep (Pediatrics)"},
        },
        "equipment": {"CT": True, "CATH_LAB": False, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.05, "a": 0.06}, "ER": {"d": 0.18, "a": 0.20}},
        "er_load": {"waiting_count": 4, "est_delay_min": 10},
    },
    {
        "id": "hosp-st-marthas",
        "hfr_id": "IN-KA-BLR-00915",
        "name": "St. Martha's Hospital (Nrupathunga Rd)",
        "tier": "mid",
        "lat": 12.9723,
        "lng": 77.5878,
        "emergency_phone": "+91-80-22275081",
        "sms_number": "+919880110009",
        "reliability": 0.89,
        "capabilities": ["OBSTETRIC", "PAEDS", "ICU", "BLOOD", "ER", "CT"],
        "wards": {
            "ICU": {"total": 16, "free": 3, "age_min": 11},
            "ER": {"total": 22, "free": 6, "age_min": 10},
        },
        "specialists": {
            "OBSTETRIC": {"on_duty": True, "name": "Dr. Mary (OBGYN)"},
            "PAEDS": {"on_duty": True, "name": "Dr. Joseph (Paeds)"},
        },
        "equipment": {"CT": True, "CATH_LAB": False, "VENTILATORS": True},
        "rates": {"ICU": {"d": 0.06, "a": 0.07}, "ER": {"d": 0.20, "a": 0.22}},
        "er_load": {"waiting_count": 5, "est_delay_min": 11},
    },
    {
        "id": "hosp-yelahanka-gen",
        "hfr_id": "IN-KA-BLR-01022",
        "name": "Yelahanka General Hospital (North Corridor)",
        "tier": "mid",
        "lat": 13.1007,
        "lng": 77.5963,
        "emergency_phone": "+91-80-28562211",
        "sms_number": "+919880110010",
        "reliability": 0.80,
        "capabilities": ["OBSTETRIC", "PAEDS", "ER", "BLOOD"],
        "wards": {
            "ER": {"total": 16, "free": 5, "age_min": 14},
            "OBS": {"total": 18, "free": 4, "age_min": 15},
        },
        "specialists": {
            "OBSTETRIC": {"on_duty": True, "name": "Dr. Bhavana (OBGYN)"},
        },
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.15, "a": 0.18}},
        "er_load": {"waiting_count": 3, "est_delay_min": 8},
    },

    # --- SMALL CLINICS / NURSING HOMES (5) ---
    {
        "id": "hosp-shanthi-nursing",
        "hfr_id": "IN-KA-BLR-01105",
        "name": "Shanthi Nursing Home (Basavanagudi)",
        "tier": "small",
        "lat": 12.9419,
        "lng": 77.5742,
        "emergency_phone": "+91-80-26612010",
        "sms_number": "+919880110011",
        "reliability": 0.70,
        "capabilities": ["ER"],
        "wards": {
            "ER": {"total": 8, "free": 3, "age_min": 8},
        },
        "specialists": {},
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.10, "a": 0.12}},
        "er_load": {"waiting_count": 2, "est_delay_min": 5},
    },
    {
        "id": "hosp-koramangala-clinic",
        "hfr_id": "IN-KA-BLR-01211",
        "name": "Koramangala Emergency Clinic (5th Block)",
        "tier": "small",
        "lat": 12.9345,
        "lng": 77.6190,
        "emergency_phone": "+91-80-25531999",
        "sms_number": "+919880110012",
        "reliability": 0.82,
        "capabilities": ["ER"],
        "wards": {
            "ER": {"total": 6, "free": 2, "age_min": 5},
        },
        "specialists": {},
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.08, "a": 0.10}},
        "er_load": {"waiting_count": 1, "est_delay_min": 4},
    },
    {
        "id": "hosp-rajajinagar-er",
        "hfr_id": "IN-KA-BLR-01314",
        "name": "Rajajinagar First Care Centre",
        "tier": "small",
        "lat": 12.9915,
        "lng": 77.5529,
        "emergency_phone": "+91-80-23154400",
        "sms_number": "+919880110013",
        "reliability": 0.75,
        "capabilities": ["ER"],
        "wards": {
            "ER": {"total": 10, "free": 4, "age_min": 12},
        },
        "specialists": {},
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.10, "a": 0.11}},
        "er_load": {"waiting_count": 2, "est_delay_min": 6},
    },
    {
        "id": "hosp-domlur-community",
        "hfr_id": "IN-KA-BLR-01428",
        "name": "Domlur Community Health Clinic",
        "tier": "small",
        "lat": 12.9609,
        "lng": 77.6382,
        "emergency_phone": "+91-80-25356789",
        "sms_number": "+919880110014",
        "reliability": 0.72,
        "capabilities": ["ER"],
        "wards": {
            "ER": {"total": 6, "free": 1, "age_min": 15},
        },
        "specialists": {},
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.07, "a": 0.08}},
        "er_load": {"waiting_count": 2, "est_delay_min": 7},
    },
    {
        "id": "hosp-hebbal-traumette",
        "hfr_id": "IN-KA-BLR-01539",
        "name": "Hebbal Minor Injury Clinic (Outer Ring Rd)",
        "tier": "small",
        "lat": 13.0358,
        "lng": 77.5970,
        "emergency_phone": "+91-80-23631122",
        "sms_number": "+919880110015",
        "reliability": 0.77,
        "capabilities": ["ER"],
        "wards": {
            "ER": {"total": 8, "free": 3, "age_min": 20},
        },
        "specialists": {},
        "equipment": {"CT": False, "CATH_LAB": False, "VENTILATORS": False},
        "rates": {"ER": {"d": 0.09, "a": 0.10}},
        "er_load": {"waiting_count": 1, "est_delay_min": 5},
    },
]

def get_seed_hospitals() -> List[Dict[str, Any]]:
    """Returns a deep-copyable list of seed hospitals with fresh timestamps."""
    hospitals = []
    for h in HOSPITALS_DATA:
        h_copy = dict(h)
        # Deep copy wards with explicit updated_at
        wards_copy = {}
        for ward_name, ward_info in h["wards"].items():
            wards_copy[ward_name] = {
                "total": ward_info["total"],
                "free": ward_info["free"],
                "age_min": ward_info["age_min"],
                "held": 0,
            }
        h_copy["wards"] = wards_copy
        h_copy["specialists"] = dict(h["specialists"])
        h_copy["equipment"] = dict(h["equipment"])
        h_copy["rates"] = dict(h["rates"])
        h_copy["er_load"] = dict(h["er_load"])
        hospitals.append(h_copy)
    return hospitals
