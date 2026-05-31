import { Download } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { CSVImportDropzone } from '../components/imports/CSVImportDropzone.jsx';
import { ImportPreviewTable } from '../components/imports/ImportPreviewTable.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { WorkflowProgress } from '../components/ui/WorkflowProgress.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import * as importService from '../services/importService.js';

const requiredColumns = ['name', 'sku', 'unit'];
const optionalColumns = ['barcode', 'description', 'category_name', 'brand_name', 'vendor_name', 'cost_price', 'selling_price', 'reorder_level', 'track_batch', 'track_expiry', 'track_serial', 'status'];

export function ProductImportPage() {
  const { accessToken } = useAuth();
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState('create_only');
  const [createMissing, setCreateMissing] = useState(false);
  const [job, setJob] = useState(null);
  const [rows, setRows] = useState([]);
  const [columnMapping, setColumnMapping] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState('');

  async function run(action) {
    setIsBusy(true);
    setError('');
    try {
      await action();
    } catch (actionError) {
      setError(actionError.message);
    } finally {
      setIsBusy(false);
    }
  }

  function upload() {
    if (!file) {
      setError('Choose a CSV file first.');
      return;
    }
    run(async () => {
      const response = await importService.uploadProductImport(accessToken, file, {
        mode,
        create_missing_references: createMissing,
        column_mapping_json: columnMapping.trim() || undefined,
      });
      setJob(response.job);
      setRows(await importService.listProductImportRows(accessToken, response.job.id));
    });
  }

  function validate() {
    run(async () => {
      const response = await importService.validateProductImport(accessToken, job.id);
      setJob(response.job);
      setRows(response.rows);
    });
  }

  function commit() {
    run(async () => {
      const response = await importService.commitProductImport(accessToken, job.id);
      setJob(response.job);
      setRows(response.rows);
    });
  }

  const canCommit = job && ['VALIDATED', 'HAS_ERRORS'].includes(job.status) && job.valid_rows > 0;

  return (
    <div className="space-y-6">
      <PageHeader backTo="/catalog/products" description="Upload product master data with preview and validation. This does not import or mutate stock." kicker="Catalog import" title="Import Products — CSV or XLSX" />
      {error ? <ErrorState description={error} /> : null}
      <WorkflowProgress
        current={job?.status === 'COMMITTED' ? 'COMMITTED' : job?.status === 'VALIDATED' || job?.status === 'HAS_ERRORS' ? 'VALIDATED' : job ? 'UPLOADED' : 'PENDING'}
        steps={[
          { key: 'PENDING', label: 'Upload' },
          { key: 'UPLOADED', label: 'Validate' },
          { key: 'VALIDATED', label: 'Preview' },
          { key: 'COMMITTED', label: 'Commit' },
        ]}
      />
      <Card>
        <CardHeader className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-warelyn-text">Import Template</h2>
            <p className="mt-1 text-sm text-warelyn-muted">Download the sample template to prepare bulk import rows in the correct format. Supported: .csv and .xlsx (Excel).</p>
          </div>
          <div className="flex gap-2">
            <a
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-warelyn-border bg-white px-4 py-2.5 text-sm font-semibold text-warelyn-text transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-300"
              download="products-import-sample.csv"
              href="/products-import-sample.csv"
            >
              <Download size={16} />
              <span>CSV Template</span>
            </a>
            <button
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-warelyn-border bg-white px-4 py-2.5 text-sm font-semibold text-warelyn-text transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-300"
              onClick={async () => {
                const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001/api';
                const res = await fetch(`${baseUrl}/imports/products/template.xlsx`, {
                  headers: { Authorization: `Bearer ${accessToken}` },
                });
                if (!res.ok) return;
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'products-import-template.xlsx';
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <Download size={16} />
              <span>XLSX Template</span>
            </button>
          </div>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <div><p className="text-sm font-semibold text-warelyn-text">Required</p><p className="mt-2 text-sm text-warelyn-muted">{requiredColumns.join(', ')}</p></div>
          <div><p className="text-sm font-semibold text-warelyn-text">Optional</p><p className="mt-2 text-sm text-warelyn-muted">{optionalColumns.join(', ')}</p></div>
        </CardBody>
      </Card>
      <Card>
        <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Upload</h2></CardHeader>
        <CardBody className="space-y-4">
          <CSVImportDropzone file={file} onFileChange={setFile} />
          <div className="grid gap-4 md:grid-cols-3">
            <label className="block text-sm font-medium text-warelyn-text">Mode
              <select className="mt-2 block w-full rounded-lg border border-warelyn-border px-3 py-2.5 text-sm" value={mode} onChange={(event) => setMode(event.target.value)}>
                <option value="create_only">Create only</option>
                <option value="update_existing">Update existing</option>
                <option value="upsert">Upsert</option>
              </select>
            </label>
            <label className="flex items-center gap-2 pt-7 text-sm font-medium text-warelyn-text">
              <input checked={createMissing} type="checkbox" onChange={(event) => setCreateMissing(event.target.checked)} />
              Create missing category, brand, vendor
            </label>
            <div className="flex items-end"><Button disabled={isBusy} onClick={upload}>{isBusy ? 'Working...' : 'Upload File'}</Button></div>
          </div>
          <div>
            <label className="block" htmlFor="column_mapping_json">
              <span className="mb-2 block text-sm font-medium text-warelyn-text">Column mapping JSON (optional)</span>
              <textarea
                className="block min-h-[120px] w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
                id="column_mapping_json"
                placeholder='{"Product Name":"name","Item Code":"sku"}'
                rows={4}
                value={columnMapping}
                onChange={(event) => setColumnMapping(event.target.value)}
              />
            </label>
            <p className="mt-2 text-xs text-warelyn-muted">Use this when your spreadsheet headers differ from Warelyn import columns. Keys are source headers and values are Warelyn target fields.</p>
          </div>
        </CardBody>
      </Card>
      {job ? (
        <Card>
          <CardHeader><h2 className="text-lg font-semibold text-warelyn-text">Import summary</h2></CardHeader>
          <CardBody className="space-y-4">
            <div className="grid gap-3 md:grid-cols-6">
              {['status', 'total_rows', 'valid_rows', 'error_rows', 'created_count', 'updated_count'].map((field) => <div key={field}><p className="text-xs uppercase text-warelyn-muted">{field.replaceAll('_', ' ')}</p><p className="font-semibold text-warelyn-text">{field === 'status' ? <StatusBadge status={job[field]}>{job[field]}</StatusBadge> : job[field]}</p></div>)}
            </div>
            <div className="flex gap-3"><Button disabled={isBusy || job.status === 'COMMITTED'} onClick={validate}>Validate</Button><Button disabled={isBusy || !canCommit} variant="accent" onClick={commit}>Commit valid rows</Button></div>
            {rows.length ? <ImportPreviewTable rows={rows} /> : null}
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
