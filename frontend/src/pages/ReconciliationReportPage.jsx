import { Badge } from '../components/ui/Badge.jsx';
import { Card, CardBody } from '../components/ui/Card.jsx';
import * as reportsService from '../services/reportsService.js';
import { SimpleReportPage } from './ReportsPage.jsx';

const columns = [{ key: 'product_name', label: 'Product' }, { key: 'sku', label: 'SKU' }, { key: 'warehouse_name', label: 'Warehouse' }, { key: 'location_name', label: 'Location' }, { key: 'expected_on_hand', label: 'Expected OH' }, { key: 'actual_on_hand', label: 'Actual OH' }, { key: 'expected_reserved', label: 'Expected Res' }, { key: 'actual_reserved', label: 'Actual Res' }, { key: 'expected_available', label: 'Expected Avail' }, { key: 'actual_available', label: 'Actual Avail' }];

export function ReconciliationReportPage() {
  return <SimpleReportPage title="Reconciliation" description="Read-only ledger-to-projection mismatch report." load={reportsService.getReconciliation} columns={columns} loadRows={(data) => data?.mismatches ?? []} summary={(data) => <Card><CardBody className="flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-wide text-warelyn-muted">Mismatch count</p><p className="mt-1 text-2xl font-bold text-warelyn-text">{data?.mismatch_count ?? 0}</p></div><Badge tone={data?.mismatch_count ? 'danger' : 'success'}>{data?.mismatch_count ? 'Needs review' : 'Clean'}</Badge></CardBody></Card>} />;
}
