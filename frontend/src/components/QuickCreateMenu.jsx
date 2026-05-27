import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';

import { quickCreateItems, canSee } from './navigation.js';
import { Button } from './ui/Button.jsx';

export function QuickCreateMenu({ role }) {
  const navigate = useNavigate();
  const ref = useRef(null);
  const [isOpen, setIsOpen] = useState(false);
  const entries = quickCreateItems.filter((item) => canSee(item, role));

  if (!entries.length) return null;

  useEffect(() => {
    function handlePointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) setIsOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  return (
    <div className="topbar-popover-anchor" ref={ref}>
      <Button className="topbar-primary-action" onClick={() => setIsOpen((current) => !current)} type="button">
        <Plus size={17} />
        <span className="hidden xl:inline">Quick Create</span>
      </Button>
      {isOpen ? (
        <div className="topbar-popover topbar-popover-right">
          <h3>Quick Create</h3>
          <p>Jump into common workflows</p>
          <div className="topbar-popover-list">
            {entries.map((entry) => (
              <button
                className="popover-row"
                key={entry.label}
                onClick={() => {
                  navigate(entry.to);
                  setIsOpen(false);
                }}
                type="button"
              >
                <entry.icon size={16} />
                <span>
                  <strong>{entry.label}</strong>
                  <small>Open workflow</small>
                </span>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
