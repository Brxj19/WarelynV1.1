import { AppRoutes } from '../routes/AppRoutes.jsx';
import { ToastContainer } from '../components/ui/Toast.jsx';
import { ErrorBoundary } from '../components/ErrorBoundary.jsx';
import { useToast } from '../hooks/useToast.jsx';

function ToastLayer() {
  const { toasts, removeToast } = useToast();
  return <ToastContainer onDismiss={removeToast} toasts={toasts} />;
}

export function App() {
  return (
    <ErrorBoundary>
      <AppRoutes />
      <ToastLayer />
    </ErrorBoundary>
  );
}
