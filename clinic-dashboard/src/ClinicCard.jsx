import React from 'react';
import { MapPin, Phone, ShieldCheck, ShieldAlert, Clock } from 'lucide-react';

export default function ClinicCard({ clinic }) {
  const isNhimaAccepted = clinic.nhima_accepted && clinic.nhima_accepted.toString().toLowerCase().includes('yes');
  const is24Hours = clinic.hours && clinic.hours.toString().toLowerCase().includes('24');

  // Determine border signal color: Green (NHIMA Available), Red (NHIMA Unavailable)
  let borderColor = '#dc2626'; // Red default (Unavailable)
  let badgeBg = '#7f1d1d';
  let badgeColor = '#fee2e2';
  let badgeText = 'NHIMA Unavailable';

  if (isNhimaAccepted) {
    borderColor = '#16a34a'; // Green (Available)
    badgeBg = '#065f46';
    badgeColor = '#dcfce7';
    badgeText = 'NHIMA Available';
  }

  return (
    <div style={{ 
      border: '1px solid #374151', 
      padding: '16px', 
      borderRadius: '8px', 
      background: '#000000', // Pure Black Background
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.5)',
      borderLeft: `6px solid ${borderColor}` // Dynamic Green/Red Signal Border
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <h4 style={{ margin: '0', color: '#ffffff', fontSize: '16px' }}>{clinic.name}</h4>
        
        {/* Dynamic Badge */}
        <span style={{ 
          fontSize: '11px', 
          padding: '3px 8px', 
          borderRadius: '12px', 
          fontWeight: 'bold',
          background: badgeBg,
          color: badgeColor
        }}>
          {badgeText}
        </span>
      </div>

      <p style={{ margin: '6px 0', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#d1d5db' }}>
        <MapPin size={16} color="#2dd4bf" /> <strong style={{ color: '#ffffff' }}>District:</strong> {clinic.district}
      </p>
      
      <p style={{ margin: '6px 0', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#d1d5db' }}>
        <Phone size={16} color="#38bdf8" /> <strong style={{ color: '#ffffff' }}>Phone:</strong> {clinic.phone || 'N/A'}
      </p>

      <p style={{ margin: '6px 0', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#d1d5db' }}>
        {isNhimaAccepted ? (
          <ShieldCheck size={16} color="#4ade80" />
        ) : (
          <ShieldAlert size={16} color="#f87171" />
        )}
        <strong style={{ color: '#ffffff' }}>NHIMA:</strong> {clinic.nhima_accepted || 'Unknown'}
      </p>

      <p style={{ margin: '6px 0', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#d1d5db' }}>
        <Clock size={16} color="#fbbf24" /> <strong style={{ color: '#ffffff' }}>Hours:</strong> {clinic.hours || '24/7'}
      </p>
    </div>
  );
}