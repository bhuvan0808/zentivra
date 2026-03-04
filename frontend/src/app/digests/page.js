'use client';

import { useState, useEffect } from 'react';
import { getDigests, getDigestPDFUrl } from '@/lib/api';

export default function DigestsPage() {
    const [digests, setDigests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => { loadDigests(); }, []);

    async function loadDigests() {
        try {
            const data = await getDigests(50);
            setDigests(data);
        } catch (e) {
            setError('Failed to load digests. Is the backend running?');
        }
        setLoading(false);
    }

    function formatDate(dt) {
        if (!dt) return '—';
        return new Date(dt).toLocaleDateString(undefined, {
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
        });
    }

    if (loading) return <div className="loading"><div className="spinner" /> Loading digests...</div>;

    return (
        <>
            <div className="page-header">
                <div>
                    <h2>Digest Archive</h2>
                    <p>{digests.length} digests generated</p>
                </div>
            </div>

            {error && (
                <div style={{
                    padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)',
                    color: 'var(--error-500)', fontSize: '13px', marginBottom: '20px'
                }}>{error}</div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {digests.map((d) => (
                    <div key={d.id} className="card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                                    <span style={{ fontSize: '28px' }}>📄</span>
                                    <div>
                                        <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-primary)' }}>
                                            AI Radar Digest — {formatDate(d.date)}
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                                            <span className="badge badge-primary">{d.total_findings || 0} findings</span>
                                            {d.email_sent && <span className="badge badge-success">Emailed</span>}
                                            {d.pdf_path && <span className="badge badge-muted">PDF</span>}
                                        </div>
                                    </div>
                                </div>

                                {d.executive_summary && (
                                    <div style={{
                                        padding: '12px 16px', background: 'var(--bg-surface-raised)',
                                        borderLeft: '3px solid var(--primary-500)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                                        marginTop: '12px', marginBottom: '8px'
                                    }}>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                                            Executive Summary
                                        </div>
                                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                                            {expanded === d.id
                                                ? d.executive_summary
                                                : d.executive_summary?.slice(0, 300) + (d.executive_summary?.length > 300 ? '...' : '')}
                                        </p>
                                        {d.executive_summary?.length > 300 && (
                                            <button
                                                className="btn btn-sm btn-secondary"
                                                style={{ marginTop: '8px' }}
                                                onClick={() => setExpanded(expanded === d.id ? null : d.id)}
                                            >
                                                {expanded === d.id ? 'Show Less' : 'Read More'}
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Section breakdown */}
                                {d.sections && Object.keys(d.sections).length > 0 && (
                                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
                                        {Object.entries(d.sections).map(([name, data]) => (
                                            <div key={name} style={{
                                                padding: '8px 12px', background: 'var(--bg-surface-raised)',
                                                borderRadius: 'var(--radius-sm)', fontSize: '12px'
                                            }}>
                                                <span style={{ color: 'var(--text-muted)' }}>{name}: </span>
                                                <span style={{ fontWeight: '600' }}>{data.count || 0}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginLeft: '16px' }}>
                                {d.pdf_path && (
                                    <a href={getDigestPDFUrl(d.id)} target="_blank" rel="noopener"
                                        className="btn btn-primary btn-sm">
                                        Download PDF
                                    </a>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {digests.length === 0 && (
                <div className="empty-state">
                    <div className="icon">📄</div>
                    <h3>No digests yet</h3>
                    <p>Digests are generated after each pipeline run. Trigger a run from the dashboard!</p>
                </div>
            )}
        </>
    );
}
