import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';

export function SortableHeader({ align = 'left', label, onSort, sortKey, sortState }) {
  const isActive = sortState?.key === sortKey;
  const Icon = !isActive ? ArrowUpDown : sortState.direction === 'asc' ? ArrowUp : ArrowDown;

  return (
    <button
      className={`sortable-header ${align === 'right' ? 'is-right' : ''}`}
      onClick={() => onSort(sortKey)}
      type="button"
    >
      <span>{label}</span>
      <Icon size={14} />
    </button>
  );
}
