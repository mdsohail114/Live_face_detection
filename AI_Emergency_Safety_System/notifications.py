"""SMS (Twilio) and email (SMTP) notifications with explicit Demo Mode."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

DEMO_SMS = "Demo Mode: SMS service is not configured."
DEMO_EMAIL = "Demo Mode: Email service is not configured."


def send_emergency_sms(to_phone, message):
    """
    Send one SMS. Returns a human-readable status string.
    Never reports success if Twilio is not configured.
    """
    if not Config.sms_configured():
        return DEMO_SMS

    try:
        from twilio.rest import Client

        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        result = client.messages.create(
            body=message,
            from_=Config.TWILIO_FROM_NUMBER,
            to=to_phone,
        )
        sid = result.sid or "unknown"
        return f"Sent (Twilio SID: {sid})"
    except Exception as error:
        return f"SMS failed: {error}"


def send_emergency_email(to_email, subject, body):
    """
    Send one email. Returns a human-readable status string.
    Never reports success if SMTP is not configured.
    """
    if not to_email:
        return "Skipped: no email address for this contact."

    if not Config.email_configured():
        return DEMO_EMAIL

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = Config.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as server:
            if Config.SMTP_USE_TLS:
                server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.sendmail(Config.SMTP_FROM_EMAIL, [to_email], msg.as_string())
        return "Sent"
    except Exception as error:
        return f"Email failed: {error}"


def notify_contacts(contacts, message, user_name):
    """
    Notify every registered emergency contact.
    Aggregates SMS and email statuses for storage on the alert row.
    """
    sms_parts = []
    email_parts = []

    if not contacts:
        return (
            "No emergency contacts saved.",
            "No emergency contacts saved.",
        )

    subject = f"EMERGENCY ALERT from {user_name}"
    for contact in contacts:
        phone = (contact.get("phone") or "").strip()
        email = (contact.get("email") or "").strip()
        label = contact.get("name") or "Contact"

        if phone:
            sms_status = send_emergency_sms(phone, message)
            sms_parts.append(f"{label}: {sms_status}")
        else:
            sms_parts.append(f"{label}: Skipped (no phone).")

        if email:
            email_status = send_emergency_email(email, subject, message)
            email_parts.append(f"{label}: {email_status}")
        else:
            email_parts.append(f"{label}: Skipped (no email).")

    return " | ".join(sms_parts), " | ".join(email_parts)
