import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Bot, Sparkles, ArrowLeft, Check, AlertCircle } from 'lucide-react';
import { api } from '../api/client';

export const AgentRegisterPage = () => {
  const navigate = useNavigate();
  const [agentName, setAgentName] = useState('');
  const [purpose, setPurpose] = useState('');
  const [department, setDepartment] = useState('Engineering');
  const [owner, setOwner] = useState('dev@company.com');
  const [modelProvider, setModelProvider] = useState('OpenAI');
  const [modelName, setModelName] = useState('gpt-4o');
  const [toolsInput, setToolsInput] = useState('web_search, code_execution');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [environment, setEnvironment] = useState('production');
  
  const [allScopes, setAllScopes] = useState([]);
  const [selectedScopes, setSelectedScopes] = useState([]);
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAvailableScopes();
  }, []);

  const fetchAvailableScopes = async () => {
    try {
      const res = await api.get('/scopes');
      // Filter out deprecated scopes
      const activeScopes = res.data.filter((s) => !s.deprecated);
      setAllScopes(activeScopes);
      setSelectedScopes(['crm:read', 'tickets:read']);
    } catch (err) {
      console.error('Failed to fetch scopes:', err);
    }
  };

  const getToolsList = () => {
    return toolsInput.split(',').map((t) => t.trim()).filter(Boolean);
  };

  const handleAnalyzePurpose = async () => {
    if (!purpose.trim()) return;
    setAiLoading(true);
    setAiRecommendation(null);
    try {
      const res = await api.post('/governance/scope-recommendation', {
        purpose,
        model_provider: modelProvider,
        model_name: modelName,
        tools: getToolsList()
      });
      setAiRecommendation(res.data);
      if (res.data.recommended_scopes && res.data.recommended_scopes.length > 0) {
        setSelectedScopes(res.data.recommended_scopes);
      }
    } catch (err) {
      console.error('AI recommendation failed:', err);
    } finally {
      setAiLoading(false);
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
      const finalRisk = aiRecommendation ? aiRecommendation.risk_level : undefined;
      const res = await api.post('/agents', {
        agent_name: agentName,
        model_provider: modelProvider,
        model_name: modelName,
        tools: getToolsList(),
        agent_endpoint_url: endpointUrl || undefined,
        deployment_environment: environment,
        purpose,
        department,
        owner,
        requested_scopes: selectedScopes,
        risk_level: finalRisk,
        risk_level_source: aiRecommendation ? 'ai_recommended' : 'admin_override'
      });
      navigate(`/agents/${res.data.agent_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register agent.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '850px' }}>
      <Link to="/agents" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
        <ArrowLeft size={16} /> Back to Directory
      </Link>

      <div style={{ marginBottom: '1.75rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Register AI Agent Identity</h2>
        <p style={{ color: 'var(--text-muted)' }}>Provision a managed identity with model capabilities, scoped credentials, and AI risk analysis</p>
      </div>

      <div className="glass-card" style={{ padding: '2rem' }}>
        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Organizational Metadata */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">Agent Name</label>
              <input type="text" className="input-field" placeholder="e.g. SupportRefundBot" value={agentName} onChange={(e) => setAgentName(e.target.value)} required />
            </div>

            <div className="form-group">
              <label className="form-label">Department</label>
              <input type="text" className="input-field" placeholder="e.g. Finance, Support" value={department} onChange={(e) => setDepartment(e.target.value)} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Owner Email</label>
            <input type="email" className="input-field" placeholder="owner@company.com" value={owner} onChange={(e) => setOwner(e.target.value)} required />
          </div>

          {/* AI Capability Metadata */}
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-cyan)', margin: '1.5rem 0 1rem 0', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            AI Model & Capability Surface
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Model Provider</label>
              <input type="text" className="input-field" placeholder="OpenAI, Anthropic, Google..." value={modelProvider} onChange={(e) => setModelProvider(e.target.value)} required />
            </div>

            <div className="form-group">
              <label className="form-label">Model Name</label>
              <input type="text" className="input-field" placeholder="gpt-4o, claude-3-5-sonnet..." value={modelName} onChange={(e) => setModelName(e.target.value)} required />
            </div>

            <div className="form-group">
              <label className="form-label">Environment</label>
              <select className="select-field" value={environment} onChange={(e) => setEnvironment(e.target.value)}>
                <option value="production">Production</option>
                <option value="staging">Staging</option>
                <option value="sandbox">Sandbox</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Capability Tools (Comma Separated)</label>
            <input type="text" className="input-field" placeholder="web_search, code_execution, send_email, payment_gateway..." value={toolsInput} onChange={(e) => setToolsInput(e.target.value)} />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>High-privilege tools (code_execution, send_email) raise the AI risk profile.</span>
          </div>

          <div className="form-group">
            <label className="form-label">Agent Endpoint Webhook URL (Optional)</label>
            <input type="url" className="input-field" placeholder="https://api.company.com/agents/webhook" value={endpointUrl} onChange={(e) => setEndpointUrl(e.target.value)} />
          </div>

          {/* Business Purpose & AI Governance Analysis */}
          <div className="form-group" style={{ marginTop: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="form-label">Stated Business Purpose & Operational Scope</label>
              <button type="button" className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }} onClick={handleAnalyzePurpose} disabled={aiLoading || !purpose.trim()}>
                <Sparkles size={14} style={{ color: 'var(--accent-purple)' }} />
                {aiLoading ? 'Analyzing...' : 'AI Governance Analysis'}
              </button>
            </div>
            <textarea className="textarea-field" rows={3} placeholder="Describe the specific tasks this AI agent executes (e.g. Processes customer refunds via Stripe and updates tickets)..." value={purpose} onChange={(e) => setPurpose(e.target.value)} required />
          </div>

          {/* AI Recommendation Banner */}
          {aiRecommendation && (
            <div style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.3)', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Sparkles size={16} /> AI Governance Assessment Output
                </span>
                <span className={`badge badge-risk-${aiRecommendation.risk_level.toLowerCase()}`}>{aiRecommendation.risk_level} Risk</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{aiRecommendation.reasoning}</p>
            </div>
          )}

          {/* Scope Selector Chips */}
          <div className="form-group" style={{ marginBottom: '2rem' }}>
            <label className="form-label">API Scope Permissions (Live IAM Manifest)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', marginTop: '0.5rem' }}>
              {allScopes.map((scope) => {
                const isSelected = selectedScopes.includes(scope.scope_name);
                const isRejected = aiRecommendation?.rejected_scopes?.includes(scope.scope_name);

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
                      border: isSelected
                        ? '1px solid var(--primary)'
                        : isRejected
                        ? '1px dashed var(--status-danger)'
                        : '1px solid var(--border-color)',
                      background: isSelected
                        ? 'rgba(59, 130, 246, 0.2)'
                        : isRejected
                        ? 'rgba(239, 68, 68, 0.1)'
                        : 'rgba(15, 23, 42, 0.6)',
                      color: isSelected ? '#93c5fd' : isRejected ? '#fca5a5' : 'var(--text-muted)'
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
