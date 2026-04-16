from datetime import datetime
from pydantic import BaseModel, EmailStr


class SendMessageIn(BaseModel):
    to_email: EmailStr
    subject: str
    body: str


class SendMessageOut(BaseModel):
    id: str
    status: str


class MessageStatusOut(BaseModel):
    id: str
    to_email: EmailStr
    subject: str
    status: str
    error: str | None
    created_at: datetime
    sent_at: datetime | None