import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { activitiesApi } from '../services/api';
import { ChevronLeft, ChevronRight, Filter } from 'lucide-react';

const activityIcons: Record<string, string> = {
    email: '📧', call: '📞', note: '📝', meeting: '🤝', system: '⚡',
};

export default function Activities() {
    const [page, setPage] = useState(1);
    const [typeFilter, setTypeFilter] = useState('');

    const { data, isLoading } = useQuery({
        queryKey: ['activities', page, typeFilter],
        queryFn: () => activitiesApi.list({ page, per_page: 25, type: typeFilter || undefined }),
    });

    const activities = data?.data?.items || [];
    const total = data?.data?.total || 0;
    const totalPages = Math.ceil(total / 25);

    return (
        <div className="animate-in">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Activities</h1>
                    <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>{total} total activities</p>
                </div>
                <div className="flex items-center gap-2">
                    <Filter size={14} style={{ color: 'var(--color-text-muted)' }} />
                    <select className="input" style={{ width: 'auto' }} value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}>
                        <option value="">All Types</option>
                        <option value="email">Email</option>
                        <option value="call">Call</option>
                        <option value="note">Note</option>
                        <option value="meeting">Meeting</option>
                        <option value="system">System</option>
                    </select>
                </div>
            </div>

            {isLoading ? (
                <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>
            ) : (
                <div className="flex flex-col gap-3">
                    {activities.map((act: any) => (
                        <div key={act.id} className="card flex gap-4" style={{ padding: '1rem' }}>
                            <span className="text-xl flex-shrink-0">{activityIcons[act.type] || '📌'}</span>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                    <h3 className="text-sm font-medium">{act.subject}</h3>
                                    <span className="text-xs flex-shrink-0 ml-2" style={{ color: 'var(--color-text-muted)' }}>
                                        {new Date(act.created_at).toLocaleString()}
                                    </span>
                                </div>
                                {act.body && (
                                    <p className="text-sm mb-2 whitespace-pre-wrap" style={{ color: 'var(--color-text-muted)' }}>
                                        {act.body.length > 200 ? act.body.slice(0, 200) + '...' : act.body}
                                    </p>
                                )}
                                <div className="flex items-center gap-2">
                                    <span className="badge" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}>
                                        {act.type}
                                    </span>
                                    <span className="badge" style={{ background: 'rgba(168,85,247,0.12)', color: 'var(--color-accent)' }}>
                                        {act.source}
                                    </span>
                                    {act.is_pinned && (
                                        <span className="badge" style={{ background: 'rgba(245,158,11,0.12)', color: 'var(--color-warning)' }}>
                                            📌 Pinned
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                    {!activities.length && (
                        <div className="card text-center py-12" style={{ color: 'var(--color-text-muted)' }}>
                            No activities found. Activities logged by n8n webhooks will show up here.
                        </div>
                    )}
                </div>
            )}

            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-4">
                    <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                        <ChevronLeft size={16} /> Prev
                    </button>
                    <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Page {page} of {totalPages}</span>
                    <button className="btn btn-ghost" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
                        Next <ChevronRight size={16} />
                    </button>
                </div>
            )}
        </div>
    );
}
