/**
 * CMER API and WebSocket Client utilities
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://emergency-referrel.onrender.com';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

export async function fetchHospitals() {
  const res = await fetch(`${API_BASE}/hospitals`);
  if (!res.ok) throw new Error('Failed to load hospitals');
  return res.json();
}

export async function createCase(payload) {
  const res = await fetch(`${API_BASE}/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create case');
  return res.json();
}

export async function verifyHospital(hospitalId) {
  const res = await fetch(`${API_BASE}/hospitals/${hospitalId}/verify`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to verify hospital');
  return res.json();
}

export async function acceptCaseHospital(caseId, hospitalId, ambulanceId = 'KA-01-G-1081') {
  const res = await fetch(`${API_BASE}/cases/${caseId}/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hospital_id: hospitalId, ambulance_id: ambulanceId }),
  });
  if (!res.ok) throw new Error('Failed to accept hospital reservation');
  return res.json();
}

/**
 * Fetch shortest real road route from OSRM demo or fallback curved road points
 */
export async function fetchRoadRoute(startLat, startLng, destLat, destLng) {
  try {
    const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${destLng},${destLat}?overview=full&geometries=geojson`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (data.routes && data.routes.length > 0) {
        // coordinates come as [lng, lat] from GeoJSON, Leaflet expects [lat, lng]
        const rawCoords = data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng]);
        const distanceKm = Math.round((data.routes[0].distance / 1000) * 10) / 10;
        const durationMin = Math.round((data.routes[0].duration / 60) * 10) / 10;
        return { coords: rawCoords, distanceKm, durationMin };
      }
    }
  } catch (err) {
    console.warn('OSRM routing fetch failed, using fallback interpolated points:', err);
  }

  // Fallback synthetic waypoints with realistic urban detour
  const midLat = (startLat + destLat) / 2 + (destLng - startLng) * 0.15;
  const midLng = (startLng + destLng) / 2 - (destLat - startLat) * 0.15;
  const coords = [
    [startLat, startLng],
    [(startLat + midLat) / 2, (startLng + midLng) / 2],
    [midLat, midLng],
    [(midLat + destLat) / 2, (midLng + destLng) / 2],
    [destLat, destLng],
  ];
  return { coords, distanceKm: 4.8, durationMin: 14.5 };
}

export async function triggerMockCadIncident(payload) {
  const res = await fetch(`${API_BASE}/integrations/cad/incident`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to trigger mock CAD incident');
  return res.json();
}

export async function fetchHospitalById(hospitalId) {
  const res = await fetch(`${API_BASE}/hospitals/${hospitalId}`);
  if (!res.ok) throw new Error('Failed to load hospital details');
  return res.json();
}

export async function fetchHospitalReservations(hospitalId) {
  const res = await fetch(`${API_BASE}/reservations/hospital/${hospitalId}`);
  if (!res.ok) throw new Error('Failed to load hospital reservations');
  return res.json();
}

export async function confirmReservation(reservationId) {
  const res = await fetch(`${API_BASE}/reservations/${reservationId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmed: true, confirmed_by: 'ER_Lead' }),
  });
  if (!res.ok) throw new Error('Failed to confirm reservation');
  return res.json();
}

export async function rejectReservation(reservationId, reason = 'Saturation / Code Blue') {
  const res = await fetch(`${API_BASE}/reservations/${reservationId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirmed: false, reason }),
  });
  if (!res.ok) throw new Error('Failed to reject reservation');
  return res.json();
}

export async function updateHospitalStatus(hospitalId, updateData) {
  const res = await fetch(`${API_BASE}/hospitals/${hospitalId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateData),
  });
  if (!res.ok) throw new Error('Failed to update hospital status');
  return res.json();
}

export function subscribeWebSocket(role, identifier, onMessage, onError) {
  const wsUrl = `${WS_BASE}/ws/${role}/${identifier}`;
  let ws = null;
  let isClosedManually = false;

  function connect() {
    try {
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch {
          // heartbeat or non-json
        }
      };

      ws.onerror = (err) => {
        if (onError) onError(err);
      };

      ws.onclose = () => {
        if (!isClosedManually) {
          setTimeout(connect, 3000); // Reconnect after 3s
        }
      };
    } catch (err) {
      if (onError) onError(err);
    }
  }

  connect();

  return () => {
    isClosedManually = true;
    if (ws) ws.close();
  };
}
