import { ArrowRight, PieChart as PieChartIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { EmptyState } from '../ui/EmptyState.jsx';
import { emptyStateIllustrations } from '../../lib/emptyStates.js';
import { formatDateTime } from '../../utils/formatters.js';

const ROLE_COLORS = ['#1e3a5f', '#10b981', '#6366f1', '#f59e0b', '#8b5cf6'];

function priorityBadgeClass(priority) {
  if (priority === 'HIGH') return 'border-red-200 bg-red-50 text-red-600';
  if (priority === 'NORMAL') return 'border-blue-200 bg-blue-50 text-blue-600';
  return 'border-slate-200 bg-slate-100 text-slate-600';
}

export function TaskInboxWidget({ tasks = [], maxItems = 5, showRoleBreakdown = false }) {
  if (!tasks.length) {
    return (
      <EmptyState
        description="No open tasks."
        illustration={emptyStateIllustrations.overview}
        title="No open tasks"
      />
    );
  }

  if (showRoleBreakdown) {
    const grouped = Object.entries(
      tasks.reduce((acc, task) => {
        acc[task.assigned_role] = (acc[task.assigned_role] || 0) + 1;
        return acc;
      }, {}),
    ).map(([role, count]) => ({ role, count }));

    return (
      <div className="grid gap-4 md:grid-cols-[220px_1fr]">
        <div className="h-[180px]">
          <ResponsiveContainer height="100%" width="100%">
            <PieChart>
              <Pie data={grouped} dataKey="count" innerRadius={50} nameKey="role" outerRadius={80}>
                {grouped.map((entry, index) => (
                  <Cell key={entry.role} fill={ROLE_COLORS[index % ROLE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e5e7eb', fontSize: '0.8rem' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-2">
          {grouped.map((entry, index) => (
            <Link
              className="flex items-center justify-between rounded-lg border border-warelyn-border bg-white px-3 py-2 text-sm transition hover:bg-gray-50"
              key={entry.role}
              to={`/my-tasks?role=${entry.role}`}
            >
              <span className="inline-flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ROLE_COLORS[index % ROLE_COLORS.length] }} />
                <span className="font-medium text-warelyn-text">{entry.role.replace(/_/g, ' ')}</span>
              </span>
              <span className="font-semibold text-[#1e3a5f]">{entry.count}</span>
            </Link>
          ))}
          <Link className="inline-flex items-center gap-1 text-xs font-semibold text-warelyn-primary hover:underline" to="/my-tasks">
            <PieChartIcon size={14} /> View full task board
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.slice(0, maxItems).map((task) => (
        <article className="rounded-xl border border-warelyn-border bg-white p-3" key={task.id}>
          <div className="mb-2 flex items-start justify-between gap-2">
            <p className="min-w-0 truncate text-sm font-semibold text-warelyn-text">{task.title}</p>
            <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${priorityBadgeClass(task.priority)}`}>
              {task.priority || 'LOW'}
            </span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-xs text-warelyn-muted">
                {String(task.entity_type || '').replace(/_/g, ' ')} #{task.entity_id}
              </p>
              <p className="text-[10px] text-warelyn-muted">{formatDateTime(task.created_at)}</p>
            </div>
            <Link
              className="inline-flex items-center gap-1 rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs font-semibold text-warelyn-primary hover:bg-slate-50"
              to={task.action_url || '/my-tasks'}
            >
              Go <ArrowRight size={12} />
            </Link>
          </div>
        </article>
      ))}
      <Link className="inline-flex items-center gap-1 text-xs font-semibold text-warelyn-primary hover:underline" to="/my-tasks">
        View all <ArrowRight size={12} />
      </Link>
    </div>
  );
}
