# """Default document templates for Phase 20 branded emails and PDFs."""
# from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey

# EMAIL = DocumentTemplateChannel.EMAIL
# PDF = DocumentTemplateChannel.PDF

# # ---------------------------------------------------------------------------
# # User management email templates
# # ---------------------------------------------------------------------------

# _ACCOUNT_CREATED_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Welcome</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
# </td></tr>
# <tr><td style="padding:40px;">
# <h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Welcome, {{ user_name }}!</h1>
# <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Your account has been created on <strong>{{ tenant_name }}</strong>.</p>
# <table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
# <tr><td style="padding:4px 0;font-size:14px;color:#64748B;">Email:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ email }}</td></tr>
# <tr><td style="padding:4px 0;font-size:14px;color:#64748B;">Role:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ role }}</td></tr>
# </table>
# <a href="{{ login_url }}" style="display:inline-block;background:#2563EB;color:#FFFFFF;font-size:14px;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;">Sign In</a>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _ACCOUNT_CREATED_TEXT = '''Welcome, {{ user_name }}!

# Your account has been created on {{ tenant_name }}.

# Email: {{ email }}
# Role: {{ role }}

# Sign in at: {{ login_url }}

# -- Warelyn Inventory'''

# _PASSWORD_RESET_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Password Reset</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
# </td></tr>
# <tr><td style="padding:40px;">
# <h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Password Reset</h1>
# <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your password on <strong>{{ tenant_name }}</strong> has been reset by an administrator.</p>
# <p style="margin:0;font-size:14px;color:#64748B;line-height:1.6;">If you did not expect this change, please contact your administrator immediately.</p>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _PASSWORD_RESET_TEXT = '''Hi {{ user_name }},

# Your password on {{ tenant_name }} has been reset by an administrator.

# If you did not expect this change, please contact your administrator immediately.

# -- Warelyn Inventory'''

# _USER_DISABLED_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Account Disabled</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
# </td></tr>
# <tr><td style="padding:40px;">
# <h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Account Disabled</h1>
# <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your account on <strong>{{ tenant_name }}</strong> has been disabled.</p>
# {% if reason %}<p style="margin:0 0 24px;font-size:14px;color:#64748B;line-height:1.6;"><strong>Reason:</strong> {{ reason }}</p>{% endif %}
# <p style="margin:0;font-size:14px;color:#64748B;line-height:1.6;">Please contact your administrator if you believe this is an error.</p>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _USER_DISABLED_TEXT = '''Hi {{ user_name }},

# Your account on {{ tenant_name }} has been disabled.
# {% if reason %}
# Reason: {{ reason }}
# {% endif %}
# Please contact your administrator if you believe this is an error.

# -- Warelyn Inventory'''

# _USER_ENABLED_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Account Enabled</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
# </td></tr>
# <tr><td style="padding:40px;">
# <h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Account Re-enabled</h1>
# <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your account on <strong>{{ tenant_name }}</strong> has been re-enabled. You can now sign in again.</p>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _USER_ENABLED_TEXT = '''Hi {{ user_name }},

# Your account on {{ tenant_name }} has been re-enabled. You can now sign in again.

# -- Warelyn Inventory'''

# _ROLE_CHANGED_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Role Changed</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:0.5px;">Inventory Platform</p>
# </td></tr>
# <tr><td style="padding:40px;">
# <h1 style="margin:0 0 16px;font-size:24px;color:#0F172A;">Role Updated</h1>
# <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">Hi {{ user_name }}, your role on <strong>{{ tenant_name }}</strong> has been changed.</p>
# <table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
# <tr><td style="padding:4px 0;font-size:14px;color:#64748B;">Previous role:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ old_role }}</td></tr>
# <tr><td style="padding:4px 0;font-size:14px;color:#64748B;">New role:</td><td style="padding:4px 0 4px 12px;font-size:14px;color:#0F172A;font-weight:600;">{{ new_role }}</td></tr>
# </table>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; {{ tenant_name }}</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _ROLE_CHANGED_TEXT = '''Hi {{ user_name }},

# Your role on {{ tenant_name }} has been changed.

# Previous role: {{ old_role }}
# New role: {{ new_role }}

# -- Warelyn Inventory'''

# _OTP_EMAIL_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Verification Code</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <table width="100%" cellpadding="0" cellspacing="0"><tr>
# <td><p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;letter-spacing:-0.5px;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);letter-spacing:0.5px;text-transform:uppercase;">Inventory Platform</p></td>
# <td align="right"><div style="background:rgba(255,255,255,0.15);border-radius:50%;width:48px;height:48px;display:inline-block;text-align:center;line-height:48px;"><span style="font-size:22px;">&#128274;</span></div></td>
# </tr></table></td></tr>
# <tr><td style="padding:40px;">
# <p style="margin:0 0 8px;font-size:14px;color:#64748B;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Security Code</p>
# <h1 style="margin:0 0 20px;font-size:28px;font-weight:700;color:#0F172A;line-height:1.2;">Verify your {{ purpose|lower }}</h1>
# <p style="margin:0 0 32px;font-size:15px;color:#475569;line-height:1.6;">Use the code below to complete your request. This code expires in <strong>{{ ttl_minutes }} minutes</strong>.</p>
# <div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:2px solid #BFDBFE;border-radius:12px;padding:28px;text-align:center;margin-bottom:32px;">
# <p style="margin:0 0 8px;font-size:11px;color:#3B82F6;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Your Code</p>
# <p style="margin:0;font-size:40px;font-weight:800;letter-spacing:12px;color:#1E3A8A;">{{ code }}</p>
# </div>
# <p style="margin:0;font-size:13px;color:#94A3B8;text-align:center;line-height:1.5;">If you didn't request this, you can safely ignore this email.<br>Your account remains secure.</p>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#94A3B8;text-align:center;">Warelyn Inventory &middot; Secure Verification System</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _OTP_EMAIL_MODERN_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Verification Code</title></head>
# <body style="margin:0;padding:0;background-color:#0F172A;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0F172A;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#1E293B;border-radius:20px;overflow:hidden;border:1px solid #334155;">
# <tr><td style="padding:32px 40px 24px;">
# <table width="100%" cellpadding="0" cellspacing="0"><tr>
# <td><p style="margin:0;font-size:24px;font-weight:800;color:#F8FAFC;letter-spacing:-0.5px;">Warelyn</p>
# <p style="margin:4px 0 0;font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;">Inventory Platform</p></td>
# <td align="right"><div style="background:rgba(59,130,246,0.15);border-radius:50%;width:48px;height:48px;display:inline-block;text-align:center;line-height:48px;"><span style="font-size:22px;">&#128274;</span></div></td>
# </tr></table></td></tr>
# <tr><td style="padding:0 40px;">
# <p style="margin:0 0 8px;font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">Security Verification</p>
# <h1 style="margin:0 0 16px;font-size:26px;font-weight:700;color:#F1F5F9;line-height:1.3;">Verify your {{ purpose|lower }}</h1>
# <p style="margin:0 0 28px;font-size:14px;color:#94A3B8;line-height:1.6;">Enter the code below to complete your request. It expires in <span style="color:#60A5FA;font-weight:600;">{{ ttl_minutes }} minutes</span>.</p>
# </td></tr>
# <tr><td style="padding:0 40px 32px;">
# <div style="background:linear-gradient(135deg,#1E3A8A,#3B82F6);border-radius:12px;padding:28px;text-align:center;">
# <p style="margin:0 0 8px;font-size:10px;color:#93C5FD;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Your Code</p>
# <p style="margin:0;font-size:44px;font-weight:800;letter-spacing:14px;color:#FFFFFF;text-shadow:0 0 20px rgba(96,165,250,0.5);">{{ code }}</p>
# </div>
# <p style="margin:20px 0 0;font-size:12px;color:#475569;text-align:center;line-height:1.5;">If you didn't request this, you can safely ignore this email.</p>
# </td></tr>
# <tr><td style="border-top:1px solid #334155;padding:20px 40px;">
# <p style="margin:0;font-size:11px;color:#475569;text-align:center;">Warelyn Inventory &middot; Secure Verification</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _OTP_EMAIL_MINIMAL_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Verification Code</title></head>
# <body style="margin:0;padding:0;background-color:#FFFFFF;font-family:Georgia,'Times New Roman',serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:48px 0;">
# <tr><td align="center">
# <table role="presentation" width="520" cellpadding="0" cellspacing="0">
# <tr><td style="border-bottom:2px solid #111;padding-bottom:16px;">
# <p style="margin:0;font-size:14px;font-weight:400;color:#111;letter-spacing:2px;text-transform:uppercase;">Warelyn</p>
# </td></tr>
# <tr><td style="padding:40px 0;">
# <p style="margin:0 0 8px;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:1px;">Verification</p>
# <h1 style="margin:0 0 20px;font-size:28px;font-weight:400;color:#111;line-height:1.3;">Verify your {{ purpose|lower }}</h1>
# <p style="margin:0 0 32px;font-size:15px;color:#444;line-height:1.8;">Please use the following code to complete your request. This code will expire in {{ ttl_minutes }} minutes.</p>
# <div style="border:1px solid #ddd;border-radius:4px;padding:24px;text-align:center;margin:0 0 32px;">
# <p style="margin:0 0 6px;font-size:11px;color:#999;text-transform:uppercase;letter-spacing:1px;">Code</p>
# <p style="margin:0;font-size:36px;font-weight:400;letter-spacing:10px;color:#111;">{{ code }}</p>
# </div>
# <p style="margin:0;font-size:13px;color:#999;line-height:1.6;">If you did not request this code, no action is needed.</p>
# </td></tr>
# <tr><td style="border-top:1px solid #eee;padding-top:16px;">
# <p style="margin:0;font-size:12px;color:#999;">Warelyn Inventory</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _DOC_EMAIL_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
# <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F1F5F9;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
# <tr><td style="background:linear-gradient(135deg,#1E3A8A 0%,#2563EB 100%);padding:28px 40px;">
# <table width="100%" cellpadding="0" cellspacing="0"><tr>
# <td><p style="margin:0;font-size:22px;font-weight:700;color:#FFFFFF;">{{ sender_name }}</p>
# <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.7);">{{ document_kind }} Notification</p></td>
# <td align="right" style="color:#FFFFFF;font-size:32px;">&#128196;</td>
# </tr></table></td></tr>
# <tr><td style="padding:0 40px;">
# <div style="background:#EFF6FF;border-left:4px solid #1E3A8A;border-radius:0 8px 8px 0;padding:16px 20px;margin:28px 0 0;">
# <p style="margin:0;font-size:11px;color:#3B82F6;font-weight:700;letter-spacing:1px;text-transform:uppercase;">{{ document_kind }}</p>
# <p style="margin:4px 0 0;font-size:20px;font-weight:700;color:#0F172A;">{{ document_number }}</p>
# </div></td></tr>
# <tr><td style="padding:24px 40px 40px;">
# <p style="margin:0 0 16px;font-size:15px;color:#475569;line-height:1.7;">{{ intro }}</p>
# {% if notes %}<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:14px 18px;margin:16px 0;">
# <p style="margin:0;font-size:12px;color:#92400E;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Notes</p>
# <p style="margin:6px 0 0;font-size:14px;color:#78350F;">{{ notes }}</p></div>{% endif %}
# <p style="margin:24px 0 0;font-size:14px;color:#64748B;">Please find your {{ document_kind|lower }} attached as a PDF.</p>
# </td></tr>
# <tr><td style="background:#F8FAFC;border-top:1px solid #E2E8F0;padding:20px 40px;">
# <table width="100%" cellpadding="0" cellspacing="0"><tr><td>
# <p style="margin:0;font-size:13px;color:#64748B;font-weight:500;">{{ sender_name }}</p>
# <p style="margin:2px 0 0;font-size:12px;color:#94A3B8;">Sent via Warelyn Inventory</p>
# </td></tr></table></td></tr>
# </table></td></tr></table>
# </body></html>'''

# _DOC_EMAIL_TEXT = '''{{ title }}

# {{ intro }}

# Please find your {{ document_kind|lower }} {{ document_number }} attached.
# {% if notes %}
# Notes: {{ notes }}
# {% endif %}
# --
# Sent by {{ sender_name }} via Warelyn Inventory'''

# _OTP_EMAIL_TEXT = '''Your {{ purpose|lower }} code is: {{ code }}

# This code will expire in {{ ttl_minutes }} minutes.

# If you did not request this, please ignore this email.

# -- Warelyn Inventory'''


# _DOC_EMAIL_MODERN_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
# <body style="margin:0;padding:0;background-color:#0F172A;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0F172A;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="background:#1E293B;border-radius:20px;overflow:hidden;border:1px solid #334155;">
# <tr><td style="padding:32px 40px 24px;">
# <table width="100%" cellpadding="0" cellspacing="0"><tr>
# <td><p style="margin:0;font-size:24px;font-weight:800;color:#F8FAFC;letter-spacing:-0.5px;">{{ sender_name }}</p></td>
# <td align="right"><span style="background:#3B82F6;color:white;font-size:11px;font-weight:700;padding:6px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:0.5px;">{{ document_kind }}</span></td>
# </tr></table></td></tr>
# <tr><td style="padding:0 40px;">
# <div style="background:linear-gradient(135deg,#1E3A8A,#3B82F6);border-radius:12px;padding:24px;margin-bottom:24px;">
# <p style="margin:0 0 4px;font-size:11px;color:#93C5FD;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;">Document Number</p>
# <p style="margin:0;font-size:28px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px;">{{ document_number }}</p>
# </div></td></tr>
# <tr><td style="padding:0 40px 32px;">
# <p style="margin:0 0 16px;font-size:15px;color:#CBD5E1;line-height:1.7;">{{ intro }}</p>
# {% if notes %}<div style="background:#0F172A;border:1px solid #334155;border-radius:8px;padding:14px 18px;margin:16px 0;">
# <p style="margin:0;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase;">Notes</p>
# <p style="margin:6px 0 0;font-size:14px;color:#E2E8F0;">{{ notes }}</p></div>{% endif %}
# <p style="margin:20px 0 0;font-size:13px;color:#64748B;">Your {{ document_kind|lower }} is attached as a PDF.</p>
# </td></tr>
# <tr><td style="border-top:1px solid #334155;padding:20px 40px;">
# <p style="margin:0;font-size:12px;color:#475569;text-align:center;">Sent via Warelyn Inventory</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _DOC_EMAIL_MINIMAL_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
# <body style="margin:0;padding:0;background-color:#FFFFFF;font-family:Georgia,'Times New Roman',serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="padding:48px 0;">
# <tr><td align="center">
# <table role="presentation" width="520" cellpadding="0" cellspacing="0">
# <tr><td style="border-bottom:2px solid #111;padding-bottom:16px;margin-bottom:32px;">
# <p style="margin:0;font-size:14px;font-weight:400;color:#111;letter-spacing:2px;text-transform:uppercase;">{{ sender_name }}</p>
# </td></tr>
# <tr><td style="padding:32px 0;">
# <p style="margin:0 0 8px;font-size:12px;color:#666;text-transform:uppercase;letter-spacing:1px;">{{ document_kind }}</p>
# <p style="margin:0 0 24px;font-size:32px;font-weight:400;color:#111;">{{ document_number }}</p>
# <p style="margin:0 0 24px;font-size:15px;color:#333;line-height:1.8;">{{ intro }}</p>
# {% if notes %}<blockquote style="margin:24px 0;padding:12px 20px;border-left:3px solid #ddd;color:#555;font-style:italic;">{{ notes }}</blockquote>{% endif %}
# <p style="margin:24px 0 0;font-size:13px;color:#999;">PDF attached.</p>
# </td></tr>
# <tr><td style="border-top:1px solid #eee;padding-top:16px;">
# <p style="margin:0;font-size:12px;color:#999;">{{ sender_name }}</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _DOC_EMAIL_FORMAL_HTML = '''<!DOCTYPE html>
# <html lang="en">
# <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ title }}</title></head>
# <body style="margin:0;padding:0;background-color:#F9FAFB;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
# <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F9FAFB;padding:40px 0;">
# <tr><td align="center">
# <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border:1px solid #E5E7EB;">
# <tr><td style="background:#111827;padding:24px 40px;">
# <table width="100%" cellpadding="0" cellspacing="0"><tr>
# <td><p style="margin:0;font-size:18px;font-weight:700;color:#FFFFFF;">{{ sender_name }}</p></td>
# <td align="right"><p style="margin:0;font-size:12px;color:#9CA3AF;">{{ document_kind }} Notification</p></td>
# </tr></table></td></tr>
# <tr><td style="padding:40px;">
# <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;border:1px solid #E5E7EB;border-radius:4px;">
# <tr><td style="background:#F9FAFB;padding:12px 16px;border-bottom:1px solid #E5E7EB;">
# <p style="margin:0;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Reference</p></td>
# <td style="background:#F9FAFB;padding:12px 16px;border-bottom:1px solid #E5E7EB;">
# <p style="margin:0;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Type</p></td></tr>
# <tr><td style="padding:12px 16px;"><p style="margin:0;font-size:16px;font-weight:700;color:#111827;">{{ document_number }}</p></td>
# <td style="padding:12px 16px;"><p style="margin:0;font-size:14px;color:#374151;">{{ document_kind }}</p></td></tr>
# </table>
# <p style="margin:0 0 16px;font-size:14px;color:#374151;line-height:1.7;">{{ intro }}</p>
# {% if notes %}<div style="background:#FEF3C7;border-left:4px solid #F59E0B;padding:12px 16px;margin:16px 0;">
# <p style="margin:0;font-size:13px;color:#92400E;">{{ notes }}</p></div>{% endif %}
# <p style="margin:24px 0 0;font-size:13px;color:#6B7280;">The {{ document_kind|lower }} document is attached to this email as a PDF.</p>
# </td></tr>
# <tr><td style="background:#F9FAFB;border-top:1px solid #E5E7EB;padding:16px 40px;">
# <p style="margin:0;font-size:11px;color:#9CA3AF;text-align:center;">This is an automated message from {{ sender_name }} via Warelyn Inventory</p>
# </td></tr>
# </table></td></tr></table>
# </body></html>'''

# _DOC_EMAIL_MODERN_TEXT = _DOC_EMAIL_TEXT
# _DOC_EMAIL_MINIMAL_TEXT = _DOC_EMAIL_TEXT
# _DOC_EMAIL_FORMAL_TEXT = _DOC_EMAIL_TEXT



# _CLASSIC_INVOICE_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Invoice {{ invoice.invoice_number }}</title>

#   <style>
#     @page {
#       size: A4;
#       margin: 0;
#     }

#     * {
#       box-sizing: border-box;
#     }

#     html,
#     body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       background: #ffffff;
#       font-family: Arial, sans-serif;
#       color: #334155;
#       overflow: hidden;
#     }

#     body {
#       font-size: 11px;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       padding: 14mm 14mm 12mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .header {
#       display: flex;
#       justify-content: space-between;
#       align-items: flex-start;
#       gap: 20px;
#       margin-bottom: 18px;
#       padding-bottom: 14px;
#       border-bottom: 2px solid #1e3a8a;
#     }

#     .company {
#       max-width: 58%;
#       font-size: 11px;
#       line-height: 1.45;
#       color: #475569;
#     }

#     .company h1 {
#       color: #1e3a8a;
#       font-size: 24px;
#       line-height: 1.1;
#       margin: 0 0 6px;
#       font-weight: 800;
#       letter-spacing: -0.5px;
#     }

#     .company p {
#       margin: 2px 0;
#     }

#     .invoice-heading {
#       text-align: right;
#     }

#     .invoice-heading h2 {
#       margin: 0;
#       color: #1e3a8a;
#       font-size: 25px;
#       line-height: 1;
#       font-weight: 800;
#       letter-spacing: 0.5px;
#       text-transform: uppercase;
#     }

#     .invoice-number {
#       margin-top: 6px;
#       color: #64748b;
#       font-size: 11px;
#       font-weight: 600;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 8px;
#       padding: 4px 9px;
#       border-radius: 999px;
#       background: #eff6ff;
#       color: #1e3a8a;
#       border: 1px solid #bfdbfe;
#       font-size: 8px;
#       font-weight: 700;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#     }

#     .top-section {
#       display: flex;
#       justify-content: space-between;
#       align-items: flex-start;
#       gap: 18px;
#       margin-bottom: 18px;
#     }

#     .bill-to {
#       width: 56%;
#       padding: 12px;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       background: #f8fafc;
#     }

#     .bill-to-title {
#       margin: 0 0 7px;
#       color: #1e3a8a;
#       font-size: 9px;
#       font-weight: 800;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .customer-name {
#       margin: 0;
#       font-size: 13px;
#       font-weight: 700;
#       color: #0f172a;
#       line-height: 1.35;
#     }

#     .customer-detail {
#       margin: 3px 0 0;
#       font-size: 10px;
#       line-height: 1.45;
#       color: #64748b;
#     }

#     .meta-wrap {
#       width: 40%;
#       padding: 12px;
#       border: 1px solid #dbeafe;
#       border-radius: 8px;
#       background: #eff6ff;
#     }

#     table.meta {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .meta td {
#       padding: 4px 0;
#       font-size: 10px;
#       line-height: 1.35;
#       vertical-align: top;
#     }

#     .meta td:first-child {
#       color: #475569;
#       font-weight: 700;
#       width: 42%;
#     }

#     .meta td:last-child {
#       color: #0f172a;
#       font-weight: 700;
#       text-align: right;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 18px 0 14px;
#       table-layout: fixed;
#     }

#     table.items th {
#       background: #1e3a8a;
#       color: #ffffff;
#       padding: 8px 7px;
#       text-align: left;
#       font-size: 8px;
#       font-weight: 700;
#       text-transform: uppercase;
#       letter-spacing: 0.6px;
#     }

#     table.items td {
#       padding: 8px 7px;
#       border-bottom: 1px solid #e2e8f0;
#       font-size: 10px;
#       line-height: 1.35;
#       vertical-align: top;
#       color: #334155;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) {
#       background: #f8fafc;
#     }

#     .product-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .muted {
#       color: #64748b;
#     }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num {
#       text-align: right;
#     }

#     .empty-items {
#       text-align: center;
#       padding: 18px 8px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-wrapper {
#       display: flex;
#       justify-content: flex-end;
#       margin-top: 10px;
#     }

#     table.totals {
#       width: 72mm;
#       border-collapse: collapse;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#     }

#     .totals td {
#       padding: 7px 10px;
#       font-size: 10px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals td:first-child {
#       color: #475569;
#       font-weight: 600;
#     }

#     .totals td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #1e3a8a;
#       color: #ffffff !important;
#       font-weight: 800;
#       font-size: 13px;
#       border-bottom: none;
#       padding-top: 9px;
#       padding-bottom: 9px;
#     }

#     .notes {
#       margin-top: 18px;
#       padding: 10px 12px;
#       border-left: 4px solid #1e3a8a;
#       background: #f8fafc;
#       border-radius: 6px;
#       color: #475569;
#       font-size: 10px;
#       line-height: 1.5;
#     }

#     .notes strong {
#       display: block;
#       margin-bottom: 4px;
#       color: #1e3a8a;
#       font-size: 9px;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#     }

#     .footer {
#       margin-top: 22px;
#       color: #64748b;
#       font-size: 9px;
#       line-height: 1.45;
#       border-top: 1px solid #e2e8f0;
#       padding-top: 10px;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="header">
#       <div class="company">
#         <h1>{{ tenant.company_name }}</h1>

#         {% if tenant.contact_email %}
#           <p>{{ tenant.contact_email }}</p>
#         {% endif %}

#         {% if tenant.phone %}
#           <p>{{ tenant.phone }}</p>
#         {% endif %}

#         {% if tenant.address %}
#           <p>{{ tenant.address }}</p>
#         {% endif %}
#       </div>

#       <div class="invoice-heading">
#         <h2>Invoice</h2>
#         <div class="invoice-number">{{ invoice.invoice_number }}</div>

#         {% if invoice.status %}
#           <div class="status-badge">{{ invoice.status }}</div>
#         {% endif %}
#       </div>
#     </div>

#     <div class="top-section">
#       <div class="bill-to">
#         <p class="bill-to-title">Bill To</p>
#         <p class="customer-name">{{ customer.name }}</p>

#         {% if customer.email %}
#           <p class="customer-detail">{{ customer.email }}</p>
#         {% endif %}

#         {% if customer.phone %}
#           <p class="customer-detail">{{ customer.phone }}</p>
#         {% endif %}

#         {% if customer.billing_address %}
#           <p class="customer-detail">{{ customer.billing_address }}</p>
#         {% endif %}
#       </div>

#       <div class="meta-wrap">
#         <table class="meta">
#           <tr>
#             <td>Date:</td>
#             <td>{{ invoice.invoice_date }}</td>
#           </tr>

#           {% if invoice.due_date %}
#           <tr>
#             <td>Due:</td>
#             <td>{{ invoice.due_date }}</td>
#           </tr>
#           {% endif %}

#           {% if sales_order %}
#           <tr>
#             <td>SO:</td>
#             <td>{{ sales_order.so_number }}</td>
#           </tr>
#           {% endif %}
#         </table>
#       </div>
#     </div>

#     <table class="items">
#       <thead>
#         <tr>
#           <th style="width: 31%;">Product</th>
#           <th style="width: 20%;">Warehouse</th>
#           <th class="num" style="width: 9%;">Qty</th>
#           <th class="num" style="width: 14%;">Unit Price</th>
#           <th class="num" style="width: 10%;">Tax %</th>
#           <th class="num" style="width: 16%;">Total</th>
#         </tr>
#       </thead>

#       <tbody>
#         {% if items %}
#           {% for item in items %}
#           <tr>
#             <td>
#               <span class="product-name">{{ item.product_name }}</span>
#               {% if item.sku %}
#                 <br><span class="muted" style="font-size: 8.5px;">SKU: {{ item.sku }}</span>
#               {% endif %}
#             </td>

#             <td class="muted">{{ item.warehouse_name }}</td>

#             <td class="num">{{ item.quantity }}</td>

#             <td class="num">
#               {{ currency_symbol | default("₹") }}{{ item.unit_price }}
#             </td>

#             <td class="num muted">{{ item.tax_rate }}</td>

#             <td class="num" style="font-weight: 700;">
#               {{ currency_symbol | default("₹") }}{{ item.total_price }}
#             </td>
#           </tr>
#           {% endfor %}
#         {% else %}
#           <tr>
#             <td colspan="6" class="empty-items">No invoice items available.</td>
#           </tr>
#         {% endif %}
#       </tbody>
#     </table>

#     <div class="totals-wrapper">
#       <table class="totals">
#         <tr>
#           <td>Subtotal:</td>
#           <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
#         </tr>

#         <tr>
#           <td>Tax:</td>
#           <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
#         </tr>

#         {% if invoice.discount_amount %}
#         <tr>
#           <td>Discount:</td>
#           <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
#         </tr>
#         {% endif %}

#         <tr class="total-row">
#           <td>Total:</td>
#           <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
#         </tr>
#       </table>
#     </div>

#     {% if invoice.notes %}
#       <div class="notes">
#         <strong>Notes</strong>
#         <em>{{ invoice.notes }}</em>
#       </div>
#     {% endif %}

#     <div class="footer">
#       {% if tenant.footer %}
#         {{ tenant.footer }}
#       {% else %}
#         This invoice was generated by {{ tenant.company_name }} using Warelyn.
#       {% endif %}
#     </div>
#   </div>
# </body>
# </html>'''

# _CLASSIC_BILL_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Bill {{ bill.bill_number }}</title>

#   <style>
#     @page { size: A4; margin: 0; }

#     * { box-sizing: border-box; }

#     html, body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       background: #ffffff;
#       font-family: Arial, sans-serif;
#       color: #334155;
#       overflow: hidden;
#     }

#     body { font-size: 11px; }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       padding: 14mm 14mm 12mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .header {
#       display: flex;
#       justify-content: space-between;
#       align-items: flex-start;
#       gap: 20px;
#       margin-bottom: 18px;
#       padding-bottom: 14px;
#       border-bottom: 2px solid #1e3a8a;
#     }

#     .company {
#       max-width: 58%;
#       font-size: 11px;
#       line-height: 1.45;
#       color: #475569;
#     }

#     .company h1 {
#       color: #1e3a8a;
#       font-size: 24px;
#       line-height: 1.1;
#       margin: 0 0 6px;
#       font-weight: 800;
#       letter-spacing: -0.5px;
#     }

#     .company p { margin: 2px 0; }

#     .bill-heading { text-align: right; }

#     .bill-heading h2 {
#       margin: 0;
#       color: #1e3a8a;
#       font-size: 25px;
#       line-height: 1;
#       font-weight: 800;
#       letter-spacing: 0.5px;
#       text-transform: uppercase;
#     }

#     .bill-number {
#       margin-top: 6px;
#       color: #64748b;
#       font-size: 11px;
#       font-weight: 600;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 8px;
#       padding: 4px 9px;
#       border-radius: 999px;
#       background: #eff6ff;
#       color: #1e3a8a;
#       border: 1px solid #bfdbfe;
#       font-size: 8px;
#       font-weight: 700;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#     }

#     .top-section {
#       display: flex;
#       justify-content: space-between;
#       align-items: flex-start;
#       gap: 18px;
#       margin-bottom: 18px;
#     }

#     .vendor-box {
#       width: 56%;
#       padding: 12px;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       background: #f8fafc;
#     }

#     .vendor-title {
#       margin: 0 0 7px;
#       color: #1e3a8a;
#       font-size: 9px;
#       font-weight: 800;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .vendor-name {
#       margin: 0;
#       font-size: 13px;
#       font-weight: 700;
#       color: #0f172a;
#       line-height: 1.35;
#     }

#     .vendor-detail {
#       margin: 3px 0 0;
#       font-size: 10px;
#       line-height: 1.45;
#       color: #64748b;
#     }

#     .meta-wrap {
#       width: 40%;
#       padding: 12px;
#       border: 1px solid #dbeafe;
#       border-radius: 8px;
#       background: #eff6ff;
#     }

#     table.meta {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .meta td {
#       padding: 4px 0;
#       font-size: 10px;
#       line-height: 1.35;
#       vertical-align: top;
#     }

#     .meta td:first-child {
#       color: #475569;
#       font-weight: 700;
#       width: 42%;
#     }

#     .meta td:last-child {
#       color: #0f172a;
#       font-weight: 700;
#       text-align: right;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 18px 0 14px;
#       table-layout: fixed;
#     }

#     table.items th {
#       background: #1e3a8a;
#       color: #ffffff;
#       padding: 8px 7px;
#       text-align: left;
#       font-size: 8px;
#       font-weight: 700;
#       text-transform: uppercase;
#       letter-spacing: 0.6px;
#     }

#     table.items td {
#       padding: 8px 7px;
#       border-bottom: 1px solid #e2e8f0;
#       font-size: 10px;
#       line-height: 1.35;
#       vertical-align: top;
#       color: #334155;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) { background: #f8fafc; }

#     .product-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .muted { color: #64748b; }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num { text-align: right; }

#     .empty-items {
#       text-align: center;
#       padding: 18px 8px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-wrapper {
#       display: flex;
#       justify-content: flex-end;
#       margin-top: 10px;
#     }

#     table.totals {
#       width: 72mm;
#       border-collapse: collapse;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#     }

#     .totals td {
#       padding: 7px 10px;
#       font-size: 10px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals td:first-child {
#       color: #475569;
#       font-weight: 600;
#     }

#     .totals td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #1e3a8a;
#       color: #ffffff !important;
#       font-weight: 800;
#       font-size: 13px;
#       border-bottom: none;
#       padding-top: 9px;
#       padding-bottom: 9px;
#     }

#     .notes {
#       margin-top: 18px;
#       padding: 10px 12px;
#       border-left: 4px solid #1e3a8a;
#       background: #f8fafc;
#       border-radius: 6px;
#       color: #475569;
#       font-size: 10px;
#       line-height: 1.5;
#     }

#     .notes strong {
#       display: block;
#       margin-bottom: 4px;
#       color: #1e3a8a;
#       font-size: 9px;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#     }

#     .footer {
#       margin-top: 22px;
#       color: #64748b;
#       font-size: 9px;
#       line-height: 1.45;
#       border-top: 1px solid #e2e8f0;
#       padding-top: 10px;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="header">
#       <div class="company">
#         <h1>{{ tenant.company_name }}</h1>
#         {% if tenant.contact_email %}<p>{{ tenant.contact_email }}</p>{% endif %}
#         {% if tenant.phone %}<p>{{ tenant.phone }}</p>{% endif %}
#         {% if tenant.address %}<p>{{ tenant.address }}</p>{% endif %}
#       </div>

#       <div class="bill-heading">
#         <h2>Bill</h2>
#         <div class="bill-number">{{ bill.bill_number }}</div>
#         {% if bill.status %}
#           <div class="status-badge">{{ bill.status }}</div>
#         {% endif %}
#       </div>
#     </div>

#     <div class="top-section">
#       <div class="vendor-box">
#         <p class="vendor-title">Vendor</p>
#         <p class="vendor-name">{{ vendor.name }}</p>
#         {% if vendor.email %}<p class="vendor-detail">{{ vendor.email }}</p>{% endif %}
#         {% if vendor.phone %}<p class="vendor-detail">{{ vendor.phone }}</p>{% endif %}
#         {% if vendor.address %}<p class="vendor-detail">{{ vendor.address }}</p>{% endif %}
#       </div>

#       <div class="meta-wrap">
#         <table class="meta">
#           <tr><td>Date:</td><td>{{ bill.bill_date }}</td></tr>
#           {% if bill.due_date %}<tr><td>Due:</td><td>{{ bill.due_date }}</td></tr>{% endif %}
#           {% if purchase_order %}<tr><td>PO:</td><td>{{ purchase_order.po_number }}</td></tr>{% endif %}
#         </table>
#       </div>
#     </div>

#     <table class="items">
#       <thead>
#         <tr>
#           <th style="width:31%;">Product</th>
#           <th style="width:20%;">Warehouse</th>
#           <th class="num" style="width:9%;">Qty</th>
#           <th class="num" style="width:14%;">Unit Price</th>
#           <th class="num" style="width:10%;">Tax %</th>
#           <th class="num" style="width:16%;">Total</th>
#         </tr>
#       </thead>

#       <tbody>
#         {% if items %}
#           {% for item in items %}
#           <tr>
#             <td>
#               <span class="product-name">{{ item.product_name }}</span>
#               {% if item.sku %}
#                 <br><span class="muted" style="font-size:8.5px;">SKU: {{ item.sku }}</span>
#               {% endif %}
#             </td>
#             <td class="muted">{{ item.warehouse_name }}</td>
#             <td class="num">{{ item.quantity_ordered }}</td>
#             <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
#             <td class="num muted">{{ item.tax_rate }}%</td>
#             <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
#           </tr>
#           {% endfor %}
#         {% else %}
#           <tr>
#             <td colspan="6" class="empty-items">No bill items available.</td>
#           </tr>
#         {% endif %}
#       </tbody>
#     </table>

#     <div class="totals-wrapper">
#       <table class="totals">
#         <tr><td>Subtotal:</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
#         <tr><td>Tax:</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
#         <tr class="total-row"><td>Total:</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
#       </table>
#     </div>

#     {% if bill.notes %}
#       <div class="notes">
#         <strong>Notes</strong>
#         <em>{{ bill.notes }}</em>
#       </div>
#     {% endif %}

#     <div class="footer">
#       {% if tenant.footer %}
#         {{ tenant.footer }}
#       {% else %}
#         This bill was generated by {{ tenant.company_name }} using Warelyn.
#       {% endif %}
#     </div>
#   </div>
# </body>
# </html>'''

# _MODERN_INVOICE_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Invoice {{ invoice.invoice_number }}</title>

#   <style>
#     @page {
#       size: A4;
#       margin: 0;
#     }

#     * {
#       box-sizing: border-box;
#     }

#     html,
#     body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       overflow: hidden;
#       background: #ffffff;
#       font-family: "Helvetica Neue", Arial, sans-serif;
#       font-size: 10px;
#       color: #1e293b;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       display: flex;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .sidebar {
#       width: 62mm;
#       height: 297mm;
#       background: #1e3a8a;
#       color: #ffffff;
#       padding: 18mm 8mm 8mm;
#       overflow: hidden;
#     }

#     .sidebar h1 {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       letter-spacing: -0.4px;
#       margin: 0 0 4px;
#       color: #ffffff;
#       word-break: break-word;
#     }

#     .sidebar .sub {
#       font-size: 8px;
#       opacity: 0.72;
#       text-transform: uppercase;
#       letter-spacing: 1.1px;
#       margin: 0 0 18mm;
#     }

#     .sidebar .section {
#       margin-bottom: 8mm;
#     }

#     .sidebar .label {
#       font-size: 7px;
#       text-transform: uppercase;
#       letter-spacing: 1px;
#       opacity: 0.62;
#       margin: 0 0 3px;
#     }

#     .sidebar .value {
#       font-size: 9.5px;
#       line-height: 1.35;
#       color: #ffffff;
#       font-weight: 600;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar .muted {
#       font-size: 8px;
#       line-height: 1.35;
#       color: rgba(255, 255, 255, 0.78);
#       margin: 2px 0 0;
#       word-break: break-word;
#     }

#     .sidebar .doc-num {
#       font-size: 21px;
#       line-height: 1.12;
#       font-weight: 800;
#       color: #93c5fd;
#       margin: 0;
#       word-break: break-word;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border-radius: 999px;
#       background: rgba(147, 197, 253, 0.15);
#       border: 1px solid rgba(147, 197, 253, 0.35);
#       color: #bfdbfe;
#       font-size: 7px;
#       font-weight: 700;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .amount-due {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       color: #bfdbfe;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar-footer {
#       margin-top: 14mm;
#       font-size: 8px;
#       line-height: 1.4;
#       color: rgba(255, 255, 255, 0.58);
#       word-break: break-word;
#     }

#     .main {
#       width: 148mm;
#       height: 297mm;
#       padding: 11mm 10mm 8mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .main-title {
#       margin-bottom: 7mm;
#       padding-bottom: 4mm;
#       border-bottom: 1px solid #e2e8f0;
#     }

#     .main-title p {
#       margin: 0;
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 800;
#       color: #1e3a8a;
#       letter-spacing: -1px;
#     }

#     .main-title span {
#       display: block;
#       margin-top: 4px;
#       font-size: 9px;
#       color: #64748b;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr {
#       background: #eff6ff;
#     }

#     table.items th {
#       padding: 7px 5px;
#       text-align: left;
#       font-size: 7.5px;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#       color: #1e3a8a;
#       border-bottom: 2px solid #bfdbfe;
#     }

#     table.items td {
#       padding: 7px 5px;
#       font-size: 9px;
#       line-height: 1.3;
#       border-bottom: 1px solid #f1f5f9;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) {
#       background: #f8fafc;
#     }

#     .item-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .item-sub {
#       display: block;
#       margin-top: 2px;
#       font-size: 7.8px;
#       color: #94a3b8;
#     }

#     .muted {
#       color: #64748b;
#     }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num {
#       text-align: right;
#     }

#     .empty-items {
#       text-align: center;
#       padding: 14px 6px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-block {
#       margin-left: auto;
#       width: 58mm;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .totals-block table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals-block td {
#       padding: 6px 8px;
#       font-size: 9px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals-block td:first-child {
#       color: #64748b;
#       font-weight: 600;
#     }

#     .totals-block td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #eff6ff;
#       font-size: 13px;
#       font-weight: 800;
#       color: #1e3a8a !important;
#       border-top: 2px solid #bfdbfe;
#       border-bottom: none;
#       padding-top: 8px;
#       padding-bottom: 8px;
#     }

#     .notes {
#       margin-top: 7mm;
#       padding: 9px 10px;
#       background: #eff6ff;
#       border-left: 4px solid #1e3a8a;
#       border-radius: 6px;
#     }

#     .notes-title {
#       margin: 0;
#       font-size: 8px;
#       color: #1e3a8a;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.8px;
#     }

#     .notes-text {
#       margin: 4px 0 0;
#       font-size: 9px;
#       line-height: 1.45;
#       color: #334155;
#     }

#     .footer {
#       margin-top: 7mm;
#       padding-top: 4mm;
#       border-top: 1px solid #e2e8f0;
#       font-size: 8px;
#       line-height: 1.45;
#       color: #94a3b8;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="sidebar">
#       <h1>{{ tenant.company_name }}</h1>
#       <p class="sub">Inventory Platform</p>

#       <div class="section">
#         <p class="label">Invoice</p>
#         <p class="doc-num">{{ invoice.invoice_number }}</p>

#         {% if invoice.status %}
#           <span class="status-badge">{{ invoice.status }}</span>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Date</p>
#         <p class="value">{{ invoice.invoice_date }}</p>

#         {% if invoice.due_date %}
#           <p class="label" style="margin-top:5px;">Due Date</p>
#           <p class="value">{{ invoice.due_date }}</p>
#         {% endif %}

#         {% if sales_order %}
#           <p class="label" style="margin-top:5px;">Sales Order</p>
#           <p class="value">{{ sales_order.so_number }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Bill To</p>
#         <p class="value">{{ customer.name }}</p>

#         {% if customer.email %}
#           <p class="muted">{{ customer.email }}</p>
#         {% endif %}

#         {% if customer.phone %}
#           <p class="muted">{{ customer.phone }}</p>
#         {% endif %}

#         {% if customer.billing_address %}
#           <p class="muted">{{ customer.billing_address }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Amount Due</p>
#         <p class="amount-due">
#           {{ currency_symbol | default("₹") }}{{ invoice.total_amount }}
#         </p>
#       </div>

#       <div class="sidebar-footer">
#         {% if tenant.contact_email %}
#           {{ tenant.contact_email }}<br>
#         {% endif %}

#         {% if tenant.phone %}
#           {{ tenant.phone }}<br>
#         {% endif %}

#         {% if tenant.address %}
#           {{ tenant.address }}
#         {% endif %}
#       </div>
#     </div>

#     <div class="main">
#       <div class="main-title">
#         <p>INVOICE</p>
#         <span>Thank you for your business.</span>
#       </div>

#       <table class="items">
#         <thead>
#           <tr>
#             <th style="width:34%;">Item</th>
#             <th style="width:20%;">Warehouse</th>
#             <th class="num" style="width:9%;">Qty</th>
#             <th class="num" style="width:13%;">Rate</th>
#             <th class="num" style="width:10%;">Tax</th>
#             <th class="num" style="width:14%;">Amount</th>
#           </tr>
#         </thead>

#         <tbody>
#           {% if items %}
#             {% for item in items %}
#             <tr>
#               <td>
#                 <span class="item-name">{{ item.product_name }}</span>

#                 {% if item.sku %}
#                   <span class="item-sub">SKU: {{ item.sku }}</span>
#                 {% endif %}
#               </td>

#               <td class="muted">{{ item.warehouse_name }}</td>

#               <td class="num">{{ item.quantity }}</td>

#               <td class="num">
#                 {{ currency_symbol | default("₹") }}{{ item.unit_price }}
#               </td>

#               <td class="num muted">{{ item.tax_rate }}%</td>

#               <td class="num" style="font-weight:700;">
#                 {{ currency_symbol | default("₹") }}{{ item.total_price }}
#               </td>
#             </tr>
#             {% endfor %}
#           {% else %}
#             <tr>
#               <td colspan="6" class="empty-items">No invoice items available.</td>
#             </tr>
#           {% endif %}
#         </tbody>
#       </table>

#       <div class="totals-block">
#         <table>
#           <tr>
#             <td>Subtotal</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
#           </tr>

#           <tr>
#             <td>Tax</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
#           </tr>

#           {% if invoice.discount_amount %}
#           <tr>
#             <td>Discount</td>
#             <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
#           </tr>
#           {% endif %}

#           <tr class="total-row">
#             <td>Total</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
#           </tr>
#         </table>
#       </div>

#       {% if invoice.notes %}
#         <div class="notes">
#           <p class="notes-title">Notes</p>
#           <p class="notes-text">{{ invoice.notes }}</p>
#         </div>
#       {% endif %}

#       <div class="footer">
#         {% if tenant.footer %}
#           {{ tenant.footer }}
#         {% else %}
#           This invoice was generated by {{ tenant.company_name }} using Warelyn.
#         {% endif %}
#       </div>
#     </div>
#   </div>
# </body>
# </html>'''

# _MODERN_BILL_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Bill {{ bill.bill_number }}</title>

#   <style>
#     @page { size: A4; margin: 0; }
#     * { box-sizing: border-box; }

#     html, body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       overflow: hidden;
#       background: #ffffff;
#       font-family: "Helvetica Neue", Arial, sans-serif;
#       font-size: 10px;
#       color: #1e293b;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       display: flex;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .sidebar {
#       width: 62mm;
#       height: 297mm;
#       background: #1e3a8a;
#       color: #ffffff;
#       padding: 18mm 8mm 8mm;
#       overflow: hidden;
#     }

#     .sidebar h1 {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       letter-spacing: -0.4px;
#       margin: 0 0 4px;
#       color: #ffffff;
#       word-break: break-word;
#     }

#     .sub {
#       font-size: 8px;
#       opacity: 0.72;
#       text-transform: uppercase;
#       letter-spacing: 1.1px;
#       margin: 0 0 18mm;
#     }

#     .section { margin-bottom: 8mm; }

#     .label {
#       font-size: 7px;
#       text-transform: uppercase;
#       letter-spacing: 1px;
#       opacity: 0.62;
#       margin: 0 0 3px;
#     }

#     .value {
#       font-size: 9.5px;
#       line-height: 1.35;
#       color: #ffffff;
#       font-weight: 600;
#       margin: 0;
#       word-break: break-word;
#     }

#     .muted {
#       font-size: 8px;
#       line-height: 1.35;
#       color: rgba(255, 255, 255, 0.78);
#       margin: 2px 0 0;
#       word-break: break-word;
#     }

#     .doc-num {
#       font-size: 21px;
#       line-height: 1.12;
#       font-weight: 800;
#       color: #93c5fd;
#       margin: 0;
#       word-break: break-word;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border-radius: 999px;
#       background: rgba(147, 197, 253, 0.15);
#       border: 1px solid rgba(147, 197, 253, 0.35);
#       color: #bfdbfe;
#       font-size: 7px;
#       font-weight: 700;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .amount-due {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       color: #bfdbfe;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar-footer {
#       margin-top: 14mm;
#       font-size: 8px;
#       line-height: 1.4;
#       color: rgba(255, 255, 255, 0.58);
#       word-break: break-word;
#     }

#     .main {
#       width: 148mm;
#       height: 297mm;
#       padding: 11mm 10mm 8mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .main-title {
#       margin-bottom: 7mm;
#       padding-bottom: 4mm;
#       border-bottom: 1px solid #e2e8f0;
#     }

#     .main-title p {
#       margin: 0;
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 800;
#       color: #1e3a8a;
#       letter-spacing: -1px;
#     }

#     .main-title span {
#       display: block;
#       margin-top: 4px;
#       font-size: 9px;
#       color: #64748b;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr { background: #eff6ff; }

#     table.items th {
#       padding: 7px 5px;
#       text-align: left;
#       font-size: 7.5px;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#       color: #1e3a8a;
#       border-bottom: 2px solid #bfdbfe;
#     }

#     table.items td {
#       padding: 7px 5px;
#       font-size: 9px;
#       line-height: 1.3;
#       border-bottom: 1px solid #f1f5f9;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) { background: #f8fafc; }

#     .item-name { font-weight: 700; color: #0f172a; }

#     .item-sub {
#       display: block;
#       margin-top: 2px;
#       font-size: 7.8px;
#       color: #94a3b8;
#     }

#     .text-muted { color: #64748b; }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num { text-align: right; }

#     .empty-items {
#       text-align: center;
#       padding: 14px 6px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-block {
#       margin-left: auto;
#       width: 58mm;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .totals-block table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals-block td {
#       padding: 6px 8px;
#       font-size: 9px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals-block td:first-child {
#       color: #64748b;
#       font-weight: 600;
#     }

#     .totals-block td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #eff6ff;
#       font-size: 13px;
#       font-weight: 800;
#       color: #1e3a8a !important;
#       border-top: 2px solid #bfdbfe;
#       border-bottom: none;
#       padding-top: 8px;
#       padding-bottom: 8px;
#     }

#     .notes {
#       margin-top: 7mm;
#       padding: 9px 10px;
#       background: #eff6ff;
#       border-left: 4px solid #1e3a8a;
#       border-radius: 6px;
#     }

#     .notes-title {
#       margin: 0;
#       font-size: 8px;
#       color: #1e3a8a;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.8px;
#     }

#     .notes-text {
#       margin: 4px 0 0;
#       font-size: 9px;
#       line-height: 1.45;
#       color: #334155;
#     }

#     .footer {
#       margin-top: 7mm;
#       padding-top: 4mm;
#       border-top: 1px solid #e2e8f0;
#       font-size: 8px;
#       line-height: 1.45;
#       color: #94a3b8;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="sidebar">
#       <h1>{{ tenant.company_name }}</h1>
#       <p class="sub">Inventory Platform</p>

#       <div class="section">
#         <p class="label">Bill</p>
#         <p class="doc-num">{{ bill.bill_number }}</p>
#         {% if bill.status %}
#           <span class="status-badge">{{ bill.status }}</span>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Date</p>
#         <p class="value">{{ bill.bill_date }}</p>

#         {% if bill.due_date %}
#           <p class="label" style="margin-top:5px;">Due Date</p>
#           <p class="value">{{ bill.due_date }}</p>
#         {% endif %}

#         {% if purchase_order %}
#           <p class="label" style="margin-top:5px;">Purchase Order</p>
#           <p class="value">{{ purchase_order.po_number }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Vendor</p>
#         <p class="value">{{ vendor.name }}</p>
#         {% if vendor.email %}<p class="muted">{{ vendor.email }}</p>{% endif %}
#         {% if vendor.phone %}<p class="muted">{{ vendor.phone }}</p>{% endif %}
#         {% if vendor.address %}<p class="muted">{{ vendor.address }}</p>{% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Amount Due</p>
#         <p class="amount-due">{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</p>
#       </div>

#       <div class="sidebar-footer">
#         {% if tenant.contact_email %}{{ tenant.contact_email }}<br>{% endif %}
#         {% if tenant.phone %}{{ tenant.phone }}<br>{% endif %}
#         {% if tenant.address %}{{ tenant.address }}{% endif %}
#       </div>
#     </div>

#     <div class="main">
#       <div class="main-title">
#         <p>BILL</p>
#         <span>Vendor bill summary for your purchase records.</span>
#       </div>

#       <table class="items">
#         <thead>
#           <tr>
#             <th style="width:34%;">Item</th>
#             <th style="width:20%;">Warehouse</th>
#             <th class="num" style="width:9%;">Qty</th>
#             <th class="num" style="width:13%;">Rate</th>
#             <th class="num" style="width:10%;">Tax</th>
#             <th class="num" style="width:14%;">Amount</th>
#           </tr>
#         </thead>

#         <tbody>
#           {% if items %}
#             {% for item in items %}
#             <tr>
#               <td>
#                 <span class="item-name">{{ item.product_name }}</span>
#                 {% if item.sku %}<span class="item-sub">SKU: {{ item.sku }}</span>{% endif %}
#               </td>
#               <td class="text-muted">{{ item.warehouse_name }}</td>
#               <td class="num">{{ item.quantity_ordered }}</td>
#               <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
#               <td class="num text-muted">{{ item.tax_rate }}%</td>
#               <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
#             </tr>
#             {% endfor %}
#           {% else %}
#             <tr>
#               <td colspan="6" class="empty-items">No bill items available.</td>
#             </tr>
#           {% endif %}
#         </tbody>
#       </table>

#       <div class="totals-block">
#         <table>
#           <tr><td>Subtotal</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
#           <tr><td>Tax</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
#           <tr class="total-row"><td>Total</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
#         </table>
#       </div>

#       {% if bill.notes %}
#         <div class="notes">
#           <p class="notes-title">Notes</p>
#           <p class="notes-text">{{ bill.notes }}</p>
#         </div>
#       {% endif %}

#       <div class="footer">
#         {% if tenant.footer %}
#           {{ tenant.footer }}
#         {% else %}
#           This bill was generated by {{ tenant.company_name }} using Warelyn.
#         {% endif %}
#       </div>
#     </div>
#   </div>
# </body>
# </html>'''

# _MINIMAL_INVOICE_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Invoice {{ invoice.invoice_number }}</title>

#   <style>
#     @page {
#       size: A4;
#       margin: 0;
#     }

#     * {
#       box-sizing: border-box;
#     }

#     html,
#     body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       background: #ffffff;
#       font-family: Georgia, "Times New Roman", serif;
#       color: #1e293b;
#       overflow: hidden;
#     }

#     body {
#       font-size: 11px;
#       line-height: 1.45;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       padding: 18mm 16mm 14mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .top {
#       display: flex;
#       justify-content: space-between;
#       align-items: flex-start;
#       gap: 16mm;
#       margin-bottom: 13mm;
#       border-bottom: 0.5px solid #cbd5e1;
#       padding-bottom: 7mm;
#     }

#     .company-block {
#       max-width: 95mm;
#     }

#     .company-name {
#       font-size: 24px;
#       line-height: 1.1;
#       font-weight: bold;
#       letter-spacing: -1px;
#       color: #0f172a;
#       margin: 0;
#     }

#     .company-detail {
#       margin: 4px 0 0;
#       font-size: 10px;
#       line-height: 1.45;
#       color: #94a3b8;
#       word-break: break-word;
#     }

#     .doc-title {
#       text-align: right;
#       min-width: 55mm;
#     }

#     .doc-title h2 {
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 300;
#       letter-spacing: 4px;
#       color: #cbd5e1;
#       margin: 0;
#       text-transform: uppercase;
#     }

#     .doc-title .num {
#       margin: 7px 0 0;
#       font-size: 14px;
#       line-height: 1.25;
#       font-weight: bold;
#       color: #1e3a8a;
#       word-break: break-word;
#     }

#     .doc-title .date {
#       margin: 4px 0 0;
#       font-size: 10px;
#       color: #64748b;
#     }

#     .status {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border: 0.5px solid #dbeafe;
#       border-radius: 999px;
#       background: #eff6ff;
#       color: #1e3a8a;
#       font-size: 7px;
#       font-family: Arial, sans-serif;
#       font-weight: 700;
#       letter-spacing: 1px;
#       text-transform: uppercase;
#     }

#     .parties {
#       display: flex;
#       gap: 16mm;
#       margin-bottom: 11mm;
#     }

#     .party {
#       flex: 1;
#       min-height: 22mm;
#     }

#     .party .label {
#       font-size: 8px;
#       text-transform: uppercase;
#       letter-spacing: 2px;
#       color: #94a3b8;
#       margin: 0 0 6px;
#     }

#     .party .name {
#       font-size: 13px;
#       line-height: 1.35;
#       font-weight: bold;
#       color: #0f172a;
#       margin: 0;
#     }

#     .party .muted {
#       color: #64748b;
#       font-size: 10px;
#       line-height: 1.45;
#       margin: 3px 0 0;
#       word-break: break-word;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 8mm 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr th {
#       font-size: 8px;
#       text-transform: uppercase;
#       letter-spacing: 1.5px;
#       color: #94a3b8;
#       padding: 8px 0;
#       text-align: left;
#       border-bottom: 0.5px solid #e2e8f0;
#       font-weight: bold;
#     }

#     table.items tbody tr td {
#       padding: 9px 0;
#       border-bottom: 0.5px solid #f1f5f9;
#       font-size: 10.5px;
#       line-height: 1.35;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     .description {
#       font-weight: bold;
#       color: #0f172a;
#     }

#     .subtext {
#       display: block;
#       margin-top: 2px;
#       font-size: 8.5px;
#       color: #94a3b8;
#       font-weight: normal;
#     }

#     .num-col {
#       text-align: right !important;
#       white-space: nowrap;
#     }

#     .muted-col {
#       color: #94a3b8;
#     }

#     .empty-items {
#       text-align: center;
#       padding: 16px 0 !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals {
#       width: 56mm;
#       margin-left: auto;
#       margin-top: 4mm;
#     }

#     .totals table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals table td {
#       padding: 4px 0;
#       font-size: 10.5px;
#       border-bottom: none;
#     }

#     .totals table td:first-child {
#       color: #64748b;
#     }

#     .totals table td:last-child {
#       text-align: right;
#       color: #0f172a;
#       font-weight: bold;
#       white-space: nowrap;
#     }

#     .grand-total td {
#       font-size: 16px !important;
#       font-weight: bold;
#       color: #0f172a !important;
#       border-top: 1px solid #1e293b;
#       padding-top: 8px !important;
#     }

#     .notes {
#       margin-top: 8mm;
#       padding-top: 4mm;
#       border-top: 0.5px solid #e2e8f0;
#       font-size: 10px;
#       line-height: 1.55;
#       color: #94a3b8;
#     }

#     .footer {
#       margin-top: 10mm;
#       font-size: 9px;
#       line-height: 1.5;
#       color: #cbd5e1;
#       border-top: 0.5px solid #e2e8f0;
#       padding-top: 4mm;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">

#     <div class="top">
#       <div class="company-block">
#         <p class="company-name">{{ tenant.company_name }}</p>

#         {% if tenant.contact_email %}
#           <p class="company-detail">{{ tenant.contact_email }}</p>
#         {% endif %}

#         {% if tenant.phone %}
#           <p class="company-detail">{{ tenant.phone }}</p>
#         {% endif %}

#         {% if tenant.address %}
#           <p class="company-detail">{{ tenant.address }}</p>
#         {% endif %}
#       </div>

#       <div class="doc-title">
#         <h2>Invoice</h2>
#         <p class="num">{{ invoice.invoice_number }}</p>
#         <p class="date">{{ invoice.invoice_date }}</p>

#         {% if invoice.status %}
#           <span class="status">{{ invoice.status }}</span>
#         {% endif %}
#       </div>
#     </div>

#     <div class="parties">
#       <div class="party">
#         <p class="label">Bill To</p>
#         <p class="name">{{ customer.name }}</p>

#         {% if customer.email %}
#           <p class="muted">{{ customer.email }}</p>
#         {% endif %}

#         {% if customer.phone %}
#           <p class="muted">{{ customer.phone }}</p>
#         {% endif %}

#         {% if customer.billing_address %}
#           <p class="muted">{{ customer.billing_address }}</p>
#         {% endif %}
#       </div>

#       <div class="party">
#         <p class="label">Invoice Details</p>

#         {% if invoice.due_date %}
#           <p class="name">Due {{ invoice.due_date }}</p>
#         {% else %}
#           <p class="name">Due on receipt</p>
#         {% endif %}

#         {% if sales_order %}
#           <p class="muted">Sales Order: {{ sales_order.so_number }}</p>
#         {% endif %}
#       </div>
#     </div>

#     <table class="items">
#       <thead>
#         <tr>
#           <th style="width: 42%;">Description</th>
#           <th class="num-col" style="width: 10%;">Qty</th>
#           <th class="num-col" style="width: 16%;">Rate</th>
#           <th class="num-col" style="width: 12%;">Tax</th>
#           <th class="num-col" style="width: 20%;">Amount</th>
#         </tr>
#       </thead>

#       <tbody>
#         {% if items %}
#           {% for item in items %}
#           <tr>
#             <td>
#               <span class="description">{{ item.product_name }}</span>

#               {% if item.warehouse_name %}
#                 <span class="subtext">Warehouse: {{ item.warehouse_name }}</span>
#               {% endif %}

#               {% if item.sku %}
#                 <span class="subtext">SKU: {{ item.sku }}</span>
#               {% endif %}
#             </td>

#             <td class="num-col">{{ item.quantity }}</td>

#             <td class="num-col">
#               {{ currency_symbol | default("₹") }}{{ item.unit_price }}
#             </td>

#             <td class="num-col muted-col">
#               {{ item.tax_rate }}%
#             </td>

#             <td class="num-col">
#               {{ currency_symbol | default("₹") }}{{ item.total_price }}
#             </td>
#           </tr>
#           {% endfor %}
#         {% else %}
#           <tr>
#             <td colspan="5" class="empty-items">No invoice items available.</td>
#           </tr>
#         {% endif %}
#       </tbody>
#     </table>

#     <div class="totals">
#       <table>
#         <tr>
#           <td>Subtotal</td>
#           <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
#         </tr>

#         <tr>
#           <td>Tax</td>
#           <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
#         </tr>

#         {% if invoice.discount_amount %}
#         <tr>
#           <td>Discount</td>
#           <td>({{ currency_symbol | default("₹") }}{{ invoice.discount_amount }})</td>
#         </tr>
#         {% endif %}

#         <tr class="grand-total">
#           <td>Total</td>
#           <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
#         </tr>
#       </table>
#     </div>

#     {% if invoice.notes %}
#       <p class="notes">
#         <em>{{ invoice.notes }}</em>
#       </p>
#     {% endif %}

#     <p class="footer">
#       {% if tenant.footer %}
#         {{ tenant.footer }}
#       {% else %}
#         This invoice was generated by {{ tenant.company_name }} using Warelyn.
#       {% endif %}
#     </p>

#   </div>
# </body>
# </html>'''

# _MINIMAL_BILL_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Bill {{ bill.bill_number }}</title>

#   <style>
#     @page { size: A4; margin: 0; }

#     * { box-sizing: border-box; }

#     html, body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       background: #ffffff;
#       font-family: Georgia, "Times New Roman", serif;
#       color: #1e293b;
#       overflow: hidden;
#     }

#     body {
#       font-size: 11px;
#       line-height: 1.45;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       padding: 18mm 16mm 14mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .top {
#       display: flex;
#       justify-content: space-between;
#       align-items: flex-start;
#       gap: 16mm;
#       margin-bottom: 13mm;
#       border-bottom: 0.5px solid #cbd5e1;
#       padding-bottom: 7mm;
#     }

#     .company-block { max-width: 95mm; }

#     .company-name {
#       font-size: 24px;
#       line-height: 1.1;
#       font-weight: bold;
#       letter-spacing: -1px;
#       color: #0f172a;
#       margin: 0;
#     }

#     .company-detail {
#       margin: 4px 0 0;
#       font-size: 10px;
#       line-height: 1.45;
#       color: #94a3b8;
#       word-break: break-word;
#     }

#     .doc-title {
#       text-align: right;
#       min-width: 55mm;
#     }

#     .doc-title h2 {
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 300;
#       letter-spacing: 4px;
#       color: #cbd5e1;
#       margin: 0;
#       text-transform: uppercase;
#     }

#     .doc-title .num {
#       margin: 7px 0 0;
#       font-size: 14px;
#       line-height: 1.25;
#       font-weight: bold;
#       color: #1e3a8a;
#       word-break: break-word;
#     }

#     .doc-title .date {
#       margin: 4px 0 0;
#       font-size: 10px;
#       color: #64748b;
#     }

#     .parties {
#       display: flex;
#       gap: 16mm;
#       margin-bottom: 11mm;
#     }

#     .party {
#       flex: 1;
#       min-height: 22mm;
#     }

#     .party .label {
#       font-size: 8px;
#       text-transform: uppercase;
#       letter-spacing: 2px;
#       color: #94a3b8;
#       margin: 0 0 6px;
#     }

#     .party .name {
#       font-size: 13px;
#       line-height: 1.35;
#       font-weight: bold;
#       color: #0f172a;
#       margin: 0;
#     }

#     .party .muted {
#       color: #64748b;
#       font-size: 10px;
#       line-height: 1.45;
#       margin: 3px 0 0;
#       word-break: break-word;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 8mm 0 6mm;
#       table-layout: fixed;
#     }

#     table.items th {
#       font-size: 8px;
#       text-transform: uppercase;
#       letter-spacing: 1.5px;
#       color: #94a3b8;
#       padding: 8px 0;
#       text-align: left;
#       border-bottom: 0.5px solid #e2e8f0;
#       font-weight: bold;
#     }

#     table.items td {
#       padding: 9px 0;
#       border-bottom: 0.5px solid #f1f5f9;
#       font-size: 10.5px;
#       line-height: 1.35;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     .description {
#       font-weight: bold;
#       color: #0f172a;
#     }

#     .subtext {
#       display: block;
#       margin-top: 2px;
#       font-size: 8.5px;
#       color: #94a3b8;
#       font-weight: normal;
#     }

#     .num-col {
#       text-align: right !important;
#       white-space: nowrap;
#     }

#     .muted-col { color: #94a3b8; }

#     .empty-items {
#       text-align: center;
#       padding: 16px 0 !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals {
#       width: 56mm;
#       margin-left: auto;
#       margin-top: 4mm;
#     }

#     .totals table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals td {
#       padding: 4px 0;
#       font-size: 10.5px;
#     }

#     .totals td:first-child { color: #64748b; }

#     .totals td:last-child {
#       text-align: right;
#       color: #0f172a;
#       font-weight: bold;
#       white-space: nowrap;
#     }

#     .grand-total td {
#       font-size: 16px !important;
#       font-weight: bold;
#       color: #0f172a !important;
#       border-top: 1px solid #1e293b;
#       padding-top: 8px !important;
#     }

#     .notes {
#       margin-top: 8mm;
#       padding-top: 4mm;
#       border-top: 0.5px solid #e2e8f0;
#       font-size: 10px;
#       line-height: 1.55;
#       color: #94a3b8;
#     }

#     .footer {
#       margin-top: 10mm;
#       font-size: 9px;
#       line-height: 1.5;
#       color: #cbd5e1;
#       border-top: 0.5px solid #e2e8f0;
#       padding-top: 4mm;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="top">
#       <div class="company-block">
#         <p class="company-name">{{ tenant.company_name }}</p>
#         {% if tenant.contact_email %}<p class="company-detail">{{ tenant.contact_email }}</p>{% endif %}
#         {% if tenant.phone %}<p class="company-detail">{{ tenant.phone }}</p>{% endif %}
#         {% if tenant.address %}<p class="company-detail">{{ tenant.address }}</p>{% endif %}
#       </div>

#       <div class="doc-title">
#         <h2>Bill</h2>
#         <p class="num">{{ bill.bill_number }}</p>
#         <p class="date">{{ bill.bill_date }}</p>
#       </div>
#     </div>

#     <div class="parties">
#       <div class="party">
#         <p class="label">Vendor</p>
#         <p class="name">{{ vendor.name }}</p>
#         {% if vendor.email %}<p class="muted">{{ vendor.email }}</p>{% endif %}
#         {% if vendor.phone %}<p class="muted">{{ vendor.phone }}</p>{% endif %}
#         {% if vendor.address %}<p class="muted">{{ vendor.address }}</p>{% endif %}
#       </div>

#       <div class="party">
#         <p class="label">Bill Details</p>
#         {% if bill.due_date %}
#           <p class="name">Due {{ bill.due_date }}</p>
#         {% else %}
#           <p class="name">Due on receipt</p>
#         {% endif %}
#         {% if purchase_order %}
#           <p class="muted">Purchase Order: {{ purchase_order.po_number }}</p>
#         {% endif %}
#       </div>
#     </div>

#     <table class="items">
#       <thead>
#         <tr>
#           <th style="width:42%;">Description</th>
#           <th class="num-col" style="width:10%;">Qty</th>
#           <th class="num-col" style="width:16%;">Rate</th>
#           <th class="num-col" style="width:12%;">Tax</th>
#           <th class="num-col" style="width:20%;">Amount</th>
#         </tr>
#       </thead>

#       <tbody>
#         {% if items %}
#           {% for item in items %}
#           <tr>
#             <td>
#               <span class="description">{{ item.product_name }}</span>
#               {% if item.warehouse_name %}
#                 <span class="subtext">Warehouse: {{ item.warehouse_name }}</span>
#               {% endif %}
#               {% if item.sku %}
#                 <span class="subtext">SKU: {{ item.sku }}</span>
#               {% endif %}
#             </td>
#             <td class="num-col">{{ item.quantity_ordered }}</td>
#             <td class="num-col">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
#             <td class="num-col muted-col">{{ item.tax_rate }}%</td>
#             <td class="num-col">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
#           </tr>
#           {% endfor %}
#         {% else %}
#           <tr>
#             <td colspan="5" class="empty-items">No bill items available.</td>
#           </tr>
#         {% endif %}
#       </tbody>
#     </table>

#     <div class="totals">
#       <table>
#         <tr><td>Subtotal</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
#         <tr><td>Tax</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
#         <tr class="grand-total"><td>Total</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
#       </table>
#     </div>

#     {% if bill.notes %}
#       <p class="notes"><em>{{ bill.notes }}</em></p>
#     {% endif %}

#     <p class="footer">
#       {% if tenant.footer %}
#         {{ tenant.footer }}
#       {% else %}
#         This bill was generated by {{ tenant.company_name }} using Warelyn.
#       {% endif %}
#     </p>
#   </div>
# </body>
# </html>'''

# _BOLD_INVOICE_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Invoice {{ invoice.invoice_number }}</title>

#   <style>
#     @page {
#       size: A4;
#       margin: 0;
#     }

#     * {
#       box-sizing: border-box;
#     }

#     html,
#     body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       overflow: hidden;
#       background: #ffffff;
#       font-family: "Helvetica Neue", Arial, sans-serif;
#       font-size: 10px;
#       color: #1e293b;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       display: flex;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .sidebar {
#       width: 62mm;
#       height: 297mm;
#       background: #0f172a;
#       color: #ffffff;
#       padding: 18mm 8mm 8mm;
#       overflow: hidden;
#     }

#     .sidebar h1 {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       letter-spacing: -0.4px;
#       margin: 0 0 4px;
#       color: #ffffff;
#       word-break: break-word;
#     }

#     .sidebar .sub {
#       font-size: 8px;
#       opacity: 0.72;
#       text-transform: uppercase;
#       letter-spacing: 1.1px;
#       margin: 0 0 18mm;
#     }

#     .sidebar .section {
#       margin-bottom: 8mm;
#     }

#     .sidebar .label {
#       font-size: 7px;
#       text-transform: uppercase;
#       letter-spacing: 1px;
#       opacity: 0.62;
#       margin: 0 0 3px;
#     }

#     .sidebar .value {
#       font-size: 9.5px;
#       line-height: 1.35;
#       color: #ffffff;
#       font-weight: 600;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar .muted {
#       font-size: 8px;
#       line-height: 1.35;
#       color: rgba(255, 255, 255, 0.78);
#       margin: 2px 0 0;
#       word-break: break-word;
#     }

#     .sidebar .doc-num {
#       font-size: 21px;
#       line-height: 1.12;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border-radius: 999px;
#       background: rgba(252, 211, 77, 0.14);
#       border: 1px solid rgba(252, 211, 77, 0.32);
#       color: #fcd34d;
#       font-size: 7px;
#       font-weight: 700;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .amount-due {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar-footer {
#       margin-top: 14mm;
#       font-size: 8px;
#       line-height: 1.4;
#       color: rgba(255, 255, 255, 0.58);
#       word-break: break-word;
#     }

#     .main {
#       width: 148mm;
#       height: 297mm;
#       padding: 11mm 10mm 8mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .main-title {
#       margin-bottom: 7mm;
#       padding-bottom: 4mm;
#       border-bottom: 1px solid #e2e8f0;
#     }

#     .main-title p {
#       margin: 0;
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 800;
#       color: #f59e0b;
#       letter-spacing: -1px;
#     }

#     .main-title span {
#       display: block;
#       margin-top: 4px;
#       font-size: 9px;
#       color: #64748b;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr {
#       background: #fffbeb;
#     }

#     table.items th {
#       padding: 7px 5px;
#       text-align: left;
#       font-size: 7.5px;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#       color: #f59e0b;
#       border-bottom: 2px solid #f59e0b;
#     }

#     table.items td {
#       padding: 7px 5px;
#       font-size: 9px;
#       line-height: 1.3;
#       border-bottom: 1px solid #f1f5f9;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) {
#       background: #fffbeb;
#     }

#     .item-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .item-sub {
#       display: block;
#       margin-top: 2px;
#       font-size: 7.8px;
#       color: #94a3b8;
#     }

#     .muted {
#       color: #64748b;
#     }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num {
#       text-align: right;
#     }

#     .empty-items {
#       text-align: center;
#       padding: 14px 6px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-block {
#       margin-left: auto;
#       width: 58mm;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .totals-block table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals-block td {
#       padding: 6px 8px;
#       font-size: 9px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals-block td:first-child {
#       color: #64748b;
#       font-weight: 600;
#     }

#     .totals-block td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #fffbeb;
#       font-size: 13px;
#       font-weight: 800;
#       color: #f59e0b !important;
#       border-top: 2px solid #f59e0b;
#       border-bottom: none;
#       padding-top: 8px;
#       padding-bottom: 8px;
#     }

#     .notes {
#       margin-top: 7mm;
#       padding: 9px 10px;
#       background: #fffbeb;
#       border-left: 4px solid #f59e0b;
#       border-radius: 6px;
#     }

#     .notes-title {
#       margin: 0;
#       font-size: 8px;
#       color: #92400e;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.8px;
#     }

#     .notes-text {
#       margin: 4px 0 0;
#       font-size: 9px;
#       line-height: 1.45;
#       color: #78350f;
#     }

#     .footer {
#       margin-top: 7mm;
#       padding-top: 4mm;
#       border-top: 1px solid #e2e8f0;
#       font-size: 8px;
#       line-height: 1.45;
#       color: #94a3b8;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="sidebar">
#       <h1>{{ tenant.company_name }}</h1>
#       <p class="sub">Inventory Platform</p>

#       <div class="section">
#         <p class="label">Invoice</p>
#         <p class="doc-num">{{ invoice.invoice_number }}</p>

#         {% if invoice.status %}
#           <span class="status-badge">{{ invoice.status }}</span>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Date</p>
#         <p class="value">{{ invoice.invoice_date }}</p>

#         {% if invoice.due_date %}
#           <p class="label" style="margin-top:5px;">Due Date</p>
#           <p class="value">{{ invoice.due_date }}</p>
#         {% endif %}

#         {% if sales_order %}
#           <p class="label" style="margin-top:5px;">Sales Order</p>
#           <p class="value">{{ sales_order.so_number }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Bill To</p>
#         <p class="value">{{ customer.name }}</p>

#         {% if customer.email %}
#           <p class="muted">{{ customer.email }}</p>
#         {% endif %}

#         {% if customer.phone %}
#           <p class="muted">{{ customer.phone }}</p>
#         {% endif %}

#         {% if customer.billing_address %}
#           <p class="muted">{{ customer.billing_address }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Amount Due</p>
#         <p class="amount-due">
#           {{ currency_symbol | default("₹") }}{{ invoice.total_amount }}
#         </p>
#       </div>

#       <div class="sidebar-footer">
#         {% if tenant.contact_email %}
#           {{ tenant.contact_email }}<br>
#         {% endif %}

#         {% if tenant.phone %}
#           {{ tenant.phone }}<br>
#         {% endif %}

#         {% if tenant.address %}
#           {{ tenant.address }}
#         {% endif %}
#       </div>
#     </div>

#     <div class="main">
#       <div class="main-title">
#         <p>INVOICE</p>
#         <span>Thank you for your business.</span>
#       </div>

#       <table class="items">
#         <thead>
#           <tr>
#             <th style="width:34%;">Item</th>
#             <th style="width:20%;">Warehouse</th>
#             <th class="num" style="width:9%;">Qty</th>
#             <th class="num" style="width:13%;">Rate</th>
#             <th class="num" style="width:10%;">Tax</th>
#             <th class="num" style="width:14%;">Amount</th>
#           </tr>
#         </thead>

#         <tbody>
#           {% if items %}
#             {% for item in items %}
#             <tr>
#               <td>
#                 <span class="item-name">{{ item.product_name }}</span>

#                 {% if item.sku %}
#                   <span class="item-sub">SKU: {{ item.sku }}</span>
#                 {% endif %}
#               </td>

#               <td class="muted">{{ item.warehouse_name }}</td>

#               <td class="num">{{ item.quantity }}</td>

#               <td class="num">
#                 {{ currency_symbol | default("₹") }}{{ item.unit_price }}
#               </td>

#               <td class="num muted">{{ item.tax_rate }}%</td>

#               <td class="num" style="font-weight:700;">
#                 {{ currency_symbol | default("₹") }}{{ item.total_price }}
#               </td>
#             </tr>
#             {% endfor %}
#           {% else %}
#             <tr>
#               <td colspan="6" class="empty-items">No invoice items available.</td>
#             </tr>
#           {% endif %}
#         </tbody>
#       </table>

#       <div class="totals-block">
#         <table>
#           <tr>
#             <td>Subtotal</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
#           </tr>

#           <tr>
#             <td>Tax</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
#           </tr>

#           {% if invoice.discount_amount %}
#           <tr>
#             <td>Discount</td>
#             <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
#           </tr>
#           {% endif %}

#           <tr class="total-row">
#             <td>Total</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
#           </tr>
#         </table>
#       </div>

#       {% if invoice.notes %}
#         <div class="notes">
#           <p class="notes-title">Notes</p>
#           <p class="notes-text">{{ invoice.notes }}</p>
#         </div>
#       {% endif %}

#       <div class="footer">
#         {% if tenant.footer %}
#           {{ tenant.footer }}
#         {% else %}
#           This invoice was generated by {{ tenant.company_name }} using Warelyn.
#         {% endif %}
#       </div>
#     </div>
#   </div>
# </body>
# </html>'''

# _BOLD_BILL_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Bill {{ bill.bill_number }}</title>

#   <style>
#     @page { size: A4; margin: 0; }

#     * { box-sizing: border-box; }

#     html, body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       overflow: hidden;
#       background: #ffffff;
#       font-family: "Helvetica Neue", Arial, sans-serif;
#       font-size: 10px;
#       color: #1e293b;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       display: flex;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .sidebar {
#       width: 62mm;
#       height: 297mm;
#       background: #0f172a;
#       color: #ffffff;
#       padding: 18mm 8mm 8mm;
#       overflow: hidden;
#     }

#     .sidebar h1 {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       letter-spacing: -0.4px;
#       margin: 0 0 4px;
#       color: #ffffff;
#       word-break: break-word;
#     }

#     .sidebar .sub {
#       font-size: 8px;
#       opacity: 0.72;
#       text-transform: uppercase;
#       letter-spacing: 1.1px;
#       margin: 0 0 18mm;
#     }

#     .section { margin-bottom: 8mm; }

#     .label {
#       font-size: 7px;
#       text-transform: uppercase;
#       letter-spacing: 1px;
#       opacity: 0.62;
#       margin: 0 0 3px;
#     }

#     .value {
#       font-size: 9.5px;
#       line-height: 1.35;
#       color: #ffffff;
#       font-weight: 600;
#       margin: 0;
#       word-break: break-word;
#     }

#     .muted {
#       font-size: 8px;
#       line-height: 1.35;
#       color: rgba(255, 255, 255, 0.78);
#       margin: 2px 0 0;
#       word-break: break-word;
#     }

#     .doc-num {
#       font-size: 21px;
#       line-height: 1.12;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border-radius: 999px;
#       background: rgba(252, 211, 77, 0.14);
#       border: 1px solid rgba(252, 211, 77, 0.32);
#       color: #fcd34d;
#       font-size: 7px;
#       font-weight: 700;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .amount-due {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar-footer {
#       margin-top: 14mm;
#       font-size: 8px;
#       line-height: 1.4;
#       color: rgba(255, 255, 255, 0.58);
#       word-break: break-word;
#     }

#     .main {
#       width: 148mm;
#       height: 297mm;
#       padding: 11mm 10mm 8mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .main-title {
#       margin-bottom: 7mm;
#       padding-bottom: 4mm;
#       border-bottom: 1px solid #e2e8f0;
#     }

#     .main-title p {
#       margin: 0;
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 800;
#       color: #f59e0b;
#       letter-spacing: -1px;
#     }

#     .main-title span {
#       display: block;
#       margin-top: 4px;
#       font-size: 9px;
#       color: #64748b;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr { background: #fffbeb; }

#     table.items th {
#       padding: 7px 5px;
#       text-align: left;
#       font-size: 7.5px;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#       color: #f59e0b;
#       border-bottom: 2px solid #f59e0b;
#     }

#     table.items td {
#       padding: 7px 5px;
#       font-size: 9px;
#       line-height: 1.3;
#       border-bottom: 1px solid #f1f5f9;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) { background: #fffbeb; }

#     .item-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .item-sub {
#       display: block;
#       margin-top: 2px;
#       font-size: 7.8px;
#       color: #94a3b8;
#     }

#     .text-muted { color: #64748b; }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num { text-align: right; }

#     .empty-items {
#       text-align: center;
#       padding: 14px 6px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-block {
#       margin-left: auto;
#       width: 58mm;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .totals-block table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals-block td {
#       padding: 6px 8px;
#       font-size: 9px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals-block td:first-child {
#       color: #64748b;
#       font-weight: 600;
#     }

#     .totals-block td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #fffbeb;
#       font-size: 13px;
#       font-weight: 800;
#       color: #f59e0b !important;
#       border-top: 2px solid #f59e0b;
#       border-bottom: none;
#       padding-top: 8px;
#       padding-bottom: 8px;
#     }

#     .notes {
#       margin-top: 7mm;
#       padding: 9px 10px;
#       background: #fffbeb;
#       border-left: 4px solid #f59e0b;
#       border-radius: 6px;
#     }

#     .notes-title {
#       margin: 0;
#       font-size: 8px;
#       color: #92400e;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.8px;
#     }

#     .notes-text {
#       margin: 4px 0 0;
#       font-size: 9px;
#       line-height: 1.45;
#       color: #78350f;
#     }

#     .footer {
#       margin-top: 7mm;
#       padding-top: 4mm;
#       border-top: 1px solid #e2e8f0;
#       font-size: 8px;
#       line-height: 1.45;
#       color: #94a3b8;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="sidebar">
#       <h1>{{ tenant.company_name }}</h1>
#       <p class="sub">Inventory Platform</p>

#       <div class="section">
#         <p class="label">Bill</p>
#         <p class="doc-num">{{ bill.bill_number }}</p>

#         {% if bill.status %}
#           <span class="status-badge">{{ bill.status }}</span>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Date</p>
#         <p class="value">{{ bill.bill_date }}</p>

#         {% if bill.due_date %}
#           <p class="label" style="margin-top:5px;">Due Date</p>
#           <p class="value">{{ bill.due_date }}</p>
#         {% endif %}

#         {% if purchase_order %}
#           <p class="label" style="margin-top:5px;">Purchase Order</p>
#           <p class="value">{{ purchase_order.po_number }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Vendor</p>
#         <p class="value">{{ vendor.name }}</p>

#         {% if vendor.email %}
#           <p class="muted">{{ vendor.email }}</p>
#         {% endif %}

#         {% if vendor.phone %}
#           <p class="muted">{{ vendor.phone }}</p>
#         {% endif %}

#         {% if vendor.address %}
#           <p class="muted">{{ vendor.address }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Amount Due</p>
#         <p class="amount-due">{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</p>
#       </div>

#       <div class="sidebar-footer">
#         {% if tenant.contact_email %}{{ tenant.contact_email }}<br>{% endif %}
#         {% if tenant.phone %}{{ tenant.phone }}<br>{% endif %}
#         {% if tenant.address %}{{ tenant.address }}{% endif %}
#       </div>
#     </div>

#     <div class="main">
#       <div class="main-title">
#         <p>BILL</p>
#         <span>Vendor bill summary for your purchase records.</span>
#       </div>

#       <table class="items">
#         <thead>
#           <tr>
#             <th style="width:34%;">Item</th>
#             <th style="width:20%;">Warehouse</th>
#             <th class="num" style="width:9%;">Qty</th>
#             <th class="num" style="width:13%;">Rate</th>
#             <th class="num" style="width:10%;">Tax</th>
#             <th class="num" style="width:14%;">Amount</th>
#           </tr>
#         </thead>

#         <tbody>
#           {% if items %}
#             {% for item in items %}
#             <tr>
#               <td>
#                 <span class="item-name">{{ item.product_name }}</span>
#                 {% if item.sku %}
#                   <span class="item-sub">SKU: {{ item.sku }}</span>
#                 {% endif %}
#               </td>
#               <td class="text-muted">{{ item.warehouse_name }}</td>
#               <td class="num">{{ item.quantity_ordered }}</td>
#               <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
#               <td class="num text-muted">{{ item.tax_rate }}%</td>
#               <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
#             </tr>
#             {% endfor %}
#           {% else %}
#             <tr>
#               <td colspan="6" class="empty-items">No bill items available.</td>
#             </tr>
#           {% endif %}
#         </tbody>
#       </table>

#       <div class="totals-block">
#         <table>
#           <tr>
#             <td>Subtotal</td>
#             <td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td>
#           </tr>
#           <tr>
#             <td>Tax</td>
#             <td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td>
#           </tr>
#           <tr class="total-row">
#             <td>Total</td>
#             <td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td>
#           </tr>
#         </table>
#       </div>

#       {% if bill.notes %}
#         <div class="notes">
#           <p class="notes-title">Notes</p>
#           <p class="notes-text">{{ bill.notes }}</p>
#         </div>
#       {% endif %}

#       <div class="footer">
#         {% if tenant.footer %}
#           {{ tenant.footer }}
#         {% else %}
#           This bill was generated by {{ tenant.company_name }} using Warelyn.
#         {% endif %}
#       </div>
#     </div>
#   </div>
# </body>
# </html>'''

# _WARM_INVOICE_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Invoice {{ invoice.invoice_number }}</title>

#   <style>
#     @page {
#       size: A4;
#       margin: 0;
#     }

#     * {
#       box-sizing: border-box;
#     }

#     html,
#     body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       overflow: hidden;
#       background: #ffffff;
#       font-family: "Helvetica Neue", Arial, sans-serif;
#       font-size: 10px;
#       color: #1e293b;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       display: flex;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .sidebar {
#       width: 62mm;
#       height: 297mm;
#       background: #7c2d12;
#       color: #ffffff;
#       padding: 18mm 8mm 8mm;
#       overflow: hidden;
#     }

#     .sidebar h1 {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       letter-spacing: -0.4px;
#       margin: 0 0 4px;
#       color: #ffffff;
#       word-break: break-word;
#     }

#     .sidebar .sub {
#       font-size: 8px;
#       opacity: 0.72;
#       text-transform: uppercase;
#       letter-spacing: 1.1px;
#       margin: 0 0 18mm;
#     }

#     .sidebar .section {
#       margin-bottom: 8mm;
#     }

#     .sidebar .label {
#       font-size: 7px;
#       text-transform: uppercase;
#       letter-spacing: 1px;
#       opacity: 0.62;
#       margin: 0 0 3px;
#     }

#     .sidebar .value {
#       font-size: 9.5px;
#       line-height: 1.35;
#       color: #ffffff;
#       font-weight: 600;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar .muted {
#       font-size: 8px;
#       line-height: 1.35;
#       color: rgba(255, 255, 255, 0.78);
#       margin: 2px 0 0;
#       word-break: break-word;
#     }

#     .sidebar .doc-num {
#       font-size: 21px;
#       line-height: 1.12;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border-radius: 999px;
#       background: rgba(252, 211, 77, 0.14);
#       border: 1px solid rgba(252, 211, 77, 0.32);
#       color: #fcd34d;
#       font-size: 7px;
#       font-weight: 700;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .amount-due {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar-footer {
#       margin-top: 14mm;
#       font-size: 8px;
#       line-height: 1.4;
#       color: rgba(255, 255, 255, 0.58);
#       word-break: break-word;
#     }

#     .main {
#       width: 148mm;
#       height: 297mm;
#       padding: 11mm 10mm 8mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .main-title {
#       margin-bottom: 7mm;
#       padding-bottom: 4mm;
#       border-bottom: 1px solid #e2e8f0;
#     }

#     .main-title p {
#       margin: 0;
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 800;
#       color: #d97706;
#       letter-spacing: -1px;
#     }

#     .main-title span {
#       display: block;
#       margin-top: 4px;
#       font-size: 9px;
#       color: #64748b;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr {
#       background: #fffbeb;
#     }

#     table.items th {
#       padding: 7px 5px;
#       text-align: left;
#       font-size: 7.5px;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#       color: #d97706;
#       border-bottom: 2px solid #d97706;
#     }

#     table.items td {
#       padding: 7px 5px;
#       font-size: 9px;
#       line-height: 1.3;
#       border-bottom: 1px solid #f1f5f9;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) {
#       background: #fffbeb;
#     }

#     .item-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .item-sub {
#       display: block;
#       margin-top: 2px;
#       font-size: 7.8px;
#       color: #94a3b8;
#     }

#     .muted {
#       color: #64748b;
#     }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num {
#       text-align: right;
#     }

#     .empty-items {
#       text-align: center;
#       padding: 14px 6px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-block {
#       margin-left: auto;
#       width: 58mm;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .totals-block table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals-block td {
#       padding: 6px 8px;
#       font-size: 9px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals-block td:first-child {
#       color: #64748b;
#       font-weight: 600;
#     }

#     .totals-block td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #fffbeb;
#       font-size: 13px;
#       font-weight: 800;
#       color: #d97706 !important;
#       border-top: 2px solid #d97706;
#       border-bottom: none;
#       padding-top: 8px;
#       padding-bottom: 8px;
#     }

#     .notes {
#       margin-top: 7mm;
#       padding: 9px 10px;
#       background: #fffbeb;
#       border-left: 4px solid #d97706;
#       border-radius: 6px;
#     }

#     .notes-title {
#       margin: 0;
#       font-size: 8px;
#       color: #92400e;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.8px;
#     }

#     .notes-text {
#       margin: 4px 0 0;
#       font-size: 9px;
#       line-height: 1.45;
#       color: #78350f;
#     }

#     .footer {
#       margin-top: 7mm;
#       padding-top: 4mm;
#       border-top: 1px solid #e2e8f0;
#       font-size: 8px;
#       line-height: 1.45;
#       color: #94a3b8;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="sidebar">
#       <h1>{{ tenant.company_name }}</h1>
#       <p class="sub">Inventory Platform</p>

#       <div class="section">
#         <p class="label">Invoice</p>
#         <p class="doc-num">{{ invoice.invoice_number }}</p>

#         {% if invoice.status %}
#           <span class="status-badge">{{ invoice.status }}</span>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Date</p>
#         <p class="value">{{ invoice.invoice_date }}</p>

#         {% if invoice.due_date %}
#           <p class="label" style="margin-top:5px;">Due Date</p>
#           <p class="value">{{ invoice.due_date }}</p>
#         {% endif %}

#         {% if sales_order %}
#           <p class="label" style="margin-top:5px;">Sales Order</p>
#           <p class="value">{{ sales_order.so_number }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Bill To</p>
#         <p class="value">{{ customer.name }}</p>

#         {% if customer.email %}
#           <p class="muted">{{ customer.email }}</p>
#         {% endif %}

#         {% if customer.phone %}
#           <p class="muted">{{ customer.phone }}</p>
#         {% endif %}

#         {% if customer.billing_address %}
#           <p class="muted">{{ customer.billing_address }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Amount Due</p>
#         <p class="amount-due">
#           {{ currency_symbol | default("₹") }}{{ invoice.total_amount }}
#         </p>
#       </div>

#       <div class="sidebar-footer">
#         {% if tenant.contact_email %}
#           {{ tenant.contact_email }}<br>
#         {% endif %}

#         {% if tenant.phone %}
#           {{ tenant.phone }}<br>
#         {% endif %}

#         {% if tenant.address %}
#           {{ tenant.address }}
#         {% endif %}
#       </div>
#     </div>

#     <div class="main">
#       <div class="main-title">
#         <p>INVOICE</p>
#         <span>Thank you for your business.</span>
#       </div>

#       <table class="items">
#         <thead>
#           <tr>
#             <th style="width:34%;">Item</th>
#             <th style="width:20%;">Warehouse</th>
#             <th class="num" style="width:9%;">Qty</th>
#             <th class="num" style="width:13%;">Rate</th>
#             <th class="num" style="width:10%;">Tax</th>
#             <th class="num" style="width:14%;">Amount</th>
#           </tr>
#         </thead>

#         <tbody>
#           {% if items %}
#             {% for item in items %}
#             <tr>
#               <td>
#                 <span class="item-name">{{ item.product_name }}</span>

#                 {% if item.sku %}
#                   <span class="item-sub">SKU: {{ item.sku }}</span>
#                 {% endif %}
#               </td>

#               <td class="muted">{{ item.warehouse_name }}</td>

#               <td class="num">{{ item.quantity }}</td>

#               <td class="num">
#                 {{ currency_symbol | default("₹") }}{{ item.unit_price }}
#               </td>

#               <td class="num muted">{{ item.tax_rate }}%</td>

#               <td class="num" style="font-weight:700;">
#                 {{ currency_symbol | default("₹") }}{{ item.total_price }}
#               </td>
#             </tr>
#             {% endfor %}
#           {% else %}
#             <tr>
#               <td colspan="6" class="empty-items">No invoice items available.</td>
#             </tr>
#           {% endif %}
#         </tbody>
#       </table>

#       <div class="totals-block">
#         <table>
#           <tr>
#             <td>Subtotal</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
#           </tr>

#           <tr>
#             <td>Tax</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
#           </tr>

#           {% if invoice.discount_amount %}
#           <tr>
#             <td>Discount</td>
#             <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
#           </tr>
#           {% endif %}

#           <tr class="total-row">
#             <td>Total</td>
#             <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
#           </tr>
#         </table>
#       </div>

#       {% if invoice.notes %}
#         <div class="notes">
#           <p class="notes-title">Notes</p>
#           <p class="notes-text">{{ invoice.notes }}</p>
#         </div>
#       {% endif %}

#       <div class="footer">
#         {% if tenant.footer %}
#           {{ tenant.footer }}
#         {% else %}
#           This invoice was generated by {{ tenant.company_name }} using Warelyn.
#         {% endif %}
#       </div>
#     </div>
#   </div>
# </body>
# </html>'''

# _WARM_BILL_PDF = '''<!DOCTYPE html>
# <html>
# <head>
#   <meta charset="utf-8">
#   <title>Bill {{ bill.bill_number }}</title>

#   <style>
#     @page { size: A4; margin: 0; }
#     * { box-sizing: border-box; }

#     html, body {
#       width: 210mm;
#       height: 297mm;
#       margin: 0;
#       padding: 0;
#       overflow: hidden;
#       background: #ffffff;
#       font-family: "Helvetica Neue", Arial, sans-serif;
#       font-size: 10px;
#       color: #1e293b;
#     }

#     .page {
#       width: 210mm;
#       height: 297mm;
#       display: flex;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .sidebar {
#       width: 62mm;
#       height: 297mm;
#       background: #7c2d12;
#       color: #ffffff;
#       padding: 18mm 8mm 8mm;
#       overflow: hidden;
#     }

#     .sidebar h1 {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       letter-spacing: -0.4px;
#       margin: 0 0 4px;
#       color: #ffffff;
#       word-break: break-word;
#     }

#     .sub {
#       font-size: 8px;
#       opacity: 0.72;
#       text-transform: uppercase;
#       letter-spacing: 1.1px;
#       margin: 0 0 18mm;
#     }

#     .section { margin-bottom: 8mm; }

#     .label {
#       font-size: 7px;
#       text-transform: uppercase;
#       letter-spacing: 1px;
#       opacity: 0.62;
#       margin: 0 0 3px;
#     }

#     .value {
#       font-size: 9.5px;
#       line-height: 1.35;
#       color: #ffffff;
#       font-weight: 600;
#       margin: 0;
#       word-break: break-word;
#     }

#     .muted {
#       font-size: 8px;
#       line-height: 1.35;
#       color: rgba(255, 255, 255, 0.78);
#       margin: 2px 0 0;
#       word-break: break-word;
#     }

#     .doc-num {
#       font-size: 21px;
#       line-height: 1.12;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .status-badge {
#       display: inline-block;
#       margin-top: 7px;
#       padding: 3px 8px;
#       border-radius: 999px;
#       background: rgba(252, 211, 77, 0.14);
#       border: 1px solid rgba(252, 211, 77, 0.32);
#       color: #fcd34d;
#       font-size: 7px;
#       font-weight: 700;
#       letter-spacing: 0.8px;
#       text-transform: uppercase;
#     }

#     .amount-due {
#       font-size: 16px;
#       line-height: 1.2;
#       font-weight: 800;
#       color: #fcd34d;
#       margin: 0;
#       word-break: break-word;
#     }

#     .sidebar-footer {
#       margin-top: 14mm;
#       font-size: 8px;
#       line-height: 1.4;
#       color: rgba(255, 255, 255, 0.58);
#       word-break: break-word;
#     }

#     .main {
#       width: 148mm;
#       height: 297mm;
#       padding: 11mm 10mm 8mm;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .main-title {
#       margin-bottom: 7mm;
#       padding-bottom: 4mm;
#       border-bottom: 1px solid #e2e8f0;
#     }

#     .main-title p {
#       margin: 0;
#       font-size: 28px;
#       line-height: 1;
#       font-weight: 800;
#       color: #d97706;
#       letter-spacing: -1px;
#     }

#     .main-title span {
#       display: block;
#       margin-top: 4px;
#       font-size: 9px;
#       color: #64748b;
#     }

#     table.items {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0 0 6mm;
#       table-layout: fixed;
#     }

#     table.items thead tr { background: #fffbeb; }

#     table.items th {
#       padding: 7px 5px;
#       text-align: left;
#       font-size: 7.5px;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.7px;
#       color: #d97706;
#       border-bottom: 2px solid #d97706;
#     }

#     table.items td {
#       padding: 7px 5px;
#       font-size: 9px;
#       line-height: 1.3;
#       border-bottom: 1px solid #f1f5f9;
#       vertical-align: top;
#       word-break: break-word;
#     }

#     table.items tbody tr:nth-child(even) { background: #fffbeb; }

#     .item-name {
#       font-weight: 700;
#       color: #0f172a;
#     }

#     .item-sub {
#       display: block;
#       margin-top: 2px;
#       font-size: 7.8px;
#       color: #94a3b8;
#     }

#     .text-muted { color: #64748b; }

#     .num {
#       text-align: right;
#       white-space: nowrap;
#     }

#     table.items th.num { text-align: right; }

#     .empty-items {
#       text-align: center;
#       padding: 14px 6px !important;
#       color: #94a3b8;
#       font-style: italic;
#     }

#     .totals-block {
#       margin-left: auto;
#       width: 58mm;
#       border: 1px solid #e2e8f0;
#       border-radius: 8px;
#       overflow: hidden;
#       background: #ffffff;
#     }

#     .totals-block table {
#       width: 100%;
#       border-collapse: collapse;
#       margin: 0;
#     }

#     .totals-block td {
#       padding: 6px 8px;
#       font-size: 9px;
#       border-bottom: 1px solid #f1f5f9;
#     }

#     .totals-block td:first-child {
#       color: #64748b;
#       font-weight: 600;
#     }

#     .totals-block td:last-child {
#       text-align: right;
#       font-weight: 700;
#       color: #0f172a;
#       white-space: nowrap;
#     }

#     .total-row td {
#       background: #fffbeb;
#       font-size: 13px;
#       font-weight: 800;
#       color: #d97706 !important;
#       border-top: 2px solid #d97706;
#       border-bottom: none;
#       padding-top: 8px;
#       padding-bottom: 8px;
#     }

#     .notes {
#       margin-top: 7mm;
#       padding: 9px 10px;
#       background: #fffbeb;
#       border-left: 4px solid #d97706;
#       border-radius: 6px;
#     }

#     .notes-title {
#       margin: 0;
#       font-size: 8px;
#       color: #92400e;
#       font-weight: 800;
#       text-transform: uppercase;
#       letter-spacing: 0.8px;
#     }

#     .notes-text {
#       margin: 4px 0 0;
#       font-size: 9px;
#       line-height: 1.45;
#       color: #78350f;
#     }

#     .footer {
#       margin-top: 7mm;
#       padding-top: 4mm;
#       border-top: 1px solid #e2e8f0;
#       font-size: 8px;
#       line-height: 1.45;
#       color: #94a3b8;
#       text-align: center;
#     }
#   </style>
# </head>

# <body>
#   <div class="page">
#     <div class="sidebar">
#       <h1>{{ tenant.company_name }}</h1>
#       <p class="sub">Inventory Platform</p>

#       <div class="section">
#         <p class="label">Bill</p>
#         <p class="doc-num">{{ bill.bill_number }}</p>

#         {% if bill.status %}
#           <span class="status-badge">{{ bill.status }}</span>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Date</p>
#         <p class="value">{{ bill.bill_date }}</p>

#         {% if bill.due_date %}
#           <p class="label" style="margin-top:5px;">Due Date</p>
#           <p class="value">{{ bill.due_date }}</p>
#         {% endif %}

#         {% if purchase_order %}
#           <p class="label" style="margin-top:5px;">Purchase Order</p>
#           <p class="value">{{ purchase_order.po_number }}</p>
#         {% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Vendor</p>
#         <p class="value">{{ vendor.name }}</p>
#         {% if vendor.email %}<p class="muted">{{ vendor.email }}</p>{% endif %}
#         {% if vendor.phone %}<p class="muted">{{ vendor.phone }}</p>{% endif %}
#         {% if vendor.address %}<p class="muted">{{ vendor.address }}</p>{% endif %}
#       </div>

#       <div class="section">
#         <p class="label">Amount Due</p>
#         <p class="amount-due">{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</p>
#       </div>

#       <div class="sidebar-footer">
#         {% if tenant.contact_email %}{{ tenant.contact_email }}<br>{% endif %}
#         {% if tenant.phone %}{{ tenant.phone }}<br>{% endif %}
#         {% if tenant.address %}{{ tenant.address }}{% endif %}
#       </div>
#     </div>

#     <div class="main">
#       <div class="main-title">
#         <p>BILL</p>
#         <span>Vendor bill summary for your purchase records.</span>
#       </div>

#       <table class="items">
#         <thead>
#           <tr>
#             <th style="width:34%;">Item</th>
#             <th style="width:20%;">Warehouse</th>
#             <th class="num" style="width:9%;">Qty</th>
#             <th class="num" style="width:13%;">Rate</th>
#             <th class="num" style="width:10%;">Tax</th>
#             <th class="num" style="width:14%;">Amount</th>
#           </tr>
#         </thead>

#         <tbody>
#           {% if items %}
#             {% for item in items %}
#             <tr>
#               <td>
#                 <span class="item-name">{{ item.product_name }}</span>
#                 {% if item.sku %}<span class="item-sub">SKU: {{ item.sku }}</span>{% endif %}
#               </td>
#               <td class="text-muted">{{ item.warehouse_name }}</td>
#               <td class="num">{{ item.quantity_ordered }}</td>
#               <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
#               <td class="num text-muted">{{ item.tax_rate }}%</td>
#               <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
#             </tr>
#             {% endfor %}
#           {% else %}
#             <tr>
#               <td colspan="6" class="empty-items">No bill items available.</td>
#             </tr>
#           {% endif %}
#         </tbody>
#       </table>

#       <div class="totals-block">
#         <table>
#           <tr><td>Subtotal</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
#           <tr><td>Tax</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
#           <tr class="total-row"><td>Total</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
#         </table>
#       </div>

#       {% if bill.notes %}
#         <div class="notes">
#           <p class="notes-title">Notes</p>
#           <p class="notes-text">{{ bill.notes }}</p>
#         </div>
#       {% endif %}

#       <div class="footer">
#         {% if tenant.footer %}
#           {{ tenant.footer }}
#         {% else %}
#           This bill was generated by {{ tenant.company_name }} using Warelyn.
#         {% endif %}
#       </div>
#     </div>
#   </div>
# </body>
# </html>'''

# DEFAULT_TEMPLATES: dict[tuple[DocumentTemplateChannel, DocumentTemplateKey], dict[str, str | bool | None]] = {
#     (EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION): {
#         "name": "Email verification",
#         "subject_template": "Verify your Warelyn email",
#         "body_template": _OTP_EMAIL_HTML,
#         "body_template_text": _OTP_EMAIL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION_MODERN): {
#         "name": "Verification email — Modern",
#         "subject_template": "Your verification code — {{ purpose }}",
#         "body_template": _OTP_EMAIL_MODERN_HTML,
#         "body_template_text": _OTP_EMAIL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION_MINIMAL): {
#         "name": "Verification email — Minimal",
#         "subject_template": "Your verification code — {{ purpose }}",
#         "body_template": _OTP_EMAIL_MINIMAL_HTML,
#         "body_template_text": _OTP_EMAIL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.INVOICE_SEND): {
#         "name": "Invoice email — Classic",
#         "subject_template": "{{ title }} from {{ sender_name }}",
#         "body_template": _DOC_EMAIL_HTML,
#         "body_template_text": _DOC_EMAIL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.INVOICE_SEND_MODERN): {
#         "name": "Invoice email — Modern",
#         "subject_template": "{{ title }} from {{ sender_name }}",
#         "body_template": _DOC_EMAIL_MODERN_HTML,
#         "body_template_text": _DOC_EMAIL_MODERN_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.INVOICE_SEND_MINIMAL): {
#         "name": "Invoice email — Minimal",
#         "subject_template": "{{ title }} — {{ sender_name }}",
#         "body_template": _DOC_EMAIL_MINIMAL_HTML,
#         "body_template_text": _DOC_EMAIL_MINIMAL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.INVOICE_SEND_FORMAL): {
#         "name": "Invoice email — Formal",
#         "subject_template": "{{ document_kind }} {{ document_number }} from {{ sender_name }}",
#         "body_template": _DOC_EMAIL_FORMAL_HTML,
#         "body_template_text": _DOC_EMAIL_FORMAL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.BILL_SEND): {
#         "name": "Bill email — Classic",
#         "subject_template": "{{ title }} from {{ sender_name }}",
#         "body_template": _DOC_EMAIL_HTML,
#         "body_template_text": _DOC_EMAIL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.BILL_SEND_MODERN): {
#         "name": "Bill email — Modern",
#         "subject_template": "{{ title }} from {{ sender_name }}",
#         "body_template": _DOC_EMAIL_MODERN_HTML,
#         "body_template_text": _DOC_EMAIL_MODERN_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.BILL_SEND_MINIMAL): {
#         "name": "Bill email — Minimal",
#         "subject_template": "{{ title }} — {{ sender_name }}",
#         "body_template": _DOC_EMAIL_MINIMAL_HTML,
#         "body_template_text": _DOC_EMAIL_MINIMAL_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.BILL_SEND_FORMAL): {
#         "name": "Bill email — Formal",
#         "subject_template": "{{ document_kind }} {{ document_number }} from {{ sender_name }}",
#         "body_template": _DOC_EMAIL_FORMAL_HTML,
#         "body_template_text": _DOC_EMAIL_FORMAL_TEXT,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_INVOICE): {
#         "name": "Invoice PDF — Classic",
#         "subject_template": None,
#         "body_template": _CLASSIC_INVOICE_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_INVOICE_MODERN): {
#         "name": "Invoice PDF — Modern",
#         "subject_template": None,
#         "body_template": _MODERN_INVOICE_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_INVOICE_MINIMAL): {
#         "name": "Invoice PDF — Minimal",
#         "subject_template": None,
#         "body_template": _MINIMAL_INVOICE_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_INVOICE_BOLD): {
#         "name": "Invoice PDF — Bold",
#         "subject_template": None,
#         "body_template": _BOLD_INVOICE_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_INVOICE_WARM): {
#         "name": "Invoice PDF — Warm",
#         "subject_template": None,
#         "body_template": _WARM_INVOICE_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_BILL): {
#         "name": "Bill PDF — Classic",
#         "subject_template": None,
#         "body_template": _CLASSIC_BILL_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_BILL_MODERN): {
#         "name": "Bill PDF — Modern",
#         "subject_template": None,
#         "body_template": _MODERN_BILL_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_BILL_MINIMAL): {
#         "name": "Bill PDF — Minimal",
#         "subject_template": None,
#         "body_template": _MINIMAL_BILL_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_BILL_BOLD): {
#         "name": "Bill PDF — Bold",
#         "subject_template": None,
#         "body_template": _BOLD_BILL_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (PDF, DocumentTemplateKey.PDF_BILL_WARM): {
#         "name": "Bill PDF — Warm",
#         "subject_template": None,
#         "body_template": _WARM_BILL_PDF,
#         "body_template_text": None,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.ACCOUNT_CREATED): {
#         "name": "Account created notification",
#         "subject_template": "Welcome to {{ tenant_name }}",
#         "body_template": _ACCOUNT_CREATED_HTML,
#         "body_template_text": _ACCOUNT_CREATED_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.PASSWORD_RESET): {
#         "name": "Password reset notification",
#         "subject_template": "Your password has been reset — {{ tenant_name }}",
#         "body_template": _PASSWORD_RESET_HTML,
#         "body_template_text": _PASSWORD_RESET_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.USER_DISABLED): {
#         "name": "Account disabled notification",
#         "subject_template": "Your account has been disabled — {{ tenant_name }}",
#         "body_template": _USER_DISABLED_HTML,
#         "body_template_text": _USER_DISABLED_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.USER_ENABLED): {
#         "name": "Account enabled notification",
#         "subject_template": "Your account has been re-enabled — {{ tenant_name }}",
#         "body_template": _USER_ENABLED_HTML,
#         "body_template_text": _USER_ENABLED_TEXT,
#         "is_active": True,
#     },
#     (EMAIL, DocumentTemplateKey.ROLE_CHANGED): {
#         "name": "Role changed notification",
#         "subject_template": "Your role has been updated — {{ tenant_name }}",
#         "body_template": _ROLE_CHANGED_HTML,
#         "body_template_text": _ROLE_CHANGED_TEXT,
#         "is_active": True,
#     },
# }
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
<div style="margin:0 0 24px;padding:14px;border:1px solid #DBEAFE;background:#EFF6FF;border-radius:8px;">
<p style="margin:0 0 10px;font-size:14px;font-weight:600;color:#1E3A8A;">First-time sign in instructions</p>
<ol style="margin:0;padding-left:18px;font-size:13px;color:#334155;line-height:1.6;">
<li>Open <a href="{{ login_url }}" style="color:#2563EB;">Sign In</a>.</li>
<li>Click <a href="{{ forgot_password_url|default('/forgot-password') }}" style="color:#2563EB;">Forgot password?</a>.</li>
<li>Use your email to receive a reset code and set your password.</li>
</ol>
</div>
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

First-time sign in instructions:
1. Open Sign In: {{ login_url }}
2. Click Forgot password?: {{ forgot_password_url|default('/forgot-password') }}
3. Use your email to receive a reset code and set your password.

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
    @page {
      size: A4;
      margin: 0;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      background: #ffffff;
      font-family: Arial, sans-serif;
      color: #334155;
      overflow: hidden;
    }

    body {
      font-size: 11px;
    }

    .page {
      width: 210mm;
      height: 297mm;
      padding: 14mm 14mm 12mm;
      overflow: hidden;
      background: #ffffff;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 20px;
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 2px solid #1e3a8a;
    }

    .company {
      max-width: 58%;
      font-size: 11px;
      line-height: 1.45;
      color: #475569;
    }

    .company h1 {
      color: #1e3a8a;
      font-size: 24px;
      line-height: 1.1;
      margin: 0 0 6px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }

    .company p {
      margin: 2px 0;
    }

    .invoice-heading {
      text-align: right;
    }

    .invoice-heading h2 {
      margin: 0;
      color: #1e3a8a;
      font-size: 25px;
      line-height: 1;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .invoice-number {
      margin-top: 6px;
      color: #64748b;
      font-size: 11px;
      font-weight: 600;
    }

    .status-badge {
      display: inline-block;
      margin-top: 8px;
      padding: 4px 9px;
      border-radius: 999px;
      background: #eff6ff;
      color: #1e3a8a;
      border: 1px solid #bfdbfe;
      font-size: 8px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.7px;
    }

    .top-section {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      margin-bottom: 18px;
    }

    .bill-to {
      width: 56%;
      padding: 12px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #f8fafc;
    }

    .bill-to-title {
      margin: 0 0 7px;
      color: #1e3a8a;
      font-size: 9px;
      font-weight: 800;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .customer-name {
      margin: 0;
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.35;
    }

    .customer-detail {
      margin: 3px 0 0;
      font-size: 10px;
      line-height: 1.45;
      color: #64748b;
    }

    .meta-wrap {
      width: 40%;
      padding: 12px;
      border: 1px solid #dbeafe;
      border-radius: 8px;
      background: #eff6ff;
    }

    table.meta {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .meta td {
      padding: 4px 0;
      font-size: 10px;
      line-height: 1.35;
      vertical-align: top;
    }

    .meta td:first-child {
      color: #475569;
      font-weight: 700;
      width: 42%;
    }

    .meta td:last-child {
      color: #0f172a;
      font-weight: 700;
      text-align: right;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0 14px;
      table-layout: fixed;
    }

    table.items th {
      background: #1e3a8a;
      color: #ffffff;
      padding: 8px 7px;
      text-align: left;
      font-size: 8px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }

    table.items td {
      padding: 8px 7px;
      border-bottom: 1px solid #e2e8f0;
      font-size: 10px;
      line-height: 1.35;
      vertical-align: top;
      color: #334155;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) {
      background: #f8fafc;
    }

    .product-name {
      font-weight: 700;
      color: #0f172a;
    }

    .muted {
      color: #64748b;
    }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num {
      text-align: right;
    }

    .empty-items {
      text-align: center;
      padding: 18px 8px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 10px;
    }

    table.totals {
      width: 72mm;
      border-collapse: collapse;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
    }

    .totals td {
      padding: 7px 10px;
      font-size: 10px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals td:first-child {
      color: #475569;
      font-weight: 600;
    }

    .totals td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #1e3a8a;
      color: #ffffff !important;
      font-weight: 800;
      font-size: 13px;
      border-bottom: none;
      padding-top: 9px;
      padding-bottom: 9px;
    }

    .notes {
      margin-top: 18px;
      padding: 10px 12px;
      border-left: 4px solid #1e3a8a;
      background: #f8fafc;
      border-radius: 6px;
      color: #475569;
      font-size: 10px;
      line-height: 1.5;
    }

    .notes strong {
      display: block;
      margin-bottom: 4px;
      color: #1e3a8a;
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 0.7px;
    }

    .footer {
      margin-top: 22px;
      color: #64748b;
      font-size: 9px;
      line-height: 1.45;
      border-top: 1px solid #e2e8f0;
      padding-top: 10px;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="header">
      <div class="company">
        {% if tenant.logo_url %}
          <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
        {% endif %}
        <h1>{{ tenant.company_name }}</h1>

        {% if tenant.contact_email %}
          <p>{{ tenant.contact_email }}</p>
        {% endif %}

        {% if tenant.phone %}
          <p>{{ tenant.phone }}</p>
        {% endif %}

        {% if tenant.address %}
          <p>{{ tenant.address }}</p>
        {% endif %}
      </div>

      <div class="invoice-heading">
        <h2>Invoice</h2>
        <div class="invoice-number">{{ invoice.invoice_number }}</div>

        {% if invoice.status %}
          <div class="status-badge">{{ invoice.status }}</div>
        {% endif %}
      </div>
    </div>

    <div class="top-section">
      <div class="bill-to">
        <p class="bill-to-title">Bill To</p>
        <p class="customer-name">{{ customer.name }}</p>

        {% if customer.email %}
          <p class="customer-detail">{{ customer.email }}</p>
        {% endif %}

        {% if customer.phone %}
          <p class="customer-detail">{{ customer.phone }}</p>
        {% endif %}

        {% if customer.billing_address %}
          <p class="customer-detail">{{ customer.billing_address }}</p>
        {% endif %}
      </div>

      <div class="meta-wrap">
        <table class="meta">
          <tr>
            <td>Date:</td>
            <td>{{ invoice.invoice_date }}</td>
          </tr>

          {% if invoice.due_date %}
          <tr>
            <td>Due:</td>
            <td>{{ invoice.due_date }}</td>
          </tr>
          {% endif %}

          {% if sales_order %}
          <tr>
            <td>SO:</td>
            <td>{{ sales_order.so_number }}</td>
          </tr>
          {% endif %}
        </table>
      </div>
    </div>

    <table class="items">
      <thead>
        <tr>
          <th style="width: 31%;">Product</th>
          <th style="width: 20%;">Warehouse</th>
          <th class="num" style="width: 9%;">Qty</th>
          <th class="num" style="width: 14%;">Unit Price</th>
          <th class="num" style="width: 10%;">Tax %</th>
          <th class="num" style="width: 16%;">Total</th>
        </tr>
      </thead>

      <tbody>
        {% if items %}
          {% for item in items %}
          <tr>
            <td>
              <span class="product-name">{{ item.product_name }}</span>
              {% if item.sku %}
                <br><span class="muted" style="font-size: 8.5px;">SKU: {{ item.sku }}</span>
              {% endif %}
            </td>

            <td class="muted">{{ item.warehouse_name }}</td>

            <td class="num">{{ item.quantity }}</td>

            <td class="num">
              {{ currency_symbol | default("₹") }}{{ item.unit_price }}
            </td>

            <td class="num muted">{{ item.tax_rate }}</td>

            <td class="num" style="font-weight: 700;">
              {{ currency_symbol | default("₹") }}{{ item.total_price }}
            </td>
          </tr>
          {% endfor %}
        {% else %}
          <tr>
            <td colspan="6" class="empty-items">No invoice items available.</td>
          </tr>
        {% endif %}
      </tbody>
    </table>

    <div class="totals-wrapper">
      <table class="totals">
        <tr>
          <td>Subtotal:</td>
          <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
        </tr>

        <tr>
          <td>Tax:</td>
          <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
        </tr>

        {% if invoice.discount_amount %}
        <tr>
          <td>Discount:</td>
          <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
        </tr>
        {% endif %}

        <tr class="total-row">
          <td>Total:</td>
          <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
        </tr>
      </table>
    </div>

    {% if invoice.notes %}
      <div class="notes">
        <strong>Notes</strong>
        <em>{{ invoice.notes }}</em>
      </div>
    {% endif %}

    <div class="footer">
      {% if tenant.footer %}
        {{ tenant.footer }}
      {% else %}
        This invoice was generated by {{ tenant.company_name }} using Warelyn.
      {% endif %}
    </div>
  </div>
</body>
</html>'''

_CLASSIC_BILL_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Bill {{ bill.bill_number }}</title>

  <style>
    @page { size: A4; margin: 0; }

    * { box-sizing: border-box; }

    html, body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      background: #ffffff;
      font-family: Arial, sans-serif;
      color: #334155;
      overflow: hidden;
    }

    body { font-size: 11px; }

    .page {
      width: 210mm;
      height: 297mm;
      padding: 14mm 14mm 12mm;
      overflow: hidden;
      background: #ffffff;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 20px;
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 2px solid #1e3a8a;
    }

    .company {
      max-width: 58%;
      font-size: 11px;
      line-height: 1.45;
      color: #475569;
    }

    .company h1 {
      color: #1e3a8a;
      font-size: 24px;
      line-height: 1.1;
      margin: 0 0 6px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }

    .company p { margin: 2px 0; }

    .bill-heading { text-align: right; }

    .bill-heading h2 {
      margin: 0;
      color: #1e3a8a;
      font-size: 25px;
      line-height: 1;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .bill-number {
      margin-top: 6px;
      color: #64748b;
      font-size: 11px;
      font-weight: 600;
    }

    .status-badge {
      display: inline-block;
      margin-top: 8px;
      padding: 4px 9px;
      border-radius: 999px;
      background: #eff6ff;
      color: #1e3a8a;
      border: 1px solid #bfdbfe;
      font-size: 8px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.7px;
    }

    .top-section {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      margin-bottom: 18px;
    }

    .vendor-box {
      width: 56%;
      padding: 12px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #f8fafc;
    }

    .vendor-title {
      margin: 0 0 7px;
      color: #1e3a8a;
      font-size: 9px;
      font-weight: 800;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .vendor-name {
      margin: 0;
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.35;
    }

    .vendor-detail {
      margin: 3px 0 0;
      font-size: 10px;
      line-height: 1.45;
      color: #64748b;
    }

    .meta-wrap {
      width: 40%;
      padding: 12px;
      border: 1px solid #dbeafe;
      border-radius: 8px;
      background: #eff6ff;
    }

    table.meta {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .meta td {
      padding: 4px 0;
      font-size: 10px;
      line-height: 1.35;
      vertical-align: top;
    }

    .meta td:first-child {
      color: #475569;
      font-weight: 700;
      width: 42%;
    }

    .meta td:last-child {
      color: #0f172a;
      font-weight: 700;
      text-align: right;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0 14px;
      table-layout: fixed;
    }

    table.items th {
      background: #1e3a8a;
      color: #ffffff;
      padding: 8px 7px;
      text-align: left;
      font-size: 8px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }

    table.items td {
      padding: 8px 7px;
      border-bottom: 1px solid #e2e8f0;
      font-size: 10px;
      line-height: 1.35;
      vertical-align: top;
      color: #334155;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) { background: #f8fafc; }

    .product-name {
      font-weight: 700;
      color: #0f172a;
    }

    .muted { color: #64748b; }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num { text-align: right; }

    .empty-items {
      text-align: center;
      padding: 18px 8px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-wrapper {
      display: flex;
      justify-content: flex-end;
      margin-top: 10px;
    }

    table.totals {
      width: 72mm;
      border-collapse: collapse;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
    }

    .totals td {
      padding: 7px 10px;
      font-size: 10px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals td:first-child {
      color: #475569;
      font-weight: 600;
    }

    .totals td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #1e3a8a;
      color: #ffffff !important;
      font-weight: 800;
      font-size: 13px;
      border-bottom: none;
      padding-top: 9px;
      padding-bottom: 9px;
    }

    .notes {
      margin-top: 18px;
      padding: 10px 12px;
      border-left: 4px solid #1e3a8a;
      background: #f8fafc;
      border-radius: 6px;
      color: #475569;
      font-size: 10px;
      line-height: 1.5;
    }

    .notes strong {
      display: block;
      margin-bottom: 4px;
      color: #1e3a8a;
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 0.7px;
    }

    .footer {
      margin-top: 22px;
      color: #64748b;
      font-size: 9px;
      line-height: 1.45;
      border-top: 1px solid #e2e8f0;
      padding-top: 10px;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="header">
      <div class="company">
        {% if tenant.logo_url %}
          <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
        {% endif %}
        <h1>{{ tenant.company_name }}</h1>
        {% if tenant.contact_email %}<p>{{ tenant.contact_email }}</p>{% endif %}
        {% if tenant.phone %}<p>{{ tenant.phone }}</p>{% endif %}
        {% if tenant.address %}<p>{{ tenant.address }}</p>{% endif %}
      </div>

      <div class="bill-heading">
        <h2>Bill</h2>
        <div class="bill-number">{{ bill.bill_number }}</div>
        {% if bill.status %}
          <div class="status-badge">{{ bill.status }}</div>
        {% endif %}
      </div>
    </div>

    <div class="top-section">
      <div class="vendor-box">
        <p class="vendor-title">Vendor</p>
        <p class="vendor-name">{{ vendor.name }}</p>
        {% if vendor.email %}<p class="vendor-detail">{{ vendor.email }}</p>{% endif %}
        {% if vendor.phone %}<p class="vendor-detail">{{ vendor.phone }}</p>{% endif %}
        {% if vendor.address %}<p class="vendor-detail">{{ vendor.address }}</p>{% endif %}
      </div>

      <div class="meta-wrap">
        <table class="meta">
          <tr><td>Date:</td><td>{{ bill.bill_date }}</td></tr>
          {% if bill.due_date %}<tr><td>Due:</td><td>{{ bill.due_date }}</td></tr>{% endif %}
          {% if purchase_order %}<tr><td>PO:</td><td>{{ purchase_order.po_number }}</td></tr>{% endif %}
        </table>
      </div>
    </div>

    <table class="items">
      <thead>
        <tr>
          <th style="width:31%;">Product</th>
          <th style="width:20%;">Warehouse</th>
          <th class="num" style="width:9%;">Qty</th>
          <th class="num" style="width:14%;">Unit Price</th>
          <th class="num" style="width:10%;">Tax %</th>
          <th class="num" style="width:16%;">Total</th>
        </tr>
      </thead>

      <tbody>
        {% if items %}
          {% for item in items %}
          <tr>
            <td>
              <span class="product-name">{{ item.product_name }}</span>
              {% if item.sku %}
                <br><span class="muted" style="font-size:8.5px;">SKU: {{ item.sku }}</span>
              {% endif %}
            </td>
            <td class="muted">{{ item.warehouse_name }}</td>
            <td class="num">{{ item.quantity_ordered }}</td>
            <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
            <td class="num muted">{{ item.tax_rate }}%</td>
            <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
          </tr>
          {% endfor %}
        {% else %}
          <tr>
            <td colspan="6" class="empty-items">No bill items available.</td>
          </tr>
        {% endif %}
      </tbody>
    </table>

    <div class="totals-wrapper">
      <table class="totals">
        <tr><td>Subtotal:</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
        <tr><td>Tax:</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
        <tr class="total-row"><td>Total:</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
      </table>
    </div>

    {% if bill.notes %}
      <div class="notes">
        <strong>Notes</strong>
        <em>{{ bill.notes }}</em>
      </div>
    {% endif %}

    <div class="footer">
      {% if tenant.footer %}
        {{ tenant.footer }}
      {% else %}
        This bill was generated by {{ tenant.company_name }} using Warelyn.
      {% endif %}
    </div>
  </div>
</body>
</html>'''

_MODERN_INVOICE_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Invoice {{ invoice.invoice_number }}</title>

  <style>
    @page {
      size: A4;
      margin: 0;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #ffffff;
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      color: #1e293b;
    }

    .page {
      width: 210mm;
      height: 297mm;
      display: flex;
      overflow: hidden;
      background: #ffffff;
    }

    .sidebar {
      width: 62mm;
      height: 297mm;
      background: #1e3a8a;
      color: #ffffff;
      padding: 18mm 8mm 8mm;
      overflow: hidden;
    }

    .sidebar h1 {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 4px;
      color: #ffffff;
      word-break: break-word;
    }

    .sidebar .sub {
      font-size: 8px;
      opacity: 0.72;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      margin: 0 0 18mm;
    }

    .sidebar .section {
      margin-bottom: 8mm;
    }

    .sidebar .label {
      font-size: 7px;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.62;
      margin: 0 0 3px;
    }

    .sidebar .value {
      font-size: 9.5px;
      line-height: 1.35;
      color: #ffffff;
      font-weight: 600;
      margin: 0;
      word-break: break-word;
    }

    .sidebar .muted {
      font-size: 8px;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.78);
      margin: 2px 0 0;
      word-break: break-word;
    }

    .sidebar .doc-num {
      font-size: 21px;
      line-height: 1.12;
      font-weight: 800;
      color: #93c5fd;
      margin: 0;
      word-break: break-word;
    }

    .status-badge {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(147, 197, 253, 0.15);
      border: 1px solid rgba(147, 197, 253, 0.35);
      color: #bfdbfe;
      font-size: 7px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .amount-due {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      color: #bfdbfe;
      margin: 0;
      word-break: break-word;
    }

    .sidebar-footer {
      margin-top: 14mm;
      font-size: 8px;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.58);
      word-break: break-word;
    }

    .main {
      width: 148mm;
      height: 297mm;
      padding: 11mm 10mm 8mm;
      overflow: hidden;
      background: #ffffff;
    }

    .main-title {
      margin-bottom: 7mm;
      padding-bottom: 4mm;
      border-bottom: 1px solid #e2e8f0;
    }

    .main-title p {
      margin: 0;
      font-size: 28px;
      line-height: 1;
      font-weight: 800;
      color: #1e3a8a;
      letter-spacing: -1px;
    }

    .main-title span {
      display: block;
      margin-top: 4px;
      font-size: 9px;
      color: #64748b;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr {
      background: #eff6ff;
    }

    table.items th {
      padding: 7px 5px;
      text-align: left;
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: #1e3a8a;
      border-bottom: 2px solid #bfdbfe;
    }

    table.items td {
      padding: 7px 5px;
      font-size: 9px;
      line-height: 1.3;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) {
      background: #f8fafc;
    }

    .item-name {
      font-weight: 700;
      color: #0f172a;
    }

    .item-sub {
      display: block;
      margin-top: 2px;
      font-size: 7.8px;
      color: #94a3b8;
    }

    .muted {
      color: #64748b;
    }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num {
      text-align: right;
    }

    .empty-items {
      text-align: center;
      padding: 14px 6px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-block {
      margin-left: auto;
      width: 58mm;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .totals-block table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals-block td {
      padding: 6px 8px;
      font-size: 9px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals-block td:first-child {
      color: #64748b;
      font-weight: 600;
    }

    .totals-block td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #eff6ff;
      font-size: 13px;
      font-weight: 800;
      color: #1e3a8a !important;
      border-top: 2px solid #bfdbfe;
      border-bottom: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    .notes {
      margin-top: 7mm;
      padding: 9px 10px;
      background: #eff6ff;
      border-left: 4px solid #1e3a8a;
      border-radius: 6px;
    }

    .notes-title {
      margin: 0;
      font-size: 8px;
      color: #1e3a8a;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .notes-text {
      margin: 4px 0 0;
      font-size: 9px;
      line-height: 1.45;
      color: #334155;
    }

    .footer {
      margin-top: 7mm;
      padding-top: 4mm;
      border-top: 1px solid #e2e8f0;
      font-size: 8px;
      line-height: 1.45;
      color: #94a3b8;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="sidebar">
      {% if tenant.logo_url %}
        <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
      {% endif %}
      <h1>{{ tenant.company_name }}</h1>
      <p class="sub">Inventory Platform</p>

      <div class="section">
        <p class="label">Invoice</p>
        <p class="doc-num">{{ invoice.invoice_number }}</p>

        {% if invoice.status %}
          <span class="status-badge">{{ invoice.status }}</span>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Date</p>
        <p class="value">{{ invoice.invoice_date }}</p>

        {% if invoice.due_date %}
          <p class="label" style="margin-top:5px;">Due Date</p>
          <p class="value">{{ invoice.due_date }}</p>
        {% endif %}

        {% if sales_order %}
          <p class="label" style="margin-top:5px;">Sales Order</p>
          <p class="value">{{ sales_order.so_number }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Bill To</p>
        <p class="value">{{ customer.name }}</p>

        {% if customer.email %}
          <p class="muted">{{ customer.email }}</p>
        {% endif %}

        {% if customer.phone %}
          <p class="muted">{{ customer.phone }}</p>
        {% endif %}

        {% if customer.billing_address %}
          <p class="muted">{{ customer.billing_address }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Amount Due</p>
        <p class="amount-due">
          {{ currency_symbol | default("₹") }}{{ invoice.total_amount }}
        </p>
      </div>

      <div class="sidebar-footer">
        {% if tenant.contact_email %}
          {{ tenant.contact_email }}<br>
        {% endif %}

        {% if tenant.phone %}
          {{ tenant.phone }}<br>
        {% endif %}

        {% if tenant.address %}
          {{ tenant.address }}
        {% endif %}
      </div>
    </div>

    <div class="main">
      <div class="main-title">
        <p>INVOICE</p>
        <span>Thank you for your business.</span>
      </div>

      <table class="items">
        <thead>
          <tr>
            <th style="width:34%;">Item</th>
            <th style="width:20%;">Warehouse</th>
            <th class="num" style="width:9%;">Qty</th>
            <th class="num" style="width:13%;">Rate</th>
            <th class="num" style="width:10%;">Tax</th>
            <th class="num" style="width:14%;">Amount</th>
          </tr>
        </thead>

        <tbody>
          {% if items %}
            {% for item in items %}
            <tr>
              <td>
                <span class="item-name">{{ item.product_name }}</span>

                {% if item.sku %}
                  <span class="item-sub">SKU: {{ item.sku }}</span>
                {% endif %}
              </td>

              <td class="muted">{{ item.warehouse_name }}</td>

              <td class="num">{{ item.quantity }}</td>

              <td class="num">
                {{ currency_symbol | default("₹") }}{{ item.unit_price }}
              </td>

              <td class="num muted">{{ item.tax_rate }}%</td>

              <td class="num" style="font-weight:700;">
                {{ currency_symbol | default("₹") }}{{ item.total_price }}
              </td>
            </tr>
            {% endfor %}
          {% else %}
            <tr>
              <td colspan="6" class="empty-items">No invoice items available.</td>
            </tr>
          {% endif %}
        </tbody>
      </table>

      <div class="totals-block">
        <table>
          <tr>
            <td>Subtotal</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
          </tr>

          <tr>
            <td>Tax</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
          </tr>

          {% if invoice.discount_amount %}
          <tr>
            <td>Discount</td>
            <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
          </tr>
          {% endif %}

          <tr class="total-row">
            <td>Total</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
          </tr>
        </table>
      </div>

      {% if invoice.notes %}
        <div class="notes">
          <p class="notes-title">Notes</p>
          <p class="notes-text">{{ invoice.notes }}</p>
        </div>
      {% endif %}

      <div class="footer">
        {% if tenant.footer %}
          {{ tenant.footer }}
        {% else %}
          This invoice was generated by {{ tenant.company_name }} using Warelyn.
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>'''

_MODERN_BILL_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Bill {{ bill.bill_number }}</title>

  <style>
    @page { size: A4; margin: 0; }
    * { box-sizing: border-box; }

    html, body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #ffffff;
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      color: #1e293b;
    }

    .page {
      width: 210mm;
      height: 297mm;
      display: flex;
      overflow: hidden;
      background: #ffffff;
    }

    .sidebar {
      width: 62mm;
      height: 297mm;
      background: #1e3a8a;
      color: #ffffff;
      padding: 18mm 8mm 8mm;
      overflow: hidden;
    }

    .sidebar h1 {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 4px;
      color: #ffffff;
      word-break: break-word;
    }

    .sub {
      font-size: 8px;
      opacity: 0.72;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      margin: 0 0 18mm;
    }

    .section { margin-bottom: 8mm; }

    .label {
      font-size: 7px;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.62;
      margin: 0 0 3px;
    }

    .value {
      font-size: 9.5px;
      line-height: 1.35;
      color: #ffffff;
      font-weight: 600;
      margin: 0;
      word-break: break-word;
    }

    .muted {
      font-size: 8px;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.78);
      margin: 2px 0 0;
      word-break: break-word;
    }

    .doc-num {
      font-size: 21px;
      line-height: 1.12;
      font-weight: 800;
      color: #93c5fd;
      margin: 0;
      word-break: break-word;
    }

    .status-badge {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(147, 197, 253, 0.15);
      border: 1px solid rgba(147, 197, 253, 0.35);
      color: #bfdbfe;
      font-size: 7px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .amount-due {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      color: #bfdbfe;
      margin: 0;
      word-break: break-word;
    }

    .sidebar-footer {
      margin-top: 14mm;
      font-size: 8px;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.58);
      word-break: break-word;
    }

    .main {
      width: 148mm;
      height: 297mm;
      padding: 11mm 10mm 8mm;
      overflow: hidden;
      background: #ffffff;
    }

    .main-title {
      margin-bottom: 7mm;
      padding-bottom: 4mm;
      border-bottom: 1px solid #e2e8f0;
    }

    .main-title p {
      margin: 0;
      font-size: 28px;
      line-height: 1;
      font-weight: 800;
      color: #1e3a8a;
      letter-spacing: -1px;
    }

    .main-title span {
      display: block;
      margin-top: 4px;
      font-size: 9px;
      color: #64748b;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr { background: #eff6ff; }

    table.items th {
      padding: 7px 5px;
      text-align: left;
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: #1e3a8a;
      border-bottom: 2px solid #bfdbfe;
    }

    table.items td {
      padding: 7px 5px;
      font-size: 9px;
      line-height: 1.3;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) { background: #f8fafc; }

    .item-name { font-weight: 700; color: #0f172a; }

    .item-sub {
      display: block;
      margin-top: 2px;
      font-size: 7.8px;
      color: #94a3b8;
    }

    .text-muted { color: #64748b; }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num { text-align: right; }

    .empty-items {
      text-align: center;
      padding: 14px 6px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-block {
      margin-left: auto;
      width: 58mm;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .totals-block table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals-block td {
      padding: 6px 8px;
      font-size: 9px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals-block td:first-child {
      color: #64748b;
      font-weight: 600;
    }

    .totals-block td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #eff6ff;
      font-size: 13px;
      font-weight: 800;
      color: #1e3a8a !important;
      border-top: 2px solid #bfdbfe;
      border-bottom: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    .notes {
      margin-top: 7mm;
      padding: 9px 10px;
      background: #eff6ff;
      border-left: 4px solid #1e3a8a;
      border-radius: 6px;
    }

    .notes-title {
      margin: 0;
      font-size: 8px;
      color: #1e3a8a;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .notes-text {
      margin: 4px 0 0;
      font-size: 9px;
      line-height: 1.45;
      color: #334155;
    }

    .footer {
      margin-top: 7mm;
      padding-top: 4mm;
      border-top: 1px solid #e2e8f0;
      font-size: 8px;
      line-height: 1.45;
      color: #94a3b8;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="sidebar">
      {% if tenant.logo_url %}
        <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
      {% endif %}
      <h1>{{ tenant.company_name }}</h1>
      <p class="sub">Inventory Platform</p>

      <div class="section">
        <p class="label">Bill</p>
        <p class="doc-num">{{ bill.bill_number }}</p>
        {% if bill.status %}
          <span class="status-badge">{{ bill.status }}</span>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Date</p>
        <p class="value">{{ bill.bill_date }}</p>

        {% if bill.due_date %}
          <p class="label" style="margin-top:5px;">Due Date</p>
          <p class="value">{{ bill.due_date }}</p>
        {% endif %}

        {% if purchase_order %}
          <p class="label" style="margin-top:5px;">Purchase Order</p>
          <p class="value">{{ purchase_order.po_number }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Vendor</p>
        <p class="value">{{ vendor.name }}</p>
        {% if vendor.email %}<p class="muted">{{ vendor.email }}</p>{% endif %}
        {% if vendor.phone %}<p class="muted">{{ vendor.phone }}</p>{% endif %}
        {% if vendor.address %}<p class="muted">{{ vendor.address }}</p>{% endif %}
      </div>

      <div class="section">
        <p class="label">Amount Due</p>
        <p class="amount-due">{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</p>
      </div>

      <div class="sidebar-footer">
        {% if tenant.contact_email %}{{ tenant.contact_email }}<br>{% endif %}
        {% if tenant.phone %}{{ tenant.phone }}<br>{% endif %}
        {% if tenant.address %}{{ tenant.address }}{% endif %}
      </div>
    </div>

    <div class="main">
      <div class="main-title">
        <p>BILL</p>
        <span>Vendor bill summary for your purchase records.</span>
      </div>

      <table class="items">
        <thead>
          <tr>
            <th style="width:34%;">Item</th>
            <th style="width:20%;">Warehouse</th>
            <th class="num" style="width:9%;">Qty</th>
            <th class="num" style="width:13%;">Rate</th>
            <th class="num" style="width:10%;">Tax</th>
            <th class="num" style="width:14%;">Amount</th>
          </tr>
        </thead>

        <tbody>
          {% if items %}
            {% for item in items %}
            <tr>
              <td>
                <span class="item-name">{{ item.product_name }}</span>
                {% if item.sku %}<span class="item-sub">SKU: {{ item.sku }}</span>{% endif %}
              </td>
              <td class="text-muted">{{ item.warehouse_name }}</td>
              <td class="num">{{ item.quantity_ordered }}</td>
              <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
              <td class="num text-muted">{{ item.tax_rate }}%</td>
              <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
            </tr>
            {% endfor %}
          {% else %}
            <tr>
              <td colspan="6" class="empty-items">No bill items available.</td>
            </tr>
          {% endif %}
        </tbody>
      </table>

      <div class="totals-block">
        <table>
          <tr><td>Subtotal</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
          <tr><td>Tax</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
          <tr class="total-row"><td>Total</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
        </table>
      </div>

      {% if bill.notes %}
        <div class="notes">
          <p class="notes-title">Notes</p>
          <p class="notes-text">{{ bill.notes }}</p>
        </div>
      {% endif %}

      <div class="footer">
        {% if tenant.footer %}
          {{ tenant.footer }}
        {% else %}
          This bill was generated by {{ tenant.company_name }} using Warelyn.
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>'''

_MINIMAL_INVOICE_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Invoice {{ invoice.invoice_number }}</title>

  <style>
    @page {
      size: A4;
      margin: 0;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      background: #ffffff;
      font-family: Georgia, "Times New Roman", serif;
      color: #1e293b;
      overflow: hidden;
    }

    body {
      font-size: 11px;
      line-height: 1.45;
    }

    .page {
      width: 210mm;
      height: 297mm;
      padding: 18mm 16mm 14mm;
      overflow: hidden;
      background: #ffffff;
    }

    .top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16mm;
      margin-bottom: 13mm;
      border-bottom: 0.5px solid #cbd5e1;
      padding-bottom: 7mm;
    }

    .company-block {
      max-width: 95mm;
    }

    .company-name {
      font-size: 24px;
      line-height: 1.1;
      font-weight: bold;
      letter-spacing: -1px;
      color: #0f172a;
      margin: 0;
    }

    .company-detail {
      margin: 4px 0 0;
      font-size: 10px;
      line-height: 1.45;
      color: #94a3b8;
      word-break: break-word;
    }

    .doc-title {
      text-align: right;
      min-width: 55mm;
    }

    .doc-title h2 {
      font-size: 28px;
      line-height: 1;
      font-weight: 300;
      letter-spacing: 4px;
      color: #cbd5e1;
      margin: 0;
      text-transform: uppercase;
    }

    .doc-title .num {
      margin: 7px 0 0;
      font-size: 14px;
      line-height: 1.25;
      font-weight: bold;
      color: #1e3a8a;
      word-break: break-word;
    }

    .doc-title .date {
      margin: 4px 0 0;
      font-size: 10px;
      color: #64748b;
    }

    .status {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border: 0.5px solid #dbeafe;
      border-radius: 999px;
      background: #eff6ff;
      color: #1e3a8a;
      font-size: 7px;
      font-family: Arial, sans-serif;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
    }

    .parties {
      display: flex;
      gap: 16mm;
      margin-bottom: 11mm;
    }

    .party {
      flex: 1;
      min-height: 22mm;
    }

    .party .label {
      font-size: 8px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #94a3b8;
      margin: 0 0 6px;
    }

    .party .name {
      font-size: 13px;
      line-height: 1.35;
      font-weight: bold;
      color: #0f172a;
      margin: 0;
    }

    .party .muted {
      color: #64748b;
      font-size: 10px;
      line-height: 1.45;
      margin: 3px 0 0;
      word-break: break-word;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 8mm 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr th {
      font-size: 8px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #94a3b8;
      padding: 8px 0;
      text-align: left;
      border-bottom: 0.5px solid #e2e8f0;
      font-weight: bold;
    }

    table.items tbody tr td {
      padding: 9px 0;
      border-bottom: 0.5px solid #f1f5f9;
      font-size: 10.5px;
      line-height: 1.35;
      vertical-align: top;
      word-break: break-word;
    }

    .description {
      font-weight: bold;
      color: #0f172a;
    }

    .subtext {
      display: block;
      margin-top: 2px;
      font-size: 8.5px;
      color: #94a3b8;
      font-weight: normal;
    }

    .num-col {
      text-align: right !important;
      white-space: nowrap;
    }

    .muted-col {
      color: #94a3b8;
    }

    .empty-items {
      text-align: center;
      padding: 16px 0 !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals {
      width: 56mm;
      margin-left: auto;
      margin-top: 4mm;
    }

    .totals table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals table td {
      padding: 4px 0;
      font-size: 10.5px;
      border-bottom: none;
    }

    .totals table td:first-child {
      color: #64748b;
    }

    .totals table td:last-child {
      text-align: right;
      color: #0f172a;
      font-weight: bold;
      white-space: nowrap;
    }

    .grand-total td {
      font-size: 16px !important;
      font-weight: bold;
      color: #0f172a !important;
      border-top: 1px solid #1e293b;
      padding-top: 8px !important;
    }

    .notes {
      margin-top: 8mm;
      padding-top: 4mm;
      border-top: 0.5px solid #e2e8f0;
      font-size: 10px;
      line-height: 1.55;
      color: #94a3b8;
    }

    .footer {
      margin-top: 10mm;
      font-size: 9px;
      line-height: 1.5;
      color: #cbd5e1;
      border-top: 0.5px solid #e2e8f0;
      padding-top: 4mm;
    }
  </style>
</head>

<body>
  <div class="page">

    <div class="top">
      <div class="company-block">
        {% if tenant.logo_url %}
          <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
        {% endif %}
        <p class="company-name">{{ tenant.company_name }}</p>

        {% if tenant.contact_email %}
          <p class="company-detail">{{ tenant.contact_email }}</p>
        {% endif %}

        {% if tenant.phone %}
          <p class="company-detail">{{ tenant.phone }}</p>
        {% endif %}

        {% if tenant.address %}
          <p class="company-detail">{{ tenant.address }}</p>
        {% endif %}
      </div>

      <div class="doc-title">
        <h2>Invoice</h2>
        <p class="num">{{ invoice.invoice_number }}</p>
        <p class="date">{{ invoice.invoice_date }}</p>

        {% if invoice.status %}
          <span class="status">{{ invoice.status }}</span>
        {% endif %}
      </div>
    </div>

    <div class="parties">
      <div class="party">
        <p class="label">Bill To</p>
        <p class="name">{{ customer.name }}</p>

        {% if customer.email %}
          <p class="muted">{{ customer.email }}</p>
        {% endif %}

        {% if customer.phone %}
          <p class="muted">{{ customer.phone }}</p>
        {% endif %}

        {% if customer.billing_address %}
          <p class="muted">{{ customer.billing_address }}</p>
        {% endif %}
      </div>

      <div class="party">
        <p class="label">Invoice Details</p>

        {% if invoice.due_date %}
          <p class="name">Due {{ invoice.due_date }}</p>
        {% else %}
          <p class="name">Due on receipt</p>
        {% endif %}

        {% if sales_order %}
          <p class="muted">Sales Order: {{ sales_order.so_number }}</p>
        {% endif %}
      </div>
    </div>

    <table class="items">
      <thead>
        <tr>
          <th style="width: 42%;">Description</th>
          <th class="num-col" style="width: 10%;">Qty</th>
          <th class="num-col" style="width: 16%;">Rate</th>
          <th class="num-col" style="width: 12%;">Tax</th>
          <th class="num-col" style="width: 20%;">Amount</th>
        </tr>
      </thead>

      <tbody>
        {% if items %}
          {% for item in items %}
          <tr>
            <td>
              <span class="description">{{ item.product_name }}</span>

              {% if item.warehouse_name %}
                <span class="subtext">Warehouse: {{ item.warehouse_name }}</span>
              {% endif %}

              {% if item.sku %}
                <span class="subtext">SKU: {{ item.sku }}</span>
              {% endif %}
            </td>

            <td class="num-col">{{ item.quantity }}</td>

            <td class="num-col">
              {{ currency_symbol | default("₹") }}{{ item.unit_price }}
            </td>

            <td class="num-col muted-col">
              {{ item.tax_rate }}%
            </td>

            <td class="num-col">
              {{ currency_symbol | default("₹") }}{{ item.total_price }}
            </td>
          </tr>
          {% endfor %}
        {% else %}
          <tr>
            <td colspan="5" class="empty-items">No invoice items available.</td>
          </tr>
        {% endif %}
      </tbody>
    </table>

    <div class="totals">
      <table>
        <tr>
          <td>Subtotal</td>
          <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
        </tr>

        <tr>
          <td>Tax</td>
          <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
        </tr>

        {% if invoice.discount_amount %}
        <tr>
          <td>Discount</td>
          <td>({{ currency_symbol | default("₹") }}{{ invoice.discount_amount }})</td>
        </tr>
        {% endif %}

        <tr class="grand-total">
          <td>Total</td>
          <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
        </tr>
      </table>
    </div>

    {% if invoice.notes %}
      <p class="notes">
        <em>{{ invoice.notes }}</em>
      </p>
    {% endif %}

    <p class="footer">
      {% if tenant.footer %}
        {{ tenant.footer }}
      {% else %}
        This invoice was generated by {{ tenant.company_name }} using Warelyn.
      {% endif %}
    </p>

  </div>
</body>
</html>'''

_MINIMAL_BILL_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Bill {{ bill.bill_number }}</title>

  <style>
    @page { size: A4; margin: 0; }

    * { box-sizing: border-box; }

    html, body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      background: #ffffff;
      font-family: Georgia, "Times New Roman", serif;
      color: #1e293b;
      overflow: hidden;
    }

    body {
      font-size: 11px;
      line-height: 1.45;
    }

    .page {
      width: 210mm;
      height: 297mm;
      padding: 18mm 16mm 14mm;
      overflow: hidden;
      background: #ffffff;
    }

    .top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16mm;
      margin-bottom: 13mm;
      border-bottom: 0.5px solid #cbd5e1;
      padding-bottom: 7mm;
    }

    .company-block { max-width: 95mm; }

    .company-name {
      font-size: 24px;
      line-height: 1.1;
      font-weight: bold;
      letter-spacing: -1px;
      color: #0f172a;
      margin: 0;
    }

    .company-detail {
      margin: 4px 0 0;
      font-size: 10px;
      line-height: 1.45;
      color: #94a3b8;
      word-break: break-word;
    }

    .doc-title {
      text-align: right;
      min-width: 55mm;
    }

    .doc-title h2 {
      font-size: 28px;
      line-height: 1;
      font-weight: 300;
      letter-spacing: 4px;
      color: #cbd5e1;
      margin: 0;
      text-transform: uppercase;
    }

    .doc-title .num {
      margin: 7px 0 0;
      font-size: 14px;
      line-height: 1.25;
      font-weight: bold;
      color: #1e3a8a;
      word-break: break-word;
    }

    .doc-title .date {
      margin: 4px 0 0;
      font-size: 10px;
      color: #64748b;
    }

    .parties {
      display: flex;
      gap: 16mm;
      margin-bottom: 11mm;
    }

    .party {
      flex: 1;
      min-height: 22mm;
    }

    .party .label {
      font-size: 8px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #94a3b8;
      margin: 0 0 6px;
    }

    .party .name {
      font-size: 13px;
      line-height: 1.35;
      font-weight: bold;
      color: #0f172a;
      margin: 0;
    }

    .party .muted {
      color: #64748b;
      font-size: 10px;
      line-height: 1.45;
      margin: 3px 0 0;
      word-break: break-word;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 8mm 0 6mm;
      table-layout: fixed;
    }

    table.items th {
      font-size: 8px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #94a3b8;
      padding: 8px 0;
      text-align: left;
      border-bottom: 0.5px solid #e2e8f0;
      font-weight: bold;
    }

    table.items td {
      padding: 9px 0;
      border-bottom: 0.5px solid #f1f5f9;
      font-size: 10.5px;
      line-height: 1.35;
      vertical-align: top;
      word-break: break-word;
    }

    .description {
      font-weight: bold;
      color: #0f172a;
    }

    .subtext {
      display: block;
      margin-top: 2px;
      font-size: 8.5px;
      color: #94a3b8;
      font-weight: normal;
    }

    .num-col {
      text-align: right !important;
      white-space: nowrap;
    }

    .muted-col { color: #94a3b8; }

    .empty-items {
      text-align: center;
      padding: 16px 0 !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals {
      width: 56mm;
      margin-left: auto;
      margin-top: 4mm;
    }

    .totals table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals td {
      padding: 4px 0;
      font-size: 10.5px;
    }

    .totals td:first-child { color: #64748b; }

    .totals td:last-child {
      text-align: right;
      color: #0f172a;
      font-weight: bold;
      white-space: nowrap;
    }

    .grand-total td {
      font-size: 16px !important;
      font-weight: bold;
      color: #0f172a !important;
      border-top: 1px solid #1e293b;
      padding-top: 8px !important;
    }

    .notes {
      margin-top: 8mm;
      padding-top: 4mm;
      border-top: 0.5px solid #e2e8f0;
      font-size: 10px;
      line-height: 1.55;
      color: #94a3b8;
    }

    .footer {
      margin-top: 10mm;
      font-size: 9px;
      line-height: 1.5;
      color: #cbd5e1;
      border-top: 0.5px solid #e2e8f0;
      padding-top: 4mm;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="top">
      <div class="company-block">
        {% if tenant.logo_url %}
          <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
        {% endif %}
        <p class="company-name">{{ tenant.company_name }}</p>
        {% if tenant.contact_email %}<p class="company-detail">{{ tenant.contact_email }}</p>{% endif %}
        {% if tenant.phone %}<p class="company-detail">{{ tenant.phone }}</p>{% endif %}
        {% if tenant.address %}<p class="company-detail">{{ tenant.address }}</p>{% endif %}
      </div>

      <div class="doc-title">
        <h2>Bill</h2>
        <p class="num">{{ bill.bill_number }}</p>
        <p class="date">{{ bill.bill_date }}</p>
      </div>
    </div>

    <div class="parties">
      <div class="party">
        <p class="label">Vendor</p>
        <p class="name">{{ vendor.name }}</p>
        {% if vendor.email %}<p class="muted">{{ vendor.email }}</p>{% endif %}
        {% if vendor.phone %}<p class="muted">{{ vendor.phone }}</p>{% endif %}
        {% if vendor.address %}<p class="muted">{{ vendor.address }}</p>{% endif %}
      </div>

      <div class="party">
        <p class="label">Bill Details</p>
        {% if bill.due_date %}
          <p class="name">Due {{ bill.due_date }}</p>
        {% else %}
          <p class="name">Due on receipt</p>
        {% endif %}
        {% if purchase_order %}
          <p class="muted">Purchase Order: {{ purchase_order.po_number }}</p>
        {% endif %}
      </div>
    </div>

    <table class="items">
      <thead>
        <tr>
          <th style="width:42%;">Description</th>
          <th class="num-col" style="width:10%;">Qty</th>
          <th class="num-col" style="width:16%;">Rate</th>
          <th class="num-col" style="width:12%;">Tax</th>
          <th class="num-col" style="width:20%;">Amount</th>
        </tr>
      </thead>

      <tbody>
        {% if items %}
          {% for item in items %}
          <tr>
            <td>
              <span class="description">{{ item.product_name }}</span>
              {% if item.warehouse_name %}
                <span class="subtext">Warehouse: {{ item.warehouse_name }}</span>
              {% endif %}
              {% if item.sku %}
                <span class="subtext">SKU: {{ item.sku }}</span>
              {% endif %}
            </td>
            <td class="num-col">{{ item.quantity_ordered }}</td>
            <td class="num-col">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
            <td class="num-col muted-col">{{ item.tax_rate }}%</td>
            <td class="num-col">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
          </tr>
          {% endfor %}
        {% else %}
          <tr>
            <td colspan="5" class="empty-items">No bill items available.</td>
          </tr>
        {% endif %}
      </tbody>
    </table>

    <div class="totals">
      <table>
        <tr><td>Subtotal</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
        <tr><td>Tax</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
        <tr class="grand-total"><td>Total</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
      </table>
    </div>

    {% if bill.notes %}
      <p class="notes"><em>{{ bill.notes }}</em></p>
    {% endif %}

    <p class="footer">
      {% if tenant.footer %}
        {{ tenant.footer }}
      {% else %}
        This bill was generated by {{ tenant.company_name }} using Warelyn.
      {% endif %}
    </p>
  </div>
</body>
</html>'''

_BOLD_INVOICE_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Invoice {{ invoice.invoice_number }}</title>

  <style>
    @page {
      size: A4;
      margin: 0;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #ffffff;
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      color: #1e293b;
    }

    .page {
      width: 210mm;
      height: 297mm;
      display: flex;
      overflow: hidden;
      background: #ffffff;
    }

    .sidebar {
      width: 62mm;
      height: 297mm;
      background: #0f172a;
      color: #ffffff;
      padding: 18mm 8mm 8mm;
      overflow: hidden;
    }

    .sidebar h1 {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 4px;
      color: #ffffff;
      word-break: break-word;
    }

    .sidebar .sub {
      font-size: 8px;
      opacity: 0.72;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      margin: 0 0 18mm;
    }

    .sidebar .section {
      margin-bottom: 8mm;
    }

    .sidebar .label {
      font-size: 7px;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.62;
      margin: 0 0 3px;
    }

    .sidebar .value {
      font-size: 9.5px;
      line-height: 1.35;
      color: #ffffff;
      font-weight: 600;
      margin: 0;
      word-break: break-word;
    }

    .sidebar .muted {
      font-size: 8px;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.78);
      margin: 2px 0 0;
      word-break: break-word;
    }

    .sidebar .doc-num {
      font-size: 21px;
      line-height: 1.12;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .status-badge {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(252, 211, 77, 0.14);
      border: 1px solid rgba(252, 211, 77, 0.32);
      color: #fcd34d;
      font-size: 7px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .amount-due {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .sidebar-footer {
      margin-top: 14mm;
      font-size: 8px;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.58);
      word-break: break-word;
    }

    .main {
      width: 148mm;
      height: 297mm;
      padding: 11mm 10mm 8mm;
      overflow: hidden;
      background: #ffffff;
    }

    .main-title {
      margin-bottom: 7mm;
      padding-bottom: 4mm;
      border-bottom: 1px solid #e2e8f0;
    }

    .main-title p {
      margin: 0;
      font-size: 28px;
      line-height: 1;
      font-weight: 800;
      color: #f59e0b;
      letter-spacing: -1px;
    }

    .main-title span {
      display: block;
      margin-top: 4px;
      font-size: 9px;
      color: #64748b;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr {
      background: #fffbeb;
    }

    table.items th {
      padding: 7px 5px;
      text-align: left;
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: #f59e0b;
      border-bottom: 2px solid #f59e0b;
    }

    table.items td {
      padding: 7px 5px;
      font-size: 9px;
      line-height: 1.3;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) {
      background: #fffbeb;
    }

    .item-name {
      font-weight: 700;
      color: #0f172a;
    }

    .item-sub {
      display: block;
      margin-top: 2px;
      font-size: 7.8px;
      color: #94a3b8;
    }

    .muted {
      color: #64748b;
    }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num {
      text-align: right;
    }

    .empty-items {
      text-align: center;
      padding: 14px 6px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-block {
      margin-left: auto;
      width: 58mm;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .totals-block table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals-block td {
      padding: 6px 8px;
      font-size: 9px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals-block td:first-child {
      color: #64748b;
      font-weight: 600;
    }

    .totals-block td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #fffbeb;
      font-size: 13px;
      font-weight: 800;
      color: #f59e0b !important;
      border-top: 2px solid #f59e0b;
      border-bottom: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    .notes {
      margin-top: 7mm;
      padding: 9px 10px;
      background: #fffbeb;
      border-left: 4px solid #f59e0b;
      border-radius: 6px;
    }

    .notes-title {
      margin: 0;
      font-size: 8px;
      color: #92400e;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .notes-text {
      margin: 4px 0 0;
      font-size: 9px;
      line-height: 1.45;
      color: #78350f;
    }

    .footer {
      margin-top: 7mm;
      padding-top: 4mm;
      border-top: 1px solid #e2e8f0;
      font-size: 8px;
      line-height: 1.45;
      color: #94a3b8;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="sidebar">
      {% if tenant.logo_url %}
        <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
      {% endif %}
      <h1>{{ tenant.company_name }}</h1>
      <p class="sub">Inventory Platform</p>

      <div class="section">
        <p class="label">Invoice</p>
        <p class="doc-num">{{ invoice.invoice_number }}</p>

        {% if invoice.status %}
          <span class="status-badge">{{ invoice.status }}</span>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Date</p>
        <p class="value">{{ invoice.invoice_date }}</p>

        {% if invoice.due_date %}
          <p class="label" style="margin-top:5px;">Due Date</p>
          <p class="value">{{ invoice.due_date }}</p>
        {% endif %}

        {% if sales_order %}
          <p class="label" style="margin-top:5px;">Sales Order</p>
          <p class="value">{{ sales_order.so_number }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Bill To</p>
        <p class="value">{{ customer.name }}</p>

        {% if customer.email %}
          <p class="muted">{{ customer.email }}</p>
        {% endif %}

        {% if customer.phone %}
          <p class="muted">{{ customer.phone }}</p>
        {% endif %}

        {% if customer.billing_address %}
          <p class="muted">{{ customer.billing_address }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Amount Due</p>
        <p class="amount-due">
          {{ currency_symbol | default("₹") }}{{ invoice.total_amount }}
        </p>
      </div>

      <div class="sidebar-footer">
        {% if tenant.contact_email %}
          {{ tenant.contact_email }}<br>
        {% endif %}

        {% if tenant.phone %}
          {{ tenant.phone }}<br>
        {% endif %}

        {% if tenant.address %}
          {{ tenant.address }}
        {% endif %}
      </div>
    </div>

    <div class="main">
      <div class="main-title">
        <p>INVOICE</p>
        <span>Thank you for your business.</span>
      </div>

      <table class="items">
        <thead>
          <tr>
            <th style="width:34%;">Item</th>
            <th style="width:20%;">Warehouse</th>
            <th class="num" style="width:9%;">Qty</th>
            <th class="num" style="width:13%;">Rate</th>
            <th class="num" style="width:10%;">Tax</th>
            <th class="num" style="width:14%;">Amount</th>
          </tr>
        </thead>

        <tbody>
          {% if items %}
            {% for item in items %}
            <tr>
              <td>
                <span class="item-name">{{ item.product_name }}</span>

                {% if item.sku %}
                  <span class="item-sub">SKU: {{ item.sku }}</span>
                {% endif %}
              </td>

              <td class="muted">{{ item.warehouse_name }}</td>

              <td class="num">{{ item.quantity }}</td>

              <td class="num">
                {{ currency_symbol | default("₹") }}{{ item.unit_price }}
              </td>

              <td class="num muted">{{ item.tax_rate }}%</td>

              <td class="num" style="font-weight:700;">
                {{ currency_symbol | default("₹") }}{{ item.total_price }}
              </td>
            </tr>
            {% endfor %}
          {% else %}
            <tr>
              <td colspan="6" class="empty-items">No invoice items available.</td>
            </tr>
          {% endif %}
        </tbody>
      </table>

      <div class="totals-block">
        <table>
          <tr>
            <td>Subtotal</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
          </tr>

          <tr>
            <td>Tax</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
          </tr>

          {% if invoice.discount_amount %}
          <tr>
            <td>Discount</td>
            <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
          </tr>
          {% endif %}

          <tr class="total-row">
            <td>Total</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
          </tr>
        </table>
      </div>

      {% if invoice.notes %}
        <div class="notes">
          <p class="notes-title">Notes</p>
          <p class="notes-text">{{ invoice.notes }}</p>
        </div>
      {% endif %}

      <div class="footer">
        {% if tenant.footer %}
          {{ tenant.footer }}
        {% else %}
          This invoice was generated by {{ tenant.company_name }} using Warelyn.
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>'''

_BOLD_BILL_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Bill {{ bill.bill_number }}</title>

  <style>
    @page { size: A4; margin: 0; }

    * { box-sizing: border-box; }

    html, body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #ffffff;
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      color: #1e293b;
    }

    .page {
      width: 210mm;
      height: 297mm;
      display: flex;
      overflow: hidden;
      background: #ffffff;
    }

    .sidebar {
      width: 62mm;
      height: 297mm;
      background: #0f172a;
      color: #ffffff;
      padding: 18mm 8mm 8mm;
      overflow: hidden;
    }

    .sidebar h1 {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 4px;
      color: #ffffff;
      word-break: break-word;
    }

    .sidebar .sub {
      font-size: 8px;
      opacity: 0.72;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      margin: 0 0 18mm;
    }

    .section { margin-bottom: 8mm; }

    .label {
      font-size: 7px;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.62;
      margin: 0 0 3px;
    }

    .value {
      font-size: 9.5px;
      line-height: 1.35;
      color: #ffffff;
      font-weight: 600;
      margin: 0;
      word-break: break-word;
    }

    .muted {
      font-size: 8px;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.78);
      margin: 2px 0 0;
      word-break: break-word;
    }

    .doc-num {
      font-size: 21px;
      line-height: 1.12;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .status-badge {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(252, 211, 77, 0.14);
      border: 1px solid rgba(252, 211, 77, 0.32);
      color: #fcd34d;
      font-size: 7px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .amount-due {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .sidebar-footer {
      margin-top: 14mm;
      font-size: 8px;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.58);
      word-break: break-word;
    }

    .main {
      width: 148mm;
      height: 297mm;
      padding: 11mm 10mm 8mm;
      overflow: hidden;
      background: #ffffff;
    }

    .main-title {
      margin-bottom: 7mm;
      padding-bottom: 4mm;
      border-bottom: 1px solid #e2e8f0;
    }

    .main-title p {
      margin: 0;
      font-size: 28px;
      line-height: 1;
      font-weight: 800;
      color: #f59e0b;
      letter-spacing: -1px;
    }

    .main-title span {
      display: block;
      margin-top: 4px;
      font-size: 9px;
      color: #64748b;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr { background: #fffbeb; }

    table.items th {
      padding: 7px 5px;
      text-align: left;
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: #f59e0b;
      border-bottom: 2px solid #f59e0b;
    }

    table.items td {
      padding: 7px 5px;
      font-size: 9px;
      line-height: 1.3;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) { background: #fffbeb; }

    .item-name {
      font-weight: 700;
      color: #0f172a;
    }

    .item-sub {
      display: block;
      margin-top: 2px;
      font-size: 7.8px;
      color: #94a3b8;
    }

    .text-muted { color: #64748b; }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num { text-align: right; }

    .empty-items {
      text-align: center;
      padding: 14px 6px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-block {
      margin-left: auto;
      width: 58mm;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .totals-block table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals-block td {
      padding: 6px 8px;
      font-size: 9px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals-block td:first-child {
      color: #64748b;
      font-weight: 600;
    }

    .totals-block td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #fffbeb;
      font-size: 13px;
      font-weight: 800;
      color: #f59e0b !important;
      border-top: 2px solid #f59e0b;
      border-bottom: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    .notes {
      margin-top: 7mm;
      padding: 9px 10px;
      background: #fffbeb;
      border-left: 4px solid #f59e0b;
      border-radius: 6px;
    }

    .notes-title {
      margin: 0;
      font-size: 8px;
      color: #92400e;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .notes-text {
      margin: 4px 0 0;
      font-size: 9px;
      line-height: 1.45;
      color: #78350f;
    }

    .footer {
      margin-top: 7mm;
      padding-top: 4mm;
      border-top: 1px solid #e2e8f0;
      font-size: 8px;
      line-height: 1.45;
      color: #94a3b8;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="sidebar">
      {% if tenant.logo_url %}
        <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
      {% endif %}
      <h1>{{ tenant.company_name }}</h1>
      <p class="sub">Inventory Platform</p>

      <div class="section">
        <p class="label">Bill</p>
        <p class="doc-num">{{ bill.bill_number }}</p>

        {% if bill.status %}
          <span class="status-badge">{{ bill.status }}</span>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Date</p>
        <p class="value">{{ bill.bill_date }}</p>

        {% if bill.due_date %}
          <p class="label" style="margin-top:5px;">Due Date</p>
          <p class="value">{{ bill.due_date }}</p>
        {% endif %}

        {% if purchase_order %}
          <p class="label" style="margin-top:5px;">Purchase Order</p>
          <p class="value">{{ purchase_order.po_number }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Vendor</p>
        <p class="value">{{ vendor.name }}</p>

        {% if vendor.email %}
          <p class="muted">{{ vendor.email }}</p>
        {% endif %}

        {% if vendor.phone %}
          <p class="muted">{{ vendor.phone }}</p>
        {% endif %}

        {% if vendor.address %}
          <p class="muted">{{ vendor.address }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Amount Due</p>
        <p class="amount-due">{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</p>
      </div>

      <div class="sidebar-footer">
        {% if tenant.contact_email %}{{ tenant.contact_email }}<br>{% endif %}
        {% if tenant.phone %}{{ tenant.phone }}<br>{% endif %}
        {% if tenant.address %}{{ tenant.address }}{% endif %}
      </div>
    </div>

    <div class="main">
      <div class="main-title">
        <p>BILL</p>
        <span>Vendor bill summary for your purchase records.</span>
      </div>

      <table class="items">
        <thead>
          <tr>
            <th style="width:34%;">Item</th>
            <th style="width:20%;">Warehouse</th>
            <th class="num" style="width:9%;">Qty</th>
            <th class="num" style="width:13%;">Rate</th>
            <th class="num" style="width:10%;">Tax</th>
            <th class="num" style="width:14%;">Amount</th>
          </tr>
        </thead>

        <tbody>
          {% if items %}
            {% for item in items %}
            <tr>
              <td>
                <span class="item-name">{{ item.product_name }}</span>
                {% if item.sku %}
                  <span class="item-sub">SKU: {{ item.sku }}</span>
                {% endif %}
              </td>
              <td class="text-muted">{{ item.warehouse_name }}</td>
              <td class="num">{{ item.quantity_ordered }}</td>
              <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
              <td class="num text-muted">{{ item.tax_rate }}%</td>
              <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
            </tr>
            {% endfor %}
          {% else %}
            <tr>
              <td colspan="6" class="empty-items">No bill items available.</td>
            </tr>
          {% endif %}
        </tbody>
      </table>

      <div class="totals-block">
        <table>
          <tr>
            <td>Subtotal</td>
            <td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td>
          </tr>
          <tr>
            <td>Tax</td>
            <td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td>
          </tr>
          <tr class="total-row">
            <td>Total</td>
            <td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td>
          </tr>
        </table>
      </div>

      {% if bill.notes %}
        <div class="notes">
          <p class="notes-title">Notes</p>
          <p class="notes-text">{{ bill.notes }}</p>
        </div>
      {% endif %}

      <div class="footer">
        {% if tenant.footer %}
          {{ tenant.footer }}
        {% else %}
          This bill was generated by {{ tenant.company_name }} using Warelyn.
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>'''

_WARM_INVOICE_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Invoice {{ invoice.invoice_number }}</title>

  <style>
    @page {
      size: A4;
      margin: 0;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #ffffff;
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      color: #1e293b;
    }

    .page {
      width: 210mm;
      height: 297mm;
      display: flex;
      overflow: hidden;
      background: #ffffff;
    }

    .sidebar {
      width: 62mm;
      height: 297mm;
      background: #7c2d12;
      color: #ffffff;
      padding: 18mm 8mm 8mm;
      overflow: hidden;
    }

    .sidebar h1 {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 4px;
      color: #ffffff;
      word-break: break-word;
    }

    .sidebar .sub {
      font-size: 8px;
      opacity: 0.72;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      margin: 0 0 18mm;
    }

    .sidebar .section {
      margin-bottom: 8mm;
    }

    .sidebar .label {
      font-size: 7px;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.62;
      margin: 0 0 3px;
    }

    .sidebar .value {
      font-size: 9.5px;
      line-height: 1.35;
      color: #ffffff;
      font-weight: 600;
      margin: 0;
      word-break: break-word;
    }

    .sidebar .muted {
      font-size: 8px;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.78);
      margin: 2px 0 0;
      word-break: break-word;
    }

    .sidebar .doc-num {
      font-size: 21px;
      line-height: 1.12;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .status-badge {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(252, 211, 77, 0.14);
      border: 1px solid rgba(252, 211, 77, 0.32);
      color: #fcd34d;
      font-size: 7px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .amount-due {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .sidebar-footer {
      margin-top: 14mm;
      font-size: 8px;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.58);
      word-break: break-word;
    }

    .main {
      width: 148mm;
      height: 297mm;
      padding: 11mm 10mm 8mm;
      overflow: hidden;
      background: #ffffff;
    }

    .main-title {
      margin-bottom: 7mm;
      padding-bottom: 4mm;
      border-bottom: 1px solid #e2e8f0;
    }

    .main-title p {
      margin: 0;
      font-size: 28px;
      line-height: 1;
      font-weight: 800;
      color: #d97706;
      letter-spacing: -1px;
    }

    .main-title span {
      display: block;
      margin-top: 4px;
      font-size: 9px;
      color: #64748b;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr {
      background: #fffbeb;
    }

    table.items th {
      padding: 7px 5px;
      text-align: left;
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: #d97706;
      border-bottom: 2px solid #d97706;
    }

    table.items td {
      padding: 7px 5px;
      font-size: 9px;
      line-height: 1.3;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) {
      background: #fffbeb;
    }

    .item-name {
      font-weight: 700;
      color: #0f172a;
    }

    .item-sub {
      display: block;
      margin-top: 2px;
      font-size: 7.8px;
      color: #94a3b8;
    }

    .muted {
      color: #64748b;
    }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num {
      text-align: right;
    }

    .empty-items {
      text-align: center;
      padding: 14px 6px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-block {
      margin-left: auto;
      width: 58mm;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .totals-block table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals-block td {
      padding: 6px 8px;
      font-size: 9px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals-block td:first-child {
      color: #64748b;
      font-weight: 600;
    }

    .totals-block td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #fffbeb;
      font-size: 13px;
      font-weight: 800;
      color: #d97706 !important;
      border-top: 2px solid #d97706;
      border-bottom: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    .notes {
      margin-top: 7mm;
      padding: 9px 10px;
      background: #fffbeb;
      border-left: 4px solid #d97706;
      border-radius: 6px;
    }

    .notes-title {
      margin: 0;
      font-size: 8px;
      color: #92400e;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .notes-text {
      margin: 4px 0 0;
      font-size: 9px;
      line-height: 1.45;
      color: #78350f;
    }

    .footer {
      margin-top: 7mm;
      padding-top: 4mm;
      border-top: 1px solid #e2e8f0;
      font-size: 8px;
      line-height: 1.45;
      color: #94a3b8;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="sidebar">
      {% if tenant.logo_url %}
        <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
      {% endif %}
      <h1>{{ tenant.company_name }}</h1>
      <p class="sub">Inventory Platform</p>

      <div class="section">
        <p class="label">Invoice</p>
        <p class="doc-num">{{ invoice.invoice_number }}</p>

        {% if invoice.status %}
          <span class="status-badge">{{ invoice.status }}</span>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Date</p>
        <p class="value">{{ invoice.invoice_date }}</p>

        {% if invoice.due_date %}
          <p class="label" style="margin-top:5px;">Due Date</p>
          <p class="value">{{ invoice.due_date }}</p>
        {% endif %}

        {% if sales_order %}
          <p class="label" style="margin-top:5px;">Sales Order</p>
          <p class="value">{{ sales_order.so_number }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Bill To</p>
        <p class="value">{{ customer.name }}</p>

        {% if customer.email %}
          <p class="muted">{{ customer.email }}</p>
        {% endif %}

        {% if customer.phone %}
          <p class="muted">{{ customer.phone }}</p>
        {% endif %}

        {% if customer.billing_address %}
          <p class="muted">{{ customer.billing_address }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Amount Due</p>
        <p class="amount-due">
          {{ currency_symbol | default("₹") }}{{ invoice.total_amount }}
        </p>
      </div>

      <div class="sidebar-footer">
        {% if tenant.contact_email %}
          {{ tenant.contact_email }}<br>
        {% endif %}

        {% if tenant.phone %}
          {{ tenant.phone }}<br>
        {% endif %}

        {% if tenant.address %}
          {{ tenant.address }}
        {% endif %}
      </div>
    </div>

    <div class="main">
      <div class="main-title">
        <p>INVOICE</p>
        <span>Thank you for your business.</span>
      </div>

      <table class="items">
        <thead>
          <tr>
            <th style="width:34%;">Item</th>
            <th style="width:20%;">Warehouse</th>
            <th class="num" style="width:9%;">Qty</th>
            <th class="num" style="width:13%;">Rate</th>
            <th class="num" style="width:10%;">Tax</th>
            <th class="num" style="width:14%;">Amount</th>
          </tr>
        </thead>

        <tbody>
          {% if items %}
            {% for item in items %}
            <tr>
              <td>
                <span class="item-name">{{ item.product_name }}</span>

                {% if item.sku %}
                  <span class="item-sub">SKU: {{ item.sku }}</span>
                {% endif %}
              </td>

              <td class="muted">{{ item.warehouse_name }}</td>

              <td class="num">{{ item.quantity }}</td>

              <td class="num">
                {{ currency_symbol | default("₹") }}{{ item.unit_price }}
              </td>

              <td class="num muted">{{ item.tax_rate }}%</td>

              <td class="num" style="font-weight:700;">
                {{ currency_symbol | default("₹") }}{{ item.total_price }}
              </td>
            </tr>
            {% endfor %}
          {% else %}
            <tr>
              <td colspan="6" class="empty-items">No invoice items available.</td>
            </tr>
          {% endif %}
        </tbody>
      </table>

      <div class="totals-block">
        <table>
          <tr>
            <td>Subtotal</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.subtotal }}</td>
          </tr>

          <tr>
            <td>Tax</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.tax_amount }}</td>
          </tr>

          {% if invoice.discount_amount %}
          <tr>
            <td>Discount</td>
            <td>-{{ currency_symbol | default("₹") }}{{ invoice.discount_amount }}</td>
          </tr>
          {% endif %}

          <tr class="total-row">
            <td>Total</td>
            <td>{{ currency_symbol | default("₹") }}{{ invoice.total_amount }}</td>
          </tr>
        </table>
      </div>

      {% if invoice.notes %}
        <div class="notes">
          <p class="notes-title">Notes</p>
          <p class="notes-text">{{ invoice.notes }}</p>
        </div>
      {% endif %}

      <div class="footer">
        {% if tenant.footer %}
          {{ tenant.footer }}
        {% else %}
          This invoice was generated by {{ tenant.company_name }} using Warelyn.
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>'''

_WARM_BILL_PDF = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Bill {{ bill.bill_number }}</title>

  <style>
    @page { size: A4; margin: 0; }
    * { box-sizing: border-box; }

    html, body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #ffffff;
      font-family: "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      color: #1e293b;
    }

    .page {
      width: 210mm;
      height: 297mm;
      display: flex;
      overflow: hidden;
      background: #ffffff;
    }

    .sidebar {
      width: 62mm;
      height: 297mm;
      background: #7c2d12;
      color: #ffffff;
      padding: 18mm 8mm 8mm;
      overflow: hidden;
    }

    .sidebar h1 {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      letter-spacing: -0.4px;
      margin: 0 0 4px;
      color: #ffffff;
      word-break: break-word;
    }

    .sub {
      font-size: 8px;
      opacity: 0.72;
      text-transform: uppercase;
      letter-spacing: 1.1px;
      margin: 0 0 18mm;
    }

    .section { margin-bottom: 8mm; }

    .label {
      font-size: 7px;
      text-transform: uppercase;
      letter-spacing: 1px;
      opacity: 0.62;
      margin: 0 0 3px;
    }

    .value {
      font-size: 9.5px;
      line-height: 1.35;
      color: #ffffff;
      font-weight: 600;
      margin: 0;
      word-break: break-word;
    }

    .muted {
      font-size: 8px;
      line-height: 1.35;
      color: rgba(255, 255, 255, 0.78);
      margin: 2px 0 0;
      word-break: break-word;
    }

    .doc-num {
      font-size: 21px;
      line-height: 1.12;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .status-badge {
      display: inline-block;
      margin-top: 7px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(252, 211, 77, 0.14);
      border: 1px solid rgba(252, 211, 77, 0.32);
      color: #fcd34d;
      font-size: 7px;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }

    .amount-due {
      font-size: 16px;
      line-height: 1.2;
      font-weight: 800;
      color: #fcd34d;
      margin: 0;
      word-break: break-word;
    }

    .sidebar-footer {
      margin-top: 14mm;
      font-size: 8px;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.58);
      word-break: break-word;
    }

    .main {
      width: 148mm;
      height: 297mm;
      padding: 11mm 10mm 8mm;
      overflow: hidden;
      background: #ffffff;
    }

    .main-title {
      margin-bottom: 7mm;
      padding-bottom: 4mm;
      border-bottom: 1px solid #e2e8f0;
    }

    .main-title p {
      margin: 0;
      font-size: 28px;
      line-height: 1;
      font-weight: 800;
      color: #d97706;
      letter-spacing: -1px;
    }

    .main-title span {
      display: block;
      margin-top: 4px;
      font-size: 9px;
      color: #64748b;
    }

    table.items {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 6mm;
      table-layout: fixed;
    }

    table.items thead tr { background: #fffbeb; }

    table.items th {
      padding: 7px 5px;
      text-align: left;
      font-size: 7.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: #d97706;
      border-bottom: 2px solid #d97706;
    }

    table.items td {
      padding: 7px 5px;
      font-size: 9px;
      line-height: 1.3;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: top;
      word-break: break-word;
    }

    table.items tbody tr:nth-child(even) { background: #fffbeb; }

    .item-name {
      font-weight: 700;
      color: #0f172a;
    }

    .item-sub {
      display: block;
      margin-top: 2px;
      font-size: 7.8px;
      color: #94a3b8;
    }

    .text-muted { color: #64748b; }

    .num {
      text-align: right;
      white-space: nowrap;
    }

    table.items th.num { text-align: right; }

    .empty-items {
      text-align: center;
      padding: 14px 6px !important;
      color: #94a3b8;
      font-style: italic;
    }

    .totals-block {
      margin-left: auto;
      width: 58mm;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: #ffffff;
    }

    .totals-block table {
      width: 100%;
      border-collapse: collapse;
      margin: 0;
    }

    .totals-block td {
      padding: 6px 8px;
      font-size: 9px;
      border-bottom: 1px solid #f1f5f9;
    }

    .totals-block td:first-child {
      color: #64748b;
      font-weight: 600;
    }

    .totals-block td:last-child {
      text-align: right;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
    }

    .total-row td {
      background: #fffbeb;
      font-size: 13px;
      font-weight: 800;
      color: #d97706 !important;
      border-top: 2px solid #d97706;
      border-bottom: none;
      padding-top: 8px;
      padding-bottom: 8px;
    }

    .notes {
      margin-top: 7mm;
      padding: 9px 10px;
      background: #fffbeb;
      border-left: 4px solid #d97706;
      border-radius: 6px;
    }

    .notes-title {
      margin: 0;
      font-size: 8px;
      color: #92400e;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .notes-text {
      margin: 4px 0 0;
      font-size: 9px;
      line-height: 1.45;
      color: #78350f;
    }

    .footer {
      margin-top: 7mm;
      padding-top: 4mm;
      border-top: 1px solid #e2e8f0;
      font-size: 8px;
      line-height: 1.45;
      color: #94a3b8;
      text-align: center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="sidebar">
      {% if tenant.logo_url %}
        <img src="{{tenant.logo_url}}" alt="{{ tenant.company_name }} logo" style="max-height: 42px; max-width: 150px; object-fit: contain; margin: 0 0 8px;">
      {% endif %}
      <h1>{{ tenant.company_name }}</h1>
      <p class="sub">Inventory Platform</p>

      <div class="section">
        <p class="label">Bill</p>
        <p class="doc-num">{{ bill.bill_number }}</p>

        {% if bill.status %}
          <span class="status-badge">{{ bill.status }}</span>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Date</p>
        <p class="value">{{ bill.bill_date }}</p>

        {% if bill.due_date %}
          <p class="label" style="margin-top:5px;">Due Date</p>
          <p class="value">{{ bill.due_date }}</p>
        {% endif %}

        {% if purchase_order %}
          <p class="label" style="margin-top:5px;">Purchase Order</p>
          <p class="value">{{ purchase_order.po_number }}</p>
        {% endif %}
      </div>

      <div class="section">
        <p class="label">Vendor</p>
        <p class="value">{{ vendor.name }}</p>
        {% if vendor.email %}<p class="muted">{{ vendor.email }}</p>{% endif %}
        {% if vendor.phone %}<p class="muted">{{ vendor.phone }}</p>{% endif %}
        {% if vendor.address %}<p class="muted">{{ vendor.address }}</p>{% endif %}
      </div>

      <div class="section">
        <p class="label">Amount Due</p>
        <p class="amount-due">{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</p>
      </div>

      <div class="sidebar-footer">
        {% if tenant.contact_email %}{{ tenant.contact_email }}<br>{% endif %}
        {% if tenant.phone %}{{ tenant.phone }}<br>{% endif %}
        {% if tenant.address %}{{ tenant.address }}{% endif %}
      </div>
    </div>

    <div class="main">
      <div class="main-title">
        <p>BILL</p>
        <span>Vendor bill summary for your purchase records.</span>
      </div>

      <table class="items">
        <thead>
          <tr>
            <th style="width:34%;">Item</th>
            <th style="width:20%;">Warehouse</th>
            <th class="num" style="width:9%;">Qty</th>
            <th class="num" style="width:13%;">Rate</th>
            <th class="num" style="width:10%;">Tax</th>
            <th class="num" style="width:14%;">Amount</th>
          </tr>
        </thead>

        <tbody>
          {% if items %}
            {% for item in items %}
            <tr>
              <td>
                <span class="item-name">{{ item.product_name }}</span>
                {% if item.sku %}<span class="item-sub">SKU: {{ item.sku }}</span>{% endif %}
              </td>
              <td class="text-muted">{{ item.warehouse_name }}</td>
              <td class="num">{{ item.quantity_ordered }}</td>
              <td class="num">{{ currency_symbol | default("₹") }}{{ item.unit_price }}</td>
              <td class="num text-muted">{{ item.tax_rate }}%</td>
              <td class="num" style="font-weight:700;">{{ currency_symbol | default("₹") }}{{ item.total_price }}</td>
            </tr>
            {% endfor %}
          {% else %}
            <tr>
              <td colspan="6" class="empty-items">No bill items available.</td>
            </tr>
          {% endif %}
        </tbody>
      </table>

      <div class="totals-block">
        <table>
          <tr><td>Subtotal</td><td>{{ currency_symbol | default("₹") }}{{ bill.subtotal }}</td></tr>
          <tr><td>Tax</td><td>{{ currency_symbol | default("₹") }}{{ bill.tax_amount }}</td></tr>
          <tr class="total-row"><td>Total</td><td>{{ currency_symbol | default("₹") }}{{ bill.total_amount }}</td></tr>
        </table>
      </div>

      {% if bill.notes %}
        <div class="notes">
          <p class="notes-title">Notes</p>
          <p class="notes-text">{{ bill.notes }}</p>
        </div>
      {% endif %}

      <div class="footer">
        {% if tenant.footer %}
          {{ tenant.footer }}
        {% else %}
          This bill was generated by {{ tenant.company_name }} using Warelyn.
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>'''

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
        "body_template": _MODERN_INVOICE_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_MINIMAL): {
        "name": "Invoice PDF — Minimal",
        "subject_template": None,
        "body_template": _MINIMAL_INVOICE_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_BOLD): {
        "name": "Invoice PDF — Bold",
        "subject_template": None,
        "body_template": _BOLD_INVOICE_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_INVOICE_WARM): {
        "name": "Invoice PDF — Warm",
        "subject_template": None,
        "body_template": _WARM_INVOICE_PDF,
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
        "body_template": _MODERN_BILL_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_MINIMAL): {
        "name": "Bill PDF — Minimal",
        "subject_template": None,
        "body_template": _MINIMAL_BILL_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_BOLD): {
        "name": "Bill PDF — Bold",
        "subject_template": None,
        "body_template": _BOLD_BILL_PDF,
        "body_template_text": None,
        "is_active": True,
    },
    (PDF, DocumentTemplateKey.PDF_BILL_WARM): {
        "name": "Bill PDF — Warm",
        "subject_template": None,
        "body_template": _WARM_BILL_PDF,
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
