import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dealsApi, stagesApi, contactsApi } from '../services/api';
import { Plus, DollarSign } from 'lucide-react';

export default function Deals() {
    const queryClient = useQueryClient();
    const [showCreate, setShowCreate] = useState(false);
    const [form, setForm] = useState({ title: '', value: 0, stage_id: '', contact_id: '' });

    const { data: stagesRes } = useQuery({ queryKey: ['stages'], queryFn: () => stagesApi.list() });
    const { data: dealsRes } = useQuery({ queryKey: ['deals'], queryFn: () => dealsApi.list({ per_page: 100 }) });
    const { data: contactsRes } = useQuery({ queryKey: ['contacts-select'], queryFn: () => contactsApi.list({ per_page: 100 }) });

    const stages = stagesRes?.data || [];
    const deals = dealsRes?.data?.items || [];
    const contacts = contactsRes?.data?.items || [];

    const createMutation = useMutation({
        mutationFn: (data: any) => dealsApi.create(data),
        onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['deals'] }); setShowCreate(false); },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => dealsApi.update(id, data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deals'] }),
    });

    const handleDragStart = (e: React.DragEvent, dealId: string) => {
        e.dataTransfer.setData('dealId', dealId);
    };

    const handleDrop = (e: React.DragEvent, stageId: string) => {
        e.preventDefault();
        const dealId = e.dataTransfer.getData('dealId');
        if (dealId) {
            updateMutation.mutate({ id: dealId, data: { stage_id: stageId } });
        }
    };

    return (
        <div className="animate-in">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Deal Pipeline</h1>
                    <p className="text-sm mt-2" style={{ color: 'var(--color-text-muted)' }}>
                        {deals.length} deals · ${deals.reduce((s: number, d: any) => s + d.value, 0).toLocaleString()} total value
                    </p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
                    <Plus size={16} /> New Deal
                </button>
            </div>

            {/* Create Modal */}
            {showCreate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.6)' }}>
                    <div className="card animate-in" style={{ width: 480, padding: '1.5rem' }}>
                        <h2 className="text-lg font-bold mb-4">New Deal</h2>
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                const data: any = { title: form.title, value: form.value || 0, stage_id: form.stage_id };
                                if (form.contact_id) data.contact_id = form.contact_id;
                                createMutation.mutate(data);
                            }}
                            className="flex flex-col gap-3"
                        >
                            <input className="input" placeholder="Deal title *" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                            <input className="input" type="number" placeholder="Value ($)" min={0} value={form.value || ''} onChange={(e) => setForm({ ...form, value: parseFloat(e.target.value) || 0 })} />
                            <select className="input" required value={form.stage_id} onChange={(e) => setForm({ ...form, stage_id: e.target.value })}>
                                <option value="">Select stage *</option>
                                {stages.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                            </select>
                            <select className="input" value={form.contact_id} onChange={(e) => setForm({ ...form, contact_id: e.target.value })}>
                                <option value="">Link to contact (optional)</option>
                                {contacts.map((c: any) => <option key={c.id} value={c.id}>{c.first_name} {c.last_name} — {c.email}</option>)}
                            </select>
                            <div className="flex gap-2 mt-2">
                                <button type="submit" className="btn btn-primary flex-1" disabled={createMutation.isPending}>
                                    {createMutation.isPending ? 'Creating...' : 'Create Deal'}
                                </button>
                                <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Kanban Board */}
            <div className="kanban-board">
                {stages.map((stage: any) => {
                    const stageDeals = deals.filter((d: any) => d.stage_id === stage.id);
                    const stageValue = stageDeals.reduce((s: number, d: any) => s + d.value, 0);

                    return (
                        <div
                            key={stage.id}
                            className="kanban-column"
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={(e) => handleDrop(e, stage.id)}
                        >
                            <div className="kanban-column-header">
                                <div className="flex items-center gap-2">
                                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: stage.color }} />
                                    <span>{stage.name}</span>
                                    <span
                                        className="badge ml-1"
                                        style={{ background: 'var(--color-bg)', color: 'var(--color-text-muted)', fontSize: '0.7rem' }}
                                    >
                                        {stageDeals.length}
                                    </span>
                                </div>
                                <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                                    ${stageValue.toLocaleString()}
                                </span>
                            </div>
                            <div className="kanban-cards">
                                {stageDeals.map((deal: any) => (
                                    <div
                                        key={deal.id}
                                        className="kanban-card"
                                        draggable
                                        onDragStart={(e) => handleDragStart(e, deal.id)}
                                    >
                                        <p className="text-sm font-medium mb-1">{deal.title}</p>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                                                <DollarSign size={12} />
                                                {deal.value.toLocaleString()}
                                            </div>
                                            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                                                {deal.probability}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
