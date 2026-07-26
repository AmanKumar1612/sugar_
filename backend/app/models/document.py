import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Document(Base):

    __tablename__ = "documents"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    title = Column(
        String,
        nullable=False,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    source_type = Column(
        String,
        nullable=False,
    )
    # pdf
    # website

    source_url = Column(
        Text,
        nullable=True,
    )

    file_name = Column(
        String,
        nullable=True,
    )

    content = Column(
        Text,
        nullable=False,
    )

    chunk_count = Column(
        Integer,
        default=0,
    )

    status = Column(
        String,
        default="INDEXED",
    )
    # INDEXING
    # INDEXED
    # FAILED

    # Visibility scope: "public" = anyone can see; "admin" = admins only
    scope = Column(
        String,
        nullable=False,
        default="public",
        index=True,
    )

    uploaded_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    uploader = relationship(
        "User",
        foreign_keys=[uploaded_by],
    )