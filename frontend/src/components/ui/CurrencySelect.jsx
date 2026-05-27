import { CURRENCIES } from '../../lib/currencies.js';

export function CurrencySelect({ value, onChange, disabled, className }) {
  return (
    <div className={className}>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-warelyn-text">Currency</span>
        <select
          value={value || 'USD'}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="block w-full rounded-lg border border-warelyn-border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:border-warelyn-primary focus:ring-4 focus:ring-blue-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {CURRENCIES.map((c) => (
            <option key={c.code} value={c.code}>
              {c.code} — {c.name}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
