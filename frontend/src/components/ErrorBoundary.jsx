import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-8 text-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-md ring-1 ring-slate-200">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="#1E3A8A" />
              <text x="50%" y="55%" dominantBaseline="middle" textAnchor="middle" fill="white" fontSize="14" fontWeight="bold">W</text>
            </svg>
          </div>
          <h1 className="text-xl font-bold text-slate-800">Something went wrong</h1>
          <p className="mt-2 max-w-sm text-sm text-slate-500">
            An unexpected error occurred. Please refresh the page to continue.
          </p>
          <button
            className="mt-6 rounded-xl bg-blue-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-800"
            onClick={() => window.location.reload()}
            type="button"
          >
            Refresh the page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
