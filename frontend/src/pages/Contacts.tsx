import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { contactsApi } from '../services/api';
import { Plus, Search, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Contacts() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', source: '', status: 'new' });

    const { data, isLoading } = useQuery({
        queryKey: ['contacts', page, search],
        queryFn: () => contactsApi.list({ page, per_page: 20, search: search || undefined }),
    });

    const createMutation = useMutation({
        mutationFn: (data: any) => contactsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contacts'] });
            setShowCreate(false);
            setForm({ first_name: '', last_name: '', email: '', phone: '', source: '', status: 'new' });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => contactsApi.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contacts'] }),
    });

    const contacts = data?.data?.items || [];
    const total = data?.data?.total || 0;
    const totalPages = Math.ceil(total / 20);

    return (
        <div className="animate-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Contacts</h1>
                    <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>{total} total contacts</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
                    <Plus size={16} /> Add Contact
                </button>
            </div>

            {/* Search */}
            <div className="mb-4 relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
                <input
                    className="input"
                    style={{ paddingLeft: '2.25rem' }}
                    placeholder="Search contacts by name, email, or phone..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                />
            </div>

            {/* Create Modal */}
            {showCreate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.6)' }}>
                    <div className="card animate-in" style={{ width: 480, padding: '1.5rem' }}>
                        <h2 className="text-lg font-bold mb-4">New Contact</h2>
                        <form
                            onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }}
                            className="flex flex-col gap-3"
                        >
                            <div className="grid grid-cols-2 gap-3">
                                <input className="input" placeholder="First Name *" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                                <input className="input" placeholder="Last Name *" required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
                            </div>
                            <input className="input" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                            <input className="input" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                            <input className="input" placeholder="Source (e.g. website, referral, n8n)" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} />
                            <div className="flex gap-2 mt-2">
                                <button type="submit" className="btn btn-primary flex-1" disabled={createMutation.isPending}>
                                    {createMutation.isPending ? 'Creating...' : 'Create Contact'}
                                </button>
                                <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Table */}
            {isLoading ? (
                <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>
            ) : (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Source</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {contacts.map((c: any) => (
                                <tr
                                    key={c.id}
                                    className="cursor-pointer"
                                    onClick={() => navigate(`/contacts/${c.id}`)}
                                >
                                    <td className="font-medium">{c.first_name} {c.last_name}</td>
                                    <td style={{ color: 'var(--color-text-muted)' }}>{c.email || '—'}</td>
                                    <td style={{ color: 'var(--color-text-muted)' }}>{c.phone || '—'}</td>
                                    <td>
                                        {c.source && (
                                            <span className="badge" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}>
                                                {c.source}
                                            </span>
                                        )}
                                    </td>
                                    <td>
                                        <span
                                            className="badge"
                                            style={{
                                                background: c.status === 'new' ? 'rgba(34,197,94,0.12)' : 'rgba(168,85,247,0.12)',
                                                color: c.status === 'new' ? 'var(--color-success)' : 'var(--color-accent)',
                                            }}
                                        >
                                            {c.status}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--color-text-muted)', fontSize: '0.813rem' }}>
                                        {new Date(c.created_at).toLocaleDateString()}
                                    </td>
                                    <td>
                                        <button
                                            className="btn btn-ghost"
                                            style={{ padding: '0.25rem 0.5rem' }}
                                            onClick={(e) => { e.stopPropagation(); if (confirm('Delete this contact?')) deleteMutation.mutate(c.id); }}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {!contacts.length && (
                                <tr>
                                    <td colSpan={7} className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
                                        No contacts found. Add your first contact or connect n8n to start receiving leads.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-4">
                    <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                        <ChevronLeft size={16} /> Prev
                    </button>
                    <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                        Page {page} of {totalPages}
                    </span>
                    <button className="btn btn-ghost" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                        Next <ChevronRight size={16} />
                    </button>
                </div>
            )}
        </div>
    );
}
