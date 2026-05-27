export function StockImpactPreview({ items = [], title = 'Stock impact preview' }) {
  if (!items.length) return null;

  return (
    <div className="stock-impact-preview">
      <div className="stock-impact-preview-header">
        <div>
          <h3>{title}</h3>
          <p>Advisory only. Final stock authority remains in backend workflows.</p>
        </div>
      </div>
      <div className="stock-impact-preview-grid">
        {items.map((item, index) => (
          <div className="stock-impact-preview-item" key={item.id ?? index}>
            <p className="stock-impact-title">{item.product ?? item.title}</p>
            <p className="stock-impact-meta">{item.meta}</p>
            <p className="stock-impact-effect">{item.effect}</p>
            {item.warning ? <p className="stock-impact-warning">{item.warning}</p> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
