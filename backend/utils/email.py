"""
Minimal email sender for password reset links, using Python's built-in
smtplib — no new paid dependency needed. Works with Gmail (via an App
Password), or any other SMTP provider.

If SMTP isn't configured (SMTP_HOST empty), send_email() doesn't fail —
it just logs the content to the console instead. This keeps local dev
and testing working without requiring email setup, while production
deployments that DO set SMTP_* env vars get real email delivery.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings


def send_email(to_email: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"\n📧 [EMAIL NOT SENT — SMTP not configured] To: {to_email} | Subject: {subject}")
        print(f"   Body:\n{text_body or html_body}\n")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False


def send_password_reset_email(to_email: str, reset_link: str, user_name: str) -> bool:
    subject = "Reset your School Hub password"
    text_body = (
        f"Hi {user_name},\n\n"
        f"We received a request to reset your School Hub password. "
        f"Click the link below to set a new password:\n\n"
        f"{reset_link}\n\n"
        f"This link expires in 1 hour. If you didn't request this, you can safely ignore this email.\n"
    )
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2>Reset your password</h2>
        <p>Hi {user_name},</p>
        <p>We received a request to reset your School Hub password. Click the button below to set a new one:</p>
        <p style="margin: 24px 0;">
            <a href="{reset_link}" style="background: #667eea; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">Reset Password</a>
        </p>
        <p style="color: #666; font-size: 13px;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
    </div>
    """
    return send_email(to_email, subject, html_body, text_body)
