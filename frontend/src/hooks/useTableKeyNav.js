import { useEffect } from 'react';

/**
 * Hook that adds keyboard navigation (arrow up/down, Enter) to table rows
 * within a container element.
 *
 * @param {React.RefObject} containerRef - Ref to the container element holding the table
 * @param {string} rowSelector - CSS selector for focusable rows (default: 'tbody tr')
 */
export function useTableKeyNav(containerRef, rowSelector = 'tbody tr') {
  useEffect(() => {
    const container = containerRef?.current;
    if (!container) return;

    function getRows() {
      return Array.from(container.querySelectorAll(rowSelector));
    }

    // Make rows focusable
    function initRows() {
      const rows = getRows();
      rows.forEach((row) => {
        if (!row.hasAttribute('tabindex')) {
          row.setAttribute('tabindex', '0');
        }
      });
    }

    function handleKeyDown(event) {
      const rows = getRows();
      if (!rows.length) return;

      const activeElement = document.activeElement;
      const currentIndex = rows.indexOf(activeElement);

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        const nextIndex = currentIndex < rows.length - 1 ? currentIndex + 1 : 0;
        rows[nextIndex].focus();
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : rows.length - 1;
        rows[prevIndex].focus();
      } else if (event.key === 'Enter' && currentIndex >= 0) {
        event.preventDefault();
        rows[currentIndex].click();
      }
    }

    initRows();

    // Observe DOM changes to add tabindex to new rows
    const observer = new MutationObserver(initRows);
    observer.observe(container, { childList: true, subtree: true });

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      observer.disconnect();
    };
  }, [containerRef, rowSelector]);
}
