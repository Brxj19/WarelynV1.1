import { ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

export function CopilotReportBlock({ data }) {
  if (!data || !data.rows?.length) return null;

  const shown = data.rows.slice(0, 20);

  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-warelyn-border bg-white">
      <div className="flex items-center justify-between border-b border-warelyn-border bg-gray-50 px-3 py-2">
        <span className="text-xs font-semibold text-warelyn-text">{data.title}</span>
        {data.action_url && (
          <Link
            to={data.action_url}
            className="flex items-center gap-1 text-xs text-warelyn-primary hover:underline"
          >
            View full report <ExternalLink size={11} />
          </Link>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-warelyn-border bg-gray-50">
              {data.columns.map((column) => (
                <th
                  key={column}
                  className="whitespace-nowrap px-3 py-2 text-left font-medium text-warelyn-muted"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((row, index) => (
              <tr key={`${data.report_type}-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                {data.row_keys.map((key) => (
                  <td key={key} className="whitespace-nowrap px-3 py-1.5 text-warelyn-text">
                    {formatCell(row[key], key)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.total_rows > 20 && (
        <div className="border-t border-warelyn-border px-3 py-2 text-xs text-warelyn-muted">
          Showing top 20 of {data.total_rows} rows.{' '}
          <Link to={data.action_url} className="text-warelyn-primary hover:underline">
            View all →
          </Link>
        </div>
      )}

      {data.insights?.filter(Boolean).length > 0 && (
        <div className="border-t border-warelyn-border bg-blue-50/40 px-3 py-2">
          <p className="mb-1 text-xs font-medium text-warelyn-primary">Insights</p>
          <ul className="space-y-0.5">
            {data.insights.filter(Boolean).map((insight, index) => (
              <li key={`${data.report_type}-insight-${index}`} className="flex gap-1.5 text-xs text-warelyn-text">
                <span className="mt-0.5 text-warelyn-primary">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function formatCell(value, key) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'number') {
    if (key.includes('value') || key.includes('price')) {
      return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return value.toLocaleString();
  }
  return String(value);
}
