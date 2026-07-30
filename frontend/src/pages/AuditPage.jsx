import React, { useEffect, useState } from 'react';
import { History, Search, Filter, Code, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { api } from '../api/client';

export const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [actionFilter, setActionFilter] = useState('');
  const [agentIdFilter, setAgentIdFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedMeta, setSelectedMeta] = useState(null);

  useEffect(() => {
    fetchAuditLogs();
  }, [page, actionFilter, agentIdFilter]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (actionFilter) params.action = actionFilter;
      if (agentIdFilter) params.agent_id = agentIdFilter;

      const res = await api.get('/audit', { params });
      setLogs(res.data.logs);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Immutable System Audit Trail</h2>
        <p style={{ color: 'var(--text-muted)' }}>Complete security audit record of all identity and credential operations</p>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            type="text"
            className="input-field"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Filter by Agent ID (agt_...)"
            value={agentIdFilter}
            onChange={(e) => { setAgentIdFilter(e.target.value); setPage(1); }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Filter size={16} style={{ color: 'var(--text-dim)' }} />
          <input
            type="text"
            className="input-field"
            style={{ width: '200px' }}
            placeholder="Filter by action name"
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          />
        </div>
      </div>

      {/* Table */}
      <div className="glass-card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading audit records...</div>
        ) : logs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>No audit logs found.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Action</th>
                <th>Method & Path</th>
                <th>Agent ID</th>
                <th>Performed By</th>
                <th>Status</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    {new Date(log.timestamp).toISOString().replace('T', ' ').substring(0, 19)}
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
                      {log.action}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span style={{ fontWeight: 600, color: '#fff', marginRight: '0.35rem' }}>{log.method}</span>
                    {log.path}
                  </td>
                  <td style={{ fontSize: '0.8rem', fontFamily: 'monospace' }}>
                    {log.agent_id || '—'}
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{log.performed_by || 'system'}</td>
                  <td>
                    <span style={{ color: log.status === 'success' ? 'var(--status-active)' : 'var(--status-danger)', fontWeight: 600, fontSize: '0.85rem' }}>
                      {log.status_code}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={() => setSelectedMeta(log.metadata_json)}>
                      <Code size={14} /> Meta
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        <span>Showing {logs.length} of {total} audit records</span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft size={16} /> Prev
          </button>
          <button className="btn btn-secondary" disabled={page * pageSize >= total} onClick={() => setPage(page + 1)}>
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* Metadata JSON Modal */}
      {selectedMeta && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: '600px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Audit Event Metadata</h3>
              <button style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={() => setSelectedMeta(null)}>
                <X size={20} />
              </button>
            </div>
            <pre style={{ background: '#000', padding: '1rem', borderRadius: 'var(--radius-sm)', color: '#6ee7b7', fontFamily: 'monospace', fontSize: '0.85rem', overflowX: 'auto' }}>
              {JSON.stringify(selectedMeta, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
