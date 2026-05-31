import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { ScreenToolbar } from '../components/ui/ScreenToolbar.jsx';
import { SortableHeader } from '../components/ui/SortableHeader.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { getNextSort, sortRows } from '../utils/table.js';
import { useAuth } from '../context/AuthContext.jsx';
import * as warehouseService from '../services/warehouseService.js';

const canWrite = new Set(['TENANT_ADMIN', 'INVENTORY_MANAGER']);

export function WarehouseDetailPage() {
  const { id } = useParams();
  const { accessToken, user } = useAuth();
  const [locations, setLocations] = useState([]);
  const [form, setForm] = useState({ name: '', code: '', barcode: '' });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortState, setSortState] = useState({ key: 'code', direction: 'asc' });
  const mayWrite = canWrite.has(user?.role);

  async function loadLocations() {
    setIsLoading(true);
    setError('');
    try {
      setLocations(await warehouseService.listWarehouseLocations(accessToken, id));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadLocations();
  }, [accessToken, id]);

  const filteredLocations = useMemo(
    () =>
      locations.filter((location) => {
        if (typeFilter !== 'ALL' && location.location_type !== typeFilter) return false;
        if (statusFilter !== 'ALL' && location.status !== statusFilter) return false;
        if (!search) return true;
        const value = search.toLowerCase();
        return `${location.name} ${location.code} ${location.barcode ?? ''}`.toLowerCase().includes(value);
      }),
    [locations, search, statusFilter, typeFilter],
  );
  const sortedLocations = useMemo(
    () =>
      sortRows(filteredLocations, sortState, {
        name: { type: 'text', accessor: (location) => location.name },
        code: { type: 'text', accessor: (location) => location.code },
        barcode: { type: 'text', accessor: (location) => location.barcode },
        location_type: { type: 'text', accessor: (location) => location.location_type },
        status: { type: 'text', accessor: (location) => location.status },
      }),
    [filteredLocations, sortState],
  );
  const activeFilters = [
    search ? { key: 'search', label: `Search: ${search}`, onRemove: () => setSearch('') } : null,
    typeFilter !== 'ALL' ? { key: 'type', label: `Type: ${typeFilter}`, onRemove: () => setTypeFilter('ALL') } : null,
    statusFilter !== 'ALL' ? { key: 'status', label: `Status: ${statusFilter}`, onRemove: () => setStatusFilter('ALL') } : null,
  ].filter(Boolean);
  const hasActiveFilters = activeFilters.length > 0;
  const locationTypes = Array.from(new Set(locations.map((location) => location.location_type).filter(Boolean))).sort();

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSaving(true);
    setError('');
    try {
      const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ''));
      await warehouseService.createWarehouseLocation(accessToken, id, payload);
      setForm({ name: '', code: '', barcode: '' });
      await loadLocations();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader backTo="/warehouses" description={`Configure bins and locations for warehouse #${id}. Location setup does not create stock balances.`} kicker="Warehouse setup" title="Warehouse locations" />
      {error ? <ErrorState description={error} /> : null}
      <div className="record-summary-grid">
        <Card className="record-summary-card"><CardBody><span>Warehouse</span><strong>#{id}</strong><small>Tenant-scoped master data</small></CardBody></Card>
        <Card className="record-summary-card"><CardBody><span>Location count</span><strong>{locations.length}</strong><small>Configured bins and zones</small></CardBody></Card>
        <Card className="record-summary-card"><CardBody><span>Active locations</span><strong>{locations.filter((row) => row.status === 'ACTIVE').length}</strong><small>Ready for workflow use</small></CardBody></Card>
      </div>
      {mayWrite ? (
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Create location</h2><p className="mt-1 text-sm text-warelyn-muted">Use receiving, storage, picking, packing, or return locations to structure warehouse operations.</p></CardHeader>
          <CardBody>
            <form className="grid gap-4 md:grid-cols-4" onSubmit={handleSubmit}>
              {['name', 'code', 'barcode'].map((field) => (
                <Input key={field} label={field[0].toUpperCase() + field.slice(1)} required={field !== 'barcode'} value={form[field]} onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))} />
              ))}
              <div className="flex items-end"><Button disabled={isSaving} type="submit">{isSaving ? 'Saving...' : 'Create'}</Button></div>
            </form>
          </CardBody>
        </Card>
      ) : null}
      {isLoading ? <LoadingState /> : (
        <TableShell
          description={`${sortedLocations.length} configured location(s)`}
          emptyDescription={hasActiveFilters ? 'Reset filters to review the full location list.' : 'Create receiving, storage, picking, or packing locations when your role allows it.'}
          emptyIllustration={hasActiveFilters ? emptyStateIllustrations.noResult : emptyStateIllustrations.warehouse}
          emptyTitle={hasActiveFilters ? 'No records match your filters' : 'No locations yet'}
          isEmpty={sortedLocations.length === 0}
          rowCount={sortedLocations.length}
          title="Locations"
          toolbar={
            <ScreenToolbar
              activeFilters={activeFilters}
              onReset={
                hasActiveFilters
                  ? () => {
                      setSearch('');
                      setTypeFilter('ALL');
                      setStatusFilter('ALL');
                    }
                  : undefined
              }
              onSearchChange={setSearch}
              searchPlaceholder="Search locations by code, name, or barcode"
              searchValue={search}
            >
              <div className="flex flex-wrap gap-2">
                <label className="block min-w-[160px]">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Location type</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                    onChange={(event) => setTypeFilter(event.target.value)}
                    value={typeFilter}
                  >
                    <option value="ALL">All types</option>
                    {locationTypes.map((locationType) => (
                      <option key={locationType} value={locationType}>
                        {locationType}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block min-w-[160px]">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Status</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                    onChange={(event) => setStatusFilter(event.target.value)}
                    value={statusFilter}
                  >
                    <option value="ALL">All statuses</option>
                    {Array.from(new Set(locations.map((location) => location.status).filter(Boolean))).sort().map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </ScreenToolbar>
          }
        >
          <table>
            <thead>
              <tr>
                <th><SortableHeader label="Name" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="name" sortState={sortState} /></th>
                <th><SortableHeader label="Code" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="code" sortState={sortState} /></th>
                <th><SortableHeader label="Barcode" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="barcode" sortState={sortState} /></th>
                <th><SortableHeader label="Type" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="location_type" sortState={sortState} /></th>
                <th><SortableHeader label="Status" onSort={(key) => setSortState((current) => getNextSort(current, key))} sortKey="status" sortState={sortState} /></th>
              </tr>
            </thead>
            <tbody>
              {sortedLocations.map((location) => (
                <tr key={location.id}>
                  <td className="font-semibold text-warelyn-text">{location.name}</td>
                  <td><span className="mono-cell">{location.code}</span></td>
                  <td><span className="mono-cell">{location.barcode ?? '-'}</span></td>
                  <td>{location.location_type}</td>
                  <td><StatusBadge status={location.status}>{location.status}</StatusBadge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableShell>
      )}
    </div>
  );
}
