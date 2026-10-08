"""
Pydantic data models for CMER API.
Strict validation and alignment with ABDM HFR IDs and clinical emergency categories.
"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


EmergencyCategory = Literal[
    "TRAUMA",
    "CARDIAC",
    "STROKE",
    "RESPIRATORY",
    "OBSTETRIC",
    "PAEDS_EMERGENCY",
    "BURNS",
    "SEPSIS",
    "GENERAL_ER",
]

ReservationStatus = Literal[
    "PROPOSED",
    "HELD",
    "REJECTED",
    "CLOSED",
    "EXPIRED",
    "RELEASED",
]

CaseStatus = Literal[
    "OPEN",
    "ASSIGNED",
    "EN_ROUTE",
    "ARRIVED",
    "DIVERTED",
    "CANCELLED",
    "CLOSED",
]


class WardStatus(BaseModel):
    total: int = Field(..., ge=0)
    free: int = Field(..., ge=0)
    age_min: float = Field(0.0, ge=0.0)


class SpecialistStatus(BaseModel):
    on_duty: bool
    name: Optional[str] = None


class HospitalStatusUpdate(BaseModel):
    wards: Optional[Dict[str, WardStatus]] = None
    specialists: Optional[Dict[str, SpecialistStatus]] = None
    equipment: Optional[Dict[str, bool]] = None
    er_load: Optional[Dict[str, Any]] = None


class HospitalVerifyRequest(BaseModel):
    confirmed_by: Optional[str] = "dispatcher"
    notes: Optional[str] = None


class CaseCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    caller_phone: Optional[str] = None
    lat: float
    lng: float
    category: EmergencyCategory
    severity: Optional[str] = "CRITICAL"
    notes: Optional[str] = None
    ambulance_id: Optional[str] = None


class CaseCategoryUpdate(BaseModel):
    category: EmergencyCategory
    updated_by: Optional[str] = "crew"
    reason: Optional[str] = None


class CaseAcceptRequest(BaseModel):
    hospital_id: str
    ambulance_id: Optional[str] = "AMB-108"
    crew_notes: Optional[str] = None


class CaseOverrideRequest(BaseModel):
    hospital_id: str
    override_reason: str
    unstable_patient: bool = False
    crew_notes: Optional[str] = None


class ReservationConfirmRejectRequest(BaseModel):
    confirmed: bool
    reason: Optional[str] = None
    confirmed_by: Optional[str] = "ER_lead"


class CaseArrivalFeedback(BaseModel):
    actual_bed_available: bool
    actual_specialist_present: bool
    actual_equipment_functional: bool
    wait_time_minutes: float = Field(0.0, ge=0.0)
    crew_feedback_notes: Optional[str] = None


class HospitalResponse(BaseModel):
    id: str
    hfr_id: str
    name: str
    tier: str
    lat: float
    lng: float
    emergency_phone: str
    sms_number: str
    reliability: float
    capabilities: List[str]
    wards: Dict[str, Any]
    specialists: Dict[str, Any]
    equipment: Dict[str, bool]
    er_load: Dict[str, Any]
    held_beds: int = 0
    updated_at: datetime


class RankedHospitalResponse(BaseModel):
    hospital_id: str
    hfr_id: str
    name: str
    tier: str
    lat: float
    lng: float
    capable: bool
    ett: float
    travel_time_min: float
    er_delay_min: float
    p_ok: float
    freshness_band: str
    data_age_min: float
    reasons: List[str]
    is_primary: bool = False
    is_backup: bool = False


class CaseResponse(BaseModel):
    id: str
    status: CaseStatus
    lat: float
    lng: float
    category: EmergencyCategory
    severity: str
    ambulance_id: Optional[str] = None
    assigned_hospital_id: Optional[str] = None
    reservation_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    recommendations: List[RankedHospitalResponse]
    override_reason: Optional[str] = None


class ReservationResponse(BaseModel):
    id: str
    case_id: str
    hospital_id: str
    ambulance_id: str
    status: ReservationStatus
    ward: str
    eta_min: float
    hold_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    rejection_reason: Optional[str] = None
