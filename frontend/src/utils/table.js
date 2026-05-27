const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });

export function getNextSort(currentSort, key, defaultDirection = 'asc') {
  if (!currentSort || currentSort.key !== key) {
    return { key, direction: defaultDirection };
  }

  return {
    key,
    direction: currentSort.direction === 'asc' ? 'desc' : 'asc',
  };
}

export function sortRows(rows, sortState, definitions = {}) {
  if (!sortState?.key) return rows;

  const definition = definitions[sortState.key] ?? {};
  const type = definition.type ?? inferSortType(sortState.key);
  const direction = sortState.direction === 'desc' ? -1 : 1;

  return [...rows].sort((left, right) => {
    const leftValue = getSortValue(left, sortState.key, definition);
    const rightValue = getSortValue(right, sortState.key, definition);
    return compareValues(leftValue, rightValue, type) * direction;
  });
}

export function hasDateRange(range) {
  return Boolean(range?.from || range?.to);
}

export function getDateRangeLabel(range) {
  if (!range?.from && !range?.to) return '';
  if (range.from && range.to) return `${range.from} to ${range.to}`;
  if (range.from) return `From ${range.from}`;
  return `Until ${range.to}`;
}

export function isDateInRange(value, range) {
  if (!value) return false;
  if (!range?.from && !range?.to) return true;

  const current = new Date(value);
  if (Number.isNaN(current.getTime())) return false;

  if (range.from) {
    const from = new Date(range.from);
    from.setHours(0, 0, 0, 0);
    if (current < from) return false;
  }

  if (range.to) {
    const to = new Date(range.to);
    to.setHours(23, 59, 59, 999);
    if (current > to) return false;
  }

  return true;
}

export function inferSortType(key) {
  if (!key) return 'text';
  if (key.includes('created_at') || key.endsWith('_date') || key === 'expiry_date' || key === 'expires_on' || key === 'warranty_until') return 'date';
  if (
    key.includes('quantity') ||
    key.includes('on_hand') ||
    key.includes('reserved') ||
    key.includes('available') ||
    key.includes('value') ||
    key.includes('cost') ||
    key.includes('price') ||
    key.includes('level') ||
    key.includes('count') ||
    key.includes('delta') ||
    key.includes('days')
  ) {
    return 'number';
  }
  return 'text';
}

function getSortValue(row, key, definition) {
  if (typeof definition.accessor === 'function') {
    return definition.accessor(row);
  }
  return row[key];
}

function compareValues(leftValue, rightValue, type) {
  const leftEmpty = leftValue === null || leftValue === undefined || leftValue === '';
  const rightEmpty = rightValue === null || rightValue === undefined || rightValue === '';

  if (leftEmpty && rightEmpty) return 0;
  if (leftEmpty) return 1;
  if (rightEmpty) return -1;

  if (type === 'number') {
    const leftNumber = Number(leftValue);
    const rightNumber = Number(rightValue);
    if (!Number.isNaN(leftNumber) && !Number.isNaN(rightNumber)) {
      return leftNumber - rightNumber;
    }
  }

  if (type === 'date') {
    const leftDate = new Date(leftValue).getTime();
    const rightDate = new Date(rightValue).getTime();
    if (!Number.isNaN(leftDate) && !Number.isNaN(rightDate)) {
      return leftDate - rightDate;
    }
  }

  return collator.compare(String(leftValue), String(rightValue));
}
