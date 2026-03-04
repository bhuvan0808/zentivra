'use client';

import { useState, useEffect } from 'react';
import { getSources, toggleSource } from '@/lib/api';

const AGENT_LABELS = {
    competitor: { icon: '🏢', label: 'Competitor', color: 'var(--primary-400)' },
    model_provider: { icon: '🤖', label: 'Model Provider', color: 'var(--accent-500)' },
    research: { icon: '📚', label: 'Research', color: 'var(--info-500)' },
    hf_benchmark: { icon: '📊', label: 'HF Benchmark', color: 'var(--warning-500)' },
};

export default function SourcesPage() {
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [error, setError] = useState(null);

    useEffect(() => { loadSources(); }, []);

    async function loadSources() {
        try {
            const data = await getSources();
            setSources(data);
        } catch (e) {
            setError('Failed to load sources. Is the backend running?');
        }
        setLoading(false);
    }

    async function handleToggle(id, enabled) {
        try {
            await toggleSource(id, !enabled);
            setSources(prev => prev.map(s => s.id === id ? { ...s, enabled: !enabled } : s));
        } catch (e) {
            setError(e.message);
        }
    }

    const filtered = filter === 'all' ? sources : sources.filter(s => s.agent_type === filter);

    const agentCounts = sources.reduce((acc, s) => {
        acc[s.agent_type] = (acc[s.agent_type] || 0) + 1;
        return acc;
    }, {});

    if (loading) return <div className="loading"><div className="spinner" /> Loading sources...</div>;

    return (
        <>
            <div className="page-header">
                <div>
                    <h2>Sources</h2>
                    <p>{sources.length} configured sources across {Object.keys(agentCounts).length} agent types</p>
                </div>
            </div>

            {error && (
                <div style={{
                    padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)',
                    color: 'var(--error-500)', fontSize: '13px', marginBottom: '20px'
                }}>{error}</div>
            )}

            {/* Agent Type Filters */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <button className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setFilter('all')}>
                    All ({sources.length})
                </button>
                {Object.entries(AGENT_LABELS).map(([type, info]) => (
                    <button key={type}
                        className={`btn btn-sm ${filter === type ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setFilter(type)}>
                        {info.icon} {info.label} ({agentCounts[type] || 0})
                    </button>
                ))}
            </div>

            {/* Sources Grid */}
            <div className="card-grid card-grid-3">
                {filtered.map((source) => {
                    const agentInfo = AGENT_LABELS[source.agent_type] || { icon: '❓', label: 'Unknown', color: 'var(--text-muted)' };
                    return (
                        <div key={source.id} className="card" style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                <div>
                                    <div style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>
                                        {agentInfo.icon} {source.name}
                                    </div>
                                    <span className="badge badge-primary">{agentInfo.label}</span>
                                </div>
                                <button
                                    className={`btn btn-sm ${source.enabled ? 'btn-success' : 'btn-secondary'}`}
                                    onClick={() => handleToggle(source.id, source.enabled)}
                                    style={{ minWidth: '70px' }}
                                >
                                    {source.enabled ? 'Active' : 'Paused'}
                                </button>
                            </div>

                            <div style={{ fontSize: '12px', color: 'var(--text-muted)', wordBreak: 'break-all', marginBottom: '8px' }}>
                                <a href={source.url} target="_blank" rel="noopener" style={{ color: 'var(--primary-400)' }}>
                                    {source.url?.slice(0, 50)}{source.url?.length > 50 ? '...' : ''}
                                </a>
                            </div>

                            {source.feed_url && (
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                    RSS: {source.feed_url?.slice(0, 40)}...
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: 'var(--text-muted)', marginTop: '12px' }}>
                                <span>Rate: {source.rate_limit_rpm || 10} RPM</span>
                                {source.last_fetched_at && (
                                    <span>Last: {new Date(source.last_fetched_at).toLocaleDateString()}</span>
                                )}
                            </div>

                            {source.keywords && source.keywords.length > 0 && (
                                <div style={{ marginTop: '8px' }}>
                                    {source.keywords.slice(0, 4).map(kw => (
                                        <span key={kw} className="tag">{kw}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {filtered.length === 0 && (
                <div className="empty-state">
                    <div className="icon">🔗</div>
                    <h3>No sources found</h3>
                    <p>Add sources in the backend config or adjust your filter.</p>
                </div>
            )}
        </>
    );
}
