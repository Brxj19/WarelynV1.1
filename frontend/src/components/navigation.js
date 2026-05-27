import {
  AlertTriangle,
  BadgePlus,
  BarChart3,
  Boxes,
  Building2,
  CalendarClock,
  ClipboardCheck,
  CornerUpLeft,
  Database,
  DollarSign,
  FileCheck2,
  FilePlus2,
  FileUp,
  Handshake,
  Hash,
  HeartPulse,
  Layers2,
  LayoutDashboard,
  LogIn,
  MapPin,
  Mail,
  Package,
  PackageCheck,
  PackagePlus,
  PlusSquare,
  ReceiptText,
  RefreshCw,
  RotateCcw,
  Scale,
  ScrollText,
  Search,
  Send,
  Settings,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  ShoppingBag,
  ShoppingCart,
  Star,
  Tag,
  TrendingUp,
  Truck,
  UserRound,
  Users,
  Warehouse,
} from 'lucide-react';

export const writeRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER'];
export const purchaseRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER'];
export const purchaseWriteRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF'];
export const salesRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER'];
export const salesWriteRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF'];
export const operationsRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF'];
export const reportRoles = ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER'];

export const superAdminRoles = ['SUPER_ADMIN'];

export const navGroups = [
  {
    label: 'Overview',
    roles: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'SALES_STAFF', 'VIEWER'],
    items: [{ icon: LayoutDashboard, label: 'Dashboard', section: 'Overview', to: '/dashboard' }],
  },
  {
    label: 'Platform',
    roles: superAdminRoles,
    items: [
      { icon: ShieldAlert, label: 'Platform Console', section: 'Platform', to: '/admin', roles: superAdminRoles, exact: true },
      { icon: Building2, label: 'Tenants', section: 'Platform', to: '/admin/tenants', roles: superAdminRoles, exact: true },
      { icon: ScrollText, label: 'Audit Logs', section: 'Platform', to: '/admin/audit-logs', roles: superAdminRoles, exact: true },
      { icon: HeartPulse, label: 'Platform Health', section: 'Platform', to: '/admin/platform-health', roles: superAdminRoles, exact: true },
    ],
  },
  {
    label: 'Catalog',
    roles: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'SALES_STAFF', 'VIEWER'],
    items: [
      {
        icon: Package,
        label: 'Products',
        section: 'Catalog',
        children: [
          { icon: Package, label: 'All Products', section: 'Catalog', to: '/catalog/products', exact: true },
          { icon: PackagePlus, label: 'Create Product', section: 'Catalog', to: '/catalog/products/new', roles: writeRoles, exact: true },
          { icon: FileUp, label: 'Import Products', section: 'Catalog', to: '/catalog/products/import', roles: writeRoles, exact: true },
        ],
      },
      { icon: Tag, label: 'Categories', section: 'Catalog', to: '/catalog/categories', exact: true },
      { icon: Star, label: 'Brands', section: 'Catalog', to: '/catalog/brands', exact: true },
      { icon: Handshake, label: 'Vendors', section: 'Catalog', to: '/catalog/vendors', exact: true },
      { icon: UserRound, label: 'Customers', section: 'Catalog', to: '/catalog/customers', exact: true },
    ],
  },
  {
    label: 'Warehousing',
    roles: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER'],
    items: [
      {
        icon: Warehouse,
        label: 'Warehouses',
        section: 'Warehousing',
        children: [
          { icon: Warehouse, label: 'All Warehouses', section: 'Warehousing', to: '/warehouses', exact: true },
          { icon: PlusSquare, label: 'Create Warehouse', section: 'Warehousing', to: '/warehouses/new', roles: writeRoles, exact: true },
        ],
      },
    ],
  },
  {
    label: 'Purchases',
    roles: purchaseRoles,
    items: [
      {
        icon: ShoppingBag,
        label: 'Purchase Orders',
        section: 'Purchases',
        roles: purchaseRoles,
        children: [
          { icon: ShoppingBag, label: 'All Purchase Orders', section: 'Purchases', to: '/purchases', roles: purchaseRoles, exact: true },
          { icon: BadgePlus, label: 'Create Purchase Order', section: 'Purchases', to: '/purchases/new', roles: purchaseWriteRoles, exact: true },
        ],
      },
      {
        icon: Truck,
        label: 'Purchase Receipts',
        section: 'Purchases',
        roles: purchaseRoles,
        children: [
          { icon: Truck, label: 'All Receipts', section: 'Purchases', to: '/purchase-receipts', roles: purchaseRoles, exact: true },
          { icon: LogIn, label: 'Receive Stock', section: 'Purchases', to: '/purchase-receipts/new', roles: purchaseWriteRoles, exact: true },
        ],
      },
      {
        icon: ReceiptText,
        label: 'Bills',
        section: 'Purchases',
        to: '/bills',
        roles: purchaseRoles,
        exact: true,
      },
    ],
  },
  {
    label: 'Sales',
    roles: salesRoles,
    items: [
      {
        icon: ShoppingCart,
        label: 'Sales Orders',
        section: 'Sales',
        roles: salesRoles,
        children: [
          { icon: ShoppingCart, label: 'All Sales Orders', section: 'Sales', to: '/sales', roles: salesRoles, exact: true },
          { icon: FilePlus2, label: 'Create Sales Order', section: 'Sales', to: '/sales/new', roles: salesWriteRoles, exact: true },
        ],
      },
      {
        icon: FileCheck2,
        label: 'Invoices',
        section: 'Sales',
        to: '/invoices',
        roles: salesRoles,
        exact: true,
      },
    ],
  },
  {
    label: 'Operations',
    roles: operationsRoles,
    items: [
      {
        icon: ClipboardCheck,
        label: 'Picking',
        section: 'Operations',
        roles: operationsRoles,
        children: [
          { icon: ClipboardCheck, label: 'Pick Tasks', section: 'Operations', to: '/pick-tasks', roles: operationsRoles, exact: true },
        ],
      },
      {
        icon: PackageCheck,
        label: 'Packing',
        section: 'Operations',
        roles: operationsRoles,
        children: [
          { icon: PackageCheck, label: 'Packages', section: 'Operations', to: '/packages', roles: operationsRoles, exact: true },
        ],
      },
      {
        icon: Send,
        label: 'Fulfillment',
        section: 'Operations',
        roles: operationsRoles,
        children: [
          { icon: Send, label: 'Fulfillments', section: 'Operations', to: '/sales-fulfillments', roles: operationsRoles, exact: true },
        ],
      },
      {
        icon: RotateCcw,
        label: 'Returns',
        section: 'Operations',
        roles: salesRoles,
        children: [
          { icon: RotateCcw, label: 'Sales Returns', section: 'Operations', to: '/returns', roles: salesRoles, exact: true },
          { icon: CornerUpLeft, label: 'Create Return', section: 'Operations', to: '/returns/new', roles: salesWriteRoles, exact: true },
          { icon: ShieldCheck, label: 'Returns QC', section: 'Operations', to: '/returns/qc', roles: operationsRoles, exact: true },
        ],
      },
    ],
  },
  {
    label: 'Reports',
    roles: reportRoles,
    items: [
      { icon: BarChart3, label: 'Overview', section: 'Reports', to: '/reports', roles: reportRoles, exact: true },
      { icon: Database, label: 'Inventory Summary', section: 'Reports', to: '/reports/inventory-summary', roles: reportRoles, exact: true },
      { icon: Layers2, label: 'Warehouse Stock', section: 'Reports', to: '/reports/warehouse-stock', roles: reportRoles, exact: true },
      { icon: MapPin, label: 'Location Stock', section: 'Reports', to: '/reports/location-stock', roles: reportRoles, exact: true },
      { icon: TrendingUp, label: 'Stock Movements', section: 'Reports', to: '/reports/stock-movements', roles: reportRoles, exact: true },
      { icon: AlertTriangle, label: 'Low Stock', section: 'Reports', to: '/reports/low-stock', roles: reportRoles, exact: true },
      { icon: RefreshCw, label: 'Reorder Suggestions', section: 'Reports', to: '/reports/reorder-suggestions', roles: reportRoles, exact: true },
      { icon: DollarSign, label: 'Product Valuation', section: 'Reports', to: '/reports/product-valuation', roles: reportRoles, exact: true },
      { icon: CalendarClock, label: 'Batch Expiry', section: 'Reports', to: '/reports/batch-expiry', roles: reportRoles, exact: true },
      { icon: Hash, label: 'Serial Status', section: 'Reports', to: '/reports/serial-status', roles: reportRoles, exact: true },
      { icon: ShieldOff, label: 'Blocked Stock', section: 'Reports', to: '/reports/blocked-stock', roles: reportRoles, exact: true },
      { icon: Scale, label: 'Reconciliation', section: 'Reports', to: '/reports/reconciliation', roles: reportRoles, exact: true },
    ],
  },
  {
    label: 'Preferences',
    roles: ['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'SALES_STAFF', 'VIEWER'],
    items: [
      {
        icon: Settings,
        label: 'Settings',
        section: 'Preferences',
        children: [
          { icon: Settings, label: 'General', section: 'Preferences', to: '/settings', exact: true },
          { icon: Users, label: 'Users & Roles', section: 'Preferences', to: '/settings/users', roles: ['TENANT_ADMIN'], exact: true },
          { icon: FileCheck2, label: 'PDF Templates', section: 'Preferences', to: '/settings/pdf-templates', roles: ['TENANT_ADMIN'], exact: true },
          { icon: Mail, label: 'Email Templates', section: 'Preferences', to: '/settings/email-templates', roles: ['TENANT_ADMIN'], exact: true },
        ],
      },
    ],
  },
];

export const quickCreateItems = [
  { icon: Package, label: 'New Product', roles: writeRoles, to: '/catalog/products/new' },
  { icon: ShoppingBag, label: 'New Purchase Order', roles: purchaseWriteRoles, to: '/purchases/new' },
  { icon: Truck, label: 'Receive Stock', roles: purchaseWriteRoles, to: '/purchase-receipts/new' },
  { icon: ShoppingCart, label: 'New Sales Order', roles: salesWriteRoles, to: '/sales/new' },
  { icon: RotateCcw, label: 'New Return', roles: salesWriteRoles, to: '/returns/new' },
  { icon: Warehouse, label: 'Open Warehouses', roles: writeRoles, to: '/warehouses' },
];

const detailRoutes = [
  { pattern: /^\/inventory$/, label: 'Inventory Dashboard', section: 'Overview', to: '/dashboard', icon: LayoutDashboard },
  { pattern: /^\/warehouses\/[^/]+$/, label: 'Warehouse Detail', section: 'Warehousing', to: '/warehouses', icon: Warehouse },
  { pattern: /^\/purchases\/[^/]+$/, label: 'Purchase Order Detail', section: 'Purchases', to: '/purchases', icon: ShoppingBag },
  { pattern: /^\/purchases\/[^/]+\/receive$/, label: 'Receive Purchase Order', section: 'Purchases', to: '/purchase-receipts/new', icon: Truck },
  { pattern: /^\/purchase-receipts\/[^/]+$/, label: 'Purchase Receipt', section: 'Purchases', to: '/purchase-receipts', icon: Truck },
  { pattern: /^\/bills\/[^/]+$/, label: 'Bill Detail', section: 'Purchases', to: '/bills', icon: ReceiptText },
  { pattern: /^\/sales\/[^/]+$/, label: 'Sales Order Detail', section: 'Sales', to: '/sales', icon: ShoppingCart },
  { pattern: /^\/invoices\/[^/]+$/, label: 'Invoice Detail', section: 'Sales', to: '/invoices', icon: FileCheck2 },
  { pattern: /^\/sales\/[^/]+\/pick$/, label: 'Sales Picking', section: 'Operations', to: '/pick-tasks', icon: ClipboardCheck },
  { pattern: /^\/sales\/[^/]+\/package$/, label: 'Sales Packaging', section: 'Operations', to: '/packages', icon: PackageCheck },
  { pattern: /^\/sales\/[^/]+\/fulfill$/, label: 'Sales Fulfillment', section: 'Operations', to: '/sales-fulfillments', icon: Send },
  { pattern: /^\/sales-fulfillments\/[^/]+$/, label: 'Fulfillment Detail', section: 'Operations', to: '/sales-fulfillments', icon: Send },
  { pattern: /^\/returns\/[^/]+$/, label: 'Return Detail', section: 'Operations', to: '/returns', icon: RotateCcw },
  { pattern: /^\/returns\/[^/]+\/inspect$/, label: 'Return Inspection', section: 'Operations', to: '/returns/qc', icon: ShieldCheck },
  { pattern: /^\/pick-tasks\/[^/]+$/, label: 'Pick Task Detail', section: 'Operations', to: '/pick-tasks', icon: ClipboardCheck },
  { pattern: /^\/packages\/[^/]+$/, label: 'Package Detail', section: 'Operations', to: '/packages', icon: PackageCheck },
];

export function canSee(item, role) {
  return !item.roles || item.roles.includes(role);
}

export function getVisibleNavGroups(role) {
  return navGroups
    .filter((group) => canSee(group, role))
    .map((group) => ({
      ...group,
      items: filterVisibleItems(group.items, role),
    }))
    .filter((group) => group.items.length > 0);
}

export function flattenNav(role) {
  return getVisibleNavGroups(role).flatMap((group) => flattenItems(group.items, group.label));
}

export function activeGroupFor(pathname, role) {
  return getVisibleNavGroups(role).find((group) => flattenItems(group.items, group.label).some((item) => matchesPathLoose(item.to, pathname)))?.label ?? 'Overview';
}

export function resolveRouteMeta(pathname, role) {
  const navItem = findBestNavMatch(pathname, role);
  if (navItem) return navItem;
  const detailMatch = detailRoutes.find((item) => item.pattern.test(pathname));
  if (detailMatch) return detailMatch;
  return { icon: Search, label: 'Workspace', section: 'Workspace', to: pathname };
}

export function isItemActive(item, pathname) {
  if (item.children?.length) {
    return item.children.some((child) => matchesPathLoose(child.to, pathname));
  }
  return matchesPath(item.to, pathname, item.exact);
}

function filterVisibleItems(items, role) {
  return items
    .map((item) => {
      if (item.children?.length) {
        const children = item.children.filter((child) => canSee(child, role));
        if (!children.length || (item.roles && !item.roles.includes(role))) return null;
        return { ...item, children };
      }
      if (!canSee(item, role)) return null;
      return item;
    })
    .filter(Boolean);
}

function flattenItems(items, groupLabel, parentLabel = null) {
  return items.flatMap((item) => {
    if (item.children?.length) {
      return flattenItems(
        item.children.map((child) => ({ ...child, icon: child.icon ?? item.icon })),
        groupLabel,
        item.label,
      );
    }
    return [{ ...item, group: groupLabel, parentLabel }];
  });
}

function findBestNavMatch(pathname, role) {
  return flattenNav(role)
    .sort((left, right) => right.to.length - left.to.length)
    .find((item) => matchesPath(item.to, pathname, item.exact));
}

function matchesPath(basePath, pathname, exact = false) {
  if (exact) return pathname === basePath;
  return pathname === basePath || pathname.startsWith(`${basePath}/`);
}

function matchesPathLoose(basePath, pathname) {
  return pathname === basePath || pathname.startsWith(`${basePath}/`);
}
