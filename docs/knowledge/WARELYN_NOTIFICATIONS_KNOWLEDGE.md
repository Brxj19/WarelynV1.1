# Warelyn Notifications Knowledge

## How do notifications work?

Warelyn sends in-app notifications when important events happen. Notifications appear in the bell icon in the top bar. The bell shows a red count badge when unread notifications exist.

## What triggers a notification?

Business events that create notifications:
- Sales order confirmed → INVENTORY_MANAGER notified to pick
- Sales order cancelled → TENANT_ADMIN and SALES_STAFF notified
- Fulfillment committed → SALES_STAFF notified to create invoice
- Purchase receipt committed → INVENTORY_MANAGER notified to putaway
- Putaway completed → PURCHASE_STAFF notified to record bill
- Return submitted → INVENTORY_MANAGER notified for QC
- Return processed → SALES_STAFF and TENANT_ADMIN notified of outcome
- High-value PO submitted → TENANT_ADMIN notified for approval
- Low stock detected → PURCHASE_STAFF notified to reorder
- User role changed → affected user notified
- Password reset requested → user notified by email

## Who receives which notifications?

Notifications are role-targeted. INVENTORY_MANAGER receives operational notifications. SALES_STAFF receives sales-specific notifications. PURCHASE_STAFF receives purchasing notifications. TENANT_ADMIN receives cross-domain notifications and approvals. No user receives notifications outside their role domain.

## How to mark notifications as read?

Click the bell icon. Click Mark all as read, or click the checkmark on individual notifications. Unread notifications are highlighted. Read notifications remain until cleared.

## How to clear notifications?

Click the bell icon. Click Clear all to remove all notifications. Or click the X on individual notifications to clear them one at a time. Cleared notifications do not appear again.

## Why am I not receiving notifications?

Check that your user account is active and the correct role is assigned. Notifications are only sent to users with the relevant role in the tenant. If you should be receiving a notification but are not, check with TENANT_ADMIN to verify your role and that your account is not disabled.

## Are notifications sent by email?

Currently, notifications are in-app only. Business event notifications (order confirmed, return submitted, etc.) are delivered via the in-app bell. Password reset and email verification codes are sent by email through the configured SMTP server.
