import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { draftEmailsApi } from '../services/api';
import { Check, X, Trash2, Edit2, ChevronDown, ChevronUp, Building2, Mail, User } from 'lucide-react';

const statusStyles: Record<string, { bg: string; color: string; label: string }> = {
    draft: { bg: 'rgba(245,158,11,0.12)', color: 'var(--color-warning)', label: 'Draft' },
    approved: { bg: 'rgba(34,197,94,0.12)', color: 'var(--color-success)', label: 'Approved' },
    sent: { bg: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)', label: 'Sent' },
    rejected: { bg: 'rgba(239,68,68,0.12)', color: 'var(--color-danger)', label: 'Rejected' },
};

function DraftEmailCard({ draft, onUpdate, onDelete }: {
    draft: any;
    onUpdate: (id: string, data: any) => void;
    onDelete: (id: string) => void;
}) {
    const [expanded, setExpanded] = useState(false);
    const [editing, setEditing] = useState(false);
    const [subject, setSubject] = useState(draft.subject);
    const [body, setBody] = useState(draft.body);

    const style = statusStyles[draft.status] || statusStyles.draft;
    const isDraft = draft.status === 'draft';

    const handleSave = () => {
        onUpdate(draft.id, { subject, body });
        setEditing(false);
    };

    return (
        <div
            className="card"
            style={{
                padding: 0,
                overflow: 'hidden',
                borderColor: isDraft ? 'rgba(245,158,11,0.3)' : undefined,
            }}
        >
            {/* Header row */}
            <div style={{ padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {/* Expand toggle */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', flexShrink: 0 }}
                >
                    {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>

                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 2 }}>
                        {draft.subject}
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem', color: 'var(--color-text-muted)', flexWrap: 'wrap' }}>
                        {draft.company_name && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Building2 size={11} /> {draft.company_name}
                            </span>
                        )}
                        {draft.contact_name && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <User size={11} /> {draft.contact_name}
                            </span>
                        )}
                        {draft.contact_email && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Mail size={11} /> {draft.contact_email}
                            </span>
                        )}
                        <span style={{ color: 'var(--color-text-muted)', opacity: 0.7 }}>
                            {new Date(draft.created_at).toLocaleDateString()}
                        </span>
                    </div>
                </div>

                {/* Status badge */}
                <span className="badge" style={{ background: style.bg, color: style.color, flexShrink: 0 }}>
                    {style.label}
                </span>

                {/* Actions */}
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                    {isDraft && (
                        <>
                            <button
                                className="btn btn-ghost"
                                style={{ padding: '0.3rem 0.6rem', color: 'var(--color-success)' }}
                                title="Approve"
                                onClick={() => onUpdate(draft.id, { status: 'approved' })}
                            >
                                <Check size={15} />
                            </button>
                            <button
                                className="btn btn-ghost"
                                style={{ padding: '0.3rem 0.6rem' }}
                                title="Edit"
                                onClick={() => { setExpanded(true); setEditing(true); }}
                            >
                                <Edit2 size={15} />
                            </button>
                            <button
                                className="btn btn-ghost"
                                style={{ padding: '0.3rem 0.6rem', color: 'var(--color-danger)' }}
                                title="Reject"
                                onClick={() => onUpdate(draft.id, { status: 'rejected' })}
                            >
                                <X size={15} />
                            </button>
                        </>
                    )}
                    {draft.status === 'approved' && (
                        <button
                            className="btn btn-primary"
                            style={{ padding: '0.3rem 0.75rem', fontSize: '0.8rem' }}
                            onClick={() => onUpdate(draft.id, { status: 'sent' })}
                        >
                            Mark Sent
                        </button>
                    )}
                    <button
                        className="btn btn-ghost"
                        style={{ padding: '0.3rem 0.6rem', color: 'var(--color-danger)' }}
                        title="Delete"
                        onClick={() => { if (confirm('Delete this draft?')) onDelete(draft.id); }}
                    >
                        <Trash2 size={15} />
                    </button>
                </div>
            </div>

            {/* Expanded body */}
            {expanded && (
                <div style={{ borderTop: '1px solid var(--color-border)', padding: '1rem 1.25rem', background: 'rgba(15,15,19,0.4)' }}>
                    {editing ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <div>
                                <label style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: 4, display: 'block' }}>Subject</label>
                                <input
                                    className="input"
                                    value={subject}
                                    onChange={(e) => setSubject(e.target.value)}
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: 4, display: 'block' }}>Body</label>
                                <textarea
                                    className="input"
                                    rows={10}
                                    style={{ resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.6 }}
                                    value={body}
                                    onChange={(e) => setBody(e.target.value)}
                                />
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button className="btn btn-primary" onClick={handleSave}>Save Changes</button>
                                <button className="btn btn-ghost" onClick={() => { setEditing(false); setSubject(draft.subject); setBody(draft.body); }}>Cancel</button>
                            </div>
                        </div>
                    ) : (
                        <div>
                            {draft.ai_model && (
                                <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
                                    Generated by <span style={{ color: 'var(--color-primary)' }}>{draft.ai_model}</span>
                                </p>
                            )}
                            <pre style={{
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                fontSize: '0.875rem',
                                lineHeight: 1.7,
                                color: 'var(--color-text)',
                                fontFamily: 'inherit',
                                margin: 0,
                            }}>
                                {draft.body}
                            </pre>
                            {draft.ai_reasoning && (
                                <details style={{ marginTop: '1rem' }}>
                                    <summary style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
                                        AI Reasoning
                                    </summary>
                                    <pre style={{
                                        marginTop: '0.5rem',
                                        fontSize: '0.8rem',
                                        color: 'var(--color-text-muted)',
                                        whiteSpace: 'pre-wrap',
                                        fontFamily: 'inherit',
                                    }}>
                                        {draft.ai_reasoning}
                                    </pre>
                                </details>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function DraftEmails() {
    const queryClient = useQueryClient();
    const [statusFilter, setStatusFilter] = useState('draft');

    const { data, isLoading } = useQuery({
        queryKey: ['draft-emails', statusFilter],
        queryFn: () => draftEmailsApi.list({ status: statusFilter || undefined }),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: any }) => draftEmailsApi.update(id, data),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['draft-emails'] }),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => draftEmailsApi.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['draft-emails'] }),
    });

    const drafts = data?.data?.items || [];

    return (
        <div className="animate-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Draft Emails</h1>
                    <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                        AI-generated outreach emails from Clay/n8n — review, edit, approve and mark as sent
                    </p>
                </div>

                {/* Status filter */}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {['draft', 'approved', 'sent', 'rejected', ''].map((s) => (
                        <button
                            key={s}
                            onClick={() => setStatusFilter(s)}
                            className="btn btn-ghost"
                            style={{
                                fontSize: '0.8rem',
                                padding: '0.3rem 0.75rem',
                                background: statusFilter === s ? 'rgba(99,102,241,0.15)' : undefined,
                                color: statusFilter === s ? 'var(--color-primary)' : 'var(--color-text-muted)',
                            }}
                        >
                            {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* List */}
            {isLoading ? (
                <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>
            ) : drafts.length === 0 ? (
                <div
                    className="card text-center"
                    style={{ padding: '3rem 1.5rem', color: 'var(--color-text-muted)', borderStyle: 'dashed' }}
                >
                    <Mail size={40} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
                    <p style={{ fontSize: '0.875rem' }}>
                        No {statusFilter || ''} draft emails found. Drafts appear here when Clay/n8n sends leads with AI-generated emails.
                    </p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {drafts.map((draft: any) => (
                        <DraftEmailCard
                            key={draft.id}
                            draft={draft}
                            onUpdate={(id, data) => updateMutation.mutate({ id, data })}
                            onDelete={(id) => deleteMutation.mutate(id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
