import { Inbox } from 'lucide-react';

import { Button } from './Button.jsx';

/* Legacy inline SVG illustrations for backward compatibility */
const legacyIllustrations = {
  warehouse: (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="8" y="24" width="48" height="32" rx="4" fill="#EFF6FF" stroke="#1E3A8A" strokeWidth="2"/>
      <path d="M8 28L32 12L56 28" stroke="#1E3A8A" strokeWidth="2" strokeLinecap="round"/>
      <rect x="20" y="36" width="10" height="12" rx="2" fill="#BFDBFE" stroke="#1E3A8A" strokeWidth="1.5"/>
      <rect x="34" y="36" width="10" height="12" rx="2" fill="#BFDBFE" stroke="#1E3A8A" strokeWidth="1.5"/>
      <rect x="26" y="48" width="12" height="8" fill="#EFF6FF" stroke="#1E3A8A" strokeWidth="1.5"/>
    </svg>
  ),
  clipboard: (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="14" y="10" width="36" height="46" rx="4" fill="#EFF6FF" stroke="#1E3A8A" strokeWidth="2"/>
      <rect x="24" y="6" width="16" height="8" rx="3" fill="#BFDBFE" stroke="#1E3A8A" strokeWidth="1.5"/>
      <line x1="22" y1="26" x2="42" y2="26" stroke="#1E3A8A" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="22" y1="34" x2="38" y2="34" stroke="#93C5FD" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="22" y1="42" x2="40" y2="42" stroke="#93C5FD" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  bell: (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M32 8C24 8 18 14 18 22V34L14 40H50L46 34V22C46 14 40 8 32 8Z" fill="#EFF6FF" stroke="#1E3A8A" strokeWidth="2"/>
      <path d="M26 44C26 47.3 28.7 50 32 50C35.3 50 38 47.3 38 44" stroke="#1E3A8A" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="44" cy="16" r="6" fill="#BFDBFE" stroke="#1E3A8A" strokeWidth="1.5"/>
    </svg>
  ),
};

const SIZES = {
  sm: { wrapper: 'min-h-[180px] px-4 py-6', img: 'mb-4 w-28 sm:w-32', title: 'text-base', message: 'text-sm mt-2' },
  default: { wrapper: 'min-h-[280px] px-6 py-12', img: 'mb-8 w-44 sm:w-56', title: 'text-xl', message: 'text-base mt-3' },
  lg: { wrapper: 'min-h-[400px] px-8 py-16', img: 'mb-10 w-56 sm:w-72', title: 'text-2xl', message: 'text-base mt-4' },
};

export function EmptyState({
  action,
  actionLabel,
  className = '',
  description,
  icon: Icon = Inbox,
  illustration,
  message,
  onAction,
  onSecondaryAction,
  secondaryActionLabel,
  size,
  title = 'Nothing here yet',
}) {
  /* Resolve display message: prefer `message` prop, fall back to `description` for legacy callers */
  const displayMessage = message || description || '';

  /* Determine if this is a "new-style" call (with size or image-src illustration) */
  const isNewStyle = size || (illustration && typeof illustration === 'string' && !legacyIllustrations[illustration]);

  /* Legacy rendering path — preserves existing behavior for current consumers */
  if (!isNewStyle) {
    return (
      <div className={`rounded-2xl border border-dashed border-warelyn-border bg-slate-50/70 p-8 text-center ${className}`}>
        {illustration && legacyIllustrations[illustration] ? (
          <div className="mx-auto mb-4 flex items-center justify-center">
            {legacyIllustrations[illustration]}
          </div>
        ) : (
          <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-warelyn-border">
            <Icon className="text-warelyn-primary" size={18} />
          </div>
        )}
        <h3 className="font-display text-base font-semibold text-warelyn-text">{title}</h3>
        {displayMessage && <p className="font-display mx-auto mt-2 max-w-md text-sm text-warelyn-muted">{displayMessage}</p>}
        {action ? <div className="mt-5">{action}</div> : null}
        {(actionLabel || secondaryActionLabel) && (
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            {actionLabel && onAction && (
              <Button variant="primary" onClick={onAction}>{actionLabel}</Button>
            )}
            {secondaryActionLabel && onSecondaryAction && (
              <Button variant="ghost" onClick={onSecondaryAction}>{secondaryActionLabel}</Button>
            )}
          </div>
        )}
      </div>
    );
  }

  /* New-style rendering with size variants and SVG image illustrations */
  const s = SIZES[size] || SIZES.default;

  return (
    <div className={`flex flex-col items-center justify-center text-center ${s.wrapper} ${className}`}>
      {illustration && (
        <img
          src={illustration}
          alt=""
          aria-hidden="true"
          className={`${s.img} max-w-full`}
        />
      )}
      <h3 className={`font-display ${s.title} font-bold tracking-tight text-warelyn-text`}>
        {title}
      </h3>
      {displayMessage && (
        <p className={`font-display ${s.message} max-w-md leading-7 text-warelyn-muted`}>
          {displayMessage}
        </p>
      )}
      {(actionLabel || secondaryActionLabel || action) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {actionLabel && onAction && (
            <Button variant="primary" onClick={onAction}>{actionLabel}</Button>
          )}
          {secondaryActionLabel && onSecondaryAction && (
            <Button variant="ghost" onClick={onSecondaryAction}>{secondaryActionLabel}</Button>
          )}
          {action}
        </div>
      )}
    </div>
  );
}
