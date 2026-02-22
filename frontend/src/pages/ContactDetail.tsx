import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { contactsApi, activitiesApi } from '../services/api';
import { ArrowLeft, Mail, Phone, Building2, Calendar, Tag } from 'lucide-react';

const activityIcons: Record<string, string> = {
    email: '📧', call: '📞', note: '📝', meeting: '🤝', system: '⚡',
};

export default function ContactDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { data: contactRes } = useQuery({
        queryKey: ['contact', id],
        queryFn: () => contactsApi.get(id!),
        enabled: !!id,
    });

    const { data: timelineRes } = useQuery({
        queryKey: ['timeline', id],
        queryFn: () => activitiesApi.timeline(id!),
        enabled: !!id,
    });

    const contact = contactRes?.data;
    const timeline = timelineRes?.data || [];

    if (!contact) {
        return (
            <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>
                Loading contact...
            </div>
        );
    }

    return (
        <div className="animate-in max-w-5xl">
            {/* Back button */}
            <button className="btn btn-ghost mb-4" onClick={() => navigate('/contacts')}>
                <ArrowLeft size={16} /> Back to Contacts
            </button>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Contact Info Card */}
                <div className="card lg:col-span-1">
                    <div className="flex items-center gap-3 mb-4">
                        <div
                            className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-bold"
                            style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', color: 'white' }}
                        >
                            {contact.first_name[0]}{contact.last_name?.[0] || ''}
                        </div>
                        <div>
                            <h2 className="text-lg font-bold">{contact.first_name} {contact.last_name}</h2>
                            <span
                                className="badge"
                                style={{
                                    background: contact.status === 'new' ? 'rgba(34,197,94,0.12)' : 'rgba(168,85,247,0.12)',
                                    color: contact.status === 'new' ? 'var(--color-success)' : 'var(--color-accent)',
                                }}
                            >
                                {contact.status}
                            </span>
                        </div>
                    </div>

                    <div className="flex flex-col gap-3 text-sm">
                        {contact.email && (
                            <div className="flex items-center gap-2">
                                <Mail size={14} style={{ color: 'var(--color-text-muted)' }} />
                                <a href={`mailto:${contact.email}`} style={{ color: 'var(--color-primary)' }}>{contact.email}</a>
                            </div>
                        )}
                        {contact.phone && (
                            <div className="flex items-center gap-2">
                                <Phone size={14} style={{ color: 'var(--color-text-muted)' }} />
                                <span>{contact.phone}</span>
                            </div>
                        )}
                        {contact.title && (
                            <div className="flex items-center gap-2">
                                <Building2 size={14} style={{ color: 'var(--color-text-muted)' }} />
                                <span>{contact.title}</span>
                            </div>
                        )}
                        {contact.source && (
                            <div className="flex items-center gap-2">
                                <Tag size={14} style={{ color: 'var(--color-text-muted)' }} />
                                <span>Source: {contact.source}</span>
                            </div>
                        )}
                        <div className="flex items-center gap-2">
                            <Calendar size={14} style={{ color: 'var(--color-text-muted)' }} />
                            <span style={{ color: 'var(--color-text-muted)' }}>
                                Created {new Date(contact.created_at).toLocaleDateString()}
                            </span>
                        </div>
                    </div>

                    {/* Tags */}
                    {contact.tags?.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-1">
                            {contact.tags.map((tag: string) => (
                                <span
                                    key={tag}
                                    className="badge"
                                    style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Custom Fields */}
                    {Object.keys(contact.custom_fields || {}).length > 0 && (
                        <div className="mt-4">
                            <h4 className="text-xs font-semibold uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>
                                Custom Fields
                            </h4>
                            {Object.entries(contact.custom_fields).map(([key, value]) => (
                                <div key={key} className="flex justify-between text-sm py-1">
                                    <span style={{ color: 'var(--color-text-muted)' }}>{key}</span>
                                    <span>{String(value)}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Notes */}
                    {contact.notes && (
                        <div className="mt-4">
                            <h4 className="text-xs font-semibold uppercase mb-2" style={{ color: 'var(--color-text-muted)' }}>Notes</h4>
                            <p className="text-sm whitespace-pre-wrap" style={{ color: 'var(--color-text-muted)' }}>
                                {contact.notes}
                            </p>
                        </div>
                    )}
                </div>

                {/* Timeline */}
                <div className="card lg:col-span-2">
                    <h3 className="text-sm font-semibold mb-4">Activity Timeline</h3>
                    <div className="flex flex-col gap-3">
                        {timeline.map((act: any) => (
                            <div
                                key={act.id}
                                className="flex gap-3 p-3 rounded-lg"
                                style={{ background: 'var(--color-bg)' }}
                            >
                                <span className="text-lg flex-shrink-0">{activityIcons[act.type] || '📌'}</span>
                                <div className="min-w-0 flex-1">
                                    <div className="flex items-center justify-between">
                                        <p className="text-sm font-medium">{act.subject}</p>
                                        <span className="text-xs flex-shrink-0 ml-2" style={{ color: 'var(--color-text-muted)' }}>
                                            {new Date(act.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    {act.body && (
                                        <p className="text-sm mt-1 whitespace-pre-wrap" style={{ color: 'var(--color-text-muted)' }}>
                                            {act.body.length > 300 ? act.body.slice(0, 300) + '...' : act.body}
                                        </p>
                                    )}
                                    <div className="flex items-center gap-2 mt-1">
                                        <span
                                            className="badge text-xs"
                                            style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}
                                        >
                                            {act.type}
                                        </span>
                                        {act.source !== 'manual' && (
                                            <span
                                                className="badge text-xs"
                                                style={{ background: 'rgba(168,85,247,0.12)', color: 'var(--color-accent)' }}
                                            >
                                                via {act.source}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {!timeline.length && (
                            <p className="text-sm text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
                                No activities yet. Activities from n8n webhooks will appear here.
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
