import smtplib
from datetime import datetime

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
    autoretry_for=(smtplib.SMTPException, TimeoutError, OSError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    rate_limit="1/m"
)
def send_message_task(self, message_id: str):
    db = SessionLocal()
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
            subject=message.subject,
            body=message.body,
        )

        message.status = "sent"
        message.sent_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        msg = db.get(Message, message_id)
        if msg:
            msg.status = "failed"
            msg.error = str(e)
            db.commit()
        raise
    finally:
        db.close()