import { ChevronDown } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { COUNTRY_CODES, isValidPhone, normalizePhone, parsePhone, stripNonDigits } from '../../lib/phone.js';

export function PhoneInput({ value = '', onChange, disabled = false, required = false, error: externalError, label, className = '' }) {
  const parsed = useMemo(() => parsePhone(value), [value]);
  const [countryCode, setCountryCode] = useState(parsed.countryCode);
  const [localNumber, setLocalNumber] = useState(parsed.localNumber);
  const [touched, setTouched] = useState(false);

  // Sync internal state when value prop changes externally
  useEffect(() => {
    const p = parsePhone(value);
    setCountryCode(p.countryCode);
    setLocalNumber(p.localNumber);
  }, [value]);

  function handleCountryChange(e) {
    const newCode = e.target.value;
    setCountryCode(newCode);
    const normalized = normalizePhone(newCode, localNumber);
    if (onChange) onChange(normalized);
  }

  function handleNumberChange(e) {
    const raw = e.target.value;
    const digits = stripNonDigits(raw);
    setLocalNumber(digits);
    const normalized = normalizePhone(countryCode, digits);
    if (onChange) onChange(normalized);
  }

  function handleBlur() {
    setTouched(true);
  }

  // Determine validation error to display
  let displayError = externalError || '';
  if (!displayError && touched && localNumber) {
    const result = isValidPhone(countryCode, localNumber);
    if (!result.valid) displayError = result.error;
  }

  const selectedCountry = COUNTRY_CODES.find((c) => c.code === countryCode);

  return (
    <div className={`block ${className}`}>
      {label ? <span className="mb-2 block text-sm font-medium text-warelyn-text">{label}</span> : null}
      <div className="flex gap-2">
        {/* Country code dropdown */}
        <div className="relative">
          <select
            value={countryCode}
            onChange={handleCountryChange}
            disabled={disabled}
            aria-label="Country code"
            className={`appearance-none rounded-lg border bg-white pl-3 pr-8 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition focus:ring-4 ${
              displayError
                ? 'border-red-300 focus:border-warelyn-danger focus:ring-red-100'
                : 'border-warelyn-border focus:border-warelyn-primary focus:ring-blue-900/10'
            } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {COUNTRY_CODES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.flag} {c.code}
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-slate-400" />
        </div>

        {/* Local number input */}
        <input
          type="tel"
          inputMode="numeric"
          value={localNumber}
          onChange={handleNumberChange}
          onBlur={handleBlur}
          disabled={disabled}
          required={required}
          placeholder={selectedCountry ? `${typeof selectedCountry.digits === 'number' ? selectedCountry.digits : selectedCountry.digits.min} digits` : 'Phone number'}
          className={`block w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-warelyn-text shadow-sm outline-none transition placeholder:text-slate-400 focus:ring-4 ${
            displayError
              ? 'border-red-300 focus:border-warelyn-danger focus:ring-red-100'
              : 'border-warelyn-border focus:border-warelyn-primary focus:ring-blue-900/10'
          } ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
          aria-label={label ? `${label} number` : 'Phone number'}
        />
      </div>
      {displayError ? <p className="mt-1.5 text-xs font-medium text-warelyn-danger">{displayError}</p> : null}
    </div>
  );
}
