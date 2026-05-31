import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


def _build_message(to_email: str, subject: str, body_text: str, body_html: str | None = None, attachment: bytes | None = None, attachment_filename: str | None = None) -> MIMEMultipart:
    settings = get_settings()
    if attachment:
        msg = MIMEMultipart("mixed")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body_text, "plain"))
        if body_html:
            alt.attach(MIMEText(body_html, "html"))
        msg.attach(alt)
        part = MIMEApplication(attachment, Name=attachment_filename or "document.pdf")
        part["Content-Disposition"] = f'attachment; filename="{attachment_filename or "document.pdf"}"'
        msg.attach(part)
    else:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    return msg


def _send_via_smtp(msg: MIMEMultipart) -> None:
    settings = get_settings()
    try:
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            if settings.smtp_use_tls:
                server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
        server.quit()
    except OSError as exc:
        raise EmailDeliveryError(f"Failed to deliver email via SMTP: {exc}") from exc


def send_email(to_email: str, subject: str, body_text: str, body_html: str | None = None, attachment: bytes | None = None, attachment_filename: str | None = None) -> None:
    settings = get_settings()
    if settings.email_delivery_mode == "log":
        logger.info(f"[EMAIL LOG MODE] To: {to_email}, Subject: {subject}, Body: {body_text[:200]}, Attachment: {'yes' if attachment else 'no'}")
        return
    msg = _build_message(to_email, subject, body_text, body_html, attachment, attachment_filename)
    _send_via_smtp(msg)


def send_verification_email(to_email: str, code: str) -> None:
    subject = "Verify your Warelyn email"
    body_text = (
        f"Your Warelyn email verification code is: {code}\n\n"
        f"This code will expire in 10 minutes.\n\n"
        f"If you did not request this, please ignore this email."
    )
    body_html = (
        f"<h2>Warelyn Email Verification</h2>"
        f"<p>Your verification code is:</p>"
        f"<h1 style='letter-spacing:8px;font-size:32px;color:#1e40af;'>{code}</h1>"
        f"<p>This code will expire in 10 minutes.</p>"
        f"<p>If you did not request this, please ignore this email.</p>"
    )
    send_email(to_email, subject, body_text, body_html)


def send_password_reset_email(to_email: str, code: str) -> None:
    subject = "Reset your Warelyn password"
    body_text = (
        f"Your Warelyn password reset code is: {code}\n\n"
        f"This code will expire in 15 minutes.\n\n"
        f"If you did not request this, please ignore this email."
    )
    body_html = (
        f"<h2>Warelyn Password Reset</h2>"
        f"<p>Your password reset code is:</p>"
        f"<h1 style='letter-spacing:8px;font-size:32px;color:#1e40af;'>{code}</h1>"
        f"<p>This code will expire in 15 minutes.</p>"
        f"<p>If you did not request this, please ignore this email.</p>"
    )
    send_email(to_email, subject, body_text, body_html)


def send_password_reset_link_email(to_email: str, reset_url: str) -> None:
    subject = "Reset your Warelyn password"
    body_text = (
        "A password reset was requested for your Warelyn account.\n\n"
        f"Reset your password using this secure link:\n{reset_url}\n\n"
        "This link will expire in 15 minutes.\n\n"
        "If you did not request this, please ignore this email."
    )
    body_html = (
        "<h2>Warelyn Password Reset</h2>"
        "<p>A password reset was requested for your account.</p>"
        f"<p><a href='{reset_url}' style='display:inline-block;background:#1e40af;color:#ffffff;padding:10px 16px;border-radius:8px;text-decoration:none;'>Reset password</a></p>"
        f"<p>If the button does not work, copy this URL:<br><a href='{reset_url}'>{reset_url}</a></p>"
        "<p>This link will expire in 15 minutes.</p>"
        "<p>If you did not request this, please ignore this email.</p>"
    )
    send_email(to_email, subject, body_text, body_html)
