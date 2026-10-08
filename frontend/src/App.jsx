import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import Dispatcher from './pages/Dispatcher';
import HospitalDashboard from './pages/Hospital';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Global Navigation Bar for Switcher */}
        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 20px',
            backgroundColor: '#090d16',
            borderBottom: '1px solid #1a2638',
            fontSize: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontWeight: 800, color: '#38bdf8', letterSpacing: '0.05em' }}>
              SEVA CMER · VIKSIT BHARAT 2047
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <NavLink
                to="/dispatcher"
                style={({ isActive }) => ({
                  color: isActive ? '#f8fafc' : '#94a3b8',
                  fontWeight: 600,
                  padding: '4px 10px',
                  borderRadius: '4px',
                  backgroundColor: isActive ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                  border: isActive ? '1px solid #38bdf8' : '1px solid transparent',
                  textDecoration: 'none',
                })}
              >
                Dispatcher Console
              </NavLink>
              <NavLink
                to="/hospital/hosp-victoria"
                style={({ isActive }) => ({
                  color: isActive ? '#f8fafc' : '#94a3b8',
                  fontWeight: 600,
                  padding: '4px 10px',
                  borderRadius: '4px',
                  backgroundColor: isActive ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                  border: isActive ? '1px solid #10b981' : '1px solid transparent',
                  textDecoration: 'none',
                })}
              >
                Hospital Dashboard
              </NavLink>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#94a3b8' }}>
            <span>Synthetic Bengaluru Corridor (15 Hospitals)</span>
            <span
              style={{
                backgroundColor: '#10b981',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '3px',
              }}
            >
              DECISION SUPPORT
            </span>
          </div>
        </nav>

        {/* Routes */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dispatcher" replace />} />
            <Route path="/dispatcher" element={<Dispatcher />} />
            <Route path="/hospital" element={<HospitalDashboard />} />
            <Route path="/hospital/:id" element={<HospitalDashboard />} />
            <Route path="*" element={<Navigate to="/dispatcher" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
