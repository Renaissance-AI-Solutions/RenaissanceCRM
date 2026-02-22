import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, customizationApi } from '../services/api';
import { Key, Webhook, Settings as SettingsIcon, Layers, Trash2, Copy } from 'lucide-react';

export default function Settings() {
    const [tab, setTab] = useState<'api-keys' | 'webhooks' | 'fields' | 'general'>('api-keys');

    const tabs = [
        { id: 'api-keys' as const, label: 'API Keys', icon: Key },
        { id: 'webhooks' as const, label: 'Webhooks', icon: Webhook },
        { id: 'fields' as const, label: 'Custom Fields', icon: Layers },
        { id: 'general' as const, label: 'General', icon: SettingsIcon },
    ];

    return (
        <div className="animate-in max-w-4xl">
            <h1 className="text-2xl font-bold mb-6" style={{ color: 'var(--color-text)' }}>Settings</h1>

            {/* Tabs */}
            <div className="flex gap-1 mb-6 p-1 rounded-xl" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
                {tabs.map(({ id, label, icon: Icon }) => (
                    <button
                        key={id}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 justify-center"
                        style={{
                            background: tab === id ? 'var(--color-primary)' : 'transparent',
                            color: tab === id ? 'white' : 'var(--color-text-muted)',
                        }}
                        onClick={() => setTab(id)}
                    >
                        <Icon size={16} /> {label}
                    </button>
                ))}
            </div>

            {tab === 'api-keys' && <ApiKeysTab />}
            {tab === 'webhooks' && <WebhooksTab />}
            {tab === 'fields' && <CustomFieldsTab />}
            {tab === 'general' && <GeneralTab />}
        </div>
    );
}

// ---------------------------------------------------------------------------
// API Keys Tab
// ---------------------------------------------------------------------------
function ApiKeysTab() {
    const queryClient = useQueryClient();
    const [label, setLabel] = useState('');
    const [newKey, setNewKey] = useState('');

    const { data } = useQuery({ queryKey: ['api-keys'], queryFn: () => authApi.listApiKeys() });
    const keys = data?.data || [];

    const createMutation = useMutation({
        mutationFn: (data: any) => authApi.createApiKey(data),
        onSuccess: (res) => {
            setNewKey(res.data.raw_key);
            setLabel('');
            queryClient.invalidateQueries({ queryKey: ['api-keys'] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => authApi.deleteApiKey(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
    });

    return (
        <div>
            <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                API keys are used to authenticate n8n webhooks. Use the <code className="px-1 py-0.5 rounded" style={{ background: 'var(--color-bg)' }}>x-api-key</code> header.
            </p>

            {newKey && (
                <div className="card mb-4" style={{ borderColor: 'var(--color-success)' }}>
                    <p className="text-sm font-medium mb-2" style={{ color: 'var(--color-success)' }}>
                        ⚠️ Copy this key now — it won't be shown again
                    </p>
                    <div className="flex items-center gap-2">
                        <code className="flex-1 text-sm p-2 rounded" style={{ background: 'var(--color-bg)', wordBreak: 'break-all' }}>
                            {newKey}
                        </code>
                        <button className="btn btn-ghost" onClick={() => { navigator.clipboard.writeText(newKey); }}>
                            <Copy size={14} />
                        </button>
                    </div>
                </div>
            )}

            <form
                className="flex gap-2 mb-4"
                onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ label, expires_in_days: 90 }); }}
            >
                <input className="input flex-1" placeholder="Key label (e.g. n8n-production)" value={label} onChange={(e) => setLabel(e.target.value)} required />
                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>Create Key</button>
            </form>

            <div className="flex flex-col gap-2">
                {keys.map((k: any) => (
                    <div key={k.id} className="card flex items-center justify-between" style={{ padding: '0.75rem 1rem' }}>
                        <div>
                            <p className="text-sm font-medium">{k.label}</p>
                            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                                Prefix: {k.key_prefix}... · Created {new Date(k.created_at).toLocaleDateString()}
                                {k.last_used_at && ` · Last used ${new Date(k.last_used_at).toLocaleDateString()}`}
                            </p>
                        </div>
                        <button className="btn btn-ghost" onClick={() => deleteMutation.mutate(k.id)}>
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
                {!keys.length && <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>No API keys yet.</p>}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Webhooks Tab
// ---------------------------------------------------------------------------
function WebhooksTab() {
    const queryClient = useQueryClient();
    const [form, setForm] = useState({ event: '', url: '' });

    const { data } = useQuery({ queryKey: ['webhooks'], queryFn: () => customizationApi.getWebhooks() });
    const webhooks = data?.data || [];

    const createMutation = useMutation({
        mutationFn: (data: any) => customizationApi.createWebhook(data),
        onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['webhooks'] }); setForm({ event: '', url: '' }); },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => customizationApi.deleteWebhook(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['webhooks'] }),
    });

    return (
        <div>
            <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                Configure outbound webhooks. The CRM will POST to these URLs when events occur.
            </p>
            <form
                className="flex gap-2 mb-4"
                onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }}
            >
                <select className="input" style={{ width: 200 }} value={form.event} onChange={(e) => setForm({ ...form, event: e.target.value })} required>
                    <option value="">Select event</option>
                    <option value="contact.created">Contact Created</option>
                    <option value="contact.updated">Contact Updated</option>
                    <option value="deal.created">Deal Created</option>
                    <option value="deal.stage_changed">Deal Stage Changed</option>
                </select>
                <input className="input flex-1" placeholder="Webhook URL" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} required />
                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>Add</button>
            </form>
            <div className="flex flex-col gap-2">
                {webhooks.map((w: any) => (
                    <div key={w.id} className="card flex items-center justify-between" style={{ padding: '0.75rem 1rem' }}>
                        <div>
                            <span className="badge mr-2" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--color-primary)' }}>
                                {w.event}
                            </span>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>{w.url}</span>
                        </div>
                        <button className="btn btn-ghost" onClick={() => deleteMutation.mutate(w.id)}>
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Custom Fields Tab
// ---------------------------------------------------------------------------
function CustomFieldsTab() {
    const queryClient = useQueryClient();
    const [form, setForm] = useState({ entity_type: 'contact', field_name: '', field_label: '', field_type: 'text' });

    const { data } = useQuery({ queryKey: ['custom-fields'], queryFn: () => customizationApi.getFields() });
    const fields = data?.data || [];

    const createMutation = useMutation({
        mutationFn: (data: any) => customizationApi.createField(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['custom-fields'] });
            setForm({ entity_type: 'contact', field_name: '', field_label: '', field_type: 'text' });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => customizationApi.deleteField(id),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['custom-fields'] }),
    });

    return (
        <div>
            <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                Add custom fields to contacts, companies, or deals. No code changes needed.
            </p>
            <form
                className="flex gap-2 mb-4 flex-wrap"
                onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form); }}
            >
                <select className="input" style={{ width: 130 }} value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })}>
                    <option value="contact">Contact</option>
                    <option value="company">Company</option>
                    <option value="deal">Deal</option>
                </select>
                <input className="input" style={{ width: 150 }} placeholder="Field name (key)" value={form.field_name} onChange={(e) => setForm({ ...form, field_name: e.target.value })} required />
                <input className="input" style={{ width: 150 }} placeholder="Label" value={form.field_label} onChange={(e) => setForm({ ...form, field_label: e.target.value })} required />
                <select className="input" style={{ width: 120 }} value={form.field_type} onChange={(e) => setForm({ ...form, field_type: e.target.value })}>
                    <option value="text">Text</option>
                    <option value="number">Number</option>
                    <option value="date">Date</option>
                    <option value="select">Select</option>
                    <option value="boolean">Boolean</option>
                    <option value="url">URL</option>
                    <option value="email">Email</option>
                    <option value="phone">Phone</option>
                </select>
                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>Add Field</button>
            </form>
            <div className="flex flex-col gap-2">
                {fields.map((f: any) => (
                    <div key={f.id} className="card flex items-center justify-between" style={{ padding: '0.75rem 1rem' }}>
                        <div className="flex items-center gap-3">
                            <span className="badge" style={{ background: 'rgba(168,85,247,0.12)', color: 'var(--color-accent)' }}>
                                {f.entity_type}
                            </span>
                            <span className="text-sm font-medium">{f.field_label}</span>
                            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>({f.field_name}, {f.field_type})</span>
                        </div>
                        <button className="btn btn-ghost" onClick={() => deleteMutation.mutate(f.id)}>
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// General Tab
// ---------------------------------------------------------------------------
function GeneralTab() {
    const { data } = useQuery({ queryKey: ['tenant-settings'], queryFn: () => customizationApi.getSettings() });
    const settings = data?.data;

    return (
        <div>
            <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                Organization settings and configuration.
            </p>
            {settings && (
                <div className="card">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Organization</label>
                            <p className="text-sm font-medium mt-1">{settings.name}</p>
                        </div>
                        <div>
                            <label className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Slug</label>
                            <p className="text-sm font-medium mt-1">{settings.slug}</p>
                        </div>
                        <div>
                            <label className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Tenant ID</label>
                            <p className="text-sm font-mono mt-1" style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{settings.tenant_id}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
