import { lazy, Suspense } from 'react';
import { Navigate, Outlet, Route, Routes } from 'react-router-dom';

import { AppLoader } from '../components/ui/AppLoader.jsx';
import { RoleGuard } from '../components/RoleGuard.jsx';
import { GuestRoute } from './GuestRoute.jsx';
import { ProtectedRoute } from './ProtectedRoute.jsx';
import { RootRedirect } from './RootRedirect.jsx';

const AdminLayout = lazy(() => import('../layouts/AdminLayout.jsx').then(m => ({ default: m.AdminLayout })));
const AuthLayout = lazy(() => import('../layouts/AuthLayout.jsx').then(m => ({ default: m.AuthLayout })));
const MainLayout = lazy(() => import('../layouts/MainLayout.jsx').then(m => ({ default: m.MainLayout })));

const AdminDashboardPage = lazy(() => import('../pages/AdminDashboardPage.jsx').then(m => ({ default: m.AdminDashboardPage })));
const AuditLogsPage = lazy(() => import('../pages/AuditLogsPage.jsx').then(m => ({ default: m.AuditLogsPage })));
const CatalogPage = lazy(() => import('../pages/CatalogPage.jsx').then(m => ({ default: m.CatalogPage })));
const BatchExpiryReportPage = lazy(() => import('../pages/BatchExpiryReportPage.jsx').then(m => ({ default: m.BatchExpiryReportPage })));
const BlockedStockReportPage = lazy(() => import('../pages/BlockedStockReportPage.jsx').then(m => ({ default: m.BlockedStockReportPage })));
const CatalogMasterPages = lazy(() => import('../pages/CatalogMasterPages.jsx'));
const DashboardPage = lazy(() => import('../pages/DashboardPage.jsx').then(m => ({ default: m.DashboardPage })));
const ForgotPasswordPage = lazy(() => import('../pages/ForgotPasswordPage.jsx').then(m => ({ default: m.ForgotPasswordPage })));
const MyTasksPage = lazy(() => import('../pages/MyTasksPage.jsx').then(m => ({ default: m.MyTasksPage })));
const DocumentsPages = lazy(() => import('../pages/DocumentsPages.jsx'));
const EmailTemplatesPage = lazy(() => import('../pages/EmailTemplatesPage.jsx').then(m => ({ default: m.EmailTemplatesPage })));
const InventorySummaryReportPage = lazy(() => import('../pages/InventorySummaryReportPage.jsx').then(m => ({ default: m.InventorySummaryReportPage })));
const LocationStockReportPage = lazy(() => import('../pages/LocationStockReportPage.jsx').then(m => ({ default: m.LocationStockReportPage })));
const LandingPage = lazy(() => import('../pages/LandingPage.jsx').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('../pages/LoginPage.jsx').then(m => ({ default: m.LoginPage })));
const LowStockReportPage = lazy(() => import('../pages/LowStockReportPage.jsx').then(m => ({ default: m.LowStockReportPage })));
const NotFoundPage = lazy(() => import('../pages/NotFoundPage.jsx').then(m => ({ default: m.NotFoundPage })));
const PackageDetailPage = lazy(() => import('../pages/PackageDetailPage.jsx').then(m => ({ default: m.PackageDetailPage })));
const PickTaskDetailPage = lazy(() => import('../pages/PickTaskDetailPage.jsx').then(m => ({ default: m.PickTaskDetailPage })));
const PickTasksPage = lazy(() => import('../pages/PickTasksPage.jsx').then(m => ({ default: m.PickTasksPage })));
const PlatformHealthPage = lazy(() => import('../pages/PlatformHealthPage.jsx').then(m => ({ default: m.PlatformHealthPage })));
const PdfTemplatesPage = lazy(() => import('../pages/PdfTemplatesPage.jsx').then(m => ({ default: m.PdfTemplatesPage })));
const ProductValuationReportPage = lazy(() => import('../pages/ProductValuationReportPage.jsx').then(m => ({ default: m.ProductValuationReportPage })));
const ProductImportPage = lazy(() => import('../pages/ProductImportPage.jsx').then(m => ({ default: m.ProductImportPage })));
const OperationalListPages = lazy(() => import('../pages/OperationalListPages.jsx'));
const PurchaseOrderDetailPage = lazy(() => import('../pages/PurchaseOrderDetailPage.jsx').then(m => ({ default: m.PurchaseOrderDetailPage })));
const PurchaseOrderFormPage = lazy(() => import('../pages/PurchaseOrderFormPage.jsx').then(m => ({ default: m.PurchaseOrderFormPage })));
const PurchaseReceiptDetailPage = lazy(() => import('../pages/PurchaseReceiptDetailPage.jsx').then(m => ({ default: m.PurchaseReceiptDetailPage })));
const PurchaseReceivePage = lazy(() => import('../pages/PurchaseReceivePage.jsx').then(m => ({ default: m.PurchaseReceivePage })));
const PurchasesPage = lazy(() => import('../pages/PurchasesPage.jsx').then(m => ({ default: m.PurchasesPage })));
const RegisterPage = lazy(() => import('../pages/RegisterPage.jsx').then(m => ({ default: m.RegisterPage })));
const ReconciliationReportPage = lazy(() => import('../pages/ReconciliationReportPage.jsx').then(m => ({ default: m.ReconciliationReportPage })));
const ReportsPage = lazy(() => import('../pages/ReportsPage.jsx').then(m => ({ default: m.ReportsPage })));
const SalesFulfillPage = lazy(() => import('../pages/SalesFulfillPage.jsx').then(m => ({ default: m.SalesFulfillPage })));
const SalesFulfillmentDetailPage = lazy(() => import('../pages/SalesFulfillmentDetailPage.jsx').then(m => ({ default: m.SalesFulfillmentDetailPage })));
const SalesOrderDetailPage = lazy(() => import('../pages/SalesOrderDetailPage.jsx').then(m => ({ default: m.SalesOrderDetailPage })));
const SalesOrderFormPage = lazy(() => import('../pages/SalesOrderFormPage.jsx').then(m => ({ default: m.SalesOrderFormPage })));
const SalesPackagePage = lazy(() => import('../pages/SalesPackagePage.jsx').then(m => ({ default: m.SalesPackagePage })));
const SalesPage = lazy(() => import('../pages/SalesPage.jsx').then(m => ({ default: m.SalesPage })));
const SalesPickPage = lazy(() => import('../pages/SalesPickPage.jsx').then(m => ({ default: m.SalesPickPage })));
const SalesReturnDetailPage = lazy(() => import('../pages/SalesReturnDetailPage.jsx').then(m => ({ default: m.SalesReturnDetailPage })));
const SalesReturnFormPage = lazy(() => import('../pages/SalesReturnFormPage.jsx').then(m => ({ default: m.SalesReturnFormPage })));
const SalesReturnInspectPage = lazy(() => import('../pages/SalesReturnInspectPage.jsx').then(m => ({ default: m.SalesReturnInspectPage })));
const SerialStatusReportPage = lazy(() => import('../pages/SerialStatusReportPage.jsx').then(m => ({ default: m.SerialStatusReportPage })));
const SettingsPage = lazy(() => import('../pages/SettingsPage.jsx').then(m => ({ default: m.SettingsPage })));
const ReturnsPage = lazy(() => import('../pages/ReturnsPage.jsx').then(m => ({ default: m.ReturnsPage })));
const UsersPage = lazy(() => import('../pages/UsersPage.jsx').then(m => ({ default: m.UsersPage })));
const StockMovementReportPage = lazy(() => import('../pages/StockMovementReportPage.jsx').then(m => ({ default: m.StockMovementReportPage })));
const TenantDetailPage = lazy(() => import('../pages/TenantDetailPage.jsx').then(m => ({ default: m.TenantDetailPage })));
const TenantsPage = lazy(() => import('../pages/TenantsPage.jsx').then(m => ({ default: m.TenantsPage })));
const VerifyEmailPage = lazy(() => import('../pages/VerifyEmailPage.jsx').then(m => ({ default: m.VerifyEmailPage })));
const VerifyPhonePage = lazy(() => import('../pages/VerifyPhonePage.jsx').then(m => ({ default: m.VerifyPhonePage })));
const WarehouseDetailPage = lazy(() => import('../pages/WarehouseDetailPage.jsx').then(m => ({ default: m.WarehouseDetailPage })));
const WarehouseStockReportPage = lazy(() => import('../pages/WarehouseStockReportPage.jsx').then(m => ({ default: m.WarehouseStockReportPage })));
const WarehousesPage = lazy(() => import('../pages/WarehousesPage.jsx'));

function LazyBillsPage(props) { return <Suspense fallback={<AppLoader />}><LazyDocBills {...props} /></Suspense>; }
function LazyInvoicesPage(props) { return <Suspense fallback={<AppLoader />}><LazyDocInvoices {...props} /></Suspense>; }

const LazyDocBills = lazy(() => import('../pages/DocumentsPages.jsx').then(m => ({ default: m.BillsPage })));
const LazyDocInvoices = lazy(() => import('../pages/DocumentsPages.jsx').then(m => ({ default: m.InvoicesPage })));
const LazyBillDetailPage = lazy(() => import('../pages/DocumentsPages.jsx').then(m => ({ default: m.BillDetailPage })));
const LazyInvoiceDetailPage = lazy(() => import('../pages/DocumentsPages.jsx').then(m => ({ default: m.InvoiceDetailPage })));
const LazyPackagesPage = lazy(() => import('../pages/OperationalListPages.jsx').then(m => ({ default: m.PackagesPage })));
const LazyPurchaseReceiptStartPage = lazy(() => import('../pages/OperationalListPages.jsx').then(m => ({ default: m.PurchaseReceiptStartPage })));
const LazyPurchaseReceiptsPage = lazy(() => import('../pages/OperationalListPages.jsx').then(m => ({ default: m.PurchaseReceiptsPage })));
const LazySalesFulfillmentsPage = lazy(() => import('../pages/OperationalListPages.jsx').then(m => ({ default: m.SalesFulfillmentsPage })));
const LazyWarehousesPage = lazy(() => import('../pages/WarehousesPage.jsx').then(m => ({ default: m.WarehousesPage })));
const LazyWarehouseFormPage = lazy(() => import('../pages/WarehousesPage.jsx').then(m => ({ default: m.WarehouseFormPage })));
const LazyPutawayTasksPage = lazy(() => import('../pages/PutawayTasksPage.jsx').then(m => ({ default: m.PutawayTasksPage })));
const LazyPutawayTaskDetailPage = lazy(() => import('../pages/PutawayTasksPage.jsx').then(m => ({ default: m.PutawayTaskDetailPage })));
const LazyCycleCountsPage = lazy(() => import('../pages/CycleCountPages.jsx').then(m => ({ default: m.CycleCountsPage })));
const LazyCycleCountFormPage = lazy(() => import('../pages/CycleCountPages.jsx').then(m => ({ default: m.CycleCountFormPage })));
const LazyCycleCountDetailPage = lazy(() => import('../pages/CycleCountPages.jsx').then(m => ({ default: m.CycleCountDetailPage })));
const LazyProductsPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.ProductsPage })));
const LazyProductFormPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.ProductFormPage })));
const LazyCategoriesPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.CategoriesPage })));
const LazyCategoryFormPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.CategoryFormPage })));
const LazyBrandsPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.BrandsPage })));
const LazyBrandFormPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.BrandFormPage })));
const LazyVendorsPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.VendorsPage })));
const LazyVendorFormPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.VendorFormPage })));
const LazyCustomersPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.CustomersPage })));
const LazyCustomerFormPage = lazy(() => import('../pages/CatalogMasterPages.jsx').then(m => ({ default: m.CustomerFormPage })));

export function AppRoutes() {
  return (
    <Suspense fallback={<AppLoader />}>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="my-tasks" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'PURCHASE_STAFF']}><MyTasksPage /></RoleGuard>} />
            <Route path="catalog" element={<CatalogPage />} />
            <Route path="catalog/products" element={<LazyProductsPage />} />
            <Route path="catalog/products/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyProductFormPage /></RoleGuard>} />
            <Route path="catalog/products/import" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><ProductImportPage /></RoleGuard>} />
            <Route path="catalog/categories" element={<LazyCategoriesPage />} />
            <Route path="catalog/categories/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyCategoryFormPage /></RoleGuard>} />
            <Route path="catalog/brands" element={<LazyBrandsPage />} />
            <Route path="catalog/brands/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyBrandFormPage /></RoleGuard>} />
            <Route path="catalog/vendors" element={<LazyVendorsPage />} />
            <Route path="catalog/vendors/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyVendorFormPage /></RoleGuard>} />
            <Route path="catalog/customers" element={<LazyCustomersPage />} />
            <Route path="catalog/customers/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyCustomerFormPage /></RoleGuard>} />
            <Route path="warehouses" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER']}><LazyWarehousesPage /></RoleGuard>} />
            <Route path="warehouses/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyWarehouseFormPage /></RoleGuard>} />
            <Route path="warehouses/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER']}><WarehouseDetailPage /></RoleGuard>} />
            <Route path="putaway-tasks" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyPutawayTasksPage /></RoleGuard>} />
            <Route path="putaway-tasks/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyPutawayTaskDetailPage /></RoleGuard>} />
            <Route path="cycle-counts" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyCycleCountsPage /></RoleGuard>} />
            <Route path="cycle-counts/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyCycleCountFormPage /></RoleGuard>} />
            <Route path="cycle-counts/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><LazyCycleCountDetailPage /></RoleGuard>} />
            <Route path="purchases" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER']}><PurchasesPage /></RoleGuard>} />
            <Route path="purchases/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']}><PurchaseOrderFormPage /></RoleGuard>} />
            <Route path="purchases/:id/edit" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']}><PurchaseOrderFormPage /></RoleGuard>} />
            <Route path="purchases/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER']}><PurchaseOrderDetailPage /></RoleGuard>} />
            <Route path="purchases/:id/receive" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']}><PurchaseReceivePage /></RoleGuard>} />
            <Route path="purchase-receipts" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER']}><LazyPurchaseReceiptsPage /></RoleGuard>} />
            <Route path="purchase-receipts/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF']}><LazyPurchaseReceiptStartPage /></RoleGuard>} />
            <Route path="purchase-receipts/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER']}><PurchaseReceiptDetailPage /></RoleGuard>} />
            <Route path="sales" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER']}><SalesPage /></RoleGuard>} />
            <Route path="sales/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesOrderFormPage /></RoleGuard>} />
            <Route path="sales/:id/edit" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesOrderFormPage /></RoleGuard>} />
            <Route path="sales/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER']}><SalesOrderDetailPage /></RoleGuard>} />
            <Route path="sales/:id/pick" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesPickPage /></RoleGuard>} />
            <Route path="sales/:id/package" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesPackagePage /></RoleGuard>} />
            <Route path="sales/:id/fulfill" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesFulfillPage /></RoleGuard>} />
            <Route path="returns" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER']}><ReturnsPage /></RoleGuard>} />
            <Route path="returns/qc" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><ReturnsPage mode="qc" /></RoleGuard>} />
            <Route path="returns/new" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesReturnFormPage /></RoleGuard>} />
            <Route path="returns/:id/edit" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesReturnFormPage /></RoleGuard>} />
            <Route path="returns/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER']}><SalesReturnDetailPage /></RoleGuard>} />
            <Route path="returns/:id/inspect" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><SalesReturnInspectPage /></RoleGuard>} />
            <Route path="pick-tasks" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><PickTasksPage /></RoleGuard>} />
            <Route path="pick-tasks/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><PickTaskDetailPage /></RoleGuard>} />
            <Route path="packages" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><LazyPackagesPage /></RoleGuard>} />
            <Route path="packages/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><PackageDetailPage /></RoleGuard>} />
            <Route path="sales-fulfillments" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><LazySalesFulfillmentsPage /></RoleGuard>} />
            <Route path="sales-fulfillments/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF']}><SalesFulfillmentDetailPage /></RoleGuard>} />
            <Route path="invoices" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER']}><LazyDocInvoices /></RoleGuard>} />
            <Route path="invoices/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'SALES_STAFF', 'VIEWER']}><LazyInvoiceDetailPage /></RoleGuard>} />
            <Route path="bills" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER']}><LazyDocBills /></RoleGuard>} />
            <Route path="bills/:id" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'PURCHASE_STAFF', 'VIEWER']}><LazyBillDetailPage /></RoleGuard>} />
            <Route path="inventory" element={<DashboardPage />} />
            <Route path="reports" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER', 'VIEWER']}><Outlet /></RoleGuard>}>
              <Route index element={<ReportsPage />} />
              <Route path="inventory-summary" element={<InventorySummaryReportPage />} />
              <Route path="warehouse-stock" element={<WarehouseStockReportPage />} />
              <Route path="location-stock" element={<LocationStockReportPage />} />
              <Route path="stock-movements" element={<StockMovementReportPage />} />
              <Route path="low-stock" element={<LowStockReportPage />} />
              <Route path="product-valuation" element={<ProductValuationReportPage />} />
              <Route path="batch-expiry" element={<BatchExpiryReportPage />} />
              <Route path="serial-status" element={<SerialStatusReportPage />} />
              <Route path="blocked-stock" element={<BlockedStockReportPage />} />
              <Route path="reconciliation" element={<ReconciliationReportPage />} />
            </Route>
            <Route path="settings" element={<SettingsPage />} />
            <Route path="settings/users" element={<RoleGuard allowedRoles={['TENANT_ADMIN']}><UsersPage /></RoleGuard>} />
            <Route path="settings/email-templates" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><EmailTemplatesPage /></RoleGuard>} />
            <Route path="settings/pdf-templates" element={<RoleGuard allowedRoles={['TENANT_ADMIN', 'INVENTORY_MANAGER']}><PdfTemplatesPage /></RoleGuard>} />
            <Route path="verify-email" element={<VerifyEmailPage />} />
            <Route path="verify-phone" element={<VerifyPhonePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
        <Route element={<ProtectedRoute requiredRole="SUPER_ADMIN" />}>
          <Route element={<AdminLayout />}>
            <Route path="admin" element={<AdminDashboardPage />} />
            <Route path="admin/tenants" element={<TenantsPage />} />
            <Route path="admin/tenants/:id" element={<TenantDetailPage />} />
            <Route path="admin/audit-logs" element={<AuditLogsPage />} />
            <Route path="admin/platform-health" element={<PlatformHealthPage />} />
          </Route>
        </Route>
        <Route element={<GuestRoute />}>
          <Route element={<AuthLayout />}>
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="forgot-password" element={<ForgotPasswordPage />} />
          </Route>
        </Route>
        <Route path="/auth" element={<Navigate replace to="/login" />} />
      </Routes>
    </Suspense>
  );
}
