'use client';

import { useState, useEffect } from 'react';
import { getHealth, getScheduler, getRuns, getFindings, getSources, triggerRun } from '@/lib/api';

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [scheduler, setScheduler] = useState(null);
  const [stats, setStats] = useState({ sources: 0, runs: 0, findings: 0 });
  const [recentFindings, setRecentFindings] = useState([]);
  const [recentRuns, setRecentRuns] = useState([]);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const [h, s, sources, runs, findings] = await Promise.all([
        getHealth().catch(() => null),
        getScheduler().catch(() => null),
        getSources().catch(() => []),
        getRuns(5).catch(() => []),
        getFindings({ limit: 8 }).catch(() => []),
      ]);
      setHealth(h);
      setScheduler(s);
      setStats({ sources: sources.length, runs: runs.length, findings: findings.length });
      setRecentRuns(runs.slice(0, 5));
      setRecentFindings(findings.slice(0, 8));
    } catch (e) {
      setError('Failed to connect to backend. Is the server running?');
    }
  }

  async function handleTriggerRun() {
    setTriggering(true);
    try {
      await triggerRun();
      setTimeout(() => loadDashboard(), 2000);
    } catch (e) {
      setError(e.message);
    }
    setTriggering(false);
  }

  const statusColor = health ? 'var(--success-500)' : 'var(--error-500)';
  const statusText = health ? 'Online' : 'Offline';

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>Frontier AI Radar — Real-time intelligence overview</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: statusColor, boxShadow: `0 0 8px ${statusColor}`
            }} />
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{statusText}</span>
          </div>
          <button className="btn btn-primary" onClick={handleTriggerRun} disabled={triggering}>
            {triggering ? '⏳ Running...' : '▶ Trigger Run'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)',
          color: 'var(--error-500)', fontSize: '13px', marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="card-grid card-grid-4" style={{ marginBottom: '24px' }}>
        <div className="stat-card">
          <div className="stat-icon">🔗</div>
          <div className="stat-value">{stats.sources}</div>
          <div className="stat-label">Active Sources</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🚀</div>
          <div className="stat-value">{stats.runs}</div>
          <div className="stat-label">Pipeline Runs</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔍</div>
          <div className="stat-value">{stats.findings}</div>
          <div className="stat-label">Findings</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏰</div>
          <div className="stat-value" style={{ fontSize: '20px' }}>
            {scheduler?.jobs?.[0]?.next_run
              ? new Date(scheduler.jobs[0].next_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              : '--:--'}
          </div>
          <div className="stat-label">Next Scheduled Run</div>
        </div>
      </div>

      {/* Two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Recent Runs */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '16px', color: 'var(--text-primary)' }}>
            Recent Runs
          </h3>
          {recentRuns.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '20px 0', textAlign: 'center' }}>
              No runs yet. Trigger your first run above!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentRuns.map((run) => (
                <div key={run.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 12px', background: 'var(--bg-surface-raised)',
                  borderRadius: 'var(--radius-sm)', fontSize: '13px'
                }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', fontFamily: 'monospace', fontSize: '11px' }}>
                      {run.id?.slice(0, 8)}
                    </span>
                    <span className={`badge badge-${run.status === 'completed' ? 'success' : run.status === 'running' ? 'primary' : run.status === 'failed' ? 'error' : 'muted'}`}
                      style={{ marginLeft: '8px' }}>
                      {run.status}
                    </span>
                  </div>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                    {run.total_findings || 0} findings
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Findings */}
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '16px', color: 'var(--text-primary)' }}>
            Latest Findings
          </h3>
          {recentFindings.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '20px 0', textAlign: 'center' }}>
              No findings yet. Run the pipeline to discover AI developments!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentFindings.map((f) => (
                <div key={f.id} style={{
                  padding: '10px 12px', background: 'var(--bg-surface-raised)',
                  borderRadius: 'var(--radius-sm)'
                }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>
                    {f.title?.slice(0, 60)}{f.title?.length > 60 ? '...' : ''}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className="badge badge-primary">{f.category}</span>
                    {f.impact_score > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <div className="impact-bar">
                          <div className="impact-bar-fill" style={{ width: `${(f.impact_score || 0) * 100}%` }} />
                        </div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {((f.impact_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* System Info */}
      {health && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '12px', color: 'var(--text-primary)' }}>
            System Configuration
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', fontSize: '13px' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>LLM Provider</div>
              <span className="badge badge-success">{health.llm_provider}</span>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>Email</div>
              <span className={`badge ${health.email_configured ? 'badge-success' : 'badge-warning'}`}>
                {health.email_configured ? 'Configured' : 'Not Configured'}
              </span>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>Environment</div>
              <span className="badge badge-muted">{health.environment}</span>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginBottom: '4px' }}>Database</div>
              <span className="badge badge-success">{health.database}</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
