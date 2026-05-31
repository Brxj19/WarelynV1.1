export function ChartFilterBar({
  options = [],
  value,
  onChange,
  compareEnabled = false,
  compareValue = false,
  onCompareChange,
  warehouseOptions = [],
  warehouseValue = '',
  onWarehouseChange,
  extra = null,
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div className="inline-flex w-fit items-center gap-1 rounded-lg border border-warelyn-border bg-gray-50 p-0.5">
        {options.map((opt) => {
          const isActive = value === opt.value;
          return (
            <button
              key={String(opt.value)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-white text-warelyn-primary shadow-sm'
                  : 'text-warelyn-muted hover:text-warelyn-text'
              }`}
              onClick={() => onChange?.(opt.value)}
              type="button"
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-2">
        {compareEnabled ? (
          <label className="inline-flex items-center gap-2 rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs text-warelyn-muted">
            <input
              checked={Boolean(compareValue)}
              className="h-3.5 w-3.5 accent-[#1e3a5f]"
              onChange={(event) => onCompareChange?.(event.target.checked)}
              type="checkbox"
            />
            vs prev period
          </label>
        ) : null}

        {warehouseOptions.length > 0 ? (
          <select
            className="rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs text-warelyn-text focus:border-warelyn-primary focus:outline-none"
            onChange={(event) => onWarehouseChange?.(event.target.value ? Number(event.target.value) : null)}
            value={warehouseValue ?? ''}
          >
            <option value="">All warehouses</option>
            {warehouseOptions.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name}
              </option>
            ))}
          </select>
        ) : null}

        {extra}
      </div>
    </div>
  );
}
