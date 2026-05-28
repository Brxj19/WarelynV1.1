---
name: warelyn-workflow-audit
description: Audit Warelyn business workflows, role handoffs, task assignment, notifications, and next-step ownership. Use when checking if sales, purchase, inventory, billing, and admin workflows move to the correct concerned role.
---

# Warelyn Workflow Audit

Inspect backend and frontend workflow code.

Check:

1. Sales workflow:
   - customer
   - sales order
   - picking
   - packing
   - fulfillment
   - invoice
   - payment
   - returns

2. Purchase workflow:
   - supplier
   - purchase order
   - approval
   - receipt
   - putaway
   - bill
   - payment

3. Inventory workflow:
   - product
   - warehouse
   - stock transfer
   - stock adjustment
   - low stock
   - reorder

4. Admin workflow:
   - user creation
   - role change
   - disable/enable
   - template management
   - notifications
   - audit logs

For every workflow step, report:

- Current step
- Current role
- Action taken
- Next expected status
- Next expected role
- Whether a task is created
- Whether a notification is created
- Whether the next role sees it in dashboard
- Backend gaps
- Frontend gaps
- Tests needed

Create or update:

docs/WARELYN_WORKFLOW_AUDIT.md