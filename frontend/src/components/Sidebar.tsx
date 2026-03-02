import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Users,
    Building2,
    Handshake,
    Activity,
    Settings,
    Brain,
    Mail,
} from 'lucide-react';

const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/contacts', icon: Users, label: 'Contacts' },
    { to: '/companies', icon: Building2, label: 'Companies' },
    { to: '/deals', icon: Handshake, label: 'Deals' },
    { to: '/activities', icon: Activity, label: 'Activities' },
    { to: '/draft-emails', icon: Mail, label: 'Draft Emails' },
    { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
    return (
        <aside
            className="fixed top-0 left-0 h-full flex flex-col"
            style={{
                width: 'var(--sidebar-width)',
                background: 'var(--color-surface)',
                borderRight: '1px solid var(--color-border)',
                zIndex: 50,
            }}
        >
            {/* Logo */}
            <div
                className="flex items-center gap-3 px-5"
                style={{ height: 'var(--header-height)', borderBottom: '1px solid var(--color-border)' }}
            >
                <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center pulse-glow"
                    style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)' }}
                >
                    <Brain size={18} color="white" />
                </div>
                <span className="font-bold text-base" style={{ color: 'var(--color-text)' }}>
                    Renaissance<span style={{ color: '#6366f1' }}>AI</span>
                </span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-4 px-3 flex flex-col gap-1">
                {navItems.map(({ to, icon: Icon, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                        style={({ isActive }) => ({
                            background: isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
                            color: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)',
                        })}
                    >
                        <Icon size={18} />
                        {label}
                    </NavLink>
                ))}
            </nav>

            {/* Footer */}
            <div
                className="px-5 py-4 text-xs"
                style={{ color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)' }}
            >
                Renaissance AI CRM v1.0
            </div>
        </aside>
    );
}
