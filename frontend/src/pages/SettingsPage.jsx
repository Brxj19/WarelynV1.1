import { Bell, Building2, CheckCircle2, FileText, Globe, Home, LayoutList, Mail, Monitor, Moon, Palette, Smartphone, Sun, XCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge, StatusBadge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';
import { CurrencySelect } from '../components/ui/CurrencySelect.jsx';
import { ErrorState } from '../components/ui/ErrorState.jsx';
import { Input } from '../components/ui/Input.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { PhoneInput } from '../components/ui/PhoneInput.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useTenantSettings } from '../context/TenantSettingsContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import * as settingsService from '../services/settingsService.js';
import * as verificationService from '../services/verificationService.js';
import * as documentService from '../services/documentService.js';

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
    { label: 'P', title: 'Paragraph', open: '<p>', close: '</p>', style: {} },
    { label: 'A', title: 'Link', open: '<a href="">', close: '</a>', style: { color: '#2563eb', textDecoration: 'underline' } },
  ];

  return (
    <div className="flex items-center gap-1 border border-warelyn-border border-b-0 bg-gray-50 px-3 py-2 rounded-t-lg">
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

function TenantSettingsSection({ accessToken }) {
  const toast = useToast();
  const { refreshSettings } = useTenantSettings();
  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('company');
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [tplList, setTplList] = useState([]);
  const [tplEditing, setTplEditing] = useState(null);
  const [tplForm, setTplForm] = useState({ name: '', subject_template: '', body_template: '' });
  const tplBodyRef = useRef(null);

  const tenantSections = [
    { group: 'Organization', items: [{ id: 'company', icon: Building2, label: 'Company' }, { id: 'address', icon: Globe, label: 'Address' }] },
    { group: 'Operations', items: [{ id: 'inventory', icon: LayoutList, label: 'Inventory' }, { id: 'documents', icon: FileText, label: 'Documents' }] },
    { group: 'Templates', items: [{ id: 'email-templates', icon: Mail, label: 'Email' }, { id: 'pdf-templates', icon: FileText, label: 'PDF' }] },
  ];

  useEffect(() => {
    settingsService.getTenantSettings(accessToken)
      .then((data) => {
        setSettings(data);
        setForm({
          company_display_name: data?.company_display_name ?? '',
          contact_email: data?.contact_email ?? '',
          phone: data?.phone ?? '',
          address_line1: data?.address_line1 ?? '',
          address_line2: data?.address_line2 ?? '',
          city: data?.city ?? '',
          state: data?.state ?? '',
          country: data?.country ?? '',
          postal_code: data?.postal_code ?? '',
          timezone: data?.timezone ?? 'UTC',
          currency: data?.currency ?? 'USD',
          tax_id: data?.tax_id ?? '',
          over_receive_tolerance: data?.over_receive_tolerance ?? '',
          low_stock_alert_enabled: data?.low_stock_alert_enabled ?? true,
          document_logo_url: data?.document_logo_url ?? '',
          document_footer: data?.document_footer ?? '',
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

  function handleChange(field) {
    return (e) => setForm((p) => ({ ...p, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const data = {};
      for (const [key, value] of Object.entries(form)) {
        if (value !== (settings?.[key] ?? '')) data[key] = value;
      }
      if (Object.keys(data).length > 0) {
        const updated = await settingsService.updateTenantSettings(accessToken, data);
        setSettings(updated);
        refreshSettings();
        toast.success('Settings saved.');
      }
      setEditing(false);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function loadTemplates(channel) {
    try {
      const data = await documentService.listTemplates(accessToken, channel);
      setTplList(data);
    } catch { setTplList([]); }
  }

  useEffect(() => {
    if (activeSection === 'email-templates') loadTemplates('EMAIL');
    if (activeSection === 'pdf-templates') loadTemplates('PDF');
  }, [activeSection, accessToken]);

  function openTplEditor(template) {
    setTplEditing(template);
    setTplForm({ name: template.name, subject_template: template.subject_template ?? '', body_template: template.body_template ?? '' });
  }

  async function saveTpl() {
    if (!tplEditing) return;
    try {
      const payload = { name: tplForm.name, body_template: tplForm.body_template, is_active: true };
      if (tplEditing.channel === 'EMAIL') payload.subject_template = tplForm.subject_template;
      await documentService.updateTemplate(accessToken, tplEditing.id, payload);
      toast.success('Template saved.');
      setTplEditing(null);
      loadTemplates(tplEditing.channel);
    } catch (e) { toast.error(e.message); }
  }

  if (loading) return <LoadingState message="Loading tenant settings..." />;
  if (error) return <ErrorState description={error} />;

  function renderSection() {
    switch (activeSection) {
      case 'company':
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Company Profile</h3>
            <p className="text-sm text-warelyn-muted mb-4">Basic company information for this tenant.</p>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Company Display Name" value={form.company_display_name} onChange={handleChange('company_display_name')} disabled={!editing} />
              <Input label="Contact Email" type="email" value={form.contact_email} onChange={handleChange('contact_email')} disabled={!editing} />
              <PhoneInput label="Phone" value={form.phone} onChange={(val) => editing && setForm((p) => ({ ...p, phone: val }))} disabled={!editing} />
              <Input label="Timezone" value={form.timezone} onChange={handleChange('timezone')} disabled={!editing} />
              <CurrencySelect value={form.currency} onChange={(val) => setForm((p) => ({ ...p, currency: val }))} disabled={!editing} />
              <Input label="Tax ID" value={form.tax_id} onChange={handleChange('tax_id')} disabled={!editing} />
            </div>
          </div>
        );
      case 'address':
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Business Address</h3>
            <p className="text-sm text-warelyn-muted mb-4">Used on invoices and official documents.</p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2"><Input label="Address Line 1" value={form.address_line1} onChange={handleChange('address_line1')} disabled={!editing} /></div>
              <div className="sm:col-span-2"><Input label="Address Line 2" value={form.address_line2} onChange={handleChange('address_line2')} disabled={!editing} /></div>
              <Input label="City" value={form.city} onChange={handleChange('city')} disabled={!editing} />
              <Input label="State" value={form.state} onChange={handleChange('state')} disabled={!editing} />
              <Input label="Country" value={form.country} onChange={handleChange('country')} disabled={!editing} />
              <Input label="Postal Code" value={form.postal_code} onChange={handleChange('postal_code')} disabled={!editing} />
            </div>
          </div>
        );
      case 'inventory':
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Inventory Preferences</h3>
            <p className="text-sm text-warelyn-muted mb-4">Default inventory behavior for this tenant.</p>
            <div className="space-y-4">
              <Input label="Over-Receive Tolerance" value={form.over_receive_tolerance} onChange={handleChange('over_receive_tolerance')} helper="e.g. 10%" disabled={!editing} />
              <ToggleSwitch label="Low stock alerts" description="Get notified when products fall below reorder level" checked={form.low_stock_alert_enabled} onChange={(v) => editing && setForm((p) => ({ ...p, low_stock_alert_enabled: v }))} />
            </div>
          </div>
        );
      case 'documents':
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Document Settings</h3>
            <p className="text-sm text-warelyn-muted mb-4">Customize generated invoices and bills.</p>
            <div className="space-y-4">
              <Input label="Document Logo URL" value={form.document_logo_url} onChange={handleChange('document_logo_url')} helper="URL to your company logo" disabled={!editing} />
              <div>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Document Footer</span>
                  <textarea className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed" value={form.document_footer} onChange={handleChange('document_footer')} rows={3} disabled={!editing} />
                </label>
              </div>
            </div>
          </div>
        );
      case 'email-templates':
      case 'pdf-templates': {
        const isPdf = activeSection === 'pdf-templates';
        if (tplEditing && tplEditing.channel === (isPdf ? 'PDF' : 'EMAIL')) {
          return (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-warelyn-text">Edit: {tplEditing.name}</h3>
                <Button variant="ghost" size="sm" onClick={() => setTplEditing(null)}>Back to Gallery</Button>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-3">
                  <Input label="Template Name" value={tplForm.name} onChange={(e) => setTplForm((p) => ({ ...p, name: e.target.value }))} />
                  {!isPdf && <Input label="Subject" value={tplForm.subject_template} onChange={(e) => setTplForm((p) => ({ ...p, subject_template: e.target.value }))} />}
                  <div>
                    <span className="mb-2 block text-sm font-medium text-warelyn-text">HTML Source</span>
                    {!isPdf && <FormatToolbar textareaRef={tplBodyRef} body={tplForm.body_template} onBodyChange={(v) => setTplForm((p) => ({ ...p, body_template: v }))} />}
                    <textarea
                      ref={tplBodyRef}
                      className={`block min-h-[300px] w-full ${!isPdf ? 'rounded-b-lg rounded-t-none' : 'rounded-lg'} border border-warelyn-border bg-white px-3 py-2.5 font-mono text-xs text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10`}
                      value={tplForm.body_template}
                      onChange={(e) => setTplForm((p) => ({ ...p, body_template: e.target.value }))}
                    />
                  </div>
                  <Button onClick={saveTpl}>Save Template</Button>
                </div>
                <div>
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">{isPdf ? 'Live Preview (A4)' : 'Live Preview'}</span>
                  {isPdf ? (
                    <div className="flex justify-center">
                      <div
                        className="relative bg-white border border-warelyn-border shadow-lg"
                        style={{ width: '360px', height: '509px', overflow: 'hidden' }}
                      >
                        <iframe srcDoc={tplForm.body_template} title="Preview" className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: '720px', height: '1018px', transform: 'scale(0.5)', transformOrigin: 'top left' }} />
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-xl border border-warelyn-border bg-white overflow-hidden" style={{ height: '500px' }}>
                      <iframe srcDoc={tplForm.body_template} title="Preview" className="w-full h-full border-0" />
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        }
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">{isPdf ? 'PDF' : 'Email'} Templates</h3>
            <p className="text-sm text-warelyn-muted mb-4">{isPdf ? 'Invoice and bill PDF layouts.' : 'Email notification templates.'}</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {tplList.map((t) => (
                <div key={t.id} className="group relative cursor-pointer overflow-hidden rounded-xl border border-warelyn-border hover:shadow-lg transition" onClick={() => openTplEditor(t)}>
                  <div className="relative h-48 overflow-hidden bg-gray-50">
                    <iframe srcDoc={t.body_template} title={t.name} className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: isPdf ? '640px' : '560px', height: isPdf ? '905px' : '700px', transform: isPdf ? 'scale(0.25)' : 'scale(0.28)', transformOrigin: 'top left' }} />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition flex items-center justify-center">
                      <span className="opacity-0 group-hover:opacity-100 transition rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-warelyn-primary shadow">Edit Template</span>
                    </div>
                  </div>
                  <div className="p-2 border-t border-warelyn-border flex items-center justify-between">
                    <span className="text-xs font-semibold text-warelyn-text truncate">{t.name}</span>
                    <StatusBadge status={t.is_active ? 'ACTIVE' : 'INACTIVE'}>{t.is_active ? 'Active' : 'Off'}</StatusBadge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      }
      default:
        return null;
    }
  }

  return (
    <div className="space-y-4">
      <div className="mb-2">
        <h2 className="text-lg font-semibold text-warelyn-text">Tenant Settings</h2>
        <p className="text-sm text-warelyn-muted">Configure your organization's workspace.</p>
      </div>
      <div className="flex gap-6 rounded-xl border border-warelyn-border bg-white p-4">
        <nav className="w-52 shrink-0 space-y-4 border-r border-warelyn-border pr-4">
          {tenantSections.map((section) => (
            <div key={section.group}>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-warelyn-muted">{section.group}</p>
              {section.items.map((item) => (
                <button key={item.id} type="button" onClick={() => { setActiveSection(item.id); setTplEditing(null); }}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition
                    ${activeSection === item.id
                      ? 'bg-blue-50 text-warelyn-primary'
                      : 'text-warelyn-text hover:bg-slate-50'
                    }`}
                >
                  <item.icon size={16} />
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="flex-1 min-w-0">
          {renderSection()}
          {!['email-templates', 'pdf-templates'].includes(activeSection) && (
            <div className="mt-6 flex justify-end gap-2 border-t border-warelyn-border pt-4">
              {editing ? (
                <>
                  <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
                  <Button onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Settings'}</Button>
                </>
              ) : (
                <Button variant="secondary" onClick={() => setEditing(true)}>Edit Settings</Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function VerificationSection() {
  const { accessToken } = useAuth();
  const toast = useToast();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    verificationService.getVerificationStatus(accessToken).then(setStatus).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [accessToken]);

  if (loading) return <LoadingState message="Loading verification status..." />;
  if (error) return <ErrorState description={error} />;

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Mail size={16} className="text-warelyn-primary" />
            <h3 className="text-sm font-bold text-warelyn-text">Email</h3>
            {status?.email_verified ? <CheckCircle2 size={16} className="text-emerald-500" /> : <XCircle size={16} className="text-amber-500" />}
          </div>
        </CardHeader>
        <CardBody>
          <p className="mb-1 text-sm text-warelyn-text">{status?.email ?? '-'}</p>
          <Badge tone={status?.email_verified ? 'success' : 'warning'}>{status?.email_verified ? 'Verified' : 'Not verified'}</Badge>
          <div className="mt-4">
            <Link to="/verify-email">
              <Button size="sm" variant={status?.email_verified ? 'secondary' : 'primary'}>{status?.email_verified ? 'Re-verify' : 'Verify Now'}</Button>
            </Link>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Smartphone size={16} className="text-emerald-600" />
            <h3 className="text-sm font-bold text-warelyn-text">Phone</h3>
            {status?.phone_verified ? <CheckCircle2 size={16} className="text-emerald-500" /> : <XCircle size={16} className="text-amber-500" />}
          </div>
        </CardHeader>
        <CardBody>
          <p className="mb-1 text-sm text-warelyn-text">{status?.phone ?? '-'}</p>
          <Badge tone={status?.phone_verified ? 'success' : 'warning'}>{status?.phone_verified ? 'Verified' : 'Not verified'}</Badge>
          <div className="mt-4">
            {status?.phone ? (
              <Link to="/verify-phone">
                <Button size="sm" variant={status?.phone_verified ? 'secondary' : 'primary'}>{status?.phone_verified ? 'Re-verify' : 'Verify Now'}</Button>
              </Link>
            ) : (
              <p className="text-xs text-warelyn-muted">No phone number on file.</p>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function ThemeCard({ value, label, icon, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition w-32
        ${selected
          ? 'border-warelyn-primary bg-blue-50 text-warelyn-primary'
          : 'border-warelyn-border bg-white text-warelyn-muted hover:border-warelyn-primary/40'
        }`}
    >
      {icon}
      <span className="text-xs font-semibold">{label}</span>
      {selected && <div className="h-2 w-2 rounded-full bg-warelyn-primary" />}
    </button>
  );
}

function DensityToggle({ value, onChange }) {
  const options = [
    { id: 'compact', label: 'Compact', description: 'More rows visible' },
    { id: 'comfortable', label: 'Comfortable', description: 'Standard spacing' },
    { id: 'spacious', label: 'Spacious', description: 'Extra breathing room' },
  ];
  return (
    <div className="flex gap-2">
      {options.map((opt) => (
        <button key={opt.id} type="button" onClick={() => onChange(opt.id)}
          className={`flex-1 rounded-xl border-2 p-3 text-left transition
            ${value === opt.id
              ? 'border-warelyn-primary bg-blue-50'
              : 'border-warelyn-border bg-white hover:border-warelyn-primary/40'
            }`}
        >
          <p className={`text-sm font-semibold ${value === opt.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>
            {opt.label}
          </p>
          <p className="text-xs text-warelyn-muted mt-0.5">{opt.description}</p>
        </button>
      ))}
    </div>
  );
}

function ToggleSwitch({ label, description, checked, onChange }) {
  return (
    <div className="flex items-start justify-between py-4 border-b border-warelyn-border last:border-0">
      <div>
        <p className="text-sm font-semibold text-warelyn-text">{label}</p>
        <p className="text-xs text-warelyn-muted mt-0.5">{description}</p>
      </div>
      <button type="button" onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${checked ? 'bg-warelyn-primary' : 'bg-gray-200'}`}
      >
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform
          ${checked ? 'translate-x-6' : 'translate-x-1'}`}
        />
      </button>
    </div>
  );
}

function UserPreferencesSection({ accessToken }) {
  const toast = useToast();
  const { user } = useAuth();
  const canManageTemplateSettings = ['TENANT_ADMIN', 'INVENTORY_MANAGER'].includes(user?.role);
  const [prefs, setPrefs] = useState(null);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('display');
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);

  const prefSections = [
    { group: 'Appearance', items: [{ id: 'display', icon: Palette, label: 'Display' }] },
    { group: 'Workspace', items: [{ id: 'startup', icon: Home, label: 'Startup Page' }, { id: 'tables', icon: LayoutList, label: 'Table View' }] },
    { group: 'Notifications', items: [{ id: 'alerts', icon: Bell, label: 'Alerts' }] },
    ...(canManageTemplateSettings
      ? [{ group: 'Templates', items: [{ id: 'invoice-templates', icon: FileText, label: 'Invoice' }, { id: 'bill-templates', icon: FileText, label: 'Bill' }, { id: 'verification-templates', icon: Mail, label: 'Verification' }] }]
      : []),
  ];

  const [invoicePdfTemplates, setInvoicePdfTemplates] = useState([]);
  const [billPdfTemplates, setBillPdfTemplates] = useState([]);
  const [invoiceEmailTemplates, setInvoiceEmailTemplates] = useState([]);
  const [billEmailTemplates, setBillEmailTemplates] = useState([]);
  const [verificationTemplates, setVerificationTemplates] = useState([]);

  useEffect(() => {
    settingsService.getUserPreferences(accessToken)
      .then((data) => {
        setPrefs(data);
        setForm({
          default_landing_page: data?.default_landing_page ?? '/dashboard',
          table_density: data?.table_density ?? 'comfortable',
          theme_preference: data?.theme_preference ?? 'light',
          notification_email_enabled: data?.notification_email_enabled ?? true,
          notification_in_app_enabled: data?.notification_in_app_enabled ?? true,
          preferred_invoice_template_id: data?.preferred_invoice_template_id ?? null,
          preferred_bill_template_id: data?.preferred_bill_template_id ?? null,
          preferred_invoice_email_template_id: data?.preferred_invoice_email_template_id ?? null,
          preferred_bill_email_template_id: data?.preferred_bill_email_template_id ?? null,
          preferred_verification_template_id: data?.preferred_verification_template_id ?? null,
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    if (canManageTemplateSettings) {
      documentService.listTemplates(accessToken, 'PDF', 'INVOICE_PDF').then(setInvoicePdfTemplates).catch(() => {});
      documentService.listTemplates(accessToken, 'PDF', 'BILL_PDF').then(setBillPdfTemplates).catch(() => {});
      documentService.listTemplates(accessToken, 'EMAIL', 'INVOICE_EMAIL').then(setInvoiceEmailTemplates).catch(() => {});
      documentService.listTemplates(accessToken, 'EMAIL', 'BILL_EMAIL').then(setBillEmailTemplates).catch(() => {});
      documentService.listTemplates(accessToken, 'EMAIL', 'EMAIL_VERIFICATION').then(setVerificationTemplates).catch(() => {});
    }
  }, [accessToken, canManageTemplateSettings]);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await settingsService.updateUserPreferences(accessToken, form);
      setPrefs(updated);
      const pref = form.theme_preference ?? 'light';
      window.localStorage.setItem('warelyn.themePref', pref);
      if (pref === 'system') {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
      } else {
        document.documentElement.setAttribute('data-theme', pref);
      }
      document.documentElement.setAttribute('data-density', form.table_density ?? 'comfortable');
      setEditing(false);
      toast.success('Preferences saved.');
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState message="Loading preferences..." />;
  if (error) return <ErrorState description={error} />;

  const landingPages = [
    { value: '/dashboard', label: 'Dashboard', icon: Home },
    { value: '/reports/inventory-summary', label: 'Inventory Summary', icon: LayoutList },
    { value: '/warehouses', label: 'Warehouse Stock', icon: LayoutList },
    { value: '/sales', label: 'Sales Orders', icon: FileText },
    { value: '/purchases', label: 'Purchase Orders', icon: FileText },
  ];

  function renderSection() {
    switch (activeSection) {
      case 'display':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-semibold text-warelyn-text mb-1">Theme</h3>
              <p className="text-sm text-warelyn-muted mb-4">Choose your preferred color scheme.</p>
              <div className={`flex gap-3 ${!editing ? 'opacity-70 pointer-events-none' : ''}`}>
                <ThemeCard value="light" label="Light" icon={<Sun size={24} />} selected={form.theme_preference === 'light'} onClick={(v) => setForm((p) => ({ ...p, theme_preference: v }))} />
                <ThemeCard value="dark" label="Dark" icon={<Moon size={24} />} selected={form.theme_preference === 'dark'} onClick={(v) => setForm((p) => ({ ...p, theme_preference: v }))} />
                <ThemeCard value="system" label="System" icon={<Monitor size={24} />} selected={form.theme_preference === 'system'} onClick={(v) => setForm((p) => ({ ...p, theme_preference: v }))} />
              </div>
            </div>
          </div>
        );
      case 'startup':
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Default Landing Page</h3>
            <p className="text-sm text-warelyn-muted mb-4">Where you land after logging in.</p>
            <div className={`grid gap-2 ${!editing ? 'opacity-70 pointer-events-none' : ''}`}>
              {landingPages.map((page) => (
                <button key={page.value} type="button" onClick={() => setForm((p) => ({ ...p, default_landing_page: page.value }))}
                  className={`flex items-center gap-3 rounded-xl border-2 p-3 text-left transition
                    ${form.default_landing_page === page.value
                      ? 'border-warelyn-primary bg-blue-50'
                      : 'border-warelyn-border bg-white hover:border-warelyn-primary/40'
                    }`}
                >
                  <page.icon size={18} className={form.default_landing_page === page.value ? 'text-warelyn-primary' : 'text-warelyn-muted'} />
                  <span className={`text-sm font-medium ${form.default_landing_page === page.value ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>{page.label}</span>
                </button>
              ))}
            </div>
          </div>
        );
      case 'tables':
        return (
          <div className="space-y-4">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Table Density</h3>
            <p className="text-sm text-warelyn-muted mb-4">Control row spacing in data tables.</p>
            <div className={!editing ? 'opacity-70 pointer-events-none' : ''}>
              <DensityToggle value={form.table_density} onChange={(v) => setForm((p) => ({ ...p, table_density: v }))} />
            </div>
          </div>
        );
      case 'alerts':
        return (
          <div className="space-y-2">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Notification Preferences</h3>
            <p className="text-sm text-warelyn-muted mb-4">Control how you receive alerts.</p>
            <ToggleSwitch label="Email notifications" description="Receive alerts via email" checked={form.notification_email_enabled} onChange={(v) => editing && setForm((p) => ({ ...p, notification_email_enabled: v }))} />
            <ToggleSwitch label="In-app notifications" description="Show alerts inside Warelyn" checked={form.notification_in_app_enabled} onChange={(v) => editing && setForm((p) => ({ ...p, notification_in_app_enabled: v }))} />
          </div>
        );
      case 'invoice-templates':
        return (
          <div className="space-y-6">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Invoice Templates</h3>
            <p className="text-sm text-warelyn-muted mb-4">Choose your preferred templates for invoices.</p>
            {invoicePdfTemplates.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-warelyn-text mb-2">PDF Template</p>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {invoicePdfTemplates.map((t) => (
                    <button key={t.id} type="button" onClick={() => editing && setForm((p) => ({ ...p, preferred_invoice_template_id: t.id }))}
                      className={`rounded-xl border-2 overflow-hidden transition ${!editing ? 'opacity-70 cursor-default' : ''}
                        ${form.preferred_invoice_template_id === t.id ? 'border-warelyn-primary' : 'border-warelyn-border hover:border-warelyn-primary/40'}`}
                    >
                      <div className="relative h-32 overflow-hidden bg-gray-50">
                        <iframe srcDoc={t.body_template} title={t.name} className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: '640px', height: '905px', transform: 'scale(0.2)', transformOrigin: 'top left' }} />
                      </div>
                      <div className="p-2 text-center">
                        <span className={`text-xs font-semibold ${form.preferred_invoice_template_id === t.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>{t.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {invoiceEmailTemplates.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-warelyn-text mb-2">Email Template</p>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {invoiceEmailTemplates.map((t) => (
                    <button key={t.id} type="button" onClick={() => editing && setForm((p) => ({ ...p, preferred_invoice_email_template_id: t.id }))}
                      className={`rounded-xl border-2 overflow-hidden transition ${!editing ? 'opacity-70 cursor-default' : ''}
                        ${form.preferred_invoice_email_template_id === t.id ? 'border-warelyn-primary' : 'border-warelyn-border hover:border-warelyn-primary/40'}`}
                    >
                      <div className="relative h-32 overflow-hidden bg-gray-50">
                        <iframe srcDoc={t.body_template} title={t.name} className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: '560px', height: '700px', transform: 'scale(0.2)', transformOrigin: 'top left' }} />
                      </div>
                      <div className="p-2 text-center">
                        <span className={`text-xs font-semibold ${form.preferred_invoice_email_template_id === t.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>{t.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      case 'bill-templates':
        return (
          <div className="space-y-6">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Bill Templates</h3>
            <p className="text-sm text-warelyn-muted mb-4">Choose your preferred templates for bills.</p>
            {billPdfTemplates.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-warelyn-text mb-2">PDF Template</p>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {billPdfTemplates.map((t) => (
                    <button key={t.id} type="button" onClick={() => editing && setForm((p) => ({ ...p, preferred_bill_template_id: t.id }))}
                      className={`rounded-xl border-2 overflow-hidden transition ${!editing ? 'opacity-70 cursor-default' : ''}
                        ${form.preferred_bill_template_id === t.id ? 'border-warelyn-primary' : 'border-warelyn-border hover:border-warelyn-primary/40'}`}
                    >
                      <div className="relative h-32 overflow-hidden bg-gray-50">
                        <iframe srcDoc={t.body_template} title={t.name} className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: '640px', height: '905px', transform: 'scale(0.2)', transformOrigin: 'top left' }} />
                      </div>
                      <div className="p-2 text-center">
                        <span className={`text-xs font-semibold ${form.preferred_bill_template_id === t.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>{t.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {billEmailTemplates.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-warelyn-text mb-2">Email Template</p>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {billEmailTemplates.map((t) => (
                    <button key={t.id} type="button" onClick={() => editing && setForm((p) => ({ ...p, preferred_bill_email_template_id: t.id }))}
                      className={`rounded-xl border-2 overflow-hidden transition ${!editing ? 'opacity-70 cursor-default' : ''}
                        ${form.preferred_bill_email_template_id === t.id ? 'border-warelyn-primary' : 'border-warelyn-border hover:border-warelyn-primary/40'}`}
                    >
                      <div className="relative h-32 overflow-hidden bg-gray-50">
                        <iframe srcDoc={t.body_template} title={t.name} className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: '560px', height: '700px', transform: 'scale(0.2)', transformOrigin: 'top left' }} />
                      </div>
                      <div className="p-2 text-center">
                        <span className={`text-xs font-semibold ${form.preferred_bill_email_template_id === t.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>{t.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      case 'verification-templates':
        return (
          <div className="space-y-6">
            <h3 className="text-base font-semibold text-warelyn-text mb-1">Verification Templates</h3>
            <p className="text-sm text-warelyn-muted mb-4">Email template used for OTP verification codes.</p>
            {verificationTemplates.length > 0 ? (
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {verificationTemplates.map((t) => (
                  <button key={t.id} type="button" onClick={() => editing && setForm((p) => ({ ...p, preferred_verification_template_id: t.id }))}
                    className={`rounded-xl border-2 overflow-hidden transition ${!editing ? 'opacity-70 cursor-default' : ''}
                      ${form.preferred_verification_template_id === t.id ? 'border-warelyn-primary' : 'border-warelyn-border hover:border-warelyn-primary/40'}`}
                  >
                    <div className="relative h-32 overflow-hidden bg-gray-50">
                      <iframe srcDoc={t.body_template} title={t.name} className="absolute top-0 left-0 border-0 pointer-events-none" style={{ width: '560px', height: '700px', transform: 'scale(0.2)', transformOrigin: 'top left' }} />
                    </div>
                    <div className="p-2 text-center">
                      <span className={`text-xs font-semibold ${form.preferred_verification_template_id === t.id ? 'text-warelyn-primary' : 'text-warelyn-text'}`}>{t.name}</span>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-warelyn-muted">No verification templates configured.</p>
            )}
          </div>
        );
      default:
        return null;
    }
  }

  return (
    <div className="space-y-4">
      <div className="mb-2">
        <h2 className="text-lg font-semibold text-warelyn-text">My Preferences</h2>
        <p className="text-sm text-warelyn-muted">How Warelyn looks and behaves just for you.</p>
      </div>
      <div className="flex gap-6 rounded-xl border border-warelyn-border bg-white p-4">
        <nav className="w-52 shrink-0 space-y-4 border-r border-warelyn-border pr-4">
          {prefSections.map((section) => (
            <div key={section.group}>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-warelyn-muted">{section.group}</p>
              {section.items.map((item) => (
                <button key={item.id} type="button" onClick={() => setActiveSection(item.id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition
                    ${activeSection === item.id
                      ? 'bg-blue-50 text-warelyn-primary'
                      : 'text-warelyn-text hover:bg-slate-50'
                    }`}
                >
                  <item.icon size={16} />
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="flex-1 min-w-0">
          {renderSection()}
          <div className="mt-6 flex justify-end gap-2 border-t border-warelyn-border pt-4">
            {editing ? (
              <>
                <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
                <Button onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Preferences'}</Button>
              </>
            ) : (
              <Button variant="secondary" onClick={() => setEditing(true)}>Edit Preferences</Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function SettingsPage() {
  const { accessToken, user } = useAuth();
  const isAdmin = user?.role === 'TENANT_ADMIN';

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="page-kicker">Workspace</p>
          <h1>Settings</h1>
          <p>Manage your workspace and personal preferences.</p>
        </div>
      </div>

      <div className="space-y-8">
        {isAdmin && <TenantSettingsSection accessToken={accessToken} />}
        <UserPreferencesSection accessToken={accessToken} />
        <div>
          <div className="mb-2">
            <h2 className="text-lg font-semibold text-warelyn-text">Verification</h2>
            <p className="text-sm text-warelyn-muted">Verify your contact details.</p>
          </div>
          <VerificationSection />
        </div>
      </div>
    </div>
  );
}
