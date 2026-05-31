import { Navigate } from 'react-router-dom';

import { EmptyState } from '../components/ui/EmptyState.jsx';
import { LoadingState } from '../components/ui/LoadingState.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { InventoryManagerDashboard } from './dashboards/InventoryManagerDashboard.jsx';
import { PurchaseStaffDashboard } from './dashboards/PurchaseStaffDashboard.jsx';
import { SalesStaffDashboard } from './dashboards/SalesStaffDashboard.jsx';
import { TenantAdminDashboard } from './dashboards/TenantAdminDashboard.jsx';
import { ViewerDashboard } from './dashboards/ViewerDashboard.jsx';

const ROLE_DASHBOARD = {
  TENANT_ADMIN: TenantAdminDashboard,
  INVENTORY_MANAGER: InventoryManagerDashboard,
  SALES_STAFF: SalesStaffDashboard,
  PURCHASE_STAFF: PurchaseStaffDashboard,
  VIEWER: ViewerDashboard,
};

export function DashboardPage() {
  const { user } = useAuth();

  if (!user) return <LoadingState />;
  if (user.role === 'SUPER_ADMIN') return <Navigate replace to="/admin" />;

  const RoleDashboard = ROLE_DASHBOARD[user.role];
  if (!RoleDashboard) {
    return (
      <EmptyState
        description="Your role does not have a configured dashboard view."
        illustration={emptyStateIllustrations.overview}
        title="Dashboard not configured"
      />
    );
  }

  return <RoleDashboard />;
}

