import os
import smtplib
from datetime import datetime, timezone

from celery import Celery

from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from app.db import SessionLocal
from app.mailer import send_email_smtp
from app.models import Message

celery_app = Celery(
    "mail_gateway",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.task_routes = {
    "app.tasks.send_message_task": {"queue": "mail"},
}


@celery_app.task(
    bind=True,
    name="app.tasks.send_message_task",
    rate_limit="5/m",
    autoretry_for=(smtplib.SMTPException, TimeoutError, OSError),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_message_task(self, message_id: str):
    db = SessionLocal()
    message = None

    try:
        message = db.get(Message, message_id)
        if not message:
            return

        if message.status == "sent":
            return

        message.status = "sending"
        message.error = None
        db.commit()

        send_email_smtp(
            to_email=message.to_email,
            from_email=message.from_email,
            cc=message.cc,
            bcc=message.bcc,
            subject=message.subject,
            body=message.body,
            attachments=message.attachments,
        )

        message.status = "sent"
        message.sent_at = datetime.now(timezone.utc)
        message.error = None
        db.commit()

    except Exception as e:
        if message is not None:
            message.status = "failed"
            message.error = str(e)
            db.commit()
        raise

    finally:
        try:
            if message and message.status in {"sent", "failed"}:
                for item in message.attachments or []:
                    path = item.get("path")
                    if path and os.path.exists(path):
                        os.remove(path)
        finally:
            db.close()