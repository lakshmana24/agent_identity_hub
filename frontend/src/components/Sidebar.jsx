import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Shield, LayoutDashboard, Bot, PlusCircle, History, LogOut } from 'lucide-react';

export const Sidebar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

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

      <nav className="nav-menu">
        <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </NavLink>

        <NavLink to="/agents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Bot size={18} />
          <span>Agent Directory</span>
        </NavLink>

        <NavLink to="/agents/register" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <PlusCircle size={18} />
          <span>Register Agent</span>
        </NavLink>

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
