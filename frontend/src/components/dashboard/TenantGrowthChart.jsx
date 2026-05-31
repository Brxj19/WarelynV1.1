import { Bar, ComposedChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const tooltipStyle = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };

export function TenantGrowthChart({ data = [] }) {
  if (!data.length) return <p className="py-20 text-center text-sm text-warelyn-muted">No tenant growth data yet.</p>;

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="#e5e7eb" strokeDasharray="3 3" />
        <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6b7280' }} />
        <YAxis yAxisId="left" allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
        <YAxis yAxisId="right" orientation="right" allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey="new_tenants" fill="#10b981" radius={[4, 4, 0, 0]} yAxisId="left" />
        <Line dataKey="cumulative" dot={{ r: 3 }} stroke="#6366f1" strokeWidth={2} type="monotone" yAxisId="right" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

