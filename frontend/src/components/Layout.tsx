import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '../App';

export default function Layout() {
    const { user, logout } = useAuth();

    return (
        <div className="flex min-h-screen" style={{ background: 'var(--color-bg)' }}>
            <Sidebar />
            <div className="flex-1 flex flex-col" style={{ marginLeft: 'var(--sidebar-width)' }}>
                {/* Header */}
                <header
                    className="flex items-center justify-between px-6"
                    style={{
                        height: 'var(--header-height)',
                        borderBottom: '1px solid var(--color-border)',
                        background: 'var(--color-surface)',
                    }}
                >
                    <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text)' }}>
                        Renaissance AI CRM
                    </h2>
                    <div className="flex items-center gap-4">
                        <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                            {user?.first_name} {user?.last_name}
                        </span>
                        <span
                            className="badge"
                            style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--color-primary)' }}
                        >
                            {user?.role}
                        </span>
                        <button className="btn btn-ghost text-sm" onClick={logout}>
                            Sign Out
                        </button>
                    </div>
                </header>

                {/* Main Content */}
                <main className="flex-1 p-8 overflow-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
