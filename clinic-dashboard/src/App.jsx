import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import ClinicCard from './ClinicCard';
import './App.css';

function App() {
  const [stats, setStats] = useState({ total_queries: 0, top_symptoms: [], busiest_district: null });
  const [clinics, setClinics] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const API_BASE = 'http://127.0.0.1:5000';

    Promise.all([
      fetch(`${API_BASE}/stats`).then(res => res.json()).catch(() => ({})),
      fetch(`${API_BASE}/clinics`).then(res => res.json()).catch(() => ([]))
    ])
    .then(([statsData, clinicsData]) => {
      setStats(statsData);
      setClinics(clinicsData);
      setLoading(false);
    });
  }, []);

  const filteredClinics = clinics.filter(clinic => {
    const matchesDistrict = selectedDistrict === 'All' || clinic.district.toLowerCase() === selectedDistrict.toLowerCase();
    const matchesSearch = clinic.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesDistrict && matchesSearch;
  });

  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: '50px', fontSize: '18px', color: '#0d9488' }}>Loading Bantu Health Dashboard...</div>;
  }

  return (
    <div style={{ padding: '30px', fontFamily: 'Arial, sans-serif', background: '#f9fafb', minHeight: '100vh' }}>
      <header style={{ marginBottom: '30px', borderBottom: '2px solid #e5e7eb', paddingBottom: '15px' }}>
        <h1 style={{ color: '#0d9488', margin: '0 0 5px 0' }}>Bantu Health AI — Admin Dashboard</h1>
        <p style={{ color: '#6b7280', margin: '0' }}>Real-time telemetry, symptom analytics, and Lusaka clinic directory.</p>
      </header>

      {/* Stats Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        <div style={{ background: '#ffffff', padding: '20px', borderRadius: '8px', borderLeft: '5px solid #16a34a', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#374151', fontSize: '14px' }}>TOTAL QUERIES</h3>
          <p style={{ fontSize: '28px', fontWeight: 'bold', margin: '0', color: '#111827' }}>{stats.total_queries || 0}</p>
        </div>
        <div style={{ background: '#ffffff', padding: '20px', borderRadius: '8px', borderLeft: '5px solid #0d9488', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#374151', fontSize: '14px' }}>BUSIEST DISTRICT</h3>
          <p style={{ fontSize: '22px', fontWeight: 'bold', margin: '0', color: '#111827' }}>
            {stats.busiest_district ? `${stats.busiest_district.district} (${stats.busiest_district.count})` : 'N/A'}
          </p>
        </div>
      </div>

      {/* Analytics Chart */}
      <div style={{ background: '#ffffff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', marginBottom: '30px' }}>
        <h3 style={{ marginTop: '0', color: '#1f2937' }}>Top Searched Symptoms</h3>
        <div style={{ width: '100%', height: 280, marginTop: '15px' }}>
          <ResponsiveContainer>
            <BarChart data={stats.top_symptoms || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="symptom" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Clinic Directory & Search Filters */}
      <div style={{ background: '#ffffff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', gap: '10px' }}>
          <h3 style={{ margin: '0', color: '#1f2937' }}>Lusaka Clinic Directory</h3>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <input 
              type="text" 
              placeholder="Search clinic name..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', outline: 'none' }}
            />
            <select 
              value={selectedDistrict} 
              onChange={(e) => setSelectedDistrict(e.target.value)}
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', outline: 'none', background: '#fff' }}
            >
              <option value="All">All Districts</option>
              <option value="Chilenje">Chilenje</option>
              <option value="Matero">Matero</option>
              <option value="Kanyama">Kanyama</option>
              <option value="Kabwata">Kabwata</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '15px' }}>
          {filteredClinics.length > 0 ? (
            filteredClinics.map((clinic, index) => (
              <ClinicCard key={index} clinic={clinic} />
            ))
          ) : (
            <p style={{ color: '#6b7280', gridColumn: '1 / -1', textAlign: 'center' }}>No clinics found matching your search.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;