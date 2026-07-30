import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Shield, LayoutDashboard, Bot, PlusCircle, History, LogOut, UserCheck } from 'lucide-react';
import { api } from '../api/client';

export const Sidebar = () => {
  const navigate = useNavigate();
  const [userAdmin, setUserAdmin] = useState(null);

  useEffect(() => {
    fetchCurrentAdmin();
  }, []);

  const fetchCurrentAdmin = async () => {
    try {
      const res = await api.get('/auth/me');
      setUserAdmin(res.data);
    } catch (err) {
      console.error('Failed to fetch admin profile', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  const isAuditor = userAdmin?.role === 'auditor';

  return (
    <aside className="sidebar">
      <div className="brand-header">
        <div className="brand-logo">
          <Shield size={20} />
        </div>
        <div>
          <h1 className="brand-title">Agent Identity Hub</h1>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Enterprise IAM for AI</span>
        </div>
      </div>

      {userAdmin && (
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.75rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <UserCheck size={18} style={{ color: 'var(--accent-cyan)' }} />
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#fff', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{userAdmin.email}</div>
            <span className={`badge ${userAdmin.role === 'superadmin' ? 'badge-risk-critical' : userAdmin.role === 'admin' ? 'badge-active' : 'badge-suspended'}`} style={{ fontSize: '0.65rem', marginTop: '0.15rem' }}>
              {userAdmin.role}
            </span>
          </div>
        </div>
      )}

      <nav className="nav-menu">
        <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/agents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Bot size={18} />
          <span>Agent Directory</span>
        </NavLink>

        {!isAuditor && (
          <NavLink to="/agents/register" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <PlusCircle size={18} />
            <span>Register Agent</span>
          </NavLink>
        )}

        <NavLink to="/audit" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <History size={18} />
          <span>Audit Logs</span>
        </NavLink>
      </nav>

      <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
        <button onClick={handleLogout} className="nav-item" style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer' }}>
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
