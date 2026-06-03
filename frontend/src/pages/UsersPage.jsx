import { KeyRound, Search, Shield, Trash2, UserMinus, UserPlus, Users } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Badge } from '../components/ui/Badge.jsx';
import { Button } from '../components/ui/Button.jsx';
import { ConfirmationModal } from '../components/ui/ConfirmationModal.jsx';
import { Input } from '../components/ui/Input.jsx';
import { PasswordInput } from '../components/ui/PasswordInput.jsx';
import { PageHeader } from '../components/ui/PageHeader.jsx';
import { PhoneInput } from '../components/ui/PhoneInput.jsx';
import { TableShell } from '../components/ui/TableShell.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../hooks/useToast.jsx';
import { isValidPhone, normalizePhone, parsePhone, stripNonDigits } from '../lib/phone.js';
import * as userService from '../services/userService.js';
import { formatDateTime } from '../utils/formatters.js';

const ROLES = [
  { value: 'TENANT_ADMIN', label: 'Tenant Admin' },
  { value: 'INVENTORY_MANAGER', label: 'Inventory Manager' },
  { value: 'SALES_STAFF', label: 'Sales Staff' },
  { value: 'PURCHASE_STAFF', label: 'Purchase Staff' },
  { value: 'VIEWER', label: 'Viewer' },
];

const ROLE_TONES = {
  TENANT_ADMIN: 'bg-purple-50 text-purple-700 ring-purple-200',
  INVENTORY_MANAGER: 'bg-blue-50 text-blue-700 ring-blue-200',
  SALES_STAFF: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  PURCHASE_STAFF: 'bg-amber-50 text-amber-700 ring-amber-200',
  VIEWER: 'bg-slate-100 text-slate-700 ring-slate-200',
};

function roleBadgeClass(role) {
  return ROLE_TONES[role] ?? ROLE_TONES.VIEWER;
}

function roleLabel(role) {
  return ROLES.find((r) => r.value === role)?.label ?? role;
}

function FormModal({ open, onClose, title, children, onSubmit, isLoading, submitLabel = 'Save' }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm" role="presentation">
      <div aria-modal="true" className="w-full max-w-lg rounded-2xl border border-warelyn-border bg-white p-6 shadow-2xl" role="dialog">
        <h2 className="text-lg font-bold tracking-tight text-warelyn-text">{title}</h2>
        <form
          className="mt-5 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          {children}
          <div className="flex justify-end gap-3 pt-2">
            <Button disabled={isLoading} onClick={onClose} variant="secondary" type="button">Cancel</Button>
            <Button isLoading={isLoading} type="submit">{submitLabel}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SelectField({ label, id, value, onChange, options, error, disabled = false }) {
  return (
    <label className="block" htmlFor={id}>
      {label ? <span className="mb-2 block text-sm font-medium text-warelyn-text">{label}</span> : null}
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:ring-4 ${error ? 'border-red-300 focus:border-warelyn-danger focus:ring-red-100' : 'border-warelyn-border focus:border-warelyn-primary focus:ring-blue-900/10'}`}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error ? <p className="mt-1.5 text-xs font-medium text-warelyn-danger">{error}</p> : null}
    </label>
  );
}

export function UsersPage() {
  const { accessToken, user: currentUser } = useAuth();
  const toast = useToast();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modals
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [disableTarget, setDisableTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [resetTarget, setResetTarget] = useState(null);

  // Form states
  const [formLoading, setFormLoading] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', email: '', phone: '', role: 'VIEWER', password: '' });
  const [createErrors, setCreateErrors] = useState({});
  const [editForm, setEditForm] = useState({ name: '', phone: '', role: '' });
  const [editErrors, setEditErrors] = useState({});

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await userService.listUsers(accessToken, { search: search || undefined, role: roleFilter || undefined, status: statusFilter || undefined });
      setUsers(data.users ?? data ?? []);
    } catch (err) {
      setError(err.message || 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, [accessToken, search, roleFilter, statusFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Create user
  function validateCreate() {
    const errs = {};
    if (!createForm.name.trim()) errs.name = 'Name is required.';
    if (!createForm.email.trim()) errs.email = 'Email is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(createForm.email)) errs.email = 'Invalid email format.';
    if (!createForm.password) errs.password = 'Password is required.';
    else if (createForm.password.length < 8) errs.password = 'Password must be at least 8 characters.';
    if (createForm.phone) {
      const { countryCode, localNumber } = parsePhone(createForm.phone);
      const phoneResult = isValidPhone(countryCode, localNumber);
      if (!phoneResult.valid) errs.phone = phoneResult.error;
    }
    return errs;
  }

  async function handleCreate() {
    const errs = validateCreate();
    setCreateErrors(errs);
    if (Object.keys(errs).length) return;
    setFormLoading(true);
    try {
      await userService.createUser(accessToken, {
        name: createForm.name.trim(),
        email: createForm.email.trim(),
        phone: createForm.phone.trim() || undefined,
        role: createForm.role,
        password: createForm.password,
      });
      toast.success('User created successfully.');
      setCreateOpen(false);
      setCreateForm({ name: '', email: '', phone: '', role: 'VIEWER', password: '' });
      setCreateErrors({});
      fetchUsers();
    } catch (err) {
      toast.error(err.message || 'Failed to create user.');
    } finally {
      setFormLoading(false);
    }
  }

  // Edit user
  function openEdit(user) {
    setEditUser(user);
    setEditForm({ name: user.name, phone: user.phone || '', role: user.role });
    setEditErrors({});
  }

  function validateEdit() {
    const errs = {};
    if (!editForm.name.trim()) errs.name = 'Name is required.';
    if (editForm.phone) {
      const { countryCode, localNumber } = parsePhone(editForm.phone);
      const phoneResult = isValidPhone(countryCode, localNumber);
      if (!phoneResult.valid) errs.phone = phoneResult.error;
    }
    return errs;
  }

  async function handleEdit() {
    const errs = validateEdit();
    setEditErrors(errs);
    if (Object.keys(errs).length) return;
    setFormLoading(true);
    try {
      await userService.updateUser(accessToken, editUser.id, {
        name: editForm.name.trim(),
        phone: editForm.phone.trim() || undefined,
        role: editForm.role,
      });
      toast.success('User updated successfully.');
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.message || 'Failed to update user.');
    } finally {
      setFormLoading(false);
    }
  }

  // Disable / Enable
  async function handleToggleStatus() {
    if (!disableTarget) return;
    setFormLoading(true);
    try {
      const isActive = disableTarget.status === 'ACTIVE' || disableTarget.is_active;
      if (isActive) {
        await userService.disableUser(accessToken, disableTarget.id);
        toast.success(`${disableTarget.name} has been disabled.`);
      } else {
        await userService.enableUser(accessToken, disableTarget.id);
        toast.success(`${disableTarget.name} has been enabled.`);
      }
      setDisableTarget(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.message || 'Failed to update user status.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDeleteUser() {
    if (!deleteTarget) return;
    setFormLoading(true);
    try {
      await userService.deleteUser(accessToken, deleteTarget.id);
      toast.success(`${deleteTarget.name} has been deleted.`);
      setDeleteTarget(null);
      fetchUsers();
    } catch (err) {
      toast.error(err.message || 'Failed to delete user.');
    } finally {
      setFormLoading(false);
    }
  }

  async function handleReset() {
    if (!resetTarget) return;
    setFormLoading(true);
    try {
      await userService.resetPassword(accessToken, resetTarget.id);
      toast.success(`Reset password link sent to ${resetTarget.name}.`);
      setResetTarget(null);
    } catch (err) {
      toast.error(err.message || 'Failed to send reset link.');
    } finally {
      setFormLoading(false);
    }
  }

  function isUserActive(user) {
    return user.status === 'ACTIVE' || user.is_active === true;
  }

  const toolbar = (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="block w-full rounded-lg border border-warelyn-border bg-white pl-9 pr-3 py-2 text-sm text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
        />
      </div>
      <select
        value={roleFilter}
        onChange={(e) => setRoleFilter(e.target.value)}
        className="rounded-lg border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
        aria-label="Filter by role"
      >
        <option value="">All Roles</option>
        {ROLES.map((r) => (
          <option key={r.value} value={r.value}>{r.label}</option>
        ))}
      </select>
      <select
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        className="rounded-lg border border-warelyn-border bg-white px-3 py-2 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10"
        aria-label="Filter by status"
      >
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="disabled">Disabled</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users & Roles"
        description="Manage team members and their access levels"
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <UserPlus size={16} />
            Add User
          </Button>
        }
      />

      <TableShell
        title="Team Members"
        rowCount={users.length}
        isLoading={loading}
        error={error}
        isEmpty={!loading && !error && users.length === 0}
        emptyTitle={(search || roleFilter || statusFilter) ? 'No matching users found' : 'No users found'}
        emptyDescription={(search || roleFilter || statusFilter) ? 'Adjust your search or role filter to find the right user.' : 'Invite your first team member to start assigning roles.'}
        emptyIllustration={(search || roleFilter || statusFilter) ? emptyStateIllustrations.noResult : emptyStateIllustrations.users}
        emptyActionLabel={!(search || roleFilter || statusFilter) ? 'Add User' : undefined}
        emptySecondaryActionLabel={(search || roleFilter || statusFilter) ? 'Clear filters' : undefined}
        onEmptyAction={!(search || roleFilter || statusFilter) ? () => setCreateOpen(true) : undefined}
        onEmptySecondaryAction={(search || roleFilter || statusFilter) ? () => { setSearch(''); setRoleFilter(''); setStatusFilter(''); } : undefined}
        toolbar={toolbar}
        actions={null}
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-warelyn-border text-left">
              <th className="px-4 py-3 font-semibold text-warelyn-muted">Name</th>
              <th className="px-4 py-3 font-semibold text-warelyn-muted">Email</th>
              <th className="px-4 py-3 font-semibold text-warelyn-muted">Role</th>
              <th className="px-4 py-3 font-semibold text-warelyn-muted">Status</th>
              <th className="px-4 py-3 font-semibold text-warelyn-muted">Last Login</th>
              <th className="px-4 py-3 font-semibold text-warelyn-muted text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const active = isUserActive(user);
              return (
                <tr key={user.id} className="border-b border-warelyn-border last:border-0 hover:bg-slate-50 transition">
                  <td className="px-4 py-3 font-medium text-warelyn-text">{user.name}</td>
                  <td className="px-4 py-3 text-warelyn-muted">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${roleBadgeClass(user.role)}`}>
                      <Shield size={12} />
                      {roleLabel(user.role)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={active ? 'success' : 'danger'}>
                      {active ? 'Active' : 'Disabled'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-warelyn-muted">
                    {user.last_login_at ? formatDateTime(user.last_login_at) : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => openEdit(user)}
                        className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-warelyn-primary hover:bg-blue-50 transition"
                        title="Edit user"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => setDisableTarget(user)}
                        className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${active ? 'text-warelyn-danger hover:bg-red-50' : 'text-emerald-700 hover:bg-emerald-50'}`}
                        title={active ? 'Disable user' : 'Enable user'}
                      >
                        {active ? 'Disable' : 'Enable'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setResetTarget(user)}
                        className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition"
                        title="Send password reset link"
                      >
                        <KeyRound size={14} />
                      </button>
                      {currentUser?.id !== user.id ? (
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(user)}
                          className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-warelyn-danger hover:bg-red-50 transition"
                          title="Delete user"
                        >
                          <Trash2 size={14} />
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </TableShell>

      {/* Create User Modal */}
      <FormModal
        open={createOpen}
        onClose={() => { setCreateOpen(false); setCreateErrors({}); }}
        title="Add New User"
        onSubmit={handleCreate}
        isLoading={formLoading}
        submitLabel="Create User"
      >
        <Input
          label="Name"
          id="create-name"
          value={createForm.name}
          onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
          error={createErrors.name}
          placeholder="Full name"
          required
        />
        <Input
          label="Email"
          id="create-email"
          type="email"
          value={createForm.email}
          onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
          error={createErrors.email}
          placeholder="user@company.com"
          required
        />
        <PhoneInput
          label="Phone"
          value={createForm.phone}
          onChange={(val) => setCreateForm((f) => ({ ...f, phone: val }))}
          error={createErrors.phone}
        />
        <SelectField
          label="Role"
          id="create-role"
          value={createForm.role}
          onChange={(val) => setCreateForm((f) => ({ ...f, role: val }))}
          options={ROLES}
        />
        <PasswordInput
          label="Password"
          id="create-password"
          autoComplete="new-password"
          minLength={8}
          value={createForm.password}
          onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
          error={createErrors.password}
          placeholder="Minimum 8 characters"
          required
        />
      </FormModal>

      {/* Edit User Modal */}
      <FormModal
        open={!!editUser}
        onClose={() => { setEditUser(null); setEditErrors({}); }}
        title="Edit User"
        onSubmit={handleEdit}
        isLoading={formLoading}
        submitLabel="Save Changes"
      >
        <Input
          label="Email"
          id="edit-email"
          value={editUser?.email ?? ''}
          disabled
          className="bg-slate-50 cursor-not-allowed"
        />
        <Input
          label="Name"
          id="edit-name"
          value={editForm.name}
          onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
          error={editErrors.name}
          required
        />
        <PhoneInput
          label="Phone"
          value={editForm.phone}
          onChange={(val) => setEditForm((f) => ({ ...f, phone: val }))}
          error={editErrors.phone}
        />
        <SelectField
          label="Role"
          id="edit-role"
          value={editForm.role}
          onChange={(val) => setEditForm((f) => ({ ...f, role: val }))}
          options={ROLES}
        />
      </FormModal>

      {/* Disable/Enable Confirmation Modal */}
      <ConfirmationModal
        open={!!disableTarget}
        title={disableTarget && isUserActive(disableTarget) ? `Disable ${disableTarget.name}?` : `Enable ${disableTarget?.name}?`}
        description={
          disableTarget && isUserActive(disableTarget)
            ? 'This user will no longer be able to log in. You can re-enable them later.'
            : 'This user will regain access and be able to log in again.'
        }
        confirmLabel={disableTarget && isUserActive(disableTarget) ? 'Disable' : 'Enable'}
        variant={disableTarget && isUserActive(disableTarget) ? 'danger' : 'primary'}
        isLoading={formLoading}
        onConfirm={handleToggleStatus}
        onCancel={() => setDisableTarget(null)}
      />

      {/* Delete User Confirmation Modal */}
      <ConfirmationModal
        open={!!deleteTarget}
        title={`Delete ${deleteTarget?.name}?`}
        description="This will permanently remove the user account. If this user has created business records, deletion will be blocked and you should disable the account instead."
        confirmLabel="Delete User"
        variant="danger"
        isLoading={formLoading}
        onConfirm={handleDeleteUser}
        onCancel={() => setDeleteTarget(null)}
      />

      {/* Reset Password Link Modal */}
      <ConfirmationModal
        open={!!resetTarget}
        title={`Send reset link to ${resetTarget?.name ?? ''}?`}
        description={`An email with a secure reset password link will be sent to ${resetTarget?.email ?? 'this user'}.`}
        confirmLabel="Send reset link"
        variant="accent"
        isLoading={formLoading}
        onConfirm={handleReset}
        onCancel={() => setResetTarget(null)}
      />
    </div>
  );
}
