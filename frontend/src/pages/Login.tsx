import { useState } from 'react';
import { useAuth } from '../App';
import { authApi } from '../services/api';
import { Brain } from 'lucide-react';

export default function Login() {
    const { setUser } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [form, setForm] = useState({
        email: '', password: '', first_name: '', last_name: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            if (isRegister) {
                // Auto-generate tenant_slug from email domain
                const emailDomain = form.email.split('@')[1]?.split('.')[0] || 'default';
                const tenant_slug = emailDomain.toLowerCase().replace(/[^a-z0-9]/g, '-');
                await authApi.register({ ...form, tenant_slug });
            }
            const { data } = await authApi.login({ email: form.email, password: form.password });
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            const { data: user } = await authApi.me();
            setUser(user);
        } catch (err: any) {
            setError(err.response?.data?.detail || err.response?.data?.error || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            className="min-h-screen flex items-center justify-center p-4"
            style={{ background: 'var(--color-bg)' }}
        >
            <div className="card animate-in" style={{ maxWidth: 420, width: '100%', padding: '2rem' }}>
                {/* Logo */}
                <div className="flex items-center gap-3 mb-8">
                    <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center pulse-glow"
                        style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)' }}
                    >
                        <Brain size={22} color="white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
                            Renaissance<span style={{ color: '#6366f1' }}>AI</span> CRM
                        </h1>
                        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                            {isRegister ? 'Create your account' : 'Sign in to continue'}
                        </p>
                    </div>
                </div>

                {error && (
                    <div
                        className="mb-4 p-3 rounded-lg text-sm"
                        style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--color-danger)', border: '1px solid rgba(239,68,68,0.2)' }}
                    >
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                    {isRegister && (
                        <div className="grid grid-cols-2 gap-3">
                            <input
                                className="input"
                                placeholder="First Name"
                                value={form.first_name}
                                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                                required
                            />
                            <input
                                className="input"
                                placeholder="Last Name"
                                value={form.last_name}
                                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                                required
                            />
                        </div>
                    )}
                    <input
                        className="input"
                        type="email"
                        placeholder="Email"
                        value={form.email}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                        required
                    />
                    <input
                        className="input"
                        type="password"
                        placeholder="Password"
                        value={form.password}
                        onChange={(e) => setForm({ ...form, password: e.target.value })}
                        required
                        minLength={8}
                    />

                    <button
                        type="submit"
                        className="btn btn-primary w-full justify-center mt-2"
                        disabled={loading}
                        style={{ padding: '0.75rem' }}
                    >
                        {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
                    </button>
                </form>

                <p className="text-center mt-4 text-sm" style={{ color: 'var(--color-text-muted)' }}>
                    {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
                    <button
                        className="font-medium"
                        style={{ color: 'var(--color-primary)', background: 'none', border: 'none', cursor: 'pointer' }}
                        onClick={() => { setIsRegister(!isRegister); setError(''); }}
                    >
                        {isRegister ? 'Sign In' : 'Register'}
                    </button>
                </p>
            </div>
        </div>
    );
}
