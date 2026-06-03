const sources = {
  full: '/warelyn-logo.png',
  collapsed: '/collapsed-sidebar-logo.png',
  mark: '/warelyn-logo.png',
};

const dimensions = {
  full: { width: 250, height: 150 },
  collapsed: { width: 100, height: 100 },
  mark: { width: 250, height: 150 },
};

const placementSizes = {
  topbar: { width: 96, height: 28 },
  sidebar: { width: 154, height: 46 },
  'sidebar-collapsed': { width: 54, height: 54 },
  auth: { width: 144, height: 42 },
  'auth-form': { width: 132, height: 38 },
  'landing-nav': { width: 112, height: 32 },
  'landing-hero': { width: 168, height: 48 },
  'landing-footer': { width: 108, height: 30 },
};

export function AppLogo({ alt = 'Warelyn', className = '', imageClassName = '', size = 'sidebar', variant = 'full' }) {
  const asset = sources[variant] ?? sources.full;
  const dimension = dimensions[variant] ?? dimensions.full;
  const placement = placementSizes[size];

  return (
    <span
      className={`app-logo app-logo--${size} ${className}`}
      data-variant={variant}
      style={placement ? { width: `${placement.width}px`, height: `${placement.height}px`, maxWidth: `${placement.width}px`, maxHeight: `${placement.height}px` } : undefined}
    >
      <span className="app-logo-frame">
        <img
          alt={alt}
          className={`app-logo-image ${imageClassName}`}
          height={dimension.height}
          src={asset}
          style={{ display: 'block', width: '100%', height: '100%', maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
          width={dimension.width}
        />
      </span>
    </span>
  );
}
