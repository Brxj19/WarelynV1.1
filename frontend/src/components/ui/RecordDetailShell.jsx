import { Card, CardBody } from './Card.jsx';
import { PageHeader } from './PageHeader.jsx';

export function RecordDetailShell({
  actions,
  backLabel,
  backTo,
  children,
  description,
  kicker,
  meta = [],
  progress = null,
  sidePanel = null,
  status = null,
  summary = [],
  title,
}) {
  return (
    <div className="space-y-6">
      <PageHeader
        actions={actions}
        backLabel={backLabel}
        backTo={backTo}
        description={description}
        kicker={kicker}
        status={status}
        title={title}
      >
        {meta.length ? (
          <div className="record-meta-grid">
            {meta.map((item) => (
              <div className="record-meta-item" key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        ) : null}
      </PageHeader>

      {progress}

      {summary.length ? (
        <div className="record-summary-grid">
          {summary.map((item) => (
            <Card className="record-summary-card" key={item.label}>
              <CardBody>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                {item.helper ? <small>{item.helper}</small> : null}
              </CardBody>
            </Card>
          ))}
        </div>
      ) : null}

      <div className={`record-detail-layout ${sidePanel ? 'has-side-panel' : ''}`}>
        <div className="record-detail-main">{children}</div>
        {sidePanel ? <aside className="record-detail-side">{sidePanel}</aside> : null}
      </div>
    </div>
  );
}
