import { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contactsApi, activitiesApi, draftEmailsApi } from '../services/api';
import {
    ArrowLeft, Mail, Phone, Building2, Calendar, Tag,
    Send, X, Edit2, Trash2, ChevronDown, ChevronUp, CheckCircle, Clock,
    Sparkles, RotateCcw, Check,
} from 'lucide-react';
import api from '../services/api';

const activityIcons: Record<string, string> = {
    email: '📧', call: '📞', note: '📝', meeting: '🤝', system: '⚡',
};

const draftStatusCfg: Record<string, { label: string; bg: string; color: string }> = {
    draft:    { label: 'Draft',    bg: 'rgba(245,158,11,0.15)',  color: '#f59e0b' },
    approved: { label: 'Approved', bg: 'rgba(99,102,241,0.15)',  color: 'var(--color-primary)' },
    sent:     { label: 'Sent',     bg: 'rgba(34,197,94,0.15)',   color: 'var(--color-success)' },
    rejected: { label: 'Rejected', bg: 'rgba(239,68,68,0.1)',    color: 'var(--color-danger)' },
};

// Quick instruction suggestions
const QUICK_INSTRUCTIONS = [
    'Make it more concise',
    'Make it more casual and friendly',
    'Make it more formal',
    'Focus on ROI and business value',
    'Add a stronger call to action',
    'Personalize it more',
    'Shorten to 3 sentences',
];

// ---------------------------------------------------------------------------
// AI Edit Panel — shown inside the draft card when editing
// ---------------------------------------------------------------------------
function AiEditPanel({
    draftId,
    currentSubject,
    currentBody,
    onAccept,
    onClose,
}: {
    draftId: string;
    currentSubject: string;
    currentBody: string;
    onAccept: (subject: string, body: string) => void;
    onClose: () => void;
}) {
    const [instruction, setInstruction] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState<{ subject: string; body: string; model_used?: string } | null>(null);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const generate = async (instr: string) => {
        const text = instr || instruction;
        if (!text.trim()) return;
        setIsGenerating(true);
        setError(null);
        setResult(null);
        try {
            const res = await api.post(`/draft-emails/${draftId}/ai-rewrite`, {
                instruction: text.trim(),
            });
            setResult(res.data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || 'AI rewrite failed. Check your LMStudio connection in Settings.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div
            style={{
                marginTop: 12,
                borderRadius: 10,
                border: '1px solid rgba(168,85,247,0.3)',
                background: 'rgba(168,85,247,0.04)',
                overflow: 'hidden',
            }}
        >
            {/* Header */}
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '0.625rem 0.875rem',
                    borderBottom: '1px solid rgba(168,85,247,0.2)',
                    background: 'rgba(168,85,247,0.08)',
                }}
            >
                <Sparkles size={14} color="var(--color-accent)" />
                <span style={{ fontSize: '0.813rem', fontWeight: 600, color: 'var(--color-accent)' }}>
                    AI Email Edit
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginLeft: 4 }}>
                    via LMStudio
                </span>
                <button
                    onClick={onClose}
                    style={{
                        marginLeft: 'auto',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'var(--color-text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                    }}
                >
                    <X size={14} />
                </button>
            </div>

            <div style={{ padding: '0.875rem' }}>
                {/* Instruction input */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                    <input
                        ref={inputRef}
                        className="input"
                        style={{ flex: 1, fontSize: '0.875rem' }}
                        placeholder='e.g. "Make it more concise" or "Add a stronger CTA"'
                        value={instruction}
                        onChange={(e) => setInstruction(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') generate(instruction); }}
                        disabled={isGenerating}
                        autoFocus
                    />
                    <button
                        className="btn btn-primary"
                        style={{ gap: 6, minWidth: 80, fontSize: '0.813rem' }}
                        onClick={() => generate(instruction)}
                        disabled={isGenerating || !instruction.trim()}
                    >
                        {isGenerating ? (
                            <>
                                <span
                                    style={{
                                        width: 12,
                                        height: 12,
                                        border: '2px solid rgba(255,255,255,0.4)',
                                        borderTopColor: 'white',
                                        borderRadius: '50%',
                                        display: 'inline-block',
                                        animation: 'spin 0.7s linear infinite',
                                    }}
                                />
                                Writing…
                            </>
                        ) : (
                            <>
                                <Sparkles size={13} /> Rewrite
                            </>
                        )}
                    </button>
                </div>

                {/* Quick suggestion chips */}
                {!result && !isGenerating && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
                        {QUICK_INSTRUCTIONS.map((s) => (
                            <button
                                key={s}
                                onClick={() => { setInstruction(s); generate(s); }}
                                style={{
                                    padding: '3px 10px',
                                    borderRadius: 20,
                                    border: '1px solid rgba(168,85,247,0.3)',
                                    background: 'rgba(168,85,247,0.07)',
                                    color: 'var(--color-accent)',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer',
                                    transition: 'background 0.15s',
                                }}
                                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(168,85,247,0.15)')}
                                onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(168,85,247,0.07)')}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                )}

                {/* Error */}
                {error && (
                    <div
                        style={{
                            padding: '0.5rem 0.75rem',
                            borderRadius: 8,
                            background: 'rgba(239,68,68,0.1)',
                            color: 'var(--color-danger)',
                            fontSize: '0.813rem',
                            marginBottom: 10,
                        }}
                    >
                        {error}
                    </div>
                )}

                {/* AI Result */}
                {result && (
                    <div>
                        {/* Model badge */}
                        {result.model_used && (
                            <div style={{ marginBottom: 8 }}>
                                <span
                                    className="badge"
                                    style={{
                                        background: 'rgba(168,85,247,0.1)',
                                        color: 'var(--color-accent)',
                                        fontSize: '0.688rem',
                                    }}
                                >
                                    ✦ {result.model_used}
                                </span>
                            </div>
                        )}

                        {/* Subject */}
                        <div
                            style={{
                                padding: '0.5rem 0.75rem',
                                borderRadius: 8,
                                background: 'var(--color-bg)',
                                border: '1px solid var(--color-border)',
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                marginBottom: 8,
                            }}
                        >
                            <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', display: 'block', marginBottom: 2 }}>
                                Subject
                            </span>
                            {result.subject}
                        </div>

                        {/* Body */}
                        <div
                            style={{
                                padding: '0.75rem',
                                borderRadius: 8,
                                background: 'var(--color-bg)',
                                border: '1px solid var(--color-border)',
                                fontSize: '0.875rem',
                                lineHeight: 1.7,
                                whiteSpace: 'pre-wrap',
                                maxHeight: 320,
                                overflowY: 'auto',
                                marginBottom: 10,
                            }}
                        >
                            {result.body}
                        </div>

                        {/* Action buttons */}
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button
                                className="btn btn-primary"
                                style={{ gap: 6, fontSize: '0.813rem' }}
                                onClick={() => onAccept(result.subject, result.body)}
                            >
                                <Check size={13} /> Use this version
                            </button>
                            <button
                                className="btn btn-ghost"
                                style={{ gap: 6, fontSize: '0.813rem' }}
                                onClick={() => { setResult(null); inputRef.current?.focus(); }}
                            >
                                <RotateCcw size={13} /> Try again
                            </button>
                            <button
                                className="btn btn-ghost"
                                style={{ gap: 6, fontSize: '0.813rem', color: 'var(--color-text-muted)' }}
                                onClick={onClose}
                            >
                                <X size={13} /> Discard
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Draft email card
// ---------------------------------------------------------------------------
function DraftEmailCard({ draft, onUpdate, onSend, onDelete }: {
    draft: any;
    onUpdate: (id: string, data: any) => void;
    onSend: (id: string) => Promise<any>;
    onDelete: (id: string) => void;
}) {
    const [expanded, setExpanded] = useState(true);
    const [editing, setEditing] = useState(false);
    const [showReasoning, setShowReasoning] = useState(false);
    const [showAiPanel, setShowAiPanel] = useState(false);
    const [editSubject, setEditSubject] = useState(draft.subject);
    const [editBody, setEditBody] = useState(draft.body);
    const [sending, setSending] = useState(false);
    const [sendResult, setSendResult] = useState<string | null>(null);

    const cfg = draftStatusCfg[draft.status] || draftStatusCfg.draft;
    const isDraft = draft.status === 'draft';
    const isApproved = draft.status === 'approved';

    const handleSend = async () => {
        setSending(true);
        setSendResult(null);
        try {
            const res = await onSend(draft.id);
            setSendResult(res?.message || 'Approved and sent to n8n.');
        } catch {
            setSendResult('Error — check console.');
        } finally {
            setSending(false);
        }
    };

    const handleAiAccept = (subject: string, body: string) => {
        setEditSubject(subject);
        setEditBody(body);
        setShowAiPanel(false);
        setEditing(true); // Drop into edit mode so they can review before saving
    };

    return (
        <div
            style={{
                borderRadius: 12,
                border: `1px solid ${isDraft ? 'rgba(245,158,11,0.4)' : 'var(--color-border)'}`,
                background: isDraft ? 'rgba(245,158,11,0.04)' : 'var(--color-surface)',
                overflow: 'hidden',
                marginBottom: 12,
            }}
        >
            {/* Header */}
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '0.875rem 1rem',
                    cursor: 'pointer',
                    borderBottom: expanded ? '1px solid var(--color-border)' : 'none',
                }}
                onClick={() => setExpanded(!expanded)}
            >
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span
                            className="badge"
                            style={{ background: cfg.bg, color: cfg.color, fontWeight: 700, fontSize: '0.688rem' }}
                        >
                            {cfg.label.toUpperCase()}
                        </span>
                        {draft.ai_model && (
                            <span className="badge" style={{ background: 'rgba(168,85,247,0.1)', color: 'var(--color-accent)', fontSize: '0.688rem' }}>
                                AI · {draft.ai_model.split('-')[0]}
                            </span>
                        )}
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                            {new Date(draft.created_at).toLocaleString()}
                        </span>
                    </div>
                    <p style={{ fontWeight: 600, fontSize: '0.938rem', marginTop: 4 }}>{editing ? editSubject : draft.subject}</p>
                    {draft.contact_email && (
                        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                            → {draft.contact_email}
                        </p>
                    )}
                </div>
                <div style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>
                    {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
            </div>

            {expanded && (
                <div style={{ padding: '1rem' }}>
                    {editing ? (
                        /* Edit mode */
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            <input
                                className="input"
                                value={editSubject}
                                onChange={(e) => setEditSubject(e.target.value)}
                                placeholder="Subject"
                                style={{ fontWeight: 600 }}
                                onClick={(e) => e.stopPropagation()}
                            />
                            <textarea
                                className="input"
                                value={editBody}
                                onChange={(e) => setEditBody(e.target.value)}
                                rows={10}
                                style={{ fontFamily: 'inherit', fontSize: '0.875rem', resize: 'vertical', whiteSpace: 'pre-wrap' }}
                                onClick={(e) => e.stopPropagation()}
                            />

                            {/* AI edit panel (inline) */}
                            {showAiPanel ? (
                                <AiEditPanel
                                    draftId={draft.id}
                                    currentSubject={editSubject}
                                    currentBody={editBody}
                                    onAccept={handleAiAccept}
                                    onClose={() => setShowAiPanel(false)}
                                />
                            ) : (
                                <button
                                    className="btn btn-ghost"
                                    style={{
                                        gap: 6,
                                        fontSize: '0.813rem',
                                        color: 'var(--color-accent)',
                                        border: '1px solid rgba(168,85,247,0.3)',
                                        alignSelf: 'flex-start',
                                    }}
                                    onClick={(e) => { e.stopPropagation(); setShowAiPanel(true); }}
                                >
                                    <Sparkles size={13} /> AI Edit with LMStudio
                                </button>
                            )}

                            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                                <button
                                    className="btn btn-primary"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onUpdate(draft.id, { subject: editSubject, body: editBody });
                                        setEditing(false);
                                        setShowAiPanel(false);
                                    }}
                                >
                                    Save
                                </button>
                                <button className="btn btn-ghost" onClick={(e) => { e.stopPropagation(); setEditing(false); setShowAiPanel(false); setEditSubject(draft.subject); setEditBody(draft.body); }}>
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        /* Read mode */
                        <>
                            <div
                                style={{
                                    fontFamily: 'inherit',
                                    fontSize: '0.875rem',
                                    lineHeight: 1.7,
                                    color: 'var(--color-text)',
                                    whiteSpace: 'pre-wrap',
                                    padding: '0.75rem',
                                    borderRadius: 8,
                                    background: 'var(--color-bg)',
                                    marginBottom: 12,
                                }}
                            >
                                {draft.body}
                            </div>

                            {/* Action buttons */}
                            {isDraft && (
                                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                                    <button
                                        className="btn btn-primary"
                                        style={{ gap: 6 }}
                                        onClick={(e) => { e.stopPropagation(); handleSend(); }}
                                        disabled={sending}
                                    >
                                        <Send size={14} />
                                        {sending ? 'Sending…' : 'Approve & Send'}
                                    </button>
                                    <button className="btn btn-ghost" style={{ gap: 6 }} onClick={(e) => { e.stopPropagation(); setEditing(true); }}>
                                        <Edit2 size={14} /> Edit
                                    </button>
                                    <button
                                        className="btn btn-ghost"
                                        style={{ gap: 6, color: 'var(--color-accent)', border: '1px solid rgba(168,85,247,0.3)' }}
                                        onClick={(e) => { e.stopPropagation(); setEditing(true); setShowAiPanel(true); }}
                                    >
                                        <Sparkles size={14} /> AI Edit
                                    </button>
                                    <button
                                        className="btn btn-ghost"
                                        style={{ gap: 6, color: 'var(--color-danger)' }}
                                        onClick={(e) => { e.stopPropagation(); onUpdate(draft.id, { status: 'rejected' }); }}
                                    >
                                        <X size={14} /> Reject
                                    </button>
                                    <button
                                        className="btn btn-ghost"
                                        style={{ gap: 6 }}
                                        onClick={(e) => { e.stopPropagation(); if (confirm('Delete this draft?')) onDelete(draft.id); }}
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            )}

                            {isApproved && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                                    <CheckCircle size={16} color="var(--color-primary)" />
                                    <span style={{ fontSize: '0.813rem', color: 'var(--color-primary)' }}>
                                        Approved — awaiting send by n8n
                                    </span>
                                    <button className="btn btn-ghost" style={{ gap: 6, marginLeft: 'auto' }} onClick={(e) => { e.stopPropagation(); setEditing(true); }}>
                                        <Edit2 size={14} /> Edit
                                    </button>
                                </div>
                            )}

                            {draft.status === 'sent' && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                                    <CheckCircle size={16} color="var(--color-success)" />
                                    <span style={{ fontSize: '0.813rem', color: 'var(--color-success)' }}>Sent</span>
                                </div>
                            )}

                            {sendResult && (
                                <div style={{ padding: '0.5rem 0.75rem', borderRadius: 8, background: 'rgba(99,102,241,0.1)', color: 'var(--color-primary)', fontSize: '0.813rem', marginBottom: 10 }}>
                                    {sendResult}
                                </div>
                            )}

                            {/* AI Reasoning toggle */}
                            {draft.ai_reasoning && (
                                <div style={{ marginTop: 8 }}>
                                    <button
                                        className="btn btn-ghost"
                                        style={{ fontSize: '0.75rem', gap: 4, padding: '0.25rem 0.5rem' }}
                                        onClick={(e) => { e.stopPropagation(); setShowReasoning(!showReasoning); }}
                                    >
                                        {showReasoning ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                        AI Reasoning
                                    </button>
                                    {showReasoning && (
                                        <div
                                            style={{
                                                marginTop: 8,
                                                padding: '0.75rem',
                                                borderRadius: 8,
                                                background: 'rgba(168,85,247,0.06)',
                                                border: '1px solid rgba(168,85,247,0.15)',
                                                fontSize: '0.813rem',
                                                color: 'var(--color-text-muted)',
                                                whiteSpace: 'pre-wrap',
                                                lineHeight: 1.6,
                                            }}
                                        >
                                            {draft.ai_reasoning}
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Email activity card
// ---------------------------------------------------------------------------
function EmailActivityCard({ activity }: { activity: any }) {
    const [expanded, setExpanded] = useState(false);
    const meta = activity.metadata_ || activity.metadata || {};
    const direction = meta.direction || 'outbound';
    const isInbound = direction === 'inbound';
    const from = meta.from || '';
    const to = Array.isArray(meta.to) ? meta.to.join(', ') : (meta.to || '');

    return (
        <div style={{ borderRadius: 12, border: '1px solid var(--color-border)', background: 'var(--color-surface)', overflow: 'hidden', marginBottom: 10 }}>
            <div
                style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.75rem 1rem', cursor: 'pointer', borderBottom: expanded ? '1px solid var(--color-border)' : 'none' }}
                onClick={() => setExpanded(!expanded)}
            >
                <div
                    style={{
                        width: 28, height: 28, borderRadius: '50%',
                        background: isInbound ? 'rgba(34,197,94,0.1)' : 'rgba(99,102,241,0.1)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        flexShrink: 0, fontSize: '0.813rem', fontWeight: 700,
                        color: isInbound ? 'var(--color-success)' : 'var(--color-primary)',
                    }}
                    title={isInbound ? 'Inbound email' : 'Outbound email'}
                >
                    {isInbound ? '←' : '→'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{activity.subject}</span>
                        <span className="badge" style={{ background: isInbound ? 'rgba(34,197,94,0.1)' : 'rgba(99,102,241,0.1)', color: isInbound ? 'var(--color-success)' : 'var(--color-primary)', fontSize: '0.625rem' }}>
                            {isInbound ? 'INBOUND' : 'OUTBOUND'}
                        </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                        {isInbound ? `From: ${from}` : `To: ${to}`}
                        <span style={{ marginLeft: 12 }}>{new Date(activity.created_at).toLocaleString()}</span>
                    </div>
                </div>
                <div style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>
                    {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>
            </div>
            {expanded && activity.body && (
                <div style={{ padding: '0.875rem 1rem', fontSize: '0.875rem', lineHeight: 1.7, whiteSpace: 'pre-wrap', color: 'var(--color-text)' }}>
                    {activity.body}
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main ContactDetail page
// ---------------------------------------------------------------------------
export default function ContactDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<'timeline' | 'emails'>('timeline');

    const { data: contactRes } = useQuery({ queryKey: ['contact', id], queryFn: () => contactsApi.get(id!), enabled: !!id });
    const { data: timelineRes } = useQuery({ queryKey: ['timeline', id], queryFn: () => activitiesApi.timeline(id!), enabled: !!id });
    const { data: draftsRes } = useQuery({ queryKey: ['contact-drafts', id], queryFn: () => draftEmailsApi.list({ contact_id: id }), enabled: !!id });
    const { data: emailActivitiesRes } = useQuery({ queryKey: ['contact-email-activities', id], queryFn: () => activitiesApi.list({ contact_id: id, type: 'email', per_page: 100 }), enabled: !!id });

    const updateMutation = useMutation({
        mutationFn: ({ draftId, data }: { draftId: string; data: any }) => draftEmailsApi.update(draftId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contact-drafts', id] });
            queryClient.invalidateQueries({ queryKey: ['all-draft-emails'] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (draftId: string) => draftEmailsApi.delete(draftId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contact-drafts', id] });
            queryClient.invalidateQueries({ queryKey: ['all-draft-emails'] });
        },
    });

    const contact = contactRes?.data;
    const timeline = timelineRes?.data || [];
    const drafts = draftsRes?.data?.items || [];
    const emailActivities = emailActivitiesRes?.data?.items || [];

    const hasDraft = drafts.some((d: any) => d.status === 'draft');
    const emailCount = drafts.length + emailActivities.length;

    const handleUpdate = (draftId: string, data: any) => updateMutation.mutate({ draftId, data });
    const handleSend = async (draftId: string) => {
        const res = await draftEmailsApi.send(draftId);
        queryClient.invalidateQueries({ queryKey: ['contact-drafts', id] });
        queryClient.invalidateQueries({ queryKey: ['all-draft-emails'] });
        return res.data;
    };
    const handleDelete = (draftId: string) => deleteMutation.mutate(draftId);

    if (!contact) return <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading contact…</div>;

    return (
        <div className="animate-in max-w-5xl">
            <button className="btn btn-ghost mb-4" onClick={() => navigate('/contacts')}>
                <ArrowLeft size={16} /> Back to Contacts
            </button>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Contact Info Card */}
                <div className="card lg:col-span-1">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-bold" style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', color: 'white' }}>
                            {contact.first_name[0]}{contact.last_name?.[0] || ''}
                        </div>
                        <div>
                            <h2 className="text-lg font-bold">{contact.first_name} {contact.last_name}</h2>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                                <span className="badge" style={{ background: contact.status === 'new' ? 'rgba(34,197,94,0.12)' : 'rgba(168,85,247,0.12)', color: contact.status === 'new' ? 'var(--color-success)' : 'var(--color-accent)' }}>
                                    {contact.status}
                                </span>
                                {hasDraft && (
                                    <span className="badge" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b', fontWeight: 700 }} title="Draft email awaiting review">
                                        ✉ Draft
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-3 text-sm">
                        {contact.email && <div className="flex items-center gap-2"><Mail size={14} style={{ color: 'var(--color-text-muted)' }} /><a href={`mailto:${contact.email}`} style={{ color: 'var(--color-primary)' }}>{contact.email}</a></div>}
                        {contact.phone && <div className="flex items-center gap-2"><Phone size={14} style={{ color: 'var(--color-text-muted)' }} /><span>{contact.phone}</span></div>}
                        {contact.title && <div className="flex items-center gap-2"><Building2 size={14} style={{ color: 'var(--color-text-muted)' }} /><span>{contact.title}</span></div>}
                        {contact.source && <div className="flex items-center gap-2"><Tag size={14} style={{ color: 'var(--color-text-muted)' }} /><span>Source: {contact.source}</span></div>}
                        <div className="flex items-center gap-2"><Calendar size={14} style={{ color: 'var(--color-text-muted)' }} /><span style={{ color: 'var(--color-text-muted)' }}>Created {new Date(contact.created_at).toLocaleDateString()}</span></div>
                    </div>

                    {contact.tags?.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-1">
                            {contact.tags.map((tag: string) => (
                                <span key={tag} className="badge" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}>{tag}</span>
                            ))}
                        </div>
                    )}
                    {Object.keys(contact.custom_fields || {}).length > 0 && (
                        <div className="mt-4">
                            <h4 className="text-xs font-semibold uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>Custom Fields</h4>
                            {Object.entries(contact.custom_fields).map(([key, value]) => (
                                <div key={key} className="flex justify-between text-sm py-1">
                                    <span style={{ color: 'var(--color-text-muted)' }}>{key}</span><span>{String(value)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                    {contact.notes && (
                        <div className="mt-4">
                            <h4 className="text-xs font-semibold uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>Notes</h4>
                            <p className="text-sm whitespace-pre-wrap" style={{ color: 'var(--color-text-muted)' }}>{contact.notes}</p>
                        </div>
                    )}
                </div>

                {/* Right panel */}
                <div className="card lg:col-span-2" style={{ padding: 0 }}>
                    {/* Tab switcher */}
                    <div style={{ display: 'flex', gap: 4, padding: '0.75rem 1rem', borderBottom: '1px solid var(--color-border)' }}>
                        {[{ id: 'timeline' as const, label: 'Timeline' }, { id: 'emails' as const, label: 'Emails', count: emailCount }].map(({ id: tabId, label, count }) => (
                            <button
                                key={tabId}
                                onClick={() => setActiveTab(tabId)}
                                style={{
                                    padding: '0.375rem 0.875rem', borderRadius: 8, border: 'none', cursor: 'pointer',
                                    fontSize: '0.875rem', fontWeight: activeTab === tabId ? 600 : 400,
                                    background: activeTab === tabId ? 'var(--color-primary)' : 'transparent',
                                    color: activeTab === tabId ? 'white' : 'var(--color-text-muted)',
                                    display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.15s',
                                }}
                            >
                                {label}
                                {(count ?? 0) > 0 && (
                                    <span style={{
                                        padding: '1px 6px', borderRadius: 10, fontSize: '0.688rem', fontWeight: 700,
                                        background: activeTab === tabId ? 'rgba(255,255,255,0.25)' : hasDraft && tabId === 'emails' ? 'rgba(245,158,11,0.2)' : 'rgba(99,102,241,0.15)',
                                        color: activeTab === tabId ? 'white' : hasDraft && tabId === 'emails' ? '#f59e0b' : 'var(--color-primary)',
                                    }}>
                                        {count}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Timeline tab */}
                    {activeTab === 'timeline' && (
                        <div style={{ padding: '1rem' }}>
                            <div className="flex flex-col gap-3">
                                {timeline.map((act: any) => (
                                    <div key={act.id} className="flex gap-3 p-3 rounded-lg" style={{ background: 'var(--color-bg)' }}>
                                        <span className="text-lg flex-shrink-0">{activityIcons[act.type] || '📌'}</span>
                                        <div className="min-w-0 flex-1">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-medium">{act.subject}</p>
                                                <span className="text-xs flex-shrink-0 ml-2" style={{ color: 'var(--color-text-muted)' }}>{new Date(act.created_at).toLocaleString()}</span>
                                            </div>
                                            {act.body && <p className="text-sm mt-1 whitespace-pre-wrap" style={{ color: 'var(--color-text-muted)' }}>{act.body.length > 300 ? act.body.slice(0, 300) + '...' : act.body}</p>}
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className="badge text-xs" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}>{act.type}</span>
                                                {act.source !== 'manual' && <span className="badge text-xs" style={{ background: 'rgba(168,85,247,0.12)', color: 'var(--color-accent)' }}>via {act.source}</span>}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {!timeline.length && <p className="text-sm text-center py-8" style={{ color: 'var(--color-text-muted)' }}>No activities yet.</p>}
                            </div>
                        </div>
                    )}

                    {/* Emails tab */}
                    {activeTab === 'emails' && (
                        <div style={{ padding: '1rem' }}>
                            {drafts.length > 0 && (
                                <div style={{ marginBottom: 20 }}>
                                    <h4 style={{ fontSize: '0.688rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--color-text-muted)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Clock size={11} /> AI Drafted Emails
                                    </h4>
                                    {drafts.map((draft: any) => (
                                        <DraftEmailCard key={draft.id} draft={draft} onUpdate={handleUpdate} onSend={handleSend} onDelete={handleDelete} />
                                    ))}
                                </div>
                            )}
                            {emailActivities.length > 0 && (
                                <div>
                                    <h4 style={{ fontSize: '0.688rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--color-text-muted)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Mail size={11} /> Email History
                                    </h4>
                                    {emailActivities.map((act: any) => <EmailActivityCard key={act.id} activity={act} />)}
                                </div>
                            )}
                            {drafts.length === 0 && emailActivities.length === 0 && (
                                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted)' }}>
                                    <Mail size={36} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
                                    <p style={{ fontSize: '0.875rem' }}>No emails yet. Draft emails from Clay/n8n will appear here.</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
