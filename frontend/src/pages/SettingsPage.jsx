import { Bell, Building2, CheckCircle2, FileText, Globe, Home, LayoutList, Mail, Monitor, Moon, Palette, Smartphone, Sun, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
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

function resolveUploadUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path) || path.startsWith('data:')) return path;
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
  return `${base.replace(/\/api$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
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
  const [invoicePdfTemplates, setInvoicePdfTemplates] = useState([]);
  const [billPdfTemplates, setBillPdfTemplates] = useState([]);
  const [invoiceEmailTemplates, setInvoiceEmailTemplates] = useState([]);
  const [billEmailTemplates, setBillEmailTemplates] = useState([]);
  const [verificationTemplates, setVerificationTemplates] = useState([]);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [logoUploadError, setLogoUploadError] = useState('');

  const tenantSections = [
    { group: 'Organization', items: [{ id: 'company', icon: Building2, label: 'Company' }, { id: 'address', icon: Globe, label: 'Address' }] },
    { group: 'Operations', items: [{ id: 'inventory', icon: LayoutList, label: 'Inventory' }, { id: 'documents', icon: FileText, label: 'Documents' }] },
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
          preferred_invoice_template_id: data?.preferred_invoice_template_id ? String(data.preferred_invoice_template_id) : '',
          preferred_bill_template_id: data?.preferred_bill_template_id ? String(data.preferred_bill_template_id) : '',
          preferred_invoice_email_template_id: data?.preferred_invoice_email_template_id ? String(data.preferred_invoice_email_template_id) : '',
          preferred_bill_email_template_id: data?.preferred_bill_email_template_id ? String(data.preferred_bill_email_template_id) : '',
          preferred_verification_template_id: data?.preferred_verification_template_id ? String(data.preferred_verification_template_id) : '',
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

    documentService.listTemplates(accessToken, 'PDF', 'INVOICE_PDF').then(setInvoicePdfTemplates).catch(() => {});
    documentService.listTemplates(accessToken, 'PDF', 'BILL_PDF').then(setBillPdfTemplates).catch(() => {});
    documentService.listTemplates(accessToken, 'EMAIL', 'INVOICE_EMAIL').then(setInvoiceEmailTemplates).catch(() => {});
    documentService.listTemplates(accessToken, 'EMAIL', 'BILL_EMAIL').then(setBillEmailTemplates).catch(() => {});
    documentService.listTemplates(accessToken, 'EMAIL', 'EMAIL_VERIFICATION').then(setVerificationTemplates).catch(() => {});
  }, [accessToken]);

  function handleChange(field) {
    return (e) => setForm((p) => ({ ...p, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));
  }

  async function handleLogoUpload(file) {
    if (!file || !editing) return;
    setIsUploadingLogo(true);
    setLogoUploadError('');
    try {
      const { url } = await settingsService.uploadTenantLogo(accessToken, file);
      const updated = await settingsService.updateTenantSettings(accessToken, { document_logo_url: url });
      setSettings(updated);
      setForm((p) => ({ ...p, document_logo_url: url }));
      refreshSettings();
      toast.success('Logo uploaded.');
    } catch (e) {
      setLogoUploadError(e.message);
      toast.error(e.message);
    } finally {
      setIsUploadingLogo(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const data = {};
      const templateFields = new Set([
        'preferred_invoice_template_id',
        'preferred_bill_template_id',
        'preferred_invoice_email_template_id',
        'preferred_bill_email_template_id',
        'preferred_verification_template_id',
      ]);
      for (const [key, value] of Object.entries(form)) {
        const nextValue = templateFields.has(key) ? (value ? Number(value) : null) : value;
        const currentValue = settings?.[key] ?? null;
        if (nextValue !== currentValue) data[key] = nextValue;
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
            <p className="text-sm text-warelyn-muted mb-4">Customize generated invoices and bills. Template selection here applies to all users in this tenant.</p>
            <div className="space-y-4">
              <div className="rounded-xl border border-dashed border-warelyn-border bg-slate-50 p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div>
                      <span className="block text-sm font-medium text-warelyn-text">Document Logo</span>
                      <p className="text-xs text-warelyn-muted">Upload a logo from your device. PNG, JPG, or SVG up to 2MB.</p>
                    </div>
                    {logoUploadError ? <p className="text-xs text-red-600">{logoUploadError}</p> : null}
                    <label
                      className={`inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-medium transition ${
                        editing && !isUploadingLogo
                          ? 'cursor-pointer bg-warelyn-primary text-white hover:bg-blue-800'
                          : 'cursor-not-allowed bg-slate-200 text-slate-500'
                      }`}
                    >
                      {isUploadingLogo ? 'Uploading...' : 'Upload from device'}
                      <input
                        accept="image/png,image/jpeg,image/jpg,image/svg+xml"
                        className="hidden"
                        disabled={!editing || isUploadingLogo}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          e.target.value = '';
                          if (file) handleLogoUpload(file);
                        }}
                        type="file"
                      />
                    </label>
                    {form.document_logo_url ? (
                      <button
                        className="ml-3 text-xs font-medium text-warelyn-muted underline decoration-dotted underline-offset-4 hover:text-warelyn-primary"
                        disabled={!editing || isUploadingLogo}
                        onClick={async () => {
                          try {
                            const updated = await settingsService.updateTenantSettings(accessToken, { document_logo_url: null });
                            setSettings(updated);
                            setForm((p) => ({ ...p, document_logo_url: '' }));
                            refreshSettings();
                            toast.success('Logo removed.');
                          } catch (e) {
                            toast.error(e.message);
                          }
                        }}
                        type="button"
                      >
                        Remove logo
                      </button>
                    ) : null}
                  </div>
                  <div className="min-h-24 min-w-48 rounded-lg border border-warelyn-border bg-white p-3">
                    {form.document_logo_url ? (
                      <img
                        alt="Document logo preview"
                        className="max-h-16 max-w-full object-contain"
                        src={resolveUploadUrl(form.document_logo_url)}
                      />
                    ) : (
                      <div className="flex h-16 items-center justify-center text-xs text-warelyn-muted">No logo uploaded yet</div>
                    )}
                  </div>
                </div>
              </div>
              <div>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Document Footer</span>
                  <textarea className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed" value={form.document_footer} onChange={handleChange('document_footer')} rows={3} disabled={!editing} />
                </label>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Invoice PDF Template</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
                    value={form.preferred_invoice_template_id ?? ''}
                    onChange={(e) => setForm((p) => ({ ...p, preferred_invoice_template_id: e.target.value }))}
                    disabled={!editing}
                  >
                    <option value="">System default</option>
                    {invoicePdfTemplates.map((template) => (
                      <option key={template.id} value={String(template.id)}>{template.name}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Invoice Email Template</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
                    value={form.preferred_invoice_email_template_id ?? ''}
                    onChange={(e) => setForm((p) => ({ ...p, preferred_invoice_email_template_id: e.target.value }))}
                    disabled={!editing}
                  >
                    <option value="">System default</option>
                    {invoiceEmailTemplates.map((template) => (
                      <option key={template.id} value={String(template.id)}>{template.name}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Bill PDF Template</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
                    value={form.preferred_bill_template_id ?? ''}
                    onChange={(e) => setForm((p) => ({ ...p, preferred_bill_template_id: e.target.value }))}
                    disabled={!editing}
                  >
                    <option value="">System default</option>
                    {billPdfTemplates.map((template) => (
                      <option key={template.id} value={String(template.id)}>{template.name}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Bill Email Template</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
                    value={form.preferred_bill_email_template_id ?? ''}
                    onChange={(e) => setForm((p) => ({ ...p, preferred_bill_email_template_id: e.target.value }))}
                    disabled={!editing}
                  >
                    <option value="">System default</option>
                    {billEmailTemplates.map((template) => (
                      <option key={template.id} value={String(template.id)}>{template.name}</option>
                    ))}
                  </select>
                </label>
                <label className="block sm:col-span-2">
                  <span className="mb-2 block text-sm font-medium text-warelyn-text">Verification Email Template</span>
                  <select
                    className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
                    value={form.preferred_verification_template_id ?? ''}
                    onChange={(e) => setForm((p) => ({ ...p, preferred_verification_template_id: e.target.value }))}
                    disabled={!editing}
                  >
                    <option value="">System default</option>
                    {verificationTemplates.map((template) => (
                      <option key={template.id} value={String(template.id)}>{template.name}</option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
          </div>
        );
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
                <Button onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Settings'}</Button>
              </>
            ) : (
              <Button variant="secondary" onClick={() => setEditing(true)}>Edit Settings</Button>
            )}
          </div>
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
  ];

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
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [accessToken]);

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
