import { useEffect, useMemo, useRef, useState } from 'react';
import { LoaderCircle, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext.jsx';
import * as catalogService from '../services/catalogService.js';
import * as fulfillmentService from '../services/fulfillmentService.js';
import * as purchasingService from '../services/purchasingService.js';
import * as returnsService from '../services/returnsService.js';
import * as salesService from '../services/salesService.js';
import * as warehouseService from '../services/warehouseService.js';

export function TopbarSearch({ navItems, recordsEnabled = true }) {
  const navigate = useNavigate();
  const { accessToken } = useAuth();
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [results, setResults] = useState([]);

  const trimmedQuery = query.trim();
  const sectionResults = useMemo(() => {
    if (trimmedQuery.length < 2) return navItems.slice(0, 6);
    const value = trimmedQuery.toLowerCase();
    return navItems
      .filter((item) => `${item.label} ${item.section}`.toLowerCase().includes(value))
      .map((item) => ({
        icon: item.icon,
        label: item.label,
        meta: item.section,
        to: item.to,
      }));
  }, [navItems, trimmedQuery]);

  useEffect(() => {
    function handlePointerDown(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) setIsOpen(false);
    }
    function handleKeyDown(event) {
      const tagName = document.activeElement?.tagName;
      if (event.key === '/' && tagName !== 'INPUT' && tagName !== 'TEXTAREA') {
        event.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      }
      if (event.key === 'Escape') setIsOpen(false);
    }

    document.addEventListener('pointerdown', handlePointerDown);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (!isOpen) return undefined;
    if (trimmedQuery.length < 2) {
      setStatus('idle');
      setErrorMessage('');
      setResults([]);
      return undefined;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      if (!recordsEnabled) {
        setResults(sectionResults.slice(0, 8));
        setStatus('success');
        return;
      }

      setStatus('loading');
      setErrorMessage('');
      try {
        const [products, vendors, customers, warehouses, purchaseOrders, salesOrders, salesReturns, pickTasks] = await Promise.all([
          catalogService.listProducts(accessToken, trimmedQuery),
          catalogService.listVendors(accessToken),
          catalogService.listCustomers(accessToken),
          warehouseService.listWarehouses(accessToken),
          purchasingService.listPurchaseOrders(accessToken),
          salesService.listSalesOrders(accessToken),
          returnsService.listSalesReturns(accessToken),
          fulfillmentService.listPickTasks(accessToken),
        ]);

        if (cancelled) return;
        const value = trimmedQuery.toLowerCase();
        const dynamicResults = [
          ...products.slice(0, 3).map((product) => ({
            icon: navItems.find((item) => item.to === '/catalog/products')?.icon,
            label: product.name,
            meta: `Product ${product.sku ? `• ${product.sku}` : ''}`.trim(),
            to: '/catalog/products',
          })),
          ...filterByText(vendors, value, ['name', 'email']).slice(0, 2).map((vendor) => ({
            icon: navItems.find((item) => item.to === '/catalog/vendors')?.icon,
            label: vendor.name,
            meta: 'Vendor directory',
            to: '/catalog/vendors',
          })),
          ...filterByText(customers, value, ['name', 'email']).slice(0, 2).map((customer) => ({
            icon: navItems.find((item) => item.to === '/catalog/customers')?.icon,
            label: customer.name,
            meta: 'Customer directory',
            to: '/catalog/customers',
          })),
          ...filterByText(warehouses, value, ['name', 'code']).slice(0, 3).map((warehouse) => ({
            icon: navItems.find((item) => item.to === '/warehouses')?.icon,
            label: warehouse.name,
            meta: warehouse.code ? `Warehouse • ${warehouse.code}` : 'Warehouse',
            to: `/warehouses/${warehouse.id}`,
          })),
          ...filterByText(purchaseOrders, value, ['po_number', 'status']).slice(0, 2).map((order) => ({
            icon: navItems.find((item) => item.to === '/purchases')?.icon,
            label: order.po_number,
            meta: `Purchase order • ${order.status}`,
            to: `/purchases/${order.id}`,
          })),
          ...filterByText(salesOrders, value, ['order_number', 'status']).slice(0, 2).map((order) => ({
            icon: navItems.find((item) => item.to === '/sales')?.icon,
            label: order.order_number,
            meta: `Sales order • ${order.status}`,
            to: `/sales/${order.id}`,
          })),
          ...filterByText(salesReturns, value, ['return_number', 'status']).slice(0, 2).map((salesReturn) => ({
            icon: navItems.find((item) => item.to === '/returns')?.icon,
            label: salesReturn.return_number,
            meta: `Return • ${salesReturn.status}`,
            to: `/returns/${salesReturn.id}`,
          })),
          ...filterByText(pickTasks, value, ['pick_number', 'status']).slice(0, 2).map((task) => ({
            icon: navItems.find((item) => item.to === '/pick-tasks')?.icon,
            label: task.pick_number,
            meta: `Pick task • ${task.status}`,
            to: `/pick-tasks/${task.id}`,
          })),
        ];

        const merged = dedupeResults([...dynamicResults, ...sectionResults]).slice(0, 8);
        setResults(merged);
        setStatus('success');
      } catch (error) {
        if (cancelled) return;
        setResults(sectionResults.slice(0, 8));
        setStatus('error');
        setErrorMessage(error.message || 'Unable to search right now.');
      }
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [accessToken, isOpen, navItems, recordsEnabled, sectionResults, trimmedQuery]);

  function openResult(item) {
    navigate(item.to);
    setIsOpen(false);
    setQuery('');
  }

  const firstResult = results[0] ?? sectionResults[0];

  return (
    <div className="topbar-search" ref={wrapperRef}>
      <Search className="search-icon" size={17} />
      <input
        onChange={(event) => setQuery(event.target.value)}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && firstResult) {
            event.preventDefault();
            openResult(firstResult);
          }
        }}
        placeholder="Search products, orders, vendors, customers, warehouses..."
        ref={inputRef}
        value={query}
      />
      <span className="search-shortcut">/</span>

      {isOpen ? (
        <div className="topbar-popover search-popover">
          <h3>Global search</h3>
          <p>Jump to records or app sections</p>

          {trimmedQuery.length < 2 ? (
            <div className="popover-empty">Type at least 2 characters to search across sections and key records.</div>
          ) : null}

          {status === 'loading' ? (
            <div className="popover-empty">
              <span className="inline-flex items-center gap-2">
                <LoaderCircle className="animate-spin" size={16} />
                Searching Warelyn...
              </span>
            </div>
          ) : null}

          {status === 'error' ? <div className="popover-empty">{errorMessage}</div> : null}

          {trimmedQuery.length >= 2 && status !== 'loading' && results.length === 0 ? (
            <div className="popover-empty">No results matched that search.</div>
          ) : null}

          {trimmedQuery.length >= 2 && status !== 'loading' && results.length > 0 ? (
            <div className="topbar-popover-list">
              {results.map((item) => {
                const Icon = item.icon ?? Search;
                return (
                  <button className="popover-row" key={`${item.to}-${item.label}`} onClick={() => openResult(item)} type="button">
                    <Icon size={16} />
                    <span>
                      <strong>{item.label}</strong>
                      <small>{item.meta}</small>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function filterByText(rows, query, fields) {
  return rows.filter((row) =>
    fields.some((field) => {
      const value = row[field];
      return typeof value === 'string' && value.toLowerCase().includes(query);
    }),
  );
}

function dedupeResults(results) {
  const seen = new Set();
  return results.filter((result) => {
    const key = `${result.to}:${result.label}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
