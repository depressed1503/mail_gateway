from datetime import datetime
from pydantic import BaseModel, EmailStr


class SendMessageOut(BaseModel):
    id: str
    status: str


class MessageStatusOut(BaseModel):
    id: str
    to_email: list[EmailStr]
    from_email: EmailStr
    cc: list[EmailStr]
    bcc: list[EmailStr]
    subject: str
    body: str
    attachments: list[dict]
    status: str
    error: str | None
    created_at: datetime
    sent_at: datetime | None