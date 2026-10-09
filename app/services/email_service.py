import logging
import smtplib
from email.message import EmailMessage

from app.config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USER:
            smtp.login(SMTP_USER, SMTP_PASSWORD or "")
        smtp.send_message(message)

    logger.info("Sent email to %s subject=%s", to_email, subject)
