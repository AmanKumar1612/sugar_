from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

import uuid

from app.core.database import Base


class PasswordResetToken(Base):

    __tablename__ = "password_reset_tokens"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    token = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # email is stored so we can look up tokens without joining users
    email = Column(
        String,
        nullable=False,
        index=True
    )

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    is_used = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User"
    )