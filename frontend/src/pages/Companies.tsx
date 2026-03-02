import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { companiesApi, draftEmailsApi } from '../services/api';
import {
    Building2,
    ChevronRight,
    ExternalLink,
    Globe,
    Linkedin,
    Mail,
    MapPin,
    Phone,
    Search,
    ShieldCheck,
    Star,
    Trash2,
    User,
    Users,
} from 'lucide-react';

// Enrichment status badge config
const enrichmentBadge: Record<string, { label: string; bg: string; color: string }> = {
    not_needed: { label: 'Has Email', bg: 'rgba(34,197,94,0.12)', color: 'var(--color-success)' },
    pending: { label: 'Pending', bg: 'rgba(245,158,11,0.12)', color: 'var(--color-warning)' },
    queued: { label: 'Queued', bg: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' },
    enriched: { label: 'Enriched', bg: 'rgba(168,85,247,0.12)', color: 'var(--color-accent)' },
    failed: { label: 'Failed', bg: 'rgba(239,68,68,0.12)', color: 'var(--color-danger)' },
};

// Email campaign status badge config
const emailStatusBadge: Record<string, { label: string; bg: string; color: string; icon: string }> = {
    draft:    { label: 'Draft',    bg: 'rgba(245,158,11,0.15)',  color: '#f59e0b',              icon: '✉' },
    approved: { label: 'Approved', bg: 'rgba(99,102,241,0.15)',  color: 'var(--color-primary)', icon: '✓' },
    sent:     { label: 'Sent',     bg: 'rgba(34,197,94,0.15)',   color: 'var(--color-success)', icon: '✉' },
    rejected: { label: 'Rejected', bg: 'rgba(239,68,68,0.1)',    color: 'var(--color-danger)',  icon: '✗' },
};

// Priority order for showing the most important status when a company has multiple drafts
const statusPriority: Record<string, number> = { draft: 4, approved: 3, sent: 2, rejected: 1 };

function CompanyCard({
    company,
    onDelete,
    contactEmailMap,
    companyEmailStatus,
}: {
    company: any;
    onDelete: (id: string) => void;
    contactEmailMap: Map<string, string>;
    companyEmailStatus: string | undefined;
}) {
    const navigate = useNavigate();
    const [expanded, setExpanded] = useState(false);

    const { data: contactsData, isLoading } = useQuery({
        queryKey: ['company-contacts', company.id],
        queryFn: () => companiesApi.contacts(company.id),
        enabled: expanded,
    });

    const contacts = contactsData?.data || [];
    const emailBadge = companyEmailStatus ? emailStatusBadge[companyEmailStatus] : null;

    return (
        <div
            className="card"
            style={{
                padding: 0,
                overflow: 'hidden',
                borderColor: expanded ? 'var(--color-primary)' : undefined,
                transition: 'border-color 0.25s, box-shadow 0.25s',
                boxShadow: expanded ? '0 0 0 1px rgba(99,102,241,0.15), 0 8px 32px rgba(0,0,0,0.2)' : undefined,
            }}
        >
            {/* Company Header — always visible */}
            <button
                onClick={() => setExpanded(!expanded)}
                style={{
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '1.25rem 1.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    textAlign: 'left',
                    color: 'var(--color-text)',
                }}
            >
                {/* Expand/Collapse chevron */}
                <div
                    style={{
                        transition: 'transform 0.2s',
                        transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
                        color: 'var(--color-text-muted)',
                        flexShrink: 0,
                    }}
                >
                    <ChevronRight size={18} />
                </div>

                {/* Company icon */}
                <div
                    style={{
                        width: 44,
                        height: 44,
                        borderRadius: 10,
                        background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                    }}
                >
                    <Building2 size={22} color="white" />
                </div>

                {/* Company info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: '1rem' }}>{company.name}</span>
                        {/* Email campaign status badge */}
                        {emailBadge && (
                            <span
                                className="badge"
                                style={{
                                    background: emailBadge.bg,
                                    color: emailBadge.color,
                                    fontWeight: 700,
                                    fontSize: '0.688rem',
                                }}
                            >
                                {emailBadge.icon} {emailBadge.label}
                            </span>
                        )}
                    </div>
                    <div
                        style={{
                            color: 'var(--color-text-muted)',
                            fontSize: '0.813rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            marginTop: 2,
                            flexWrap: 'wrap',
                        }}
                    >
                        {company.domain && (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                <Globe size={12} /> {company.domain}
                            </span>
                        )}
                        {company.address && (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                <MapPin size={12} /> {company.address.length > 40 ? company.address.slice(0, 40) + '…' : company.address}
                            </span>
                        )}
                        {company.phone && (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                <Phone size={12} /> {company.phone}
                            </span>
                        )}
                    </div>
                </div>

                {/* Rating */}
                {company.rating != null && (
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '0.25rem 0.625rem',
                            borderRadius: 20,
                            background: 'rgba(245,158,11,0.1)',
                            color: 'var(--color-warning)',
                            fontSize: '0.813rem',
                            fontWeight: 600,
                            flexShrink: 0,
                        }}
                    >
                        <Star size={13} fill="currentColor" />
                        {company.rating.toFixed(1)}
                        {company.reviews_count != null && (
                            <span style={{ fontWeight: 400, marginLeft: 2 }}>({company.reviews_count})</span>
                        )}
                    </div>
                )}

                {/* External links */}
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                    {company.website && (
                        <a
                            href={company.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            title="Website"
                            style={{
                                width: 32,
                                height: 32,
                                borderRadius: 8,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: 'var(--color-bg)',
                                color: 'var(--color-text-muted)',
                                border: '1px solid var(--color-border)',
                                transition: 'all 0.15s',
                            }}
                        >
                            <ExternalLink size={14} />
                        </a>
                    )}
                    {company.google_maps_url && (
                        <a
                            href={company.google_maps_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            title="Google Maps"
                            style={{
                                width: 32,
                                height: 32,
                                borderRadius: 8,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: 'var(--color-bg)',
                                color: 'var(--color-text-muted)',
                                border: '1px solid var(--color-border)',
                                transition: 'all 0.15s',
                            }}
                        >
                            <MapPin size={14} />
                        </a>
                    )}
                    <button
                        onClick={(e) => { e.stopPropagation(); if (confirm(`Delete ${company.name}?`)) onDelete(company.id); }}
                        title="Delete company"
                        style={{
                            width: 32,
                            height: 32,
                            borderRadius: 8,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: 'var(--color-bg)',
                            color: 'var(--color-danger)',
                            border: '1px solid var(--color-border)',
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                        }}
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            </button>

            {/* Expanded contacts list */}
            {expanded && (
                <div
                    className="animate-in"
                    style={{
                        borderTop: '1px solid var(--color-border)',
                        background: 'rgba(15,15,19,0.5)',
                    }}
                >
                    {/* Section header */}
                    <div
                        style={{
                            padding: '0.75rem 1.5rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 8,
                            color: 'var(--color-text-muted)',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                        }}
                    >
                        <Users size={13} />
                        Employees
                        {!isLoading && (
                            <span
                                style={{
                                    marginLeft: 4,
                                    padding: '1px 6px',
                                    borderRadius: 10,
                                    background: 'rgba(99,102,241,0.15)',
                                    color: 'var(--color-primary)',
                                    fontSize: '0.688rem',
                                }}
                            >
                                {contacts.length}
                            </span>
                        )}
                    </div>

                    {isLoading ? (
                        <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                            Loading employees…
                        </div>
                    ) : contacts.length === 0 ? (
                        <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                            No employees linked to this company yet.
                        </div>
                    ) : (
                        <div style={{ padding: '0 0.75rem 0.75rem' }}>
                            {contacts.map((contact: any) => {
                                const contactEmailStatus = contactEmailMap.get(contact.id);
                                const contactBadge = contactEmailStatus ? emailStatusBadge[contactEmailStatus] : null;
                                return (
                                    <div
                                        key={contact.id}
                                        onClick={() => navigate(`/contacts/${contact.id}`)}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.875rem',
                                            padding: '0.75rem',
                                            borderRadius: 10,
                                            cursor: 'pointer',
                                            transition: 'background 0.15s',
                                            marginTop: 2,
                                        }}
                                        onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-surface-hover)')}
                                        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                                    >
                                        {/* Avatar */}
                                        <div
                                            style={{
                                                width: 36,
                                                height: 36,
                                                borderRadius: '50%',
                                                background: contact.is_primary_contact
                                                    ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                                                    : 'var(--color-surface)',
                                                border: contact.is_primary_contact
                                                    ? 'none'
                                                    : '1px solid var(--color-border)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                flexShrink: 0,
                                                position: 'relative',
                                            }}
                                        >
                                            <User size={16} color={contact.is_primary_contact ? 'white' : 'var(--color-text-muted)'} />
                                            {contact.is_primary_contact && (
                                                <div
                                                    title="Primary contact"
                                                    style={{
                                                        position: 'absolute',
                                                        bottom: -2,
                                                        right: -2,
                                                        width: 16,
                                                        height: 16,
                                                        borderRadius: '50%',
                                                        background: 'var(--color-surface)',
                                                        border: '2px solid var(--color-bg)',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                    }}
                                                >
                                                    <ShieldCheck size={10} color="var(--color-success)" />
                                                </div>
                                            )}
                                        </div>

                                        {/* Name & Title */}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                                                <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>
                                                    {contact.first_name} {contact.last_name}
                                                </span>
                                                {contact.is_primary_contact && (
                                                    <span
                                                        className="badge"
                                                        style={{
                                                            background: 'rgba(34,197,94,0.12)',
                                                            color: 'var(--color-success)',
                                                            fontSize: '0.625rem',
                                                            padding: '1px 6px',
                                                        }}
                                                    >
                                                        PRIMARY
                                                    </span>
                                                )}
                                                {/* Per-contact email campaign badge */}
                                                {contactBadge && (
                                                    <span
                                                        className="badge"
                                                        style={{
                                                            background: contactBadge.bg,
                                                            color: contactBadge.color,
                                                            fontSize: '0.625rem',
                                                            padding: '1px 6px',
                                                            fontWeight: 700,
                                                        }}
                                                    >
                                                        {contactBadge.icon} {contactBadge.label}
                                                    </span>
                                                )}
                                            </div>
                                            <div
                                                style={{
                                                    color: 'var(--color-text-muted)',
                                                    fontSize: '0.75rem',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.625rem',
                                                    marginTop: 2,
                                                    flexWrap: 'wrap',
                                                }}
                                            >
                                                {contact.title && <span>{contact.title}</span>}
                                                {contact.departments?.length > 0 && (
                                                    <span style={{ opacity: 0.7 }}>
                                                        {contact.departments.join(', ')}
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Email */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                                            {contact.email ? (
                                                <span
                                                    style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        gap: 4,
                                                        fontSize: '0.813rem',
                                                        color: 'var(--color-text-muted)',
                                                    }}
                                                >
                                                    <Mail size={12} /> {contact.email}
                                                </span>
                                            ) : (
                                                contact.enrichment_status && enrichmentBadge[contact.enrichment_status] && (
                                                    <span
                                                        className="badge"
                                                        style={{
                                                            background: enrichmentBadge[contact.enrichment_status].bg,
                                                            color: enrichmentBadge[contact.enrichment_status].color,
                                                        }}
                                                    >
                                                        {enrichmentBadge[contact.enrichment_status].label}
                                                    </span>
                                                )
                                            )}
                                        </div>

                                        {/* LinkedIn */}
                                        {contact.linkedin_url && (
                                            <a
                                                href={contact.linkedin_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                onClick={(e) => e.stopPropagation()}
                                                title="LinkedIn profile"
                                                style={{
                                                    width: 28,
                                                    height: 28,
                                                    borderRadius: 6,
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    background: 'rgba(99,102,241,0.08)',
                                                    color: 'var(--color-primary)',
                                                    flexShrink: 0,
                                                    transition: 'background 0.15s',
                                                }}
                                            >
                                                <Linkedin size={13} />
                                            </a>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function Companies() {
    const [search, setSearch] = useState('');
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ['companies'],
        queryFn: () => companiesApi.list(),
    });

    // Fetch all draft emails to show campaign status on company/contact cards
    const { data: draftsRes } = useQuery({
        queryKey: ['all-draft-emails'],
        queryFn: () => draftEmailsApi.list(),
        staleTime: 30_000,
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => companiesApi.delete(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['companies'] }),
    });

    const allCompanies = data?.data || [];
    const companies = search
        ? allCompanies.filter(
            (c: any) =>
                c.name?.toLowerCase().includes(search.toLowerCase()) ||
                c.domain?.toLowerCase().includes(search.toLowerCase()) ||
                c.address?.toLowerCase().includes(search.toLowerCase())
        )
        : allCompanies;

    // Build maps from draft emails
    const contactEmailMap = new Map<string, string>();
    const companyEmailMap = new Map<string, string>();

    for (const draft of (draftsRes?.data?.items || [])) {
        // Per-contact: highest priority status
        const currentContact = contactEmailMap.get(draft.contact_id);
        if (!currentContact || (statusPriority[draft.status] || 0) > (statusPriority[currentContact] || 0)) {
            contactEmailMap.set(draft.contact_id, draft.status);
        }
        // Per-company: highest priority status across all contacts
        const currentCompany = companyEmailMap.get(draft.company_id);
        if (!currentCompany || (statusPriority[draft.status] || 0) > (statusPriority[currentCompany] || 0)) {
            companyEmailMap.set(draft.company_id, draft.status);
        }
    }

    return (
        <div className="animate-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Companies</h1>
                    <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                        {allCompanies.length} companies · Click to expand employees
                    </p>
                </div>
            </div>

            {/* Search */}
            <div className="mb-5 relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
                <input
                    className="input"
                    style={{ paddingLeft: '2.25rem' }}
                    placeholder="Search companies by name, domain, or location…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {/* Company list */}
            {isLoading ? (
                <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>
                    <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                    Loading companies…
                </div>
            ) : companies.length === 0 ? (
                <div
                    className="card text-center"
                    style={{
                        padding: '3rem 1.5rem',
                        color: 'var(--color-text-muted)',
                        borderStyle: 'dashed',
                    }}
                >
                    <Building2 size={40} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
                    <p style={{ fontSize: '0.875rem' }}>
                        {search ? 'No companies match your search.' : 'No companies yet. Companies will appear here once leads arrive from Clay.'}
                    </p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {companies.map((company: any) => (
                        <CompanyCard
                            key={company.id}
                            company={company}
                            onDelete={(id) => deleteMutation.mutate(id)}
                            contactEmailMap={contactEmailMap}
                            companyEmailStatus={companyEmailMap.get(company.id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
