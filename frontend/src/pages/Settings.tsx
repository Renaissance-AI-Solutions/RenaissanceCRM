import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, customizationApi } from '../services/api';
import { Key, Webhook, Settings as SettingsIcon, Layers, Trash2, Copy, Save, CheckCircle, Sparkles, Mail, Wifi, WifiOff } from 'lucide-react';
import api from '../services/api';

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
    const queryClient = useQueryClient();

    // n8n webhook state
    const [webhookUrl, setWebhookUrl] = useState('');
    const [webhookSaved, setWebhookSaved] = useState(false);

    // LMStudio state
    const [lmUrl, setLmUrl] = useState('');
    const [lmApiKey, setLmApiKey] = useState('');
    const [lmModel, setLmModel] = useState('');
    const [lmSaved, setLmSaved] = useState(false);

    // Gmail state
    const [gmailClientId, setGmailClientId] = useState('');
    const [gmailClientSecret, setGmailClientSecret] = useState('');
    const [gmailRefreshToken, setGmailRefreshToken] = useState('');
    const [gmailPollEnabled, setGmailPollEnabled] = useState(false);
    const [gmailSaved, setGmailSaved] = useState(false);
    const [gmailStatus, setGmailStatus] = useState<{ connected: boolean; email?: string; error?: string; last_polled_at?: string } | null>(null);
    const [gmailTesting, setGmailTesting] = useState(false);

    const { data } = useQuery({ queryKey: ['tenant-settings'], queryFn: () => customizationApi.getSettings() });
    const settings = data?.data;

    // Populate fields from settings once loaded
    useEffect(() => {
        if (settings?.settings) {
            const s = settings.settings;
            if (s.n8n_email_send_webhook !== undefined) setWebhookUrl(s.n8n_email_send_webhook || '');
            if (s.lmstudio_url !== undefined) setLmUrl(s.lmstudio_url || '');
            if (s.lmstudio_api_key !== undefined) setLmApiKey(s.lmstudio_api_key || '');
            if (s.lmstudio_model !== undefined) setLmModel(s.lmstudio_model || '');
            if (s.gmail_client_id !== undefined) setGmailClientId(s.gmail_client_id || '');
            if (s.gmail_client_secret !== undefined) setGmailClientSecret(s.gmail_client_secret || '');
            if (s.gmail_refresh_token !== undefined) setGmailRefreshToken(s.gmail_refresh_token || '');
            if (s.gmail_poll_enabled !== undefined) setGmailPollEnabled(!!s.gmail_poll_enabled);
        }
    }, [settings]);

    // Load Gmail status on mount
    useEffect(() => {
        api.get('/api/gmail/status')
            .then(res => setGmailStatus(res.data))
            .catch(() => setGmailStatus({ connected: false }));
    }, []);

    const webhookMutation = useMutation({
        mutationFn: (url: string) => customizationApi.updateSettings({ n8n_email_send_webhook: url }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tenant-settings'] });
            setWebhookSaved(true);
            setTimeout(() => setWebhookSaved(false), 3000);
        },
    });

    const lmstudioMutation = useMutation({
        mutationFn: (cfg: { lmstudio_url: string; lmstudio_api_key: string; lmstudio_model: string }) =>
            customizationApi.updateSettings(cfg),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tenant-settings'] });
            setLmSaved(true);
            setTimeout(() => setLmSaved(false), 3000);
        },
    });

    const gmailMutation = useMutation({
        mutationFn: (cfg: { gmail_client_id: string; gmail_client_secret: string; gmail_refresh_token: string; gmail_poll_enabled: boolean }) =>
            customizationApi.updateSettings(cfg),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tenant-settings'] });
            setGmailSaved(true);
            setTimeout(() => setGmailSaved(false), 3000);
        },
    });

    const testGmailConnection = async () => {
        setGmailTesting(true);
        try {
            const res = await api.post('/api/gmail/test');
            setGmailStatus({ connected: true, email: res.data.email });
        } catch (err: any) {
            setGmailStatus({ connected: false, error: err?.response?.data?.detail || 'Connection failed' });
        } finally {
            setGmailTesting(false);
        }
    };

    return (
        <div className="flex flex-col gap-6">
            {/* Organization info */}
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                Organization settings and integration configuration.
            </p>
            {settings && (
                <div className="card">
                    <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.688rem' }}>
                        Organization
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Name</label>
                            <p className="text-sm font-medium mt-1">{settings.name}</p>
                        </div>
                        <div>
                            <label className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Slug</label>
                            <p className="text-sm font-medium mt-1">{settings.slug}</p>
                        </div>
                        <div className="col-span-2">
                            <label className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>Tenant ID</label>
                            <p className="text-sm font-mono mt-1" style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{settings.tenant_id}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* n8n Integrations */}
            <div className="card">
                <h3
                    className="text-sm font-semibold mb-1"
                    style={{ color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.688rem' }}
                >
                    n8n Integrations
                </h3>
                <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                    When you click <strong>Approve &amp; Send</strong> on a draft email, the CRM will POST the email payload to this n8n webhook URL so n8n can send it via your email provider.
                </p>

                <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>
                    Email Send Webhook URL
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                    <input
                        className="input flex-1"
                        type="url"
                        placeholder="https://your-n8n.com/webhook/send-email"
                        value={webhookUrl}
                        onChange={(e) => { setWebhookUrl(e.target.value); setWebhookSaved(false); }}
                    />
                    <button
                        className="btn btn-primary"
                        style={{ gap: 6, minWidth: 90 }}
                        disabled={webhookMutation.isPending}
                        onClick={() => webhookMutation.mutate(webhookUrl)}
                    >
                        {webhookSaved ? (
                            <><CheckCircle size={14} /> Saved</>
                        ) : (
                            <><Save size={14} /> Save</>
                        )}
                    </button>
                </div>

                {/* Payload preview */}
                <div style={{ marginTop: 16 }}>
                    <p className="text-xs font-semibold mb-2" style={{ color: 'var(--color-text-muted)' }}>
                        Payload sent to your webhook:
                    </p>
                    <pre
                        style={{
                            fontSize: '0.75rem', lineHeight: 1.6, padding: '0.75rem', borderRadius: 8,
                            background: 'var(--color-bg)', color: 'var(--color-text-muted)', overflow: 'auto',
                        }}
                    >
{`{
  "draft_email_id": "uuid",
  "contact_id": "uuid",
  "contact_name": "Kimberly Young",
  "contact_email": "kimyoung@yahoo.com",
  "company_name": "Baptist Memorial Hospital",
  "subject": "Email subject line",
  "body": "Full email body text..."
}`}
                    </pre>
                </div>

                {/* n8n callback info */}
                <div style={{ marginTop: 16, padding: '0.75rem', borderRadius: 8, background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.15)' }}>
                    <p className="text-xs font-semibold mb-1" style={{ color: 'var(--color-primary)' }}>
                        After n8n sends the email, close the loop:
                    </p>
                    <p className="text-xs" style={{ color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
                        Have n8n call <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 4 }}>POST /api/webhooks/n8n/draft-email-sent</code> with{' '}
                        <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 4 }}>{'{"draft_email_id": "uuid"}'}</code>{' '}
                        to automatically mark the draft as <strong>Sent</strong> in the CRM.
                        Use your <strong>n8n-production</strong> API key in the <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 4 }}>x-api-key</code> header.
                    </p>
                </div>
            </div>

            {/* AI Integration (LMStudio) */}
            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Sparkles size={14} color="var(--color-accent)" />
                    <h3
                        className="text-sm font-semibold"
                        style={{ color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.688rem' }}
                    >
                        AI Integration (LMStudio)
                    </h3>
                </div>
                <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                    Connect to your local LMStudio instance to rewrite draft emails with AI.
                    Accessible via Tailscale VPN. Click <strong>AI Edit</strong> on any draft email to use it.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div>
                        <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>
                            LMStudio Base URL
                        </label>
                        <input
                            className="input"
                            style={{ width: '100%' }}
                            placeholder="http://100.x.x.x:1234"
                            value={lmUrl}
                            onChange={(e) => { setLmUrl(e.target.value); setLmSaved(false); }}
                        />
                        <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                            Your Tailscale IP + LMStudio port, e.g. <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 3 }}>http://100.121.191.37:1234</code>
                        </p>
                    </div>

                    <div>
                        <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>
                            API Key
                        </label>
                        <input
                            className="input"
                            style={{ width: '100%' }}
                            type="password"
                            placeholder="sk-lm-..."
                            value={lmApiKey}
                            onChange={(e) => { setLmApiKey(e.target.value); setLmSaved(false); }}
                            autoComplete="off"
                        />
                        <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                            From LMStudio → Developer → API Key
                        </p>
                    </div>

                    <div>
                        <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>
                            Default Model
                        </label>
                        <input
                            className="input"
                            style={{ width: '100%' }}
                            placeholder="qwen/qwen3-14b"
                            value={lmModel}
                            onChange={(e) => { setLmModel(e.target.value); setLmSaved(false); }}
                        />
                        <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                            Model ID exactly as shown in LMStudio. Available models: <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 3 }}>qwen/qwen3-14b</code>,{' '}
                            <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 3 }}>qwen/qwen3-32b</code>,{' '}
                            <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 3 }}>kimi-linear-48b-a3b-instruct</code>
                        </p>
                    </div>

                    <div>
                        <button
                            className="btn btn-primary"
                            style={{ gap: 6 }}
                            disabled={lmstudioMutation.isPending}
                            onClick={() => lmstudioMutation.mutate({ lmstudio_url: lmUrl, lmstudio_api_key: lmApiKey, lmstudio_model: lmModel })}
                        >
                            {lmSaved ? (
                                <><CheckCircle size={14} /> Saved</>
                            ) : (
                                <><Save size={14} /> Save AI Settings</>
                            )}
                        </button>
                        {lmstudioMutation.isError && (
                            <p className="text-xs mt-2" style={{ color: 'var(--color-danger)' }}>
                                Failed to save. Please try again.
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Gmail Integration */}
            <div className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Mail size={14} color="var(--color-primary)" />
                    <h3
                        className="text-sm font-semibold"
                        style={{ color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.688rem' }}
                    >
                        Gmail Integration
                    </h3>
                    {gmailStatus && (
                        <span
                            style={{
                                marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4,
                                fontSize: '0.75rem', fontWeight: 600,
                                color: gmailStatus.connected ? 'var(--color-success)' : 'var(--color-text-muted)',
                            }}
                        >
                            {gmailStatus.connected
                                ? <><Wifi size={12} /> {gmailStatus.email}</>
                                : <><WifiOff size={12} /> Not connected</>}
                        </span>
                    )}
                </div>
                <p className="text-sm mb-4" style={{ color: 'var(--color-text-muted)' }}>
                    Connect Gmail to automatically capture inbound replies and auto-draft AI responses.
                    Polling runs every 2 minutes in the background.
                </p>

                {/* Setup instructions */}
                <div style={{ marginBottom: 16, padding: '0.75rem', borderRadius: 8, background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.15)' }}>
                    <p className="text-xs font-semibold mb-2" style={{ color: 'var(--color-primary)' }}>Setup (one-time):</p>
                    <ol style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', lineHeight: 1.8, paddingLeft: 16, margin: 0 }}>
                        <li>Go to <strong>console.cloud.google.com</strong> → Create project → Enable Gmail API</li>
                        <li>Create OAuth credentials → type: <strong>Desktop app</strong> → Download JSON</li>
                        <li>Run <code style={{ background: 'var(--color-bg)', padding: '1px 4px', borderRadius: 3 }}>python get_gmail_token.py</code> from the repo root on your local machine</li>
                        <li>Paste the Client ID, Client Secret, and Refresh Token below → Save → Test</li>
                    </ol>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div>
                        <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>Client ID</label>
                        <input
                            className="input"
                            style={{ width: '100%' }}
                            placeholder="1234567890-abc.apps.googleusercontent.com"
                            value={gmailClientId}
                            onChange={(e) => { setGmailClientId(e.target.value); setGmailSaved(false); }}
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>Client Secret</label>
                        <input
                            className="input"
                            style={{ width: '100%' }}
                            type="password"
                            placeholder="GOCSPX-..."
                            value={gmailClientSecret}
                            onChange={(e) => { setGmailClientSecret(e.target.value); setGmailSaved(false); }}
                            autoComplete="off"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-semibold block mb-1" style={{ color: 'var(--color-text-muted)' }}>Refresh Token</label>
                        <input
                            className="input"
                            style={{ width: '100%' }}
                            type="password"
                            placeholder="1//0g..."
                            value={gmailRefreshToken}
                            onChange={(e) => { setGmailRefreshToken(e.target.value); setGmailSaved(false); }}
                            autoComplete="off"
                        />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.875rem', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={gmailPollEnabled}
                                onChange={(e) => { setGmailPollEnabled(e.target.checked); setGmailSaved(false); }}
                            />
                            Enable polling (every 2 min)
                        </label>
                        {gmailStatus?.last_polled_at && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                                Last polled: {new Date(gmailStatus.last_polled_at).toLocaleTimeString()}
                            </span>
                        )}
                    </div>
                    {gmailStatus?.error && (
                        <p style={{ fontSize: '0.75rem', color: 'var(--color-danger)' }}>⚠ {gmailStatus.error}</p>
                    )}
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button
                            className="btn btn-primary"
                            style={{ gap: 6 }}
                            disabled={gmailMutation.isPending}
                            onClick={() => gmailMutation.mutate({
                                gmail_client_id: gmailClientId,
                                gmail_client_secret: gmailClientSecret,
                                gmail_refresh_token: gmailRefreshToken,
                                gmail_poll_enabled: gmailPollEnabled,
                            })}
                        >
                            {gmailSaved ? <><CheckCircle size={14} /> Saved</> : <><Save size={14} /> Save Gmail Settings</>}
                        </button>
                        <button
                            className="btn btn-ghost"
                            style={{ gap: 6 }}
                            disabled={gmailTesting || !gmailClientId}
                            onClick={testGmailConnection}
                        >
                            {gmailTesting ? 'Testing…' : <><Wifi size={14} /> Test Connection</>}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
