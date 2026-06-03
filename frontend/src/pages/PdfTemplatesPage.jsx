import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Copy, Eye, FileText, Pencil, Plus, Trash2 } from 'lucide-react';

import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { EmptyState } from '../components/ui/EmptyState.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as documentService from '../services/documentService.js';

const TABS = [
  { id: 'INVOICE_PDF', label: 'Invoice PDF' },
  { id: 'BILL_PDF', label: 'Bill PDF' },
];

function FormatToolbar({ textareaRef, onBodyChange, body }) {
  function applyFormat(openTag, closeTag) {
    const el = textareaRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const selected = body.substring(start, end);
    const newBody = body.substring(0, start) + openTag + selected + closeTag + body.substring(end);
    onBodyChange(newBody);
    setTimeout(() => {
      el.selectionStart = start + openTag.length;
      el.selectionEnd = start + openTag.length + selected.length;
      el.focus();
    }, 0);
  }

  const tools = [
    { label: 'B', title: 'Bold', open: '<strong>', close: '</strong>', style: { fontWeight: 'bold' } },
    { label: 'I', title: 'Italic', open: '<em>', close: '</em>', style: { fontStyle: 'italic' } },
    { label: 'U', title: 'Underline', open: '<u>', close: '</u>', style: { textDecoration: 'underline' } },
    { label: 'S', title: 'Strikethrough', open: '<s>', close: '</s>', style: { textDecoration: 'line-through' } },
    { label: 'H1', title: 'Heading 1', open: '<h1>', close: '</h1>', style: { fontWeight: 'bold', fontSize: '14px' } },
    { label: 'H2', title: 'Heading 2', open: '<h2>', close: '</h2>', style: { fontWeight: 'bold', fontSize: '12px' } },
    { label: 'H3', title: 'Heading 3', open: '<h3>', close: '</h3>', style: { fontWeight: 'bold', fontSize: '11px' } },
    { label: 'P', title: 'Paragraph', open: '<p>', close: '</p>', style: {} },
    { label: 'Table', title: 'Table', open: '<table border="1" cellpadding="4" cellspacing="0">\n  <tr>\n    <th>', close: '</th>\n  </tr>\n  <tr>\n    <td></td>\n  </tr>\n</table>', style: { fontSize: '10px' } },
    { label: 'Div', title: 'Div', open: '<div style="">', close: '</div>', style: {} },
    { label: 'Img', title: 'Image', open: '<img src="', close: '" alt="" />', style: {} },
    { label: 'HR', title: 'Horizontal Rule', open: '<hr />', close: '', style: {} },
  ];

  return (
    <div className="flex flex-wrap items-center gap-1 border border-warelyn-border border-b-0 bg-gray-50 px-3 py-2 rounded-t-lg">
      {tools.map((tool) => (
        <button
          key={tool.label}
          type="button"
          title={tool.title}
          style={tool.style}
          className="px-2 py-1 text-sm rounded hover:bg-warelyn-border transition text-warelyn-text"
          onClick={() => applyFormat(tool.open, tool.close)}
        >
          {tool.label}
        </button>
      ))}
    </div>
  );
}

const VARIABLE_HELPERS = {
  INVOICE_PDF: [
    '{{invoice_number}}', '{{customer_name}}', '{{total}}', '{{due_date}}',
    '{{items}}', '{{tenant.company_name}}', '{{invoice_date}}', '{{subtotal}}',
    '{{tax_amount}}', '{{discount_amount}}', '{{notes}}', '{{tenant.logo_url}}',
    '{{currency_code}}', '{{currency_symbol}}',
  ],
  BILL_PDF: [
    '{{bill_number}}', '{{vendor_name}}', '{{total}}', '{{due_date}}',
    '{{items}}', '{{tenant.company_name}}', '{{bill_date}}', '{{subtotal}}',
    '{{tax_amount}}', '{{notes}}', '{{tenant.logo_url}}',
    '{{currency_code}}', '{{currency_symbol}}',
  ],
};

function TemplateCard({ template, onPreview, onDuplicate, onEdit, onDelete }) {
  const isSystem = !template.created_by_user_id;
  return (
    <div className="overflow-hidden rounded-xl border border-warelyn-border bg-white transition hover:shadow-md">
      <div className="relative h-44 overflow-hidden bg-gray-50">
        <iframe
          srcDoc={template.body_template}
          title={template.name}
          className="absolute top-0 left-0 border-0 pointer-events-none"
          style={{ width: '640px', height: '905px', transform: 'scale(0.25)', transformOrigin: 'top left' }}
        />
      </div>
      <div className="border-t border-warelyn-border p-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-semibold text-warelyn-text truncate">{template.name}</span>
          <div className="flex items-center gap-1.5 shrink-0">
            <Badge tone={isSystem ? 'info' : 'success'}>{isSystem ? 'System' : 'Custom'}</Badge>
            <Badge tone={template.is_active ? 'success' : 'neutral'}>{template.is_active ? 'Active' : 'Inactive'}</Badge>
          </div>
        </div>
        {template.description && (
          <p className="text-xs text-warelyn-muted line-clamp-2">{template.description}</p>
        )}
        {template.updated_at && (
          <p className="text-xs text-warelyn-muted">Updated: {new Date(template.updated_at).toLocaleDateString()}</p>
        )}
        <div className="flex items-center gap-1.5 pt-1">
          <button type="button" onClick={() => onPreview(template)} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-warelyn-muted hover:bg-slate-100 hover:text-warelyn-text transition" title="Preview">
            <Eye size={13} /> Preview
          </button>
          <button type="button" onClick={() => onDuplicate(template)} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-warelyn-muted hover:bg-slate-100 hover:text-warelyn-text transition" title="Duplicate">
            <Copy size={13} /> Duplicate
          </button>
          {!isSystem && (
            <>
              <button type="button" onClick={() => onEdit(template)} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-warelyn-muted hover:bg-slate-100 hover:text-warelyn-text transition" title="Edit">
                <Pencil size={13} /> Edit
              </button>
              <button type="button" onClick={() => onDelete(template)} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-red-400 hover:bg-red-50 hover:text-red-600 transition" title="Delete">
                <Trash2 size={13} /> Delete
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function TemplateEditor({ template, purpose, onSave, onCancel }) {
  const { accessToken } = useAuth();
  const toast = useToast();
  const bodyRef = useRef(null);
  const [form, setForm] = useState({
    name: template?.name ?? '',
    description: template?.description ?? '',
    body_template: template?.body_template ?? '',
  });
  const [saving, setSaving] = useState(false);
  const [variablesOpen, setVariablesOpen] = useState(false);

  const variables = VARIABLE_HELPERS[purpose] ?? [];

  function insertVariable(variable) {
    const el = bodyRef.current;
    if (!el) {
      setForm((p) => ({ ...p, body_template: p.body_template + variable }));
      return;
    }
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const value = el.value;
    const newValue = value.substring(0, start) + variable + value.substring(end);
    setForm((p) => ({ ...p, body_template: newValue }));
    setTimeout(() => {
      el.selectionStart = el.selectionEnd = start + variable.length;
      el.focus();
    }, 0);
  }

  async function handleSave() {
    if (!form.name.trim()) {
      toast.error('Template name is required.');
      return;
    }
    setSaving(true);
    try {
      if (template?.id) {
        await documentService.updateTemplate(accessToken, template.id, {
          name: form.name,
          description: form.description,
          body_template: form.body_template,
        });
      } else {
        await documentService.createTemplate(accessToken, {
          name: form.name,
          description: form.description,
          channel: 'PDF',
          purpose,
          body_template: form.body_template,
        });
      }
      toast.success('Template saved.');
      onSave();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDownloadPdf() {
    if (!template?.id) return;
    try {
      const blob = await documentService.previewTemplatePdf(accessToken, template.id, {});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'preview.pdf';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error(e.message);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={onCancel}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-warelyn-muted hover:text-warelyn-text transition"
      >
        <ArrowLeft size={16} />
        Back to Templates
      </button>

      <div className="page-header">
        <div>
          <p className="page-kicker">PDF Templates</p>
          <h1>{template?.id ? `Edit: ${template.name}` : 'Create Template'}</h1>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Template Name" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} />
            <Input label="Description" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
          </div>

          <div>
            <span className="mb-2 block text-sm font-medium text-warelyn-text">HTML Body</span>
            <FormatToolbar
              textareaRef={bodyRef}
              body={form.body_template}
              onBodyChange={(val) => setForm((p) => ({ ...p, body_template: val }))}
            />
            <textarea
              ref={bodyRef}
              className="block min-h-[400px] w-full rounded-lg rounded-t-none border border-warelyn-border bg-white px-3 py-2.5 font-mono text-xs text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
              value={form.body_template}
              onChange={(e) => setForm((p) => ({ ...p, body_template: e.target.value }))}
              rows={20}
            />
          </div>

          <div className="flex gap-2">
            <Button onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Template'}</Button>
            {template?.id && <Button variant="secondary" onClick={handleDownloadPdf}>Download PDF</Button>}
            <Button variant="ghost" onClick={onCancel}>Cancel</Button>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <span className="mb-2 block text-sm font-medium text-warelyn-text">Live Preview (A4)</span>
            <div className="flex justify-center">
              <div
                className="relative bg-white border border-warelyn-border shadow-lg"
                style={{ width: '100%', maxWidth: '360px', aspectRatio: '210/297', overflow: 'hidden' }}
              >
                <iframe
                  srcDoc={form.body_template}
                  title="PDF preview"
                  className="absolute top-0 left-0 border-0 pointer-events-none"
                  style={{ width: '792px', height: '1120px', transform: 'scale(0.45)', transformOrigin: 'top left' }}
                />
              </div>
            </div>
          </div>

          <div>
            <button
              className="text-sm font-medium text-warelyn-primary hover:underline"
              onClick={() => setVariablesOpen((v) => !v)}
              type="button"
            >
              {variablesOpen ? 'Hide' : 'Show'} Available Variables
            </button>
            {variablesOpen && (
              <div className="mt-2 rounded-lg border border-warelyn-border bg-slate-50 p-3">
                <ul className="space-y-1">
                  {variables.map((v) => (
                    <li key={v}>
                      <button
                        type="button"
                        className="text-xs font-mono text-warelyn-muted hover:text-warelyn-primary transition"
                        onClick={() => insertVariable(v)}
                      >
                        {v}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function PdfTemplatesPage() {
  const { accessToken } = useAuth();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('INVOICE_PDF');
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mode, setMode] = useState('list'); // list | edit | create
  const [selected, setSelected] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const data = await documentService.listTemplates(accessToken, 'PDF', activeTab);
      setTemplates(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [accessToken, activeTab]);

  function handlePreview(template) {
    setSelected(template);
    setMode('edit');
  }

  async function handleDuplicate(template) {
    const name = prompt('Name for the duplicate:', `${template.name} (Copy)`);
    if (!name) return;
    try {
      await documentService.duplicateTemplate(accessToken, template.id, name);
      toast.success('Template duplicated.');
      await load();
    } catch (e) {
      toast.error(e.message);
    }
  }

  function handleEdit(template) {
    setSelected(template);
    setMode('edit');
  }

  async function handleDelete(template) {
    setConfirmDelete(template);
  }

  async function confirmDeleteAction() {
    if (!confirmDelete) return;
    try {
      await documentService.deleteTemplate(accessToken, confirmDelete.id);
      toast.success('Template deleted.');
      setConfirmDelete(null);
      await load();
    } catch (e) {
      toast.error(e.message);
      setConfirmDelete(null);
    }
  }

  function handleCreate() {
    setSelected(null);
    setMode('create');
  }

  function handleEditorDone() {
    setMode('list');
    setSelected(null);
    load();
  }

  if (mode === 'edit' || mode === 'create') {
    return (
      <TemplateEditor
        template={selected}
        purpose={activeTab}
        onSave={handleEditorDone}
        onCancel={() => { setMode('list'); setSelected(null); }}
      />
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => window.history.back()}
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-warelyn-muted hover:text-warelyn-text transition"
      >
        <ArrowLeft size={16} />
        Back to Settings
      </button>

      <div className="page-header flex items-start justify-between">
        <div>
          <p className="page-kicker">Settings</p>
          <h1>PDF Templates</h1>
          <p>Invoice and bill PDF layouts.</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus size={16} className="mr-1" /> Create Template
        </Button>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-warelyn-border">
        <nav className="flex gap-6" aria-label="Template tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 text-sm font-medium transition border-b-2 -mb-px
                ${activeTab === tab.id
                  ? 'border-warelyn-primary text-warelyn-primary'
                  : 'border-transparent text-warelyn-muted hover:text-warelyn-text hover:border-warelyn-border'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading && <LoadingState message="Loading PDF templates..." />}
      {error && <ErrorState description={error} />}
      {!loading && !error && templates.length === 0 && (
        <EmptyState
          illustration={emptyStateIllustrations.templates}
          title="No PDF templates created yet"
          message="Duplicate a system template or create your own invoice and bill PDF layout."
          actionLabel="Create Template"
          onAction={handleCreate}
          size="default"
        />
      )}
      {!loading && !error && templates.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onPreview={handlePreview}
              onDuplicate={handleDuplicate}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Delete confirmation */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <h3 className="text-base font-semibold text-warelyn-text mb-2">Delete Template</h3>
            <p className="text-sm text-warelyn-muted mb-4">
              Are you sure you want to delete <span className="font-medium text-warelyn-text">{confirmDelete.name}</span>? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setConfirmDelete(null)}>Cancel</Button>
              <Button variant="primary" onClick={confirmDeleteAction} className="bg-red-600 hover:bg-red-700">Delete</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
