import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2,
  BedDouble,
  UserCheck,
  Cpu,
  Plus,
  Minus,
  Clock,
  RefreshCw,
} from 'lucide-react';
import PreAlertModal from '../components/PreAlertModal';
import {
  fetchHospitals,
  fetchHospitalById,
  fetchHospitalReservations,
  updateHospitalStatus,
  confirmReservation,
  rejectReservation,
  subscribeWebSocket,
} from '../services/api';

export default function HospitalDashboard() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [allHospitals, setAllHospitals] = useState([]);
  const [currentHospitalId, setCurrentHospitalId] = useState(id || 'hosp-victoria');
  const [hospital, setHospital] = useState(null);
  const [reservations, setReservations] = useState([]);
  const [incomingPreAlert, setIncomingPreAlert] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState(null);

  // Sync route param with state
  useEffect(() => {
    if (id && id !== currentHospitalId) {
      setCurrentHospitalId(id);
    }
  }, [id, currentHospitalId]);

  // Load all hospitals for dropdown switcher
  useEffect(() => {
    fetchHospitals()
      .then((data) => setAllHospitals(data))
      .catch((err) => console.error(err));
  }, []);

  // Load current hospital data
  const loadHospitalData = useCallback(async () => {
    try {
      const data = await fetchHospitalById(currentHospitalId);
      setHospital(data);
      const resData = await fetchHospitalReservations(currentHospitalId);
      setReservations(resData);
    } catch (err) {
      console.error('Failed to load hospital data:', err);
    }
  }, [currentHospitalId]);

  useEffect(() => {
    loadHospitalData();
  }, [loadHospitalData]);

  // Subscribe to real-time WebSocket events for this hospital
  useEffect(() => {
    const unsubscribe = subscribeWebSocket(
      'hospital',
      currentHospitalId,
      (msg) => {
        if (msg.type === 'prealert') {
          // Trigger high-priority pop-up modal
          setIncomingPreAlert(msg.payload);
        } else if (msg.type === 'reservation.updated' || msg.type === 'status.updated') {
          loadHospitalData();
        }
      },
      (err) => console.error('Hospital WS error', err)
    );
    return () => unsubscribe();
  }, [currentHospitalId, loadHospitalData]);

  // Bed +/- stepper handler
  const handleBedChange = async (wardName, delta) => {
    if (!hospital || !hospital.wards[wardName]) return;
    const currentFree = hospital.wards[wardName].free || 0;
    const newFree = Math.max(0, currentFree + delta);

    const updatedWards = {
      ...hospital.wards,
      [wardName]: {
        ...hospital.wards[wardName],
        free: newFree,
      },
    };

    setIsUpdating(true);
    try {
      const updated = await updateHospitalStatus(currentHospitalId, { wards: updatedWards });
      setHospital(updated);
      setActionSuccessMsg(`Updated ${wardName} beds to ${newFree}`);
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Failed to update beds:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  // Toggle specialist on-duty status
  const handleSpecialistToggle = async (specKey) => {
    if (!hospital || !hospital.specialists[specKey]) return;
    const currentStatus = hospital.specialists[specKey].on_duty;

    const updatedSpecialists = {
      ...hospital.specialists,
      [specKey]: {
        ...hospital.specialists[specKey],
        on_duty: !currentStatus,
      },
    };

    try {
      const updated = await updateHospitalStatus(currentHospitalId, {
        specialists: updatedSpecialists,
      });
      setHospital(updated);
    } catch (err) {
      console.error('Failed to toggle specialist:', err);
    }
  };

  // Toggle equipment operational status
  const handleEquipmentToggle = async (eqKey) => {
    if (!hospital || hospital.equipment[eqKey] === undefined) return;
    const currentStatus = hospital.equipment[eqKey];

    const updatedEq = {
      ...hospital.equipment,
      [eqKey]: !currentStatus,
    };

    try {
      const updated = await updateHospitalStatus(currentHospitalId, { equipment: updatedEq });
      setHospital(updated);
    } catch (err) {
      console.error('Failed to toggle equipment:', err);
    }
  };

  // PreAlert Modal Confirmation
  const handleConfirmPreAlert = async (resId) => {
    try {
      await confirmReservation(resId);
      setIncomingPreAlert(null);
      await loadHospitalData();
      setActionSuccessMsg('Bed reservation confirmed! Bed held until ETA + buffer.');
      setTimeout(() => setActionSuccessMsg(null), 4000);
    } catch (err) {
      console.error('Failed to confirm reservation:', err);
    }
  };

  // PreAlert Modal Rejection
  const handleRejectPreAlert = async (resId) => {
    try {
      await rejectReservation(resId, 'Emergency ward code blue');
      setIncomingPreAlert(null);
      await loadHospitalData();
    } catch (err) {
      console.error('Failed to reject reservation:', err);
    }
  };

  const activeHolds = reservations.filter((r) => r.status === 'HELD');

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)',
        overflowY: 'auto',
      }}
    >
      {/* High-priority modal when pre-alert arrives */}
      <PreAlertModal
        preAlert={incomingPreAlert}
        onConfirm={handleConfirmPreAlert}
        onReject={handleRejectPreAlert}
        isConfirming={isUpdating}
      />

      {/* Top Bar with Hospital Selector */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 24px',
          backgroundColor: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-card)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--color-success)',
            }}
          >
            <Building2 size={18} color="var(--color-success)" />
            <span style={{ fontWeight: 800, fontSize: '15px' }}>HOSPITAL RECEPTION</span>
          </div>

          {/* Hospital Switcher */}
          <select
            value={currentHospitalId}
            onChange={(e) => {
              const newId = e.target.value;
              setCurrentHospitalId(newId);
              navigate(`/hospital/${newId}`);
            }}
            style={{
              padding: '7px 12px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              color: 'var(--text-primary)',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            {allHospitals.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.tier.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '12px' }}>
          {actionSuccessMsg && (
            <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>
              ✓ {actionSuccessMsg}
            </span>
          )}
          <button
            onClick={loadHospitalData}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              color: 'var(--text-secondary)',
              padding: '6px 12px',
              borderRadius: '6px',
            }}
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      {hospital && (
        <div
          style={{
            maxWidth: '1200px',
            width: '100%',
            margin: '0 auto',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '24px',
          }}
        >
          {/* Facility Profile Header Banner */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-card)',
              borderRadius: '10px',
              padding: '20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h1 style={{ fontSize: '22px', fontWeight: 800 }}>{hospital.name}</h1>
                <span
                  style={{
                    backgroundColor: 'rgba(2, 132, 199, 0.2)',
                    color: '#38bdf8',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                  }}
                >
                  {hospital.tier}
                </span>
              </div>
              <div
                style={{
                  color: 'var(--text-secondary)',
                  fontSize: '13px',
                  marginTop: '4px',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                ABDM HFR ID: <strong style={{ color: '#f8fafc' }}>{hospital.hfr_id}</strong> · Emergency: {hospital.emergency_phone}
              </div>
            </div>

            {/* Live Reliability & Active Holds count */}
            <div style={{ display: 'flex', gap: '20px' }}>
              <div
                style={{
                  backgroundColor: 'rgba(0,0,0,0.3)',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-card)',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Reliability Score (R)
                </div>
                <div
                  style={{
                    fontSize: '22px',
                    fontWeight: 800,
                    color: hospital.reliability >= 0.8 ? 'var(--color-success)' : 'var(--color-warning)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {Math.round(hospital.reliability * 100)}%
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(0,0,0,0.3)',
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-card)',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Active Bed Holds
                </div>
                <div
                  style={{
                    fontSize: '22px',
                    fontWeight: 800,
                    color: activeHolds.length > 0 ? '#38bdf8' : 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {hospital.held_beds || activeHolds.length}
                </div>
              </div>
            </div>
          </div>

          {/* Active 108 Pre-Alerts & Holds Section */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-card)',
              borderRadius: '10px',
              padding: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={18} color="var(--color-brand-light)" /> Active Pre-Alerts & Bed Reservations ({reservations.length})
              </h2>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Holds prevent double-allocation by dispatcher engine
              </span>
            </div>

            {reservations.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', fontSize: '13px' }}>
                No active 108 reservations currently held for this facility.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
                {reservations.map((r) => {
                  const isHeld = r.status === 'HELD';
                  return (
                    <div
                      key={r.id}
                      style={{
                        backgroundColor: isHeld ? 'rgba(16, 185, 129, 0.08)' : 'var(--bg-card)',
                        border: isHeld ? '1px solid var(--color-success)' : '1px solid var(--border-card)',
                        borderRadius: '8px',
                        padding: '14px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: 800,
                            padding: '2px 8px',
                            borderRadius: '4px',
                            backgroundColor: isHeld ? 'var(--color-success)' : '#ef4444',
                            color: '#ffffff',
                          }}
                        >
                          {r.status}
                        </span>
                        <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          {r.ambulance_id || 'AMB-108'}
                        </span>
                      </div>

                      <div style={{ fontSize: '14px', fontWeight: 700 }}>
                        {r.ward} Ward Reserved · ETA ~{r.eta_min}m
                      </div>

                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Case: {r.case_id}
                      </div>

                      {r.hold_expires_at && (
                        <div style={{ fontSize: '11px', color: '#38bdf8' }}>
                          Hold expires at: {new Date(r.hold_expires_at).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Ward Bed Steppers Grid (Immediate real-time updater) */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-card)',
              borderRadius: '10px',
              padding: '20px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BedDouble size={18} color="var(--color-brand-light)" /> Ward Capacity & Bed Steppers
                </h2>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Modifying free beds updates the dispatcher in real time via WebSockets and recalculates P(ok)
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '16px' }}>
              {Object.entries(hospital.wards).map(([wardName, wardInfo]) => (
                <div
                  key={wardName}
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-card)',
                    borderRadius: '8px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 800, fontSize: '14px', color: '#f8fafc' }}>
                      {wardName}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Total: {wardInfo.total}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Free Available
                      </div>
                      <div
                        style={{
                          fontSize: '28px',
                          fontWeight: 800,
                          color: wardInfo.free > 0 ? 'var(--color-brand-light)' : '#ef4444',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {wardInfo.free}
                      </div>
                    </div>

                    {/* Stepper Buttons */}
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => handleBedChange(wardName, -1)}
                        disabled={wardInfo.free <= 0 || isUpdating}
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(239, 68, 68, 0.2)',
                          border: '1px solid #ef4444',
                          color: '#f87171',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          cursor: wardInfo.free <= 0 ? 'not-allowed' : 'pointer',
                          opacity: wardInfo.free <= 0 ? 0.5 : 1,
                        }}
                        title="Decrement available bed"
                      >
                        <Minus size={16} />
                      </button>

                      <button
                        onClick={() => handleBedChange(wardName, 1)}
                        disabled={isUpdating}
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(16, 185, 129, 0.2)',
                          border: '1px solid var(--color-success)',
                          color: '#34d399',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                        title="Increment available bed"
                      >
                        <Plus size={16} />
                      </button>
                    </div>
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                    Data Age: {Math.round(wardInfo.age_min || 0)} min ago
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Specialists & Critical Equipment Toggles */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Specialists Panel */}
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-card)',
                borderRadius: '10px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              <h2 style={{ fontSize: '15px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserCheck size={18} color="var(--color-brand-light)" /> On-Duty Specialist Roster
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(hospital.specialists || {}).map(([specKey, specData]) => (
                  <div
                    key={specKey}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: 'var(--bg-card)',
                      padding: '10px 14px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-card)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '13px' }}>
                        {specData.name || specKey}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {specKey} Specialist
                      </div>
                    </div>

                    <button
                      onClick={() => handleSpecialistToggle(specKey)}
                      style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: specData.on_duty ? 'var(--color-success)' : 'rgba(239,68,68,0.2)',
                        border: specData.on_duty ? 'none' : '1px solid #ef4444',
                        color: specData.on_duty ? '#ffffff' : '#f87171',
                      }}
                    >
                      {specData.on_duty ? 'ON DUTY' : 'OFF DUTY'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Equipment Panel */}
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-card)',
                borderRadius: '10px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              <h2 style={{ fontSize: '15px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Cpu size={18} color="var(--color-brand-light)" /> Critical Equipment Readiness
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(hospital.equipment || {}).map(([eqKey, isAvailable]) => (
                  <div
                    key={eqKey}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: 'var(--bg-card)',
                      padding: '10px 14px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-card)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '13px' }}>{eqKey} Scanner / System</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Vital for advanced emergency capability verification
                      </div>
                    </div>

                    <button
                      onClick={() => handleEquipmentToggle(eqKey)}
                      style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: isAvailable ? 'var(--color-brand)' : 'rgba(239,68,68,0.2)',
                        border: isAvailable ? 'none' : '1px solid #ef4444',
                        color: isAvailable ? '#ffffff' : '#f87171',
                      }}
                    >
                      {isAvailable ? 'OPERATIONAL' : 'OFFLINE'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
