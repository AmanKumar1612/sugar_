import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Message(Base):

    __tablename__ = "messages"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    chat_id = Column(
        String,
        ForeignKey("chats.id"),
        nullable=False,
        index=True,
    )

    role = Column(
        String,
        nullable=False,
    )
    # user
    # assistant

    content = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    chat = relationship(
        "Chat",
        back_populates="messages",
    )