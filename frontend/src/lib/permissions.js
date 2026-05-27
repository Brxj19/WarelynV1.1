/**
 * Centralized permissions module for role-based access control.
 */

export const ROLES = {
  SUPER_ADMIN: 'SUPER_ADMIN',
  TENANT_ADMIN: 'TENANT_ADMIN',
  INVENTORY_MANAGER: 'INVENTORY_MANAGER',
  SALES_STAFF: 'SALES_STAFF',
  PURCHASE_STAFF: 'PURCHASE_STAFF',
  VIEWER: 'VIEWER',
};

// Route access matrix — keys use glob-like patterns for readability
const ROUTE_ACCESS = {
  '/dashboard': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF', 'VIEWER'],
  '/catalog/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF', 'VIEWER'],
  '/warehouses/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER'],
  '/purchases/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER'],
  '/purchase-receipts/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER'],
  '/sales/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER'],
  '/invoices/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER'],
  '/bills/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER'],
  '/returns/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER'],
  '/pick-tasks/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF'],
  '/packages/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF'],
  '/sales-fulfillments/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF'],
  '/reports/*': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER'],
  '/settings': ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF', 'VIEWER'],
  '/settings/users': ['TENANT_ADMIN'],
  '/settings/pdf-templates': ['TENANT_ADMIN'],
  '/settings/email-templates': ['TENANT_ADMIN'],
  '/admin/*': ['SUPER_ADMIN'],
};

// Action permissions
const ACTION_ACCESS = {
  create: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF'],
  edit: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF'],
  delete: ['TENANT_ADMIN', 'INVENTORY_MANAGER'],
  manage_users: ['TENANT_ADMIN'],
  manage_templates: ['TENANT_ADMIN'],
  manage_settings: ['TENANT_ADMIN'],
  create_purchase: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF'],
  create_sale: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF'],
  send_invoice: ['TENANT_ADMIN', 'SALES_STAFF'],
  send_bill: ['TENANT_ADMIN', 'PURCHASE_STAFF'],
  approve: ['TENANT_ADMIN', 'INVENTORY_MANAGER'],
};

export function hasRole(user, role) {
  return user?.role === role;
}

export function hasAnyRole(user, roles) {
  return roles.includes(user?.role);
}

/**
 * Check if a user can access a given route path.
 * Matches the most specific pattern first (longer keys win).
 */
export function canAccessRoute(user, route) {
  if (!user?.role) return false;

  // Sort patterns by specificity (longer = more specific)
  const patterns = Object.keys(ROUTE_ACCESS).sort((a, b) => b.length - a.length);

  for (const pattern of patterns) {
    if (routeMatchesPattern(route, pattern)) {
      return ROUTE_ACCESS[pattern].includes(user.role);
    }
  }

  // If no pattern matches, allow access (unguarded route)
  return true;
}

export function canPerformAction(user, action) {
  return ACTION_ACCESS[action]?.includes(user?.role) ?? false;
}

export function isViewer(user) {
  return user?.role === 'VIEWER';
}

export function isTenantAdmin(user) {
  return user?.role === 'TENANT_ADMIN';
}

export function isSuperAdmin(user) {
  return user?.role === 'SUPER_ADMIN';
}

// --- Helpers ---

function routeMatchesPattern(route, pattern) {
  if (pattern.endsWith('/*')) {
    const base = pattern.slice(0, -2);
    return route === base || route.startsWith(base + '/') || route === base;
  }
  return route === pattern;
}
