import { SlidersHorizontal, X } from 'lucide-react';

export function ActiveFilterChips({ filters = [] }) {
  const visibleFilters = filters.filter(Boolean);

  if (!visibleFilters.length) return null;

  return (
    <div className="screen-toolbar-filter-chips">
      {visibleFilters.map((filter) => (
        <span className="filter-chip" key={`${filter.key}-${filter.label}`}>
          <SlidersHorizontal size={12} />
          {filter.label}
          {filter.onRemove ? (
            <button aria-label={`Remove ${filter.label}`} onClick={filter.onRemove} type="button">
              <X size={12} />
            </button>
          ) : null}
        </span>
      ))}
    </div>
  );
}
