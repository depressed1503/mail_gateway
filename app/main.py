import os
import tempfile

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import Base, Message
from app.schemas import MessageStatusOut, SendMessageOut
from app.security import check_api_key
from app.tasks import send_message_task

app = FastAPI(title="Mail Gateway MVP")

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_email_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@app.get("/health")
def health():
    return {"ok": True}


@app.post(
    "/send",
    response_model=SendMessageOut,
    dependencies=[Depends(check_api_key)],
)
async def send_message(
    to_email: str = Form(..., description="Comma-separated emails"),
    from_email: str = Form(...),
    cc: str | None = Form(default=None, description="Comma-separated emails"),
    bcc: str | None = Form(default=None, description="Comma-separated emails"),
    subject: str = Form(...),
    body: str = Form(...),
    attachments: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    to_list = parse_email_list(to_email)
    cc_list = parse_email_list(cc)
    bcc_list = parse_email_list(bcc)

    if not to_list:
        raise HTTPException(status_code=400, detail="to_email is required")

    saved_attachments: list[dict] = []

    for file in attachments:
        suffix = os.path.splitext(file.filename or "")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name

        saved_attachments.append(
            {
                "filename": file.filename or os.path.basename(temp_path),
                "content_type": file.content_type,
                "path": temp_path,
            }
        )

    message = Message(
        to_email=to_list,
        from_email=from_email,
        cc=cc_list,
        bcc=bcc_list,
        subject=subject,
        body=body,
        attachments=saved_attachments,
        status="queued",
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    send_message_task.delay(message.id)

    return SendMessageOut(id=message.id, status=message.status)


@app.get(
    "/messages/{message_id}",
    response_model=MessageStatusOut,
    dependencies=[Depends(check_api_key)],
)
def get_message(message_id: str, db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message