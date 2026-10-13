import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

/**
 * Creates custom colored map pin for hospitals:
 * - Green (★): Primary recommendation
 * - Blue (2): Backup hospital
 * - Red (✕): Incapable facility
 * - Amber / Red (+): Aging / Stale capable facilities
 */
function createHospitalIcon(hospital, isPrimary, isBackup, isCapable = true) {
  let bgColor = '#10b981'; // Fresh emerald
  let size = 28;
  let label = '+';

  if (!isCapable) {
    bgColor = '#ef4444'; // Incapable red
    size = 24;
    label = '✕';
  } else if (isPrimary) {
    bgColor = '#10b981'; // Green primary
    size = 34;
    label = '★';
  } else if (isBackup) {
    bgColor = '#0284c7'; // Blue backup
    size = 30;
    label = '2';
  } else if (hospital.freshness_band === 'stale') {
    bgColor = '#dc2626'; // Stale red
    label = '!';
  } else if (hospital.freshness_band === 'aging') {
    bgColor = '#f59e0b'; // Aging amber
    label = '+';
  }

  const border = isPrimary
    ? '3px solid #ffffff'
    : isBackup
    ? '2px solid #38bdf8'
    : '2px solid #ffffff';

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="
      background-color: ${bgColor};
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-weight: 800;
      font-size: ${size > 28 ? '15px' : '12px'};
      border: ${border};
      box-shadow: 0 0 12px rgba(0,0,0,0.8);
      cursor: pointer;
    ">${label}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function createIncidentIcon() {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="
      background-color: #ef4444;
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-size: 16px;
      border: 3px solid #ffffff;
      box-shadow: 0 0 18px #ef4444;
      animation: pulse-subtle 1.5s infinite;
      cursor: pointer;
    ">🚨</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
}

// Map Click Handler component to let dispatcher pick incident location
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

// Center view animator helper
function ChangeView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom || 12);
    }
  }, [center, zoom, map]);
  return null;
}

export default function MapView({
  hospitals = [],
  incidentLocation,
  primaryHospitalId,
  backupHospitalId,
  onHospitalSelect,
  onMapClick,
  mode = 'CMER',
  activeRoute = null, // { coords, distanceKm, durationMin, hospitalName }
}) {
  const defaultCenter = [12.9716, 77.5946]; // Bengaluru Center

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer
        center={incidentLocation ? [incidentLocation.lat, incidentLocation.lng] : defaultCenter}
        zoom={12}
        style={{ width: '100%', height: '100%', background: '#0b1320' }}
        scrollWheelZoom={true}
      >
        <ChangeView
          center={incidentLocation ? [incidentLocation.lat, incidentLocation.lng] : defaultCenter}
        />
        <MapClickHandler onMapClick={onMapClick} />

        {/* High-contrast dark OpenStreetMap CartoDB Tiles (without watermark) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Turn-by-Turn Route Navigation Polyline (Road Traffic Style) */}
        {activeRoute && activeRoute.coords && activeRoute.coords.length > 0 && (
          <>
            {/* Background shadow glow */}
            <Polyline
              positions={activeRoute.coords}
              pathOptions={{
                color: '#0284c7',
                weight: 8,
                opacity: 0.5,
              }}
            />
            {/* Main Road Route with traffic speed styling */}
            <Polyline
              positions={activeRoute.coords}
              pathOptions={{
                color: '#38bdf8',
                weight: 5,
                opacity: 0.95,
                dashArray: null,
              }}
            />
          </>
        )}

        {/* Incident Marker */}
        {incidentLocation && (
          <Marker
            position={[incidentLocation.lat, incidentLocation.lng]}
            icon={createIncidentIcon()}
          >
            <Popup>
              <div style={{ color: '#000', fontSize: '12px' }}>
                <strong>108 Emergency Incident Scene</strong>
                <br />
                {incidentLocation.lat.toFixed(4)}, {incidentLocation.lng.toFixed(4)}
                <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>
                  Click anywhere on map to reposition scene
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Hospital Markers */}
        {hospitals.map((h) => {
          const isPrimary = h.hospital_id === primaryHospitalId || h.id === primaryHospitalId;
          const isBackup = h.hospital_id === backupHospitalId || h.id === backupHospitalId;
          const isCapable = h.capable !== false;

          const lat = h.lat || (h.raw_hospital && h.raw_hospital.lat);
          const lng = h.lng || (h.raw_hospital && h.raw_hospital.lng);

          if (!lat || !lng) return null;

          return (
            <Marker
              key={h.hospital_id || h.id}
              position={[lat, lng]}
              icon={createHospitalIcon(h, isPrimary, isBackup, isCapable)}
              eventHandlers={{
                click: () => onHospitalSelect && onHospitalSelect(h),
              }}
            >
              <Popup>
                <div style={{ color: '#000', fontSize: '12px', minWidth: '170px' }}>
                  <div style={{ fontWeight: 'bold' }}>{h.name}</div>
                  <div style={{ color: '#666', fontSize: '11px' }}>{h.hfr_id}</div>
                  <div style={{ marginTop: '6px' }}>
                    {isCapable ? (
                      <>
                        <strong>ETT:</strong> {h.ett || '--'} min
                        <br />
                        <strong>Drive:</strong> {h.travel_time_min || h.travel_time || '--'} min
                        <br />
                        <strong>P(ok):</strong> {Math.round((h.p_ok || 0.8) * 100)}% probable
                      </>
                    ) : (
                      <span style={{ color: '#dc2626', fontWeight: 'bold' }}>
                        Incapable for this emergency category
                      </span>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Floating Active Turn-by-Turn Navigation HUD */}
      {activeRoute && (
        <div
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            zIndex: 1000,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid #10b981',
            borderRadius: '10px',
            padding: '14px 18px',
            boxShadow: '0 4px 25px rgba(0,0,0,0.7)',
            backdropFilter: 'blur(8px)',
            minWidth: '280px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span
              style={{
                backgroundColor: '#10b981',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 800,
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.04em',
              }}
            >
              ACTIVE 108 NAVIGATION
            </span>
            <span style={{ fontSize: '11px', color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
              FASTEST ROAD ROUTE
            </span>
          </div>

          <div style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
            {activeRoute.hospitalName}
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)' }}>
              {activeRoute.durationMin} <span style={{ fontSize: '14px', fontWeight: 600 }}>min</span>
            </div>
            <div style={{ fontSize: '14px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
              ({activeRoute.distanceKm} km via urban corridor)
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              color: '#34d399',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              padding: '6px 8px',
              borderRadius: '4px',
            }}
          >
            <span>✓ Pre-Alert Sent: Bed reservation held at receiving hospital</span>
          </div>
        </div>
      )}

      {/* Map Legend Floating Box - Perfectly Matching Icon Elements */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          zIndex: 1000,
          backgroundColor: 'rgba(15, 23, 42, 0.94)',
          border: '1px solid var(--border-card)',
          borderRadius: '8px',
          padding: '10px 14px',
          fontSize: '11.5px',
          color: 'var(--text-secondary)',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
          backdropFilter: 'blur(6px)',
        }}
      >
        <div style={{ fontWeight: 800, color: 'var(--text-primary)', marginBottom: '2px' }}>
          Map Symbols & Capabilities ({mode})
        </div>

        {/* Primary Hospital Icon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 800,
              border: '2px solid #ffffff',
            }}
          >
            ★
          </div>
          <span>Primary Recommendation (Lowest ETT)</span>
        </div>

        {/* Backup Hospital Icon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '10px',
              fontWeight: 800,
              border: '1.5px solid #38bdf8',
            }}
          >
            2
          </div>
          <span>Backup Facility (Secondary Destination)</span>
        </div>

        {/* Incapable Hospital Icon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '10px',
              fontWeight: 800,
              border: '1.5px solid #ffffff',
            }}
          >
            ✕
          </div>
          <span>Incapable Facility (Lacks Specialty / Equipment)</span>
        </div>

        {/* Incident Scene Icon */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              border: '2px solid #ffffff',
            }}
          >
            🚨
          </div>
          <span>108 Incident Scene (Click map to move)</span>
        </div>
      </div>
    </div>
  );
}
