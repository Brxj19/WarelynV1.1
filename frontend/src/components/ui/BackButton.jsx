import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const backLabelMatchers = [
  { match: (to) => to.startsWith('/catalog/products'), label: 'Back to Products' },
  { match: (to) => to.startsWith('/catalog/categories'), label: 'Back to Categories' },
  { match: (to) => to.startsWith('/catalog/brands'), label: 'Back to Brands' },
  { match: (to) => to.startsWith('/catalog/vendors'), label: 'Back to Vendors' },
  { match: (to) => to.startsWith('/catalog/customers'), label: 'Back to Customers' },
  { match: (to) => to.startsWith('/warehouses'), label: 'Back to Warehouses' },
  { match: (to) => to.startsWith('/purchase-receipts'), label: 'Back to Purchase Receipts' },
  { match: (to) => to.startsWith('/purchases'), label: 'Back to Purchase Orders' },
  { match: (to) => to.startsWith('/sales-fulfillments'), label: 'Back to Fulfillments' },
  { match: (to) => to.startsWith('/sales'), label: 'Back to Sales Orders' },
  { match: (to) => to.startsWith('/pick-tasks'), label: 'Back to Pick Tasks' },
  { match: (to) => to.startsWith('/packages'), label: 'Back to Packages' },
  { match: (to) => to.startsWith('/returns/qc'), label: 'Back to Returns QC' },
  { match: (to) => to.startsWith('/returns'), label: 'Back to Returns' },
  { match: (to) => to.startsWith('/reports'), label: 'Back to Reports' },
];

export function BackButton({ label, to }) {
  if (!to) return null;

  const resolvedLabel = label || resolveBackLabel(to);

  return (
    <Link className="page-back-link" title={resolvedLabel} to={to}>
      <ArrowLeft size={15} />
      <span>{resolvedLabel}</span>
    </Link>
  );
}

function resolveBackLabel(to) {
  for (const matcher of backLabelMatchers) {
    if (matcher.match(to)) return matcher.label;
  }

  const segments = to.split('/').filter(Boolean);
  if (!segments.length) return 'Back';

  let target = segments.at(-1);
  if (/^\d+$/.test(target) && segments.length > 1) {
    target = segments.at(-2);
  }

  return `Back to ${target
    .replaceAll('-', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())}`;
}
