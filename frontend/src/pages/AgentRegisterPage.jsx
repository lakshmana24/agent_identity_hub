import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Bot, ArrowLeft, Check, AlertCircle } from 'lucide-react';
import { api } from '../api/client';

export const AgentRegisterPage = () => {
  const navigate = useNavigate();
  const [agentName, setAgentName] = useState('');
  const [purpose, setPurpose] = useState('');
  const [owningTeam, setOwningTeam] = useState('Growth');
  const [department, setDepartment] = useState('Engineering');
  const [owner, setOwner] = useState('dev@company.com');
  const [expiryDate, setExpiryDate] = useState('');
  
  const [allScopes, setAllScopes] = useState([]);
  const [selectedScopes, setSelectedScopes] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAvailableScopes();
  }, []);

  const fetchAvailableScopes = async () => {
    try {
      const res = await api.get('/scopes');
      const activeScopes = res.data.filter((s) => !s.deprecated);
      setAllScopes(activeScopes);
      setSelectedScopes(['crm:read', 'tickets:read']);
    } catch (err) {
      console.error('Failed to fetch scopes:', err);
    }
  };

  const toggleScope = (scopeName) => {
    if (selectedScopes.includes(scopeName)) {
      setSelectedScopes(selectedScopes.filter((s) => s !== scopeName));
    } else {
      setSelectedScopes([...selectedScopes, scopeName]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedScopes.length === 0) {
      setError('Please select at least one API scope.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const payload = {
        agent_name: agentName,
        purpose,
        owning_team: owningTeam,
        department,
        owner,
        requested_scopes: selectedScopes,
        expiry_date: expiryDate ? new Date(expiryDate).toISOString() : undefined
      };
      const res = await api.post('/agents', payload);
      navigate(`/agents/${res.data.agent_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register agent.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '780px' }}>
      <Link to="/agents" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
        <ArrowLeft size={16} /> Back to Directory
      </Link>

      <div style={{ marginBottom: '1.75rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Register AI Agent Identity</h2>
        <p style={{ color: 'var(--text-muted)' }}>Provision a managed identity with an owning team, scoped permissions, and identity lifetime</p>
      </div>

      <div className="glass-card" style={{ padding: '2rem' }}>
        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Agent Identification */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Agent Name</label>
              <input type="text" className="input-field" placeholder="e.g. RefundProcessorBot" value={agentName} onChange={(e) => setAgentName(e.target.value)} required />
            </div>

            <div className="form-group">
              <label className="form-label">Owning Team</label>
              <select className="select-field" value={owningTeam} onChange={(e) => setOwningTeam(e.target.value)}>
                <option value="Growth">Growth</option>
                <option value="Finance">Finance</option>
                <option value="DevOps">DevOps</option>
                <option value="Customer Support">Customer Support</option>
                <option value="Platform">Platform</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Department / Unit</label>
              <input type="text" className="input-field" placeholder="e.g. Engineering, Finance" value={department} onChange={(e) => setDepartment(e.target.value)} required />
            </div>

            <div className="form-group">
              <label className="form-label">Owner Email</label>
              <input type="email" className="input-field" placeholder="owner@company.com" value={owner} onChange={(e) => setOwner(e.target.value)} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Agent Identity Authorized Lifetime Expiry (Optional)</label>
            <input type="datetime-local" className="input-field" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Leave blank to default to 1-year identity lifetime. Credentials issued will be capped by this expiry date.</span>
          </div>

          {/* Purpose */}
          <div className="form-group" style={{ marginTop: '1.25rem' }}>
            <label className="form-label">Stated Purpose Description</label>
            <textarea className="textarea-field" rows={3} placeholder="Describe the operational purpose of this AI agent (e.g. Processes customer ticket refunds and updates CRM records)..." value={purpose} onChange={(e) => setPurpose(e.target.value)} required />
          </div>

          {/* Scope Selector Chips */}
          <div className="form-group" style={{ marginBottom: '2rem' }}>
            <label className="form-label">Approved Tool Scopes (Live IAM Manifest)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', marginTop: '0.5rem' }}>
              {allScopes.map((scope) => {
                const isSelected = selectedScopes.includes(scope.scope_name);
                return (
                  <button
                    key={scope.scope_name}
                    type="button"
                    onClick={() => toggleScope(scope.scope_name)}
                    title={scope.description}
                    style={{
                      padding: '0.5rem 0.85rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.85rem',
                      fontFamily: 'monospace',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                      background: isSelected ? 'rgba(59, 130, 246, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                      color: isSelected ? '#93c5fd' : 'var(--text-muted)'
                    }}
                  >
                    {isSelected && <Check size={14} />}
                    {scope.scope_name}
                  </button>
                );
              })}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/agents')}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Registering Agent...' : 'Submit & Register Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
