from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import Base, Message
from app.schemas import SendMessageIn, SendMessageOut, MessageStatusOut
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


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/send", response_model=SendMessageOut, dependencies=[Depends(check_api_key)])
def send_message(payload: SendMessageIn, db: Session = Depends(get_db)):
    message = Message(
        to_email=payload.to_email,
        subject=payload.subject,
        body=payload.body,
        status="queued",
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    send_message_task.delay(message.id)

    return SendMessageOut(id=message.id, status=message.status)


@app.get("/messages/{message_id}", response_model=MessageStatusOut, dependencies=[Depends(check_api_key)])
def get_message(message_id: str, db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message