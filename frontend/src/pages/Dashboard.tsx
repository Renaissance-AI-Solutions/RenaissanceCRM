import { useQuery } from '@tanstack/react-query';
import { reportsApi, activitiesApi } from '../services/api';
import {
    TrendingUp,
    DollarSign,
    Target,
    Activity,
    ArrowUpRight,
} from 'lucide-react';

export default function Dashboard() {
    const { data: pipeline } = useQuery({ queryKey: ['pipeline-report'], queryFn: () => reportsApi.pipeline() });
    const { data: forecast } = useQuery({ queryKey: ['forecast'], queryFn: () => reportsApi.forecast() });
    const { data: actSummary } = useQuery({ queryKey: ['activity-summary'], queryFn: () => reportsApi.activitySummary(30) });
    const { data: recentActs } = useQuery({ queryKey: ['recent-activities'], queryFn: () => activitiesApi.list({ per_page: 8 }) });

    const p = pipeline?.data;
    const f = forecast?.data;
    const as = actSummary?.data;

    const kpis = [
        {
            label: 'Open Deals',
            value: p?.total_open_deals ?? '—',
            icon: Target,
            color: '#6366f1',
            bg: 'rgba(99,102,241,0.1)',
        },
        {
            label: 'Pipeline Value',
            value: p ? `$${(p.total_open_value ?? 0).toLocaleString()}` : '—',
            icon: DollarSign,
            color: '#22c55e',
            bg: 'rgba(34,197,94,0.1)',
        },
        {
            label: 'Weighted Forecast',
            value: f ? `$${(f.weighted_forecast ?? 0).toLocaleString()}` : '—',
            icon: TrendingUp,
            color: '#a855f7',
            bg: 'rgba(168,85,247,0.1)',
        },
        {
            label: 'Activities (30d)',
            value: as?.total_activities ?? '—',
            icon: Activity,
            color: '#f59e0b',
            bg: 'rgba(245,158,11,0.1)',
        },
    ];

    return (
        <div className="animate-in">
            <h1 className="text-2xl font-bold mb-6" style={{ color: 'var(--color-text)' }}>
                Dashboard
            </h1>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {kpis.map((kpi) => (
                    <div key={kpi.label} className="card flex items-center gap-4">
                        <div
                            className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                            style={{ background: kpi.bg }}
                        >
                            <kpi.icon size={22} color={kpi.color} />
                        </div>
                        <div>
                            <p className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
                                {kpi.label}
                            </p>
                            <p className="text-xl font-bold" style={{ color: 'var(--color-text)' }}>
                                {kpi.value}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Pipeline Stages */}
                <div className="card lg:col-span-2">
                    <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text)' }}>
                        Pipeline Stages
                    </h3>
                    <div className="flex flex-col gap-2">
                        {p?.stages?.map((stage: any) => (
                            <div
                                key={stage.name}
                                className="flex items-center justify-between p-3 rounded-lg"
                                style={{ background: 'var(--color-bg)' }}
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full" style={{ background: stage.color }} />
                                    <span className="text-sm font-medium">{stage.name}</span>
                                </div>
                                <div className="flex items-center gap-4 text-sm">
                                    <span style={{ color: 'var(--color-text-muted)' }}>{stage.count} deals</span>
                                    <span className="font-medium">${(stage.value ?? 0).toLocaleString()}</span>
                                </div>
                            </div>
                        ))}
                        {!p?.stages?.length && (
                            <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>
                                No deals yet. Create your first deal to see pipeline stats.
                            </p>
                        )}
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="card">
                    <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text)' }}>
                        Recent Activity
                    </h3>
                    <div className="flex flex-col gap-2">
                        {recentActs?.data?.items?.map((act: any) => (
                            <div
                                key={act.id}
                                className="flex items-start gap-3 p-2 rounded-lg"
                                style={{ background: 'var(--color-bg)' }}
                            >
                                <ArrowUpRight size={14} style={{ color: 'var(--color-primary)', marginTop: 3, flexShrink: 0 }} />
                                <div className="min-w-0">
                                    <p className="text-sm truncate">{act.subject}</p>
                                    <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                                        {act.type} · {new Date(act.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        ))}
                        {!recentActs?.data?.items?.length && (
                            <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>
                                No activities yet.
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Win Rate */}
            {p && (p.won_count > 0 || p.lost_count > 0) && (
                <div className="card mt-4">
                    <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text)' }}>
                        Win Rate
                    </h3>
                    <div className="flex items-center gap-4">
                        <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ background: 'var(--color-bg)' }}>
                            <div
                                className="h-full rounded-full"
                                style={{
                                    width: `${p.win_rate}%`,
                                    background: 'linear-gradient(90deg, #22c55e, #6366f1)',
                                }}
                            />
                        </div>
                        <span className="text-sm font-bold" style={{ color: 'var(--color-success)' }}>
                            {p.win_rate?.toFixed(1)}%
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
