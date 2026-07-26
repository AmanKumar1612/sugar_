import uuid

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime

from sqlalchemy.sql import func


class UUIDMixin:

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )


class TimestampMixin:

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )