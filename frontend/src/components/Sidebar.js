'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
    { href: '/', icon: '📊', label: 'Dashboard' },
    { href: '/sources', icon: '🔗', label: 'Sources' },
    { href: '/runs', icon: '🚀', label: 'Runs' },
    { href: '/findings', icon: '🔍', label: 'Findings' },
    { href: '/digests', icon: '📄', label: 'Digests' },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <h1>ZENTIVRA</h1>
                <span>Frontier AI Radar</span>
            </div>
            <nav className="sidebar-nav">
                {NAV_ITEMS.map(({ href, icon, label }) => (
                    <Link
                        key={href}
                        href={href}
                        className={`nav-item ${pathname === href ? 'active' : ''}`}
                    >
                        <span className="icon">{icon}</span>
                        {label}
                    </Link>
                ))}
            </nav>
            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: 'var(--success-500)',
                        boxShadow: '0 0 6px var(--success-500)'
                    }} />
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>System Online</span>
                </div>
            </div>
        </aside>
    );
}
