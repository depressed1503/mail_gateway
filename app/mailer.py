import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.config import SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USERNAME


def send_email_smtp(
    to_email: list[str],
    from_email: str,
    cc: list[str],
    bcc: list[str],
    subject: str,
    body: str,
    attachments: list[dict],
) -> None:
    msg = EmailMessage()
    msg["From"] = from_email or SMTP_FROM
    msg["To"] = ", ".join(to_email)

    if cc:
        msg["Cc"] = ", ".join(cc)

    msg["Subject"] = subject
    msg.set_content(body)

    for item in attachments:
        file_path = item["path"]
        filename = item["filename"]

        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )

    recipients = list(to_email) + list(cc) + list(bcc)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg, to_addrs=recipients)