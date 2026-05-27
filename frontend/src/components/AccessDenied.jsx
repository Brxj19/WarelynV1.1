import { ShieldOff } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from './ui/Button.jsx';

export function AccessDenied() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
        <ShieldOff className="text-red-600" size={32} aria-hidden="true" />
      </div>
      <h1 className="text-2xl font-bold text-warelyn-text">Access Denied</h1>
      <p className="mt-2 text-warelyn-muted">You do not have permission to view this page.</p>
      <p className="mt-1 text-sm text-warelyn-muted">Contact your tenant administrator if you need access.</p>
      <Link className="mt-6" to="/dashboard">
        <Button variant="primary">Go to Dashboard</Button>
      </Link>
    </div>
  );
}
