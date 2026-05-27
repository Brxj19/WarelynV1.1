import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ActionMenu } from '../components/ui/ActionMenu.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { formatDecimal, formatMoney } from '../utils/formatters.js';
import { getNextSort, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER']);

export function MasterDataListPage({
  actions = null,
  customCellRender,
  description,
  emptyDescription = 'Create master data records when your role allows it.',
  emptyFilteredDescription,
  emptyFilteredTitle,
  emptyIllustration,
  emptyTitle,
  fields,
  kicker = 'Master data',
  listRecords,
  rowActions,
  rowLink = null,
  searchPlaceholder = '',
  tableTitle = 'Records',
  title,
}) {
  const { accessToken, user } = useAuth();
  const { currency } = useTenantSettings();
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortState, setSortState] = useState(() => ({
    key: fields[0]?.name ?? 'name',
    direction: 'asc',
  }));
  const mayWrite = canWrite.has(user?.role);

  async function loadRecords() {
    setIsLoading(true);
    setError('');
    try {
      setRecords(await listRecords(accessToken));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadRecords();
  }, [accessToken]);

  const hasStatusFilter = useMemo(
    () => records.some((record) => record.status && String(record.status).trim()),
    [records],
  );
  const sortDefinitions = useMemo(
    () =>
      Object.fromEntries([
        ...fields.map((field) => [field.name, { type: field.numeric || field.type === 'number' ? 'number' : 'text' }]),
        ['status', { type: 'text' }],
      ]),
    [fields],
  );
  const filteredRecords = useMemo(() => {
    const value = search.trim().toLowerCase();
    return records.filter((record) => {
      if (hasStatusFilter && statusFilter !== 'ALL' && record.status !== statusFilter) return false;
      if (!value) return true;
      return fields.some((field) => String(record[field.name] ?? '').toLowerCase().includes(value));
    });
  }, [fields, hasStatusFilter, records, search, statusFilter]);
  const visibleRecords = useMemo(
    () => sortRows(filteredRecords, sortState, sortDefinitions),
    [filteredRecords, sortDefinitions, sortState],
  );
  const activeFilters = [
    search
      ? {
          key: 'search',
          label: `Search: ${search}`,
          onRemove: () => setSearch(''),
        }
      : null,
    hasStatusFilter && statusFilter !== 'ALL'
      ? {
          key: 'status',
          label: `Status: ${statusFilter}`,
          onRemove: () => setStatusFilter('ALL'),
        }
      : null,
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;
  const statusOptions = Array.from(
    new Set(records.map((record) => record.status).filter(Boolean)),
  ).sort();

  const emptyTitleValue = hasActiveFilters ? (emptyFilteredTitle ?? 'No records match your filters') : emptyTitle ?? `No ${title.toLowerCase()} yet`;
  const emptyDescriptionValue = hasActiveFilters
    ? (emptyFilteredDescription ?? 'Reset filters to review the full record list.')
    : emptyDescription;

  return (
    <div className="space-y-6">
      <PageHeader kicker={kicker} title={title} description={description} actions={mayWrite ? actions : null} />
      <TableShell
        description={`${visibleRecords.length} record(s) in this view`}
        emptyDescription={emptyDescriptionValue}
        emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyIllustration}
        emptySecondaryActionLabel={hasActiveFilters ? 'Clear filters' : undefined}
        emptyTitle={emptyTitleValue}
        error={error}
        isEmpty={visibleRecords.length === 0}
        isLoading={isLoading}
        onEmptySecondaryAction={hasActiveFilters ? () => { setSearch(''); setStatusFilter('ALL'); } : undefined}
        rowCount={visibleRecords.length}
        title={tableTitle}
        toolbar={
          <ScreenToolbar
            activeFilters={activeFilters}
            onReset={
              hasActiveFilters
                ? () => {
                    setSearch('');
                    setStatusFilter('ALL');
                  }
                : undefined
            }
            onSearchChange={setSearch}
            searchPlaceholder={searchPlaceholder || `Search ${title.toLowerCase()}`}
            searchValue={search}
          >
            {hasStatusFilter ? (
              <label className="block min-w-[160px]">
                <span className="mb-2 block text-sm font-medium text-warelyn-text">Status</span>
                <select
                  className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                  onChange={(event) => setStatusFilter(event.target.value)}
                  value={statusFilter}
                >
                  <option value="ALL">All statuses</option>
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
          </ScreenToolbar>
        }
      >
        <table>
          <thead>
            <tr>
              {fields.map((field) => (
                <th className={field.numeric ? 'text-right' : ''} key={field.name}>
                  <SortableHeader
                    align={field.numeric ? 'right' : 'left'}
                    label={field.label}
                    onSort={(key) => setSortState((current) => getNextSort(current, key))}
                    sortKey={field.name}
                    sortState={sortState}
                  />
                </th>
              ))}
              <th>
                <SortableHeader
                  label="Status"
                  onSort={(key) => setSortState((current) => getNextSort(current, key))}
                  sortKey="status"
                  sortState={sortState}
                />
              </th>
              {rowLink || rowActions ? <th /> : null}
            </tr>
          </thead>
          <tbody>
            {visibleRecords.map((record) => {
              const menuItems = rowActions ? rowActions(record) : rowLink ? [{ label: 'View', onClick: () => navigate(rowLink(record)) }] : [];
              return (
                <tr key={record.id}>
                  {fields.map((field, index) => {
                    const content = customCellRender
                      ? customCellRender(record[field.name], field, record)
                      : renderCell(record[field.name], field, currency);
                    const rowUrl = index === 0 && rowLink ? rowLink(record) : null;
                    return (
                      <td className={field.numeric ? 'number-cell' : ''} key={field.name}>
                        {rowUrl ? (
                          <Link className="font-semibold text-warelyn-primary" to={rowUrl}>
                            {content}
                          </Link>
                        ) : (
                          content
                        )}
                      </td>
                    );
                  })}
                  <td><StatusBadge status={record.status ?? 'ACTIVE'}>{record.status ?? 'ACTIVE'}</StatusBadge></td>
                  {rowLink || rowActions ? (
                    <td className="text-right">
                      {menuItems.length ? <ActionMenu items={menuItems} /> : null}
                    </td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
      </TableShell>
    </div>
  );
}

export function MasterDataFormPage({
  backLabel,
  backTo,
  createRecord,
  customInputs = {},
  description,
  fields,
  helperText = 'Saving this form creates a master record only. It does not calculate or mutate inventory balances.',
  helperTitle = 'What happens next?',
  kicker = 'Master data',
  onSuccess,
  submitLabel = 'Create record',
  title,
  transformPayload,
}) {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(Object.fromEntries(fields.map((field) => [field.name, field.defaultValue ?? defaultValueForField(field)])));
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const rawPayload = Object.fromEntries(
        Object.entries(form).filter(([, value]) => value !== '' && value !== null && value !== undefined),
      );
      const payload = transformPayload ? transformPayload(rawPayload) : rawPayload;
      const record = await createRecord(accessToken, payload);
      if (typeof onSuccess === 'function') {
        onSuccess(record);
      } else if (typeof onSuccess === 'string') {
        navigate(onSuccess);
      } else if (backTo) {
        navigate(backTo);
      }
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader backLabel={backLabel} backTo={backTo} kicker={kicker} title={title} description={description} />
      {error ? <ErrorState description={error} /> : null}
      <form className="space-y-6" onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-warelyn-text">Create record</h2>
          </CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            {fields.map((field) => {
              const FieldInput = customInputs[field.name] ?? Input;
              return (
                <FieldInput
                  key={field.name}
                  helper={field.helper}
                  label={field.label}
                  min={field.min}
                  name={field.name}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      [field.name]: field.type === 'checkbox' ? event.target.checked : event.target.value,
                    }))
                  }
                  required={field.required}
                  step={field.step}
                  type={field.type ?? 'text'}
                  value={form[field.name]}
                />
              );
            })}
          </CardBody>
        </Card>

        <div className="sticky-form-footer">
          <div className="workflow-helper-panel max-w-xl">
            <h3>{helperTitle}</h3>
            <p>{helperText}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {backTo ? (
              <Button onClick={() => navigate(backTo)} type="button" variant="ghost">
                Cancel
              </Button>
            ) : null}
            <Button isLoading={isSaving} type="submit">
              {submitLabel}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}

function defaultValueForField(field) {
  return field.type === 'checkbox' ? false : '';
}

function renderCell(value, field, currency) {
  if (value === null || value === undefined || value === '') return '-';
  if (['sku', 'barcode', 'gst_number', 'code'].includes(field.name)) return <span className="mono-cell">{value}</span>;
  if (field.name === 'reorder_level') return formatDecimal(value);
  if (field.money) return formatMoney(value, currency);
  return value;
}
