"""
FastAPI Application and CMER REST / WebSocket API Routes.
Implements Section 4.7 & Section 6 Phase 3 of CMER:
- GET /hospitals
- GET /hospitals/{id}
- PATCH /hospitals/{id}/status
- POST /hospitals/{id}/verify
- POST /cases
- GET /cases/{id}
- GET /cases/{id}/recommendations
- PATCH /cases/{id}/category
- POST /cases/{id}/accept
- POST /cases/{id}/override
- POST /cases/{id}/arrival
- POST /reservations/{id}/confirm
- POST /reservations/{id}/reject
- GET /reservations/hospital/{id}
- GET /events (polling fallback)
- WS /ws/{role}/{identifier}
- POST /integrations/cad/incident (mock CAD sidecar integration)
"""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    HospitalResponse,
    HospitalStatusUpdate,
    HospitalVerifyRequest,
    CaseCreateRequest,
    CaseResponse,
    CaseCategoryUpdate,
    CaseAcceptRequest,
    CaseOverrideRequest,
    CaseArrivalFeedback,
    ReservationConfirmRejectRequest,
    ReservationResponse,
    RankedHospitalResponse,
)
from app.store import store
from app.ws import manager
from app.engine.ranking import rank_hospitals, estimate_travel_time_minutes
from app.engine.capability import get_target_ward


app = FastAPI(
    title="Capability-Matched Emergency Referral (CMER) API",
    version="1.0.0",
    description="Emergency destination decision support engine for 108 ambulances.",
)

# Enable CORS for Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Hospital Endpoints
# -------------------------------------------------------------
@app.get("/hospitals", response_model=List[HospitalResponse])
def get_hospitals():
    """Returns all 15 synthetic hospitals in Bengaluru with capabilities and current bed states."""
    return store.list_hospitals()


@app.get("/hospitals/{hospital_id}", response_model=HospitalResponse)
def get_hospital(hospital_id: str):
    h = store.get_hospital(hospital_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return h


@app.patch("/hospitals/{hospital_id}/status", response_model=HospitalResponse)
async def update_hospital_status(hospital_id: str, updates: HospitalStatusUpdate):
    """
    Hospital dashboard updates beds, specialists, equipment or ER load.
    Triggers real-time notification to dispatchers.
    """
    update_data = updates.model_dump(exclude_unset=True)
    h = store.update_hospital_status(hospital_id, update_data)
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")

    await manager.broadcast_event(
        event_type="status.updated",
        payload={"hospital_id": hospital_id, "name": h["name"], "wards": h["wards"]},
        target_hospital_id=hospital_id,
    )
    return h


@app.post("/hospitals/{hospital_id}/verify", response_model=HospitalResponse)
async def verify_hospital(hospital_id: str, req: HospitalVerifyRequest = None):
    """
    One-tap verification by dispatcher or call center.
    Resets hospital data freshness age to 0 minutes.
    """
    h = store.verify_hospital(hospital_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")

    await manager.broadcast_event(
        event_type="status.verified",
        payload={"hospital_id": hospital_id, "name": h["name"]},
        target_hospital_id=hospital_id,
    )
    return h


# -------------------------------------------------------------
# Case Endpoints
# -------------------------------------------------------------
def _compute_and_attach_rankings(case_dict: dict) -> List[dict]:
    """Helper to run ranking engine and attach formatted recommendations to case."""
    hospitals = store.list_hospitals()
    ranked_candidates, _ = rank_hospitals(
        hospitals=hospitals,
        case_lat=case_dict["lat"],
        case_lng=case_dict["lng"],
        category=case_dict["category"],
    )

    recs = []
    for idx, c in enumerate(ranked_candidates):
        is_primary = (idx == 0)
        is_backup = (idx == 1)
        recs.append({
            "hospital_id": c["hospital_id"],
            "hfr_id": c["hfr_id"],
            "name": c["name"],
            "tier": c["tier"],
            "lat": c["lat"],
            "lng": c["lng"],
            "capable": c["capable"],
            "ett": c["ett"],
            "travel_time_min": c["travel_time_min"],
            "er_delay_min": c["er_delay_min"],
            "p_ok": c["p_ok"],
            "freshness_band": c["freshness_band"],
            "data_age_min": c["data_age_min"],
            "reasons": c["reasons"],
            "is_primary": is_primary,
            "is_backup": is_backup,
        })
    case_dict["recommendations"] = recs
    return recs


@app.post("/cases", response_model=CaseResponse)
async def create_case(req: CaseCreateRequest):
    """
    Dispatcher creates a new emergency case.
    Immediately filters capable hospitals and runs ETT ranking engine.
    Returns case with primary + backup recommendations and clinical reasons.
    """
    case_data = req.model_dump()
    case_data["status"] = "OPEN"
    _compute_and_attach_rankings(case_data)

    new_case = store.create_case(case_data)

    await manager.broadcast_event(
        event_type="case.created",
        payload={"case_id": new_case["id"], "category": new_case["category"], "severity": new_case["severity"]},
        case_id=new_case["id"],
    )
    return new_case


@app.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: str):
    c = store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    return c


@app.get("/cases/{case_id}/recommendations", response_model=List[RankedHospitalResponse])
def get_case_recommendations(case_id: str):
    c = store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    # Freshly recalculate to reflect any live bed / reservation updates
    recs = _compute_and_attach_rankings(c)
    store.update_case(case_id, {"recommendations": recs})
    return recs


@app.patch("/cases/{case_id}/category", response_model=CaseResponse)
async def update_case_category(case_id: str, req: CaseCategoryUpdate):
    """
    EMT crew on scene re-evaluates or confirms the category (e.g. from GENERAL_ER to TRAUMA/NEURO).
    Triggers instant re-ranking of all candidate hospitals and pushes updates.
    """
    c = store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    c["category"] = req.category
    _compute_and_attach_rankings(c)
    updated_case = store.update_case(case_id, c)

    await manager.broadcast_event(
        event_type="case.reranked",
        payload={
            "case_id": case_id,
            "category": req.category,
            "primary": updated_case["recommendations"][0] if updated_case["recommendations"] else None,
        },
        case_id=case_id,
    )
    return updated_case


@app.post("/cases/{case_id}/accept", response_model=ReservationResponse)
async def accept_case_hospital(case_id: str, req: CaseAcceptRequest):
    """
    EMT accepts destination hospital recommendation (Primary or other).
    Generates a PROPOSED reservation and sends PRE-ALERT to the receiving hospital.
    """
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    hospital = store.get_hospital(req.hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    eta_min = estimate_travel_time_minutes(
        case["lat"], case["lng"], hospital["lat"], hospital["lng"]
    )
    target_ward = get_target_ward(case["category"])

    res_dict = {
        "case_id": case_id,
        "hospital_id": req.hospital_id,
        "ambulance_id": req.ambulance_id or case.get("ambulance_id") or "AMB-108",
        "status": "PROPOSED",
        "ward": target_ward,
        "eta_min": eta_min,
        "hold_expires_at": None,
        "rejection_reason": None,
    }
    res = store.create_reservation(res_dict)

    store.update_case(case_id, {
        "status": "ASSIGNED",
        "assigned_hospital_id": req.hospital_id,
        "reservation_id": res["id"],
    })

    # Broadcast PRE-ALERT to the receiving hospital
    await manager.broadcast_event(
        event_type="prealert",
        payload={
            "reservation_id": res["id"],
            "case_id": case_id,
            "hospital_id": req.hospital_id,
            "hospital_name": hospital["name"],
            "category": case["category"],
            "severity": case["severity"],
            "eta_min": eta_min,
            "target_ward": target_ward,
        },
        target_hospital_id=req.hospital_id,
        case_id=case_id,
    )
    return res


@app.post("/cases/{case_id}/override", response_model=CaseResponse)
async def override_destination(case_id: str, req: CaseOverrideRequest):
    """
    EMT overrides the recommendation with rationale (e.g. unstable patient, bystander insistence).
    Logs the override and releases any prior holds.
    """
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Release any existing reservation
    existing_res = store.get_reservation_by_case(case_id)
    if existing_res:
        store.update_reservation_status(existing_res["id"], "RELEASED")

    hospital = store.get_hospital(req.hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    target_ward = get_target_ward(case["category"])
    eta_min = estimate_travel_time_minutes(case["lat"], case["lng"], hospital["lat"], hospital["lng"])

    # Create new hold for the overridden hospital
    res_dict = {
        "case_id": case_id,
        "hospital_id": req.hospital_id,
        "ambulance_id": case.get("ambulance_id") or "AMB-108",
        "status": "PROPOSED",
        "ward": target_ward,
        "eta_min": eta_min,
    }
    new_res = store.create_reservation(res_dict)

    updated = store.update_case(case_id, {
        "status": "ASSIGNED",
        "assigned_hospital_id": req.hospital_id,
        "reservation_id": new_res["id"],
        "override_reason": req.override_reason,
    })

    await manager.broadcast_event(
        event_type="crew.override",
        payload={
            "case_id": case_id,
            "hospital_id": req.hospital_id,
            "reason": req.override_reason,
            "unstable": req.unstable_patient,
        },
        target_hospital_id=req.hospital_id,
        case_id=case_id,
    )
    return updated


@app.post("/cases/{case_id}/arrival", response_model=HospitalResponse)
async def record_arrival(case_id: str, feedback: CaseArrivalFeedback):
    """
    EMT confirms arrival and reports whether bed, specialist, and equipment were matched.
    Updates the receiving hospital's reliability score R via Bayesian exponential moving average.
    """
    case = store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    hospital_id = case.get("assigned_hospital_id")
    if not hospital_id:
        raise HTTPException(status_code=400, detail="Case does not have an assigned hospital")

    # Close reservation
    if case.get("reservation_id"):
        store.update_reservation_status(case["reservation_id"], "CLOSED")

    store.update_case(case_id, {"status": "ARRIVED"})

    # Calculate match (1.0 = full match, 0.0 = complete mismatch)
    match_score = (
        (1.0 if feedback.actual_bed_available else 0.0) * 0.5
        + (1.0 if feedback.actual_specialist_present else 0.0) * 0.3
        + (1.0 if feedback.actual_equipment_functional else 0.0) * 0.2
    )

    updated_hospital = store.update_hospital_reliability(hospital_id, match_score)

    await manager.broadcast_event(
        event_type="case.arrived",
        payload={
            "case_id": case_id,
            "hospital_id": hospital_id,
            "match_score": match_score,
            "new_reliability": updated_hospital["reliability"],
        },
        target_hospital_id=hospital_id,
        case_id=case_id,
    )
    return updated_hospital


# -------------------------------------------------------------
# Reservation Endpoints
# -------------------------------------------------------------
@app.post("/reservations/{reservation_id}/confirm", response_model=ReservationResponse)
async def confirm_reservation(reservation_id: str, req: Optional[ReservationConfirmRejectRequest] = None):
    """
    Hospital confirms pre-alert.
    Reservation status transitions to HELD with hold countdown window (ETA + 20 min buffer).
    Held bed increments in hospital data.
    """
    r = store.get_reservation(reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    eta_min = r.get("eta_min", 20.0)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=(eta_min + 20.0))

    r["hold_expires_at"] = expires_at
    updated_res = store.update_reservation_status(reservation_id, "HELD")

    await manager.broadcast_event(
        event_type="reservation.updated",
        payload={
            "reservation_id": reservation_id,
            "status": "HELD",
            "hospital_id": r["hospital_id"],
            "case_id": r["case_id"],
            "expires_at": expires_at.isoformat(),
        },
        target_hospital_id=r["hospital_id"],
        case_id=r["case_id"],
    )
    return updated_res


@app.post("/reservations/{reservation_id}/reject", response_model=ReservationResponse)
async def reject_reservation(reservation_id: str, req: ReservationConfirmRejectRequest):
    """
    Hospital rejects pre-alert due to sudden code blue, power failure, or saturation.
    Transitions status to REJECTED. Prompt crew/dispatcher to route to backup hospital.
    """
    r = store.get_reservation(reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    updated_res = store.update_reservation_status(
        reservation_id, "REJECTED", rejection_reason=req.reason or "Hospital saturated"
    )

    await manager.broadcast_event(
        event_type="reservation.updated",
        payload={
            "reservation_id": reservation_id,
            "status": "REJECTED",
            "hospital_id": r["hospital_id"],
            "case_id": r["case_id"],
            "reason": req.reason,
        },
        target_hospital_id=r["hospital_id"],
        case_id=r["case_id"],
    )
    return updated_res


@app.get("/reservations/hospital/{hospital_id}", response_model=List[ReservationResponse])
def get_hospital_reservations(hospital_id: str):
    """Returns active and past pre-alerts and holds for this hospital."""
    return store.list_reservations_for_hospital(hospital_id)


# -------------------------------------------------------------
# Polling and Fallback Endpoints
# -------------------------------------------------------------
@app.get("/events")
def get_events_polling(since: int = Query(0, description="Index of last received event")):
    """Polling fallback for environments where WebSockets are unavailable or dropped."""
    return {
        "events": store.get_events(since_index=since),
        "count": len(store.get_events()),
    }


# -------------------------------------------------------------
# CAD Sidecar Integration Endpoint
# -------------------------------------------------------------
@app.post("/integrations/cad/incident", response_model=CaseResponse)
async def cad_sidecar_incident(req: CaseCreateRequest):
    """
    Mock CAD sidecar webhook.
    108 CAD pushes an incident; CMER automatically generates recommendations without altering core dispatch logs.
    """
    return await create_case(req)


# -------------------------------------------------------------
# WebSocket Hub Route
# -------------------------------------------------------------
@app.websocket("/ws/{role}/{identifier}")
async def websocket_endpoint(websocket: WebSocket, role: str, identifier: str):
    """
    Role channels:
    - /ws/dispatcher/all
    - /ws/hospital/{hospital_id}
    - /ws/crew/{case_id}
    """
    channel = f"{role}:{identifier}"
    await manager.connect(websocket, channel)
    try:
        while True:
            # Keep-alive heartbeat / message listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, channel)
    except Exception:
        await manager.disconnect(websocket, channel)
