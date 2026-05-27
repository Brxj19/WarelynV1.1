import { MoreHorizontal } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export function ActionMenu({ items = [] }) {
  const ref = useRef(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    function handlePointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) setIsOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  if (!items.length) return null;

  return (
    <div className="action-menu" ref={ref}>
      <button aria-label="More actions" className="action-menu-trigger" onClick={() => setIsOpen((value) => !value)} title="More actions" type="button">
        <MoreHorizontal size={16} />
      </button>
      {isOpen ? (
        <div className="action-menu-popover">
          {items.map((item) => (
            <button
              className={`action-menu-item ${item.danger ? 'is-danger' : ''}`}
              disabled={item.disabled}
              key={item.label}
              onClick={() => {
                if (item.disabled) return;
                item.onClick?.();
                setIsOpen(false);
              }}
              title={item.disabledReason ?? item.label}
              type="button"
            >
              {item.icon ? <item.icon size={15} /> : null}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
