import smtplib
from email.message import EmailMessage
from loguru import logger
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM


def send_email_smtp(to_email: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    logger.debug(f"from: {msg["From"]}, to: {msg['To']}, subject: {msg['Subject']}")
    # with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
    #     server.ehlo()
    #     server.starttls()
    #     server.ehlo()
    #     server.login(SMTP_USERNAME, SMTP_PASSWORD)
    #     server.send_message(msg)