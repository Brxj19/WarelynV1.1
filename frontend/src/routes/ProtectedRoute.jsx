import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { LoadingState } from '../components/ui/LoadingState.jsx';
import { useAuth } from '../context/AuthContext.jsx';

export function ProtectedRoute({ requiredRole }) {
  const location = useLocation();
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingState message="Checking your Warelyn session..." />;
  }

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to="/login" />;
  }

  if (!requiredRole && user?.role === 'SUPER_ADMIN') {
    return <Navigate replace to="/admin" />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate replace to="/dashboard" />;
  }

  return <Outlet />;
}
