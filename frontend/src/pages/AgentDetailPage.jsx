import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Shield, KeyRound, RefreshCw, AlertOctagon, Trash2, ArrowLeft, CheckCircle, Copy, Clock, ShieldAlert, Cpu, Wrench, Globe } from 'lucide-react';
import { api } from '../api/client';

export const AgentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [agent, setAgent] = useState(null);
  const [governance, setGovernance] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [modalType, setModalType] = useState(null);
  const [genSecretResult, setGenSecretResult] = useState(null);
  const [expiresInDays, setExpiresInDays] = useState(90);
  const [explicitExpiresAt, setExplicitExpiresAt] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchAgentDetails();
    fetchUserRole();
  }, [id]);

  const fetchUserRole = async () => {
    try {
      const res = await api.get('/auth/me');
      setUserRole(res.data.role);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAgentDetails = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/agents/${id}`);
      setAgent(res.data);

      try {
        const govRes = await api.get(`/governance/security-score/${id}`);
        setGovernance(govRes.data);
      } catch (err) {
        console.error('Failed to fetch governance details', err);
      }
    } catch (err) {
      console.error('Failed to fetch agent', err);
    } finally {
      setLoading(false);
    }
  };

  const getExpiryPayload = () => {
    if (explicitExpiresAt) {
      return { expires_at: new Date(explicitExpiresAt).toISOString() };
    }
    return { expires_in_days: Number(expiresInDays) };
  };

  const handleGenerateCredential = async () => {
    setActionLoading(true);
    setActionError('');
    try {
      const payload = { agent_id: id, ...getExpiryPayload() };
      const res = await api.post('/credentials/generate', payload);
      setGenSecretResult(res.data.credential);
      fetchAgentDetails();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to generate credential.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRotateCredential = async () => {
    setActionLoading(true);
    setActionError('');
    try {
      const payload = { agent_id: id, ...getExpiryPayload() };
      const res = await api.post('/credentials/rotate', payload);
      setGenSecretResult(res.data.credential);
      fetchAgentDetails();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to rotate credential.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRenewCredential = async () => {
    setActionLoading(true);
    setActionError('');
    try {
      const payload = { agent_id: id, ...getExpiryPayload() };
      await api.post('/credentials/renew', payload);
      setModalType(null);
      fetchAgentDetails();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to renew credential.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevokeCredential = async () => {
    setActionLoading(true);
    setActionError('');
    try {
      await api.post('/credentials/revoke', {
        agent_id: id,
        reason: 'Revoked via governance dashboard interface'
      });
      setModalType(null);
      fetchAgentDetails();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to revoke credential.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteAgent = async () => {
    setActionLoading(true);
    try {
      await api.delete(`/agents/${id}`);
      navigate('/agents');
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Failed to delete agent.');
    } finally {
      setActionLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading Agent Identity Card...</div>;
  if (!agent) return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--status-danger)' }}>Agent not found.</div>;

  const isAuditor = userRole === 'auditor';

  return (
    <div>
      <Link to="/agents" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
        <ArrowLeft size={16} /> Back to Directory
      </Link>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>{agent.agent_name}</h2>
            <span className={`badge badge-${agent.lifecycle_status}`}>{agent.lifecycle_status}</span>
            <span className={`badge badge-risk-${agent.risk_level.toLowerCase()}`}>{agent.risk_level} Risk ({agent.risk_level_source})</span>
          </div>
          <div style={{ color: 'var(--text-dim)', fontSize: '0.875rem' }}>ID: {agent.agent_id} • Created {new Date(agent.created_at).toLocaleDateString()}</div>
        </div>

        {/* Action Controls (Disabled for Auditor) */}
        {!isAuditor && (
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            {agent.credential_status === 'not_issued' ? (
              <button className="btn btn-primary" onClick={() => { setGenSecretResult(null); setModalType('generate'); }}>
                <KeyRound size={16} /> Issue Credential
              </button>
            ) : (
              <>
                <button className="btn btn-secondary" onClick={() => { setGenSecretResult(null); setModalType('rotate'); }}>
                  <RefreshCw size={16} /> Rotate
                </button>
                <button className="btn btn-secondary" onClick={() => setModalType('renew')}>
                  <Clock size={16} /> Extend Expiry
                </button>
                <button className="btn btn-danger" onClick={() => setModalType('revoke')}>
                  <AlertOctagon size={16} /> Revoke
                </button>
              </>
            )}
            {userRole === 'superadmin' && (
              <button className="btn btn-danger" style={{ padding: '0.6rem' }} title="Deprovision Agent" onClick={() => setModalType('delete')}>
                <Trash2 size={16} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        {/* Identity Specifications Card */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>Identity Specifications</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem', fontSize: '0.9rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Purpose Description</span>
              <p style={{ marginTop: '0.25rem', color: '#fff' }}>{agent.purpose}</p>
            </div>

            {/* AI Architecture Row */}
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.6rem' }}>
                <Cpu size={16} /> AI Architecture Specs
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
                <div>
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Provider</span>
                  <div style={{ fontWeight: 600 }}>{agent.model_provider}</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Model</span>
                  <div style={{ fontWeight: 600 }}>{agent.model_name}</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Env</span>
                  <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{agent.deployment_environment}</div>
                </div>
              </div>
            </div>

            {/* Tools */}
            {agent.tools && agent.tools.length > 0 && (
              <div>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Wrench size={14} /> Capability Tools ({agent.tools.length})
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                  {agent.tools.map((t) => (
                    <span key={t} style={{ background: 'rgba(139, 92, 246, 0.15)', border: '1px solid rgba(139, 92, 246, 0.3)', color: '#c084fc', padding: '0.2rem 0.6rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Owner & Department */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textTransform: 'uppercase' }}>Department</span>
                <div style={{ fontWeight: 600, marginTop: '0.2rem' }}>{agent.department}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textTransform: 'uppercase' }}>Owner Email</span>
                <div style={{ fontWeight: 600, marginTop: '0.2rem' }}>{agent.owner}</div>
              </div>
            </div>

            {agent.agent_endpoint_url && (
              <div>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Globe size={14} /> Webhook Endpoint URL
                </span>
                <div style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--accent-cyan)', marginTop: '0.2rem' }}>{agent.agent_endpoint_url}</div>
              </div>
            )}

            <div>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', textTransform: 'uppercase' }}>Granted API Scopes</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                {agent.allowed_scopes.map((scope) => (
                  <span key={scope} style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.3)', color: '#93c5fd', padding: '0.2rem 0.6rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                    {scope}
                  </span>
                ))}
              </div>
            </div>

            {agent.ai_summary && (
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem', marginTop: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-purple)', textTransform: 'uppercase' }}>AI Identity Card Summary</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>{agent.ai_summary}</p>
              </div>
            )}
          </div>
        </div>

        {/* Security Governance Score */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>Security Posture & Compliance</h3>
          
          <div style={{ textAlign: 'center', margin: '1rem 0 1.5rem 0' }}>
            <div style={{ fontSize: '2.75rem', fontWeight: 800, color: agent.security_score >= 80 ? 'var(--status-active)' : agent.security_score >= 60 ? 'var(--status-warning)' : 'var(--status-danger)' }}>
              {agent.security_score}
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>Security Governance Score (100 Max)</div>
          </div>

          {governance && governance.breakdown.length > 0 ? (
            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>Active Penalty Deductions:</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {governance.breakdown.map((item, idx) => (
                  <div key={idx} style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: 'var(--radius-sm)', padding: '0.65rem', fontSize: '0.8rem' }}>
                    <div style={{ color: '#fca5a5', fontWeight: 600 }}>-{item.penalty} pts • {item.rule}</div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>{item.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: 'var(--radius-sm)', padding: '1rem', textAlign: 'center', color: '#6ee7b7', fontSize: '0.875rem' }}>
              <CheckCircle size={20} style={{ margin: '0 auto 0.35rem auto', display: 'block' }} />
              Optimal security health. No governance penalties detected.
            </div>
          )}
        </div>
      </div>

      {/* Action Modals */}
      {modalType && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem' }}>
              {modalType === 'generate' && 'Issue New API Credential'}
              {modalType === 'rotate' && 'Rotate Agent Credential'}
              {modalType === 'renew' && 'Extend Credential Expiry'}
              {modalType === 'revoke' && 'Revoke Agent Credential'}
              {modalType === 'delete' && 'Deprovision Agent'}
            </h3>

            {actionError && (
              <div style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5', padding: '0.65rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                {actionError}
              </div>
            )}

            {genSecretResult ? (
              <div>
                <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#fcd34d', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <ShieldAlert size={16} style={{ display: 'inline', marginRight: '0.35rem' }} />
                  Save this raw secret now! It will <strong>NEVER</strong> be displayed again.
                </div>
                <div style={{ position: 'relative', background: '#000', padding: '0.85rem', borderRadius: 'var(--radius-sm)', fontFamily: 'monospace', fontSize: '0.85rem', color: '#6ee7b7', wordBreak: 'break-all' }}>
                  {genSecretResult}
                  <button onClick={() => copyToClipboard(genSecretResult)} style={{ position: 'absolute', right: '0.5rem', top: '0.5rem', background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', padding: '0.3rem 0.5rem', borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontSize: '0.75rem' }}>
                    {copied ? 'Copied!' : <Copy size={14} />}
                  </button>
                </div>
                <button className="btn btn-secondary" style={{ width: '100%', marginTop: '1.25rem' }} onClick={() => setModalType(null)}>
                  Close & Done
                </button>
              </div>
            ) : (
              <div>
                {(modalType === 'generate' || modalType === 'rotate' || modalType === 'renew') && (
                  <div>
                    <div className="form-group">
                      <label className="form-label">Expiration Duration (Days)</label>
                      <input type="number" className="input-field" value={expiresInDays} onChange={(e) => setExpiresInDays(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">OR Testing Override Expiration Date (ISO 8601)</label>
                      <input type="datetime-local" className="input-field" value={explicitExpiresAt} onChange={(e) => setExplicitExpiresAt(e.target.value)} />
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Set a date in the past or near future for instant auto-revoke testing.</span>
                    </div>
                  </div>
                )}

                {modalType === 'revoke' && (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                    Revoking the credential immediately invalidates all API calls made by this agent.
                  </p>
                )}

                {modalType === 'delete' && (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                    Are you sure you want to soft-delete this agent? Its status will become <strong>deprovisioned</strong>.
                  </p>
                )}

                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                  <button className="btn btn-secondary" onClick={() => setModalType(null)}>Cancel</button>
                  {modalType === 'generate' && <button className="btn btn-primary" onClick={handleGenerateCredential} disabled={actionLoading}>Issue Credential</button>}
                  {modalType === 'rotate' && <button className="btn btn-primary" onClick={handleRotateCredential} disabled={actionLoading}>Rotate Secret</button>}
                  {modalType === 'renew' && <button className="btn btn-primary" onClick={handleRenewCredential} disabled={actionLoading}>Extend Expiry</button>}
                  {modalType === 'revoke' && <button className="btn btn-danger" onClick={handleRevokeCredential} disabled={actionLoading}>Revoke Now</button>}
                  {modalType === 'delete' && <button className="btn btn-danger" onClick={handleDeleteAgent} disabled={actionLoading}>Deprovision Agent</button>}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
