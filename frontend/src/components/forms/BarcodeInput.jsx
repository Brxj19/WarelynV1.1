import { ScanLine, X } from 'lucide-react';

export function BarcodeInput({ hint = 'Scan or paste a product barcode.', id, label = 'Barcode', onChange, onKeyDown, value = '', ...props }) {
  return (
    <label className="block" htmlFor={id}>
      <span className="mb-2 block text-sm font-medium text-warelyn-text">{label}</span>
      <div className="barcode-input-shell">
        <ScanLine className="barcode-input-icon" size={17} />
        <input
          autoComplete="off"
          className="barcode-input-field"
          id={id}
          inputMode="text"
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder="Scan barcode"
          value={value}
          {...props}
        />
        {value ? (
          <button
            aria-label="Clear barcode"
            className="barcode-input-clear"
            onClick={() => onChange?.({ target: { value: '' } })}
            type="button"
          >
            <X size={15} />
          </button>
        ) : null}
      </div>
      <p className="mt-1.5 text-xs text-warelyn-muted">{hint}</p>
    </label>
  );
}
