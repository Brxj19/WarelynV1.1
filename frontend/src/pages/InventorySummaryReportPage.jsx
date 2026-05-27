import { Card, CardBody } from '../components/ui/Card.jsx';
import { BackButton } from '../components/ui/BackButton.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

export function InventorySummaryReportPage() {
  return (
    <SimpleReportPage
      title="Inventory summary"
      description="Backend-calculated inventory KPIs and exception counts."
      load={reportsService.getInventorySummary}
      columns={[]}
      loadRows={() => []}
      summary={(data) =>
        data ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(data).map(([key, value]) => (
              <Card key={key}>
                <CardBody>
                  <p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">
                    {key.replaceAll('_', ' ')}
                  </p>
                  <p className="mt-1 text-2xl font-bold text-warelyn-text">
                    {typeof value === 'object' ? String(value) : value}
                  </p>
                </CardBody>
              </Card>
            ))}
          </div>
        ) : null
      }
    />
  );
}
