import { Children, cloneElement, isValidElement, useEffect, useMemo, useState } from 'react';

import { EmptyState } from './EmptyState.jsx';
import { ErrorState } from './ErrorState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { PaginationControls } from './PaginationControls.jsx';

function countTableRows(node) {
  if (!isValidElement(node)) return 0;
  if (node.type === 'tbody') {
    return Children.toArray(node.props.children).length;
  }
  return Children.toArray(node.props.children).reduce((sum, child) => sum + countTableRows(child), 0);
}

function extractNodeText(node) {
  if (node === null || node === undefined || typeof node === 'boolean') return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (!isValidElement(node)) return '';
  return Children.toArray(node.props?.children)
    .map((child) => extractNodeText(child))
    .join(' ');
}

function normalize(value) {
  return value.toLowerCase().replace(/\s+/g, ' ').trim();
}

function rowMatchesQuery(row, query) {
  if (!query) return true;
  const haystack = normalize(extractNodeText(row));
  return query.split(' ').every((term) => haystack.includes(term));
}

function sliceTableRows(node, start, end) {
  if (!isValidElement(node)) return node;
  if (node.type === 'tbody') {
    const rows = Children.toArray(node.props.children);
    return cloneElement(node, node.props, rows.slice(start, end));
  }
  if (!node.props?.children) return node;
  return cloneElement(
    node,
    node.props,
    Children.map(node.props.children, (child) => sliceTableRows(child, start, end)),
  );
}

function filterTableRows(node, query) {
  if (!isValidElement(node)) return node;
  if (node.type === 'tbody') {
    const rows = Children.toArray(node.props.children);
    const filteredRows = rows.filter((row) => rowMatchesQuery(row, query));
    return cloneElement(node, node.props, filteredRows);
  }
  if (!node.props?.children) return node;
  return cloneElement(
    node,
    node.props,
    Children.map(node.props.children, (child) => filterTableRows(child, query)),
  );
}

export function TableShell({
  actions,
  children,
  description,
  emptyAction,
  emptyActionLabel,
  emptyDescription = 'No rows match this view.',
  emptyIllustration,
  emptySecondaryActionLabel,
  emptyTitle = 'No rows',
  error,
  isEmpty = false,
  isLoading = false,
  onEmptyAction,
  onEmptySecondaryAction,
  rowCount,
  title,
  toolbar,
  paginated = true,
  initialPageSize = 10,
  filterable = true,
  filterPlaceholder = 'Filter table...',
}) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [query, setQuery] = useState('');
  const normalizedQuery = useMemo(() => normalize(query), [query]);
  const detectedRowCount = useMemo(() => countTableRows(children), [children]);
  const filteredChildren = useMemo(() => {
    if (!filterable || !normalizedQuery) return children;
    return filterTableRows(children, normalizedQuery);
  }, [children, filterable, normalizedQuery]);
  const filteredRowCount = useMemo(() => countTableRows(filteredChildren), [filteredChildren]);
  const totalRows = rowCount ?? detectedRowCount;
  const pageCount = Math.max(1, Math.ceil((filteredRowCount || 0) / pageSize));

  useEffect(() => {
    setPage(1);
  }, [filteredRowCount, pageSize]);

  useEffect(() => {
    if (page > pageCount) {
      setPage(pageCount);
    }
  }, [page, pageCount]);

  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const renderedChildren = useMemo(() => {
    if (!paginated || filteredRowCount <= pageSize) return filteredChildren;
    return sliceTableRows(filteredChildren, startIndex, endIndex);
  }, [endIndex, filteredChildren, filteredRowCount, pageSize, paginated, startIndex]);

  return (
    <section className="table-shell">
      <div className="table-header">
        <div>
          <div className="table-title-row">
            <h2>{title}</h2>
            {totalRows !== undefined ? (
              <span className="table-row-count">
                {filterable && normalizedQuery ? `${filteredRowCount}/${totalRows}` : totalRows}
              </span>
            ) : null}
          </div>
          {description ? <p>{description}</p> : null}
        </div>
        {actions ? <div className="table-header-actions">{actions}</div> : null}
      </div>
      {toolbar ? <div className="table-toolbar">{toolbar}</div> : null}
      {filterable && !isLoading && !error && !isEmpty ? (
        <div className="table-search-shell">
          <input
            className="table-search-input"
            onChange={(event) => setQuery(event.target.value)}
            placeholder={filterPlaceholder}
            value={query}
          />
        </div>
      ) : null}
      {isLoading ? <LoadingState variant="table" /> : null}
      {!isLoading && error ? <ErrorState description={error} /> : null}
      {!isLoading && !error && isEmpty ? (
        <EmptyState
          action={emptyAction}
          actionLabel={emptyActionLabel}
          illustration={emptyIllustration}
          message={emptyDescription}
          onAction={onEmptyAction}
          onSecondaryAction={onEmptySecondaryAction}
          secondaryActionLabel={emptySecondaryActionLabel}
          size="default"
          title={emptyTitle}
        />
      ) : null}
      {!isLoading && !error && !isEmpty ? (
        <>
          <div className="table-scroll overflow-x-auto">{renderedChildren}</div>
          {paginated && detectedRowCount > 0 ? (
            <PaginationControls
              page={page}
              pageCount={pageCount}
              pageSize={pageSize}
              pageSizeOptions={[10, 25, 50, 100]}
              setPage={setPage}
              setPageSize={setPageSize}
              totalRows={filteredRowCount}
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}
