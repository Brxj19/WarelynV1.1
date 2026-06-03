import { useNavigate } from 'react-router-dom';

import { Button } from '../components/ui/Button.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';
import { useAuth } from '../context/AuthContext.jsx';

export function NotFoundPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const homeTarget = isAuthenticated ? (user?.role === 'SUPER_ADMIN' ? '/admin' : '/dashboard') : '/login';
  const homeLabel = isAuthenticated ? (user?.role === 'SUPER_ADMIN' ? 'Go to platform console' : 'Go to dashboard') : 'Log in';

  return (
    <div className="not-found-page">
      <img alt="" aria-hidden className="not-found-illustration" src={emptyStateIllustrations.notFound} />
      <p className="not-found-code">404</p>
      <h1 className="not-found-title">Page not found</h1>
      <p className="not-found-message">
        We searched every aisle, checked receiving, and asked the forklifts. That page is not in inventory.
      </p>
      <Button className="mt-6" onClick={() => navigate(homeTarget)} type="button">
        {homeLabel}
      </Button>
    </div>
  );
}
