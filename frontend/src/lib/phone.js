export const COUNTRY_CODES = [
  { code: '+91', country: 'India', flag: '🇮🇳', digits: 10 },
  { code: '+1', country: 'USA/Canada', flag: '🇺🇸', digits: 10 },
  { code: '+44', country: 'UK', flag: '🇬🇧', digits: { min: 7, max: 10 } },
  { code: '+61', country: 'Australia', flag: '🇦🇺', digits: 9 },
  { code: '+971', country: 'UAE', flag: '🇦🇪', digits: 9 },
  { code: '+65', country: 'Singapore', flag: '🇸🇬', digits: 8 },
  { code: '+81', country: 'Japan', flag: '🇯🇵', digits: { min: 9, max: 10 } },
  { code: '+49', country: 'Germany', flag: '🇩🇪', digits: { min: 10, max: 11 } },
  { code: '+33', country: 'France', flag: '🇫🇷', digits: 9 },
  { code: '+86', country: 'China', flag: '🇨🇳', digits: 11 },
];

export function stripNonDigits(value) {
  return value.replace(/\D/g, '');
}

export function normalizePhone(countryCode, localNumber) {
  const digits = stripNonDigits(localNumber);
  if (!digits) return '';
  return `${countryCode}${digits}`;
}

export function isValidPhone(countryCode, localNumber) {
  const digits = stripNonDigits(localNumber);
  if (!digits) return { valid: false, error: 'Phone number is required.' };

  const country = COUNTRY_CODES.find((c) => c.code === countryCode);
  if (!country) {
    if (digits.length < 6 || digits.length > 15) {
      return { valid: false, error: 'Phone number must be 6-15 digits.' };
    }
    return { valid: true, error: '' };
  }

  if (typeof country.digits === 'number') {
    if (digits.length !== country.digits) {
      return { valid: false, error: `Phone number for ${country.country} must be ${country.digits} digits.` };
    }
  } else {
    if (digits.length < country.digits.min || digits.length > country.digits.max) {
      return { valid: false, error: `Phone number for ${country.country} must be ${country.digits.min}-${country.digits.max} digits.` };
    }
  }

  return { valid: true, error: '' };
}

export function parsePhone(fullNumber) {
  if (!fullNumber) return { countryCode: '+91', localNumber: '' };
  // Try to match known country codes (longest first)
  const sorted = [...COUNTRY_CODES].sort((a, b) => b.code.length - a.code.length);
  for (const c of sorted) {
    if (fullNumber.startsWith(c.code)) {
      return { countryCode: c.code, localNumber: fullNumber.slice(c.code.length) };
    }
  }
  // Fallback: assume +91
  if (fullNumber.startsWith('+')) {
    return { countryCode: '+91', localNumber: fullNumber.slice(3) };
  }
  return { countryCode: '+91', localNumber: fullNumber };
}
