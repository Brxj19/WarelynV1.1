import { useId } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from './Button.jsx';

export function PaginationControls({
  page,
  pageCount,
  pageSize,
  pageSizeOptions = [10, 25, 50, 100],
  setPage,
  setPageSize,
  totalRows,
}) {
  const pageSizeId = useId();
  const start = totalRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(totalRows, page * pageSize);

  return (
    <div className="flex flex-col gap-3 border-t border-warelyn-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-warelyn-muted">
        Showing <span className="font-semibold text-warelyn-text">{start}</span>-<span className="font-semibold text-warelyn-text">{end}</span> of{' '}
        <span className="font-semibold text-warelyn-text">{totalRows}</span>
      </p>
      <div className="flex items-center gap-2">
        <label className="text-xs text-warelyn-muted" htmlFor={pageSizeId}>
          Rows
        </label>
        <select
          className="rounded-md border border-warelyn-border bg-white px-2 py-1 text-xs text-warelyn-text"
          id={pageSizeId}
          onChange={(event) => setPageSize(Number(event.target.value))}
          value={pageSize}
        >
          {pageSizeOptions.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
        <Button
          className="px-2 py-1"
          disabled={page <= 1}
          onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          size="sm"
          variant="ghost"
        >
          <ChevronLeft size={14} />
        </Button>
        <span className="min-w-[70px] text-center text-xs font-medium text-warelyn-text">
          Page {page} / {pageCount}
        </span>
        <Button
          className="px-2 py-1"
          disabled={page >= pageCount}
          onClick={() => setPage((prev) => Math.min(pageCount, prev + 1))}
          size="sm"
          variant="ghost"
        >
          <ChevronRight size={14} />
        </Button>
      </div>
    </div>
  );
}
