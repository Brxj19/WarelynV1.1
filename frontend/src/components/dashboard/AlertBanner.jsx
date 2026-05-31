import { X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

const toneMap = {
  danger: 'border-red-200 bg-red-50 text-red-700',
  warning: 'border-amber-200 bg-amber-50 text-amber-700',
  info: 'border-blue-200 bg-blue-50 text-blue-700',
};

function keyForAlert(sessionKey, title) {
  return `${sessionKey}:${title}`;
}

export function AlertBanner({ alerts = [], maxItems = 3, sessionKey }) {
  const [dismissed, setDismissed] = useState(() => new Set());

  useEffect(() => {
    if (!sessionKey) return;
    const next = new Set();
    alerts.forEach((alert) => {
      if (sessionStorage.getItem(keyForAlert(sessionKey, alert.title)) === 'dismissed') {
        next.add(alert.title);
      }
    });
    setDismissed(next);
  }, [alerts, sessionKey]);

  const visibleAlerts = useMemo(
    () => alerts.filter((alert) => !dismissed.has(alert.title)).slice(0, maxItems),
    [alerts, dismissed, maxItems],
  );

  if (!visibleAlerts.length) return null;

  function dismissAlert(title) {
    if (sessionKey) {
      sessionStorage.setItem(keyForAlert(sessionKey, title), 'dismissed');
    }
    setDismissed((prev) => new Set(prev).add(title));
  }

  return (
    <div className="sticky top-2 z-20 space-y-2">
      {visibleAlerts.map((alert) => (
        <div className={`flex items-start gap-3 rounded-lg border px-3 py-2 shadow-sm ${toneMap[alert.severity] ?? toneMap.info}`} key={alert.title}>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold">{alert.title}</p>
            <p className="text-xs">{alert.message}</p>
            {alert.action_url ? (
              <Link className="mt-1 inline-block text-xs font-semibold underline" to={alert.action_url}>
                Open
              </Link>
            ) : null}
          </div>
          <button
            className="rounded-md p-1 text-current/70 transition hover:bg-white/70 hover:text-current"
            onClick={() => dismissAlert(alert.title)}
            type="button"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
