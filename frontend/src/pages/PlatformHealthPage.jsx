import { CheckCircle2, Database, Server, XCircle } from 'lucide-react';
import { BackButton } from '../components/ui/BackButton.jsx';
import { useEffect, useState } from 'react';

import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { formatDate } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as adminService from '../services/adminService.js';

export function PlatformHealthPage() {
  const { accessToken } = useAuth();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    adminService.getPlatformHealth(accessToken).then(setHealth).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [accessToken]);

  if (loading) return <LoadingState message="Checking platform health..." />;
  if (error) return <ErrorState description={error} />;

  const dbOk = health?.database_status === 'connected';
  const appOk = health?.app_status === 'healthy';

  return (
    <div>
      <BackButton to="/admin" />
      <div className="page-header">
        <div>
          <p className="page-kicker">Super Admin</p>
          <h1>Platform Health</h1>
          <p>System status and connectivity checks.</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database size={18} className={dbOk ? 'text-emerald-600' : 'text-red-600'} />
              <h3 className="text-sm font-bold text-warelyn-text">Database</h3>
              {dbOk ? <CheckCircle2 size={16} className="text-emerald-500" /> : <XCircle size={16} className="text-red-500" />}
            </div>
          </CardHeader>
          <CardBody>
            <p className="text-sm text-warelyn-text">Status: <span className={dbOk ? 'font-medium text-emerald-600' : 'font-medium text-red-600'}>{health?.database_status ?? 'unknown'}</span></p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Server size={18} className={appOk ? 'text-emerald-600' : 'text-red-600'} />
              <h3 className="text-sm font-bold text-warelyn-text">Application</h3>
              {appOk ? <CheckCircle2 size={16} className="text-emerald-500" /> : <XCircle size={16} className="text-red-500" />}
            </div>
          </CardHeader>
          <CardBody>
            <p className="text-sm text-warelyn-text">Status: <span className={appOk ? 'font-medium text-emerald-600' : 'font-medium text-red-600'}>{health?.app_status ?? 'unknown'}</span></p>
          </CardBody>
        </Card>
      </div>

      <Card className="mt-6">
        <CardBody>
          <p className="text-xs text-warelyn-muted">Last checked: {formatDate(health?.timestamp)}</p>
        </CardBody>
      </Card>
    </div>
  );
}
