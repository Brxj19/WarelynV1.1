import { Link } from 'react-router-dom';

import { Badge } from '../components/ui/Badge.jsx';
import { Card, CardBody, CardHeader } from '../components/ui/Card.jsx';

const modules = [
  ['Products', '/catalog/products', 'SKU, barcode, unit, price, and tracking flags.'],
  ['Categories', '/catalog/categories', 'Tenant-specific product grouping.'],
  ['Brands', '/catalog/brands', 'Tenant-specific product brands.'],
  ['Vendors', '/catalog/vendors', 'Supplier master records for purchasing.'],
  ['Customers', '/catalog/customers', 'Customer master records for sales.'],
];

export function CatalogPage() {
  return (
    <div className="space-y-6">
      <div>
        <Badge tone="primary">Tenant Catalog</Badge>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-warelyn-text">Catalog foundation</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-warelyn-muted">Manage tenant-scoped master data. These records do not calculate or mutate stock.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {modules.map(([title, to, description]) => (
          <Link key={to} to={to}>
            <Card className="h-full transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md">
              <CardHeader>
                <h2 className="text-lg font-semibold text-warelyn-text">{title}</h2>
              </CardHeader>
              <CardBody>
                <p className="text-sm leading-6 text-warelyn-muted">{description}</p>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
