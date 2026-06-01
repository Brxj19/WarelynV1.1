import { Navigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';
import { LandingPage } from '../pages/LandingPage.jsx';

export function RootRedirect() {
  const { isAuthenticated, defaultLandingPage, user } = useAuth();

  if (isAuthenticated) {
    if (user?.role === 'SUPER_ADMIN') {
      return <Navigate to="/admin" replace />;
    }
    return <Navigate to={defaultLandingPage ?? '/dashboard'} replace />;
  }

  return <LandingPage />;
}
