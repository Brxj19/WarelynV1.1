import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock } from 'lucide-react';

import { Button } from './ui/Button.jsx';

export function RecentHistoryMenu({ history }) {
  const navigate = useNavigate();
  const ref = useRef(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    function handlePointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) setIsOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  return (
    <div className="topbar-popover-anchor" ref={ref}>
      <Button aria-label="Recent history" className="topbar-icon-btn" onClick={() => setIsOpen((current) => !current)} title="Recent history" type="button" variant="ghost">
        <Clock size={18} />
      </Button>
      {isOpen ? (
        <div className="topbar-popover topbar-popover-right">
          <h3>Recent History</h3>
          <p>Last visited Warelyn pages</p>
          {history.length ? (
            <div className="topbar-popover-list">
              {history.map((entry) => (
                <button
                  className="popover-row"
                  key={entry.path}
                  onClick={() => {
                    navigate(entry.path);
                    setIsOpen(false);
                  }}
                  type="button"
                >
                  <Clock size={16} />
                  <span>
                    <strong>{entry.label}</strong>
                    <small>{entry.section}</small>
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="popover-empty">Recent pages will appear here as you move through the workspace.</div>
          )}
        </div>
      ) : null}
    </div>
  );
}
