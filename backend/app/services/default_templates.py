"""Default document templates for Phase 20 branded emails and PDFs."""
from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey

EMAIL = DocumentTemplateChannel.EMAIL
PDF = DocumentTemplateChannel.PDF

# ---------------------------------------------------------------------------
# User management email templates
# ---------------------------------------------------------------------------

_ACCOUNT_CREATED_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Welcome</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
</td></tr>
<tr><td style="padding:40px;">
<h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Welcome, {{ user_name }}!</h1>
<p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Your account has been created on <strong>{{ tenant_name }}</strong>.</p>
<table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
<tr><td style="padding:4px 0;font-size:14px;color:#64748B;">Email:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ email }}</td></tr>
<tr><td style="padding:4px 0;font-size:14px;color:#64748B;">Role:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ role }}</td></tr>
</table>
<a href="{{ login_url }}" style="display:inline-block;background:#2563EB;color:#FFFFFF;font-size:14px;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;">Sign In</a>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_ACCOUNT_CREATED_TEXT = '''Welcome, {{ user_name }}!

Your account has been created on {{ tenant_name }}.

Email: {{ email }}
Role: {{ role }}

Sign in at: {{ login_url }}

-- Warelyn Inventory'''

_PASSWORD_RESET_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Password Reset</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
</td></tr>
<tr><td style="padding:40px;">
<h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Password Reset</h1>
<p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your password on <strong>{{ tenant_name }}</strong> has been reset by an administrator.</p>
<p style="margin:0;font-size:14px;color:#64748B;line-height:1.6;">If you did not expect this change, please contact your administrator immediately.</p>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_PASSWORD_RESET_TEXT = '''Hi {{ user_name }},

Your password on {{ tenant_name }} has been reset by an administrator.

If you did not expect this change, please contact your administrator immediately.

-- Warelyn Inventory'''

_USER_DISABLED_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Account Disabled</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
</td></tr>
<tr><td style="padding:40px;">
<h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Account Disabled</h1>
<p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your account on <strong>{{ tenant_name }}</strong> has been disabled.</p>
{% if reason %}<p style="margin:0 0 24px;font-size:14px;color:#64748B;line-height:1.6;"><strong>Reason:</strong> {{ reason }}</p>{% endif %}
<p style="margin:0;font-size:14px;color:#64748B;line-height:1.6;">Please contact your administrator if you believe this is an error.</p>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_USER_DISABLED_TEXT = '''Hi {{ user_name }},

Your account on {{ tenant_name }} has been disabled.
{% if reason %}
Reason: {{ reason }}
{% endif %}
Please contact your administrator if you believe this is an error.

-- Warelyn Inventory'''

_USER_ENABLED_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Account Enabled</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
</td></tr>
<tr><td style="padding:40px;">
<h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Account Re-enabled</h1>
<p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your account on <strong>{{ tenant_name }}</strong> has been re-enabled. You can now sign in again.</p>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_USER_ENABLED_TEXT = '''Hi {{ user_name }},

Your account on {{ tenant_name }} has been re-enabled. You can now sign in again.

-- Warelyn Inventory'''

_ROLE_CHANGED_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Role Changed</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
</td></tr>
<tr><td style="padding:40px;">
<h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Role Updated</h1>
<p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your role on <strong>{{ tenant_name }}</strong> has been changed.</p>
<table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
<tr><td style="padding:4px 0;font-size:14px;color:#64748B;">Previous role:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ old_role }}</td></tr>
<tr><td style="padding:4px 0;font-size:14px;color:#64748B;">New role:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ new_role }}</td></tr>
</table>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_ROLE_CHANGED_TEXT = '''Hi {{ user_name }},

Your role on {{ tenant_name }} has been changed.

Previous role: {{ old_role }}
New role: {{ new_role }}

-- Warelyn Inventory'''

_OTP_EMAIL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Verification Code</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;letter-spacing:-0.5px;">Warelyn</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);letter-spacing:0.5px;text-transform:uppercase;">Inventory Platform</p></td>
<td align="right"><div style="background:rgba(255,255,255,0.15);border-radius:50%;width:48px;height:48px;display:inline-block;text-align:center;line-height:48px;"><span style="font-size:22px;">&#128274;</span></div></td>
</tr></table></td></tr>
<tr><td style="padding:40px;">
<p style="margin:0 0 8px;font-size:14px;color:#64748B;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Security Code</p>
<h1 style="margin:0 0 20px;font-size:28px;font-weight:700;color:#0F172A;line-height:1.2;">Verify your {{ purpose|lower }}</h1>
<p style="margin:0 0 32px;font-size:15px;color:#475569;line-height:1.6;">Use the code below to complete your request. This code expires in <strong>{{ ttl_minutes }} minutes</strong>.</p>
<div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:2px solid #BFDBFE;border-radius:12px;padding:28px;text-align:center;margin-bottom:32px;">
<p style="margin:0 0 8px;font-size:11px;color:#3B82F6;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Your Code</p>
<p style="margin:0;font-size:40px;font-weight:800;letter-spacing:12px;color:#1E3A8A;">{{ code }}</p>
</div>
<p style="margin:0;font-size:13px;color:#94A3B8;text-align:center;line-height:1.5;">If you didn't request this, you can safely ignore this email.<br>Your account remains secure.</p>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; Secure Verification System</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_OTP_EMAIL_MODERN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Verification Code</title></head>
<body style="margin:0;padding:0;background-color:#0F172A;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0F172A;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#1E293B;border-radius:20px;overflow:hidden;border:1px solid #334155;">
<tr><td style="padding:32px 40px 24px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><p style="margin:0;font-size:24px;font-weight:800;color:#F8FAFC;letter-spacing:-0.5px;">Warelyn</p>
<p style="margin:4px 0 0;font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;">Inventory Platform</p></td>
<td align="right"><div style="background:rgba(59,130,246,0.15);border-radius:50%;width:48px;height:48px;display:inline-block;text-align:center;line-height:48px;"><span style="font-size:22px;">&#128274;</span></div></td>
</tr></table></td></tr>
<tr><td style="padding:0 40px;">
<p style="margin:0 0 8px;font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">Security Verification</p>
<h1 style="margin:0 0 16px;font-size:26px;font-weight:700;color:#F1F5F9;line-height:1.3;">Verify your {{ purpose|lower }}</h1>
<p style="margin:0 0 28px;font-size:14px;color:#94A3B8;line-height:1.6;">Enter the code below to complete your request. It expires in <span style="color:#60A5FA;font-weight:600;">{{ ttl_minutes }} minutes</span>.</p>
</td></tr>
<tr><td style="padding:0 40px 32px;">
<div style="background:linear-gradient(135deg,#1E3A8A,#3B82F6);border-radius:12px;padding:28px;text-align:center;">
<p style="margin:0 0 8px;font-size:10px;color:#93C5FD;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Your Code</p>
<p style="margin:0;font-size:44px;font-weight:800;letter-spacing:14px;color:#FFFFFF;text-shadow:0 0 20px rgba(96,165,250,0.5);">{{ code }}</p>
</div>
<p style="margin:20px 0 0;font-size:12px;color:#475569;text-align:center;line-height:1.5;">If you didn't request this, you can safely ignore this email.</p>
</td></tr>
<tr><td style="border-top:1px solid #334155;padding:20px 40px;">
<p style="margin:0;font-size:11px;color:#475569;text-align:center;">Warelyn Inventory &middot; Secure Verification</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_OTP_EMAIL_MINIMAL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Verification Code</title></head>
<body style="margin:0;padding:0;background-color:#FFFFFF;font-family:Georgia,'Times New Roman',serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:48px 0;">
<tr><td align="center">
<table role="presentation" width="520" cellpadding="0" cellspacing="0">
<tr><td style="border-bottom:2px solid #111;padding-bottom:16px;">
<p style="margin:0;font-size:14px;font-weight:400;color:#111;letter-spacing:2px;text-transform:uppercase;">Warelyn</p>
</td></tr>
<tr><td style="padding:40px 0;">
<p style="margin:0 0 8px;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:1px;">Verification</p>
<h1 style="margin:0 0 20px;font-size:28px;font-weight:400;color:#111;line-height:1.3;">Verify your {{ purpose|lower }}</h1>
<p style="margin:0 0 32px;font-size:15px;color:#444;line-height:1.8;">Please use the following code to complete your request. This code will expire in {{ ttl_minutes }} minutes.</p>
<div style="border:1px solid #ddd;border-radius:4px;padding:24px;text-align:center;margin:0 0 32px;">
<p style="margin:0 0 6px;font-size:11px;color:#999;text-transform:uppercase;letter-spacing:1px;">Code</p>
<p style="margin:0;font-size:36px;font-weight:400;letter-spacing:10px;color:#111;">{{ code }}</p>
</div>
<p style="margin:0;font-size:13px;color:#999;line-height:1.6;">If you did not request this code, no action is needed.</p>
</td></tr>
<tr><td style="border-top:1px solid #eee;padding-top:16px;">
<p style="margin:0;font-size:12px;color:#999;">Warelyn Inventory</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_DOC_EMAIL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">{{ sender_name }}</p>
<p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);">{{ document_kind }} Notification</p></td>
<td align="right" style="color:#FFFFFF;font-size:32px;">&#128196;</td>
</tr></table></td></tr>
<tr><td style="padding:0 40px;">
<div style="background:#EFF6FF;border-left:4px solid #1E3A8A;border-radius:0 8px 8px 0;padding:16px 20px;margin:28px 0 0;">
<p style="margin:0;font-size:11px;color:#3B82F6;font-weight:700;letter-spacing:1px;text-transform:uppercase;">{{ document_kind }}</p>
<p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#0F172A;">{{ document_number }}</p>
</div></td></tr>
<tr><td style="padding:24px 40px 40px;">
<p style="margin:0 0 16px;font-size:15px;color:#475569;line-height:1.7;">{{ intro }}</p>
{% if notes %}<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:14px 18px;margin:16px 0;">
<p style="margin:0;font-size:12px;color:#92400E;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Notes</p>
<p style="margin:6px 0 0;font-size:14px;color:#78350F;">{{ notes }}</p></div>{% endif %}
<p style="margin:24px 0 0;font-size:14px;color:#64748B;">Please find your {{ document_kind|lower }} attached as a PDF.</p>
</td></tr>
<tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr><td>
<p style="margin:0;font-size:13px;color:#64748B;font-weight:500;">{{ sender_name }}</p>
<p style="margin:2px 0 0;font-size:12px;color:#94A3B8;">Sent via Warelyn Inventory</p>
</td></tr></table></td></tr>
</table></td></tr></table>
</body></html>'''

_DOC_EMAIL_TEXT = '''{{ title }}

{{ intro }}

Please find your {{ document_kind|lower }} {{ document_number }} attached.
{% if notes %}
Notes: {{ notes }}
{% endif %}
--
Sent by {{ sender_name }} via Warelyn Inventory'''

_OTP_EMAIL_TEXT = '''Your {{ purpose|lower }} code is: {{ code }}

This code will expire in {{ ttl_minutes }} minutes.

If you did not request this, please ignore this email.

-- Warelyn Inventory'''


_DOC_EMAIL_MODERN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
<body style="margin:0;padding:0;background-color:#0F172A;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0F172A;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#1E293B;border-radius:20px;overflow:hidden;border:1px solid #334155;">
<tr><td style="padding:32px 40px 24px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><p style="margin:0;font-size:24px;font-weight:800;color:#F8FAFC;letter-spacing:-0.5px;">{{ sender_name }}</p></td>
<td align="right"><span style="background:#3B82F6;color:white;font-size:11px;font-weight:700;padding:6px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:0.5px;">{{ document_kind }}</span></td>
</tr></table></td></tr>
<tr><td style="padding:0 40px;">
<div style="background:linear-gradient(135deg,#1E3A8A,#3B82F6);border-radius:12px;padding:24px;margin-bottom:24px;">
<p style="margin:0 0 4px;font-size:11px;color:#93C5FD;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;">Document Number</p>
<p style="margin:0;font-size:28px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px;">{{ document_number }}</p>
</div></td></tr>
<tr><td style="padding:0 40px 32px;">
<p style="margin:0 0 16px;font-size:15px;color:#CBD5E1;line-height:1.7;">{{ intro }}</p>
{% if notes %}<div style="background:#0F172A;border:1px solid #334155;border-radius:8px;padding:14px 18px;margin:16px 0;">
<p style="margin:0;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase;">Notes</p>
<p style="margin:6px 0 0;font-size:14px;color:#E2E8F0;">{{ notes }}</p></div>{% endif %}
<p style="margin:20px 0 0;font-size:13px;color:#64748B;">Your {{ document_kind|lower }} is attached as a PDF.</p>
</td></tr>
<tr><td style="border-top:1px solid #334155;padding:20px 40px;">
<p style="margin:0;font-size:12px;color:#475569;text-align:center;">Sent via Warelyn Inventory</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_DOC_EMAIL_MINIMAL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
<body style="margin:0;padding:0;background-color:#FFFFFF;font-family:Georgia,'Times New Roman',serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:48px 0;">
<tr><td align="center">
<table role="presentation" width="520" cellpadding="0" cellspacing="0">
<tr><td style="border-bottom:2px solid #111;padding-bottom:16px;margin-bottom:32px;">
<p style="margin:0;font-size:14px;font-weight:400;color:#111;letter-spacing:2px;text-transform:uppercase;">{{ sender_name }}</p>
</td></tr>
<tr><td style="padding:32px 0;">
<p style="margin:0 0 8px;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:1px;">{{ document_kind }}</p>
<p style="margin:0 0 24px;font-size:32px;font-weight:400;color:#111;">{{ document_number }}</p>
<p style="margin:0 0 24px;font-size:15px;color:#333;line-height:1.8;">{{ intro }}</p>
{% if notes %}<blockquote style="margin:24px 0;padding:12px 20px;border-left:3px solid #ddd;color:#555;font-style:italic;">{{ notes }}</blockquote>{% endif %}
<p style="margin:24px 0 0;font-size:13px;color:#999;">PDF attached.</p>
</td></tr>
<tr><td style="border-top:1px solid #eee;padding-top:16px;">
<p style="margin:0;font-size:12px;color:#999;">{{ sender_name }}</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_DOC_EMAIL_FORMAL_HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
<body style="margin:0;padding:0;background-color:#F9FAFB;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F9FAFB;padding:40px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border:1px solid #E5E7EB;">
<tr><td style="background:#111827;padding:24px 40px;">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><p style="margin:0;font-size:18px;font-weight:700;color:#FFFFFF;">{{ sender_name }}</p></td>
<td align="right"><p style="margin:0;font-size:12px;color:#9CA3AF;">{{ document_kind }} Notification</p></td>
</tr></table></td></tr>
<tr><td style="padding:40px;">
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;border:1px solid #E5E7EB;border-radius:4px;">
<tr><td style="background:#F9FAFB;padding:12px 16px;border-bottom:1px solid #E5E7EB;">
<p style="margin:0;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Reference</p></td>
<td style="background:#F9FAFB;padding:12px 16px;border-bottom:1px solid #E5E7EB;">
<p style="margin:0;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Type</p></td></tr>
<tr><td style="padding:12px 16px;"><p style="margin:0;font-size:16px;font-weight:700;color:#111827;">{{ document_number }}</p></td>
<td style="padding:12px 16px;"><p style="margin:0;font-size:14px;color:#374151;">{{ document_kind }}</p></td></tr>
</table>
<p style="margin:0 0 16px;font-size:14px;color:#374151;line-height:1.7;">{{ intro }}</p>
{% if notes %}<div style="background:#FEF3C7;border-left:4px solid #F59E0B;padding:12px 16px;margin:16px 0;">
<p style="margin:0;font-size:13px;color:#92400E;">{{ notes }}</p></div>{% endif %}
<p style="margin:24px 0 0;font-size:13px;color:#6B7280;">The {{ document_kind|lower }} document is attached to this email as a PDF.</p>
</td></tr>
<tr><td style="background:#F9FAFB;border-top:1px solid #E5E7EB;padding:16px 40px;">
<p style="margin:0;font-size:11px;color:#9CA3AF;text-align:center;">This is an automated message from {{ sender_name }} via Warelyn Inventory</p>
</td></tr>
</table></td></tr></table>
</body></html>'''

_DOC_EMAIL_MODERN_TEXT = _DOC_EMAIL_TEXT
_DOC_EMAIL_MINIMAL_TEXT = _DOC_EMAIL_TEXT
_DOC_EMAIL_FORMAL_TEXT = _DOC_EMAIL_TEXT


_CLASSIC_INVOICE_PDF = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Invoice {{ invoice.invoice_number }}</title>
<style>
body { font-family: Arial, sans-serif; font-size: 12px; color: #333; margin: 40px; }
h1 { color: #1E3A8A; margin-bottom: 5px; }
.header { display: flex; justify-content: space-between; margin-bottom: 30px; }
.company { font-size: 14px; }
.meta { margin-bottom: 20px; }
.meta td { padding: 3px 10px 3px 0; }
table.items { width: 100%; border-collapse: collapse; margin: 20px 0; }
table.items th { background: #1E3A8A; color: white; padding: 8px; text-align: left; }
table.items td { padding: 8px; border-bottom: 1px solid #E2E8F0; }
.totals { text-align: right; margin-top: 20px; }
.totals td { padding: 4px 0 4px 20px; }
.total-row { font-weight: bold; font-size: 14px; }
.footer { margin-top: 40px; color: #64748B; font-size: 10px; border-top: 1px solid #E2E8F0; padding-top: 10px; }
@media print {
  .no-print { display: none; }
  body { margin: 0; }
  @page { margin: 10mm; }
}
</style>
</head>
<body>
<div class="header">
<div class="company">
<h1>{{ tenant.company_name }}</h1>
{% if tenant.contact_email %}<p>{{ tenant.contact_email }}</p>{% endif %}
{% if tenant.phone %}<p>{{ tenant.phone }}</p>{% endif %}
{% if tenant.address %}<p>{{ tenant.address }}</p>{% endif %}
</div>
</div>
<h2>Invoice {{ invoice.invoice_number }}</h2>
<table class="meta">
<tr><td><strong>Date:</strong></td><td>{{ invoice.invoice_date }}</td></tr>
{% if invoice.due_date %}<tr><td><strong>Due:</strong></td><td>{{ invoice.due_date }}</td></tr>{% endif %}
{% if sales_order %}<tr><td><strong>SO:</strong></td><td>{{ sales_order.so_number }}</td></tr>{% endif %}
</table>
<p><strong>Bill To:</strong></p>
<p>{{ customer.name }}{% if customer.email %}<br>{{ customer.email }}{% endif %}{% if customer.phone %}<br>{{ customer.phone }}{% endif %}</p>
<table class="items">
<thead><tr><th>Product</th><th>Warehouse</th><th>Qty</th><th>Unit Price</th><th>Tax %</th><th>Total</th></tr></thead>
<tbody>
{% for item in items %}
<tr><td>{{ item.product_name }}</td><td>{{ item.warehouse_name }}</td><td>{{ item.quantity }}</td><td>{{ item.unit_price }}</td><td>{{ item.tax_rate }}</td><td>{{ item.total_price }}</td></tr>
{% endfor %}
</tbody>
</table>
<table class="totals">
<tr><td>Subtotal:</td><td>{{ invoice.subtotal }}</td></tr>
<tr><td>Tax:</td><td>{{ invoice.tax_amount }}</td></tr>
<tr><td>Discount:</td><td>{{ invoice.discount_amount }}</td></tr>
<tr class="total-row"><td>Total:</td><td>{{ invoice.total_amount }}</td></tr>
</table>
{% if invoice.notes %}<p><em>{{ invoice.notes }}</em></p>{% endif %}
<div class="footer">{{ tenant.footer }}</div>
</body>
</html>'''

_CLASSIC_BILL_PDF = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Bill {{ bill.bill_number }}</title>
<style>
body { font-family: Arial, sans-serif; font-size: 12px; color: #333; margin: 40px; }
h1 { color: #1E3A8A; margin-bottom: 5px; }
.header { display: flex; justify-content: space-between; margin-bottom: 30px; }
.company { font-size: 14px; }
.meta { margin-bottom: 20px; }
.meta td { padding: 3px 10px 3px 0; }
table.items { width: 100%; border-collapse: collapse; margin: 20px 0; }
table.items th { background: #1E3A8A; color: white; padding: 8px; text-align: left; }
table.items td { padding: 8px; border-bottom: 1px solid #E2E8F0; }
.totals { text-align: right; margin-top: 20px; }
.totals td { padding: 4px 0 4px 20px; }
.total-row { font-weight: bold; font-size: 14px; }
.footer { margin-top: 40px; color: #64748B; font-size: 10px; border-top: 1px solid #E2E8F0; padding-top: 10px; }
@media print {
  .no-print { display: none; }
  body { margin: 0; }
  @page { margin: 10mm; }
}
</style>
</head>
<body>
<div class="header">
<div class="company">
<h1>{{ tenant.company_name }}</h1>
{% if tenant.contact_email %}<p>{{ tenant.contact_email }}</p>{% endif %}
{% if tenant.phone %}<p>{{ tenant.phone }}</p>{% endif %}
{% if tenant.address %}<p>{{ tenant.address }}</p>{% endif %}
</div>
</div>
<h2>Bill {{ bill.bill_number }}</h2>
<table class="meta">
<tr><td><strong>Date:</strong></td><td>{{ bill.bill_date }}</td></tr>
{% if bill.due_date %}<tr><td><strong>Due:</strong></td><td>{{ bill.due_date }}</td></tr>{% endif %}
{% if purchase_order %}<tr><td><strong>PO:</strong></td><td>{{ purchase_order.po_number }}</td></tr>{% endif %}
</table>
<p><strong>Vendor:</strong></p>
<p>{{ vendor.name }}{% if vendor.email %}<br>{{ vendor.email }}{% endif %}{% if vendor.phone %}<br>{{ vendor.phone }}{% endif %}</p>
<table class="items">
<thead><tr><th>Product</th><th>Warehouse</th><th>Qty</th><th>Unit Price</th><th>Tax %</th><th>Total</th></tr></thead>
<tbody>
{% for item in items %}
<tr><td>{{ item.product_name }}</td><td>{{ item.warehouse_name }}</td><td>{{ item.quantity_ordered }}</td><td>{{ item.unit_price }}</td><td>{{ item.tax_rate }}</td><td>{{ item.total_price }}</td></tr>
{% endfor %}
</tbody>
</table>
<table class="totals">
<tr><td>Subtotal:</td><td>{{ bill.subtotal }}</td></tr>
<tr><td>Tax:</td><td>{{ bill.tax_amount }}</td></tr>
<tr class="total-row"><td>Total:</td><td>{{ bill.total_amount }}</td></tr>
</table>
{% if bill.notes %}<p><em>{{ bill.notes }}</em></p>{% endif %}
<div class="footer">{{ tenant.footer }}</div>
</body>
</html>'''


def _pdf_modern(doc_type="invoice"):
    """Modern two-tone sidebar template."""
    is_inv = doc_type == "invoice"
    num_var = "invoice.invoice_number" if is_inv else "bill.bill_number"
    date_var = "invoice.invoice_date" if is_inv else "bill.bill_date"
    due_var = "invoice.due_date" if is_inv else "bill.due_date"
    ref_label = "Sales Order" if is_inv else "Purchase Order"
    ref_var = "sales_order.so_number" if is_inv else "purchase_order.po_number"
    ref_cond = "sales_order" if is_inv else "purchase_order"
    party_label = "Bill To" if is_inv else "Vendor"
    party_var = "customer" if is_inv else "vendor"
    doc_title = "INVOICE" if is_inv else "BILL"
    qty_field = "item.quantity" if is_inv else "item.quantity_ordered"
    notes_var = "invoice.notes" if is_inv else "bill.notes"
    subtotal = "invoice.subtotal" if is_inv else "bill.subtotal"
    tax = "invoice.tax_amount" if is_inv else "bill.tax_amount"
    discount = "invoice.discount_amount" if is_inv else "bill.discount_amount"
    total = "invoice.total_amount" if is_inv else "bill.total_amount"

    return f'''<!DOCTYPE html><html>
<head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 0; }}
body {{ margin:0; font-family: 'Helvetica Neue', Arial, sans-serif; font-size:11px; color:#1E293B; }}
.page {{ display:flex; min-height:297mm; }}
.sidebar {{ width:64mm; background:#1E3A8A; padding:24mm 8mm 8mm; color:white; }}
.sidebar h1 {{ font-size:16px; font-weight:800; letter-spacing:-0.5px; margin:0 0 4px; color:white; }}
.sidebar .sub {{ font-size:9px; opacity:0.7; text-transform:uppercase; letter-spacing:1px; margin:0 0 24px; }}
.sidebar .label {{ font-size:8px; text-transform:uppercase; letter-spacing:1px; opacity:0.6; margin:16px 0 4px; }}
.sidebar .value {{ font-size:11px; color:white; font-weight:600; }}
.sidebar .doc-num {{ font-size:22px; font-weight:800; color:#93C5FD; margin:0; }}
.main {{ flex:1; padding:12mm 10mm; }}
table.items {{ width:100%; border-collapse:collapse; margin:8mm 0; }}
table.items thead tr {{ background:#EFF6FF; }}
table.items th {{ padding:8px 6px; text-align:left; font-size:9px; text-transform:uppercase; letter-spacing:0.8px; color:#1E3A8A; border-bottom:2px solid #BFDBFE; }}
table.items td {{ padding:8px 6px; border-bottom:1px solid #F1F5F9; }}
.totals-block {{ margin-left:auto; width:180px; }}
.totals-block table {{ width:100%; }}
.totals-block td {{ padding:5px 0; font-size:11px; }}
.totals-block td:last-child {{ text-align:right; font-weight:600; }}
.total-row td {{ font-size:15px; font-weight:800; color:#1E3A8A; border-top:2px solid #BFDBFE; padding-top:10px; }}
.footer {{ margin-top:8mm; font-size:9px; color:#94A3B8; }}
@media print {{
  .no-print {{ display: none; }}
  body {{ margin: 0; }}
  @page {{ margin: 10mm; }}
}}
</style></head>
<body>
<div class="page">
  <div class="sidebar">
    <h1>{{{{ tenant.company_name }}}}</h1>
    <p class="sub">Inventory Platform</p>
    <p class="label">{doc_title}</p>
    <p class="doc-num">{{{{ {num_var} }}}}</p>
    <p class="label">Date</p><p class="value">{{{{ {date_var} }}}}</p>
    {{% if {due_var} %}}<p class="label">Due Date</p><p class="value">{{{{ {due_var} }}}}</p>{{% endif %}}
    {{% if {ref_cond} %}}<p class="label">{ref_label}</p><p class="value">{{{{ {ref_var} }}}}</p>{{% endif %}}
    <br><br>
    <p class="label">{party_label}</p>
    <p class="value">{{{{ {party_var}.name }}}}</p>
    {{% if {party_var}.email %}}<p class="value" style="font-size:9px;opacity:0.8;">{{{{ {party_var}.email }}}}</p>{{% endif %}}
    {{% if {party_var}.phone %}}<p class="value" style="font-size:9px;opacity:0.8;">{{{{ {party_var}.phone }}}}</p>{{% endif %}}
  </div>
  <div class="main">
    <div style="margin-bottom:6mm;"><p style="margin:0;font-size:28px;font-weight:800;color:#1E3A8A;letter-spacing:-1px;">{doc_title}</p></div>
    <table class="items">
      <thead><tr><th>Item</th><th>Warehouse</th><th>Qty</th><th>Rate</th><th>Tax</th><th>Amount</th></tr></thead>
      <tbody>
        {{% for item in items %}}
        <tr><td>{{{{ item.product_name }}}}</td><td style="color:#64748B;">{{{{ item.warehouse_name }}}}</td><td>{{{{ {qty_field} }}}}</td><td>{{{{ item.unit_price }}}}</td><td style="color:#64748B;">{{{{ item.tax_rate }}}}%</td><td style="font-weight:600;">{{{{ item.total_price }}}}</td></tr>
        {{% endfor %}}
      </tbody>
    </table>
    <div class="totals-block"><table>
      <tr><td>Subtotal</td><td>{{{{ {subtotal} }}}}</td></tr>
      <tr><td>Tax</td><td>{{{{ {tax} }}}}</td></tr>
      {"<tr><td>Discount</td><td>{{{{ " + discount + " }}}}</td></tr>" if is_inv else ""}
      <tr class="total-row"><td>Total</td><td>{{{{ {total} }}}}</td></tr>
    </table></div>
    {{% if {notes_var} %}}<div style="margin-top:8mm;padding:10px;background:#FFFBEB;border-radius:6px;"><p style="margin:0;font-size:10px;color:#92400E;font-weight:600;">Notes</p><p style="margin:4px 0 0;font-size:11px;color:#78350F;">{{{{ {notes_var} }}}}</p></div>{{% endif %}}
    <div class="footer">{{{{ tenant.footer }}}}</div>
  </div>
</div>
</body></html>'''


def _pdf_minimal(doc_type="invoice"):
    """Minimal clean white template with Georgia font."""
    is_inv = doc_type == "invoice"
    num_var = "invoice.invoice_number" if is_inv else "bill.bill_number"
    date_var = "invoice.invoice_date" if is_inv else "bill.bill_date"
    due_var = "invoice.due_date" if is_inv else "bill.due_date"
    party_var = "customer" if is_inv else "vendor"
    party_label = "Bill To" if is_inv else "Vendor"
    doc_title = "Invoice" if is_inv else "Bill"
    qty_field = "item.quantity" if is_inv else "item.quantity_ordered"
    notes_var = "invoice.notes" if is_inv else "bill.notes"
    subtotal = "invoice.subtotal" if is_inv else "bill.subtotal"
    tax = "invoice.tax_amount" if is_inv else "bill.tax_amount"
    discount = "invoice.discount_amount" if is_inv else "bill.discount_amount"
    total = "invoice.total_amount" if is_inv else "bill.total_amount"

    return f'''<!DOCTYPE html><html>
<head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 20mm 16mm; }}
body {{ font-family: Georgia, 'Times New Roman', serif; font-size:11px; color:#1E293B; }}
.top {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16mm; border-bottom:0.5px solid #CBD5E1; padding-bottom:8mm; }}
.company-name {{ font-size:24px; font-weight:bold; letter-spacing:-1px; color:#0F172A; margin:0; }}
.doc-title {{ text-align:right; }}
.doc-title h2 {{ font-size:28px; font-weight:300; letter-spacing:4px; color:#CBD5E1; margin:0; text-transform:uppercase; }}
.doc-title .num {{ font-size:14px; font-weight:bold; color:#1E3A8A; }}
.parties {{ display:flex; gap:20mm; margin-bottom:12mm; }}
.party {{ flex:1; }}
.party .label {{ font-size:8px; text-transform:uppercase; letter-spacing:2px; color:#94A3B8; margin:0 0 6px; }}
.party .name {{ font-size:13px; font-weight:bold; color:#0F172A; }}
table {{ width:100%; border-collapse:collapse; margin:8mm 0; }}
thead tr th {{ font-size:8px; text-transform:uppercase; letter-spacing:1.5px; color:#94A3B8; padding:8px 0; text-align:left; border-bottom:0.5px solid #E2E8F0; }}
tbody tr td {{ padding:10px 0; border-bottom:0.5px solid #F1F5F9; font-size:11px; }}
.totals {{ width:200px; margin-left:auto; margin-top:4mm; }}
.totals table td {{ padding:4px 0; font-size:11px; }}
.totals table td:last-child {{ text-align:right; }}
.grand-total td {{ font-size:16px; font-weight:bold; color:#0F172A; border-top:1px solid #1E293B; padding-top:8px; }}
@media print {{
  .no-print {{ display: none; }}
  body {{ margin: 0; }}
  @page {{ margin: 10mm; }}
}}
</style></head>
<body>
<div class="top">
  <div><p class="company-name">{{{{ tenant.company_name }}}}</p><p style="margin:4px 0 0;font-size:11px;color:#94A3B8;">{{{{ tenant.contact_email }}}}</p></div>
  <div class="doc-title"><h2>{doc_title}</h2><p class="num">{{{{ {num_var} }}}}</p><p style="font-size:11px;color:#64748B;margin:4px 0 0;">{{{{ {date_var} }}}}</p></div>
</div>
<div class="parties">
  <div class="party"><p class="label">{party_label}</p><p class="name">{{{{ {party_var}.name }}}}</p><p style="color:#64748B;font-size:10px;margin:2px 0;">{{{{ {party_var}.email or '' }}}}</p></div>
  {{% if {due_var} %}}<div class="party"><p class="label">Due Date</p><p class="name">{{{{ {due_var} }}}}</p></div>{{% endif %}}
</div>
<table>
  <thead><tr><th>Description</th><th>Qty</th><th>Rate</th><th>Tax</th><th style="text-align:right;">Amount</th></tr></thead>
  <tbody>
    {{% for item in items %}}
    <tr><td>{{{{ item.product_name }}}}</td><td>{{{{ {qty_field} }}}}</td><td>{{{{ item.unit_price }}}}</td><td style="color:#94A3B8;">{{{{ item.tax_rate }}}}%</td><td style="text-align:right;">{{{{ item.total_price }}}}</td></tr>
    {{% endfor %}}
  </tbody>
</table>
<div class="totals"><table>
  <tr><td style="color:#64748B;">Subtotal</td><td>{{{{ {subtotal} }}}}</td></tr>
  <tr><td style="color:#64748B;">Tax</td><td>{{{{ {tax} }}}}</td></tr>
  {"<tr><td style='color:#64748B;'>Discount</td><td>({{{{ " + discount + " }}}})</td></tr>" if is_inv else ""}
  <tr class="grand-total"><td>Total</td><td>{{{{ {total} }}}}</td></tr>
</table></div>
{{% if {notes_var} %}}<p style="margin-top:8mm;font-size:10px;color:#94A3B8;"><em>{{{{ {notes_var} }}}}</em></p>{{% endif %}}
<p style="margin-top:12mm;font-size:9px;color:#CBD5E1;border-top:0.5px solid #E2E8F0;padding-top:4mm;">{{{{ tenant.footer }}}}</p>
</body></html>'''


def _pdf_bold(doc_type="invoice"):
    """Bold dark header template."""
    html = _pdf_modern(doc_type)
    html = html.replace("background:#1E3A8A", "background:#0F172A")
    html = html.replace("color:#1E3A8A", "color:#F59E0B")
    html = html.replace("color:#93C5FD", "color:#FCD34D")
    html = html.replace("border-bottom:2px solid #BFDBFE", "border-bottom:2px solid #F59E0B")
    html = html.replace("border-top:2px solid #BFDBFE", "border-top:2px solid #F59E0B")
    html = html.replace("background:#EFF6FF", "background:#FFFBEB")
    return html


def _pdf_warm(doc_type="invoice"):
    """Warm earthy tones template."""
    html = _pdf_modern(doc_type)
    html = html.replace("background:#1E3A8A", "background:#7C2D12")
    html = html.replace("color:#1E3A8A", "color:#D97706")
    html = html.replace("color:#93C5FD", "color:#FCD34D")
    html = html.replace("border-bottom:2px solid #BFDBFE", "border-bottom:2px solid #D97706")
    html = html.replace("border-top:2px solid #BFDBFE", "border-top:2px solid #D97706")
    html = html.replace("background:#EFF6FF", "background:#FFFBEB")
    return html


DEFAULT_TEMPLATES: dict[tuple[DocumentTemplateChannel, DocumentTemplateKey], dict[str, str | bool | None]] = {
    (EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION): {
        "name": "Email verification",
        "subject_template": "Verify your Warelyn email",
        "body_template": _OTP_EMAIL_HTML,
        "body_template_text": _OTP_EMAIL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION_MODERN): {
        "name": "Verification email — Modern",
        "subject_template": "Your verification code — {{ purpose }}",
        "body_template": _OTP_EMAIL_MODERN_HTML,
        "body_template_text": _OTP_EMAIL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION_MINIMAL): {
        "name": "Verification email — Minimal",
        "subject_template": "Your verification code — {{ purpose }}",
        "body_template": _OTP_EMAIL_MINIMAL_HTML,
        "body_template_text": _OTP_EMAIL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.INVOICE_SEND): {
        "name": "Invoice email — Classic",
        "subject_template": "{{ title }} from {{ sender_name }}",
        "body_template": _DOC_EMAIL_HTML,
        "body_template_text": _DOC_EMAIL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.INVOICE_SEND_MODERN): {
        "name": "Invoice email — Modern",
        "subject_template": "{{ title }} from {{ sender_name }}",
        "body_template": _DOC_EMAIL_MODERN_HTML,
        "body_template_text": _DOC_EMAIL_MODERN_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.INVOICE_SEND_MINIMAL): {
        "name": "Invoice email — Minimal",
        "subject_template": "{{ title }} — {{ sender_name }}",
        "body_template": _DOC_EMAIL_MINIMAL_HTML,
        "body_template_text": _DOC_EMAIL_MINIMAL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.INVOICE_SEND_FORMAL): {
        "name": "Invoice email — Formal",
        "subject_template": "{{ document_kind }} {{ document_number }} from {{ sender_name }}",
        "body_template": _DOC_EMAIL_FORMAL_HTML,
        "body_template_text": _DOC_EMAIL_FORMAL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.BILL_SEND): {
        "name": "Bill email — Classic",
        "subject_template": "{{ title }} from {{ sender_name }}",
        "body_template": _DOC_EMAIL_HTML,
        "body_template_text": _DOC_EMAIL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.BILL_SEND_MODERN): {
        "name": "Bill email — Modern",
        "subject_template": "{{ title }} from {{ sender_name }}",
        "body_template": _DOC_EMAIL_MODERN_HTML,
        "body_template_text": _DOC_EMAIL_MODERN_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.BILL_SEND_MINIMAL): {
        "name": "Bill email — Minimal",
        "subject_template": "{{ title }} — {{ sender_name }}",
        "body_template": _DOC_EMAIL_MINIMAL_HTML,
        "body_template_text": _DOC_EMAIL_MINIMAL_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.BILL_SEND_FORMAL): {
        "name": "Bill email — Formal",
        "subject_template": "{{ document_kind }} {{ document_number }} from {{ sender_name }}",
        "body_template": _DOC_EMAIL_FORMAL_HTML,
        "body_template_text": _DOC_EMAIL_FORMAL_TEXT,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE): {
        "name": "Invoice PDF — Classic",
        "subject_template": None,
        "body_template": _CLASSIC_INVOICE_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_MODERN): {
        "name": "Invoice PDF — Modern",
        "subject_template": None,
        "body_template": _pdf_modern("invoice"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_MINIMAL): {
        "name": "Invoice PDF — Minimal",
        "subject_template": None,
        "body_template": _pdf_minimal("invoice"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_BOLD): {
        "name": "Invoice PDF — Bold",
        "subject_template": None,
        "body_template": _pdf_bold("invoice"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_WARM): {
        "name": "Invoice PDF — Warm",
        "subject_template": None,
        "body_template": _pdf_warm("invoice"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL): {
        "name": "Bill PDF — Classic",
        "subject_template": None,
        "body_template": _CLASSIC_BILL_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_MODERN): {
        "name": "Bill PDF — Modern",
        "subject_template": None,
        "body_template": _pdf_modern("bill"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_MINIMAL): {
        "name": "Bill PDF — Minimal",
        "subject_template": None,
        "body_template": _pdf_minimal("bill"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_BOLD): {
        "name": "Bill PDF — Bold",
        "subject_template": None,
        "body_template": _pdf_bold("bill"),
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_WARM): {
        "name": "Bill PDF — Warm",
        "subject_template": None,
        "body_template": _pdf_warm("bill"),
        "body_template_text": None,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.ACCOUNT_CREATED): {
        "name": "Account created notification",
        "subject_template": "Welcome to {{ tenant_name }}",
        "body_template": _ACCOUNT_CREATED_HTML,
        "body_template_text": _ACCOUNT_CREATED_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.PASSWORD_RESET): {
        "name": "Password reset notification",
        "subject_template": "Your password has been reset — {{ tenant_name }}",
        "body_template": _PASSWORD_RESET_HTML,
        "body_template_text": _PASSWORD_RESET_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.USER_DISABLED): {
        "name": "Account disabled notification",
        "subject_template": "Your account has been disabled — {{ tenant_name }}",
        "body_template": _USER_DISABLED_HTML,
        "body_template_text": _USER_DISABLED_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.USER_ENABLED): {
        "name": "Account enabled notification",
        "subject_template": "Your account has been re-enabled — {{ tenant_name }}",
        "body_template": _USER_ENABLED_HTML,
        "body_template_text": _USER_ENABLED_TEXT,
        "is_active": True,
    },
    (EMAIL, DocumentTemplateKey.ROLE_CHANGED): {
        "name": "Role changed notification",
        "subject_template": "Your role has been updated — {{ tenant_name }}",
        "body_template": _ROLE_CHANGED_HTML,
        "body_template_text": _ROLE_CHANGED_TEXT,
        "is_active": True,
    },
}
