import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    to_email: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    from_email: Mapped[str] = mapped_column(String(320), nullable=False)
    cc: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    bcc: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    attachments: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )