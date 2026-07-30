import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Plus, Search, Filter, ChevronLeft, ChevronRight, Users } from 'lucide-react';
import { api } from '../api/client';

export const AgentListPage = () => {
  const [agents, setAgents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [statusFilter, setStatusFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
  }, [page, statusFilter, teamFilter, riskFilter]);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (statusFilter) params.status = statusFilter;
      if (teamFilter) params.owning_team = teamFilter;
      if (riskFilter) params.risk_level = riskFilter;

      const res = await api.get('/agents', { params });
      setAgents(res.data.agents);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = agents.filter((a) =>
    search ? a.agent_name.toLowerCase().includes(search.toLowerCase()) || a.purpose.toLowerCase().includes(search.toLowerCase()) : true
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Agent Identity Directory</h2>
          <p style={{ color: 'var(--text-muted)' }}>Manage identities, granted tool scopes, and lifecycle states</p>
        </div>
        <Link to="/agents/register" className="btn btn-primary">
          <Plus size={18} />
          <span>Register New Agent</span>
        </Link>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-card" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            type="text"
            className="input-field"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Search agents by name or purpose..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Filter size={16} style={{ color: 'var(--text-dim)' }} />
          
          <select className="select-field" style={{ width: '130px' }} value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="deprovisioned">Deprovisioned</option>
          </select>

          <select className="select-field" style={{ width: '140px' }} value={teamFilter} onChange={(e) => { setTeamFilter(e.target.value); setPage(1); }}>
            <option value="">All Teams</option>
            <option value="Growth">Growth</option>
            <option value="Finance">Finance</option>
            <option value="DevOps">DevOps</option>
            <option value="Customer Support">Customer Support</option>
            <option value="Platform">Platform</option>
          </select>

          <select className="select-field" style={{ width: '130px' }} value={riskFilter} onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}>
            <option value="">All Risks</option>
            <option value="Low">Low Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="High">High Risk</option>
            <option value="Critical">Critical Risk</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading agents...</div>
        ) : filteredAgents.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>No agents found matching criteria.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Agent Name & ID</th>
                <th>Owning Team</th>
                <th>Department</th>
                <th>Risk Level</th>
                <th>Credential</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAgents.map((agent) => (
                <tr key={agent.agent_id}>
                  <td>
                    <div style={{ fontWeight: 600, color: '#fff' }}>{agent.agent_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{agent.agent_id}</div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600, color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      <Users size={14} /> {agent.owning_team}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{agent.department}</td>
                  <td>
                    <span className={`badge badge-risk-${agent.risk_level.toLowerCase()}`}>
                      {agent.risk_level}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem', color: agent.credential_status === 'active' ? 'var(--status-active)' : 'var(--text-dim)' }}>
                      {agent.credential_status}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${agent.lifecycle_status}`}>
                      {agent.lifecycle_status}
                    </span>
                  </td>
                  <td>
                    <Link to={`/agents/${agent.agent_id}`} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                      View Card
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        <span>Showing {filteredAgents.length} of {total} agents</span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft size={16} /> Prev
          </button>
          <button className="btn btn-secondary" disabled={page * pageSize >= total} onClick={() => setPage(page + 1)}>
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
