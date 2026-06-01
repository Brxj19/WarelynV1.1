# Warelyn Settings Knowledge

## Company settings

Company settings are managed by TENANT_ADMIN under Settings, Company. You can change the company name, timezone, and base currency. The currency is used on all invoices, bills, and monetary reports. Changing the currency does not retroactively change historical documents — each document snapshots the currency at creation time.

## User management

TENANT_ADMIN manages users under Settings, Users. You can invite new users, set their role, enable or disable accounts, and reset passwords. A disabled user cannot log in. Roles: TENANT_ADMIN, INVENTORY_MANAGER, SALES_STAFF, PURCHASE_STAFF, VIEWER.

## How to invite a new user

Go to Settings, Users. Click Create User. Enter the name, email address, and select a role. The user receives an email with their login credentials. They must verify their email before the account is fully active.

## How to change a user's role

Go to Settings, Users. Click on the user. Click Edit. Change the role. Save. The change takes effect on the user's next login or on their next API call.

## Document templates

TENANT_ADMIN and INVENTORY_MANAGER can manage document templates under Settings. Templates are available for: Invoice PDF, Invoice Email, Bill PDF, Bill Email, Email Verification. Templates use Jinja2-style variables like {{company_name}}, {{customer_name}}, {{invoice_number}}, {{total_amount}}, {{currency_symbol}}. Customise templates to match your brand.

## Email and PDF template variables

Common variables available in all document templates:
- {{company_name}} — Your company name from settings
- {{document_number}} — Invoice or bill number
- {{customer_name}} or {{vendor_name}} — Recipient name
- {{total_amount}} — Document total
- {{currency_code}} — 3-letter currency code (USD, EUR, INR)
- {{currency_symbol}} — Currency symbol ($, €, ₹)
- {{due_date}} — Payment due date
- {{line_items}} — Table of line items
- {{notes}} — Optional document notes

## Currency settings

The base currency is set per tenant. Go to Settings, Company and select a currency from the dropdown. Only currencies in the supported list can be selected. The currency affects: invoice formatting, bill formatting, product valuation reports, and the AI copilot's monetary insights.

## User preferences

Each user can set their own preferences under Settings, My Profile: timezone display, date format, and notification preferences. These are personal and do not affect other users.

## SMTP email configuration

Email sending requires SMTP configuration. Go to Settings, Company to configure SMTP settings. Required fields: SMTP host, port, username, password, from email address, from name. Enable TLS or SSL depending on your email provider. Test the configuration by sending a test email. If email delivery mode is set to LOG, emails are not sent but are written to the backend logs only (useful for development).

## How to configure notifications

Users can manage which notifications they receive. Go to Settings, My Profile, Notifications. Toggle notification categories on or off. Notifications are delivered in-app via the bell icon in the top bar.
