import React, { useEffect, useState } from 'react';
import { Bot, KeyRound, AlertTriangle, ShieldCheck, Activity, ArrowUpRight } from 'lucide-react';
import { api } from '../api/client';
import { Link } from 'react-router-dom';

export const DashboardPage = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardMetrics();
  }, []);

  const fetchDashboardMetrics = async () => {
    try {
      const res = await api.get('/dashboard');
      setMetrics(res.data);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading Hub Dashboard Metrics...</div>;
  }

  if (!metrics) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--status-danger)' }}>Failed to load dashboard data.</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Security Governance Overview</h2>
        <p style={{ color: 'var(--text-muted)' }}>Real-time posture and credential health for all enterprise AI Agents</p>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Total Provisioned</span>
            <Bot size={20} style={{ color: 'var(--primary)' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{metrics.total_agents}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--status-active)', marginTop: '0.25rem' }}>{metrics.active_agents} Active / {metrics.suspended_agents} Suspended</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Average Security Score</span>
            <ShieldCheck size={20} style={{ color: 'var(--status-active)' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{metrics.average_security_score}<span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}> / 100</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Rule-based posture metric</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Expired Credentials</span>
            <KeyRound size={20} style={{ color: 'var(--status-danger)' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: metrics.expired_credentials > 0 ? '#fca5a5' : 'var(--text-main)' }}>{metrics.expired_credentials}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{metrics.credentials_near_expiry} expiring in &lt;7 days</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>Reviews Pending</span>
            <AlertTriangle size={20} style={{ color: 'var(--status-warning)' }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: metrics.reviews_pending > 0 ? '#fcd34d' : 'var(--text-main)' }}>{metrics.reviews_pending}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Stale 30+ day inactivity alerts</div>
        </div>
      </div>

      {/* Grid: Risk Distribution + Audit Feed */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '1.5rem' }}>
        {/* Risk Distribution Card */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.25rem' }}>Risk Level Breakdown</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {Object.entries(metrics.risk_distribution).map(([level, count]) => (
              <div key={level}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.35rem' }}>
                  <span className={`badge badge-risk-${level.toLowerCase()}`}>{level} Risk</span>
                  <span style={{ fontWeight: 600 }}>{count} agents</span>
                </div>
                <div style={{ width: '100%', background: 'rgba(255,255,255,0.06)', height: '6px', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${metrics.total_agents > 0 ? (count / metrics.total_agents) * 100 : 0}%`, 
                    height: '100%', 
                    background: level === 'Critical' ? 'var(--risk-critical)' : level === 'High' ? 'var(--risk-high)' : level === 'Medium' ? 'var(--risk-medium)' : 'var(--risk-low)'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Log Activity Feed */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={18} style={{ color: 'var(--primary)' }} />
              <span>Recent Activity Feed</span>
            </h3>
            <Link to="/audit" style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              View All <ArrowUpRight size={14} />
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '280px', overflowY: 'auto' }}>
            {metrics.recent_audit_activity.map((log) => (
              <div key={log.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0.8rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>{log.action}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>by {log.performed_by || 'system'}</div>
                </div>
                <span style={{ fontSize: '0.75rem', color: log.status === 'success' ? 'var(--status-active)' : 'var(--status-danger)', fontWeight: 500 }}>
                  {log.status_code}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
