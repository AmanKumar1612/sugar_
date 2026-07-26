from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

import uuid

from app.core.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String,
        nullable=True
    )

    provider = Column(
        String,
        nullable=False,
        default="LOCAL"
    )

    is_verified = Column(
        Boolean,
        default=False
    )

    is_active = Column(
    Boolean,
    default=True
    )

    profile_image = Column(
        String,
        nullable=True
    )

    role_id = Column(
        String,
        ForeignKey("roles.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    role = relationship(
        "Role",
        back_populates="users"
    )


    chats = relationship(
        "Chat",
        back_populates="user",
        cascade="all, delete"
    )

    search_logs = relationship(
    "SearchLog",
    back_populates="user",
    cascade="all, delete-orphan",
)