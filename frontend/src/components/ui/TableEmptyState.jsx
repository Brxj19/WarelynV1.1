import { EmptyState } from './EmptyState.jsx';

export function TableEmptyState({
  colSpan = 1,
  illustration,
  title,
  message,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
}) {
  return (
    <tr>
      <td colSpan={colSpan}>
        <EmptyState
          illustration={illustration}
          title={title}
          message={message}
          actionLabel={actionLabel}
          onAction={onAction}
          secondaryActionLabel={secondaryActionLabel}
          onSecondaryAction={onSecondaryAction}
          size="sm"
        />
      </td>
    </tr>
  );
}
