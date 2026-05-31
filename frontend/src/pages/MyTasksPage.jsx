import { CheckCircle2, Clock, ExternalLink, Inbox, PlayCircle } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDateTime } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as workflowService from '../services/workflowService.js';

const TABS = [
  { key: null, label: 'All' },
  { key: 'OPEN', label: 'Open' },
  { key: 'IN_PROGRESS', label: 'In Progress' },
  { key: 'COMPLETED', label: 'Completed' },
];

const PRIORITY_STYLES = {
  URGENT: 'bg-red-100 text-red-700 border-red-200',
  HIGH: 'bg-red-50 text-red-600 border-red-200',
  NORMAL: 'bg-blue-50 text-blue-600 border-blue-200',
  LOW: 'bg-gray-100 text-gray-500 border-gray-200',
};

function isOverdue(dueAt) {
  if (!dueAt) return false;
  return new Date(dueAt) < new Date();
}

export function MyTasksPage() {
  const { accessToken } = useAuth();
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [activeTab, setActiveTab] = useState('OPEN');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyIds, setBusyIds] = useState(new Set());
  const roleFilter = searchParams.get('role');

  const load = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await workflowService.getMyTasks(accessToken, activeTab);
      setTasks(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, activeTab]);

  useEffect(() => { load(); }, [load]);

  async function handleComplete(taskId) {
    setBusyIds((prev) => new Set([...prev, taskId]));
    try {
      await workflowService.completeTask(accessToken, taskId);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyIds((prev) => { const next = new Set(prev); next.delete(taskId); return next; });
    }
  }

  async function handleStart(taskId) {
    setBusyIds((prev) => new Set([...prev, taskId]));
    try {
      await workflowService.startTask(accessToken, taskId);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusyIds((prev) => { const next = new Set(prev); next.delete(taskId); return next; });
    }
  }

  const displayedTasks = useMemo(() => {
    if (!roleFilter) return tasks;
    return tasks.filter((task) => task.assigned_role === roleFilter);
  }, [roleFilter, tasks]);

  return (
    <div className="space-y-6">
      <PageHeader kicker="Workflow" title="My Tasks" description="Tasks assigned to your role or directly to you." />

      <div className="flex gap-2 border-b border-warelyn-border pb-1">
        {TABS.map((tab) => (
          <button
            className={`px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${activeTab === tab.key ? 'bg-warelyn-primary/10 text-warelyn-primary border-b-2 border-warelyn-primary' : 'text-warelyn-muted hover:text-warelyn-text'}`}
            key={tab.key ?? 'all'}
            onClick={() => setActiveTab(tab.key)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && <ErrorState description={error} />}
      {isLoading && <LoadingState />}

      {!isLoading && !error && displayedTasks.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <img alt="" className="mb-4 h-32 w-32 opacity-60" src={emptyStateIllustrations.overview} />
          <h3 className="text-lg font-semibold text-warelyn-text">No tasks found</h3>
          <p className="mt-1 text-sm text-warelyn-muted">
            {activeTab === 'OPEN' ? 'You have no open tasks right now.' : 'No tasks match this filter.'}
          </p>
        </div>
      )}

      {!isLoading && displayedTasks.length > 0 && (
        <div className="space-y-3">
          {displayedTasks.map((task) => (
            <div className="flex items-start gap-4 rounded-xl border border-warelyn-border bg-white p-4 shadow-sm transition-shadow hover:shadow-md" key={task.id}>
              <div className="mt-0.5 shrink-0">
                {task.status === 'COMPLETED' ? (
                  <CheckCircle2 className="text-emerald-500" size={20} />
                ) : (
                  <Inbox className="text-warelyn-primary" size={20} />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold text-warelyn-text truncate">{task.title}</h3>
                  <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.NORMAL}`}>
                    {task.priority}
                  </span>
                </div>
                {task.description && <p className="mt-1 text-sm text-warelyn-muted line-clamp-2">{task.description}</p>}
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-warelyn-muted">
                  <span>{task.entity_type.replace(/_/g, ' ')} #{task.entity_id}</span>
                  <StatusBadge status={task.status}>{task.status.replace(/_/g, ' ')}</StatusBadge>
                  <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600">{task.assigned_role.replace(/_/g, ' ')}</span>
                  <span className="inline-flex items-center gap-1"><Clock size={12} />{formatDateTime(task.created_at)}</span>
                  {task.due_at && (
                    <span className={`inline-flex items-center gap-1 ${isOverdue(task.due_at) ? 'font-semibold text-red-600' : ''}`}>
                      Due {formatDateTime(task.due_at)}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {task.action_url && (
                  <Link to={task.action_url}>
                    <Button size="sm" variant="secondary"><ExternalLink size={14} /> View</Button>
                  </Link>
                )}
                {task.status === 'OPEN' && (
                  <Button disabled={busyIds.has(task.id)} onClick={() => handleStart(task.id)} size="sm" variant="secondary">
                    <PlayCircle size={14} /> Start
                  </Button>
                )}
                {(task.status === 'OPEN' || task.status === 'IN_PROGRESS') && (
                  <Button disabled={busyIds.has(task.id)} onClick={() => handleComplete(task.id)} size="sm" variant="accent">
                    <CheckCircle2 size={14} /> Complete
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
