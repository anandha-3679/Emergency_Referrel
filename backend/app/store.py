"""
In-Memory Datastore for CMER prototype with thread-safe locks.
Houses:
- Hospitals (initialized from seed/city.py with real HFR IDs)
- Cases
- Reservations
- Reliability audit logs
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import copy
import uuid

from app.seed.city import get_seed_hospitals


class InMemoryStore:
    def __init__(self):
        self._hospitals: Dict[str, Dict[str, Any]] = {}
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._reservations: Dict[str, Dict[str, Any]] = {}
        self._events: List[Dict[str, Any]] = []
        self.reset()

    def reset(self):
        """Resets the store and reloads seed hospitals."""
        self._hospitals.clear()
        self._cases.clear()
        self._reservations.clear()
        self._events.clear()

        seed_data = get_seed_hospitals()
        now = datetime.now(timezone.utc)
        for h in seed_data:
            h_copy = copy.deepcopy(h)
            h_copy["held_beds"] = 0
            h_copy["updated_at"] = now
            self._hospitals[h_copy["id"]] = h_copy

    # --- Hospital Accessors ---
    def list_hospitals(self) -> List[Dict[str, Any]]:
        return list(self._hospitals.values())

    def get_hospital(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        return self._hospitals.get(hospital_id)

    def update_hospital_status(self, hospital_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        h = self._hospitals.get(hospital_id)
        if not h:
            return None

        if "wards" in updates and updates["wards"] is not None:
            for ward_name, ward_data in updates["wards"].items():
                if ward_name in h["wards"]:
                    h["wards"][ward_name].update(ward_data)
                else:
                    h["wards"][ward_name] = ward_data
                # Reset age since status was freshly updated
                h["wards"][ward_name]["age_min"] = 0.0

        if "specialists" in updates and updates["specialists"] is not None:
            for spec_key, spec_val in updates["specialists"].items():
                if spec_key in h["specialists"]:
                    h["specialists"][spec_key].update(spec_val)
                else:
                    h["specialists"][spec_key] = spec_val

        if "equipment" in updates and updates["equipment"] is not None:
            h["equipment"].update(updates["equipment"])

        if "er_load" in updates and updates["er_load"] is not None:
            h["er_load"].update(updates["er_load"])

        h["updated_at"] = datetime.now(timezone.utc)
        return h

    def verify_hospital(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        """One-tap verification sets data freshness to 0 min."""
        h = self._hospitals.get(hospital_id)
        if not h:
            return None
        for ward in h["wards"].values():
            ward["age_min"] = 0.0
        h["updated_at"] = datetime.now(timezone.utc)
        return h

    def update_hospital_reliability(self, hospital_id: str, match: float, alpha: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Bayesian EMA update: R_new = (1 - alpha) * R_old + alpha * match
        """
        h = self._hospitals.get(hospital_id)
        if not h:
            return None
        r_old = h.get("reliability", 0.8)
        r_new = round((1.0 - alpha) * r_old + alpha * match, 3)
        h["reliability"] = max(0.1, min(1.0, r_new))
        h["updated_at"] = datetime.now(timezone.utc)
        return h

    def recalculate_held_beds(self, hospital_id: str):
        """Recalculates held_beds for a hospital based on active HELD reservations."""
        count = sum(
            1 for r in self._reservations.values()
            if r["hospital_id"] == hospital_id and r["status"] == "HELD"
        )
        if hospital_id in self._hospitals:
            self._hospitals[hospital_id]["held_beds"] = count

    # --- Cases Accessors ---
    def create_case(self, case_dict: Dict[str, Any]) -> Dict[str, Any]:
        case_id = case_dict.get("id") or f"case-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        case_dict["id"] = case_id
        case_dict["status"] = case_dict.get("status", "OPEN")
        case_dict["created_at"] = now
        case_dict["updated_at"] = now
        case_dict.setdefault("assigned_hospital_id", None)
        case_dict.setdefault("reservation_id", None)
        case_dict.setdefault("recommendations", [])
        self._cases[case_id] = case_dict
        return case_dict

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        return self._cases.get(case_id)

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        case = self._cases.get(case_id)
        if not case:
            return None
        case.update(updates)
        case["updated_at"] = datetime.now(timezone.utc)
        return case

    def list_cases(self) -> List[Dict[str, Any]]:
        return list(self._cases.values())

    # --- Reservations Accessors ---
    def create_reservation(self, res_dict: Dict[str, Any]) -> Dict[str, Any]:
        res_id = res_dict.get("id") or f"res-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        res_dict["id"] = res_id
        res_dict["created_at"] = now
        res_dict["updated_at"] = now
        self._reservations[res_id] = res_dict

        if res_dict.get("status") == "HELD":
            self.recalculate_held_beds(res_dict["hospital_id"])
        return res_dict

    def get_reservation(self, res_id: str) -> Optional[Dict[str, Any]]:
        return self._reservations.get(res_id)

    def get_reservation_by_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        for r in self._reservations.values():
            if r["case_id"] == case_id and r["status"] in ["PROPOSED", "HELD"]:
                return r
        return None

    def update_reservation_status(self, res_id: str, new_status: str, rejection_reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        r = self._reservations.get(res_id)
        if not r:
            return None
        r["status"] = new_status
        if rejection_reason:
            r["rejection_reason"] = rejection_reason
        r["updated_at"] = datetime.now(timezone.utc)

        self.recalculate_held_beds(r["hospital_id"])
        return r

    def list_reservations_for_hospital(self, hospital_id: str) -> List[Dict[str, Any]]:
        return [r for r in self._reservations.values() if r["hospital_id"] == hospital_id]

    # --- Event log for Polling / SSE fallback ---
    def add_event(self, event_type: str, payload: Dict[str, Any]):
        event = {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        # Keep last 200 events
        if len(self._events) > 200:
            self._events = self._events[-200:]
        return event

    def get_events(self, since_index: int = 0) -> List[Dict[str, Any]]:
        return self._events[since_index:]


store = InMemoryStore()
