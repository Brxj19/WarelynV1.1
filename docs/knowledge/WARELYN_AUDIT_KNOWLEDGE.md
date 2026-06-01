# Warelyn Audit Log Knowledge

## What is the audit log?

The audit log is a complete history of every significant action taken in Warelyn. It records: who did it, what they did, when they did it, what entity was affected, and any relevant metadata. It is immutable — audit entries cannot be deleted or edited.

## Who can view the audit log?

TENANT_ADMIN can view the full audit log for their tenant. Go to Settings, Audit Logs. SUPER_ADMIN can view audit logs across all tenants at the platform level.

## What actions are logged?

Every major action is logged: user logins, user creation, role changes, product create/edit/delete, warehouse changes, sales order creation, confirmation, cancellation, purchase order creation, submission, receipt commit, fulfillment commit, return submission, return processing, invoice creation, bill recording, stock adjustments, transfers, cycle count creation, reconciliation, template changes, and AI assistant queries.

## How to find who changed a stock level?

Go to Settings, Audit Logs. Filter by entity type STOCK_ADJUSTMENT or by the product name in the metadata search. Each entry shows the actor user ID, their role, the action, and the change details.

## How to investigate a suspicious activity?

Filter the audit log by user_id, date range, and action type. Look for unexpected STOCK_ADJUSTMENT entries, unusual login times, or bulk changes. If you see actions from a user who should not have done them, check their role in user management.

## What is the difference between audit log and stock ledger?

The stock ledger records every stock quantity change with the delta and reference. The audit log records every user action with who did it and when. They complement each other: use the stock ledger to trace why stock changed, and the audit log to trace who triggered the action.

## Are AI assistant queries logged?

Yes. Every FAQ question and AI Copilot query is logged with: the user ID, their role, whether the answer was confident or abstained, citation count, and token usage. View these in the audit log filtered by action ASSISTANT_FAQ_ASK or ASSISTANT_COPILOT_ASK.

## How long are audit logs kept?

Audit logs are kept indefinitely. There is no automatic deletion. They grow with every action and should be monitored for disk usage on large deployments.
