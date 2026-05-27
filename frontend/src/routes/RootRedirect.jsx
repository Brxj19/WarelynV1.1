import { Navigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';
import { LandingPage } from '../pages/LandingPage.jsx';

export function RootRedirect() {
  const { isAuthenticated, defaultLandingPage } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={defaultLandingPage ?? '/dashboard'} replace />;
  }

  return <LandingPage />;
}
