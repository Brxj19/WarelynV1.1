import { Search } from 'lucide-react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { MetadataDrawer } from '../components/MetadataDrawer.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as auditService from '../services/auditService.js';

const actionTones = {
  STOCK_IN: 'success',
  STOCK_OUT: 'danger',
  STOCK_ADJUST: 'warning',
  STOCK_RESERVE: 'primary',
  STOCK_RELEASE: 'primary',
  STOCK_DEDUCT: 'success',
  STOCK_TRANSFER: 'warning',
  RETURN_RESTOCK: 'success',
  RETURN_BLOCKED: 'warning',
  RETURN_DAMAGED: 'danger',
  RETURN_SCRAP: 'danger',
  TENANT_ENABLE: 'success',
  TENANT_DISABLE: 'danger',
  SETTINGS_UPDATE: 'primary',
  PREFERENCES_UPDATE: 'neutral',
};

export function AuditLogsPage() {
  const { accessToken, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMeta, setSelectedMeta] = useState(null);
  const [actionFilter, setActionFilter] = useState(searchParams.get('action') ?? '');
  const [entityFilter, setEntityFilter] = useState(searchParams.get('entity_type') ?? '');

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (actionFilter) params.action = actionFilter;
      if (entityFilter) params.entity_type = entityFilter;
      setSearchParams(params, { replace: true });
      const data = await auditService.listAuditLogs(accessToken, actionFilter ? { action: actionFilter } : entityFilter ? { entityType: entityFilter } : {});
      setLogs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [accessToken, actionFilter, entityFilter, setSearchParams]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const uniqueActions = [...new Set(logs.map((l) => l.action))];
  const uniqueEntities = [...new Set(logs.map((l) => l.entity_type).filter(Boolean))];

  return (
    <div>
      <BackButton to="/admin" />
      <div className="page-header">
        <div>
          <p className="page-kicker">Super Admin</p>
          <h1>Audit Logs</h1>
          <p>Platform-wide activity and inventory mutation history.</p>
        </div>
      </div>

      <TableShell error={error} isLoading={loading} isEmpty={logs.length === 0} title="Audit Events" rowCount={logs.length}
        emptyIllustration={(actionFilter || entityFilter) ? emptyStateIllustrations.noResult : emptyStateIllustrations.data}
        emptyTitle={(actionFilter || entityFilter) ? 'No matching results found' : 'No audit logs yet'}
        emptyDescription={(actionFilter || entityFilter) ? 'Try changing your search keyword or clearing filters.' : 'Audit events will appear after platform activity is recorded.'}
        emptySecondaryActionLabel={(actionFilter || entityFilter) ? 'Clear filters' : undefined}
        onEmptySecondaryAction={(actionFilter || entityFilter) ? () => { setActionFilter(''); setEntityFilter(''); } : undefined}
        toolbar={
          <div className="flex gap-3">
            <select className="rounded-lg border border-warelyn-border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
              <option value="">All actions</option>
              {uniqueActions.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
            <select className="rounded-lg border border-warelyn-border bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10" value={entityFilter} onChange={(e) => setEntityFilter(e.target.value)}>
              <option value="">All entities</option>
              {uniqueEntities.map((e) => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
        }
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-warelyn-border text-left text-xs font-semibold uppercase tracking-wide text-warelyn-muted">
              <th className="py-3 pl-4 pr-2">Action</th>
              <th className="px-2 py-3">Entity</th>
              <th className="px-2 py-3">Actor</th>
              <th className="px-2 py-3">Role</th>
              <th className="px-2 py-3">Timestamp</th>
              <th className="px-2 py-3">Metadata</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr className="border-b border-warelyn-border last:border-0 hover:bg-slate-50" key={log.id}>
                <td className="py-3 pl-4 pr-2">
                  <Badge tone={actionTones[log.action] ?? 'neutral'}>{log.action}</Badge>
                </td>
                <td className="px-2 py-3 text-warelyn-muted">{log.entity_type ?? '-'}</td>
                <td className="px-2 py-3 font-medium">{log.actor_user_id ? `User #${log.actor_user_id}` : '-'}</td>
                <td className="px-2 py-3 text-warelyn-muted">{log.actor_role ?? '-'}</td>
                <td className="px-2 py-3 text-warelyn-muted">{formatDate(log.created_at)}</td>
                <td className="px-2 py-3">
                  {log.metadata_json ? (
                    <button className="text-xs font-medium text-warelyn-primary hover:underline" onClick={() => setSelectedMeta(log)} type="button">View Metadata</button>
                  ) : <span className="text-warelyn-muted">-</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>

      <MetadataDrawer
        data={selectedMeta?.metadata_json}
        onClose={() => setSelectedMeta(null)}
        open={!!selectedMeta}
      />
    </div>
  );
}
