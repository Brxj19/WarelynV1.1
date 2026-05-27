import { useAuth } from '../context/AuthContext.jsx';
import { AccessDenied } from './AccessDenied.jsx';

/**
 * Route guard that renders children only if the current user's role
 * is in the allowedRoles list. Otherwise shows the AccessDenied page.
 */
export function RoleGuard({ allowedRoles, children }) {
  const { user } = useAuth();

  if (!allowedRoles.includes(user?.role)) {
    return <AccessDenied />;
  }

  return children;
}
