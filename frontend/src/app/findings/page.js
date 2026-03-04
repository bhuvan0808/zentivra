'use client';

import { useState, useEffect } from 'react';
import { getFindings } from '@/lib/api';

const CATEGORIES = ['all', 'models', 'apis', 'pricing', 'benchmarks', 'research', 'safety', 'tooling', 'other'];

export default function FindingsPage() {
    const [findings, setFindings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [category, setCategory] = useState('all');
    const [search, setSearch] = useState('');
    const [expanded, setExpanded] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => { loadFindings(); }, [category]);

    async function loadFindings() {
        setLoading(true);
        try {
            const params = { limit: 50 };
            if (category !== 'all') params.category = category;
            if (search) params.search = search;
            const data = await getFindings(params);
            setFindings(data);
        } catch (e) {
            setError('Failed to load findings. Is the backend running?');
        }
        setLoading(false);
    }

    function handleSearch(e) {
        e.preventDefault();
        loadFindings();
    }

    function impactColor(score) {
        if (score >= 0.8) return 'var(--success-500)';
        if (score >= 0.6) return 'var(--primary-400)';
        if (score >= 0.4) return 'var(--warning-500)';
        return 'var(--text-muted)';
    }

    return (
        <>
            <div className="page-header">
                <div>
                    <h2>Findings Explorer</h2>
                    <p>{findings.length} findings discovered</p>
                </div>
            </div>

            {error && (
                <div style={{
                    padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)',
                    color: 'var(--error-500)', fontSize: '13px', marginBottom: '20px'
                }}>{error}</div>
            )}

            {/* Filters */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
                    <input
                        className="input"
                        placeholder="Search findings..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ width: '240px' }}
                    />
                    <button className="btn btn-secondary btn-sm" type="submit">Search</button>
                </form>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {CATEGORIES.map((cat) => (
                        <button key={cat}
                            className={`btn btn-sm ${category === cat ? 'btn-primary' : 'btn-secondary'}`}
                            onClick={() => setCategory(cat)}>
                            {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="loading"><div className="spinner" /> Loading findings...</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {findings.map((f) => (
                        <div key={f.id} className="card" style={{ cursor: 'pointer' }}
                            onClick={() => setExpanded(expanded === f.id ? null : f.id)}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
                                        {f.title}
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '8px' }}>
                                        <span className="badge badge-primary">{f.category}</span>
                                        {f.publisher && <span className="badge badge-muted">{f.publisher}</span>}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Impact:</span>
                                            <div className="impact-bar" style={{ width: '80px' }}>
                                                <div className="impact-bar-fill"
                                                    style={{ width: `${(f.impact_score || 0) * 100}%`, background: impactColor(f.impact_score) }} />
                                            </div>
                                            <span style={{ fontSize: '12px', fontWeight: '600', color: impactColor(f.impact_score) }}>
                                                {((f.impact_score || 0) * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                            Confidence: {((f.confidence || 0) * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    {f.summary_short && (
                                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                                            {f.summary_short}
                                        </p>
                                    )}
                                </div>
                                <span style={{ fontSize: '20px', color: 'var(--text-muted)', marginLeft: '12px' }}>
                                    {expanded === f.id ? '▲' : '▼'}
                                </span>
                            </div>

                            {expanded === f.id && (
                                <div style={{
                                    marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-default)'
                                }}>
                                    {f.summary_long && (
                                        <div style={{ marginBottom: '12px' }}>
                                            <h4 style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                                                Full Summary
                                            </h4>
                                            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                                                {f.summary_long}
                                            </p>
                                        </div>
                                    )}
                                    {f.why_it_matters && (
                                        <div style={{ marginBottom: '12px' }}>
                                            <h4 style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                                                Why It Matters
                                            </h4>
                                            <p style={{ fontSize: '13px', color: 'var(--primary-300)', lineHeight: '1.6', fontStyle: 'italic' }}>
                                                {f.why_it_matters}
                                            </p>
                                        </div>
                                    )}

                                    {/* Score Breakdown */}
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '12px' }}>
                                        {[
                                            { label: 'Relevance', score: f.relevance_score },
                                            { label: 'Novelty', score: f.novelty_score },
                                            { label: 'Credibility', score: f.credibility_score },
                                            { label: 'Actionability', score: f.actionability_score },
                                        ].map(({ label, score }) => (
                                            <div key={label} style={{
                                                padding: '10px', background: 'var(--bg-surface-raised)',
                                                borderRadius: 'var(--radius-sm)', textAlign: 'center'
                                            }}>
                                                <div style={{ fontSize: '18px', fontWeight: '700', color: impactColor(score) }}>
                                                    {((score || 0) * 100).toFixed(0)}%
                                                </div>
                                                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>{label}</div>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Tags & Entities */}
                                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                                        {f.tags && f.tags.length > 0 && (
                                            <div>
                                                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Tags: </span>
                                                {f.tags.map(t => <span key={t} className="tag">{t}</span>)}
                                            </div>
                                        )}
                                        {f.entities && Object.keys(f.entities).length > 0 && (
                                            <div>
                                                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Entities: </span>
                                                {Object.entries(f.entities).map(([type, vals]) =>
                                                    Array.isArray(vals) && vals.map(v => (
                                                        <span key={v} className="tag" style={{ background: 'rgba(102,126,234,0.15)' }}>{v}</span>
                                                    ))
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    {f.source_url && (
                                        <div style={{ marginTop: '8px' }}>
                                            <a href={f.source_url} target="_blank" rel="noopener"
                                                style={{ fontSize: '12px', color: 'var(--primary-400)' }}>
                                                View Source →
                                            </a>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {!loading && findings.length === 0 && (
                <div className="empty-state">
                    <div className="icon">🔍</div>
                    <h3>No findings yet</h3>
                    <p>Run the pipeline from the dashboard to discover AI developments.</p>
                </div>
            )}
        </>
    );
}
