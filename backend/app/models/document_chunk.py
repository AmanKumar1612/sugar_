from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy import ForeignKey

from app.core.database import Base

from app.models.base import UUIDMixin
from app.models.base import TimestampMixin


class DocumentChunk(
    Base,
    UUIDMixin,
    TimestampMixin
):
    __tablename__ = "document_chunks"

    document_id = Column(
        String(36),
        ForeignKey("documents.id")
    )

    chunk_index = Column(
        Integer,
        nullable=False
    )

    chunk_text = Column(
        Text,
        nullable=False
    )

    qdrant_point_id = Column(
        String(100),
        nullable=True
    )