import React from 'react';

export default function ConfidenceBar({ pOk }) {
  const pct = Math.round(Math.max(0, Math.min(1, pOk)) * 100);

  // Colour gradient depending on probability
  let barColor = '#ef4444'; // Red
  if (pct >= 80) {
    barColor = '#10b981'; // Emerald
  } else if (pct >= 50) {
    barColor = '#f59e0b'; // Amber
  }

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '3px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
        <span style={{ fontWeight: 500 }}>Availability P(ok)</span>
        <span style={{ fontWeight: 700, color: barColor, fontFamily: 'var(--font-mono)' }}>
          {pct}%
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: '6px',
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          borderRadius: '3px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            backgroundColor: barColor,
            borderRadius: '3px',
            transition: 'width 0.4s ease-out, background-color 0.4s ease',
          }}
        />
      </div>
    </div>
  );
}
