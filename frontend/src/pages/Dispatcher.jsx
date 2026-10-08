import React, { useState, useEffect, useCallback } from 'react';
import {
  Radio,
  RefreshCw,
  Activity,
  Sparkles,
} from 'lucide-react';
import MapView from '../components/MapView';
import HospitalCard from '../components/HospitalCard';
import {
  fetchHospitals,
  createCase,
  verifyHospital,
  triggerMockCadIncident,
  subscribeWebSocket,
  acceptCaseHospital,
  fetchRoadRoute,
} from '../services/api';

const EMERGENCY_CATEGORIES = [
  { id: 'TRAUMA', label: 'Severe Head Injury / Polytrauma', defaultSeverity: 'CRITICAL' },
  { id: 'CARDIAC', label: 'Acute STEMI / Cardiac Arrest', defaultSeverity: 'CRITICAL' },
  { id: 'STROKE', label: 'Acute Ischemic Stroke (<4.5h window)', defaultSeverity: 'CRITICAL' },
  { id: 'OBSTETRIC', label: 'Eclampsia / High-Risk Delivery', defaultSeverity: 'CRITICAL' },
  { id: 'BURNS', label: 'Extensive Thermal Burns (>30% TBSA)', defaultSeverity: 'CRITICAL' },
  { id: 'PAEDS_EMERGENCY', label: 'Paediatric / Neonatal Distress', defaultSeverity: 'CRITICAL' },
  { id: 'GENERAL_ER', label: 'General Acute Emergency', defaultSeverity: 'MODERATE' },
];

export default function Dispatcher() {
  const [hospitals, setHospitals] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('TRAUMA');
  const [incidentLocation, setIncidentLocation] = useState({
    lat: 12.942, // Basavanagudi corridor (near Shanthi nursing home)
    lng: 77.5745,
  });
  const [activeCase, setActiveCase] = useState(null);
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [rankingMode, setRankingMode] = useState('CMER'); // 'CMER' or 'NEAREST'
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [cadNotification, setCadNotification] = useState(null);
  const [activeRoute, setActiveRoute] = useState(null); // { coords, distanceKm, durationMin, hospitalName, hospitalId }

  // Load initial hospitals
  const loadHospitals = useCallback(async () => {
    try {
      const data = await fetchHospitals();
      setHospitals(data);
    } catch (err) {
      console.error('Failed to load hospitals:', err);
    }
  }, []);

  useEffect(() => {
    loadHospitals();
  }, [loadHospitals]);

  // Submit case and compute ETT ranking
  const handleCreateCase = useCallback(
    async (loc = incidentLocation, cat = selectedCategory) => {
      setLoading(true);
      try {
        const payload = {
          lat: loc.lat,
          lng: loc.lng,
          category: cat,
          severity: 'CRITICAL',
          ambulance_id: 'KA-01-G-1081',
          notes: 'Emergency 108 CAD dispatch triage',
        };
        const caseRes = await createCase(payload);
        setActiveCase(caseRes);
        if (caseRes.recommendations && caseRes.recommendations.length > 0) {
          setSelectedHospital(caseRes.recommendations[0]);
        }
      } catch (err) {
        console.error('Case generation failed:', err);
      } finally {
        setLoading(false);
      }
    },
    [incidentLocation, selectedCategory]
  );

  // Auto-generate initial case on load for instant demo readiness
  useEffect(() => {
    handleCreateCase();
  }, []);

  // Subscribe to real-time WebSockets
  useEffect(() => {
    const unsubscribe = subscribeWebSocket(
      'dispatcher',
      'all',
      (msg) => {
        setWsConnected(true);
        if (msg.type === 'status.updated' || msg.type === 'status.verified') {
          loadHospitals();
          // If active case, refresh recommendations
          if (activeCase) {
            handleCreateCase();
          }
        }
        if (msg.type === 'case.created' && msg.payload.case_id !== activeCase?.id) {
          setCadNotification(`New CAD Case received: ${msg.payload.case_id}`);
          setTimeout(() => setCadNotification(null), 5000);
        }
      },
      () => setWsConnected(false)
    );
    return () => unsubscribe();
  }, [loadHospitals, activeCase, handleCreateCase]);

  // Handle map click to re-locate incident
  const handleMapClick = (lat, lng) => {
    const newLoc = { lat, lng };
    setIncidentLocation(newLoc);
    handleCreateCase(newLoc, selectedCategory);
  };

  // Handle category change
  const handleCategoryChange = (e) => {
    const cat = e.target.value;
    setSelectedCategory(cat);
    handleCreateCase(incidentLocation, cat);
  };

  // One-tap verify stale hospital
  const handleVerify = async (hospId) => {
    try {
      await verifyHospital(hospId);
      await loadHospitals();
      await handleCreateCase();
    } catch (err) {
      console.error('Verification failed:', err);
    }
  };

  // Trigger Mock 108 CAD Incident
  const handleMockCadTrigger = async () => {
    try {
      const mockCadCase = {
        lat: 12.925,
        lng: 77.585,
        category: 'CARDIAC',
        severity: 'CRITICAL',
        notes: 'Inbound 108 CAD webhook: Sudden collapse at Jayanagar 4th Block',
        ambulance_id: 'KA-01-G-1082',
      };
      setIncidentLocation({ lat: mockCadCase.lat, lng: mockCadCase.lng });
      setSelectedCategory('CARDIAC');
      const res = await triggerMockCadIncident(mockCadCase);
      setActiveCase(res);
      if (res.recommendations?.length > 0) {
        setSelectedHospital(res.recommendations[0]);
      }
      setCadNotification('Live 108 CAD Incident Ingested via Sidecar Adapter!');
      setTimeout(() => setCadNotification(null), 4000);
    } catch (err) {
      console.error('Mock CAD failed:', err);
    }
  };

  // Confirm hospital, send Pre-Alert to hospital dashboard, and trigger shortest turn-by-turn road navigation
  const handleConfirmAndNavigate = async (targetHosp) => {
    if (!activeCase?.id) return;
    try {
      setLoading(true);
      // 1. Send Pre-Alert to Hospital dashboard (POST /cases/{id}/accept)
      await acceptCaseHospital(activeCase.id, targetHosp.hospital_id);

      // 2. Fetch shortest real road route geometry
      const destLat = targetHosp.lat || targetHosp.raw_hospital?.lat;
      const destLng = targetHosp.lng || targetHosp.raw_hospital?.lng;
      const routeData = await fetchRoadRoute(
        incidentLocation.lat,
        incidentLocation.lng,
        destLat,
        destLng
      );

      setActiveRoute({
        ...routeData,
        hospitalId: targetHosp.hospital_id,
        hospitalName: targetHosp.name,
      });

      setSelectedHospital(targetHosp);
      setCadNotification(`Pre-Alert sent to ${targetHosp.name}! Real-time road navigation active.`);
      setTimeout(() => setCadNotification(null), 5000);
    } catch (err) {
      console.error('Failed to initiate navigation:', err);
    } finally {
      setLoading(false);
    }
  };

  // Compute displayed list depending on rankingMode
  const displayedRecommendations = () => {
    if (!activeCase?.recommendations) return [];

    if (rankingMode === 'CMER') {
      return activeCase.recommendations;
    }

    // Nearest mode: sort strictly by travel time / distance, ignoring capabilities
    // Map seed hospitals to simulate traditional naive 108 dispatch
    const naiveList = hospitals.map((h) => {
      // Calculate simple crow-flies/travel estimate
      const rad = Math.PI / 180;
      const dlat = (h.lat - incidentLocation.lat) * rad;
      const dlng = (h.lng - incidentLocation.lng) * rad;
      const a =
        Math.sin(dlat / 2) * Math.sin(dlat / 2) +
        Math.cos(incidentLocation.lat * rad) *
          Math.cos(h.lat * rad) *
          Math.sin(dlng / 2) *
          Math.sin(dlng / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      const distKm = 6371 * c;
      const driveMin = Math.round((distKm * 1.4 / 30) * 60 * 10) / 10;

      // Check if actually capable
      const isActuallyCapable = activeCase.recommendations.some(
        (r) => r.hospital_id === h.id && r.capable
      );

      return {
        hospital_id: h.id,
        hfr_id: h.hfr_id,
        name: h.name,
        tier: h.tier,
        lat: h.lat,
        lng: h.lng,
        capable: isActuallyCapable,
        travel_time_min: driveMin,
        er_delay_min: h.er_load?.est_delay_min || 10,
        ett: driveMin + 10,
        p_ok: h.reliability || 0.8,
        freshness_band: 'fresh',
        data_age_min: 5,
        reasons: isActuallyCapable
          ? ['Nearest facility with capability']
          : ['Lacks ICU / Trauma / CT capability for this condition'],
        is_primary: false,
        is_backup: false,
      };
    });

    naiveList.sort((a, b) => a.travel_time_min - b.travel_time_min);
    if (naiveList.length > 0) naiveList[0].is_primary = true;
    if (naiveList.length > 1) naiveList[1].is_backup = true;

    return naiveList;
  };

  const recs = displayedRecommendations();
  const primaryHosp = recs.find((r) => r.is_primary);
  const backupHosp = recs.find((r) => r.is_backup);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        width: '100%',
        height: '100%',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)',
        overflow: 'hidden',
      }}
    >
      {/* Top Clinical Header */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 20px',
          backgroundColor: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-card)',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'rgba(2, 132, 199, 0.15)',
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--color-brand)',
            }}
          >
            <Activity size={18} color="var(--color-brand-light)" />
            <span style={{ fontWeight: 800, fontSize: '15px', letterSpacing: '0.04em' }}>
              CMER 108
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              DISPATCHER CONSOLE
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: wsConnected ? 'var(--color-success)' : 'var(--color-warning)',
              }}
            />
            <span style={{ color: 'var(--text-secondary)' }}>
              {wsConnected ? 'Real-time WebSocket Live' : 'Connecting WebSocket...'}
            </span>
          </div>
        </div>

        {/* CAD Sidecar Button & Quick Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleMockCadTrigger}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#4338ca',
              color: '#ffffff',
              padding: '7px 14px',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 600,
            }}
            title="Simulates 108 CAD pushing an incident into CMER companion overlay"
          >
            <Radio size={14} /> Incoming from 108 CAD
          </button>

          <button
            onClick={async () => {
              await loadHospitals();
              await handleCreateCase(incidentLocation, selectedCategory);
              setActiveRoute(null);
              setCadNotification('Recommendations recalculated with latest hospital status!');
              setTimeout(() => setCadNotification(null), 3000);
            }}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              color: 'var(--text-secondary)',
              padding: '7px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> {loading ? 'Recalculating...' : 'Recalculate'}
          </button>
        </div>
      </header>

      {/* CAD Notification Toast banner */}
      {cadNotification && (
        <div
          style={{
            backgroundColor: '#4338ca',
            color: '#ffffff',
            padding: '8px 20px',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
          }}
        >
          <Sparkles size={16} /> {cadNotification}
        </div>
      )}

      {/* Main Workspace: Left Controls & Recommendations, Right Leaflet Map */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Side Panel */}
        <aside
          style={{
            width: '460px',
            minWidth: '420px',
            backgroundColor: 'var(--bg-surface)',
            borderRight: '1px solid var(--border-card)',
            display: 'flex',
            flexDirection: 'column',
            overflowY: 'auto',
            padding: '16px',
            gap: '16px',
          }}
        >
          {/* Triage & Emergency Category Selector */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              borderRadius: '8px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  color: 'var(--text-muted)',
                }}
              >
                108 Incident Triage
              </span>
              <span
                style={{
                  fontSize: '11px',
                  color: 'var(--color-brand-light)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {activeCase?.id || 'Ready'}
              </span>
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  marginBottom: '4px',
                }}
              >
                Emergency Category
              </label>
              <select
                value={selectedCategory}
                onChange={handleCategoryChange}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-card)',
                  color: 'var(--text-primary)',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: 600,
                  outline: 'none',
                }}
              >
                {EMERGENCY_CATEGORIES.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Coordinates and Click-to-move prompt */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: 'rgba(0,0,0,0.2)',
                padding: '6px 10px',
                borderRadius: '4px',
                fontSize: '11px',
                color: 'var(--text-muted)',
              }}
            >
              <span>
                Scene GPS: {incidentLocation.lat.toFixed(4)}, {incidentLocation.lng.toFixed(4)}
              </span>
              <span style={{ color: 'var(--color-brand-light)' }}>
                Click map to reposition
              </span>
            </div>
          </div>

          {/* Strategy Comparison Toggle: CMER (ETT) vs Baseline Nearest */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              borderRadius: '8px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Dispatch Strategy
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                Interactive A/B Toggle
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '6px',
                padding: '3px',
                gap: '4px',
              }}
            >
              <button
                onClick={() => setRankingMode('CMER')}
                style={{
                  padding: '8px',
                  borderRadius: '5px',
                  fontSize: '12px',
                  fontWeight: 700,
                  backgroundColor: rankingMode === 'CMER' ? 'var(--color-brand)' : 'transparent',
                  color: rankingMode === 'CMER' ? '#ffffff' : 'var(--text-secondary)',
                }}
              >
                CMER (Capability + ETT)
              </button>
              <button
                onClick={() => setRankingMode('NEAREST')}
                style={{
                  padding: '8px',
                  borderRadius: '5px',
                  fontSize: '12px',
                  fontWeight: 700,
                  backgroundColor: rankingMode === 'NEAREST' ? '#ef4444' : 'transparent',
                  color: rankingMode === 'NEAREST' ? '#ffffff' : 'var(--text-secondary)',
                }}
              >
                Baseline Nearest Only
              </button>
            </div>

            {rankingMode === 'NEAREST' ? (
              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '6px',
                  padding: '8px 10px',
                  fontSize: '11.5px',
                  color: '#f87171',
                }}
              >
                <strong>Warning (Status Quo Failure):</strong> Baseline selects the closest nursing home regardless of whether it has an ICU, neurosurgery, or CT scanner. Patient risks secondary inter-hospital transfer.
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  borderRadius: '6px',
                  padding: '8px 10px',
                  fontSize: '11.5px',
                  color: '#34d399',
                }}
              >
                <strong>CMER Decision Support:</strong> Filters out incapable clinics. Ranks verified surgical facilities by Expected Time to Treatment, accounting for arrival probability P(ok).
              </div>
            )}
          </div>

          {/* Ranked Hospital List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  color: 'var(--text-muted)',
                }}
              >
                Ranked Recommendations ({recs.length})
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                Sorted by {rankingMode === 'CMER' ? 'Expected Treatment Time' : 'Distance'}
              </span>
            </div>

            {recs.map((h) => (
              <HospitalCard
                key={h.hospital_id}
                hospital={h}
                isSelected={selectedHospital?.hospital_id === h.hospital_id}
                onSelect={(selected) => setSelectedHospital(selected)}
                onVerify={handleVerify}
                onConfirmAndNavigate={handleConfirmAndNavigate}
                isNavigating={activeRoute?.hospitalId === h.hospital_id}
              />
            ))}
          </div>
        </aside>

        {/* Right Map Canvas */}
        <main style={{ flex: 1, position: 'relative', height: '100%' }}>
          <MapView
            hospitals={recs}
            incidentLocation={incidentLocation}
            primaryHospitalId={primaryHosp?.hospital_id}
            backupHospitalId={backupHosp?.hospital_id}
            onHospitalSelect={(h) => setSelectedHospital(h)}
            onMapClick={handleMapClick}
            mode={rankingMode}
            activeRoute={activeRoute}
          />
        </main>
      </div>
    </div>
  );
}
