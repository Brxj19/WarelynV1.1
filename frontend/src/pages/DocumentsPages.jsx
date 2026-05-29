import { Download, Mail, Receipt, Stamp } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { RecordDetailShell } from '../components/ui/RecordDetailShell.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDate, formatMoney } from '../utils/formatters.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import * as documentService from '../services/documentService.js';

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function InvoicesPage() {
  const { accessToken } = useAuth();
  const { currency } = useTenantSettings();
  const [invoices, setInvoices] = useState([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    documentService.listInvoices(accessToken).then(setInvoices).catch((e) => setError(e.message)).finally(() => setIsLoading(false));
  }, [accessToken]);

  const rows = useMemo(() => {
    const value = search.trim().toLowerCase();
    if (!value) return invoices;
    return invoices.filter((invoice) => `${invoice.invoice_number} ${invoice.status} ${invoice.customer_id}`.toLowerCase().includes(value));
  }, [invoices, search]);

  return (
    <div className="space-y-6">
      <PageHeader kicker="Documents" title="Invoices" description="Customer-facing invoice records generated from committed sales workflow context." />
      <TableShell
        description={`${rows.length} invoice(s) in view`}
        emptyDescription={search ? 'Adjust your customer, status, date, or invoice number filters.' : 'Create your first invoice to start tracking customer payments.'}
        emptyIllustration={search ? emptyStateIllustrations.noResult : emptyStateIllustrations.sales}
        emptySecondaryActionLabel={search ? 'Clear filters' : undefined}
        emptyTitle={search ? 'No matching invoices found' : 'No invoices created yet'}
        error={error}
        isEmpty={rows.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={search ? () => setSearch('') : undefined}
        rowCount={rows.length}
        title="Invoice records"
        toolbar={<ScreenToolbar onSearchChange={setSearch} searchPlaceholder="Search invoice number or status" searchValue={search} />}
      >
        <table>
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Status</th>
              <th>Issue date</th>
              <th>Due date</th>
              <th className="text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((invoice) => (
              <tr key={invoice.id}>
                <td>
                  <Link className="font-semibold text-warelyn-primary" to={`/invoices/${invoice.id}`}>
                    {invoice.invoice_number}
                  </Link>
                </td>
                <td><StatusBadge status={invoice.status}>{invoice.status}</StatusBadge></td>
                <td>{formatDate(invoice.issue_date)}</td>
                <td>{invoice.due_date ? formatDate(invoice.due_date) : '-'}</td>
                <td className="number-cell">{formatMoney(invoice.total_amount, currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function InvoiceDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [invoice, setInvoice] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const mayWrite = user?.role !== 'VIEWER';

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      setInvoice(await documentService.getInvoice(accessToken, id));
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  async function run(action) {
    setIsBusy(true);
    setError('');
    try {
      await action();
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsBusy(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!invoice) return <ErrorState description={error || 'Invoice not found.'} />;

  return (
    <div className="space-y-6">
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            <Button disabled={isBusy} variant="secondary" onClick={() => run(async () => saveBlob(await documentService.downloadInvoicePdf(accessToken, id), `${invoice.invoice_number}.pdf`))}>
              <Download size={16} />
              PDF
            </Button>
            {mayWrite && invoice.status !== 'PAID' && (
              <Button disabled={isBusy} variant="secondary" onClick={() => run(() => documentService.sendInvoice(accessToken, id))}>
                <Mail size={16} />
                Send
              </Button>
            )}
            {mayWrite && invoice.status !== 'PAID' && (
              <Button disabled={isBusy} variant="accent" onClick={() => run(() => documentService.markInvoicePaid(accessToken, id))}>
                <Stamp size={16} />
                Mark paid
              </Button>
            )}
          </div>
        }
        backTo="/invoices"
        description="PDF output and email delivery use tenant templates and branding settings."
        kicker="Invoice"
        meta={[
          { label: 'Sales order', value: invoice.sales_order_id ? `#${invoice.sales_order_id}` : '-' },
          { label: 'Fulfillment', value: invoice.fulfillment_id ? `#${invoice.fulfillment_id}` : '-' },
          { label: 'Customer', value: `#${invoice.customer_id}` },
        ]}
        status={<StatusBadge status={invoice.status}>{invoice.status}</StatusBadge>}
        summary={[
          { label: 'Lines', value: invoice.items.length, helper: 'Billed item count' },
          { label: 'Subtotal', value: formatMoney(invoice.subtotal_amount, invoice.currency || 'USD'), helper: 'Before tax/discount' },
          { label: 'Total', value: formatMoney(invoice.total_amount, invoice.currency || 'USD'), helper: 'Document total' },
        ]}
        title={invoice.invoice_number}
      >
        <TableShell description="Invoice line items" isEmpty={invoice.items.length === 0} rowCount={invoice.items.length} title="Items">
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Unit price</th>
                <th className="text-right">Line total</th>
              </tr>
            </thead>
            <tbody>
              {invoice.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.description}</td>
                  <td className="number-cell">{item.quantity}</td>
                  <td className="number-cell">{formatMoney(item.unit_price, invoice.currency || 'USD')}</td>
                  <td className="number-cell">{formatMoney(item.line_total, invoice.currency || 'USD')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      </RecordDetailShell>
    </div>
  );
}

export function BillsPage() {
  const { accessToken } = useAuth();
  const { currency } = useTenantSettings();
  const [bills, setBills] = useState([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    documentService.listBills(accessToken).then(setBills).catch((e) => setError(e.message)).finally(() => setIsLoading(false));
  }, [accessToken]);

  const rows = useMemo(() => {
    const value = search.trim().toLowerCase();
    if (!value) return bills;
    return bills.filter((bill) => `${bill.bill_number} ${bill.status} ${bill.vendor_id}`.toLowerCase().includes(value));
  }, [bills, search]);

  return (
    <div className="space-y-6">
      <PageHeader kicker="Documents" title="Bills" description="Vendor-facing payable documents linked back to purchase orders and receipts." />
      <TableShell
        description={`${rows.length} bill(s) in view`}
        emptyDescription={search ? 'Adjust your supplier, status, date, or bill number filters.' : 'Record supplier bills to track payables and purchase expenses.'}
        emptyIllustration={search ? emptyStateIllustrations.noResult : emptyStateIllustrations.billings}
        emptySecondaryActionLabel={search ? 'Clear filters' : undefined}
        emptyTitle={search ? 'No matching bills found' : 'No bills recorded yet'}
        error={error}
        isEmpty={rows.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={search ? () => setSearch('') : undefined}
        rowCount={rows.length}
        title="Bill records"
        toolbar={<ScreenToolbar onSearchChange={setSearch} searchPlaceholder="Search bill number or status" searchValue={search} />}
      >
        <table>
          <thead>
            <tr>
              <th>Bill</th>
              <th>Status</th>
              <th>Issue date</th>
              <th>Due date</th>
              <th className="text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((bill) => (
              <tr key={bill.id}>
                <td>
                  <Link className="font-semibold text-warelyn-primary" to={`/bills/${bill.id}`}>
                    {bill.bill_number}
                  </Link>
                </td>
                <td><StatusBadge status={bill.status}>{bill.status}</StatusBadge></td>
                <td>{formatDate(bill.issue_date)}</td>
                <td>{bill.due_date ? formatDate(bill.due_date) : '-'}</td>
                <td className="number-cell">{formatMoney(bill.total_amount, currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function BillDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [bill, setBill] = useState(null);
  const mayWrite = user?.role !== 'VIEWER';
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);

  async function load() {
    setIsLoading(true);
    setError('');
    try {
      setBill(await documentService.getBill(accessToken, id));
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [accessToken, id]);

  async function run(action) {
    setIsBusy(true);
    setError('');
    try {
      await action();
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsBusy(false);
    }
  }

  if (isLoading) return <LoadingState />;
  if (!bill) return <ErrorState description={error || 'Bill not found.'} />;

  return (
    <div className="space-y-6">
      {error ? <ErrorState description={error} /> : null}
      <RecordDetailShell
        actions={
          <div className="flex flex-wrap gap-2">
            <Button disabled={isBusy} variant="secondary" onClick={() => run(async () => saveBlob(await documentService.downloadBillPdf(accessToken, id), `${bill.bill_number}.pdf`))}>
              <Download size={16} />
              PDF
            </Button>
            {mayWrite && bill.status !== 'PAID' && (
              <Button disabled={isBusy} variant="secondary" onClick={() => run(() => documentService.sendBill(accessToken, id))}>
                <Mail size={16} />
                Send
              </Button>
            )}
            {mayWrite && bill.status !== 'PAID' && (
              <Button disabled={isBusy} variant="accent" onClick={() => run(() => documentService.markBillPaid(accessToken, id))}>
                <Receipt size={16} />
                Mark paid
              </Button>
            )}
          </div>
        }
        backTo="/bills"
        description="Bills reuse the same template and PDF foundation as invoices, with vendor-specific document context."
        kicker="Bill"
        meta={[
          { label: 'Purchase order', value: bill.purchase_order_id ? `#${bill.purchase_order_id}` : '-' },
          { label: 'Receipt', value: bill.receipt_id ? `#${bill.receipt_id}` : '-' },
          { label: 'Vendor', value: `#${bill.vendor_id}` },
        ]}
        status={<StatusBadge status={bill.status}>{bill.status}</StatusBadge>}
        summary={[
          { label: 'Lines', value: bill.items.length, helper: 'Billed item count' },
          { label: 'Subtotal', value: formatMoney(bill.subtotal_amount, bill.currency || 'USD'), helper: 'Before tax/discount' },
          { label: 'Total', value: formatMoney(bill.total_amount, bill.currency || 'USD'), helper: 'Document total' },
        ]}
        title={bill.bill_number}
      >
        <TableShell description="Bill line items" isEmpty={bill.items.length === 0} rowCount={bill.items.length} title="Items">
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Unit cost</th>
                <th className="text-right">Line total</th>
              </tr>
            </thead>
            <tbody>
              {bill.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.description}</td>
                  <td className="number-cell">{item.quantity}</td>
                  <td className="number-cell">{formatMoney(item.unit_cost, bill.currency || 'USD')}</td>
                  <td className="number-cell">{formatMoney(item.line_total, bill.currency || 'USD')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      </RecordDetailShell>
    </div>
  );
}
