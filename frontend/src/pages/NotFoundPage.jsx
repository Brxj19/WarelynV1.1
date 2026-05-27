import { useNavigate } from 'react-router-dom';

import { EmptyState } from '../components/ui/EmptyState.jsx';
import { emptyStateIllustrations } from '../lib/emptyStates.js';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <EmptyState
      illustration={emptyStateIllustrations.notFound}
      title="Page not found"
      message="The page you are looking for does not exist or may have been moved."
      actionLabel="Go to Dashboard"
      onAction={() => navigate('/dashboard')}
      size="lg"
    />
  );
}
