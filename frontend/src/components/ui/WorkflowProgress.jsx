import { AlertTriangle, Check, XCircle } from 'lucide-react';
import { titleCaseStatus } from '../../utils/formatters.js';

export function WorkflowProgress({ current, steps }) {
  const currentIndex = Math.max(0, steps.findIndex((step) => step.matches?.includes(current) || step.key === current));
  const isTerminalDanger = ['CANCELLED', 'REJECTED', 'SCRAPPED', 'DAMAGED'].includes(current);
  return (
    <ol className="progress-steps">
      {steps.map((step, index) => {
        const isCurrent = step.matches?.includes(current) || step.key === current;
        const state = index < currentIndex ? 'is-complete' : isCurrent ? (isTerminalDanger ? 'is-blocked' : 'is-active') : 'is-pending';
        const icon = state === 'is-complete' ? <Check size={13} /> : state === 'is-blocked' ? <XCircle size={13} /> : index + 1;
        return (
          <li className={`progress-step ${state}`} key={step.key}>
            <span className="progress-node">{icon}</span>
            <span className="progress-label">{step.label}</span>
          </li>
        );
      })}
      {isTerminalDanger ? (
        <li className="progress-step is-terminal">
          <span className="progress-node">
            <AlertTriangle size={13} />
          </span>
          <span className="progress-label">{titleCaseStatus(current)}</span>
        </li>
      ) : null}
    </ol>
  );
}
