import { BackButton } from './BackButton.jsx';

export function PageHeader({ actions, backLabel, backTo, children, description, kicker, status, title }) {
  return (
    <section className="page-header">
      <div>
        <BackButton label={backLabel} to={backTo} />
        {kicker ? <p className="page-kicker">{kicker}</p> : null}
        <div className="page-title-row">
          <h1>{title}</h1>
          {status}
        </div>
        {description ? <p>{description}</p> : null}
        {children}
      </div>
      {actions ? <div className="page-header-actions">{actions}</div> : null}
    </section>
  );
}
