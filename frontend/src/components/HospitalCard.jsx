import React from 'react';
import { Star, ShieldAlert, Navigation, Clock, CheckCircle2 } from 'lucide-react';
import ConfidenceBar from './ConfidenceBar';
import FreshnessBadge from './FreshnessBadge';

export default function HospitalCard({
  hospital,
  isSelected,
  onSelect,
  onVerify,
  onConfirmAndNavigate,
  isNavigating,
}) {
  const {
    hospital_id,
    name,
    tier,
    hfr_id,
    ett,
    travel_time_min,
    er_delay_min,
    p_ok,
    freshness_band,
    data_age_min,
    reasons = [],
    is_primary,
    is_backup,
    capable = true,
  } = hospital;

  const cardBorder = isSelected
    ? '2px solid var(--border-focus)'
    : is_primary
    ? '1px solid #10b981'
    : is_backup
    ? '1px solid #38bdf8'
    : '1px solid var(--border-card)';

  const cardBg = isSelected
    ? 'var(--bg-card-selected)'
    : !capable
    ? 'rgba(239, 68, 68, 0.05)'
    : 'var(--bg-card)';

  return (
    <div
      onClick={() => onSelect && onSelect(hospital)}
      style={{
        backgroundColor: cardBg,
        border: cardBorder,
        borderRadius: '8px',
        padding: '14px',
        cursor: 'pointer',
        transition: 'all 0.15s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        position: 'relative',
        boxShadow: is_primary ? '0 0 15px rgba(16, 185, 129, 0.12)' : 'none',
      }}
    >
      {/* Top badges: Primary / Backup indicator & Tier */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {is_primary && (
            <span
              style={{
                backgroundColor: '#10b981',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: 800,
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.04em',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
              }}
            >
              <Star size={11} fill="#ffffff" /> PRIMARY RECOMMENDATION
            </span>
          )}
          {is_backup && (
            <span
              style={{
                backgroundColor: '#0284c7',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: 800,
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.04em',
              }}
            >
              BACKUP FACILITY
            </span>
          )}
          {!capable && (
            <span
              style={{
                backgroundColor: '#ef4444',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: 800,
                textTransform: 'uppercase',
                padding: '2px 8px',
                borderRadius: '4px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
              }}
            >
              <ShieldAlert size={11} /> INCAPABLE FOR THIS EMERGENCY
            </span>
          )}
        </div>

        <span
          style={{
            fontSize: '10px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            textTransform: 'uppercase',
          }}
        >
          {tier} · {hfr_id}
        </span>
      </div>

      {/* Hospital Name & Location info */}
      <div>
        <h3
          style={{
            fontSize: '15px',
            fontWeight: 700,
            color: capable ? 'var(--text-primary)' : 'var(--text-secondary)',
            marginBottom: '4px',
          }}
        >
          {name}
        </h3>
        <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Navigation size={13} color="var(--color-brand-light)" /> {travel_time_min} min drive
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={13} color="var(--color-warning)" /> {er_delay_min} min ER queue
          </span>
        </div>
      </div>

      {/* Metric comparison: ETT vs Travel */}
      {capable ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            backgroundColor: 'rgba(0, 0, 0, 0.25)',
            borderRadius: '6px',
            padding: '8px 10px',
            gap: '8px',
          }}
        >
          <div>
            <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Expected Treatment (ETT)
            </div>
            <div
              style={{
                fontSize: '17px',
                fontWeight: 800,
                color: 'var(--color-brand-light)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {ett} <span style={{ fontSize: '11px', fontWeight: 500 }}>min</span>
            </div>
          </div>
          <div>
            <ConfidenceBar pOk={p_ok} />
          </div>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px dashed #ef4444',
            borderRadius: '6px',
            padding: '8px 10px',
            fontSize: '12px',
            color: '#f87171',
          }}
        >
          Lacks required surgical/ICU capability. Arriving here guarantees secondary inter-hospital transfer penalty (+35m).
        </div>
      )}

      {/* Reasons breakdown list */}
      {reasons && reasons.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {reasons.map((r, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '6px',
                fontSize: '11.5px',
                color: 'var(--text-secondary)',
              }}
            >
              <CheckCircle2 size={13} color="var(--color-success)" style={{ marginTop: '2px', flexShrink: 0 }} />
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}

      {/* Action Button: Confirm & Start Navigation */}
      {capable && onConfirmAndNavigate && (
        <div style={{ marginTop: '4px' }}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onConfirmAndNavigate(hospital);
            }}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              backgroundColor: isNavigating ? '#10b981' : is_primary ? '#0284c7' : '#1e293b',
              color: '#ffffff',
              padding: '8px 12px',
              borderRadius: '6px',
              fontWeight: 700,
              fontSize: '12px',
              border: is_primary ? '1px solid #38bdf8' : '1px solid #334155',
              cursor: 'pointer',
              boxShadow: is_primary ? '0 0 10px rgba(2, 132, 199, 0.4)' : 'none',
            }}
          >
            <Navigation size={14} />
            {isNavigating
              ? '✓ Navigating & Pre-Alert Sent'
              : `Confirm & Start Navigation (${travel_time_min}m)`}
          </button>
        </div>
      )}

      {/* Card footer: Freshness badge */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: '8px',
          marginTop: '2px',
        }}
      >
        <FreshnessBadge
          band={freshness_band}
          ageMin={data_age_min}
          onVerify={onVerify}
          hospitalId={hospital_id}
        />
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {isNavigating ? 'Active Turn-by-Turn' : isSelected ? 'Selected destination' : 'Click to preview'}
        </span>
      </div>
    </div>
  );
}
