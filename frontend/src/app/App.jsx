import { AppRoutes } from '../routes/AppRoutes.jsx';
import { ToastContainer } from '../components/ui/Toast.jsx';
import { ErrorBoundary } from '../components/ErrorBoundary.jsx';
import { useToast } from '../hooks/useToast.jsx';
import { useLocation } from 'react-router-dom';

function ToastLayer() {
  const { toasts, removeToast } = useToast();
  return <ToastContainer onDismiss={removeToast} toasts={toasts} />;
}

export function App() {
  const location = useLocation();

  return (
    <ErrorBoundary resetKey={location.pathname}>
      <AppRoutes />
      <ToastLayer />
    </ErrorBoundary>
  );
}
