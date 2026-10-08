import React, { useState, useEffect } from 'react';
import { Siren, Clock, Check, X } from 'lucide-react';

export default function PreAlertModal({ preAlert, onConfirm, onReject, isConfirming }) {
  const [countdownSec, setCountdownSec] = useState(120); // 2 minutes to accept or auto-escalate

  useEffect(() => {
    if (!preAlert) return;
    const timer = setInterval(() => {
      setCountdownSec((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [preAlert]);

  if (!preAlert) return null;

  const minutes = Math.floor(countdownSec / 60);
  const seconds = countdownSec % 60;
  const formattedCountdown = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.78)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          backgroundColor: '#0f172a',
          border: '2px solid #ef4444',
          borderRadius: '12px',
          boxShadow: '0 0 30px rgba(239, 68, 68, 0.4)',
          overflow: 'hidden',
          animation: 'pulse-subtle 2s infinite',
        }}
      >
        {/* Banner Header */}
        <div
          style={{
            backgroundColor: '#ef4444',
            color: '#ffffff',
            padding: '14px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Siren size={24} />
            <div>
              <div style={{ fontWeight: 800, fontSize: '16px', letterSpacing: '0.04em' }}>
                108 INCOMING PRE-ALERT
              </div>
              <div style={{ fontSize: '11px', opacity: 0.9 }}>
                Immediate Bed & Team Standby Required
              </div>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: 'rgba(0,0,0,0.3)',
              padding: '4px 8px',
              borderRadius: '6px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              fontSize: '13px',
            }}
          >
            <Clock size={14} /> {formattedCountdown}
          </div>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Clinical Details Card */}
          <div
            style={{
              backgroundColor: '#162032',
              border: '1px solid #273954',
              borderRadius: '8px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8', fontSize: '12px' }}>Emergency Category</span>
              <span
                style={{
                  color: '#f8fafc',
                  fontWeight: 700,
                  fontSize: '13px',
                  backgroundColor: '#0284c7',
                  padding: '2px 8px',
                  borderRadius: '4px',
                }}
              >
                {preAlert.category || 'TRAUMA'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8', fontSize: '12px' }}>Target Ward Requested</span>
              <span style={{ color: '#38bdf8', fontWeight: 700, fontSize: '14px' }}>
                {preAlert.target_ward || 'ICU / Trauma ER'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8', fontSize: '12px' }}>Ambulance ETA</span>
              <span
                style={{
                  color: '#10b981',
                  fontWeight: 800,
                  fontSize: '16px',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                ~{preAlert.eta_min || 18} mins
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8', fontSize: '12px' }}>Case Reference ID</span>
              <span style={{ color: '#94a3b8', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                {preAlert.case_id}
              </span>
            </div>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(2, 132, 199, 0.1)',
              border: '1px solid rgba(2, 132, 199, 0.3)',
              borderRadius: '6px',
              padding: '10px 12px',
              fontSize: '12px',
              color: '#94a3b8',
              lineHeight: 1.4,
            }}
          >
            <strong style={{ color: '#38bdf8' }}>Reservation Protocol:</strong> Confirming holds 1 bed for ETA + 20 min. The system automatically reduces this hospital's free bed count so other ambulances do not double-book.
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '10px' }}>
            <button
              onClick={() => onReject(preAlert.reservation_id)}
              disabled={isConfirming}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #ef4444',
                color: '#f87171',
                padding: '10px',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '13px',
              }}
            >
              <X size={16} /> Reject (Full)
            </button>

            <button
              onClick={() => onConfirm(preAlert.reservation_id)}
              disabled={isConfirming}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                backgroundColor: '#10b981',
                color: '#ffffff',
                padding: '10px',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '13px',
                boxShadow: '0 0 15px rgba(16, 185, 129, 0.4)',
              }}
            >
              <Check size={16} /> Confirm & Hold Bed
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
