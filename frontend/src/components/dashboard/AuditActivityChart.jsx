import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const tooltipStyle = { borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' };

export function AuditActivityChart({ data = [], avgLine = 0 }) {
  if (!data.length) return <p className="py-20 text-center text-sm text-warelyn-muted">No audit activity yet.</p>;
  const max = Math.max(...data.map((point) => Number(point.event_count || 0)), 1);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="#e5e7eb" strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={(value) => String(value).slice(5)} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
        <Tooltip contentStyle={tooltipStyle} />
        {avgLine > 0 ? <ReferenceLine stroke="#6366f1" strokeDasharray="5 5" y={avgLine} /> : null}
        <Bar dataKey="event_count" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => {
            const value = Number(entry.event_count || 0);
            const isSpike = avgLine > 0 && value > avgLine * 2;
            const opacity = Math.max(0.35, value / max);
            const fill = isSpike ? '#ef4444' : `rgba(99,102,241,${opacity})`;
            return <Cell key={`${entry.date}-${index}`} fill={fill} />;
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

