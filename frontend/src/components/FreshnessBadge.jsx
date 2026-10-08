import React from 'react';
import { Clock, ShieldCheck, AlertCircle } from 'lucide-react';

export default function FreshnessBadge({ band, ageMin, onVerify, hospitalId }) {
  const getBadgeStyle = () => {
    switch (band) {
      case 'fresh':
        return {
          bg: 'rgba(16, 185, 129, 0.15)',
          border: '#10b981',
          text: '#34d399',
          icon: <ShieldCheck size={13} />,
          label: `Fresh · ${Math.round(ageMin)}m`,
        };
      case 'aging':
        return {
          bg: 'rgba(245, 158, 11, 0.15)',
          border: '#f59e0b',
          text: '#fbbf24',
          icon: <Clock size={13} />,
          label: `Aging · ${Math.round(ageMin)}m`,
        };
      case 'stale':
      default:
        return {
          bg: 'rgba(239, 68, 68, 0.18)',
          border: '#ef4444',
          text: '#f87171',
          icon: <AlertCircle size={13} />,
          label: `Stale · ${Math.round(ageMin)}m`,
        };
    }
  };

  const style = getBadgeStyle();

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: 600,
          backgroundColor: style.bg,
          border: `1px solid ${style.border}`,
          color: style.text,
          letterSpacing: '0.02em',
        }}
      >
        {style.icon}
        {style.label}
      </span>
      {band === 'stale' && onVerify && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onVerify(hospitalId);
          }}
          style={{
            padding: '2px 8px',
            fontSize: '10px',
            fontWeight: 700,
            textTransform: 'uppercase',
            backgroundColor: '#0284c7',
            color: '#ffffff',
            borderRadius: '4px',
            border: 'none',
          }}
          title="Call or radio-verify bed status, resetting age to 0"
        >
          Verify
        </button>
      )}
    </div>
  );
}
