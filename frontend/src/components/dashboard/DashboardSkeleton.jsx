function SkeletonBlock({ className = '' }) {
  return <div className={`animate-pulse rounded-xl bg-gray-200 ${className}`} />;
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SkeletonBlock className="h-28" />
        <SkeletonBlock className="h-28" />
        <SkeletonBlock className="h-28" />
        <SkeletonBlock className="h-28" />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SkeletonBlock className="h-[320px]" />
        <SkeletonBlock className="h-[320px]" />
      </div>

      <SkeletonBlock className="h-[220px]" />
    </div>
  );
}
