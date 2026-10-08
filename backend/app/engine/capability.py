"""
Capability Mapping Engine for CMER.
Maps emergency categories to mandatory clinical capabilities and primary target ward.
"""

from typing import List, Dict, Any

CATEGORY_CAPABILITY_MAP: Dict[str, Dict[str, Any]] = {
    "TRAUMA": {
        "label": "Severe Trauma / Head Injury",
        "required_capabilities": ["TRAUMA", "NEURO", "ICU", "CT"],
        "target_ward": "ICU",
        "description": "Requires neurosurgeon, trauma OT, CT scanner, and ICU bed.",
    },
    "CARDIAC": {
        "label": "Cardiac / Acute Coronary Syndrome",
        "required_capabilities": ["CARDIAC", "CATH_LAB", "ICU"],
        "target_ward": "ICU",
        "description": "Requires 24x7 Cath Lab and CCU/ICU ventilator support.",
    },
    "STROKE": {
        "label": "Acute Stroke / Neuro Emergency",
        "required_capabilities": ["NEURO", "CT", "ICU"],
        "target_ward": "ICU",
        "description": "Requires urgent CT evaluation, stroke unit, and neuro critical care.",
    },
    "OBSTETRIC": {
        "label": "High-Risk Obstetric / Delivery",
        "required_capabilities": ["OBSTETRIC", "BLOOD"],
        "target_ward": "OBS",
        "fallback_ward": "ER",
        "description": "Requires obstetrician, blood bank cross-matching, and delivery suite.",
    },
    "PAEDIATRIC": {
        "label": "Paediatric Emergency / Neonatal",
        "required_capabilities": ["PAEDS"],
        "target_ward": "ER",
        "description": "Requires paediatrician on duty and pediatric resuscitation.",
    },
    "BURNS": {
        "label": "Severe Burns (>20% or Inhalation)",
        "required_capabilities": ["BURNS", "ICU"],
        "target_ward": "BURNS",
        "fallback_ward": "ICU",
        "description": "Requires specialized burn ICU and sterile barrier care.",
    },
    "GENERAL": {
        "label": "General / Uncategorized Emergency",
        "required_capabilities": ["ER"],
        "target_ward": "ER",
        "description": "Standard emergency room resuscitation and stabilization.",
    },
}


def get_required_capabilities(category: str) -> List[str]:
    """Returns list of required capability codes for a given emergency category."""
    cat_key = category.upper()
    cat_info = CATEGORY_CAPABILITY_MAP.get(cat_key, CATEGORY_CAPABILITY_MAP["GENERAL"])
    return list(cat_info["required_capabilities"])


def get_target_ward(category: str) -> str:
    """Returns the primary hospital ward to evaluate bed availability for."""
    cat_key = category.upper()
    cat_info = CATEGORY_CAPABILITY_MAP.get(cat_key, CATEGORY_CAPABILITY_MAP["GENERAL"])
    return cat_info.get("target_ward", "ER")


def is_hospital_capable(hospital: Dict[str, Any], category: str) -> bool:
    """Checks if a hospital satisfies all required capabilities for the category."""
    required = set(get_required_capabilities(category))
    hosp_caps = set(hospital.get("capabilities", []))
    return required.issubset(hosp_caps)
