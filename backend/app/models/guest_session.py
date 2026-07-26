"""
GuestSession — tracks anonymous public users by a client-generated token.
Contact info is only collected at escalation time (not up-front).
"""
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GuestSession(Base):

    __tablename__ = "guest_sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # The opaque token handed to the browser (cookie or client-generated UUID)
    session_token = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    # Populated only when an escalation occurs
    contact_name = Column(String(200), nullable=True)
    contact_email = Column(String(320), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # One session → many escalated queries
    escalated_queries = relationship(
        "EscalatedQuery",
        back_populates="guest_session",
        cascade="all, delete-orphan",
    )
